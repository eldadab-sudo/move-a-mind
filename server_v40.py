import os,json,time,hmac,hashlib,urllib.parse,urllib.request,urllib.error
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse
import server_v39 as v39
import server_v21 as v21
app=v39.app
PLANS={'deep':('STRIPE_PRICE_DEEP','payment'),'monthly':('STRIPE_PRICE_MONTHLY','subscription'),'annual':('STRIPE_PRICE_ANNUAL','subscription')}
INDEX=app.WEB/'global.html';html=INDEX.read_text(encoding='utf-8')
html=html.replace("onclick=\"location.href='/'\" data-t=\"again\"","onclick=\"chosen=null;sid=null;renderDomains();go('choose')\" data-t=\"again\"")
css=r'''<style id="mamV421">#mamAnalysisLoading{position:fixed;inset:0;z-index:99999;background:linear-gradient(160deg,#fbfaf6,#f2efe7);display:none;overflow:auto;padding:22px 18px;color:#10201e}#mamAnalysisLoading.on{display:block}.mamLoadWrap{max-width:560px;margin:0 auto;text-align:center}.mamFacesRing{width:164px;height:164px;border:3px solid #bdd0ca;border-radius:50%;margin:16px auto 18px;position:relative;display:grid;place-items:center}.mamFacesRing:before,.mamFacesRing:after{content:'➤';position:absolute;color:#075d55;font-size:24px}.mamFacesRing:before{right:-2px;top:23px;transform:rotate(35deg)}.mamFacesRing:after{left:-2px;bottom:23px;transform:rotate(215deg)}.mamFacesCrop{width:112px;height:112px;border-radius:50%;overflow:hidden;background:#0d2926;position:relative;animation:mamFacesSpin 2.2s linear infinite}.mamFacesCrop img{position:absolute;width:165px;height:165px;max-width:none;left:50%;top:-5px;transform:translateX(-50%);object-fit:cover;object-position:center top}.mamLoadTitle{font-size:38px;font-weight:900;margin:8px 0 6px}.mamLoadText{font-size:18px;line-height:1.5;color:#1d5f58;margin:0 auto 22px;max-width:480px}.mamSteps{background:rgba(255,255,255,.82);border:1px solid #d8ddd9;border-radius:25px;padding:6px 24px;text-align:right;box-shadow:0 14px 38px rgba(20,45,40,.06)}.mamStep{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:16px 0;border-bottom:1px solid #e4e7e3;font-size:17px}.mamStep:last-child{border:0}.mamStatus{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;flex:0 0 34px}.mamDone{background:#0a776c;color:#fff;font-size:22px}.mamWorking{border:4px solid #d7e7e2;border-top-color:#0a776c;animation:mamFacesSpin .9s linear infinite}.mamWaiting{background:#e8e9e7}.mamTip{margin-top:20px;background:#e4efeb;border-radius:24px;padding:20px 24px;text-align:right;color:#205a53;font-size:16px;line-height:1.55}.mamTip b{display:block;font-size:18px;margin-bottom:5px}.mamTime{margin:22px 0;color:#777;font-size:15px}.premium{background:#fbfaf7!important;color:#10201e!important;border:1px solid #d9ddd8!important}.premium p{color:#3f4a46!important}.mamPayGrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:18px}.mamPlanCard{position:relative;background:#fff;color:#10201e;border:1px solid #d9ddd9;border-radius:18px;padding:18px 12px;display:flex;flex-direction:column;min-width:0;min-height:310px;overflow:hidden}.mamPlanCard.best{border-color:#8cc9b8}.mamBadge{background:#ccefe3;color:#075d55;border-radius:8px;padding:4px 7px;font-size:12px;font-weight:800;margin:-10px 0 8px}.mamPlanName{font-weight:900;font-size:18px;direction:ltr}.mamPrice{font-size:34px;font-weight:900;margin:7px 0 0;direction:ltr}.mamPeriod{font-size:13px;color:#5f6c68;direction:ltr}.mamBenefits{list-style:none;padding:0;margin:16px 0;text-align:right;line-height:1.8;font-size:14px;flex:1;color:#20302d}.mamBenefits li:before{content:'✓';color:#08756b;font-weight:900;margin-left:7px}.mamPlanBtn{width:100%;border:0;border-radius:12px;padding:12px;background:#08756b;color:#fff;font-weight:900;font-size:16px}.mamLockedPanel{border:1px solid #d9ddd9;border-radius:22px;padding:28px 18px;background:#fff;margin:16px 0;text-align:center}.mamLock{font-size:38px}.mamFeatureRow{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;text-align:center;margin:20px 0;color:#174e49}.mamFeatureIcon{font-size:32px}.mamRetry{margin-top:12px;width:100%;border:1px solid #0a5f57;border-radius:30px;background:transparent;padding:13px;font-weight:800;color:#183b38}@keyframes mamFacesSpin{to{transform:rotate(360deg)}}@media(max-width:600px){.mamLoadTitle{font-size:32px}.premium{padding:18px!important;margin-left:-8px!important;margin-right:-8px!important}.mamPayGrid{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;gap:12px;padding:4px 2px 12px}.mamPlanCard{flex:0 0 82%;scroll-snap-align:center;min-height:340px}.mamFeatureRow{font-size:13px}.mamFacesRing{width:148px;height:148px}.mamFacesCrop{width:100px;height:100px}.mamFacesCrop img{width:150px;height:150px}}</style>'''
loader=r'''<div id="mamAnalysisLoading" dir="rtl"><div class="mamLoadWrap"><div class="mamFacesRing"><div class="mamFacesCrop"><img src="/move-a-mind-logo.webp" alt="Move A Mind"></div></div><div class="mamLoadTitle">מנתחים את השיחה שלך...</div><div class="mamLoadText">אנחנו מעבדים את תוכן השיחה, מזהים דפוסים ומכינים עבורך תובנות מעשיות.</div><div class="mamSteps"><div class="mamStep"><span>מעבדים את תוכן השיחה</span><span class="mamStatus mamDone">✓</span></div><div class="mamStep"><span>מזהים דפוסים והתנהגויות</span><span class="mamStatus mamDone">✓</span></div><div class="mamStep"><span>מנתחים אסטרטגיות השפעה</span><span class="mamStatus mamWorking"></span></div><div class="mamStep"><span>מכינים את התובנות שלך</span><span class="mamStatus mamWaiting"></span></div></div><div class="mamTip"><b>💡 טיפ בינתיים:</b>אנשים נוטים להיות פתוחים יותר לרעיונות חדשים כשהם מרגישים שמקשיבים להם באמת.</div><div class="mamTime">◷ זה בדרך כלל לוקח 20–40 שניות...</div></div></div>'''
html=html.replace('</head>',css+'</head>',1).replace('<body>','<body>'+loader,1)
start=html.find('function renderLocked(j){');end=html.find("$('#scoreBtn').onclick",start)
if start>=0 and end>start:
 pay=r'''function renderLocked(j){const p=j.preview||j,he=lang==='he';$('#outcome').textContent='';$('#freeInsight').innerHTML=`<div class="insight"><h3>${he?'טעימה מהניתוח שלך':'A glimpse of your analysis'}</h3><p>${p.top_insight||''}</p></div>`;$('#fullReport').innerHTML=`<div class="mamLockedPanel"><div class="mamLock">🔒</div><h2>${he?'לקבלת הדוח המלא':'Get your full report'}</h2><p>${he?'נשארה רק טעימה מהניתוח. כדי לגלות את כל התובנות, נקודות המפנה וההמלצות המעשיות לשיחה הבאה — בחר את המסלול שמתאים לך.':'You have seen a preview. Choose the plan that fits you to unlock every insight, turning point and practical recommendation.'}</p></div>`;const box=$('#paywall');box.style.display='block';box.innerHTML=`<div class="premium" dir="${he?'rtl':'ltr'}"><h2 style="font-size:30px;line-height:1.15;margin:4px 0 8px">${he?'בחר את הדרך שלך לדוח המלא':'Choose your path to the full report'}</h2><p style="font-size:16px;line-height:1.55">${he?'הדוח המלא כבר מוכן. בחר מסלול והמשך מיד לתובנות המלאות.':'Your full report is ready. Choose a plan and unlock it now.'}</p><input id="mamEmail" class="checkoutEmail" type="email" placeholder="Email" autocomplete="email"><div class="mamPayGrid"><div class="mamPlanCard"><div class="mamPlanName">Deep Report</div><div class="mamPrice">$4.90</div><div class="mamPeriod">${he?'דוח חד־פעמי':'one-time'}</div><ul class="mamBenefits"><li>${he?'הדוח המלא לשיחה הזו':'Full report for this conversation'}</li><li>${he?'כל התובנות וההמלצות':'All insights and recommendations'}</li><li>${he?'גישה מיידית':'Immediate access'}</li><li>${he?'ללא התחייבות':'No commitment'}</li></ul><button class="mamPlanBtn" data-plan="deep">${he?'בחר מסלול':'Choose plan'}</button></div><div class="mamPlanCard"><div class="mamPlanName">Pro Monthly</div><div class="mamPrice">$15</div><div class="mamPeriod">/month</div><ul class="mamBenefits"><li>${he?'גישה מלאה לחודש':'Full access for a month'}</li><li>${he?'כל הדוחות והכלים':'All reports and tools'}</li><li>${he?'עדכונים ושיפורים':'Updates and improvements'}</li><li>${he?'ביטול בכל עת':'Cancel anytime'}</li></ul><button class="mamPlanBtn" data-plan="monthly">${he?'בחר מסלול':'Choose plan'}</button></div><div class="mamPlanCard best"><div class="mamBadge">★ ${he?'הכי משתלם':'Best value'}</div><div class="mamPlanName">Pro Annual</div><div class="mamPrice">$129</div><div class="mamPeriod">/year</div><ul class="mamBenefits"><li>${he?'גישה מלאה לשנה':'Full access for a year'}</li><li>${he?'כל הדוחות והכלים':'All reports and tools'}</li><li>${he?'עדכונים ושיפורים':'Updates and improvements'}</li><li>${he?'חיסכון של כ־30%':'Save about 30%'}</li></ul><button class="mamPlanBtn" data-plan="annual">${he?'בחר מסלול':'Choose plan'}</button></div></div><div class="mamFeatureRow"><div><div class="mamFeatureIcon">🎯</div>${he?'המלצות מעשיות לשיחה הבאה':'Practical next-step advice'}</div><div><div class="mamFeatureIcon">💡</div>${he?'איפה אפשר להשתפר':'Where to improve'}</div><div><div class="mamFeatureIcon">▥</div>${he?'מה עבד טוב בשיחה שלך':'What worked well'}</div></div><div class="micro">${he?'תשלום מאובטח באמצעות Stripe':'Secure checkout with Stripe'}</div><button class="mamRetry" onclick="chosen=null;sid=null;renderDomains();go('choose')">↻ ${he?'נסה תרחיש נוסף':'Try another scenario'}</button></div>`;box.querySelectorAll('.mamPlanBtn').forEach(b=>b.onclick=()=>checkoutPlan(b.dataset.plan,b))}
async function checkoutPlan(plan,b){const e=$('#mamEmail'),email=(e?.value||'').trim();if(!email||!email.includes('@')){alert(lang==='he'?'יש להזין כתובת אימייל תקינה כדי להמשיך לתשלום.':'Enter a valid email to continue.');e?.focus();return}b.disabled=true;const old=b.textContent;b.textContent='…';try{const r=await fetch('/api/stripe/checkout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sid,email,plan,lang})});const j=await r.json();if(j.url){location.href=j.url;return}alert(j.error||'Checkout unavailable')}catch(x){alert(lang==='he'?'לא ניתן לפתוח את התשלום כרגע.':'Checkout error')}finally{b.disabled=false;b.textContent=old}}
'''
 html=html[:start]+pay+html[end:]
