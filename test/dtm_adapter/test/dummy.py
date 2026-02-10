from http.server import BaseHTTPRequestHandler , HTTPServer
from datetime import datetime

class DummyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length" , 0))
        body = self.rfile.read(length)
        print(f"[{datetime.now()}] REQ POST {self.path} BODY={body.decode(errors='ignore')}" )
        self._send_ok()

    def _send_ok(self):
        print(f"[{datetime.now()}] RESP 200 START")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
        print(f"[{datetime.now()}] RESP 200 END")

HTTPServer(("127.0.0.1", 9000) , DummyHandler).serve_forever()
