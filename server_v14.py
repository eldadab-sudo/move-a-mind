import os, json, csv, io, html, datetime
import server_v13 as v13
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path

app = v13.app
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN','').strip()
FEEDBACK_PATH = Path(os.getenv('FEEDBACK_PATH','/persistent/pilot_feedback.jsonl'))
FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)

FIELDS = ['created_at','name','track','realism','difficulty','naturalness','length_fit','responsiveness','ending','try_again','best','change','scenario_idea','overall']

def load_feedback():
    rows=[]
    if not FEEDBACK_PATH.exists():
        return rows
    with FEEDBACK_PATH.open('r',encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try: rows.append(json.loads(line))
            except: pass
    return rows

def save_feedback(record):
    with FEEDBACK_PATH.open('a',encoding='utf-8') as f:
        f.write(json.dumps(record,ensure_ascii=False)+'\n')

def authorized(path):
    if not ADMIN_TOKEN: return False
    q=parse_qs(urlparse(path).query)
    return q.get('token',[''])[0] == ADMIN_TOKEN

def avg(rows,key):
    vals=[]
    for r in rows:
        try: vals.append(float(r.get(key,'')))
        except: pass
    return round(sum(vals)/len(vals),1) if vals else '-'

class H(v13.v12.v11.v10.H):
    def do_GET(self):
        p=urlparse(self.path).path
        if p == '/admin-feedback':
            if not authorized(self.path):
                return self._json({'error':'אין הרשאה'},403)
            rows=load_feedback()
            by_track={}
            for r in rows:
                by_track[r.get('track','לא ידוע')] = by_track.get(r.get('track','לא ידוע'),0)+1
            cards=f'''
            <div class="cards">
              <div class="stat"><b>{len(rows)}</b><span>משובים</span></div>
              <div class="stat"><b>{avg(rows,'overall')}</b><span>ציון כללי ממוצע</span></div>
              <div class="stat"><b>{avg(rows,'realism')}</b><span>מציאותיות</span></div>
              <div class="stat"><b>{avg(rows,'difficulty')}</b><span>רמת קושי</span></div>
              <div class="stat"><b>{avg(rows,'naturalness')}</b><span>טבעיות</span></div>
              <div class="stat"><b>{avg(rows,'responsiveness')}</b><span>תגובה למה שנאמר</span></div>
            </div>'''
            track_html=''.join(f'<span class="tag">{html.escape(str(k))}: {v}</span>' for k,v in sorted(by_track.items(), key=lambda x:-x[1])) or '<span class="muted">עדיין אין משובים</span>'
            table_rows=''
            for r in reversed(rows):
                table_rows += '<tr>' + ''.join([
                    f"<td>{html.escape(str(r.get('created_at',''))[:16].replace('T',' '))}</td>",
                    f"<td>{html.escape(str(r.get('name','') or 'אנונימי'))}</td>",
                    f"<td>{html.escape(str(r.get('track','')))}</td>",
                    f"<td>{html.escape(str(r.get('overall','')))}</td>",
                    f"<td>{html.escape(str(r.get('realism','')))}</td>",
                    f"<td>{html.escape(str(r.get('difficulty','')))}</td>",
                    f"<td>{html.escape(str(r.get('naturalness','')))}</td>",
                    f"<td class='text'>{html.escape(str(r.get('best','')))}</td>",
                    f"<td class='text'>{html.escape(str(r.get('change','')))}</td>",
                    f"<td class='text'>{html.escape(str(r.get('scenario_idea','')))}</td>",
                ]) + '</tr>'
            token=parse_qs(urlparse(self.path).query).get('token',[''])[0]
            page=f'''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Move A Mind — משובי פיילוט</title><style>
            body{{font-family:Arial,sans-serif;background:#f5f2ec;color:#111;margin:0}}main{{max-width:1200px;margin:auto;padding:24px}}h1{{margin:0 0 6px}}.muted{{color:#6d6a65}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:22px 0}}.stat{{background:white;border:1px solid #e8e3db;border-radius:16px;padding:18px}}.stat b{{font-size:30px;display:block}}.stat span{{color:#6d6a65;font-size:13px}}.tags{{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0 22px}}.tag{{background:#e2f0ec;color:#0d6253;padding:7px 10px;border-radius:999px;font-size:13px;font-weight:700}}.actions{{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}}a.btn{{background:#0d6253;color:white;text-decoration:none;padding:10px 14px;border-radius:10px;font-weight:700}}.tablewrap{{overflow:auto;background:white;border-radius:16px;border:1px solid #e8e3db}}table{{border-collapse:collapse;width:100%;min-width:1100px}}th,td{{padding:10px;border-bottom:1px solid #eee;vertical-align:top;text-align:right;font-size:13px}}th{{position:sticky;top:0;background:#faf8f5}}td.text{{max-width:260px;white-space:normal;line-height:1.45}}@media(max-width:600px){{main{{padding:14px}}}}
            </style></head><body><main><h1>Move A Mind — משובי פיילוט</h1><div class="muted">מרכז המשובים שנשלחו מהטופס</div>{cards}<div class="tags">{track_html}</div><div class="actions"><a class="btn" href="/admin-feedback.csv?token={html.escape(token)}">הורד CSV</a></div><div class="tablewrap"><table><thead><tr><th>זמן</th><th>שם</th><th>תחום</th><th>כללי</th><th>מציאותיות</th><th>קושי</th><th>טבעיות</th><th>הכי טוב</th><th>מה לשנות</th><th>רעיון לתרחיש</th></tr></thead><tbody>{table_rows}</tbody></table></div></main></body></html>'''
            b=page.encode('utf-8'); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return
        if p == '/admin-feedback.csv':
            if not authorized(self.path):
                return self._json({'error':'אין הרשאה'},403)
            rows=load_feedback(); s=io.StringIO(); w=csv.DictWriter(s,fieldnames=FIELDS,extrasaction='ignore'); w.writeheader(); w.writerows(rows); b=s.getvalue().encode('utf-8-sig')
            self.send_response(200); self.send_header('Content-Type','text/csv; charset=utf-8'); self.send_header('Content-Disposition','attachment; filename="move-a-mind-feedback.csv"'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return
        return super().do_GET()

    def do_POST(self):
        p=urlparse(self.path).path
        if p == '/api/feedback':
            try: body=self._body()
            except: return self._json({'error':'בקשה לא תקינה'},400)
            required=['track','realism','difficulty','naturalness','length_fit','responsiveness','ending','try_again','best','change','overall']
            missing=[k for k in required if not str(body.get(k,'')).strip()]
            if missing: return self._json({'error':'חסרים שדות חובה','missing':missing},400)
            record={
                'created_at':datetime.datetime.utcnow().isoformat()+'Z',
                'name':str(body.get('name','')).strip()[:120],
                'track':str(body.get('track','')).strip()[:120],
                'realism':str(body.get('realism','')).strip()[:3],
                'difficulty':str(body.get('difficulty','')).strip()[:3],
                'naturalness':str(body.get('naturalness','')).strip()[:3],
                'length_fit':str(body.get('length_fit','')).strip()[:50],
                'responsiveness':str(body.get('responsiveness','')).strip()[:3],
                'ending':str(body.get('ending','')).strip()[:50],
                'try_again':str(body.get('try_again','')).strip()[:50],
                'best':str(body.get('best','')).strip()[:2000],
                'change':str(body.get('change','')).strip()[:2000],
                'scenario_idea':str(body.get('scenario_idea','')).strip()[:2000],
                'overall':str(body.get('overall','')).strip()[:3],
            }
            save_feedback(record)
            return self._json({'ok':True})
        return super().do_POST()

if __name__=='__main__':
    os.chdir(app.ROOT)
    print('Move A Mind v1.8 persistent feedback dashboard')
    ThreadingHTTPServer(('0.0.0.0',app.PORT),H).serve_forever()
