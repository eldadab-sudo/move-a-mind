import os, uuid, random, datetime
from urllib.parse import urlparse, parse_qs
from http.server import ThreadingHTTPServer
import server_v22 as v22
import server_v21 as v21
from subdomains_v1 import SUBDOMAINS, get_subdomain

app=v22.app

ROLE={'sales':'איש/ת המכירות או השירות','work':'המנהל/ת','military':'המפקד/ת','restaurant':'עובד/ת המסעדה','parent':'ההורה','teacher':'המורה/מחנכ/ת','everyday':'האדם שמנסה לקדם את ההחלטה'}
CHAR={'sales':'נועם','work':'אורי','military':'עידו','restaurant':'מיכל','parent':'תום','teacher':'רוני','everyday':'יעל'}

# Fast deterministic, clear scenario frames. No LLM call is made when a scenario is opened.
TRACK_FRAMES={
'sales':{
 'situation':'לקוח/ה נמצא/ת כבר בשלב שבו יש עניין אמיתי, אבל עוצר/ת לפני החלטה בגלל סיכון, מחיר, אמון או ניסיון עבר.',
 'goal':'לגלות מה באמת מונע התקדמות, לטפל בהתנגדות בלי לחץ ולהוביל לצעד מתאים: בדיקה, הדגמה, הצעה, רכישה — או החלטה נכונה שלא להתקדם.',
 'known':'יש עניין במוצר או בשירות, אבל עדיין אין הסכמה להתקדם.',
 'opening':'אני אומר/ת מראש: אני לא מתקדם/ת כרגע. יש פה משהו שלא מספיק ברור לי כדי לקבל החלטה.'},
'work':{
 'situation':'עובד/ת מעלה בקשה או התנגדות שמשפיעה גם עליו/ה וגם על הצוות. יש מגבלה ניהולית אמיתית, אבל גם צורך אישי שעדיין לא נאמר במלואו.',
 'goal':'להבין את הצורך האמיתי, לשמור על הוגנות ועל דרישות העבודה, ולהגיע להסכמה מעשית או לאי-הסכמה מכבדת עם צעד הבא ברור.',
 'known':'לא ניתן פשוט לומר כן או לא בלי לבחון את המשמעות לצוות ולעובד/ת.',
 'opening':'אני צריך/ה שנדבר על זה עכשיו. מבחינתי המצב הנוכחי לא יכול להמשיך כמו שהוא.'},
'military':{
 'situation':'חייל/ת מעלה קושי או בקשה שיש בה גם צורך אישי וגם השלכה על הצוות והמשימה.',
 'goal':'להבין מה עומד מאחורי הבקשה, להציב ציפיות פיקודיות ברורות, לבדוק פתרון אמיתי ולהגיע להחלטה שמכבדת גם את האדם וגם את המשימה.',
 'known':'החייל/ת אינו/ה מחפש/ת עימות, אבל כבר לא מוכן/ה להסתפק בתשובה כללית.',
 'opening':'המפקד/ת, אני רוצה שנדבר ברצינות. מבחינתי צריך להשתנות כאן משהו, ואני לא רוצה לקבל שוב תשובה כללית.'},
'restaurant':{
 'situation':'לקוח/ה חווה כשל שירות ברור ופונה לצוות בזמן אמת. מעבר לבעיה עצמה, יש גם פגיעה בתחושת ההתייחסות וההוגנות.',
 'goal':'להבין מה השתבש ומה חשוב ללקוח/ה עכשיו, לקחת אחריות מתאימה ולהציע פתרון שניתן לבצע במסגרת הזמן והסמכות.',
 'known':'פיצוי אוטומטי אינו בהכרח מה שהלקוח/ה רוצה; קודם צריך להבין את העדיפות שלו/ה.',
 'opening':'אני חייב/ת להגיד שאני ממש לא מרוצה. הבעיה היא לא רק מה שקרה — אלא גם איך שטיפלו בי עד עכשיו.'},
'parent':{
 'situation':'מתבגר/ת מבקש/ת יותר חופש או שינוי בכלל ביתי. מאחורי הוויכוח יש צורך בעצמאות, אמון ושייכות, לצד אחריות הורית אמיתית.',
 'goal':'להקשיב למה שבאמת חשוב למתבגר/ת, לשמור על גבול ברור ובטוח, ולבדוק אם קיימת פשרה שמכבדת גם עצמאות וגם אחריות הורית.',
 'known':'המטרה אינה לגרום לילד/ה לציית בכל מחיר אלא לנהל שיחה שמחזיקה קשר וגבול יחד.',
 'opening':'אני רוצה שתשמע/י אותי עד הסוף לפני שאת/ה אומר/ת לא. מבחינתי הכלל הזה כבר לא מתאים למה שאני מסוגל/ת לקחת עליו אחריות.'},
'teacher':{
 'situation':'הורה מתנגד להחלטה או להמלצה חינוכית שנוגעת לילד/ה שלו/ה. ההתנגדות משלבת דאגה מקצועית, רגשית וחברתית.',
 'goal':'להבין את הדאגה המרכזית, להסביר את ההמלצה באופן ברור ומבוסס, לשלב את קול התלמיד/ה ולהגיע לתוכנית מעשית עם נקודת בדיקה.',
 'known':'אין ודאות שההמלצה תצליח; השיחה צריכה לבנות שותפות ולא לדרוש אמון עיוור.',
 'opening':'אני רוצה להבין למה אתם חושבים שזה הדבר הנכון לילד שלי. כרגע אני לא שלם/ה עם ההחלטה הזאת.'},
'everyday':{
 'situation':'שני אנשים רוצים דברים שונים סביב החלטה משותפת. העמדה הגלויה אינה בהכרח האינטרס האמיתי.',
 'goal':'לזהות מה חשוב לצד השני, להציג את הצורך שלך בלי מאבק כוח ולנסות להגיע להסכמה, תנאי מוסכם או החלטה להישאר עם המצב הקיים.',
 'known':'יש יותר מאפשרות אחת סבירה; איכות השיחה חשובה לא פחות מהתוצאה.',
 'opening':'אני מבין/ה למה את/ה רוצה לשנות, אבל מבחינתי יש כאן בעיה אמיתית שלא פתרנו עדיין.'}
}

