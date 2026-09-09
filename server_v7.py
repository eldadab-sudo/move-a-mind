import os, json, datetime
import server_v6 as v6
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

app = v6.app

class H(app.H):
    def do_GET(self):
        p = urlparse(self.path).path
        if p in ('/feedback', '/feedback/'):
            f = app.WEB / 'feedback.html'
            if not f.exists():
                return self._json({'error':'טופס המשוב לא נמצא'},404)
            b = f.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        return super().do_GET()

    def do_POST(self):
        p = urlparse(self.path).path
        if p == '/api/feedback':
            try:
                body = self._body()
            except Exception:
                return self._json({'error':'בקשה לא תקינה'},400)

            required = ['track','realism','difficulty','naturalness','length_fit','responsiveness','ending','try_again','best','change','overall']
            missing = [k for k in required if not str(body.get(k,'')).strip()]
            if missing:
                return self._json({'error':'חסרים שדות חובה','missing':missing},400)

            record = {
                'created_at': datetime.datetime.utcnow().isoformat()+'Z',
                'name': str(body.get('name','')).strip()[:120],
                'track': str(body.get('track','')).strip()[:120],
                'realism': str(body.get('realism','')).strip()[:3],
                'difficulty': str(body.get('difficulty','')).strip()[:3],
                'naturalness': str(body.get('naturalness','')).strip()[:3],
                'length_fit': str(body.get('length_fit','')).strip()[:50],
                'responsiveness': str(body.get('responsiveness','')).strip()[:3],
                'ending': str(body.get('ending','')).strip()[:50],
                'try_again': str(body.get('try_again','')).strip()[:50],
                'best': str(body.get('best','')).strip()[:2000],
                'change': str(body.get('change','')).strip()[:2000],
                'scenario_idea': str(body.get('scenario_idea','')).strip()[:2000],
                'overall': str(body.get('overall','')).strip()[:3],
            }
            feedback_file = app.DATA / 'pilot_feedback.jsonl'
            with feedback_file.open('a', encoding='utf-8') as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + '\n')
            return self._json({'ok':True})

        return super().do_POST()

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v1.1 + feedback fix')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), H).serve_forever()
