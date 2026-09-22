import os, json, hmac, hashlib, urllib.request, urllib.parse
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse
import server_v21 as v21

app=v21.app
PERSIST=Path(os.getenv('PERSIST_DIR','/persistent')); SESS=PERSIST/'sessions'; ENT=PERSIST/'entitlements'
SESS.mkdir(parents=True,exist_ok=True); ENT.mkdir(parents=True,exist_ok=True)

def persistent_save(sid):
    s=app.STORE.get(sid)
    if s:(SESS/f'{sid}.json').write_text(json.dumps(s,ensure_ascii=False),encoding='utf-8')
app.save=persistent_save
for f in SESS.glob('*.json'):
    try:
        s=json.loads(f.read_text(encoding='utf-8'))
        if s.get('id'):app.STORE[s['id']]=s
    except:pass
for f in ENT.glob('*.json'):v21.PAID_SESSIONS.add(f.stem)

STRIPE_KEY=os.getenv('STRIPE_SECRET_KEY','').strip()
STRIPE_WEBHOOK=os.getenv('STRIPE_WEBHOOK_SECRET','').strip()
PRICES={'deep':os.getenv('STRIPE_PRICE_DEEP','').strip(),'monthly':os.getenv('STRIPE_PRICE_MONTHLY','').strip(),'annual':os.getenv('STRIPE_PRICE_ANNUAL','').strip()}
PUBLIC_BASE=os.getenv('PUBLIC_BASE_URL','https://move-a-mind-v08-production.up.railway.app').rstrip('/')

def stripe_req(path,data=None):
    headers={'Authorization':f'Bearer {STRIPE_KEY}'}
    body=None
    if data is not None:
        body=urllib.parse.urlencode(data).encode();headers['Content-Type']='application/x-www-form-urlencoded'
    req=urllib.request.Request('https://api.stripe.com'+path,data=body,headers=headers,method='POST' if data is not None else 'GET')
    with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read().decode())

def price_status():
    out={}
    for plan,pid in PRICES.items():
        x={'configured':bool(STRIPE_KEY and pid),'verified':False,'mode':'payment' if plan=='deep' else 'subscription'}
        if x['configured']:
            try:
                p=stripe_req('/v1/prices/'+urllib.parse.quote(pid,safe=''))
                x.update({'verified':bool(p.get('active')),'currency':p.get('currency'),'unit_amount':p.get('unit_amount'),'type':p.get('type')})
            except Exception as e:x['error']='verification_failed'
        out[plan]=x
    return out

def mark_paid(sid,meta):
    if sid not in app.STORE:return False
    v21.PAID_SESSIONS.add(sid);(ENT/f'{sid}.json').write_text(json.dumps(meta,ensure_ascii=False),encoding='utf-8');return True

def verify_stripe(raw,sig):
    if not STRIPE_WEBHOOK or not sig:return False
    try:
        parts=dict(x.split('=',1) for x in sig.split(',') if '=' in x);t=parts['t'];v=parts['v1']
        expected=hmac.new(STRIPE_WEBHOOK.encode(),(t+'.').encode()+raw,hashlib.sha256).hexdigest()
        return hmac.compare_digest(v,expected)
    except:return False

class H(v21.H):
    def do_GET(self):
        p=urlparse(self.path).path
        if p=='/health':return self._json({'status':'ok','version':'4.47','scenarios':105,'persistent_sessions':True,'paywall_enabled':v21.PAYWALL_ENABLED,'payments_configured':bool(STRIPE_KEY and all(PRICES.values()))})
        if p=='/api/stripe/status':
            st=price_status();return self._json({'provider':'stripe','configured':bool(STRIPE_KEY and all(PRICES.values())),'plans':st,'verified':all(x.get('verified') for x in st.values())})
        return super().do_GET()
    def do_POST(self):
        p=urlparse(self.path).path
        if p=='/api/webhooks/stripe':
            n=int(self.headers.get('Content-Length','0'));raw=self.rfile.read(n)
            if not verify_stripe(raw,self.headers.get('Stripe-Signature','')):return self._json({'error':'invalid signature'},401)
            try:j=json.loads(raw.decode())
            except:return self._json({'error':'invalid json'},400)
            obj=(j.get('data') or {}).get('object') or {};meta=obj.get('metadata') or {};sid=str(meta.get('session_id',''))
            if j.get('type')=='checkout.session.completed' and sid:mark_paid(sid,{'paid':True,'checkout_session_id':obj.get('id'),'plan':meta.get('plan')})
            return self._json({'ok':True})
        if p=='/api/reflection':
            try:body=self._body()
            except:return self._json({'error':'bad request'},400)
            sid=str(body.get('session_id',''));lang=str(body.get('lang','en'))
            if sid not in app.STORE:return self._json({'error':'not found'},404)
            q_he=['מה ניסית להשיג בשיחה?','מה לדעתך עבד הכי טוב?','איפה הרגשת התנגדות או קושי?','האם השגת את התוצאה שרצית?','באיזו מידה, מ-0 עד 100, הצלחת להזיז את השיחה קדימה?']
            q_en=['What were you trying to achieve in the conversation?','What do you think worked best?','Where did you feel resistance or difficulty?','Did you achieve the outcome you wanted?','From 0 to 100, how much did you move the conversation forward?']
            return self._json({'questions':q_he if lang=='he' else q_en})
        if p=='/api/checkout':
            try:body=self._body()
            except:return self._json({'error':'bad request'},400)
            sid=str(body.get('session_id',''));email=str(body.get('email','')).strip();plan=str(body.get('plan','deep'))
            if sid not in app.STORE or '@' not in email or plan not in PRICES:return self._json({'error':'Enter a valid email and plan.'},400)
            if not v21.PAYWALL_ENABLED:return self._json({'error':'Paid checkout is not active yet.'},503)
            if not STRIPE_KEY or not PRICES[plan]:return self._json({'error':'Stripe is not configured yet.'},503)
            data={'mode':'payment' if plan=='deep' else 'subscription','line_items[0][price]':PRICES[plan],'line_items[0][quantity]':'1','customer_email':email,'metadata[session_id]':sid,'metadata[plan]':plan,'success_url':f'{PUBLIC_BASE}/?paid=1&sid={sid}','cancel_url':f'{PUBLIC_BASE}/?canceled=1&sid={sid}'}
            try:
                j=stripe_req('/v1/checkout/sessions',data);return self._json({'url':j.get('url'),'checkout_session_id':j.get('id'),'plan':plan,'mode':data['mode']})
            except Exception as e:
                print('STRIPE CHECKOUT ERROR',repr(e));return self._json({'error':'Could not create Stripe checkout.'},502)
        if p=='/api/score':
            # Let v21 generate the locked report, then enrich its preview is not possible after headers; handled by v21 below.
            return super().do_POST()
        return super().do_POST()

if __name__=='__main__':
    os.chdir(app.ROOT);print('Move A Mind v4.47 - reflection launch fix')
    ThreadingHTTPServer(('0.0.0.0',app.PORT),H).serve_forever()
