#!/usr/bin/python3
import hmac
import json
import socket
import ssl
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from common import *
import cluster
from control import local
from languages import using
class Handler(BaseHTTPRequestHandler):
    server_version='LinuxSphere/0.2'
    def log_message(self,*_):pass
    def answer(self,status,obj):
        data=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
    def do_GET(self):
        self.answer(200,{'service':'LinuxSphere VE','api':1}) if self.path=='/v1/health' else self.answer(404,{'error':'Unbekannter Pfad.'})
    def do_POST(self):
        with using(self.headers.get('Accept-Language')):
            self.handle_post()
    def handle_post(self):
        try:
            if self.path not in ('/v1/node','/v1/enroll','/v1/revoke','/v1/fusion'):return self.answer(404,{'error':'Unbekannter Pfad.'})
            raw=self.headers.get('Authorization','');token=raw[7:] if raw.startswith('Bearer ') else ''
            manager=None
            if self.path in ('/v1/node','/v1/revoke'):
                manager=next((k for k,v in jsonread(cluster.GRANTS,{}).items() if hmac.compare_digest(v,digest(token))),None)
                if not manager:raise PermissionError(tr('Access denied.'))
            length=number(self.headers.get('Content-Length','0'),2,1048576,tr('Request length'))
            a=json.loads(self.rfile.read(length))
            if not isinstance(a,dict):raise ValueError(tr('Expected a JSON object.'))
            if self.path=='/v1/enroll':result=cluster.enroll(a)
            elif self.path=='/v1/fusion':
                group=jsonread(cluster.GROUPS,{}).get(name(a['name']),{})
                if not group.get('auth') or not hmac.compare_digest(group['auth'],digest(token)):raise PermissionError(tr('Invalid group key.'))
                result=cluster.batch(a)
            elif self.path=='/v1/revoke':
                with locked('grants'):
                    grants=jsonread(cluster.GRANTS,{});grants.pop(manager,None);atomic(cluster.GRANTS,grants)
                result={'ok':True}
            else:result=local(a['op'],a.get('args',{}))
            self.answer(200,result)
        except PermissionError as e:self.answer(403,{'error':str(e)})
        except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as e:self.answer(400,{'error':str(e)[:1200]})
class Server(ThreadingHTTPServer):
    daemon_threads=True
    limit=threading.BoundedSemaphore(24)
    def process_request(self,request,client_address):
        if self.limit.acquire(blocking=False):super().process_request(request,client_address)
        else:request.close()
    def process_request_thread(self,request,client_address):
        try:
            request.settimeout(20)
            with tls.wrap_socket(request,server_side=True) as secure:self.finish_request(secure,client_address)
        except (OSError,ssl.SSLError):pass
        finally:self.shutdown_request(request);self.limit.release()
crt,key=cluster.cert();tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.minimum_version=ssl.TLSVersion.TLSv1_2;tls.load_cert_chain(crt,key)
Server(('0.0.0.0',9443),Handler).serve_forever()
