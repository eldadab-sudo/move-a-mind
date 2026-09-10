import os, json, hmac, hashlib, urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse
import server_v21 as v21

app=v21.app
PERSIST=Path(os.getenv('PERSIST_DIR','/persistent'))
SESS=PERSIST/'sessions'; ENT=PERSIST/'entitlements'
SESS.mkdir(parents=True,exist_ok=True); ENT.mkdir(parents=True,exist_ok=True)

# Persist every conversation so Railway restarts/redeploys do not invalidate active sessions.
def persistent_save(sid):
    s=app.STORE.get(sid)
    if not s:return
    (SESS/f'{sid}.json').write_text(json.dumps(s,ensure_ascii=False),encoding='utf-8')
app.save=persistent_save

# Restore previous sessions and paid entitlements on startup.
for f in SESS.glob('*.json'):
    try:
        s=json.loads(f.read_text(encoding='utf-8'))
        if s.get('id'):app.STORE[s['id']]=s
    except:pass
for f in ENT.glob('*.json'):
    v21.PAID_SESSIONS.add(f.stem)

LEMON_API=os.getenv('LEMON_API_KEY','').strip()
LEMON_STORE=os.getenv('LEMON_STORE_ID','').strip()
LEMON_VARIANT=os.getenv('LEMON_VARIANT_ID','').strip()
LEMON_SECRET=os.getenv('LEMON_WEBHOOK_SECRET','').strip()
PUBLIC_BASE=os.getenv('PUBLIC_BASE_URL','https://move-a-mind-v08-production.up.railway.app').rstrip('/')


def configured():
    return bool(LEMON_API and LEMON_STORE and LEMON_VARIANT and LEMON_SECRET)

def mark_paid(sid,meta):
    if sid not in app.STORE:return False
    v21.PAID_SESSIONS.add(sid)
    (ENT/f'{sid}.json').write_text(json.dumps(meta,ensure_ascii=False),encoding='utf-8')
    return True

class H(v21.H):
    def do_GET(self):
        if urlparse(self.path).path=='/health':
            return self._json({'status':'ok','version':'3.1','scenarios':105,'persistent_sessions':True,'paywall_enabled':v21.PAYWALL_ENABLED,'payments_configured':configured()})
        return super().do_GET()

    def do_POST(self):
        p=urlparse(self.path).path
        if p=='/api/webhooks/lemonsqueezy':
            n=int(self.headers.get('Content-Length','0')); raw=self.rfile.read(n)
            if not LEMON_SECRET:return self._json({'error':'webhook not configured'},503)
            sig=self.headers.get('X-Signature',''); expected=hmac.new(LEMON_SECRET.encode(),raw,hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig,expected):return self._json({'error':'invalid signature'},401)
            try:j=json.loads(raw.decode('utf-8'))
            except:return self._json({'error':'invalid json'},400)
            event=(j.get('meta') or {}).get('event_name') or self.headers.get('X-Event-Name','')
            custom=(j.get('meta') or {}).get('custom_data') or {}; sid=str(custom.get('session_id',''))
            if event=='order_created' and sid:
                attrs=(j.get('data') or {}).get('attributes') or {}
                mark_paid(sid,{'paid':True,'order_id':str((j.get('data') or {}).get('id','')),'email':str(attrs.get('user_email',''))[:180]})
            return self._json({'ok':True})
        if p=='/api/checkout':
            try:body=self._body()
            except:return self._json({'error':'bad request'},400)
            sid=str(body.get('session_id','')); email=str(body.get('email','')).strip(); lang='en' if body.get('lang')=='en' else 'he'
            if sid not in app.STORE or '@' not in email:return self._json({'error':'Enter a valid email.'},400)
            if not v21.PAYWALL_ENABLED:return self._json({'error':'Paid checkout is not active yet.'},503)
            if not configured():return self._json({'error':'Checkout provider is not configured yet.'},503)
            cents=int(round(float(v21.PRICE_USD)*100))
            payload={'data':{'type':'checkouts','attributes':{'custom_price':cents,'product_options':{'name':'Move A Mind — Deep Performance Report','description':'Full evidence-based analysis of one completed conversation.','redirect_url':f'{PUBLIC_BASE}/?paid=1&sid={sid}'},'checkout_options':{'embed':False,'media':False,'logo':True,'desc':True,'discount':False,'locale':'en'},'checkout_data':{'email':email,'custom':{'session_id':sid}}},'relationships':{'store':{'data':{'type':'stores','id':LEMON_STORE}},'variant':{'data':{'type':'variants','id':LEMON_VARIANT}}}}}
            req=urllib.request.Request('https://api.lemonsqueezy.com/v1/checkouts',data=json.dumps(payload).encode(),headers={'Authorization':f'Bearer {LEMON_API}','Accept':'application/vnd.api+json','Content-Type':'application/vnd.api+json'},method='POST')
            try:
                with urllib.request.urlopen(req,timeout=30) as r:j=json.loads(r.read().decode())
                return self._json({'url':j['data']['attributes']['url']})
            except Exception:return self._json({'error':'Could not create checkout.'},502)
        return super().do_POST()

if __name__=='__main__':
    os.chdir(app.ROOT)
    print(f'Move A Mind v3.1 global launch · 105 scenarios · persistent · paywall={v21.PAYWALL_ENABLED}')
    ThreadingHTTPServer(('0.0.0.0',app.PORT),H).serve_forever()
