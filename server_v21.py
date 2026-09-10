import os, json, uuid, random, datetime
from urllib.parse import urlparse
from http.server import ThreadingHTTPServer
import server_v20 as v20
import server_v18 as scoring
from scenario_bank_v1 import BANK

app = v20.app
BASE_H = v20.v19.v18.H
PRICE_USD = os.getenv('REPORT_PRICE_USD','4.90')
CHECKOUT_URL = os.getenv('CHECKOUT_URL','').strip()
PAYWALL_ENABLED = os.getenv('PAYWALL_ENABLED','0').strip() == '1'
PAID_SESSIONS = set()

# Keep expert lenses from v2.4 while allowing each session to own its scenario.
def session_scenario(s):
    return s.get('scenario') or app.SCENARIOS[s['track']]

def scenario_prompt(sc, track, turn):
    # v20 scenario_system expects identity in current SCENARIOS; build directly with the same expert lens.
    lens = v20.EXPERT_LENSES.get(track,'')
    return app.GLOBAL + f'''\n\nתרחיש:\n{sc.get('brief','')}\n\nעובדות נסתרות וכללי דמות:\n{sc.get('facts','')}\n\nשכבות אפשריות: {', '.join(sc.get('layers',[]))}.\nסופים לגיטימיים: {', '.join(sc.get('possible_endings',[]))}.\nמספר תור משתמש: {turn}.\n{lens}\n\nאתה מגלם רק את {sc.get('character','הדמות')}. המשתמש ממלא את התפקיד שמוגדר בתרחיש. אל תדבר בשם המשתמש. אם זה תור 0, אתה פותח ראשון באופן טבעי. אל תחשוף עובדות נסתרות בלי שהן הורווחו בשיחה.'''

def translated_brief(sc, lang):
    if lang != 'en': return sc.get('brief','')
    prompt = f'''Translate the following Hebrew scenario brief into polished natural English for a premium training app. Preserve roles, facts and goal. Do not add advice. Return translation only.\n\n{sc.get('brief','')}'''
    return app.ai('Return only the English translation.',[{'role':'user','content':prompt}],350) or sc.get('brief','')

def translated_title(sc, lang):
    if lang != 'en': return sc.get('title','')
    prompt=f"Translate this short scenario title to natural English. Return title only: {sc.get('title','')}"
    return app.ai('Return only a short English title.',[{'role':'user','content':prompt}],80) or sc.get('title','')

def maybe_translate_reply(txt, lang):
    if lang != 'en' or not txt: return txt
    prompt=f'''Translate this roleplay character reply from Hebrew to concise, natural spoken English. Preserve tone and meaning. Return only the reply.\n\n{txt}'''
    return app.ai('Return only the translated reply.',[{'role':'user','content':prompt}],180) or txt

