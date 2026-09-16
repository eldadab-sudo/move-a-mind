import os, json, uuid, random, datetime
from urllib.parse import urlparse
from http.server import ThreadingHTTPServer
import server_v20 as v20
import server_v18 as scoring
from scenario_bank_v1 import BANK
app=v20.app
BASE_H=v20.v19.v18.H
PRICE_USD=os.getenv('REPORT_PRICE_USD','4.90')
CHECKOUT_URL=os.getenv('CHECKOUT_URL','').strip()
PAYWALL_ENABLED=True
PAID_SESSIONS=set()
def session_scenario(s):return s.get('scenario') or app.SCENARIOS[s['track']]
def scenario_prompt(sc,track,turn):
 lens=v20.EXPERT_LENSES.get(track,'')
 return app.GLOBAL+f'''\n\nתרחיש:\n{sc.get('brief','')}\n\nעובדות נסתרות וכללי דמות:\n{sc.get('facts','')}\n\nשכבות אפשריות: {', '.join(sc.get('layers',[]))}.\nסופים לגיטימיים: {', '.join(sc.get('possible_endings',[]))}.\nמספר תור משתמש: {turn}.\n{lens}\n\nאתה מגלם רק את {sc.get('character','הדמות')}. המשתמש ממלא את התפקיד שמוגדר בתרחיש. אל תדבר בשם המשתמש. אם זה תור 0, אתה פותח ראשון באופן טבעי. אל תחשוף עובדות נסתרות בלי שהן הורווחו בשיחה.'''
def translated_brief(sc,lang):
 if lang!='en':return sc.get('brief','')
 return app.ai('Return only the English translation.',[{'role':'user','content':'Translate into polished natural English without advice:\n'+sc.get('brief','')}],350) or sc.get('brief','')
def translated_title(sc,lang):
 if lang!='en':return sc.get('title','')
 return app.ai('Return only a short English title.',[{'role':'user','content':'Translate: '+sc.get('title','')}],80) or sc.get('title','')
def maybe_translate_reply(txt,lang):
 if lang!='en' or not txt:return txt
 return app.ai('Return only the translated reply.',[{'role':'user','content':'Translate to concise natural spoken English:\n'+txt}],180) or txt
