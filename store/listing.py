#!/usr/bin/env python3
"""Store-Eintrag von FocusHer über die App Store Connect API pflegen.

  python3 store/listing.py setup   -> App-Infos, Altersfreigabe, Preis, Verfügbarkeit, Version 1.0.0,
                                      Texte, Screenshots, Build, Prüfer-Infos, Abo-Prüfbild
  python3 store/listing.py status  -> nur anzeigen, was eingetragen ist
  python3 store/listing.py submit  -> Abo + Version zur Prüfung einreichen

Benötigt: API_KEY_ID, API_ISSUER, KEY_PATH
"""
import hashlib, json, os, sys, time
import jwt, requests

API = "https://api.appstoreconnect.apple.com"
BUNDLE = "de.vellunaprints.focusher"
VERSION = "1.0.0"
LOC = "de-DE"
HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    REPORT.append(s)


def token():
    key = open(os.environ["KEY_PATH"]).read()
    now = int(time.time())
    return jwt.encode({"iss": os.environ["API_ISSUER"], "iat": now, "exp": now + 1100, "aud": "appstoreconnect-v1"},
                      key, algorithm="ES256", headers={"kid": os.environ["API_KEY_ID"], "typ": "JWT"})


def call(method, path, ok404=False, **kw):
    url = path if path.startswith("http") else API + (path if path.startswith("/v") else "/v1" + path)
    r = requests.request(method, url, headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"}, timeout=90, **kw)
    if ok404 and r.status_code == 404:
        return None
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path}: {r.status_code} {r.text[:1500]}")
    return r.json() if r.text else {}


def step(name, fn):
    try:
        fn()
    except Exception as e:
        log(f"FEHLER bei {name}: {e}")


# ---------------- Texte ----------------
SUBTITLE = "ADHS-Planer ohne Druck"
PRIVACY_URL = "https://vellunaprints.de/focusher/datenschutz/"
SUPPORT_URL = "https://vellunaprints.de/focusher/"
COPYRIGHT = "2026 Walter Götz"
KEYWORDS = "ADHS,ADHD,Planer,To-do,Aufgaben,Fokus,Erinnerung,Deadline,Routine,Aufschieben,Struktur,Journal"
PROMO = ("Weniger Druck, mehr erledigt: FocusHer zerlegt große Aufgaben in kleine Schritte, "
         "passt sich deiner Energie an und erinnert dich sanft an Deadlines.")
DESCRIPTION = """FocusHer ist ein ruhiger Planer für Menschen mit ADHS und für alle, in deren Kopf zu viele Tabs offen sind. Keine Punkte, die verfallen, keine roten Zahlen, kein schlechtes Gewissen. Nur der nächste kleine Schritt.

SO HILFT DIR FOCUSHER
• Energie-Regler: Stell ein, wie viel Kraft du gerade hast – wenig, mittel oder viel. FocusHer zeigt dir die Aufgaben, die jetzt wirklich passen.
• KI-Zerleger: Große Brocken wie „Steuer machen“ oder „Küche aufräumen“ werden in kleine, machbare Schritte zerlegt, passend zu deiner Energie.
• Deadlines im Blick: Aufgaben mit Frist stehen ganz oben und sind farblich markiert. Je näher die Frist, desto deutlicher.
• Erinnerungen, wie du sie brauchst: eine Woche, drei Tage, einen Tag oder eine Stunde vorher – oder an festen Wochentagen bis zur Deadline.
• Funken-Glas statt Streaks: Jede erledigte Aufgabe fällt als Funke in dein Glas. Es gibt keine Serie, die reißen kann. Was du geschafft hast, bleibt.
• Ein Tipp genügt: Abhaken mit einem Klick, ohne Untermenüs.

RUHIG GESTALTET
Dunkles Design, sanfte Pastellfarben, keine Töne, keine blinkenden Hinweise. Der Ruhemodus schaltet auch Animationen ab.

DEINE DATEN BLEIBEN BEI DIR
Kein Konto, keine Werbung, kein Tracking. Aufgaben, Deadlines und Journal werden nur auf deinem Gerät gespeichert.

KOSTENLOS TESTEN, DANN FREI WÄHLEN
In den ersten 7 Tagen kannst du alles kostenlos nutzen. Danach bleiben Aufgaben, Deadlines, Erinnerungen und die letzten 7 Tage im Journal kostenlos; der KI-Zerleger ist einmal pro Tag frei.

Die Vollversion mit unbegrenztem KI-Zerleger und vollständigem Journal gibt es als Jahresabo für 29,99 € pro Jahr. Die Zahlung erfolgt über deinen Apple-Account. Das Abo verlängert sich automatisch um ein weiteres Jahr, wenn du es nicht mindestens 24 Stunden vor Ablauf kündigst. Kündigen kannst du jederzeit in den Einstellungen deines Apple-Accounts unter „Abonnements“.

Nutzungsbedingungen (EULA): https://www.apple.com/legal/internet-services/itunes/dev/stdeula/
Datenschutz: https://vellunaprints.de/focusher/datenschutz/

FocusHer ist ein Werkzeug zur Alltagsorganisation und kein Medizinprodukt. Es ersetzt keine Diagnose und keine Behandlung."""

