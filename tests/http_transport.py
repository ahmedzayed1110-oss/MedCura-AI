"""Exercise the production HTTP parser/handler without requesting a TCP connection."""
import base64
import io
import json
import sys
import tempfile
from http.client import HTTPResponse
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import run


class ByteStream:
    def __init__(self,data):
        self.input=io.BytesIO(data)
        self.output=io.BytesIO()

    def makefile(self,*args,**kwargs):
        return self.input

    def sendall(self,data):
        self.output.write(data)


def response(server,method,path,headers,body=b""):
    values={k.lower():str(v) for k,v in headers.items()}
    values.setdefault("host",f"127.0.0.1:{server.server_port}")
    values["content-length"]=str(len(body))
    raw=(f"{method} {path} HTTP/1.0\r\n"+"".join(f"{k}: {v}\r\n" for k,v in values.items())+"\r\n").encode("latin1")+body
    stream=ByteStream(raw)
    run.Handler(stream,("127.0.0.1",0),server)
    result=HTTPResponse(ByteStream(stream.output.getvalue()))
    result.begin()
    return result


def main():
    with tempfile.TemporaryDirectory() as folder:
        cfg=run.Settings(folder)
        srv=SimpleNamespace(cfg=cfg,server_port=8765)
        # Only temporary fixture credentials travel through the private test process pipe.
        print(json.dumps({"password":json.loads((Path(folder)/"local-accounts.json").read_text())["director"]}),flush=True)
        for line in sys.stdin:
            req=json.loads(line)
            res=response(srv,req["method"],req["path"],req["headers"],base64.b64decode(req["body"]))
            print(json.dumps(dict(id=req["id"],status=res.status,headers=dict(res.getheaders()),
                                  body=base64.b64encode(res.read()).decode())),flush=True)

if __name__=="__main__":
    main()

