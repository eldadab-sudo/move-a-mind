import os
from http.server import ThreadingHTTPServer
import server_v40 as v40
app=v40.app
# Use the Railway persistent volume for session/report storage when available.
try:
    _persistent_data=__import__('pathlib').Path('/persistent/sessions'); _persistent_data.mkdir(parents=True,exist_ok=True); app.DATA=_persistent_data
except Exception: pass
# Restore persisted conversations/reports after a restart so checkout return links remain valid.
try:
    _session_dirs=[app.DATA]
    _persistent=__import__('pathlib').Path('/persistent/sessions')
    try: _persistent.mkdir(parents=True,exist_ok=True); _session_dirs.append(_persistent)
    except Exception: pass
    for _dir in _session_dirs:
        for _p in _dir.glob('*.json'):
            try:
                _s=__import__('json').loads(_p.read_text(encoding='utf-8'))
                if isinstance(_s,dict) and _s.get('id'): app.STORE[_s['id']]=_s
            except Exception: pass
    _base_save=app.save
    def _durable_save(_sid):
        _base_save(_sid)
        try:
            (_persistent/f'{_sid}.json').write_text(__import__('json').dumps(app.STORE[_sid],ensure_ascii=False,indent=2),encoding='utf-8')
        except Exception as _e: print('persistent session save warning',_e)
    app.save=_durable_save
