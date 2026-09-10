import os, json, urllib.parse, urllib.request, hashlib, hmac, time
from urllib.parse import urlparse
from http.server import ThreadingHTTPServer
import server_v28 as v28

app = v28.app
BASE_H = v28.v27.v26.v25.v24.H

STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY','').strip()
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET','').strip()
BASE_URL = os.getenv('PUBLIC_BASE_URL','https://move-a-mind-v08-production.up.railway.app').rstrip('/')
PRICE_DEEP = os.getenv('STRIPE_PRICE_DEEP','').strip()
PRICE_MONTHLY = os.getenv('STRIPE_PRICE_MONTHLY','').strip()
PRICE_ANNUAL = os.getenv('STRIPE_PRICE_ANNUAL','').strip()
PAYWALL_ENABLED = os.getenv('PAYWALL_ENABLED','0').strip() == '1'

PLAN_MAP = {
    'deep': {'price': PRICE_DEEP, 'mode':'payment'},
    'monthly': {'price': PRICE_MONTHLY, 'mode':'subscription'},
    'annual': {'price': PRICE_ANNUAL, 'mode':'subscription'},
}

def stripe_post(path, data):
    if not STRIPE_SECRET_KEY:
        raise RuntimeError('Stripe secret key not configured')
    body = urllib.parse.urlencode(data, doseq=True).encode()
    req = urllib.request.Request('https://api.stripe.com'+path, data=body, method='POST')
    req.add_header('Authorization', 'Bearer '+STRIPE_SECRET_KEY)
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

def verify_signature(payload, sig_header):
    if not STRIPE_WEBHOOK_SECRET or not sig_header:
        return False
    parts={}
    for item in sig_header.split(','):
        if '=' in item:
            k,v=item.split('=',1); parts.setdefault(k,[]).append(v)
    try: ts=parts.get('t',[None])[0]
    except: return False
    if not ts: return False
    signed=(ts+'.').encode()+payload
    expected=hmac.new(STRIPE_WEBHOOK_SECRET.encode(), signed, hashlib.sha256).hexdigest()
    ok=any(hmac.compare_digest(expected,v) for v in parts.get('v1',[]))
    try:
        if abs(time.time()-int(ts))>300: return False
    except: return False
    return ok

def mark_paid(session_id, plan):
    if not session_id: return
    try:
        s=app.STORE.get(session_id)
        if not s and hasattr(app,'load'):
            s=app.load(session_id)
        if s is not None:
            s['paid']=True; s['paid_plan']=plan; app.STORE[session_id]=s; app.save(session_id)
    except Exception:
        pass

class H(v28.v27.v26.v25.v24.H):
    def do_GET(self):
        p=urlparse(self.path).path
        if p=='/api/pricing':
            return self._json({
                'paywall_enabled':PAYWALL_ENABLED,
                'stripe_ready':bool(STRIPE_SECRET_KEY and PRICE_DEEP and PRICE_MONTHLY and PRICE_ANNUAL),
                'plans':{
                    'deep':{'label':'Deep Report','price':'4.90','currency':'USD','interval':'one_time'},
                    'monthly':{'label':'Pro Monthly','price':'15','currency':'USD','interval':'month'},
                    'annual':{'label':'Pro Annual','price':'129','currency':'USD','interval':'year'}
                }
            })
        return super().do_GET()

    def do_POST(self):
        p=urlparse(self.path).path
        if p=='/api/checkout':
            try: body=self._body()
            except: return self._json({'error':'bad request'},400)
            sid=(body.get('session_id') or '').strip(); email=(body.get('email') or '').strip(); plan=(body.get('plan') or 'deep').strip()
            if not sid or sid not in app.STORE or '@' not in email:return self._json({'error':'Enter a valid email.'},400)
            cfg=PLAN_MAP.get(plan)
            if not cfg or not cfg.get('price'): return self._json({'error':'Pricing is not configured.'},503)
            if not PAYWALL_ENABLED: return self._json({'error':'Paid checkout is not active yet.'},503)
            if not STRIPE_SECRET_KEY: return self._json({'error':'Stripe is not connected yet.'},503)
            try:
                data={
                    'mode':cfg['mode'],
                    'success_url':f'{BASE_URL}/?paid=1&sid={urllib.parse.quote(sid)}&plan={plan}&session_id={{CHECKOUT_SESSION_ID}}',
                    'cancel_url':f'{BASE_URL}/?sid={urllib.parse.quote(sid)}&canceled=1',
                    'customer_email':email,
                    'line_items[0][price]':cfg['price'],
                    'line_items[0][quantity]':'1',
                    'metadata[app_session_id]':sid,
                    'metadata[plan]':plan,
                    'allow_promotion_codes':'true'
                }
                obj=stripe_post('/v1/checkout/sessions',data)
                return self._json({'url':obj.get('url')})
            except Exception as e:
                return self._json({'error':'Stripe checkout could not be created.'},502)
        if p=='/api/stripe/webhook':
            length=int(self.headers.get('Content-Length','0') or 0); payload=self.rfile.read(length)
            sig=self.headers.get('Stripe-Signature','')
            if not verify_signature(payload,sig): return self._json({'error':'invalid signature'},400)
            try: evt=json.loads(payload.decode())
            except: return self._json({'error':'bad payload'},400)
            if evt.get('type')=='checkout.session.completed':
                obj=(evt.get('data') or {}).get('object') or {}; meta=obj.get('metadata') or {}
                mark_paid(meta.get('app_session_id'), meta.get('plan','deep'))
            return self._json({'received':True})
        return super().do_POST()

if __name__=='__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v3.8 Stripe checkout wiring')
    ThreadingHTTPServer(('0.0.0.0',app.PORT),H).serve_forever()