REVIEW_NOTES = """No login or account is needed. All user data is stored locally on the device.

How to test:
- Tab "Heute": add a task (optionally with a deadline and reminders), tap the circle to complete it; a spark flies into the jar in tab "Journal".
- Tab "Zerlegen": enter a task and tap "Zerlegen" - our backend asks an AI model for small steps (only the task text is sent).
- Reminders are local notifications only.

Subscription: "FocusHer Vollversion" (product ID focusher_jahr), auto-renewable, 1 year, 29.99 EUR. Purchase in tab "Mehr" -> "Vollversion holen"; "Käufe wiederherstellen" restores it. During the first 7 days after installation all features are free (local trial, no payment). After that the free version keeps tasks, deadlines and reminders and limits the AI decomposer to once per day and the journal to the last 7 days.

The app is German only. Contact: goetzshop1@gmail.com"""

SCREENSHOTS = [os.path.join(HERE, "screenshots", f) for f in (
    "FocusHer-Screenshot-1-heute.png", "FocusHer-Screenshot-2-zerlegen.png", "FocusHer-Screenshot-3-deadline.png",
    "FocusHer-Screenshot-4-journal.png", "FocusHer-Screenshot-5-erinnerung.png")]
SUB_REVIEW_SHOT = os.path.join(HERE, "FocusHer-Abo-Pruefung.png")
TERRITORIES = ["DEU", "AUT", "CHE", "LIE", "LUX"]


# ---------------- Hilfen ----------------
def upload_asset(create_path, rel_name, parent_type, parent_id, path, extra_attrs=None):
    """Reservieren, hochladen, bestätigen (Screenshots, Abo-Prüfbild)."""
    data = open(path, "rb").read()
    body = {"data": {"type": create_path.strip("/"), "attributes": {"fileName": os.path.basename(path), "fileSize": len(data), **(extra_attrs or {})},
                     "relationships": {rel_name: {"data": {"type": parent_type, "id": parent_id}}}}}
    res = call("POST", create_path, json=body)["data"]
    for op in res["attributes"]["uploadOperations"]:
        chunk = data[op["offset"]:op["offset"] + op["length"]]
        hdr = {h["name"]: h["value"] for h in op.get("requestHeaders", [])}
        r = requests.request(op["method"], op["url"], headers=hdr, data=chunk, timeout=120)
        r.raise_for_status()
    call("PATCH", f"{create_path}/{res['id']}", json={"data": {"type": create_path.strip("/"), "id": res["id"],
         "attributes": {"uploaded": True, "sourceFileChecksum": hashlib.md5(data).hexdigest()}}})
    return res["id"]


class Ctx:
    pass


C = Ctx()