class H(BASE_H):
    def do_GET(self):
        p=urlparse(self.path).path
        if p=='/':
            b=(app.WEB/'global.html').read_bytes(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return
        if p=='/legacy':
            b=(app.WEB/'index.html').read_bytes(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return
        if p=='/api/catalog':
            return self._json({'domains':{k:len(v) for k,v in BANK.items()},'total':sum(len(v) for v in BANK.values()),'price_usd':PRICE_USD,'paywall_enabled':PAYWALL_ENABLED})
        return super().do_GET()

    def do_POST(self):
        p=urlparse(self.path).path
        if p=='/api/start':
            try: body=self._body()
            except: return self._json({'error':'bad request'},400)
            track=body.get('track'); lang=body.get('lang','he')
            if track not in BANK:return self._json({'error':'invalid track'},400)
            sc=random.choice(BANK[track])
            sid=str(uuid.uuid4())
            s={'id':sid,'track':track,'turn':0,'messages':[],'status':'active','created_at':datetime.datetime.utcnow().isoformat()+'Z','scenario':sc,'scenario_title':sc.get('title','')}
            app.STORE[sid]=s
            ans=app.ai(scenario_prompt(sc,track,0),[]) or app.fallback(track,1)
            ended='[END]' in ans; ans=ans.replace('[END]','').strip(); s['messages'].append({'role':'assistant','content':ans}); s['status']='finished' if ended else 'active'; app.save(sid)
            return self._json({'session_id':sid,'brief':translated_brief(sc,lang),'scenario_title':translated_title(sc,lang),'character':sc.get('character',''),'message':maybe_translate_reply(ans,lang),'ended':ended,'demo':not bool(app.API_KEY)})
        if p=='/api/chat':
            try: body=self._body()
            except:return self._json({'error':'bad request'},400)
            sid=body.get('session_id'); text=(body.get('message') or '').strip(); lang=body.get('lang','he')
            if sid not in app.STORE or not text:return self._json({'error':'invalid session'},400)
            s=app.STORE[sid]
            if s.get('status')!='active':return self._json({'error':'conversation ended'},400)
            s['turn']+=1; sc=session_scenario(s)
            # Store canonical conversation language as entered by user; model can handle English input with Hebrew scenario context.
            s['messages'].append({'role':'user','content':text})
            ans=app.ai(scenario_prompt(sc,s['track'],s['turn']),s['messages']) or app.fallback(s['track'],s['turn'])
            ended='[END]' in ans or s['turn']>=9; ans=ans.replace('[END]','').strip(); s['messages'].append({'role':'assistant','content':ans}); s['status']='finished' if ended else 'active'; app.save(sid)
            return self._json({'message':maybe_translate_reply(ans,lang),'ended':ended,'turn':s['turn']})
        if p=='/api/score':
            try: body=self._body()
            except:return self._json({'error':'bad request'},400)
            sid=body.get('session_id'); lang=body.get('lang','he')
            if sid not in app.STORE:return self._json({'error':'not found'},404)
            s=app.STORE[sid]; sc=session_scenario(s)
            fallback=scoring.heuristic_report(s,sc)
            transcript='\n'.join([('Participant' if m.get('role')=='user' else sc.get('character','Counterpart'))+': '+m.get('content','') for m in s.get('messages',[])])
            reflection=body.get('reflection') or {}
            language_rule='Write all report fields in English.' if lang=='en' else 'כתוב את כל שדות הדוח בעברית.'
            prompt=f'''You are a rigorous conversation-performance evaluator. Analyze behavior in this conversation only; do not diagnose personality.\nScenario: {sc.get('brief','')}\nTranscript:\n{transcript}\nSelf-reflection: {json.dumps(reflection,ensure_ascii=False)}\n\nScore exactly these 10 dimensions from 1.0 to 5.0: {', '.join(app.DIMS)}. Use decimals. For every dimension provide specific evidence from the transcript. Distinguish dimensions; do not default them to the same score. Reward precise inquiry, listening, adaptation, trust-building, relevant reasoning and concrete next steps. Penalize missed interests, repetition, pressure, unsupported promises, ignoring objections, or lack of closure. Agreement itself is not the goal; a respectful no can score highly. Give 3 specific strengths, 3 specific improvements, the real turning point, one better phrase for a weak moment, an outcome analysis, and a 5-8 sentence summary. Return JSON only, without performance_score; server computes it. {language_rule}\nSchema: {{"dimensions":[{{"name":"...","score":4.2,"evidence":"..."}}],"outcome":"...","strengths":["..."],"improvements":["..."],"turning_point":"...","better_phrase":"...","summary":"..."}}'''
            raw=app.ai('Return valid JSON only.',[{'role':'user','content':prompt}],2400)
            rep=scoring.normalize_report(scoring.extract_json(raw),fallback)
            rep['alpha_notice']='Experimental performance feedback for this conversation only — not a validated psychological measure.' if lang=='en' else 'משוב ביצוע ניסויי לשיחה הזו בלבד — אינו מדד פסיכולוגי מאומת.'
            s['report']=rep; app.save(sid)
            paid=(sid in PAID_SESSIONS) or not PAYWALL_ENABLED
            if paid:
                return self._json(rep)
            top_dim=max(rep.get('dimensions',[]),key=lambda d:d.get('score',0),default={})
            low_dim=min(rep.get('dimensions',[]),key=lambda d:d.get('score',9),default={})
            preview={'performance_score':rep.get('performance_score'),'outcome':rep.get('outcome'),'top_insight':(f"Strongest signal: {top_dim.get('name')} ({top_dim.get('score')}/5). Biggest opportunity: {low_dim.get('name')} ({low_dim.get('score')}/5)." if lang=='en' else f"האות החזק ביותר: {top_dim.get('name')} ({top_dim.get('score')}/5). הזדמנות השיפור הגדולה ביותר: {low_dim.get('name')} ({low_dim.get('score')}/5).")}
            return self._json({'locked':True,'preview':preview,'performance_score':rep.get('performance_score'),'outcome':rep.get('outcome'),'alpha_notice':rep.get('alpha_notice'),'price_usd':PRICE_USD})
        if p=='/api/checkout':
            try: body=self._body()
            except:return self._json({'error':'bad request'},400)
            sid=body.get('session_id'); email=(body.get('email') or '').strip()
            if not sid or sid not in app.STORE or '@' not in email:return self._json({'error':'Enter a valid email.'},400)
            if not PAYWALL_ENABLED:return self._json({'error':'Paid checkout is not active yet.'},503)
            if not CHECKOUT_URL:return self._json({'error':'Checkout provider is not configured yet.'},503)
            # Hosted checkout provider must be configured by the account owner. The provider handles card data.
            sep='&' if '?' in CHECKOUT_URL else '?'
            return self._json({'url':f'{CHECKOUT_URL}{sep}checkout[custom][session_id]={sid}&checkout[email]={email}'})
        return super().do_POST()

if __name__=='__main__':
    os.chdir(app.ROOT)
    print(f'Move A Mind v3.0 global 105-scenario platform · paywall={PAYWALL_ENABLED}')
    ThreadingHTTPServer(('0.0.0.0',app.PORT),H).serve_forever()
