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

app = v39.app

PLANS = {
    'deep': ('STRIPE_PRICE_DEEP', 'payment'),
    'monthly': ('STRIPE_PRICE_MONTHLY', 'subscription'),
    'annual': ('STRIPE_PRICE_ANNUAL', 'subscription'),
}


def stripe_request(path, fields):
    key = os.getenv('STRIPE_SECRET_KEY', '').strip()
    if not key:
        raise RuntimeError('Stripe is not configured')
    data = urllib.parse.urlencode(fields).encode('utf-8')
    req = urllib.request.Request(
        'https://api.stripe.com' + path,
        data=data,
        method='POST',
        headers={
            'Authorization': 'Bearer ' + key,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', errors='replace')[:1000]
        raise RuntimeError('Stripe request failed: ' + detail)


def verify_webhook(raw, signature):
    secret = os.getenv('STRIPE_WEBHOOK_SECRET', '').strip()
    if not secret or not signature:
        return False
    parts = {}
    for item in signature.split(','):
        if '=' in item:
            k, v = item.split('=', 1)
            parts.setdefault(k, []).append(v)
    try:
        timestamp = int(parts.get('t', ['0'])[0])
    except ValueError:
        return False
    if abs(int(time.time()) - timestamp) > 300:
        return False
    signed = str(timestamp).encode('ascii') + b'.' + raw
    expected = hmac.new(secret.encode('utf-8'), signed, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, sig) for sig in parts.get('v1', []))


class H(v39.v38.H):
    def do_GET(self):
        p = urlparse(self.path).path
        if p == '/api/stripe/status':
            return self._json({
                'checkout_configured': bool(os.getenv('STRIPE_SECRET_KEY')),
                'webhook_configured': bool(os.getenv('STRIPE_WEBHOOK_SECRET')),
                'prices_configured': all(os.getenv(name) for name, _ in PLANS.values()),
                'paywall_enabled': os.getenv('PAYWALL_ENABLED', '').lower() in ('1','true','yes','on'),
            })
        return super().do_GET()

    def do_POST(self):
        p = urlparse(self.path).path
        if p == '/api/stripe/checkout':
            try:
                body = self._body()
                plan = (body.get('plan') or '').strip().lower()
                if plan not in PLANS:
                    return self._json({'error': 'invalid plan'}, 400)
                env_name, mode = PLANS[plan]
                price = os.getenv(env_name, '').strip()
                if not price:
                    return self._json({'error': 'price not configured'}, 503)
                base = os.getenv('PUBLIC_BASE_URL', '').strip().rstrip('/')
                if not base:
                    host = self.headers.get('Host', '')
                    proto = self.headers.get('X-Forwarded-Proto', 'https')
                    base = proto + '://' + host
                fields = {
                    'mode': mode,
                    'line_items[0][price]': price,
                    'line_items[0][quantity]': '1',
                    'success_url': base + '/?stripe=success&session_id={CHECKOUT_SESSION_ID}',
                    'cancel_url': base + '/?stripe=cancel',
                    'metadata[plan]': plan,
                    'allow_promotion_codes': 'false',
                }
                email = (body.get('email') or '').strip()
                if email:
                    fields['customer_email'] = email
                session = stripe_request('/v1/checkout/sessions', fields)
                return self._json({'url': session.get('url'), 'id': session.get('id')})
            except Exception as e:
                print('stripe checkout error:', str(e))
                return self._json({'error': 'checkout unavailable'}, 503)

        if p == '/api/stripe/webhook':
            try:
                length = int(self.headers.get('Content-Length', '0'))
                raw = self.rfile.read(length)
                if not verify_webhook(raw, self.headers.get('Stripe-Signature', '')):
                    return self._json({'error': 'invalid signature'}, 400)
                event = json.loads(raw.decode('utf-8'))
                event_type = event.get('type', '')
                obj = event.get('data', {}).get('object', {})
                # Keep processing intentionally idempotent/stateless for now. The event
                # is verified here; entitlement persistence is added only after the
                # application's user/session ownership model is wired to checkout.
                print('verified stripe event:', event_type, obj.get('id', ''))
                return self._json({'received': True})
            except Exception as e:
                print('stripe webhook error:', str(e))
                return self._json({'error': 'bad webhook'}, 400)

        return super().do_POST()


if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.12 Stripe checkout + verified webhook foundation')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), H).serve_forever()
