import os
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse
import server_v41 as v41
import server_v21 as v21

app = v41.app


def grounded_prompt(sc, track, turn, messages):
    lens = v21.v20.EXPERT_LENSES.get(track, '')
    recent = messages[-8:]
    transcript = '\n'.join(('משתמש' if m.get('role') == 'user' else sc.get('character','הדמות')) + ': ' + (m.get('content') or '') for m in recent)
    return app.GLOBAL + f'''\n\n