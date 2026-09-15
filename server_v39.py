import os
import re
from http.server import ThreadingHTTPServer

import server_v38 as v38

app = v38.app
INDEX = app.WEB / 'global.html'

html = INDEX.read_text(encoding='utf-8')

# The film belongs only to the opening gate. Remove older homepage video embeds.
html = re.sub(r'<video\b[^>]*>.*?</video>', '', html, flags=re.I | re.S)

intro_css = r'''
<style id="mamIntroStyles">
html.mam-intro-lock,html.mam-intro-lock body{overflow:hidden!important;background:#031322!important}
#mamIntro{position:fixed;inset:0;z-index:2147483647;background:#031322;display:flex;align-items:center;justify-content:center;overflow:hidden}
#mamIntro:after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(180deg,rgba(1,8,16,.06),rgba(1,8,16,.16));box-shadow:inset 0 0 120px rgba(0,0,0,.24)}
#mamIntroVideo{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;background:#031322}
#mamIntroEnd{position:absolute;inset:0;z-index:3;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:24px;padding:28px;text-align:center;background:radial-gradient(circle at 50% 45%,rgba(9,44,91,.10),rgba(3,19,34,.60));opacity:0;visibility:hidden;transition:opacity .55s ease}
#mamIntro.ended #mamIntroEnd{opacity:1;visibility:visible}
#mamIntro.ended #mamIntroVideo{filter:brightness(.64) saturate(1.08);transform:scale(1.01);transition:filter .55s ease,transform 2s ease}
#mamEnter{appearance:none;border:1px solid rgba(255,255,255,.65);border-radius:999px;padding:18px 32px;background:#fff;color:#071f32;font:900 17px/1 Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;letter-spacing:.01em;box-shadow:0 16px 50px rgba(0,0,0,.34);cursor:pointer;transform:translateY(10px) scale(.98);transition:.28s}
#mamIntro.ended #mamEnter{transform:translateY(0) scale(1)}
#mamEnter:hover{transform:translateY(-2px) scale(1.015)}
@media(max-width:760px){#mamIntroVideo{object-fit:cover}#mamEnter{font-size:16px;padding:17px 27px}}
</style>
'''
intro_html = r'''
<div id="mamIntro" role="dialog" aria-label="Move A Mind introduction">
  <video id="mamIntroVideo" autoplay playsinline preload="auto" poster="/move-a-mind-video-poster.jpg">
    <source src="/move-a-mind-animation.mp4" type="video/mp4">
  </video>
  <div id="mamIntroEnd">
    <button id="mamEnter" type="button">Start the challenge →</button>
  </div>
</div>
'''
intro_js = r'''
<script id="mamIntroScript">
(function(){
  var root=document.documentElement, gate=document.getElementById('mamIntro'), video=document.getElementById('mamIntroVideo'), enter=document.getElementById('mamEnter');
  if(!gate||!video||!enter)return;
  root.classList.add('mam-intro-lock');
  function ended(){gate.classList.add('ended');}
  function tryPlay(){
    video.defaultMuted=false; video.muted=false; video.volume=1;
    var p=video.play();
    if(p&&p.catch)p.catch(function(){video.muted=true;video.play().catch(ended);});
  }
  video.addEventListener('ended',ended);
  video.addEventListener('error',ended);
  enter.addEventListener('click',function(){root.classList.remove('mam-intro-lock');gate.remove();window.scrollTo(0,0);});
  tryPlay();
})();
</script>
'''
html = html.replace('</head>', intro_css + '</head>', 1)
html = html.replace('<body>', '<body>' + intro_html, 1)
html = html.replace('</body>', intro_js + '</body>', 1)
INDEX.write_text(html, encoding='utf-8')

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.10 polished intro, duplicate homepage video removed')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), v38.H).serve_forever()
