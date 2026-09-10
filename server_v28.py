import os
from http.server import ThreadingHTTPServer
import server_v27 as v27

app = v27.app

index_path = app.WEB / 'global.html'
html = index_path.read_text(encoding='utf-8')

patch = r'''
<style>
#subdomains .domain span{display:none!important}
#subdomains .domain>div:first-child{display:flex;align-items:center;min-height:34px}
</style>
<script>
window.addEventListener('load',()=>{
  const refineTopicScreen=()=>{
    const he=(document.documentElement.lang||'').toLowerCase().startsWith('he');
    const step=document.querySelector('#subStep');
    const h=document.querySelector('#subH');
    const p=document.querySelector('#subP');
    if(step) step.textContent=he?'בחר את האתגר שלך':'Choose your challenge';
    if(h) h.textContent=he?'על מה נדבר?':'What should we talk about?';
    if(p) p.textContent=he?'בחר את השיחה שבה היית רוצה להיות חד יותר — ואנחנו נכניס אותך ישר לסיטואציה.':'Choose the conversation you want to handle better — and we’ll put you straight into the situation.';
    document.querySelectorAll('#subdomains .domain span').forEach(s=>s.remove());
  };
  refineTopicScreen();
  const box=document.querySelector('#subdomains');
  if(box){
    const obs=new MutationObserver(refineTopicScreen);
    obs.observe(box,{childList:true,subtree:true});
  }
  const screen=document.querySelector('#subchoose');
  if(screen){
    const obs2=new MutationObserver(refineTopicScreen);
    obs2.observe(screen,{attributes:true,childList:true,subtree:false});
  }
});
</script>
'''

html = html.replace('</body>', patch + '</body>')
index_path.write_text(html, encoding='utf-8')

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v3.7 clean topic selection')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), v27.v26.v25.v24.H).serve_forever()
