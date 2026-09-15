import os
from http.server import ThreadingHTTPServer
import server_v36 as v36

app = v36.app
INDEX = app.WEB / 'global.html'

html = INDEX.read_text(encoding='utf-8')
replacements = {
    'ולפעמים להבין מתי נכון לא לדחוף.': 'ולפעמים לזהות את האינטרס שמאחורי העמדה — ומשם לפתוח אפשרות חדשה.',
    'ולפעמים להבין מתי נכון שלא לדחוף.': 'ולפעמים לזהות את האינטרס שמאחורי העמדה — ומשם לפתוח אפשרות חדשה.',
    'Sometimes knowing when not to push.': 'Sometimes identifying the interest behind the position — and opening a new possibility from there.',
}
for old, new in replacements.items():
    html = html.replace(old, new)
INDEX.write_text(html, encoding='utf-8')

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.6 negotiation-principle landing copy')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), v36.H).serve_forever()
