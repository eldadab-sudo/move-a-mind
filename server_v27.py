import os
from http.server import ThreadingHTTPServer
import server_v26 as v26

app = v26.app

# The subdomain screen itself is injected dynamically by server_v24.H.
# Add a late-running UI patch so the injected screen has no redundant Start CTA:
# selecting a subdomain opens the scenario immediately.
index_path = app.WEB / 'global.html'
html = index_path.read_text(encoding='utf-8')

patch = r'''
<style>
#subchoose .bottomAction{display:none!important}
#subchoose #subStart{display:none!important}
</style>
<script>
window.addEventListener('load',()=>{
  const applySubCopy=()=>{
    const he=(document.documentElement.lang||'').toLowerCase().startsWith('he');
    const h=document.querySelector('#subH');
    const p=document.querySelector('#subP');
    const step=document.querySelector('#subStep');
    if(h) h.textContent=he?'על מה נדבר?':'What should we talk about?';
    if(p) p.textContent=he?'בחר את נושא השיחה. מכאן נפתח תרחיש ממוקד ומציאותי שמתאים בדיוק לבחירה שלך.':'Choose the conversation topic. We’ll open a focused, realistic scenario tailored precisely to your choice.';
    if(step) step.textContent=he?'בחר נושא שיחה':'Choose a conversation topic';
  };
  applySubCopy();
  const box=document.querySelector('#subdomains');
  if(box){
    box.addEventListener('click',(e)=>{
      const card=e.target.closest('.domain');
      if(!card) return;
      setTimeout(()=>{
        applySubCopy();
        if(typeof startPrecise==='function' && chosenSub){ startPrecise(); }
      },0);
    });
  }
  const obs=new MutationObserver(applySubCopy);
  const screen=document.querySelector('#subchoose');
  if(screen) obs.observe(screen,{attributes:true,childList:true,subtree:false});
});
</script>
'''

html = html.replace('</body>', patch + '</body>')
index_path.write_text(html, encoding='utf-8')

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v3.6 direct topic selection')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), v26.v25.v24.H).serve_forever()
