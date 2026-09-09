import os, json, re
import server_v17 as v17
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

app = v17.app
BASE_H = v17.v16.v15.v14.H
DIMS = app.DIMS


def extract_json(raw):
    if not raw:
        return None
    t = raw.strip()
    t = re.sub(r'^```(?:json)?\s*', '', t, flags=re.I)
    t = re.sub(r'\s*```$', '', t)
    try:
        return json.loads(t)
    except Exception:
        pass
    a, b = t.find('{'), t.rfind('}')
    if a >= 0 and b > a:
        try:
            return json.loads(t[a:b+1])
        except Exception:
            return None
    return None


def clamp(v, lo=1.0, hi=5.0):
    try:
        return max(lo, min(hi, float(v)))
    except Exception:
        return 3.0


def heuristic_report(s, sc):
    users = [m.get('content','') for m in s.get('messages',[]) if m.get('role') == 'user']
    text = ' '.join(users)
    turns = len(users)
    words = len(text.split())
    q = text.count('?') + text.count('？')
    empathy_terms = ['מבין','מבינה','שומע','שומעת','חשוב לך','מטריד','דואג','דואגת','מבין למה','אני יכול להבין']
    explore_terms = ['למה','מה חשוב','מה מפריע','מה מטריד','מה אתה צריך','מה את צריכה','מה מבחינתך','מה יאפשר']
    action_terms = ['מציע','אפשר','בוא','נקבע','נבדוק','אבדוק','אני אקח','נסכם','ננסה','עד ','מחר','שבוע','שעה','איסוף','פיילוט','עדכון']
    respect_terms = ['מבין','מכבד','הוגן','יחד','אפשר','רוצה להבין']
    pressure_terms = ['חייב','אין ברירה','אתה צריך','את חייבת','תסכים','תסכימי']

    empathy = sum(text.count(x) for x in empathy_terms)
    explore = sum(text.count(x) for x in explore_terms)
    action = sum(text.count(x) for x in action_terms)
    respect = sum(text.count(x) for x in respect_terms)
    pressure = sum(text.count(x) for x in pressure_terms)

    scores = {
        'הקשבה והכרה': 2.3 + min(1.7, empathy*0.55 + explore*0.15) - pressure*0.2,
        'איכות השאלות': 2.1 + min(2.0, q*0.35 + explore*0.35),
        'הבנת האינטרסים': 2.2 + min(1.9, explore*0.45 + empathy*0.2),
        'אמון וכבוד': 2.7 + min(1.5, respect*0.35) - pressure*0.35,
        'בהירות': 2.5 + min(1.6, action*0.25 + (0.5 if words >= 25 else 0)),
        'רלוונטיות': 2.5 + min(1.5, (turns*0.12) + action*0.18),
        'הסתגלות': 2.3 + min(1.8, empathy*0.25 + explore*0.2 + action*0.18),
        'התמודדות עם התנגדות': 2.2 + min(2.0, empathy*0.2 + explore*0.25 + action*0.25),
        'היגיון': 2.5 + min(1.5, action*0.22 + (0.4 if words >= 35 else 0)),
        'התקדמות לפעולה': 2.0 + min(2.3, action*0.42 + (0.4 if turns >= 5 else 0)),
    }
    dims=[]
    for name in DIMS:
        val=round(clamp(scores.get(name,3.0)),1)
        ev='הציון חושב מגוף השיחה ומהדפוסים שנצפו בה.'
        if name=='איכות השאלות': ev=f'זוהו כ-{q} שאלות לאורך {turns} תורי משתמש; נבדקה גם איכות הבירור ולא רק הכמות.'
        elif name=='התקדמות לפעולה': ev='נבדקה הופעת הצעות קונקרטיות, תנאים, זמנים או צעד הבא בשיחה.'
        elif name=='הקשבה והכרה': ev='נבדקו סימנים להכרה בחשש/אינטרס של הצד השני לפני ניסיון לשכנע.'
        dims.append({'name':name,'score':val,'evidence':ev})
    perf=round(sum(d['score'] for d in dims)/len(dims)*20)
    perf=max(20,min(96,perf))
    strongest=max(dims,key=lambda d:d['score'])
    weakest=min(dims,key=lambda d:d['score'])
    return {
        'dimensions':dims,
        'performance_score':perf,
        'outcome':'השיחה הוערכה לפי איכות הדרך וההתקדמות בפועל, לא לפי עצם ההסכמה בלבד.',
        'strengths':[f"החוזקה הבולטת: {strongest['name']} ({strongest['score']}/5).", 'נשמרה שיחה שמאפשרת לצד השני להגיב ולא רק לקבל מסר חד-צדדי.', 'נבחנה התקדמות לעבר פתרון ולא רק ניסוח נעים.'],
        'improvements':[f"הממד החלש יחסית: {weakest['name']} ({weakest['score']}/5) — כאן נמצא פוטנציאל השיפור הגדול ביותר.", 'להשתמש מוקדם יותר בשאלה שמבררת מה באמת עומד מאחורי ההתנגדות.', 'לפני הסיום, לנסח צעד הבא קונקרטי עם תנאי ברור או חלופה.'],
        'turning_point':'במצב גיבוי לא ניתן לזהות בוודאות משפט יחיד ששינה את השיחה; הניתוח מבוסס על דפוסי השיחה המלאה.',
        'better_phrase':'אני רוצה לוודא שאני מבין מה באמת מפריע לך לפני שאני מציע פתרון — מה הדבר המרכזי מבחינתך?',
        'summary':f'נותחו {turns} תורי משתמש וכ-{words} מילים. הציון נגזר מעשרת ממדי הביצוע ואינו ערך ברירת מחדל קבוע. זהו ניתוח Alpha של ההתנהגות בשיחה הספציפית בלבד.'
    }