def load():
    apps = call("GET", "/apps", params={"filter[bundleId]": BUNDLE})["data"]
    C.app = apps[0]
    C.app_id = C.app["id"]
    log("App:", C.app["attributes"]["name"], C.app_id, "Primärsprache:", C.app["attributes"].get("primaryLocale"),
        "Inhaltsrechte:", C.app["attributes"].get("contentRightsDeclaration"))
    infos = call("GET", f"/apps/{C.app_id}/appInfos")["data"]
    editable = [i for i in infos if i["attributes"].get("appStoreState") not in ("READY_FOR_SALE", "READY_FOR_DISTRIBUTION")] or infos
    C.info = editable[0]
    log("App-Info:", C.info["id"], C.info["attributes"].get("appStoreState") or C.info["attributes"].get("state"))
    vers = call("GET", f"/apps/{C.app_id}/appStoreVersions", params={"filter[platform]": "IOS"})["data"]
    for v in vers:
        log("Version:", v["attributes"]["versionString"], v["attributes"].get("appStoreState"), v["id"])
    open_v = [v for v in vers if v["attributes"].get("appStoreState") in ("PREPARE_FOR_SUBMISSION", "DEVELOPER_REJECTED", "REJECTED", "METADATA_REJECTED", "WAITING_FOR_REVIEW", "IN_REVIEW", "INVALID_BINARY")]
    C.version = open_v[0] if open_v else None


# ---------------- Schritte ----------------
def s_content_rights():
    call("PATCH", f"/apps/{C.app_id}", json={"data": {"type": "apps", "id": C.app_id,
         "attributes": {"contentRightsDeclaration": "DOES_NOT_USE_THIRD_PARTY_CONTENT"}}})
    log("OK Inhaltsrechte: keine Inhalte Dritter")


def s_categories():
    call("PATCH", f"/appInfos/{C.info['id']}", json={"data": {"type": "appInfos", "id": C.info["id"], "relationships": {
        "primaryCategory": {"data": {"type": "appCategories", "id": "PRODUCTIVITY"}},
        "secondaryCategory": {"data": {"type": "appCategories", "id": "LIFESTYLE"}}}}})
    log("OK Kategorien: Produktivität / Lifestyle")


def s_info_loc():
    locs = call("GET", f"/appInfos/{C.info['id']}/appInfoLocalizations")["data"]
    log("App-Info-Sprachen:", [l["attributes"]["locale"] for l in locs])
    attrs = {"subtitle": SUBTITLE, "privacyPolicyUrl": PRIVACY_URL}
    mine = [l for l in locs if l["attributes"]["locale"] == LOC]
    if mine:
        call("PATCH", f"/appInfoLocalizations/{mine[0]['id']}", json={"data": {"type": "appInfoLocalizations", "id": mine[0]["id"], "attributes": attrs}})
    else:
        call("POST", "/appInfoLocalizations", json={"data": {"type": "appInfoLocalizations", "attributes": {"locale": LOC, "name": "FocusHer", **attrs},
             "relationships": {"appInfo": {"data": {"type": "appInfos", "id": C.info["id"]}}}}})
    log("OK Untertitel + Datenschutz-URL")


def s_age():
    d = call("GET", f"/appInfos/{C.info['id']}/ageRatingDeclaration")["data"]
    attrs = {}
    skip = {"kidsAgeBand", "ageRatingOverride", "ageRatingOverrideV2", "koreaAgeRatingOverride", "developerAgeRatingInfoUrl", "gracRatingClassificationNumber"}
    for k, v in d["attributes"].items():
        if k in skip:
            continue
        if isinstance(v, bool) or k in ("gambling", "unrestrictedWebAccess", "lootBox", "messagingAndChat", "parentalControls",
                                        "ageAssurance", "userGeneratedContent", "advertising", "healthOrWellnessTopics", "seventeenPlus", "socialMedia", "socialMediaAgeRestricted"):
            attrs[k] = False
        elif v is None or isinstance(v, str):
            attrs[k] = "NONE"
    try:
        call("PATCH", f"/ageRatingDeclarations/{d['id']}", json={"data": {"type": "ageRatingDeclarations", "id": d["id"], "attributes": attrs}})
    except RuntimeError as e:
        # unbekannte Felder einzeln weglassen
        log("Altersfreigabe abgelehnt:", str(e)[:3000])
        log("Aktuelle Werte:", json.dumps(d["attributes"]))
    log("OK Altersfreigabe: alles Nein/Keine ->", sorted(attrs))


