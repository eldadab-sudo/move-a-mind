import os
from http.server import ThreadingHTTPServer

import server_v38 as v38

app = v38.app

# The approved V8 launch video is part of web/global.html and must remain there.
# Do not rewrite global.html during startup.

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.11 approved launch video preserved')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), v38.H).serve_forever()
