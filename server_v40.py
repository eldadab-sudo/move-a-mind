import os
import json
import time
import hmac
import hashlib
import urllib.parse
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

import server_v39 as v39
import server_v21 as v21

app = v39.app

PLANS = {
    'deep': ('STRIPE_PRICE_DEEP', 'payment'),
    'monthly': ('STRIPE_PRICE_MONTHLY', 'subscription'),
    'annual': ('STRIPE_PRICE_ANNUAL', 'subscription'),
}

# v4.14 UI patch. server_v39 already injected the opening film into global.html.
INDEX = app.WEB / 'global.html'
html = INDEX.read_text(encoding='utf-8')
html = html.replace("onclick=\"location.href='/'\" data-t=\"again\"", "onclick=\"chosen=null;sid=null;renderDomains();go('choose')\" data-t=\"again\"")
# Show commercial choices after a full free report while PAYWALL_ENABLED remains off for safe Sandbox testing.
offers_js = r'''
<script id="mamStripeOffers">
(function(){
  function offers(){
    var box=document.getElementById('paywall');
    if(!box||!window.sid)return;
    box.style.display='block';
    box.innerHTML='<div class="premium"><div style="font-size:12px;letter-spacing:.1em;color:#9dc4b9;font-weight:900">MOVE A MIND · UPGRADE</div><h2 style="font-family:Georgia,serif;font-size:34px;margin:10px 0">Choose your next level</h2><p>Unlock a deep report for this conversation, or choose Pro for ongoing access.</p><input class="checkoutEmail" id="mamOfferEmail" type="email" placeholder="Email" style="margin:12px 0"><button class="btn mamPlan" data-plan="deep">Deep Report · $4.90 one-time</button><button class="btn mamPlan" data-plan="monthly">Pro Monthly · $15/month</button><button class="btn mamPlan" data-plan="annual">Pro Annual · $129/year</button><div class="micro">Stripe Sandbox checkout · no live charge during testing</div></div>';
    box.querySelectorAll('.mamPlan').forEach(function(b){b.onclick=function(){checkoutPlan(b.dataset.plan,b)}});
  }
  async function checkoutPlan(plan,b){
    var e=document.getElementById('mamOfferEmail'),email=(e&&e.value||'').trim();
    if(!email||email.indexOf('@')<1){if(e)e.focus();return;}
    b.disabled=true;var old=b.textContent;b.textContent='…';
    try{var r=await fetch('/api/stripe/checkout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:window.sid||sid,email:email,plan:plan,lang:window.lang||lang})});var j=await r.json();if(j.url){location.href=j.url;return;}alert(j.error||'Checkout unavailable');}catch(x){alert('Checkout error');}finally{b.disabled=false;b.textContent=old;}
  }
  var oldRenderFull=window.renderFull;
  if(typeof oldRenderFull==='function')window.renderFull=function(j){oldRenderFull(j);setTimeout(offers,0)};
  window.mamShowOffers=offers;
})();
</script>
'''
html = html.replace('</body>', offers_js + '</body>', 1)
# The intro should run only once per browser tab/session. Repeat scenarios stay inside the app.
intro_once_js = r'''
<script id="mamIntroOnce">
(function(){
  var gate=document.getElementById('mamIntro');
  if(!gate)return;
  if(sessionStorage.getItem('mam_intro_seen')==='1'){
    document.documentElement.classList.remove('mam-intro-lock');gate.remove();return;
  }
  var enter=document.getElementById('mamEnter');
  if(enter)enter.addEventListener('click',function(){sessionStorage.setItem('mam_intro_seen','1')},{once:true});
})();
</script>
'''
html = html.replace('</body>', intro_once_js + '</body>', 1)
INDEX.write_text(html, encoding='utf-8')


