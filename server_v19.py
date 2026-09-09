import os
import server_v18 as v18
from http.server import ThreadingHTTPServer

app = v18.app

index_path = app.WEB / 'index.html'
html = index_path.read_text(encoding='utf-8')
html = html.replace('התחל סימולציה','התחל')
html = html.replace('בדוק אותי','התחל')
html = html.replace('הצג תרחיש והתחל','התחל')
index_path.write_text(html, encoding='utf-8')

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v2.3 start button label')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), v18.H).serve_forever()