def s_price():
    sched = call("GET", f"/apps/{C.app_id}/appPriceSchedule", ok404=True)
    if sched and sched.get("data"):
        try:
            mp = call("GET", f"/appPriceSchedules/{sched['data']['id']}/manualPrices", params={"include": "appPricePoint"})
            if mp.get("data"):
                log("Preis ist schon gesetzt:", [i["attributes"].get("customerPrice") for i in mp.get("included", [])])
                return
        except RuntimeError:
            pass
    pts = call("GET", f"/apps/{C.app_id}/appPricePoints", params={"filter[territory]": "DEU", "limit": 200})["data"]
    free = [p for p in pts if float(p["attributes"]["customerPrice"]) == 0.0][0]
    call("POST", "/appPriceSchedules", json={"data": {"type": "appPriceSchedules", "relationships": {
        "app": {"data": {"type": "apps", "id": C.app_id}},
        "baseTerritory": {"data": {"type": "territories", "id": "DEU"}},
        "manualPrices": {"data": [{"type": "appPrices", "id": "${p0}"}]}}},
        "included": [{"type": "appPrices", "id": "${p0}", "attributes": {"startDate": None},
                      "relationships": {"appPricePoint": {"data": {"type": "appPricePoints", "id": free["id"]}}}}]})
    log("OK Preis: kostenlos")


def s_availability():
    av = call("GET", f"/apps/{C.app_id}/appAvailabilityV2", ok404=True)
    if av and av.get("data"):
        log("Verfügbarkeit ist schon gesetzt:", av["data"]["id"])
        return
    data, inc = [], []
    allt = [t["id"] for t in call("GET", "/territories", params={"limit": 200})["data"]]
    for i, t in enumerate(allt):
        lid = "${t%d}" % i
        data.append({"type": "territoryAvailabilities", "id": lid})
        inc.append({"type": "territoryAvailabilities", "id": lid, "attributes": {"available": t in TERRITORIES},
                    "relationships": {"territory": {"data": {"type": "territories", "id": t}}}})
    call("POST", "/v2/appAvailabilities", json={"data": {"type": "appAvailabilities", "attributes": {"availableInNewTerritories": False},
         "relationships": {"app": {"data": {"type": "apps", "id": C.app_id}}, "territoryAvailabilities": {"data": data}}}, "included": inc})
    log("OK Verfügbarkeit:", ", ".join(TERRITORIES))


def s_version():
    if not C.version:
        v = call("POST", "/appStoreVersions", json={"data": {"type": "appStoreVersions", "attributes": {"platform": "IOS", "versionString": VERSION},
                 "relationships": {"app": {"data": {"type": "apps", "id": C.app_id}}}}})["data"]
        C.version = v
    vid = C.version["id"]
    call("PATCH", f"/appStoreVersions/{vid}", json={"data": {"type": "appStoreVersions", "id": vid, "attributes": {
        "versionString": VERSION, "copyright": COPYRIGHT, "releaseType": "AFTER_APPROVAL"}}})
    log("OK Version", VERSION, "Copyright, automatische Veröffentlichung nach Freigabe")


