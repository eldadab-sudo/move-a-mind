import os
import server_v16 as v16
from http.server import ThreadingHTTPServer

app = v16.app

index_path = app.WEB / 'index.html'
html = index_path.read_text(encoding='utf-8')

# Do not autofocus the message box when opening a scenario on mobile.
html = html.replace("go(\"s4\");$(\"#msg\").focus()", "go(\"s4\");setTimeout(()=>{try{$(\"#msg\").blur()}catch(e){};window.scrollTo(0,0);document.getElementById('s4').scrollIntoView({block:'start'});},80)")
html = html.replace("go('s4');$('#msg').focus()", "go('s4');setTimeout(()=>{try{$('#msg').blur()}catch(e){};window.scrollTo(0,0);document.getElementById('s4').scrollIntoView({block:'start'});},80)")

# Make sure conversation screen is anchored at the top, not vertically centered.
html = html.replace('.screen.active{display:flex}', '.screen.active{display:flex}.screen#s4.active{align-items:flex-start;padding-top:10px}')

index_path.write_text(html, encoding='utf-8')

if __name__ == '__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v2.1 mobile scenario-first fix')
    ThreadingHTTPServer(('0.0.0.0', app.PORT), v16.v15.v14.H).serve_forever()
