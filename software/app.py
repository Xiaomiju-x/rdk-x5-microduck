"""D-only local tuning panel. Defaults to DEMO; hardware needs --robot.

Always binds loopback. Use an SSH local forward to reach the X5 from a laptop.
Starting, opening the page, saving parameters and selecting cycles do not move.
"""
import argparse
import json
import secrets
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

import runtime
from parameters import validate_parameters,validate_cycles

class Manager:
    def __init__(self,robot=None,data_dir=None,demo_scale=1.):
        self.cfg=runtime.read_json(robot) if robot else None;self.demo=self.cfg is None
        self.folder=Path(data_dir or runtime.HERE/'.local');self.folder.mkdir(parents=True,exist_ok=True)
        self.preset_path=self.folder/'preset.json'
        self.parameters=validate_parameters(runtime.read_json(self.preset_path)) if self.preset_path.exists() else runtime.defaults()
        self.lock=threading.Lock();self.stop_event=threading.Event();self.current=None;self.history=[];self.busy=False
        self.token=secrets.token_urlsafe(32);self.demo_scale=demo_scale
    def status(self):
        with self.lock:return json.loads(json.dumps({'demo':self.demo,'busy':self.busy,'current':self.current,'history':self.history[-10:]}))
    def save(self,params):
        params=validate_parameters(params)
        with self.lock:
            if self.busy:raise ValueError('运行期间不能改参数，请等待结束')
            runtime.write_json(self.preset_path,params);self.parameters=params
        return {'saved':True,'parameters':params,'motion_writes':0}
    def start(self,request):
        action=request.get('action');cycles=validate_cycles(request.get('cycles',1))
        if action not in ('run','restore','partial_restore','inspect'):raise ValueError('Unknown action')
        if action!='run' and cycles!=1:raise ValueError('Only run supports multiple cycles')
        params=validate_parameters(request.get('parameters',self.parameters))
        if action=='run' and request.get('onsite_ready') is not True:raise ValueError('请确认本轮现场已准备：悬空时托稳且双腿自由；落地时自行站稳并留空位。线缆松弛，全程在旁接护')
        if action in ('restore','partial_restore') and request.get('supported') is not True:raise ValueError('请先托稳躯干和头部、双脚卸重')
        if self.cfg and action!='inspect':runtime.validate_device(self.cfg,motion=True,imu=action=='run')
        if action=='run':runtime.plan(self.cfg,params,cycles)
        with self.lock:
            if self.busy:raise ValueError('已有任务运行，不排队')
            self.busy=True;self.stop_event.clear()
            self.current={'id':uuid.uuid4().hex,'action':action,'cycles':cycles,'parameters':params,'status':'running','progress':{},'started_at':time.time()}
        threading.Thread(target=self._work,args=(action,params,cycles),daemon=True).start()
        return self.status()
    def _cancel(self):
        if self.stop_event.is_set():raise RuntimeError('操作员停止：保持最后目标，不自动失能或复位')
    def _progress(self,row):
        with self.lock:self.current['progress']=row
    def _demo(self,action,params,cycles):
        if action=='inspect':return {'motion_writes':0,'note':'DEMO has no serial device'}
        if action!='run':
            for k in range(30):self._cancel();self._progress({'frame':k+1,'total':30,'phase':'DEMO_RESTORE'});time.sleep(.1*self.demo_scale)
            return {'demo':True,'motion_writes':0}
        frames=runtime.build_frames(runtime.integer_map(runtime.reference()['start'],'start'))
        completed=0
        for cycle in range(1,cycles+1):
            for k,frame in enumerate(frames):
                self._cancel();self._progress({'cycle':cycle,'cycles':cycles,'frame':k+1,'total':400,'global_frame':(cycle-1)*400+k+1,'global_total':400*cycles,'phase':frame['phase']})
                time.sleep(frame['interval_s']*self.demo_scale)
            completed+=1
        return {'demo':True,'motion_writes':0,'cycles_completed':completed,'physical_result':'not evaluated'}
    def _work(self,action,params,cycles):
        try:
            if self.demo:result=self._demo(action,params,cycles)
            elif action=='inspect':result=runtime.inspect_device(self.cfg,self.folder/'records')
            elif action=='run':result=runtime.run(self.cfg,params,cycles,self._progress,self._cancel,self.folder/'records')
            else:
                for remaining in (3,2,1):self._cancel();self._progress({'phase':'RESTORE_COUNTDOWN','seconds':remaining});time.sleep(1)
                result=runtime.restore(self.cfg,self._progress,self._cancel,self.folder/'records',partial=action=='partial_restore')
            with self.lock:self.current.update(status='completed',result=result)
        except BaseException as exc:
            with self.lock:self.current.update(status='stopped' if self.stop_event.is_set() else 'failed',error=str(exc))
        finally:
            with self.lock:
                self.current['finished_at']=time.time();self.history.append(dict(self.current));self.history=self.history[-30:]
                try:runtime.write_json(self.folder/'jobs'/f"{self.current['id']}.json",self.current)
                except OSError as exc:self.current['logging_error']=str(exc)
                finally:self.busy=False

