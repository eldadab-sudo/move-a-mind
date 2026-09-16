import os,json,time,hmac,hashlib,urllib.parse,urllib.request,urllib.error
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse
import server_v39 as v39
import server_v21 as v21
app=v39.app
PLANS={'deep':('STRIPE_PRICE_DEEP','payment'),'monthly':('STRIPE_PRICE_MONTHLY','subscription'),'annual':('STRIPE_PRICE_ANNUAL','subscription')}
INDEX=app.WEB/'global.html';html=INDEX.read_text(encoding='utf-8')
html=html.replace("onclick=\"location.href='/'\" data-t=\"again\"","onclick=\"chosen=null;sid=null;renderDomains();go('choose')\" data-t=\"again\"")
# Add a real loading overlay while the score is being generated.
loading_css=r'''<style id="mamLoadingCss">#mamAnalysisLoading{position:fixed;inset:0;z-index:99990;background:rgba(242,239,232,.97);display:none;align-items:center;justify-content:center;padding:24px;text-align:center}#mamAnalysisLoading.on{display:flex}.mamLoadInner{max-width:420px}.mamSpinLogo{width:126px;height:126px;border-radius:30px;object-fit:cover;animation:mamSpin 1.6s linear infinite;box-shadow:0 18px 50px rgba(16,32,30,.16)}.mamLoadTitle{font-family:Georgia,serif;font-size:36px;margin:24px 0 10px}.mamLoadText{color:#56635f;font-size:17px;line-height:1.6}@keyframes mamSpin{to{transform:rotate(360deg)}}@media(max-width:600px){.mamSpinLogo{width:108px;height:108px}.mamLoadTitle{font-size:31px}}</style>'''
loading_html=r'''<div id="mamAnalysisLoading"><div class="mamLoadInner"><img class="mamSpinLogo" src="/move-a-mind-logo.webp" alt="Move A Mind"><div class="mamLoadTitle" id="mamLoadTitle">מנתחים את השיחה שלך…</div><div class="mamLoadText" id="mamLoadText">אנחנו מזהים דפוסים, נקודות מפנה והזדמנויות לשיפור. התוצאה תופיע מיד כשהניתוח יושלם.</div></div></div>'''
html=html.replace('</head>',loading_css+'</head>',1).replace('<body>','<body>'+loading_html,1)
# Replace renderLocked through checkout with a three-plan paywall that always renders for unpaid sessions.
start=html.find('function renderLocked(j){');end=html.find("$('#scoreBtn').onclick",start)
if start>=0 and end>start:
 new=r'''function renderLocked(j){const p=j.preview||j,he=lang==='he';$('#freeInsight').innerHTML=`<div class="insight"><h3>${he?'טעימה מהניתוח שלך':'A glimpse of your analysis'}</h3><p>${p.top_insight||p.outcome||''}</p></div>`;$('#fullReport').innerHTML=`<div style="margin-top:18px"><h3>${he?'המשך הניתוח נעול':'The rest of the analysis is locked'}</h3><div class="lockedBlur"><div class="dims">${[1,2,3,4].map(()=>`<div class="dim"><b>${he?'ממד שיחה':'Conversation dimension'}</b><span class="dimScore">•••</span><p>${he?'ראיות והמלצות מדויקות מתוך השיחה מופיעות בדוח המלא.':'Specific evidence and recommendations appear in the full report.'}</p></div>`).join('')}</div></div></div>`;const box=$('#paywall');box.style.display='block';box.innerHTML=`<div class="premium"><div style="display:flex;align-items:center;gap:10px"><img src="/move-a-mind-logo.webp" alt="Move A Mind" style="width:46px;height:46px;border-radius:12px"><b>MOVE A MIND</b></div><h2 style="font-family:Georgia,serif;font-size:34px;margin:16px 0 8px">${he?'רוצה לדעת מה באמת קרה בשיחה שלך?':'Want to know what really happened in your conversation?'}</h2><p>${he?'גלה מה עבד, איפה איבדת השפעה ואיך לנהל את השיחה הבאה טוב יותר.':'Discover what worked, where you lost influence, and how to handle the next conversation better.'}</p><input class="checkoutEmail" id="mamEmail" type="email" placeholder="Email" autocomplete="email" style="margin:12px 0"><button class="btn mamPlan" data-plan="deep">Deep Report · $4.90 ${he?'חד־פעמי':'one-time'}</button><button class="btn mamPlan" data-plan="monthly">Pro Monthly · $15/month</button><button class="btn mamPlan" data-plan="annual">Pro Annual · $129/year</button><div class="micro">${he?'תשלום מאובטח באמצעות Stripe':'Secure checkout with Stripe'}</div></div>`;box.querySelectorAll('.mamPlan').forEach(b=>b.onclick=()=>checkoutPlan(b.dataset.plan,b))}
async function checkoutPlan(plan,b){const e=$('#mamEmail'),email=(e?.value||'').trim();if(!email||!email.includes('@')){alert(lang==='he'?'יש להזין כתובת אימייל תקינה כדי להמשיך לתשלום.':'Enter a valid email to continue.');e?.focus();return}b.disabled=true;const old=b.textContent;b.textContent='…';try{const r=await fetch('/api/stripe/checkout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sid,email,plan,lang})});const j=await r.json();if(j.url){location.href=j.url;return}alert(j.error||'Checkout unavailable')}catch(x){alert(lang==='he'?'לא ניתן לפתוח את התשלום כרגע.':'Checkout error')}finally{b.disabled=false;b.textContent=old}}
'''
 html=html[:start]+new+html[end:]
