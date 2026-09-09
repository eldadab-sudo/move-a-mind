import os
import server_v14 as v14
from http.server import ThreadingHTTPServer

app = v14.app

# Refine the raw landing page before the inherited UI transformations run.
index_path = app.WEB / 'index.html'
html = index_path.read_text(encoding='utf-8')

# Fix English headline direction so the question mark renders at the true end.
html = html.replace(
    '<h1>How well can you<br>move a mind?</h1>',
    '<h1 dir="ltr" style="direction:ltr;unicode-bidi:isolate">How well can you<br>move a mind?</h1>'
)

# Premium, clearer positioning copy.
html = html.replace(
    '<h2>עד כמה אתה באמת יודע להשפיע?</h2><p>יש לך כמה דקות לגרום לאדם שמולך לעצור, להקשיב ולשקול מחדש — בלי לחץ, בלי טריקים ובלי תשובה מוכנה מראש.</p><button class="btn" onclick="go(\'s2\')">בדוק אותי</button>',
    '<h2>עד כמה אתה באמת יודע להשפיע בשיחה?</h2><p><strong style="color:var(--ink)">היכולת להשפיע אינה נמדדת בכמה אתה מדבר — אלא בכמה אתה מבין את האדם שמולך.</strong><br><br>Move A Mind היא סימולציית שיחות דינמית שבוחנת כיצד אתה מזהה התנגדויות, קורא אינטרסים, בונה אמון ומוביל אנשים לעבר החלטה.<br><br>כל תגובה שלך משנה את השיחה. לפעמים תוביל להסכמה, לפעמים לפשרה — ולפעמים המהלך הנכון הוא דווקא לדעת מתי לא לדחוף יותר.</p><button class="btn" onclick="go(\'s2\')">התחל סימולציה</button>'
)

# If a previous dynamic copy version is already present in the source, replace that as well.
html = html.replace(
    '<h2>עד כמה אתה באמת יודע להשפיע בשיחה?</h2><p>Move A Mind היא סימולציית שיחות. בכל תרחיש תפגוש אדם שמתנגד לעמדה שלך, לבקשה שלך או לפתרון שאתה מציע. המטרה היא להבין מה עומד מאחורי ההתנגדות, להגיב נכון ולהוביל את השיחה לתוצאה — הסכמה, פעולה, פשרה או גם אי-הסכמה מכבדת.</p>',
    '<h2>עד כמה אתה באמת יודע להשפיע בשיחה?</h2><p><strong style="color:var(--ink)">היכולת להשפיע אינה נמדדת בכמה אתה מדבר — אלא בכמה אתה מבין את האדם שמולך.</strong><br><br>Move A Mind היא סימולציית שיחות דינמית שבוחנת כיצד אתה מזהה התנגדויות, קורא אינטרסים, בונה אמון ומוביל אנשים לעבר החלטה.<br><br>כל תגובה שלך משנה את השיחה. לפעמים תוביל להסכמה, לפעמים לפשרה — ולפעמים המהלך הנכון הוא דווקא לדעת מתי לא לדחוף יותר.</p>'
)

index_path.write_text(html, encoding='utf-8')

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v1.9 premium landing copy')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), v14.H).serve_forever()
