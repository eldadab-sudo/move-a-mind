import os
from http.server import ThreadingHTTPServer
import server_v40 as v40
app=v40.app
INDEX=app.WEB/'global.html'
html=INDEX.read_text(encoding='utf-8')
# Make every analysis step start empty; JS fills them progressively.
html=html.replace('<span class="mamStatus mamDone">✓</span>','<span class="mamStatus mamWaiting"></span>')
html=html.replace('<span class="mamStatus mamWorking"></span>','<span class="mamStatus mamWaiting"></span>')
# Payment cards and progress-state visuals. Hide any legacy/base result retry button;
# the only retry control allowed is .mamRetry inside the payment panel.
html=html.replace('</head>',r'''<style id="mamV424fix">
#result .btn.ghost[data-t="again"],#result> .card>button[data-t="again"]{display:none!important}
.mamPlanCard,.mamPlanCard *{opacity:1!important;filter:none!important;text-shadow:none!important}
.mamPlanCard{background:#fff!important;color:#10201e!important}
.mamPlanCard .mamPlanName,.mamPlanCard .mamPrice,.mamPlanCard .mamBenefits,.mamPlanCard .mamBenefits li{color:#10201e!important}
.mamPlanCard .mamPeriod{color:#5f6c68!important}
.mamPlanCard .mamPlanBtn{color:#fff!important;background:#08756b!important}
.mamStatus.mamWaiting{background:#fff!important;border:3px solid #dfe4e1!important}
.mamStatus.mamWorking{background:#fff!important;border:4px solid #d7e7e2!important;border-top-color:#0a776c!important}
.mamStatus.mamDone{background:#0a776c!important;border:0!important;color:#fff!important}
@media(max-width:600px){.mamPayGrid{display:grid!important;grid-template-columns:1fr!important;overflow:visible!important}.mamPlanCard{width:100%!important;min-height:0!important;flex:none!important}.mamBenefits{display:block!important;visibility:visible!important}.mamBenefits li{display:list-item!important;visibility:visible!important}}
</style></head>''',1)
html=html.replace('</body>',r'''<script id="mamProgress424">
(function(){
 const ov=document.getElementById('mamAnalysisLoading');
 if(ov){
  const states=()=>Array.from(ov.querySelectorAll('.mamStatus'));
  function reset(){states().forEach(s=>{s.className='mamStatus mamWaiting';s.textContent='';});}
  function done(i){const s=states()[i];if(s){s.className='mamStatus mamDone';s.textContent='✓';}}
  function working(i){const s=states()[i];if(s){s.className='mamStatus mamWorking';s.textContent='';}}
  let timers=[];function clearTimers(){timers.forEach(clearTimeout);timers=[];}
  const observer=new MutationObserver(()=>{if(ov.classList.contains('on')){clearTimers();reset();working(0);timers.push(setTimeout(()=>{done(0);working(1)},900));timers.push(setTimeout(()=>{done(1);working(2)},2300));timers.push(setTimeout(()=>{done(2);working(3)},4200));}else clearTimers();});
  observer.observe(ov,{attributes:true,attributeFilter:['class']});reset();
 }
 // Remove legacy duplicate even if its markup/copy changes or is translated at runtime.
 function removeLegacyRetry(){document.querySelectorAll('#result button[data-t="again"]').forEach(b=>{if(!b.classList.contains('mamRetry'))b.remove();});}
 removeLegacyRetry();new MutationObserver(removeLegacyRetry).observe(document.getElementById('result')||document.body,{childList:true,subtree:true});
})();
</script></body>''',1)
INDEX.write_text(html,encoding='utf-8')
class H(v40.H):
    def end_headers(self):
        self.send_header('Cache-Control','no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma','no-cache')
        self.send_header('Expires','0')
        super().end_headers()
if __name__=='__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.24 - duplicate retry removed by selector')
    ThreadingHTTPServer(('0.0.0.0',app.PORT),H).serve_forever()