# A specific surface detail for each subdomain makes the brief concrete while keeping load time near-zero.
DETAILS={
'banking':'לקוח/ה בוחן/ת מעבר למסלול בנקאי חדש אחרי שהוצגו דמי ניהול ותנאים, אבל חושש/ת מעלויות נסתרות ומוויתור על מה שכבר עובד.',
'mobile':'לקוח/ה בוחן/ת חבילת סלולר חדשה לשתי קווים, אך מהסס/ת בגלל מחיר מבצע זמני וניסיון שירות גרוע בעבר.',
'fashion':'לקוח/ה בחנות מתלבט/ת אם לקנות פריט יקר יחסית, אבל לא בטוח/ה שהוא באמת מתאים לצורך ושואל/ת על החזרה ושימוש בפועל.',
'electronics':'לקוח/ה משווה מכשיר חשמלי ב-3,200 ש״ח לחלופה זולה יותר ושואל/ת אם האחריות והפער באיכות באמת מצדיקים את המחיר.',
'home_decor':'לקוח/ה שוקל/ת שטיח/פריט ריהוט לבית, אבל חושש/ת מהתאמה לחלל, עמידות ומשלוח של מוצר שקשה להחזיר.',
'automotive':'לקוח/ה בוחן/ת עסקת רכב או ליסינג ומתלבט/ת בגלל העלות הכוללת, התחייבות ארוכה ומה יקרה אם הצרכים ישתנו.',
'real_estate':'לקוח/ה בוחן/ת נכס שמעניין אותו/ה אבל חושש/ת שהמחיר גבוה ושחלק מהמידע החשוב על העסקה עדיין חסר.',
'saas':'מנהל/ת עסק בוחן/ת מערכת חדשה אך חושש/ת מהטמעה כושלת ומהתנגדות העובדים יותר מאשר מהמחיר עצמו.',
'fitness':'לקוח/ה שוקל/ת להצטרף לשירות כושר/פנאי אך לא בטוח/ה שהמסגרת מתאימה לזמן, לשגרה וליכולת להתמיד.',
'travel':'לקוח/ה שוקל/ת להזמין חופשה אך עוצר/ת בגלל תנאי ביטול, גמישות ושאלה אם המחיר באמת כולל את כל מה שחשוב.',
'performance':'עובד/ת שמקבל/ת משוב על ירידה בביצועים טוענ/ת שהיעדים לא ריאליים ושלא רואים את העומס שנוסף עליו/ה.',
'leave':'עובד/ת מבקש/ת חופש ביום קריטי לצוות ומרגיש/ה שסירוב יהיה לא הוגן לאור הגמישות שנתן/ה בעבר.',
'promotion':'עובד/ת מבקש/ת קידום וטוענ/ת שכבר מבצע/ת בפועל חלק מהתפקיד הבא.',
'conflict':'שני עובדים מאשימים זה את זה בעיכוב משימה, ואחד מהם מגיע אליך בתחושה שלא מתייחסים אליו בהוגנות.',
'change':'הצוות מתנגד לתהליך עבודה חדש וטוען שהוא מוסיף בירוקרטיה בלי לפתור את הבעיה האמיתית.',
'delegation':'עובד/ת מתנגד/ת לקבל אחריות חדשה כי מרגיש/ה שמעמיסים עליו/ה בלי סמכות או תמיכה.',
'burnout':'עובד/ת אומר/ת שהעומס הפך בלתי אפשרי ומבקש/ת שינוי סדרי עדיפויות לפני שהאיכות תיפגע.',
'hybrid':'עובד/ת מתנגד/ת להגדלת ימי הנוכחות במשרד וטוענ/ת שאין לכך הצדקה מקצועית ברורה.',
'feedback':'עובד/ת נפגע/ת ממשוב שקיבל/ה וטוענ/ת שהוא היה חד-צדדי ולא התייחס לנסיבות.',
'retention':'עובד/ת מפתח מודיע/ה שהוא/היא שוקל/ת לעזוב בגלל תחושת תקיעות ולא רק בגלל שכר.',
'transfer':'חייל/ת מבקש/ת מעבר ליחידה אחרת בגלל תחושת תקיעות מקצועית והבטחות קודמות שלא התממשו.',
'motivation':'חייל/ת שהיה/תה חזק/ה בצוות מראה ירידה במעורבות ואומר/ת שאין יותר תחושת משמעות.',
'discipline':'חייל/ת חרג/ה מסטנדרט מקצועי מוסכם וטוענ/ת שהכלל נאכף בצורה לא עקבית.',
'task_resistance':'חייל/ת מתנגד/ת למשימה שגרתית וטוענ/ת שעומס העבודה מתחלק בצורה לא הוגנת.',
'development':'חייל/ת מבקש/ת אחריות, קורס או מסלול התפתחות ברור ומרגיש/ה שכבר מיצה/תה את התפקיד הנוכחי.',
'team_conflict':'חייל/ת אומר/ת שהמתח עם חבר/ה לצוות כבר פוגע בעבודה ושלא ניתן להמשיך להתעלם.',
'after_mistake':'לאחר טעות מקצועית ללא פגיעה, חייל/ת מגיע/ה לשיחה כשהוא/היא חושש/ת שהמפקד כבר איבד אמון.',
'values':'חייל/ת קיבל/ה הערה על התנהגות שאינה עומדת בסטנדרט היחידה ומרגיש/ה שמציגים אותו/ה כאדם בעייתי.',
'return_to_team':'חייל/ת חוזר/ת לצוות אחרי היעדרות חוקית ומרגיש/ה שהציפיות ממנו/ה אינן ברורות.',
'recognition':'חייל/ת מוערך/ת מרגיש/ה שהתרומה שלו/ה מובנת מאליה ושאחרים מקבלים יותר הזדמנויות.',
'delay':'מנה עיקרית מתעכבת זמן חריג בזמן שהשולחן כבר קיבל חלק מהמנות.',
'wrong_order':'ללקוח/ה הוגשה מנה אחרת מזו שהוזמנה, אחרי שכבר המתין/ה זמן משמעותי.',
'quality':'לקוח/ה טוענ/ת שהמנה שקיבל/ה אינה ברמה שציפה/תה ביחס למחיר.',
'bill':'בחשבון מופיע חיוב שהלקוח/ה אינו/ה מבינ/ה או מסכים/ה לו.',
'reservation':'לקוח/ה שהזמין/ה מראש מגלה שהשולחן או זמן הישיבה אינם כפי שהבין/ה.',
'allergy_process':'לקוח/ה עם בקשה תזונתית מבקש/ת ודאות שהצוות אינו יכול לתת בלי בדיקה מול אחראי.',
'special_event':'ארוחה לאירוע מיוחד נפגעה בגלל תקלה בשירות, והלקוח/ה מרגיש/ה שהרגע עצמו כבר לא יחזור.',
'noise':'לקוח/ה טוענ/ת שהמיקום או הרעש אינם מאפשרים ליהנות מהארוחה.',
'takeaway':'הזמנת טייק־אוויי/משלוח הגיעה חסרה או באיחור משמעותי.',
'loyal_customer':'לקוח/ה קבוע/ה מרגיש/ה שרמת השירות ירדה ושכבר לא מתייחסים אליו/ה כפי שהיה בעבר.',
'curfew':'מתבגר/ת בן/בת 15 מבקש/ת לחזור מאירוע ב-01:30 בעוד ההורה לא מכיר את ההסעה המתוכננת.',
'screen_time':'מתבגר/ת מבקש/ת להמשיך גיימינג/מסך עד מאוחר וטוענ/ת שהכלל בבית לא מתחשב באחריות שכבר הוכיח/ה.',
'school':'מתבגר/ת לא עומד/ת לאחרונה במשימות לימודיות ומתנגד/ת לכך שההורה ינהל עבורו/ה כל פרט.',
'chores':'מתבגר/ת טוענ/ת שמטלות הבית אינן מתחלקות בהוגנות בין בני הבית.',
'friends':'הורה מודאג מבחירה חברתית מסוימת, והמתבגר/ת מרגיש/ה שלא סומכים על שיקול הדעת שלו/ה.',
'money':'מתבגר/ת מבקש/ת קנייה יקרה יחסית מכספי דמי כיס/חיסכון ומתנגד/ת להתערבות של ההורה.',
'privacy':'מתבגר/ת דורש/ת יותר פרטיות בטלפון ובחדר ומרגיש/ה שהבדיקות של ההורה פוגעות באמון.',
'family_time':'מתבגר/ת לא רוצה להצטרף לאירוע משפחתי שכבר תוכנן ומרגיש/ה שאין לו/ה בחירה.',
'rules':'מתבגר/ת מתנגד/ת לכלל ביתי קבוע וטוענ/ת שהוא כבר לא מתאים לגיל שלו/ה.',
'independence':'מתבגר/ת מבקש/ת לקבל החלטה יומיומית משמעותית יותר בעצמו/ה ולהוכיח אחריות.',
'academic_support':'הורה מתנגד לקבוצת תגבור קטנה כי חושש/ת מתיוג ומהשפעה על הביטחון העצמי.',
'behavior':'הורה מתנגד לתיאור של בעיית התנהגות וטוענ/ת שהילד/ה מסומן/ת מראש.',
'grading':'הורה מערער על ציון וטוענ/ת שההערכה אינה משקפת את היכולת האמיתית של הילד/ה.',
'attendance':'יש דפוס איחורים/היעדרויות וההורה טוענ/ת שבית הספר אינו מבין את הנסיבות.',
'social':'הורה מודאג ממצב חברתי של הילד/ה ורוצה פעולה מיידית מבית הספר.',
'homework':'הורה טוענ/ת שעומס שיעורי הבית אינו סביר ומייצר עימותים בבית.',
'phone':'הורה מתנגד למדיניות הטלפונים בכיתה וטוענ/ת שהכלל נוקשה מדי.',
'placement':'הורה חולק/ת על שיבוץ לקבוצה או מסלול ורוצה להבין על בסיס מה התקבלה ההחלטה.',
'special_project':'הורה חושש/ת משיטת הוראה חדשה ורוצה לדעת למה הילד/ה צריך/ה להיות חלק מהניסוי.',
'parent_boundary':'הורה דורש זמינות או חריגה מהנהלים שהמורה אינו/ה יכול/ה לספק באופן קבוע.',
'travel':'קבוצת חברים חלוקה על שינוי יעד או מסלול אחרי שכבר נקבעו רכבים וזמנים.',
'shared_expense':'יש מחלוקת בקבוצה על חלוקת תשלום ועל מה נחשב הוגן.',
'plans':'צד אחד רוצה לשנות תוכנית שכבר נסגרה והצד השני מרגיש שלא מתחשבים בזמן שלו.',
'neighbor':'שכן/ה מעלה בעיה סביב רעש, חניה או שימוש משותף ורוצה שינוי ברור.',
'family_decision':'בני משפחה חלוקים על אירוח, ביקור או חלוקת אחריות סביב אירוע קרוב.',
'friend_boundary':'אדם רוצה להציב גבול לחבר/ה בלי לפרק את הקשר.',
'shared_home':'שותפים לבית חלוקים על ניקיון, אורחים או שימוש במרחב משותף.',
'group_choice':'קבוצה צריכה לבחור פעילות או יעד ולכל אחד אינטרס אחר.',
'favor':'חבר/ה מתנגד/ת לבקשת טובה בגלל זמן, עומס או תחושת חוסר הדדיות.',
'commitment':'אדם שינה התחייבות ברגע האחרון והצד השני מרגיש שנפגע האמון.'
}