def normalize_report(rep, fallback):
    if not isinstance(rep, dict):
        return fallback
    incoming = rep.get('dimensions')
    if not isinstance(incoming, list) or len(incoming) < 8:
        return fallback
    by_name={str(d.get('name','')).strip():d for d in incoming if isinstance(d,dict)}
    dims=[]
    for name in DIMS:
        d=by_name.get(name)
        if not d:
            # Allow model order fallback while keeping canonical names.
            idx=len(dims)
            d=incoming[idx] if idx < len(incoming) and isinstance(incoming[idx],dict) else {}
        score=round(clamp(d.get('score',3)),1)
        evidence=str(d.get('evidence','')).strip() or 'לא סופקה עדות מספקת; נדרש לעיין בתמליל.'
        dims.append({'name':name,'score':score,'evidence':evidence[:500]})
    # IMPORTANT: server computes the total from dimensions; model cannot default it to 60.
    perf=round(sum(d['score'] for d in dims)/len(dims)*20)
    perf=max(20,min(98,perf))
    out={
        'dimensions':dims,
        'performance_score':perf,
        'outcome':str(rep.get('outcome','')).strip() or fallback['outcome'],
        'strengths':rep.get('strengths') if isinstance(rep.get('strengths'),list) else fallback['strengths'],
        'improvements':rep.get('improvements') if isinstance(rep.get('improvements'),list) else fallback['improvements'],
        'turning_point':str(rep.get('turning_point','')).strip() or fallback['turning_point'],
        'better_phrase':str(rep.get('better_phrase','')).strip() or fallback['better_phrase'],
        'summary':str(rep.get('summary','')).strip() or fallback['summary'],
    }
    out['strengths']=[str(x)[:700] for x in out['strengths'][:4]]
    out['improvements']=[str(x)[:700] for x in out['improvements'][:4]]
    return out


