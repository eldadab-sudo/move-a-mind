import os
from urllib.parse import urlparse
from http.server import ThreadingHTTPServer
import server_v35 as v35
import server_v21 as v21

app = v35.app

class H(v35.v34.v33.H):
    def do_POST(self):
        p = urlparse(self.path).path
        if p == '/api/chat':
            try:
                body = self._body()
            except Exception:
                return self._json({'error':'bad request'},400)
            sid = body.get('session_id')
            text = (body.get('message') or '').strip()
            lang = body.get('lang','he')
            if sid not in app.STORE or not text:
                return self._json({'error':'invalid session'},400)
            s = app.STORE[sid]
            if s.get('status') != 'active':
                return self._json({'error':'conversation ended'},400)
            s['turn'] += 1
            sc = v21.session_scenario(s)
            s['messages'].append({'role':'user','content':text})
            ans = app.ai(v21.scenario_prompt(sc,s['track'],s['turn']),s['messages']) or app.fallback(s['track'],s['turn'])
            # Conversation remains active until the user explicitly finishes.
            ans = (ans or '').replace('[END]','').strip()
            s['messages'].append({'role':'assistant','content':ans})
            s['status'] = 'active'
            app.save(sid)
            return self._json({'message':v21.maybe_translate_reply(ans,lang),'ended':False,'turn':s['turn']})
        return super().do_POST()

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.5 user-controlled conversation length')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), H).serve_forever()
