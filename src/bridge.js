// Verbindung zwischen der FocusHer-Oberfläche (app.html) und dem iPhone/Android-Gerät.
// Stellt window.FocusHerStore bereit: Abo (RevenueCat), echte Erinnerungen (LocalNotifications),
// KI-Zerleger und Feedback (Base44-Server).
import { Capacitor } from "@capacitor/core";
import { LocalNotifications } from "@capacitor/local-notifications";
import { Purchases, LOG_LEVEL } from "@revenuecat/purchases-capacitor";
import { App } from "@capacitor/app";

const CFG = window.FOCUSHER_CONFIG || {};
const ENTITLEMENT = CFG.entitlement || "focusher_pro";
const platform = Capacitor.getPlatform(); // "ios" | "android" | "web"
const native = Capacitor.isNativePlatform();

/* ---------- Abo ---------- */
let rcReady = null;
function rcKey(){ return platform === "ios" ? CFG.revenuecatIos : platform === "android" ? CFG.revenuecatAndroid : ""; }
function initPurchases(){
  if(rcReady) return rcReady;
  rcReady = (async () => {
    const apiKey = rcKey();
    if(!native || !apiKey) return false;
    try{ await Purchases.setLogLevel({ level: LOG_LEVEL.WARN }); }catch(e){}
    await Purchases.configure({ apiKey });
    try{
      await Purchases.addCustomerInfoUpdateListener(info => announce(info));
    }catch(e){}
    return true;
  })().catch(() => false);
  return rcReady;
}
function isActive(info){ return !!(info && info.entitlements && info.entitlements.active && info.entitlements.active[ENTITLEMENT]); }
function announce(info){
  window.dispatchEvent(new CustomEvent("fh-entitlement", { detail: { active: isActive(info) } }));
}
async function refreshEntitlement(){
  if(!(await initPurchases())) return;
  try{ const { customerInfo } = await Purchases.getCustomerInfo(); announce(customerInfo); }catch(e){}
}
async function currentPackage(){
  const offerings = await Purchases.getOfferings();
  const cur = offerings && offerings.current;
  if(!cur) return null;
  return cur.annual || (cur.availablePackages && cur.availablePackages[0]) || null;
}
function cancelled(e){
  return !!(e && (e.userCancelled || (e.data && e.data.userCancelled) || String(e.code) === "1" || /cancel/i.test(String(e.message || ""))));
}

