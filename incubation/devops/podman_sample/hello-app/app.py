from http.server import BaseHTTPRequestHandler, HTTPServer
import redis

r = redis.Redis(host="localhost", port=6379)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        hits = r.incr("hits")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"Hello from Podman! Seen {hits} times.\n".encode())


HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
