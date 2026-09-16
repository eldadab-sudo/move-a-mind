import os
from http.server import ThreadingHTTPServer
import server_v40 as v40

# v4.19: keep all v4.18 UI/paywall changes, but prevent mobile browsers
# from serving stale HTML after a Production deploy.
app = v40.app

class H(v40.H):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.19 - fresh UI + paywall + rotating analysis logo')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), H).serve_forever()
