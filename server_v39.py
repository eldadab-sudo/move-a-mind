import os
import re
from http.server import ThreadingHTTPServer

import server_v38 as v38

app = v38.app
INDEX = app.WEB / 'global.html'
html = INDEX.read_text(encoding='utf-8')

# The film belongs only to the opening gate. Remove older homepage video embeds.
html = re.sub(r'<video\b[^>]*>.*?</video>', '', html, flags=re.I | re.S)

# Opening video is rendered by web/global.html. Do not inject a second legacy intro gate.
INDEX.write_text(html, encoding='utf-8')

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.11 autoplay audio fallback control')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), v38.H).serve_forever()
