import os
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse
import server_v41 as v41
import server_v21 as v21

app = v41.app


def grounded_prompt(sc, track, turn, messages):
    lens = v21.v20.EXPERT_LENSES.get(track, '')
    recent = messages[-8:]
    transcript = '\n'.join(
        ('משתמש' if m.get('role') == 'user' else sc.get('character', 'הדמות')) + ': ' + (m.get('content') or '')
        for m in recent
    )
    rules = f"""

אתה מנוע סימולציה לשיחה מציאותית. אתה מגלם אך ורק את {sc.get('character','הדמות')} בתרחיש הבא.

תרחיש:
{sc.get('brief','')}

עובדות נסתרות וכללי דמות:
{sc.get('facts','')}

שכבות אפשריות: {', '.join(sc.get('layers',[]))}.
סופים לגיטימיים: {', '.join(sc.get('possible_endings',[]))}.
מספר תור משתמש: {turn}.
{lens}

השיחה האחרונה:
{transcript}

כללי תגובה מחייבים:
1. זהה תחילה מה המשתמש אמר עכשיו ומה הוא שואל, טוען או מבקש. התגובה חייבת להתייחס ישירות לכך.
2. שמור רציפות מלאה עם העובדות שכבר נאמרו. אל תחליף נושא, אל תסתור פרט קודם ואל תחזור על שאלה שכבר נענתה.
3. הישאר בדמות ובתחום התרחיש בלבד. אל תיתן עצות, ציונים, משוב או הסבר על הסימולציה בזמן השיחה.
4. לשאלת הבהרה רלוונטית ענה כדמות. אם המידע אינו קיים בעובדות התרחיש או בשיחה, אמור באופן טבעי שאינך יודע במקום להמציא.
5. אם המשתמש מניח הנחה שגויה לגבי מה שנאמר, תקן אותה באופן טבעי וקצר מתוך הדמות.
6. קדם את אותו חוט שיחה: תשובה ישירה, תגובה עניינית או רגשית מתאימה, ואז לכל היותר שאלה אחת טבעית שמעמיקה את הנושא.
7. אל תייצר התנגדות אקראית. התנגדות חייבת לנבוע מעובדות התרחיש, מאינטרס של הדמות או ישירות מדברי המשתמש.
8. אל תחשוף עובדות נסתרות אלא אם המשתמש בירר באופן שמצדיק זאת.
9. כתוב בעברית טבעית ושיחתית, בדרך כלל 1–4 משפטים.
10. אל תכתוב [END]. השיחה מסתיימת רק כשהמשתמש בוחר לסיים.

השב עכשיו רק כדמות ורק להודעה האחרונה של המשתמש.
"""
    return app.GLOBAL + rules


class H(v41.H):
    def do_POST(self):
        if urlparse(self.path).path != '/api/chat':
            return super().do_POST()
        try:
            body = self._body()
        except Exception:
            return self._json({'error': 'bad request'}, 400)
        sid = body.get('session_id')
        text = (body.get('message') or '').strip()
        lang = body.get('lang', 'he')
        if sid not in app.STORE or not text:
            return self._json({'error': 'invalid session'}, 400)
        s = app.STORE[sid]
        if s.get('status') != 'active':
            return self._json({'error': 'conversation ended'}, 400)
        s['turn'] += 1
        sc = v21.session_scenario(s)
        s['messages'].append({'role': 'user', 'content': text})
        prompt = grounded_prompt(sc, s['track'], s['turn'], s['messages'])
        ans = app.ai(prompt, s['messages'])
        if not ans:
            ans = 'אני רוצה להבין את הנקודה הזו טוב יותר. תוכל/י לפרט למה זה חשוב מבחינתך?'
        ans = (ans or '').replace('[END]', '').strip()
        s['messages'].append({'role': 'assistant', 'content': ans})
        s['status'] = 'active'
        app.save(sid)
        return self._json({'message': v21.maybe_translate_reply(ans, lang), 'ended': False, 'turn': s['turn']})


if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.27.1 - grounded context-aware conversation engine')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), H).serve_forever()