# Replace score click handler to show/hide rotating logo around the actual API wait.
ss=html.find("$('#scoreBtn').onclick=async()=>{");se=html.find('async function restorePaid(){',ss)
if ss>=0 and se>ss:
 score=r'''$('#scoreBtn').onclick=async()=>{const refl={};qs.forEach((q,i)=>refl[q]=$('#q'+i)?.value||'');const b=$('#scoreBtn'),ov=$('#mamAnalysisLoading');$('#mamLoadTitle').textContent=lang==='he'?'מנתחים את השיחה שלך…':'Analyzing your conversation…';$('#mamLoadText').textContent=lang==='he'?'אנחנו מזהים דפוסים, נקודות מפנה והזדמנויות לשיפור. התוצאה תופיע מיד כשהניתוח יושלם.':'We are identifying patterns, turning points and opportunities to improve. Your result will appear as soon as the analysis is complete.';b.disabled=true;b.textContent=t('processing');ov?.classList.add('on');try{const r=await fetch('/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sid,reflection:refl,lang})});const j=await r.json();lastReport=j;$('#score').textContent=j.performance_score??j.preview?.performance_score??'—';$('#outcome').textContent=j.outcome||j.preview?.outcome||'';$('#notice').textContent=j.alpha_notice||'';$('#freeInsight').innerHTML='';$('#fullReport').innerHTML='';if(j.locked)renderLocked(j);else renderFull(j);go('result')}catch(e){alert(lang==='he'?'לא ניתן להפיק משוב כרגע.':'Could not generate feedback right now.')}finally{ov?.classList.remove('on');b.disabled=false;b.textContent=t('result')}};
'''
 html=html[:ss]+score+html[se:]
# Stripe return confirmation and report restoration.
rs=html.find('async function restorePaid(){');re=html.find('setLang(localStorage.getItem',rs)
if rs>=0 and re>rs:
 restore=r'''async function restorePaid(){const u=new URLSearchParams(location.search);sid=u.get('sid')||localStorage.getItem('mam_sid');if(u.get('stripe')==='success'&&u.get('session_id')&&sid){try{const c=await fetch('/api/stripe/confirm?session_id='+encodeURIComponent(u.get('session_id'))+'&sid='+encodeURIComponent(sid));const cj=await c.json();if(!cj.paid)throw Error('not paid');const r=await fetch('/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sid,reflection:{},lang})});const j=await r.json();$('#score').textContent=j.performance_score??j.preview?.performance_score??'—';$('#outcome').textContent=j.outcome||j.preview?.outcome||'';$('#notice').textContent=j.alpha_notice||'';if(j.locked)renderLocked(j);else renderFull(j);go('result');history.replaceState({},'',location.pathname)}catch(e){alert(lang==='he'?'שחזור הדוח לאחר התשלום נכשל. נסה לרענן.':'Report restoration failed. Please refresh.')}return}}
'''
 html=html[:rs]+restore+html[re:]
html=html.replace('</body>',r'''<script id="mamIntroOnce">(function(){var g=document.getElementById('mamIntro');if(!g)return;if(sessionStorage.getItem('mam_intro_seen')==='1'){document.documentElement.classList.remove('mam-intro-lock');g.remove();return}var e=document.getElementById('mamEnter');if(e)e.addEventListener('click',function(){sessionStorage.setItem('mam_intro_seen','1')},{once:true})})();</script></body>''',1)
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
  if p=='/api/stripe/status':return self._json({'checkout_configured':bool(os.getenv('STRIPE_SECRET_KEY')),'webhook_configured':bool(os.getenv('STRIPE_WEBHOOK_SECRET')),'prices_configured':all(os.getenv(n) for n,_ in PLANS.values()),'paywall_enabled':os.getenv('PAYWALL_ENABLED','').lower() in ('1','true','yes','on')})
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
    ev=json.loads(raw.decode());obj=ev.get('data',{}).get('object',{});grant=grant_entitlement(obj) if ev.get('type')=='checkout.session.completed' else False;print('stripe event',ev.get('type'),'granted',grant);return self._json({'received':True})
   except Exception:return self._json({'error':'bad webhook'},400)
  return super().do_POST()
if __name__=='__main__':
 os.chdir(app.ROOT);print('Move A Mind v4.18 paywall + rotating analysis logo');ThreadingHTTPServer(('0.0.0.0',app.PORT),H).serve_forever()
