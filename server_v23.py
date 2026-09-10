import os, uuid, random, datetime
from urllib.parse import urlparse, parse_qs
from http.server import ThreadingHTTPServer
import server_v22 as v22
import server_v21 as v21
from subdomains_v1 import SUBDOMAINS, get_subdomain

app = v22.app

ROLE_BY_TRACK = {
 'sales':'איש/ת מכירות או שירות','work':'מנהל/ת','military':'מפקד/ת','restaurant':'עובד/ת מסעדה',
 'parent':'הורה','teacher':'מורה/מחנכ/ת','everyday':'האדם שמנסה לקדם החלטה'
}
CHAR_BY_TRACK = {'sales':'הלקוח/ה','work':'העובד/ת','military':'החייל/ת','restaurant':'הלקוח/ה','parent':'המתבגר/ת','teacher':'ההורה','everyday':'הצד השני'}

def build_precise_scenario(track, sub):
    seed = random.choice(v21.BANK[track])
    role = ROLE_BY_TRACK[track]
    counterpart = CHAR_BY_TRACK[track]
    lens = v21.v20.EXPERT_LENSES.get(track,'')
    prompt = f'''צור תרחיש סימולציה מקצועי ומציאותי בעברית עבור Move A Mind.
תחום על: {track}
תת-תחום: {sub['he']}
הקשר מקצועי מחייב: {sub['context']}
תפקיד המתנסה: {role}
הצד שמולו: {counterpart}
עדשת מומחיות: {lens}
השתמש בתרחיש הבא כהשראה לרמת המורכבות בלבד, בלי להעתיק: {seed.get('brief','')}

דרישות מחייבות:
- התרחיש חייב להיות ספציפי לתת-התחום, עם מוצר/שירות/מצב, מחיר או טווח, זמן, אילוץ וסיבה אמינה להתנגדות כאשר רלוונטי.
- הצד השני פותח ראשון בשפה טבעית.
- מניע עמוק אחד אינו נאמר מיד; 3-5 עובדות נוספות נחשפות רק אם המתנסה שואל נכון.
- לפחות שתי תוצאות לגיטימיות; הצלחה אינה בהכרח הסכמה.
- אל תייצר התנגדות חדשה אחרי שחסם אמיתי נפתר.
- תגובות קצרות, אנושיות; רוב התגובות אינן צריכות להסתיים בשאלה.
- אין מניפולציה, הטעיה, השפלה, איום או לחץ פסול.
- בהורות/חינוך עם קטינים: גבולות בטוחים ומכבדים, ללא תוכן מסוכן.
- בבנקאות/בריאות/משפט: אל תיתן ייעוץ אישי; שמור את התרגול בתחום התקשורת והשיחה בלבד.

החזר JSON בלבד:
{{"title":"כותרת קצרה","character":"שם פרטי טבעי","brief":"2-4 משפטים ברורים","facts":"עובדות נסתרות וכללי דמות מפורטים","layers":["..."],"possible_endings":["..."],"opening":"פתיחה טבעית של הצד השני"}}'''
    raw = app.ai('Return valid JSON only in Hebrew.', [{'role':'user','content':prompt}], 1800)
    try: data = v21.scoring.extract_json(raw) or {}
    except Exception: data = {}
    if not isinstance(data, dict) or not data.get('brief') or not data.get('opening'):
        data = {
            'title': sub['he'],
            'character': seed.get('character','נועם'),
            'brief': f"את/ה {role}. הסימולציה מתרחשת בעולם של {sub['he']}. {sub['context']} הצד שמולך פותח את השיחה. המטרה היא להבין את ההתנגדות, לפעול מקצועית ולהוביל לתוצאה אמיתית ומכבדת.",
            'facts': f"הקשר תת-התחום: {sub['context']}\n{seed.get('facts','')}\nאל תחשוף את כל המידע מיד. אם חסם נפתר, אל תמציא חסם חדש.",
            'layers': seed.get('layers',[])[:5],
            'possible_endings': seed.get('possible_endings',[])[:4],
            'opening': 'אני רוצה לעצור רגע לפני שמתקדמים. יש כאן משהו שלא יושב לי נכון.'
        }
    data['label'] = app.SCENARIOS.get(track,{}).get('label', track)
    data['subdomain_id']=sub['id']; data['subdomain_he']=sub['he']; data['subdomain_en']=sub['en']
    data['facts'] = data.get('facts','') + f"\n\nשמור כל פרט בשיחה עקבי עם תת-התחום {sub['he']}."
    return data