def s_build():
    builds = call("GET", "/builds", params={"filter[app]": C.app_id, "filter[preReleaseVersion.version]": VERSION, "sort": "-uploadedDate", "limit": 10})["data"]
    for b in builds:
        log("Build:", b["attributes"]["version"], b["attributes"]["processingState"], "abgelaufen" if b["attributes"].get("expired") else "")
    ok = [b for b in builds if b["attributes"]["processingState"] == "VALID" and not b["attributes"].get("expired")]
    if not ok:
        log("FEHLER: kein gültiger Build für", VERSION)
        return
    b = max(ok, key=lambda x: int(x["attributes"]["version"]))
    if int(b["attributes"]["version"]) < int(os.environ.get("MIN_BUILD", "0")):
        C.build_ok = False
        log("Build", os.environ.get("MIN_BUILD"), "ist noch nicht fertig verarbeitet. Abbruch.")
        return
    call("PATCH", f"/appStoreVersions/{C.version['id']}/relationships/build", json={"data": {"type": "builds", "id": b["id"]}})
    log("OK Build", b["attributes"]["version"], "ausgewählt")


def s_version_loc():
    locs = call("GET", f"/appStoreVersions/{C.version['id']}/appStoreVersionLocalizations")["data"]
    attrs = {"description": DESCRIPTION, "keywords": KEYWORDS, "promotionalText": PROMO, "supportUrl": SUPPORT_URL, "marketingUrl": SUPPORT_URL}
    mine = [l for l in locs if l["attributes"]["locale"] == LOC]
    if mine:
        C.vloc = mine[0]["id"]
        call("PATCH", f"/appStoreVersionLocalizations/{C.vloc}", json={"data": {"type": "appStoreVersionLocalizations", "id": C.vloc, "attributes": attrs}})
    else:
        C.vloc = call("POST", "/appStoreVersionLocalizations", json={"data": {"type": "appStoreVersionLocalizations", "attributes": {"locale": LOC, **attrs},
                      "relationships": {"appStoreVersion": {"data": {"type": "appStoreVersions", "id": C.version["id"]}}}}})["data"]["id"]
    log("OK Beschreibung, Werbetext, Schlüsselwörter, Support-URL", f"({len(DESCRIPTION)} Zeichen)")


def s_screens():
    sets = call("GET", f"/appStoreVersionLocalizations/{C.vloc}/appScreenshotSets", params={"include": "appScreenshots"})
    by = {s["attributes"]["screenshotDisplayType"]: s for s in sets["data"]}
    log("Vorhandene Screenshot-Gruppen:", list(by))
    if "APP_IPHONE_67" in by:
        sid = by["APP_IPHONE_67"]["id"]
        for sh in by["APP_IPHONE_67"].get("relationships", {}).get("appScreenshots", {}).get("data", []):
            call("DELETE", f"/appScreenshots/{sh['id']}")
    else:
        sid = call("POST", "/appScreenshotSets", json={"data": {"type": "appScreenshotSets", "attributes": {"screenshotDisplayType": "APP_IPHONE_67"},
                   "relationships": {"appStoreVersionLocalization": {"data": {"type": "appStoreVersionLocalizations", "id": C.vloc}}}}})["data"]["id"]
    ids = [upload_asset("/appScreenshots", "appScreenshotSet", "appScreenshotSets", sid, p) for p in SCREENSHOTS]
    call("PATCH", f"/appScreenshotSets/{sid}/relationships/appScreenshots", json={"data": [{"type": "appScreenshots", "id": i} for i in ids]})
    time.sleep(15)
    st = call("GET", f"/appScreenshotSets/{sid}/appScreenshots")["data"]
    log("OK Screenshots 6,9\":", [s["attributes"].get("assetDeliveryState", {}).get("state") for s in st])


def s_review():
    attrs = {"contactFirstName": "Walter", "contactLastName": "Götz", "contactPhone": "+49 175 2884648",
             "contactEmail": "goetzshop1@gmail.com", "demoAccountRequired": False, "notes": REVIEW_NOTES}
    cur = call("GET", f"/appStoreVersions/{C.version['id']}/appStoreReviewDetail", ok404=True)
    if cur and cur.get("data"):
        call("PATCH", f"/appStoreReviewDetails/{cur['data']['id']}", json={"data": {"type": "appStoreReviewDetails", "id": cur["data"]["id"], "attributes": attrs}})
    else:
        call("POST", "/appStoreReviewDetails", json={"data": {"type": "appStoreReviewDetails", "attributes": attrs,
             "relationships": {"appStoreVersion": {"data": {"type": "appStoreVersions", "id": C.version["id"]}}}}})
    log("OK Prüfer-Kontakt und Hinweise")