except Exception as _e: print('session restore warning',_e)
INDEX=app.WEB/'global.html'
html=INDEX.read_text(encoding='utf-8')
html=html.replace('<span class="mamStatus mamDone">✓</span>','<span class="mamStatus mamWaiting"></span>')
html=html.replace('<span class="mamStatus mamWorking"></span>','<span class="mamStatus mamWaiting"></span>')
html=html.replace('אנשים נוטים להיות פתוחים יותר לרעיונות חדשים כשהם מרגישים שמקשיבים להם באמת.','<span id="mamTipText">אנשים נוטים להיות פתוחים יותר לרעיונות חדשים כשהם מרגישים שמקשיבים להם באמת.</span>')
html=html.replace('</head>',r'''<style id="mamV426fix">
#result .btn.ghost[data-t="again"],#result> .card>button[data-t="again"]{display:none!important}
.mamPlanCard,.mamPlanCard *{opacity:1!important;filter:none!important;text-shadow:none!important}.mamPlanCard{background:#fff!important;color:#10201e!important}.mamPlanCard .mamPlanName,.mamPlanCard .mamPrice,.mamPlanCard .mamBenefits,.mamPlanCard .mamBenefits li{color:#10201e!important}.mamPlanCard .mamPeriod{color:#5f6c68!important}.mamPlanCard .mamPlanBtn{color:#fff!important;background:#08756b!important}.mamStatus.mamWaiting{background:#fff!important;border:3px solid #dfe4e1!important}.mamStatus.mamWorking{background:#fff!important;border:4px solid #d7e7e2!important;border-top-color:#0a776c!important}.mamStatus.mamDone{background:#0a776c!important;border:0!important;color:#fff!important}
#mamNeedConversation{position:fixed;inset:0;z-index:100000;background:rgba(16,32,30,.52);display:none;align-items:center;justify-content:center;padding:22px}#mamNeedConversation.on{display:flex}.mamNeedBox{width:min(440px,100%);background:#fbfaf7;border-radius:26px;padding:28px;text-align:center;box-shadow:0 24px 70px rgba(16,32,30,.22)}.mamNeedIcon{width:58px;height:58px;border-radius:50%;margin:0 auto 14px;background:#dcebe6;display:grid;place-items:center;font-size:27px}.mamNeedBox h2{font-family:inherit;font-size:27px;letter-spacing:0;margin:0 0 10px}.mamNeedBox p{color:#52605c;line-height:1.6;margin:0 0 20px}.mamNeedBox button{width:100%;border:0;border-radius:15px;padding:14px;background:#0a5f52;color:#fff;font-size:16px;font-weight:900}
@media(max-width:600px){.mamPayGrid{display:grid!important;grid-template-columns:1fr!important;overflow:visible!important}.mamPlanCard{width:100%!important;min-height:0!important;flex:none!important}.mamBenefits{display:block!important;visibility:visible!important}.mamBenefits li{display:list-item!important;visibility:visible!important}}
</style></head>''',1)
html=html.replace('<body>',r'''<body><div id="mamNeedConversation" dir="rtl"><div class="mamNeedBox"><div class="mamNeedIcon">💬</div><h2>עדיין אין מספיק מידע לניתוח מקצועי</h2><p id="mamNeedText">השיחה עדיין קצרה או שטחית מדי כדי להפיק ממנה דוח ותובנות אמינים. המשך את השיחה, התייחס למה שנאמר לך, נסה לקדם את הצד השני והעמק את התגובה.</p><button id="mamBackToConversation">חזרה לשיחה</button></div></div>''',1)
html=html.replace('</body>',r'''<script id="mamProgress426">
(function(){
 const tips=[
 'אנשים נוטים להיות פתוחים יותר לרעיונות חדשים כשהם מרגישים שמקשיבים להם באמת.',
 'שאלה טובה יכולה לקדם שיחה יותר מעוד טיעון. נסו להבין מה באמת חשוב לצד השני.',
 'התנגדות אינה בהכרח סירוב. לעיתים היא סימן לכך שחסר מידע, ביטחון או תחושת הבנה.',
 'לפני שמציעים פתרון, כדאי לבדוק אם הבנתם נכון את הצורך שמאחורי העמדה.',
 'שכנוע אפקטיבי אינו רק מה אומרים — אלא גם מתי, באיזה ניסוח ובתגובה למה שנאמר.',
 'חזרה קצרה על דברי הצד השני יכולה להראות הקשבה ולחשוף אי־הבנות לפני שהן גדלות.',
 'כששיחה נתקעת, שינוי השאלה עשוי להיות יעיל יותר מחזרה על אותו נימוק.',
 'אנשים משתכנעים בקלות רבה יותר כשהפתרון מתחבר למטרה שלהם, לא רק למטרה שלכם.',
 'הסכמה על נקודה קטנה יכולה ליצור בסיס להתקדמות גם כשעדיין קיימת מחלוקת גדולה.',
 'תגובה טובה להתנגדות מתחילה בסקרנות: מה עומד מאחוריה, ומה צריך לקרות כדי להתקדם?',
 'לפעמים הדרך להזיז שיחה קדימה היא להאט: לברר, לשקף ורק אחר כך להציע.',
 'אמון נבנה גם כשלא מסכימים. הכרה עניינית בנקודת המבט של הצד השני יכולה לפתוח אפשרויות חדשות.'
 ];
 const tipEl=document.getElementById('mamTipText');if(tipEl){let last=-1;try{last=Number(sessionStorage.getItem('mamLastTip')??-1)}catch(e){}let idx=Math.floor(Math.random()*tips.length);if(tips.length>1&&idx===last)idx=(idx+1+Math.floor(Math.random()*(tips.length-1)))%tips.length;tipEl.textContent=tips[idx];try{sessionStorage.setItem('mamLastTip',String(idx))}catch(e){}}
 const ov=document.getElementById('mamAnalysisLoading');if(ov){const states=()=>Array.from(ov.querySelectorAll('.mamStatus'));function reset(){states().forEach(s=>{s.className='mamStatus mamWaiting';s.textContent='';});}function done(i){const s=states()[i];if(s){s.className='mamStatus mamDone';s.textContent='✓';}}function working(i){const s=states()[i];if(s){s.className='mamStatus mamWorking';s.textContent='';}}let timers=[];function clearTimers(){timers.forEach(clearTimeout);timers=[];}const observer=new MutationObserver(()=>{if(ov.classList.contains('on')){clearTimers();reset();working(0);timers.push(setTimeout(()=>{done(0);working(1)},900));timers.push(setTimeout(()=>{done(1);working(2)},2300));timers.push(setTimeout(()=>{done(2);working(3)},4200));}else clearTimers();});observer.observe(ov,{attributes:true,attributeFilter:['class']});reset();}
 function removeLegacyRetry(){document.querySelectorAll('#result button[data-t="again"]').forEach(b=>{if(!b.classList.contains('mamRetry'))b.remove();});}removeLegacyRetry();new MutationObserver(removeLegacyRetry).observe(document.getElementById('result')||document.body,{childList:true,subtree:true});
 function conversationIsSubstantial(){const user=Array.from(document.querySelectorAll('#chat .msg.me')).map(x=>(x.textContent||'').trim()).filter(Boolean);const ai=Array.from(document.querySelectorAll('#chat .msg.ai')).map(x=>(x.textContent||'').trim()).filter(Boolean);const all=user.concat(ai).join(' ');const userWords=user.join(' ').split(/\s+/).filter(Boolean);const allWords=all.split(/\s+/).filter(Boolean);const meaningful=user.filter(x=>x.length>=12);const unique=new Set(allWords.map(w=>w.replace(/[^\p{L}\p{N}]/gu,'').toLowerCase()).filter(w=>w.length>1));/* A completed exchange is analyzable even when the participant is concise. Do not force artificial extra turns after a clear agreement/closure. */return (user.length>=4&&ai.length>=4&&all.length>=180&&unique.size>=18)||(user.length>=3&&ai.length>=3&&userWords.length>=18&&meaningful.length>=2&&unique.size>=16);}
 const finish=document.getElementById('finishBtn'),modal=document.getElementById('mamNeedConversation'),back=document.getElementById('mamBackToConversation');
 if(finish){finish.addEventListener('click',function(e){if(!conversationIsSubstantial()){e.preventDefault();e.stopImmediatePropagation();modal?.classList.add('on');}},true);}
 if(back)back.onclick=()=>modal.classList.remove('on');
})();
</script><script id="mamCheckoutState432">
(function(){
 const KEY='mam_checkout_state_v2';
 function getSid(){try{return localStorage.getItem('mam_sid')||''}catch(e){return ''}}
 function save(){try{localStorage.setItem(KEY,JSON.stringify({sid:getSid(),savedAt:Date.now()}))}catch(e){}}
 document.addEventListener('click',e=>{if(e.target.closest('.mamPlanBtn'))save()},true);
 window.addEventListener('pagehide',save);
 async function restoreCancel(){
   const u=new URLSearchParams(location.search);if(u.get('stripe')!=='cancel')return;
   let st={};try{st=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
   const keep=u.get('sid')||st.sid||getSid();if(!keep)return;
   try{localStorage.setItem('mam_sid',keep)}catch(e){}
   try{
     const r=await fetch('/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:keep,reflection:{},lang:(localStorage.getItem('mam_lang')||'he')})});
     const j=await r.json();if(!r.ok)throw Error('restore');
     sid=keep;lastReport=j;
     $('#score').textContent=j.performance_score??j.preview?.performance_score??'—';$('#outcome').textContent=j.outcome||j.preview?.outcome||'';$('#notice').textContent=j.alpha_notice||'';
     $('#freeInsight').innerHTML='';$('#fullReport').innerHTML='';if(j.locked)renderLocked(j);else renderFull(j);go('result');history.replaceState({},'',location.pathname);
   }catch(e){}
 }
 window.addEventListener('load',()=>setTimeout(restoreCancel,180));
})();
</script></body>''',1)
INDEX.write_text(html,encoding='utf-8')
class H(v40.H):
    def end_headers(self):
        self.send_header('Cache-Control','no-store, no-cache, must-revalidate, max-age=0');self.send_header('Pragma','no-cache');self.send_header('Expires','0');super().end_headers()
if __name__=='__main__':
    os.chdir(app.ROOT);print('Move A Mind v4.40 - completion-aware analysis gate');ThreadingHTTPServer(('0.0.0.0',app.PORT),H).serve_forever()