class H(BASE_H):
 def do_GET(self):
  p=urlparse(self.path).path
  if p=='/':
   b=(app.WEB/'global.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
  if p=='/legacy':
   b=(app.WEB/'index.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
  if p=='/api/catalog':return self._json({'domains':{k:len(v) for k,v in BANK.items()},'total':sum(len(v) for v in BANK.values()),'price_usd':PRICE_USD,'paywall_enabled':True})
  return super().do_GET()
 def do_POST(self):
  p=urlparse(self.path).path
  if p=='/api/start':
   try:body=self._body()
   except:return self._json({'error':'bad request'},400)
   track=body.get('track');lang=body.get('lang','he')
   if track not in BANK:return self._json({'error':'invalid track'},400)
   sc=random.choice(BANK[track]);sid=str(uuid.uuid4());s={'id':sid,'track':track,'turn':0,'messages':[],'status':'active','created_at':datetime.datetime.utcnow().isoformat()+'Z','scenario':sc,'scenario_title':sc.get('title','')};app.STORE[sid]=s
   ans=app.ai(scenario_prompt(sc,track,0),[]) or app.fallback(track,1);ended='[END]' in ans;ans=ans.replace('[END]','').strip();s['messages'].append({'role':'assistant','content':ans});s['status']='finished' if ended else 'active';app.save(sid)
   return self._json({'session_id':sid,'brief':translated_brief(sc,lang),'scenario_title':translated_title(sc,lang),'character':sc.get('character',''),'message':maybe_translate_reply(ans,lang),'ended':ended,'demo':not bool(app.API_KEY)})
  if p=='/api/chat':
   try:body=self._body()
   except:return self._json({'error':'bad request'},400)
   sid=body.get('session_id');text=(body.get('message')or'').strip();lang=body.get('lang','he')
   if sid not in app.STORE or not text:return self._json({'error':'invalid session'},400)
   s=app.STORE[sid]
   if s.get('status')!='active':return self._json({'error':'conversation ended'},400)
   s['turn']+=1;sc=session_scenario(s);s['messages'].append({'role':'user','content':text});ans=app.ai(scenario_prompt(sc,s['track'],s['turn']),s['messages']) or app.fallback(s['track'],s['turn']);ended='[END]' in ans or s['turn']>=9;ans=ans.replace('[END]','').strip();s['messages'].append({'role':'assistant','content':ans});s['status']='finished' if ended else 'active';app.save(sid);return self._json({'message':maybe_translate_reply(ans,lang),'ended':ended,'turn':s['turn']})
  if p=='/api/score':
   try:body=self._body()
   except:return self._json({'error':'bad request'},400)
   sid=body.get('session_id');lang=body.get('lang','he')
   if sid not in app.STORE:return self._json({'error':'not found'},404)
   s=app.STORE[sid];sc=session_scenario(s);rep=s.get('report')
   if not rep:
    fallback=scoring.heuristic_report(s,sc);transcript='\n'.join([('Participant' if m.get('role')=='user' else sc.get('character','Counterpart'))+': '+m.get('content','') for m in s.get('messages',[])]);reflection=body.get('reflection')or{};rule='Write all report fields in English.' if lang=='en' else 'כתוב את כל שדות הדוח בעברית.'
    prompt=f'''You are a rigorous conversation-performance evaluator. Analyze behavior in this conversation only; do not diagnose personality.\nScenario: {sc.get('brief','')}\nTranscript:\n{transcript}\nSelf-reflection: {json.dumps(reflection,ensure_ascii=False)}\nScore exactly these 10 dimensions from 1.0 to 5.0: {', '.join(app.DIMS)}. For every dimension provide specific transcript evidence. Give 3 strengths, 3 improvements, the turning point, one better phrase, outcome analysis and a 5-8 sentence summary. Return JSON only. {rule}\nSchema: {{"dimensions":[{{"name":"...","score":4.2,"evidence":"..."}}],"outcome":"...","strengths":["..."],"improvements":["..."],"turning_point":"...","better_phrase":"...","summary":"..."}}'''
    raw=app.ai('Return valid JSON only.',[{'role':'user','content':prompt}],2400);rep=scoring.normalize_report(scoring.extract_json(raw),fallback);rep['alpha_notice']='Experimental performance feedback for this conversation only — not a validated psychological measure.' if lang=='en' else 'משוב ביצוע ניסויי לשיחה הזו בלבד — אינו מדד פסיכולוגי מאומת.';s['report']=rep;app.save(sid)
   ent=s.get('entitlements')or{};paid=(sid in PAID_SESSIONS) or bool(ent.get('deep') or ent.get('pro'))
   if paid:return self._json(rep)
   dims=rep.get('dimensions',[]);top=max(dims,key=lambda d:d.get('score',0),default={})
   top_insight=(f"Your strongest signal was {top.get('name','one conversation skill')} ({top.get('score','—')}/5). The full report shows the evidence, turning point, weaker dimensions and exactly what to change next." if lang=='en' else f"החוזקה הבולטת שלך בשיחה הייתה {top.get('name','אחד מממדי השיחה')} ({top.get('score','—')}/5). בדוח המלא תראה את הראיות, נקודת המפנה, הממדים החלשים ומה בדיוק כדאי לשנות בשיחה הבאה.")
   preview={'performance_score':rep.get('performance_score'),'top_insight':top_insight}
   return self._json({'locked':True,'preview':preview,'performance_score':rep.get('performance_score'),'alpha_notice':rep.get('alpha_notice'),'price_usd':PRICE_USD})
  return super().do_POST()
if __name__=='__main__':
 os.chdir(app.ROOT);ThreadingHTTPServer(('0.0.0.0',app.PORT),H).serve_forever()
