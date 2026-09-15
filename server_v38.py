import os
from http.server import ThreadingHTTPServer

import server_v37 as v37

app = v37.app

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.7 homepage video')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), v37.v36.H).serve_forever()