ss=html.find("$('#scoreBtn').onclick=async()=>{");se=html.find('async function restorePaid(){',ss)
if ss>=0 and se>ss:
 handler=r'''$('#scoreBtn').onclick=async()=>{const refl={};qs.forEach((q,i)=>refl[q]=$('#q'+i)?.value||'');const b=$('#scoreBtn'),ov=$('#mamAnalysisLoading');b.disabled=true;b.textContent=t('processing');ov?.classList.add('on');try{const r=await fetch('/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sid,reflection:refl,lang})});const j=await r.json();lastReport=j;$('#score').textContent=j.performance_score??j.preview?.performance_score??'—';$('#outcome').textContent=j.outcome||'';$('#notice').textContent=j.alpha_notice||'';$('#freeInsight').innerHTML='';$('#fullReport').innerHTML='';if(j.locked)renderLocked(j);else renderFull(j);go('result')}catch(e){alert(lang==='he'?'לא ניתן להפיק משוב כרגע.':'Could not generate feedback right now.')}finally{ov?.classList.remove('on');b.disabled=false;b.textContent=t('result')}};
'''
 html=html[:ss]+handler+html[se:]
rs=html.find('async function restorePaid(){');re=html.find('setLang(localStorage.getItem',rs)
if rs>=0 and re>rs:
 restore=r'''async function restorePaid(){const u=new URLSearchParams(location.search);sid=u.get('sid')||localStorage.getItem('mam_sid');if(u.get('stripe')==='success'&&u.get('session_id')&&sid){try{const c=await fetch('/api/stripe/confirm?session_id='+encodeURIComponent(u.get('session_id'))+'&sid='+encodeURIComponent(sid));const cj=await c.json();if(!cj.paid)throw Error('not paid');const r=await fetch('/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sid,reflection:{},lang})});const j=await r.json();$('#score').textContent=j.performance_score??'—';$('#outcome').textContent=j.outcome||'';$('#notice').textContent=j.alpha_notice||'';if(j.locked)renderLocked(j);else renderFull(j);go('result');history.replaceState({},'',location.pathname)}catch(e){alert(lang==='he'?'שחזור הדוח לאחר התשלום נכשל. נסה לרענן.':'Report restoration failed. Please refresh.')}}}
'''
 html=html[:rs]+restore+html[re:]
