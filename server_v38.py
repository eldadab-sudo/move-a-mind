import os
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

import server_v37 as v37

app = v37.app


class H(v37.v36.H):
    STATIC = {
        '/move-a-mind-animation.mp4': (app.WEB / 'move-a-mind-animation.mp4', 'video/mp4'),
        '/move-a-mind-video-poster.jpg': (app.WEB / 'move-a-mind-video-poster.jpg', 'image/jpeg'),
    }

    def do_GET(self):
        item = self.STATIC.get(urlparse(self.path).path)
        if not item:
            return super().do_GET()

        path, content_type = item
        if not path.exists():
            self.send_error(404)
            return

        size = path.stat().st_size
        start, end = 0, size - 1
        range_header = self.headers.get('Range', '')
        partial = range_header.startswith('bytes=')
        if partial:
            try:
                bounds = range_header[6:].split(',', 1)[0].split('-', 1)
                if bounds[0]:
                    start = int(bounds[0])
                if bounds[1]:
                    end = min(int(bounds[1]), size - 1)
                if start < 0 or start > end or start >= size:
                    raise ValueError
            except ValueError:
                self.send_response(416)
                self.send_header('Content-Range', f'bytes */{size}')
                self.end_headers()
                return

        length = end - start + 1
        self.send_response(206 if partial else 200)
        self.send_header('Content-Type', content_type)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Cache-Control', 'public, max-age=3600')
        self.send_header('Content-Length', str(length))
        if partial:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        with path.open('rb') as source:
            source.seek(start)
            remaining = length
            while remaining:
                chunk = source.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.8 video delivery fix - redeploy trigger')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), H).serve_forever()