class H(v22.H):
    def do_GET(self):
        parsed=urlparse(self.path); p=parsed.path
        if p=='/api/subdomains':
            track=parse_qs(parsed.query).get('track',[''])[0]
            if track not in SUBDOMAINS:return self._json({'error':'invalid track'},400)
            return self._json({'track':track,'subdomains':SUBDOMAINS[track]})
        if p=='/':
            html=(app.WEB/'global.html').read_text(encoding='utf-8')
            marker='<section id="chatScreen" class="screen">'
            subsec='''<section id="subchoose" class="screen"><button class="back" id="subBack">← <span id="subBackText">Back</span></button><div class="pageHead"><small id="subStep">Choose a specialty</small><h2 id="subH">Make it specific.</h2><p id="subP">Choose the world you want the conversation to come from. The scenario, objections and hidden motives will be built for that context.</p></div><div class="domains" id="subdomains"></div><div class="bottomAction"><button class="btn primary" id="subStart" disabled>Start</button></div></section>'''
            html=html.replace(marker,subsec+marker)
            inject=r'''<script>
let chosenSub=null, subCache={};
function subTxt(k){const H={back:'חזרה',step:'בחר תת־תחום',h:'עכשיו מדייקים.',p:'בחר את העולם המקצועי שממנו תגיע השיחה. התרחיש, ההתנגדויות והמניעים הנסתרים ייבנו במיוחד להקשר הזה.',start:'התחל'},E={back:'Back',step:'Choose a specialty',h:'Make it specific.',p:'Choose the professional world the conversation should come from. The scenario, objections and hidden motives will be built specifically for that context.',start:'Start'};return (lang==='he'?H:E)[k]}
function renderSubs(){const box=document.querySelector('#subdomains');box.innerHTML='';(subCache[chosen]||[]).forEach(s=>{const b=document.createElement('button');b.className='domain'+(chosenSub===s.id?' selected':'');b.innerHTML=`<div><b>${lang==='he'?s.he:s.en}</b><span>${lang==='he'?'תרחיש מדויק לעולם הזה':'A scenario built specifically for this context'}</span></div><div class="arr">›</div>`;b.onclick=()=>{chosenSub=s.id;renderSubs();document.querySelector('#subStart').disabled=false};box.appendChild(b)})}
async function openSubs(){if(!chosen)return;chosenSub=null;document.querySelector('#subStart').disabled=true;document.querySelector('#subBackText').textContent=subTxt('back');document.querySelector('#subStep').textContent=subTxt('step');document.querySelector('#subH').textContent=subTxt('h');document.querySelector('#subP').textContent=subTxt('p');document.querySelector('#subStart').textContent=subTxt('start');if(!subCache[chosen]){const r=await fetch('/api/subdomains?track='+encodeURIComponent(chosen));const j=await r.json();subCache[chosen]=j.subdomains||[]}renderSubs();go('subchoose')}
document.querySelector('#startBtn').onclick=openSubs;document.querySelector('#subBack').onclick=()=>go('choose');
async function startPrecise(){if(!chosen||!chosenSub)return;const b=document.querySelector('#subStart');b.disabled=true;b.textContent='…';try{const r=await fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({track:chosen,subdomain:chosenSub,lang})});const j=await r.json();if(!r.ok)throw Error(j.error||'start');sid=j.session_id;localStorage.setItem('mam_sid',sid);document.querySelector('#scenarioLabel').textContent=(lang==='he'?'התרחיש שלך · ':'YOUR SCENARIO · ')+(j.subdomain_label||'');document.querySelector('#scenarioTitle').textContent=j.scenario_title||'';document.querySelector('#brief').textContent=j.brief;document.querySelector('#charTitle').textContent=t('talking')+' '+j.character;document.querySelector('#turnPill').textContent=t('turn')+' 0';document.querySelector('#chat').innerHTML='';addMsg(j.message,'ai');go('chatScreen');setTimeout(()=>{document.querySelector('#msg').blur();window.scrollTo(0,0)},80)}catch(e){alert(lang==='he'?'לא ניתן לפתוח תרחיש כרגע.':'Could not open a scenario right now.')}finally{b.disabled=false;b.textContent=subTxt('start')}}
document.querySelector('#subStart').onclick=startPrecise;
const originalSetLang=setLang;setLang=function(l){originalSetLang(l);if(document.querySelector('#subchoose').classList.contains('active')){document.querySelector('#subBackText').textContent=subTxt('back');document.querySelector('#subStep').textContent=subTxt('step');document.querySelector('#subH').textContent=subTxt('h');document.querySelector('#subP').textContent=subTxt('p');document.querySelector('#subStart').textContent=subTxt('start');renderSubs()}}
</script>'''
            html=html.replace('</body>',inject+'</body>')
            b=html.encode('utf-8');self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
        return super().do_GET()

    def do_POST(self):
        p=urlparse(self.path).path
        if p!='/api/start': return super().do_POST()
        try: body=self._body()
        except:return self._json({'error':'bad request'},400)
        track=body.get('track'); subid=body.get('subdomain'); lang=body.get('lang','he')
        if not subid:
            # Preserve backward compatibility with direct starts.
            return super().do_POST()
        sub=get_subdomain(track,subid)
        if track not in v21.BANK or not sub:return self._json({'error':'invalid selection'},400)
        sc=build_precise_scenario(track,sub)
        sid=str(uuid.uuid4())
        opening=sc.get('opening') or ''
        s={'id':sid,'track':track,'subdomain':subid,'turn':0,'messages':[{'role':'assistant','content':opening}],'status':'active','created_at':datetime.datetime.utcnow().isoformat()+'Z','scenario':sc,'scenario_title':sc.get('title','')}
        app.STORE[sid]=s; app.save(sid)
        return self._json({'session_id':sid,'brief':v21.translated_brief(sc,lang),'scenario_title':v21.translated_title(sc,lang),'character':sc.get('character',''),'message':v21.maybe_translate_reply(opening,lang),'ended':False,'subdomain_label':sub['he'] if lang!='en' else sub['en'],'demo':not bool(app.API_KEY)})

if __name__=='__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v3.2 subdomain precision engine')
    ThreadingHTTPServer(('0.0.0.0',app.PORT),H).serve_forever()