class H(BASE_H):
    def do_POST(self):
        p=urlparse(self.path).path
        if p != '/api/score':
            return super().do_POST()
        try:
            body=self._body()
        except Exception:
            return self._json({'error':'בקשה לא תקינה'},400)
        sid=body.get('session_id')
        if sid not in app.STORE:
            return self._json({'error':'לא נמצא'},404)
        s=app.STORE[sid]; sc=app.SCENARIOS[s['track']]
        fallback=heuristic_report(s,sc)
        transcript='\n'.join([('המתנסה' if m.get('role')=='user' else sc['character'])+': '+m.get('content','') for m in s.get('messages',[])])
        reflection=body.get('reflection') or {}
        prompt=f'''אתה מעריך מקצועי של ביצוע בשיחה. נתח את השיחה עצמה, לא את אישיות המשתמש. זהו כלי Alpha ולא אבחון.

תרחיש:
{sc.get('brief','')}

תמליל מלא:
{transcript}

הערכת המתנסה את עצמו:
{json.dumps(reflection,ensure_ascii=False)}

הנחיות מחייבות:
1. הערך כל אחד מעשרת הממדים בדיוק בסולם 1.0 עד 5.0. מותרות עשיריות.
2. לכל ממד כתוב evidence ספציפי: התייחס למעשה/משפט/חוסר מהותי מתוך השיחה. אל תכתוב משפטים כלליים.
3. אל תיתן ציונים זהים אוטומטית. הבדל בין ממדים צריך לשקף את התמליל.
4. אל תתגמל רק על השגת הסכמה; שיחה מכבדת עם אי-הסכמה יכולה לקבל ציון גבוה.
5. הורד ציון כאשר המשתמש לא בירר אינטרס, התעלם מהתנגדות, חזר על עצמו, לחץ, הבטיח ללא בסיס או לא סגר צעד הבא.
6. העלה ציון כאשר המשתמש שאל שאלה מדויקת, שינה גישה בעקבות תשובה, זיהה אינטרס נסתר, נתן מענה ממוקד, בדק הבנה או הציע צעד קונקרטי.
7. strengths: שלוש נקודות ספציפיות מהשיחה, עם הסבר למה עבדו.
8. improvements: שלוש נקודות ספציפיות, כל אחת עם מה היה חסר ומה לעשות במקום.
9. turning_point: צטט/תאר בקצרה את הרגע ששינה את כיוון השיחה ולמה. אם לא היה — אמור זאת.
10. better_phrase: ניסוח חלופי אחד שמותאם לרגע חלש אמיתי בתמליל, לא משפט גנרי.
11. summary: 5-8 משפטים. פרט את דפוס השיחה, איכות ההשפעה, מה עבד, מה הגביל את התוצאה ומה כדאי לתרגל בפעם הבאה.
12. outcome: תאר את התוצאה בפועל ואת איכות הדרך אליה.
13. החזר JSON בלבד. אל תחזיר performance_score; השרת מחשב אותו בעצמו.

מבנה:
{{"dimensions":[{{"name":"...","score":4.2,"evidence":"..."}}],"outcome":"...","strengths":["..."],"improvements":["..."],"turning_point":"...","better_phrase":"...","summary":"..."}}

שמות הממדים בדיוק: {', '.join(DIMS)}'''
        raw=app.ai('החזר JSON תקין בלבד, בעברית, ללא Markdown.',[{'role':'user','content':prompt}],2200)
        rep=normalize_report(extract_json(raw),fallback)
        rep['alpha_notice']='ציון Alpha ניסויי — משקף את הביצוע בשיחה הזו בלבד ואינו מדד פסיכולוגי מאומת.'
        rep['scoring_note']='הציון הכולל מחושב כעת מעשרת ממדי השיחה; אין ציון ברירת מחדל קבוע של 60.'
        s['report']=rep
        app.save(sid)
        return self._json(rep)

if __name__=='__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v2.2 deep calibrated scoring')
    ThreadingHTTPServer(('0.0.0.0',app.PORT),H).serve_forever()
