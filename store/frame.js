const {chromium}=require('playwright');const fs=require('fs');const S=process.argv[2];
const items=[
 ['1-heute','Nur eine Sache.<br>Nicht alles.','Der Energie-Regler zeigt, was heute wirklich passt.'],
 ['2-zerlegen','Zu groß?<br>Wird zerlegt.','Die KI macht aus jeder Aufgabe kleine Schritte. Der erste ist immer leicht.'],
 ['3-deadline','Fristen, die<br>dich erinnern','Deadlines stehen oben und melden sich, wann du willst.'],
 ['4-journal','Jeder Erfolg<br>landet im Glas','Keine Serie, die reißt. Deine Funken bleiben.'],
 ['5-erinnerung','Erinnern an<br>deinen Tagen','Zum Beispiel montags bis mittwochs um 9 Uhr, bis zur Frist.'],
];
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
const p=await b.newPage({viewport:{width:1320,height:2868},deviceScaleFactor:1});
for(const [n,h,sub] of items){
 const img='data:image/png;base64,'+fs.readFileSync(`${S}/raw-${n}.png`).toString('base64');
 await p.setContent(`<html><head><link rel="stylesheet" href="http://localhost:8765/fonts.css"><style>
 body{margin:0;width:1320px;height:2868px;overflow:hidden;background:radial-gradient(120% 70% at 50% 0%,#2e2740 0%,#16141b 60%);font-family:"Atkinson Hyperlegible",sans-serif;color:#ece7f0;display:flex;flex-direction:column;align-items:center}
 h1{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:118px;line-height:1.04;letter-spacing:-2px;text-align:center;margin:170px 80px 0}
 p{font-size:50px;line-height:1.35;color:#c9c1d4;text-align:center;margin:44px 130px 0;max-width:1060px}
 .ph{margin-top:90px;width:960px;border-radius:84px;overflow:hidden;border:10px solid #2c2834;box-shadow:0 40px 120px rgba(0,0,0,.55);flex:none}
 .ph img{display:block;width:100%}
 .dot{color:#c7b6ee}
 </style></head><body><h1>${h}</h1><p>${sub}</p><div class="ph"><img src="${img}"></div></body></html>`,{waitUntil:'networkidle'});
 await p.waitForTimeout(300);
 await p.screenshot({path:`${S}/FocusHer-Screenshot-${n}.png`});
}
await b.close();})();
