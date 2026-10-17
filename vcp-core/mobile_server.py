"""Phone-friendly VCP demonstrator. Localhost only; never expose API keys in browser."""
import json, os, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from model_adapter import assess_claim, model_proposal, parse_claim
UI=Path(__file__).with_name("mobile.html")
class Handler(BaseHTTPRequestHandler):
    def _json(self,obj,status=200):
        data=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(data)))
        self.end_headers();self.wfile.write(data)
    def do_GET(self):
        if self.path!="/":
            return self._json({"error":"not found"},404)
        data=UI.read_bytes()
        self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Security-Policy","default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; object-src 'none'")
        self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
    def do_POST(self):
        if self.path not in ("/assess","/model"): return self._json({"error":"not found"},404)
        try:
            n=int(self.headers.get("Content-Length","0"))
            if n<1 or n>12000: return self._json({"error":"invalid request length"},413)
            body=json.loads(self.rfile.read(n))
            if not isinstance(body,dict): raise ValueError("Expected object")
            if self.path=="/model":
                claim=model_proposal(str(body.get("prompt","")),str(body.get("model","")))
                result=assess_claim(claim)
                result["model_generated"]=True
            else:
                claim=body.get("claim")
                if not isinstance(claim,dict): raise ValueError("Missing claim")
                result=assess_claim(parse_claim(json.dumps(claim)))
                result["model_generated"]=False
            self._json(result)
        except (ValueError,KeyError,TypeError) as ex:
            self._json({"error":str(ex)[:180]},400)
        except Exception:
            self._json({"error":"Model gateway unavailable or unconfigured"},503)
    def log_message(self,fmt,*args): pass
if __name__=="__main__":
    print("i VCP local verification interface: http://127.0.0.1:8795")
    ThreadingHTTPServer(("127.0.0.1",8795),Handler).serve_forever()