def instant_scenario(track,sub):
    f=TRACK_FRAMES[track]; detail=DETAILS.get(sub['id'],sub['context']); char=CHAR[track]
    brief=(f"התפקיד שלך: {ROLE[track]}.\n\nמה קורה: {detail}\n\nהמטרה שלך: {f['goal']}\n\nמה ידוע לך בתחילת השיחה: {f['known']}")
    facts=(f"תת-תחום: {sub['he']}. {sub['context']}\nהדמות שמול המשתמש: {char}.\n"
           f"המצב הגלוי: {detail}\nמניע נסתר: אל תחשוף אותו מיד; בחר סיבה אמינה מתוך אמון, סיכון, הוגנות, עצמאות, שייכות, עומס או ניסיון עבר בהתאם לתת-התחום.\n"
           "חשוף מידע בהדרגה רק כשנשאלת שאלה טובה או נוצר אמון. אם המשתמש פתר את החסם המרכזי, אפשר להתקדם. אל תמציא התנגדות חדשה רק כדי להאריך. רוב התגובות אינן שאלות. שמור על שיחה טבעית וקצרה.")
    return {'label':sub['he'],'title':sub['he'],'character':char,'brief':brief,'facts':facts,'layers':['ההתנגדות הגלויה','המניע האמיתי','אמון','חלופה מעשית','החלטה'],'possible_endings':['agreement','conditional_agreement','respectful_no'],'opening':f["opening"],'subdomain_id':sub['id'],'subdomain_he':sub['he'],'subdomain_en':sub['en']}

