import os
import server_v15 as v15
from http.server import ThreadingHTTPServer

app = v15.app
index_path = app.WEB / 'index.html'
html = index_path.read_text(encoding='utf-8')

# Conversation screen must start at the top so the scenario is the first thing visible.
html = html.replace(
    '.screen.active{display:flex}',
    '.screen.active{display:flex}#s4.screen{align-items:flex-start;padding-top:10px}'
)

# Make the scenario itself visually dominant before the dialogue begins.
html = html.replace(
    '.brief{background:#faf8f5;border:1px solid var(--line);border-radius:16px;padding:14px;font-size:14px;line-height:1.55}',
    '.brief{background:#faf8f5;border:1px solid var(--line);border-radius:16px;padding:14px;font-size:14px;line-height:1.55}#s4 .brief{font-size:16px;line-height:1.7;padding:18px;background:#fff;box-shadow:var(--shadow);margin-bottom:8px}'
)

# Remove finish button from the top header.
html = html.replace(
    '<button class="btn alt" style="width:auto;padding:10px 14px" id="finishBtn">סיימתי</button>',
    ''
)

# Put finish action below the composer, where it belongs at the end of the conversation.
html = html.replace(
    '<div class="composer"><textarea id="msg" placeholder="כתוב כפי שהיית מדבר במציאות..."></textarea><button id="sendBtn" class="btn send">שלח</button></div><div class="small" id="demoNote"></div>',
    '<div class="composer"><textarea id="msg" placeholder="כתוב כפי שהיית מדבר במציאות..."></textarea><button id="sendBtn" class="btn send">שלח</button></div><div class="small" id="demoNote"></div><div style="margin-top:14px"><button class="btn alt" id="finishBtn">סיימתי את השיחה</button></div>'
)

# After choosing a domain, start immediately and show the scenario; skip the redundant pre-start screen.
html = html.replace(
    '<button id="continueBtn" class="btn" disabled>המשך</button>',
    '<button id="continueBtn" class="btn" disabled>הצג תרחיש והתחל</button>'
)
html = html.replace(
    '$('#+'"continueBtn"'+').onclick=()=>go("s3");',
    '$('#+'"continueBtn"'+').onclick=()=>$('#+'"startBtn"'+').click();'
)

# If the exact JS string is stored without concatenation artifacts, replace it directly too.
html = html.replace('$("#continueBtn").onclick=()=>go("s3");','$("#continueBtn").onclick=()=>$("#startBtn").click();')

index_path.write_text(html, encoding='utf-8')

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v2.0 scenario-first conversation UX')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), v15.v14.H).serve_forever()