html=html.replace('</body>',r'''<script>(function(){var g=document.getElementById('mamIntro');if(!g)return;if(sessionStorage.getItem('mam_intro_seen')==='1'){document.documentElement.classList.remove('mam-intro-lock');g.remove();return}var e=document.getElementById('mamEnter');if(e)e.addEventListener('click',function(){sessionStorage.setItem('mam_intro_seen','1')},{once:true})})();</script></body>''',1)
INDEX.write_text(html,encoding='utf-8')
def stripe_request(path,fields=None,method='POST'):
 key=os.getenv('STRIPE_SECRET_KEY','').strip()
 if not key:raise RuntimeError('Stripe is not configured')
 data=None if fields is None else urllib.parse.urlencode(fields).encode();req=urllib.request.Request('https://api.stripe.com'+path,data=data,method=method,headers={'Authorization':'Bearer '+key,'Content-Type':'application/x-www-form-urlencoded'})
 try:
  with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read().decode())
 except urllib.error.HTTPError as e:raise RuntimeError(e.read().decode(errors='replace')[:1000])
def verify_webhook(raw,signature):
 secret=os.getenv('STRIPE_WEBHOOK_SECRET','').strip()
 if not secret or not signature:return False
 parts={}
 for item in signature.split(','):
  if '=' in item:k,v=item.split('=',1);parts.setdefault(k,[]).append(v)
 try:ts=int(parts.get('t',['0'])[0])
 except ValueError:return False
 if abs(int(time.time())-ts)>300:return False
 expected=hmac.new(secret.encode(),str(ts).encode()+b'.'+raw,hashlib.sha256).hexdigest();return any(hmac.compare_digest(expected,x) for x in parts.get('v1',[]))