def stripe_request(path, fields=None, method='POST'):
    key = os.getenv('STRIPE_SECRET_KEY', '').strip()
    if not key:
        raise RuntimeError('Stripe is not configured')
    data = None if fields is None else urllib.parse.urlencode(fields).encode('utf-8')
    req = urllib.request.Request('https://api.stripe.com' + path,data=data,method=method,headers={'Authorization':'Bearer '+key,'Content-Type':'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:raise RuntimeError('Stripe request failed: '+e.read().decode('utf-8',errors='replace')[:1000])


def verify_webhook(raw, signature):
    secret=os.getenv('STRIPE_WEBHOOK_SECRET','').strip()
    if not secret or not signature:return False
    parts={}
    for item in signature.split(','):
        if '=' in item:
            k,v=item.split('=',1);parts.setdefault(k,[]).append(v)
    try:timestamp=int(parts.get('t',['0'])[0])
    except ValueError:return False
    if abs(int(time.time())-timestamp)>300:return False
    expected=hmac.new(secret.encode(),str(timestamp).encode('ascii')+b'.'+raw,hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected,s) for s in parts.get('v1',[]))


def grant_entitlement(obj):
    meta=obj.get('metadata') or {};sid=(obj.get('client_reference_id') or meta.get('session_id') or '').strip();plan=(meta.get('plan') or '').strip()
    if not sid or sid not in app.STORE or plan not in PLANS:return False
    if obj.get('payment_status') not in ('paid','no_payment_required'):return False
    s=app.STORE[sid];ent=s.setdefault('entitlements',{});ent[plan]=True;ent['stripe_checkout_session_id']=obj.get('id');ent['stripe_customer_id']=obj.get('customer');ent['stripe_subscription_id']=obj.get('subscription');ent['updated_at']=int(time.time())
    if plan!='deep':ent['pro']=True
    v21.PAID_SESSIONS.add(sid);app.save(sid);return True


class H(v39.v38.H):
    def do_GET(self):
        parsed=urlparse(self.path);p=parsed.path
        if p=='/api/stripe/status':return self._json({'checkout_configured':bool(os.getenv('STRIPE_SECRET_KEY')),'webhook_configured':bool(os.getenv('STRIPE_WEBHOOK_SECRET')),'prices_configured':all(os.getenv(n) for n,_ in PLANS.values()),'paywall_enabled':os.getenv('PAYWALL_ENABLED','').lower() in ('1','true','yes','on')})
        if p=='/api/stripe/confirm':
            try:
                q=urllib.parse.parse_qs(parsed.query);checkout_id=(q.get('session_id') or [''])[0].strip();sid=(q.get('sid') or [''])[0].strip()
                if not checkout_id or not sid or sid not in app.STORE:return self._json({'paid':False},400)
                session=stripe_request('/v1/checkout/sessions/'+urllib.parse.quote(checkout_id,safe=''),None,'GET');expected=session.get('client_reference_id') or (session.get('metadata') or {}).get('session_id')
                if expected!=sid:return self._json({'paid':False},403)
                granted=grant_entitlement(session);return self._json({'paid':bool(granted),'plan':(session.get('metadata') or {}).get('plan')})
            except Exception as e:print('stripe confirm error:',str(e));return self._json({'paid':False},503)
        return super().do_GET()

    def do_POST(self):
        p=urlparse(self.path).path
        if p in ('/api/stripe/checkout','/api/checkout'):
            try:
                body=self._body();plan=(body.get('plan') or 'deep').strip().lower();sid=(body.get('session_id') or '').strip()
                if plan not in PLANS:return self._json({'error':'invalid plan'},400)
                if not sid or sid not in app.STORE:return self._json({'error':'invalid session'},400)
                env_name,mode=PLANS[plan];price=os.getenv(env_name,'').strip()
                if not price:return self._json({'error':'price not configured'},503)
                base=os.getenv('PUBLIC_BASE_URL','').strip().rstrip('/')
                if not base:base=self.headers.get('X-Forwarded-Proto','https')+'://'+self.headers.get('Host','')
                fields={'mode':mode,'line_items[0][price]':price,'line_items[0][quantity]':'1','success_url':base+'/?stripe=success&session_id={CHECKOUT_SESSION_ID}&sid='+urllib.parse.quote(sid),'cancel_url':base+'/?stripe=cancel&sid='+urllib.parse.quote(sid),'client_reference_id':sid,'metadata[session_id]':sid,'metadata[plan]':plan,'allow_promotion_codes':'false'}
                email=(body.get('email') or '').strip()
                if email:fields['customer_email']=email
                session=stripe_request('/v1/checkout/sessions',fields);return self._json({'url':session.get('url'),'id':session.get('id')})
            except Exception as e:print('stripe checkout error:',str(e));return self._json({'error':'checkout unavailable'},503)
        if p=='/api/stripe/webhook':
            try:
                length=int(self.headers.get('Content-Length','0'));raw=self.rfile.read(length)
                if not verify_webhook(raw,self.headers.get('Stripe-Signature','')):return self._json({'error':'invalid signature'},400)
                event=json.loads(raw.decode());event_type=event.get('type','');obj=event.get('data',{}).get('object',{});granted=grant_entitlement(obj) if event_type=='checkout.session.completed' else False
                print('verified stripe event:',event_type,obj.get('id',''),'granted=',granted);return self._json({'received':True})
            except Exception as e:print('stripe webhook error:',str(e));return self._json({'error':'bad webhook'},400)
        return super().do_POST()


if __name__=='__main__':
    os.chdir(app.ROOT);print('Move A Mind v4.14 Stripe offers + repeat scenario navigation');ThreadingHTTPServer(('0.0.0.0',app.PORT),H).serve_forever()
