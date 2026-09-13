import os
from urllib.parse import urlparse
from http.server import ThreadingHTTPServer
import server_v31 as v31

app = v31.app
LOGO_PATH = app.WEB / 'move-a-mind-logo.webp'
INDEX = app.WEB / 'global.html'

# Patch the shared shell once, but DO NOT intercept '/'.
# The inherited handler must keep serving '/' because it injects the current
# domain -> subdomain -> scenario navigation and all working event handlers.
html = INDEX.read_text(encoding='utf-8')
if 'brandLogo' not in html:
    html = html.replace(
        '</head>',
        '<link rel="icon" type="image/webp" href="/move-a-mind-logo.webp">'
        '<link rel="apple-touch-icon" href="/move-a-mind-logo.webp"></head>'
    )
    html = html.replace(
        '</style>',
        '.brand{display:flex;align-items:center;gap:10px;letter-spacing:.17em}'
        '.brandLogo{width:42px;height:42px;border-radius:12px;object-fit:cover;box-shadow:0 7px 22px rgba(16,32,30,.14);flex:0 0 auto}'
        '.brandText{font-weight:900;letter-spacing:.17em;font-size:13px;white-space:nowrap}'
        '@media(max-width:760px){.brandLogo{width:36px;height:36px;border-radius:10px}.brandText{font-size:12px;letter-spacing:.13em}}'
        '</style>'
    )
    html = html.replace(
        '<div class="brand">MOVE A MIND</div>',
        '<div class="brand"><img class="brandLogo" src="/move-a-mind-logo.webp" alt="Move A Mind logo"><span class="brandText">MOVE A MIND</span></div>'
    )
    INDEX.write_text(html, encoding='utf-8')

class H(v31.v29.H):
    def do_GET(self):
        p = urlparse(self.path).path
        if p in ('/move-a-mind-logo.webp', '/favicon.ico'):
            b = LOGO_PATH.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type','image/webp')
            self.send_header('Cache-Control','public, max-age=86400')
            self.send_header('Content-Length',str(len(b)))
            self.end_headers(); self.wfile.write(b); return
        # Critical: delegate '/' and every app route to the inherited handler.
        return super().do_GET()

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.2 restore navigation + persistent logo')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), H).serve_forever()
