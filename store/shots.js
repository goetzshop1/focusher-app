const {chromium}=require('playwright');const fs=require('fs');
const OUT=process.argv[2];
const DAY=864e5;
function seed(now, opts={}){
  const t=(id,title,energy,extra={})=>Object.assign({id,title,energy,done:false,created:now-3*DAY},extra);
  const at=(d,h,m=0)=>{const x=new Date(now+d*DAY);x.setHours(h,m,0,0);return x.getTime();};
  const tasks=[
    t('a','Steuererklärung abgeben','high',{deadline:at(3,18),rem:['1440'],weekly:{days:[1,2,3],time:'09:00'},ack:[],snooze:{}}),
    t('b','Rezept beim Hausarzt abholen','mid',{deadline:opts.remNow?now+50*60000:at(1,12),rem:['60','1440'],ack:[],snooze:{},created:now-2*3600e3}),
    t('c','Geschenk für Mamas Geburtstag bestellen','low',{deadline:at(6,20),rem:['1440'],ack:[],snooze:{}}),
    t('d','Pflanzen gießen','low'),
    t('e','Drei Mails nur lesen, nicht beantworten','low'),
    t('f','Wäsche in die Maschine','mid'),
    t('g','Kleiderschrank ausmisten','high'),
    t('h','Ein Glas Wasser trinken','low',{done:true,doneAt:now-3600e3}),
  ];
  const texts=['Wäsche aufgehängt','Arzttermin gemacht','Küche aufgeräumt','Mails gelesen','Spazieren gegangen','Rechnung bezahlt','Einkauf erledigt','Pflanzen gegossen','Bewerbung angefangen','Müll rausgebracht'];
  const E=['low','mid','high'];const journal=[];let s=11;const r=()=>{s=(s*16807)%2147483647;return s/2147483647;};
  for(let i=0;i<46;i++){const ts=now-Math.floor(r()*27*DAY)-3600e3;const win=r()<0.15;journal.push({id:'j'+i,ts,text:win?'Heute gut für mich gesorgt':texts[i%texts.length],kind:win?'win':'task',energy:E[Math.floor(r()*3)],mood:win?'stolz':''});}
  journal.push({id:'jx',ts:now-3600e3,text:'Ein Glas Wasser trinken',kind:'task',energy:'low'});
  journal.sort((a,b)=>b.ts-a.ts);
  return {tasks,journal,energy:opts.energy??1,settings:{theme:'dark',calm:false,size:'m',name:'Lena',notif:true},trialStart:now,unlocked:false,decUse:{day:'',n:0},lastVisit:now,jarSeen:now};
}
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
async function shot(name,opts,act){
  const ctx=await b.newContext({viewport:{width:440,height:956},deviceScaleFactor:3,reducedMotion:'reduce',locale:'de-DE',timezoneId:'Europe/Berlin'});
  const p=await ctx.newPage();await p.clock.install({time:new Date('2026-10-07T09:24:00+02:00')});await p.goto('http://localhost:8765/shots.html');
  const now=await p.evaluate(()=>Date.now());const d=seed(now,opts);
  await p.evaluate(d=>{for(const k in d)localStorage.setItem('fh_'+k,JSON.stringify(d[k]));sessionStorage.clear();},d);
  await p.reload();await p.waitForTimeout(700);
  if(act) await act(p);
  await p.waitForTimeout(500);
  await p.screenshot({path:`${OUT}/raw-${name}.png`});await ctx.close();
}
await shot('1-heute',{energy:1},async p=>{await p.evaluate(()=>{document.getElementById('dlWrap').hidden=true;document.getElementById('reminders').hidden=true;});});
await shot('2-zerlegen',{},async p=>{await p.click('[data-go=zerlegen]');await p.fill('#decInput','Steuererklärung machen');await p.click('#decCount [data-n="5"]');await p.click('#decBtn');await p.waitForTimeout(600);await p.evaluate(()=>document.getElementById('decResult').scrollIntoView({block:'start'}));await p.evaluate(()=>window.scrollBy(0,-70));});
await shot('3-deadline',{remNow:true},null);
await shot('4-journal',{},async p=>{await p.click('[data-go=journal]');await p.waitForTimeout(400);await p.evaluate(()=>window.scrollTo(0,170));});
await shot('5-erinnerung',{},async p=>{await p.evaluate(()=>{document.getElementById('dlWrap').hidden=true;document.getElementById('reminders').hidden=true;});await p.fill('#addInput','Steuererklärung abgeben');await p.click('#addEnergy [data-e=high]');await p.click('#dlToggle');await p.fill('#dlDate','2026-10-10');await p.click('#dlDays [data-d="1"]');await p.click('#dlDays [data-d="2"]');await p.click('#dlDays [data-d="3"]');await p.evaluate(()=>document.getElementById('addForm').scrollIntoView({block:'start'}));await p.evaluate(()=>window.scrollBy(0,-60));});
await b.close();})();
