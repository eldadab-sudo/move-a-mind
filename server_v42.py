import os
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse
import server_v41 as v41
import server_v21 as v21

app = v41.app


def grounded_prompt(sc, track, turn, messages):
    lens = v21.v20.EXPERT_LENSES.get(track, '')
    recent = messages[-10:]
    transcript = '\n'.join(
        ('משתמש' if m.get('role') == 'user' else sc.get('character', 'הדמות')) + ': ' + (m.get('content') or '')
        for m in recent
    )
    last_user = next((m.get('content','') for m in reversed(messages) if m.get('role') == 'user'), '')
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

הודעת המשתמש האחרונה, שהיא העוגן לתגובה:
{last_user}

כללי תגובה מחייבים:
1. ענה קודם כל למשמעות המדויקת של הודעת המשתמש האחרונה. כל משפט בתגובה צריך להיות קשור אליה או לפרט שכבר הופיע בשיחה/בתרחיש.
2. השתמש במילים ובמושגים הקונקרטיים של השיחה. אל תחליף אותם במונחים דרמטיים, מקצועיים או מופשטים שלא נאמרו.
3. אסור להכניס מושג חדש שמרמז על עובדה, בעיה או מצב שלא קיימים בתרחיש או בשיחה. בפרט אל תשתמש במילים כגון "הסלמה", "להסלים", "מסלימים", "משבר", "איום", "לחץ", "סיכון" או מונחים דומים אלא אם אותו רעיון כבר עלה במפורש בשיחה או בעובדות התרחיש.
4. אם המשתמש שואל על פרט עובדתי (למשל מחיר, תנאים, זמן, תקלה, אחריות, תהליך), ענה ישירות על אותו פרט ורק אחר כך, אם טבעי, שאל שאלה אחת שמקדמת אותו.
5. שמור רציפות מלאה: אל תחליף נושא, אל תסתור פרט קודם ואל תחזור על שאלה שכבר נענתה.
6. הישאר בדמות ובתחום התרחיש בלבד. אל תיתן עצות, ציונים, משוב או הסבר על הסימולציה בזמן השיחה.
7. אם מידע אינו קיים בעובדות התרחיש או בשיחה, אל תמציא אותו. אמור באופן טבעי שאין לך כרגע את המידע או בקש הבהרה קצרה.
8. התנגדות או קושי חייבים לנבוע ישירות מעובדה קיימת, מאינטרס מפורש של הדמות או מדברי המשתמש. אין ליצור התנגדות אקראית כדי "להקשות".
9. אל תחשוף עובדות נסתרות אלא אם המשתמש בירר באופן שמצדיק זאת.
10. כתוב בעברית טבעית, פשוטה ושיחתית, בדרך כלל 1–3 משפטים. העדף ניסוח כמו שאדם אמיתי היה אומר בשיחה, לא שפת דוח או ייעוץ.
11. לפני התשובה בצע בדיקה פנימית: האם הכנסתי מילה או נושא שלא נובעים מההודעה האחרונה או מההקשר? אם כן, מחק אותם ונסח מחדש. אל תציג את הבדיקה למשתמש.
12. אם הצדדים הגיעו להסכמה ברורה, החלטה מעשית או סגירה טבעית של העניין, אל תמשיך לפתוח שוב את אותו נושא ואל תחזור על אותה התחייבות. הגב בקצרה ובטבעיות כאדם שמסיים שיחה.\n13. הימנע מחזרה סמנטית: לפני התשובה השווה אותה ל-3 התגובות האחרונות של הדמות. אם היא אומרת למעשה אותו דבר, נסח תגובה שונה שמקדמת או סוגרת את השיחה.\n14. אל תכתוב [END]. השיחה מסתיימת רק כשהמשתמש בוחר לסיים.

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
            ans = 'אני רוצה להבין את הנקודה הזו טוב יותר. תוכל/י לפרט?'
        ans = (ans or '').replace('[END]', '').strip()
        # Guard against near-verbatim repetition from the model.
        prev=[(m.get('content') or '').strip() for m in s.get('messages',[]) if m.get('role')=='assistant'][-3:]
        def norm(x):
            import re
            return set(re.findall(r'[\\wא-ת]+',x.lower()))
        a=norm(ans)
        repeated=False
        for p in prev:
            b=norm(p)
            if a and b and len(a & b)/max(1,min(len(a),len(b)))>=0.72:
                repeated=True;break
        if repeated:
            retry=prompt+"\\nהתגובה הראשונה שלך חזרה על תגובה קודמת. נסח עכשיו תגובה חדשה וקצרה שאינה חוזרת על מידע שכבר נאמר. אם העניין כבר נסגר, הסתפק באישור טבעי קצר וסגור את הנושא."
            ans2=app.ai(retry,s['messages'])
            if ans2: ans=(ans2 or '').replace('[END]','').strip()
        s['messages'].append({'role': 'assistant', 'content': ans})
        s['status'] = 'active'
        app.save(sid)
        return self._json({'message': v21.maybe_translate_reply(ans, lang), 'ended': False, 'turn': s['turn']})


if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.39 - repetition guard + end-state quality')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), H).serve_forever()