class H(v22.H):
    def do_GET(self):
        parsed=urlparse(self.path);p=parsed.path
        if p=='/api/subdomains':
            track=parse_qs(parsed.query).get('track',[''])[0]
            if track not in SUBDOMAINS:return self._json({'error':'invalid track'},400)
            return self._json({'track':track,'subdomains':SUBDOMAINS[track]})
        if p=='/':
            html=(app.WEB/'global.html').read_text(encoding='utf-8')
            marker='<section id="chatScreen" class="screen">'
            subsec='''<section id="subchoose" class="screen"><div class="stickyBack"><button class="back" id="subBack">← <span id="subBackText">חזרה לתחומים</span></button></div><div class="pageHead"><small id="subStep">בחר תת־תחום</small><h2 id="subH">עכשיו מדייקים.</h2><p id="subP">בחר את העולם המקצועי המדויק. התרחיש שייפתח יהיה בנוי סביב מצב אמיתי מאותו עולם.</p></div><div class="domains" id="subdomains"></div><div class="bottomAction"><button class="btn primary" id="subStart" disabled>התחל</button></div></section>'''
            html=html.replace(marker,subsec+marker)
            html=html.replace('</style>','.stickyBack{position:sticky;top:0;z-index:20;padding:10px 0 8px;background:linear-gradient(var(--bg) 70%,transparent)}.stickyBack .back{background:#fff;border:1px solid var(--line);border-radius:999px;padding:10px 14px;box-shadow:0 5px 18px rgba(16,32,30,.06)}.changeSub{width:100%;margin:0 0 12px;background:#fff;border:1px solid var(--line);color:var(--jade)} </style>')
            inject=r'''<script>
let chosenSub=null,subCache={};
function subTxt(k){const H={back:'חזרה לתחומים',step:'בחר תת־תחום',h:'עכשיו מדייקים.',p:'בחר את העולם המקצועי המדויק. התרחיש שייפתח יהיה בנוי סביב מצב אמיתי מאותו עולם.',start:'התחל',change:'החלף תת־תחום'},E={back:'Back to domains',step:'Choose a specialty',h:'Make it specific.',p:'Choose the exact professional context. Your scenario will be built around a realistic situation from that world.',start:'Start',change:'Change specialty'};return (lang==='he'?H:E)[k]}
function renderSubs(){const box=document.querySelector('#subdomains');box.innerHTML='';(subCache[chosen]||[]).forEach(s=>{const b=document.createElement('button');b.className='domain'+(chosenSub===s.id?' selected':'');b.innerHTML=`<div><b>${lang==='he'?s.he:s.en}</b><span>${lang==='he'?'תרחיש מדויק לעולם הזה':'A precise scenario for this context'}</span></div><div class="arr">›</div>`;b.onclick=()=>{chosenSub=s.id;renderSubs();document.querySelector('#subStart').disabled=false};box.appendChild(b)})}
async function openSubs(){if(!chosen)return;chosenSub=null;document.querySelector('#subStart').disabled=true;document.querySelector('#subBackText').textContent=subTxt('back');document.querySelector('#subStep').textContent=subTxt('step');document.querySelector('#subH').textContent=subTxt('h');document.querySelector('#subP').textContent=subTxt('p');document.querySelector('#subStart').textContent=subTxt('start');if(!subCache[chosen]){const r=await fetch('/api/subdomains?track='+encodeURIComponent(chosen));const j=await r.json();subCache[chosen]=j.subdomains||[]}renderSubs();go('subchoose')}
document.querySelector('#startBtn').onclick=openSubs;document.querySelector('#subBack').onclick=()=>go('choose');
const chat=document.querySelector('#chatScreen');const cb=document.createElement('button');cb.className='btn changeSub';cb.id='changeSubBtn';cb.textContent=subTxt('change');cb.onclick=()=>go('subchoose');chat.insertBefore(cb,chat.querySelector('.scenarioCard'));
async function startPrecise(){if(!chosen||!chosenSub)return;const b=document.querySelector('#subStart');b.disabled=true;b.textContent='…';try{const r=await fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({track:chosen,subdomain:chosenSub,lang})});const j=await r.json();if(!r.ok)throw Error(j.error||'start');sid=j.session_id;localStorage.setItem('mam_sid',sid);document.querySelector('#scenarioLabel').textContent=(lang==='he'?'התרחיש שלך · ':'YOUR SCENARIO · ')+(j.subdomain_label||'');document.querySelector('#scenarioTitle').textContent=j.scenario_title||'';document.querySelector('#brief').textContent=j.brief;document.querySelector('#charTitle').textContent=t('talking')+' '+j.character;document.querySelector('#turnPill').textContent=t('turn')+' 0';document.querySelector('#chat').innerHTML='';addMsg(j.message,'ai');go('chatScreen');setTimeout(()=>{document.querySelector('#msg').blur();window.scrollTo(0,0)},30)}catch(e){alert(lang==='he'?'לא ניתן לפתוח תרחיש כרגע.':'Could not open a scenario right now.')}finally{b.disabled=false;b.textContent=subTxt('start')}}
document.querySelector('#subStart').onclick=startPrecise;
const oldSet=setLang;setLang=function(l){oldSet(l);if(document.querySelector('#subchoose').classList.contains('active')){document.querySelector('#subBackText').textContent=subTxt('back');document.querySelector('#subStep').textContent=subTxt('step');document.querySelector('#subH').textContent=subTxt('h');document.querySelector('#subP').textContent=subTxt('p');document.querySelector('#subStart').textContent=subTxt('start');renderSubs()}document.querySelector('#changeSubBtn').textContent=subTxt('change')}
</script>'''
            html=html.replace('</body>',inject+'</body>');b=html.encode('utf-8');self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
        return super().do_GET()

    def do_POST(self):
        p=urlparse(self.path).path
        if p!='/api/start':return super().do_POST()
        try:body=self._body()
        except:return self._json({'error':'bad request'},400)
        track=body.get('track');subid=body.get('subdomain');lang=body.get('lang','he')
        if not subid:return super().do_POST()
        sub=get_subdomain(track,subid)
        if track not in TRACK_FRAMES or not sub:return self._json({'error':'invalid selection'},400)
        sc=instant_scenario(track,sub);sid=str(uuid.uuid4());opening=sc['opening']
        s={'id':sid,'track':track,'subdomain':subid,'turn':0,'messages':[{'role':'assistant','content':opening}],'status':'active','created_at':datetime.datetime.utcnow().isoformat()+'Z','scenario':sc,'scenario_title':sc['title']}
        app.STORE[sid]=s;app.save(sid)
        # Hebrew path is fully local and instant. English keeps labels but avoids three translation model calls at start.
        brief=sc['brief'] if lang!='en' else f"Your role: {ROLE[track]}.\n\nContext: {sub['en']}.\n\nGoal: understand the real resistance, respond professionally, and move toward a concrete next step without pressure or deception."
        opening_out=opening if lang!='en' else 'I want to be clear before we go any further: there is something here I am not comfortable agreeing to yet.'
        return self._json({'session_id':sid,'brief':brief,'scenario_title':sub['he'] if lang!='en' else sub['en'],'character':sc['character'],'message':opening_out,'ended':False,'subdomain_label':sub['he'] if lang!='en' else sub['en'],'demo':not bool(app.API_KEY)})

if __name__=='__main__':
    os.chdir(app.ROOT);print('Move A Mind v3.3 instant clear subdomain scenarios');ThreadingHTTPServer(('0.0.0.0',app.PORT),H).serve_forever()