/* ---------- Erinnerungen ---------- */
const DAY = 86400000;
function remTime(t, r){
  if(r === "due") return t.deadline;
  if(r === "morning"){ const d = new Date(t.deadline); d.setHours(8,0,0,0); return d.getTime() < t.deadline ? d.getTime() : null; }
  return t.deadline - (+r) * 60000;
}
const LABEL = {"10080":"in einer Woche","4320":"in 3 Tagen","1440":"morgen","morning":"heute","180":"in 3 Stunden","60":"in einer Stunde","15":"in 15 Minuten"};
function fmtDue(ts){
  const d = new Date(ts);
  return d.toLocaleDateString("de-DE", { weekday:"short", day:"numeric", month:"numeric" }) + ", " + d.toLocaleTimeString("de-DE", { hour:"2-digit", minute:"2-digit" });
}
function hashId(str){ let h = 0x811c9dc5; for(let i=0;i<str.length;i++){ h ^= str.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; } return (h % 2000000000) + 1; }
function planFor(tasks){
  const now = Date.now(), out = [];
  for(const t of tasks || []){
    if(t.done) continue;
    if(t.deadline){
      for(const r of (t.rem || []).concat("due")){
        const at = remTime(t, r);
        if(at == null || at <= now + 5000) continue;
        out.push({ id: hashId(t.id + r), at, title: t.title,
          body: r === "due" ? "Die Frist ist jetzt erreicht. Ein kleiner Schritt reicht." : "Fällig " + LABEL[r] + ": " + fmtDue(t.deadline) + "." });
      }
    }
    if(t.weekly && t.weekly.days && t.weekly.days.length){
      const [hh, mm] = String(t.weekly.time || "09:00").split(":").map(Number);
      for(let i=0; i<21; i++){
        const d = new Date(now + i*DAY); d.setHours(hh, mm, 0, 0);
        if(!t.weekly.days.includes(d.getDay()) || d.getTime() <= now + 5000) continue;
        if(t.deadline && d.getTime() > t.deadline) continue;
        out.push({ id: hashId(t.id + "w" + d.toDateString()), at: d.getTime(), title: t.title,
          body: t.deadline ? "Deine Erinnerung für heute. Fällig " + fmtDue(t.deadline) + "." : "Deine Erinnerung für heute. Ein kleiner Schritt zählt schon." });
      }
    }
  }
  // iOS erlaubt höchstens 64 geplante Mitteilungen: die nächsten 60 nehmen
  return out.sort((a,b) => a.at - b.at).slice(0, 60);
}
let lastPlanKey = "";
async function syncReminders(tasks){
  if(!native) return;
  const plan = planFor(tasks);
  const key = plan.map(p => p.id + ":" + p.at).join(",");
  if(key === lastPlanKey) return;
  try{
    let perm = await LocalNotifications.checkPermissions();
    if(plan.length && perm.display === "prompt") perm = await LocalNotifications.requestPermissions();
    const pending = await LocalNotifications.getPending();
    if(pending.notifications && pending.notifications.length){
      await LocalNotifications.cancel({ notifications: pending.notifications.map(n => ({ id: n.id })) });
    }
    if(perm.display !== "granted" || !plan.length){ lastPlanKey = key; return; }
    await LocalNotifications.schedule({ notifications: plan.map(p => ({
      id: p.id, title: "FocusHer: " + p.title, body: p.body, schedule: { at: new Date(p.at), allowWhileIdle: true }
    })) });
    lastPlanKey = key;
  }catch(e){ /* nächster Versuch beim nächsten Speichern */ }
}

/* ---------- Server (Base44) ---------- */
async function callServer(fn, payload){
  const res = await fetch(CFG.apiBase + "/" + fn, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-FocusHer-Key": CFG.apiKey },
    body: JSON.stringify(payload)
  });
  if(!res.ok) throw { code: res.status === 429 ? "rate_limited" : "upstream_error" };
  return res.json();
}

/* ---------- Schnittstelle für die Oberfläche ---------- */
if(native){
  window.FocusHerStore = {
    platform,
    version: CFG.version || "1.0",
    price: CFG.priceLabel || "29,99 €",
    async purchase(){
      if(!(await initPurchases())) throw new Error("not_configured");
      const pkg = await currentPackage();
      if(!pkg) throw new Error("no_offering");
      try{
        const { customerInfo } = await Purchases.purchasePackage({ aPackage: pkg });
        announce(customerInfo);
        return isActive(customerInfo);
      }catch(e){
        if(cancelled(e)) return false;
        throw e;
      }
    },
    async restore(){
      if(!(await initPurchases())) throw new Error("not_configured");
      const { customerInfo } = await Purchases.restorePurchases();
      announce(customerInfo);
      return isActive(customerInfo);
    },
    async decompose(opts){
      const out = await callServer("fhDecompose", opts);
      return out && out.steps;
    },
    async sendFeedback(entry){
      await callServer("fhFeedback", entry);
      return true;
    },
    syncReminders,
    async notifStatus(){ const p = await LocalNotifications.checkPermissions(); return p.display; },
    async notifRequest(){ const p = await LocalNotifications.requestPermissions(); return p.display; }
  };

  // Abo-Status beim Start und beim Zurückkehren in die App prüfen
  setTimeout(refreshEntitlement, 300);
  App.addListener("appStateChange", ({ isActive: active }) => { if(active) refreshEntitlement(); });
  // Echten Preis aus dem Store holen (z. B. 29,99 €), sobald verfügbar
  initPurchases().then(async ok => {
    if(!ok) return;
    try{
      const pkg = await currentPackage();
      if(pkg && pkg.product && pkg.product.priceString){
        window.FocusHerStore.price = pkg.product.priceString;
        const el = document.getElementById("buyPrice"); if(el) el.textContent = pkg.product.priceString;
      }
    }catch(e){}
  });
}
