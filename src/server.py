"""Private-by-default HTTP job API. Secrets and raster work stay on the backend."""
import argparse, hmac, json, os, queue, secrets, subprocess, sys, threading, time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1]
RUNTIME=Path(os.environ.get('WHEANUT_RUNTIME_DIR','/tmp/wheanut-live-runtime'))
ALLOWED={'https://wheanut.pages.dev','http://127.0.0.1:8765','http://127.0.0.1:8767','http://127.0.0.1:8766','https://hacktheharvest.farmgpu.net'}
JOBS={};LOCK=threading.Lock();PENDING=queue.Queue(maxsize=4)

def load_environment():
    # Only the explicitly named backend .env, never a directory scan or browser file.
    file=ROOT/'.env'
    if file.exists():
        for line in file.read_text().splitlines():
            key,sep,value=line.partition('=')
            if sep and key.strip() in {'NVIDIA_API_KEY','NVIDIA_MODEL','WHEANUT_EXPLAINER','WHEANUT_API_TOKEN'}:
                os.environ.setdefault(key.strip(),value.strip().strip('\"\''))

def worker():
    while True:
        job_id=PENDING.get();job=JOBS[job_id];folder=RUNTIME/job_id
        with LOCK:job['status']='running'
        try:
            with (folder/'worker.log').open('w') as log:
                process=subprocess.Popen([sys.executable,str(ROOT/'src/job_worker.py'),str(folder)],stdout=log,stderr=log)
                try:process.wait(timeout=480)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    try:process.wait(timeout=10)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
                    raise RuntimeError('Analysis timed out after eight minutes. Try again later.')
            result=json.loads((folder/'output.json').read_text())
            with LOCK:job.update(result);job['finishedAt']=time.time()
        except Exception:
            with LOCK:job.update(status='error',error='Analysis worker failed or timed out. Check the private worker log.')
        finally:PENDING.task_done()

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'frontend'),**kwargs)
    def log_message(self,*args):pass # Do not log user bodies, tokens, or API headers.
    def end_headers(self):
        origin=self.headers.get('Origin','')
        if origin in ALLOWED:
            self.send_header('Access-Control-Allow-Origin',origin);self.send_header('Vary','Origin')
        self.send_header('X-Content-Type-Options','nosniff');super().end_headers()
    def reply(self,status,payload):
        body=json.dumps(payload,allow_nan=False).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def authorized(self):
        if self.headers.get('Origin') and self.headers['Origin'] not in ALLOWED:return False
        return hmac.compare_digest(self.headers.get('Authorization',''), 'Bearer '+self.server.access_token)
    def do_OPTIONS(self):
        if self.headers.get('Origin','') not in ALLOWED:return self.reply(403,{'error':'Origin not allowed'})
        self.send_response(204);self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS');self.send_header('Access-Control-Allow-Headers','Authorization, Content-Type');self.send_header('Content-Length','0');self.end_headers()
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/health':
            if self.headers.get('Authorization') and not self.authorized():return self.reply(401,{'error':'Invalid backend access token'})
            return self.reply(200,{'status':'ready','authentication':'required','provider':os.environ.get('WHEANUT_EXPLAINER','local'),'maxJobSeconds':480,'publicDeployment':False})
        if path.startswith('/api/'):
            if not self.authorized():return self.reply(401,{'error':'Backend access token required. This is not your NVIDIA API key.'})
            job_id=path.removeprefix('/api/jobs/')
            with LOCK:job=dict(JOBS.get(job_id,{}))
            return self.reply(200,job) if job else self.reply(404,{'error':'Job not found'})
        # Prevent source, runtime, secret, directory and symlink escapes from static root.
        decoded=unquote(path);candidate=(ROOT/'frontend'/decoded.lstrip('/')).resolve()
        try:candidate.relative_to((ROOT/'frontend').resolve())
        except ValueError:return self.reply(404,{'error':'Not found'})
        if any(part.startswith('.') for part in Path(decoded).parts if part not in ['/']):return self.reply(404,{'error':'Not found'})
        return super().do_GET()
    def list_directory(self,path):return self.reply(404,{'error':'Not found'})
    def do_POST(self):
        if urlsplit(self.path).path!='/api/jobs':return self.reply(404,{'error':'Not found'})
        if not self.authorized():return self.reply(401,{'error':'Backend access token required. Never use the NVIDIA key in the browser.'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.reply(415,{'error':'Use application/json'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=131072:return self.reply(413,{'error':'Request must be smaller than 128 KiB'})
            request=json.loads(self.rfile.read(length))
            if not isinstance(request,dict):raise ValueError('Expected a JSON object')
            if len(str(request.get('question','')))>1000:raise ValueError('Question is too long')
            action=request.get('action','analyze')
            if action not in ['analyze','explain']:raise ValueError('Unknown action')
            if action=='explain' and not isinstance(request.get('fieldId'),str):raise ValueError('Choose an existing field report')
            # Bound retained metadata and queued work. One worker at a time shares the GPU.
            with LOCK:
                recent=sum(j['createdAt']>time.time()-3600 for j in JOBS.values())
                if recent>=20:return self.reply(429,{'error':'Demo limit: 20 jobs per hour. Reuse completed results.'})
                if PENDING.full():return self.reply(429,{'error':'Analysis queue is full. Retry later.'})
                job_id=secrets.token_hex(12);folder=RUNTIME/job_id;folder.mkdir(mode=0o700)
                (folder/'request.json').write_text(json.dumps(request));job={'jobId':job_id,'status':'queued','createdAt':time.time()};JOBS[job_id]=job;PENDING.put_nowait(job_id)
            return self.reply(202,job)
        except (ValueError,TypeError):return self.reply(400,{'error':'Invalid request. Check the field boundary, season and question.'})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8767);args=parser.parse_args();load_environment()
    RUNTIME.mkdir(parents=True,exist_ok=True,mode=0o700)
    token=os.environ.get('WHEANUT_API_TOKEN') or secrets.token_urlsafe(32)
    token_file=RUNTIME/'.api-token';token_file.write_text(token);token_file.chmod(0o600)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.access_token=token
    threading.Thread(target=worker,daemon=True).start()
    print(f'Wheanut backend listening on loopback port {args.port}; API requires a token stored in the private runtime directory. No public tunnel is configured.',flush=True)
    server.serve_forever()
