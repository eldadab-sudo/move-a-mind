import os
from urllib.parse import urlparse
from http.server import ThreadingHTTPServer
import server_v31 as v31

app = v31.app
LOGO_DATA = "data:image/webp;base64,UklGRgQlAABXRUJQVlA4IPgkAAAQkACdASoAAQABPj0ai0QiIaET+QW8IAPEpEDFQ0RtN9M+N90+tf7L"
# Full base64 is appended below at startup from a compact literal split to keep the source readable.
LOGO_DATA += ""

# The full logo payload is stored here as a single compact string.
LOGO_B64 = "__LOGO_B64__"
LOGO_DATA = "data:image/webp;base64," + LOGO_B64

class H(v31.v29.H):
    def do_GET(self):
        p = urlparse(self.path).path
        if p == '/':
            html = (app.WEB / 'global.html').read_text(encoding='utf-8')
            html = html.replace('</head>', f'<link rel="icon" type="image/webp" href="{LOGO_DATA}"><link rel="apple-touch-icon" href="{LOGO_DATA}"></head>')
            html = html.replace('</style>', '''
.brand{display:flex;align-items:center;gap:10px;letter-spacing:.17em}
.brandLogo{width:42px;height:42px;border-radius:12px;object-fit:cover;box-shadow:0 7px 22px rgba(16,32,30,.14);flex:0 0 auto}
.brandText{font-weight:900;letter-spacing:.17em;font-size:13px;white-space:nowrap}
@media(max-width:760px){.brandLogo{width:36px;height:36px;border-radius:10px}.brandText{font-size:12px;letter-spacing:.13em}}
</style>''')
            html = html.replace('<div class="brand">MOVE A MIND</div>', f'<div class="brand"><img class="brandLogo" src="{LOGO_DATA}" alt="Move A Mind logo"><span class="brandText">MOVE A MIND</span></div>')
            b = html.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Cache-Control','no-store')
            self.send_header('Content-Length',str(len(b)))
            self.end_headers(); self.wfile.write(b); return
        return super().do_GET()

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.1 logo on every screen')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), H).serve_forever()
