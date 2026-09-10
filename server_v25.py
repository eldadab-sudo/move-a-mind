import os
from http.server import ThreadingHTTPServer
import server_v24 as v24

app = v24.app

ROLE_LABELS = {
    'sales': ('איש/ת המכירות או השירות', 'הלקוח/ה'),
    'work': ('המנהל/ת', 'העובד/ת'),
    'military': ('המפקד/ת', 'החייל/ת'),
    'restaurant': ('עובד/ת המסעדה', 'הלקוח/ה'),
    'parent': ('ההורה', 'המתבגר/ת'),
    'teacher': ('המורה/מחנכ/ת', 'ההורה'),
    'everyday': ('האדם שמנסה לקדם את ההחלטה', 'הצד השני'),
}

OPENINGS = {
    'sales': 'אני הלקוח/ה. אני כן מתעניין/ת במה שאתם מציעים, אבל לפני שאני מתקדם/ת אני צריך/ה להבין למה זה באמת עדיף לי ומה הסיכון מבחינתי.',
    'work': 'אני העובד/ת. אני רוצה שנדבר על המצב הזה, כי מבחינתי הוא כבר דורש שינוי ולא הייתי רוצה לקבל רק תשובה של כן או לא.',
    'military': 'המפקד/ת, אני רוצה לדבר איתך על המצב שלי בצוות. מבחינתי צריך להשתנות כאן משהו, ואני רוצה שתשמע/י קודם למה.',
    'restaurant': 'אני הלקוח/ה. אני רוצה שתבין/י מה קרה כאן, כי מבחינתי הבעיה היא לא רק התקלה עצמה אלא גם איך שטיפלו בי אחריה.',
    'parent': 'אמא/אבא, אני רוצה שתשמע/י אותי עד הסוף לפני שאת/ה מחליט/ה. אני מבקש/ת שנשנה את ההסכמה שיש בינינו בנושא הזה.',
    'teacher': 'אני ההורה. לפני שאני מסכים/ה להצעה שלכם, אני רוצה להבין למה אתם חושבים שזה נכון לילד שלי ומה יקרה אם זה לא יעבוד.',
    'everyday': 'אני הצד השני בשיחה. אני מבין/ה למה את/ה רוצה לשנות את ההחלטה, אבל מבחינתי יש כאן בעיה שצריך לפתור לפני שאסכים.',
}

_original_instant = v24.instant_scenario

def explicit_role_scenario(track, sub):
    sc = _original_instant(track, sub)
    user_role, other_role = ROLE_LABELS[track]
    char = sc.get('character', '')
    old_brief = sc.get('brief', '')
    if old_brief.startswith('התפקיד שלך:'):
        parts = old_brief.split('\n\n', 1)
        old_brief = parts[1] if len(parts) > 1 else old_brief
    sc['brief'] = (
        f"את/ה בתפקיד: {user_role}.\n"
        f"מולך: {char} — {other_role}.\n"
        f"מי מתחיל/ה: {char} ({other_role}) פותח/ת את השיחה ראשון/ה.\n"
        f"מה את/ה עושה: את/ה מקשיב/ה לפתיחה ואז עונה מתוך התפקיד שלך — {user_role}.\n\n"
        f"{old_brief}"
    )
    sc['opening'] = OPENINGS[track]
    sc['facts'] = sc.get('facts','') + (
        f"\n\nחלוקת תפקידים מחייבת: המשתמש הוא {user_role}. "
        f"אתה מגלם את {char}, שהוא/היא {other_role}. "
        f"אתה פותח את השיחה ראשון. לאחר מכן המשתמש עונה. "
        f"אסור להחליף תפקידים או לדבר בשם המשתמש."
    )
    return sc

v24.instant_scenario = explicit_role_scenario

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v3.4 explicit conversation roles')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), v24.H).serve_forever()