def make_handler(manager):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def _send(self,status,body,kind='application/json; charset=utf-8'):
            if not isinstance(body,bytes):body=json.dumps(body,ensure_ascii=False).encode()
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers();self.wfile.write(body)
        def _local(self):
            host=self.headers.get('Host','')
            if host not in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'):
                raise ValueError('Loopback Host required; use an SSH tunnel with the same local port')
            origin=self.headers.get('Origin')
            if origin and origin!=f'http://{host}':raise ValueError('Same-origin request required')
        def do_GET(self):
            try:
                self._local()
                if self.path=='/api/config':self._send(200,{'version':'D_PUBLIC_CASE_20261027_R1','demo':manager.demo,'parameters':manager.parameters,'cycles':[1,2,3,5],'token':manager.token})
                elif self.path=='/api/status':self._send(200,manager.status())
                elif self.path in ('/','/index.html','/app.js','/style.css'):
                    filename='index.html' if self.path=='/' else self.path[1:]
                    kind='text/html; charset=utf-8' if filename.endswith('.html') else ('text/css' if filename.endswith('.css') else 'text/javascript')
                    self._send(200,(runtime.HERE/'web'/filename).read_bytes(),kind)
                else:self._send(404,{'error':'Not found'})
            except Exception as exc:self._send(400,{'error':str(exc)})
        def do_POST(self):
            try:
                self._local()
                if self.headers.get('X-Control-Token')!=manager.token:raise ValueError('Invalid control token')
                n=int(self.headers.get('Content-Length','0'))
                if not 0<n<=8192:raise ValueError('Invalid body size')
                value=json.loads(self.rfile.read(n))
                if self.path=='/api/save':result=manager.save(value['parameters'])
                elif self.path=='/api/action':result=manager.start(value)
                elif self.path=='/api/stop':manager.stop_event.set();result={'stop_requested':True}
                else:self._send(404,{'error':'Not found'});return
                self._send(200,result)
            except Exception as exc:self._send(400,{'error':str(exc)})
    return Handler

def main():
    cli=argparse.ArgumentParser(description=__doc__);group=cli.add_mutually_exclusive_group()
    group.add_argument('--demo',action='store_true');group.add_argument('--robot')
    cli.add_argument('--port',type=int,default=9194);cli.add_argument('--data-dir')
    args=cli.parse_args();manager=Manager(args.robot,args.data_dir)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),make_handler(manager))
    print(f"D {'DEMO — no hardware' if manager.demo else 'HARDWARE — explicit actions only'} http://127.0.0.1:{args.port}/",flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:manager.stop_event.set()
    finally:server.server_close()

if __name__=='__main__':main()