def grant_entitlement(obj):
 meta=obj.get('metadata')or{};sid=(obj.get('client_reference_id')or meta.get('session_id')or'').strip();plan=(meta.get('plan')or'').strip()
 if not sid or sid not in app.STORE or plan not in PLANS or obj.get('payment_status') not in ('paid','no_payment_required'):return False
 s=app.STORE[sid];ent=s.setdefault('entitlements',{});ent[plan]=True
 if plan!='deep':ent['pro']=True
 ent.update({'stripe_checkout_session_id':obj.get('id'),'stripe_customer_id':obj.get('customer'),'stripe_subscription_id':obj.get('subscription'),'updated_at':int(time.time())});v21.PAID_SESSIONS.add(sid);app.save(sid);return True
class H(v39.v38.H):
 def do_GET(self):
  parsed=urlparse(self.path);p=parsed.path
  if p=='/api/stripe/status':return self._json({'checkout_configured':bool(os.getenv('STRIPE_SECRET_KEY')),'webhook_configured':bool(os.getenv('STRIPE_WEBHOOK_SECRET')),'prices_configured':all(os.getenv(n) for n,_ in PLANS.values()),'paywall_enabled':True})
  if p=='/api/stripe/confirm':
   try:
    q=urllib.parse.parse_qs(parsed.query);cid=(q.get('session_id')or[''])[0];sid=(q.get('sid')or[''])[0]
    if not cid or not sid or sid not in app.STORE:return self._json({'paid':False},400)
    session=stripe_request('/v1/checkout/sessions/'+urllib.parse.quote(cid,safe=''),None,'GET');expected=session.get('client_reference_id')or(session.get('metadata')or{}).get('session_id')
    if expected!=sid:return self._json({'paid':False},403)
    return self._json({'paid':grant_entitlement(session),'plan':(session.get('metadata')or{}).get('plan')})
   except Exception as e:print('stripe confirm error',e);return self._json({'paid':False},503)
  return super().do_GET()
 def do_POST(self):
  p=urlparse(self.path).path
  if p in ('/api/stripe/checkout','/api/checkout'):
   try:
    body=self._body();plan=(body.get('plan')or'deep').strip().lower();sid=(body.get('session_id')or'').strip()
    if plan not in PLANS:return self._json({'error':'invalid plan'},400)
    if not sid or sid not in app.STORE:return self._json({'error':'invalid session'},400)
    env_name,mode=PLANS[plan];price=os.getenv(env_name,'').strip()
    if not price:return self._json({'error':'price not configured'},503)
    base=os.getenv('PUBLIC_BASE_URL','').strip().rstrip('/')or self.headers.get('X-Forwarded-Proto','https')+'://'+self.headers.get('Host','')
    fields={'mode':mode,'line_items[0][price]':price,'line_items[0][quantity]':'1','success_url':base+'/?stripe=success&session_id={CHECKOUT_SESSION_ID}&sid='+urllib.parse.quote(sid),'cancel_url':base+'/?stripe=cancel&sid='+urllib.parse.quote(sid),'client_reference_id':sid,'metadata[session_id]':sid,'metadata[plan]':plan}
    email=(body.get('email')or'').strip()
    if email:fields['customer_email']=email
    s=stripe_request('/v1/checkout/sessions',fields);return self._json({'url':s.get('url'),'id':s.get('id')})
   except Exception as e:print('stripe checkout error',e);return self._json({'error':'checkout unavailable'},503)
  if p=='/api/stripe/webhook':
   try:
    raw=self.rfile.read(int(self.headers.get('Content-Length','0')))
    if not verify_webhook(raw,self.headers.get('Stripe-Signature','')):return self._json({'error':'invalid signature'},400)
    ev=json.loads(raw.decode());obj=ev.get('data',{}).get('object',{});granted=grant_entitlement(obj) if ev.get('type')=='checkout.session.completed' else False;print('stripe event',ev.get('type'),'granted',granted);return self._json({'received':True})
   except Exception:return self._json({'error':'bad webhook'},400)
  return super().do_POST()
if __name__=='__main__':
 os.chdir(app.ROOT);print('Move A Mind v4.21 mobile pricing + full report invitation');ThreadingHTTPServer(('0.0.0.0',app.PORT),H).serve_forever()
