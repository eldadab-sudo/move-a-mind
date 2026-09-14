import os
from http.server import ThreadingHTTPServer
import server_v34 as v34
import server_v21 as v21

app = v34.app
PREVIOUS_PROMPT = v21.scenario_prompt

def resilient_dialogue_prompt(sc, track, turn):
    base = PREVIOUS_PROMPT(sc, track, turn)
    return base + '''

כלל טכני קריטי:
- אל תכתוב [END] ואל תסיים את הסשן בעצמך. גם אם מבחינה אנושית הושגה הסכמה, הגב באופן טבעי כאדם והנח למשתמש להחליט אם לסיים באמצעות כפתור "סיימתי את השיחה".
- אם הושגה הסכמה מוקדם, אפשר לענות במשפט קצר שמאשר אותה או מסכם את הצעד הבא, אבל השיחה נשארת פתוחה.
'''

v21.scenario_prompt = resilient_dialogue_prompt

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v4.4 prevent premature conversation lock')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), v34.v33.H).serve_forever()
