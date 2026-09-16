import os
from http.server import ThreadingHTTPServer
import server_v40 as v40
app=v40.app
INDEX=app.WEB/'global.html'
html=INDEX.read_text(encoding='utf-8')
html=html.replace('<span class="mamStatus mamDone">✓</span>','<span class="mamStatus mamWaiting"></span>')
html=html.replace('<span class="mamStatus mamWorking"></span>','<span class="mamStatus mamWaiting"></span>')
html=html.replace('</head>',r'''<style id="mamV425fix">
#result .btn.ghost[data-t="again"],#result> .card>button[data-t="again"]{display:none!important}
.mamPlanCard,.mamPlanCard *{opacity:1!important;filter:none!important;text-shadow:none!important}.mamPlanCard{background:#fff!important;color:#10201e!important}.mamPlanCard .mamPlanName,.mamPlanCard .mamPrice,.mamPlanCard .mamBenefits,.mamPlanCard .mamBenefits li{color:#10201e!important}.mamPlanCard .mamPeriod{color:#5f6c68!important}.mamPlanCard .mamPlanBtn{color:#fff!important;background:#08756b!important}.mamStatus.mamWaiting{background:#fff!important;border:3px solid #dfe4e1!important}.mamStatus.mamWorking{background:#fff!important;border:4px solid #d7e7e2!important;border-top-color:#0a776c!important}.mamStatus.mamDone{background:#0a776c!important;border:0!important;color:#fff!important}
#mamNeedConversation{position:fixed;inset:0;z-index:100000;background:rgba(16,32,30,.52);display:none;align-items:center;justify-content:center;padding:22px}#mamNeedConversation.on{display:flex}.mamNeedBox{width:min(440px,100%);background:#fbfaf7;border-radius:26px;padding:28px;text-align:center;box-shadow:0 24px 70px rgba(16,32,30,.22)}.mamNeedIcon{width:58px;height:58px;border-radius:50%;margin:0 auto 14px;background:#dcebe6;display:grid;place-items:center;font-size:27px}.mamNeedBox h2{font-family:inherit;font-size:27px;letter-spacing:0;margin:0 0 10px}.mamNeedBox p{color:#52605c;line-height:1.6;margin:0 0 20px}.mamNeedBox button{width:100%;border:0;border-radius:15px;padding:14px;background:#0a5f52;color:#fff;font-size:16px;font-weight:900}
@media(max-width:600px){.mamPayGrid{display:grid!important;grid-template-columns:1fr!important;overflow:visible!important}.mamPlanCard{width:100%!important;min-height:0!important;flex:none!important}.mamBenefits{display:block!important;visibility:visible!important}.mamBenefits li{display:list-item!important;visibility:visible!important}}
</style></head>''',1)
html=html.replace('<body>',r'''<body><div id="mamNeedConversation" dir="rtl"><div class="mamNeedBox"><div class="mamNeedIcon">💬</div><h2>עדיין אין מספיק מידע לניתוח</h2><p>כדי לקבל תובנות והמלצות, יש לנהל שיחה קצרה בתרחיש לפני סיום השיחה.</p><button id="mamBackToConversation">חזרה לשיחה</button></div></div>''',1)
html=html.replace('</body>',r'''<script id="mamProgress425">
(function(){
 const ov=document.getElementById('mamAnalysisLoading');if(ov){const states=()=>Array.from(ov.querySelectorAll('.mamStatus'));function reset(){states().forEach(s=>{s.className='mamStatus mamWaiting';s.textContent='';});}function done(i){const s=states()[i];if(s){s.className='mamStatus mamDone';s.textContent='✓';}}function working(i){const s=states()[i];if(s){s.className='mamStatus mamWorking';s.textContent='';}}let timers=[];function clearTimers(){timers.forEach(clearTimeout);timers=[];}const observer=new MutationObserver(()=>{if(ov.classList.contains('on')){clearTimers();reset();working(0);timers.push(setTimeout(()=>{done(0);working(1)},900));timers.push(setTimeout(()=>{done(1);working(2)},2300));timers.push(setTimeout(()=>{done(2);working(3)},4200));}else clearTimers();});observer.observe(ov,{attributes:true,attributeFilter:['class']});reset();}
 function removeLegacyRetry(){document.querySelectorAll('#result button[data-t="again"]').forEach(b=>{if(!b.classList.contains('mamRetry'))b.remove();});}removeLegacyRetry();new MutationObserver(removeLegacyRetry).observe(document.getElementById('result')||document.body,{childList:true,subtree:true});
 // A valid conversation requires at least one actual user message. The scenario's opening AI message alone does not count.
 const finish=document.getElementById('finishBtn'),modal=document.getElementById('mamNeedConversation'),back=document.getElementById('mamBackToConversation');
 if(finish){finish.addEventListener('click',function(e){const userTurns=document.querySelectorAll('#chat .msg.me').length;if(userTurns<1){e.preventDefault();e.stopImmediatePropagation();modal?.classList.add('on');}},true);}
 if(back)back.onclick=()=>modal.classList.remove('on');
})();
</script></body>''',1)
INDEX.write_text(html,encoding='utf-8')
class H(v40.H):
    def end_headers(self):
        self.send_header('Cache-Control','no-store, no-cache, must-revalidate, max-age=0');self.send_header('Pragma','no-cache');self.send_header('Expires','0');super().end_headers()
if __name__=='__main__':
    os.chdir(app.ROOT);print('Move A Mind v4.25 - empty conversation analysis blocked');ThreadingHTTPServer(('0.0.0.0',app.PORT),H).serve_forever()