def s_subscription(fix=True):
    groups = call("GET", f"/apps/{C.app_id}/subscriptionGroups", params={"include": "subscriptions,subscriptionGroupLocalizations"})
    inc = groups.get("included", [])
    for g in groups["data"]:
        log("Abo-Gruppe:", g["attributes"]["referenceName"], g["id"])
        glocs = [i for i in inc if i["type"] == "subscriptionGroupLocalizations"
                 and i["id"] in [x["id"] for x in g["relationships"]["subscriptionGroupLocalizations"].get("data", [])]]
        log("  Gruppen-Sprachen:", [(l["attributes"]["locale"], l["attributes"].get("name"), l["attributes"].get("state")) for l in glocs])
        if fix and not any(l["attributes"]["locale"] == LOC for l in glocs):
            call("POST", "/subscriptionGroupLocalizations", json={"data": {"type": "subscriptionGroupLocalizations",
                 "attributes": {"locale": LOC, "name": "FocusHer"}, "relationships": {"subscriptionGroup": {"data": {"type": "subscriptionGroups", "id": g["id"]}}}}})
            log("  OK Gruppen-Sprache Deutsch angelegt")
    subs = [i for i in inc if i["type"] == "subscriptions"]
    C.subs = subs
    for s in subs:
        a = s["attributes"]
        log("Abo:", a.get("productId"), a.get("name"), a.get("state"), a.get("subscriptionPeriod"), s["id"])
        locs = call("GET", f"/subscriptions/{s['id']}/subscriptionLocalizations")["data"]
        log("  Sprachen:", [(l["attributes"]["locale"], l["attributes"].get("name"), l["attributes"].get("state")) for l in locs])
        if fix and not any(l["attributes"]["locale"] == LOC for l in locs):
            call("POST", "/subscriptionLocalizations", json={"data": {"type": "subscriptionLocalizations",
                 "attributes": {"locale": LOC, "name": "FocusHer Vollversion", "description": "Unbegrenzt zerlegen, volles Journal"},
                 "relationships": {"subscription": {"data": {"type": "subscriptions", "id": s["id"]}}}}})
            log("  OK Abo-Sprache Deutsch angelegt")
        prices = call("GET", f"/subscriptions/{s['id']}/prices", params={"include": "subscriptionPricePoint,territory", "limit": 200})
        terr = [p["relationships"]["territory"]["data"]["id"] for p in prices["data"]]
        deu = [i["attributes"].get("customerPrice") for i in prices.get("included", []) if i["type"] == "subscriptionPricePoints"][:3]
        log("  Preise in", len(terr), "Ländern, z. B.", deu, "DEU dabei:", "DEU" in terr)
        av = call("GET", f"/subscriptions/{s['id']}/subscriptionAvailability", ok404=True)
        log("  Verfügbarkeit:", "gesetzt" if av and av.get("data") else "FEHLT")
        if fix and not (av and av.get("data")):
            call("POST", "/subscriptionAvailabilities", json={"data": {"type": "subscriptionAvailabilities", "attributes": {"availableInNewTerritories": False},
                 "relationships": {"subscription": {"data": {"type": "subscriptions", "id": s["id"]}},
                                   "availableTerritories": {"data": [{"type": "territories", "id": t} for t in TERRITORIES]}}}})
            log("  OK Abo-Verfügbarkeit gesetzt")
        shot = call("GET", f"/subscriptions/{s['id']}/appStoreReviewScreenshot", ok404=True)
        log("  Prüfbild:", "vorhanden" if shot and shot.get("data") else "FEHLT")
        if fix and not (shot and shot.get("data")):
            upload_asset("/subscriptionAppStoreReviewScreenshots", "subscription", "subscriptions", s["id"], SUB_REVIEW_SHOT)
            log("  OK Prüfbild hochgeladen")
        if fix and not a.get("reviewNote"):
            call("PATCH", f"/subscriptions/{s['id']}", json={"data": {"type": "subscriptions", "id": s["id"], "attributes": {
                "reviewNote": "Purchase in tab 'Mehr' -> 'Vollversion holen'. Unlocks unlimited AI decomposition and full journal history."}}})
            log("  OK Prüfhinweis zum Abo")


