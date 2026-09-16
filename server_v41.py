import os
from http.server import ThreadingHTTPServer
import server_v40 as v40

app = v40.app

class H(v40.H):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.20 - approved analysis screens + Stripe paywall')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), H).serve_forever()
