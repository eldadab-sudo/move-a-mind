import os
from http.server import ThreadingHTTPServer
import server_v25 as v25

app = v25.app

# Refine the domain-selection UX before the inherited server serves global.html.
index_path = app.WEB / 'global.html'
html = index_path.read_text(encoding='utf-8')

# Stronger, more intriguing domain-selection headline.
html = html.replace(
    "chooseH:'Where do you want to test yourself?'",
    "chooseH:'Where do you want to discover how much influence you really have?'"
)
html = html.replace(
    "chooseH:'איפה אתה רוצה לבחון את עצמך?'",
    "chooseH:'באיזו זירה אתה רוצה לגלות כמה השפעה באמת יש לך?'"
)
html = html.replace(
    '<h2 data-t="chooseH">Where do you want to test yourself?</h2>',
    '<h2 data-t="chooseH">Where do you want to discover how much influence you really have?</h2>'
)

# Remove the redundant Start button from the domain screen.
html = html.replace(
    '<div class="bottomAction"><button class="btn primary" id="startBtn" disabled data-t="start">Start</button></div>',
    '<button id="startBtn" style="display:none" aria-hidden="true"></button>'
)

# Clicking a domain now advances immediately to its subdomain screen.
old = "b.onclick=()=>{chosen=id;renderDomains();$('#startBtn').disabled=false}"
new = "b.onclick=()=>{chosen=id;renderDomains();const sb=$('#startBtn');if(sb)sb.disabled=false;setTimeout(()=>{if(typeof openSubs==='function'){openSubs()}else if(sb){sb.click()}},0)}"
html = html.replace(old, new)

index_path.write_text(html, encoding='utf-8')

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v3.5 sharper domain choice direct navigation')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), v25.v24.H).serve_forever()
