import os
from http.server import ThreadingHTTPServer

import server_v38 as v38

app = v38.app
INDEX = app.WEB / 'global.html'

# Add a full-screen video gate before the existing application.
html = INDEX.read_text(encoding='utf-8')
intro_css = r'''
<style id="mamIntroStyles">
html.mam-intro-lock,html.mam-intro-lock body{overflow:hidden!important}
#mamIntro{position:fixed;inset:0;z-index:2147483647;background:#000;display:flex;align-items:center;justify-content:center;overflow:hidden}
#mamIntroVideo{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;background:#000}
#mamIntroEnd{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:24px;padding:28px;text-align:center;background:rgba(7,18,17,.38);opacity:0;visibility:hidden;transition:opacity .45s ease}
#mamIntro.ended #mamIntroEnd{opacity:1;visibility:visible}
#mamIntro.ended #mamIntroVideo{filter:brightness(.72)}
#mamEnter{appearance:none;border:1px solid rgba(255,255,255,.55);border-radius:999px;padding:17px 30px;background:#fff;color:#10201e;font:900 17px/1 Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;letter-spacing:.01em;box-shadow:0 12px 40px rgba(0,0,0,.28);cursor:pointer;transform:translateY(8px);transition:.25s}
#mamIntro.ended #mamEnter{transform:translateY(0)}
#mamEnter:hover{transform:translateY(-2px)}
#mamSoundHint{position:absolute;left:50%;bottom:max(22px,env(safe-area-inset-bottom));transform:translateX(-50%);z-index:2;border:1px solid rgba(255,255,255,.45);background:rgba(0,0,0,.42);color:#fff;border-radius:999px;padding:10px 14px;font:700 13px/1.2 Inter,Arial,sans-serif;backdrop-filter:blur(8px);cursor:pointer;display:none}
@media(max-width:760px){#mamIntroVideo{object-fit:cover}#mamEnter{font-size:16px;padding:16px 26px}}
</style>
'''
intro_html = r'''
<div id="mamIntro" role="dialog" aria-label="Move A Mind introduction">
  <video id="mamIntroVideo" autoplay playsinline preload="auto" poster="/move-a-mind-video-poster.jpg">
    <source src="/move-a-mind-animation.mp4" type="video/mp4">
  </video>
  <button id="mamSoundHint" type="button">Tap for sound</button>
  <div id="mamIntroEnd">
    <button id="mamEnter" type="button">Start the challenge →</button>
  </div>
</div>
'''
intro_js = r'''
<script id="mamIntroScript">
(function(){
  var root=document.documentElement, gate=document.getElementById('mamIntro'), video=document.getElementById('mamIntroVideo'), enter=document.getElementById('mamEnter'), sound=document.getElementById('mamSoundHint');
  if(!gate||!video||!enter)return;
  root.classList.add('mam-intro-lock');
  function ended(){gate.classList.add('ended');sound.style.display='none';}
  function tryPlay(){
    video.muted=false;
    var p=video.play();
    if(p&&p.catch)p.catch(function(){video.muted=true;var q=video.play();if(q&&q.then)q.then(function(){sound.style.display='block';}).catch(function(){sound.style.display='block';});});
  }
  video.addEventListener('ended',ended);
  video.addEventListener('error',function(){sound.style.display='none'; ended();});
  sound.addEventListener('click',function(){video.muted=false;video.play().catch(function(){});sound.style.display='none';});
  enter.addEventListener('click',function(){root.classList.remove('mam-intro-lock');gate.remove();window.scrollTo(0,0);});
  tryPlay();
})();
</script>
'''
if 'id="mamIntro"' not in html:
    html = html.replace('</head>', intro_css + '</head>', 1)
    html = html.replace('<body>', '<body>' + intro_html, 1)
    html = html.replace('</body>', intro_js + '</body>', 1)
    INDEX.write_text(html, encoding='utf-8')

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.9 fullscreen intro video gate')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), v38.H).serve_forever()