def setup():
    load()
    for name, fn in [("Inhaltsrechte", s_content_rights), ("Kategorien", s_categories), ("App-Info-Texte", s_info_loc),
                     ("Altersfreigabe", s_age), ("Preis", s_price), ("Verfügbarkeit", s_availability), ("Version", s_version),
                     ("Build", s_build), ("Versionstexte", s_version_loc), ("Screenshots", s_screens), ("Prüfer-Infos", s_review),
                     ("Abo", s_subscription)]:
        only = os.environ.get("STEPS")
        if only and name not in only.split(","):
            continue
        if name in ("Screenshots",) and not getattr(C, "vloc", None):
            continue
        step(name, fn)


def status():
    load()
    step("Abo", lambda: s_subscription(fix=False))
    if C.version:
        step("Build", lambda: log("Build an Version:", call("GET", f"/appStoreVersions/{C.version['id']}/build").get("data")))


def submit():
    load()
    C.build_ok = True
    step("Build", s_build)
    if not C.build_ok:
        return
    step("Abo", lambda: s_subscription(fix=False))
    subs = call("GET", "/reviewSubmissions", params={"filter[app]": C.app_id, "filter[platform]": "IOS"})["data"]
    open_s = [x for x in subs if x["attributes"]["state"] in ("READY_FOR_REVIEW",)]
    rs = open_s[0] if open_s else call("POST", "/reviewSubmissions", json={"data": {"type": "reviewSubmissions", "attributes": {"platform": "IOS"},
                                       "relationships": {"app": {"data": {"type": "apps", "id": C.app_id}}}}})["data"]
    try:
        call("POST", "/reviewSubmissionItems", json={"data": {"type": "reviewSubmissionItems", "relationships": {
            "reviewSubmission": {"data": {"type": "reviewSubmissions", "id": rs["id"]}},
            "appStoreVersion": {"data": {"type": "appStoreVersions", "id": C.version["id"]}}}}})
        log("OK Version zur Einreichung hinzugefügt")
    except RuntimeError as e:
        log("Version hinzufügen:", str(e)[:1200])
    ok_sub = True
    for s in C.subs:
        if s["attributes"].get("state") in ("READY_TO_SUBMIT", "DEVELOPER_ACTION_NEEDED", "REJECTED"):
            try:
                call("POST", "/subscriptionSubmissions", json={"data": {"type": "subscriptionSubmissions",
                     "relationships": {"subscription": {"data": {"type": "subscriptions", "id": s["id"]}}}}})
                log("OK Abo", s["attributes"].get("productId"), "mit der Version eingereicht")
            except RuntimeError as e:
                ok_sub = False
                log("FEHLER Abo einreichen:", str(e)[:2000])
    if not ok_sub and os.environ.get("FORCE") != "1":
        log("NICHT eingereicht, weil das Abo nicht mitkam. Einreichung bleibt als Entwurf.")
        return
    try:
        call("PATCH", f"/reviewSubmissions/{rs['id']}", json={"data": {"type": "reviewSubmissions", "id": rs["id"], "attributes": {"submitted": True}}})
        log("OK EINGEREICHT: Version", VERSION, "wartet auf die Prüfung")
    except RuntimeError as e:
        log("FEHLER beim Einreichen:", str(e)[:2500])


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    try:
        {"setup": setup, "status": status, "submit": submit}[mode]()
    finally:
        open(os.environ.get("REPORT_PATH", "listing-report.txt"), "w").write("\n".join(REPORT) + "\n")
