#!/usr/bin/env python3
"""App-Store-Signatur über die App Store Connect API, ohne Mac und ohne Gerät.

  python3 scripts/asc_signing.py setup    -> legt Verteilungszertifikat + App-Store-Profil an,
                                            importiert beides, schreibt Werte nach $GITHUB_ENV
  python3 scripts/asc_signing.py cleanup  -> widerruft das Zertifikat und löscht das Profil wieder

Benötigt: API_KEY_ID, API_ISSUER, KEY_PATH, BUNDLE_ID, RUN_ID (Umgebungsvariablen).
"""
import base64, json, os, subprocess, sys, time, uuid, plistlib, tempfile
import jwt, requests

API = "https://api.appstoreconnect.apple.com/v1"
STATE = os.path.expanduser("~/asc_signing_state.json")


def token():
    key = open(os.environ["KEY_PATH"]).read()
    now = int(time.time())
    return jwt.encode({"iss": os.environ["API_ISSUER"], "iat": now, "exp": now + 1100, "aud": "appstoreconnect-v1"},
                      key, algorithm="ES256", headers={"kid": os.environ["API_KEY_ID"], "typ": "JWT"})


def call(method, path, **kw):
    r = requests.request(method, API + path, headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"}, timeout=60, **kw)
    if r.status_code >= 400:
        print(f"API-Fehler {method} {path}: {r.status_code} {r.text[:800]}", file=sys.stderr)
        r.raise_for_status()
    return r.json() if r.text else {}


def sh(*args):
    subprocess.run(args, check=True)


def setup():
    run = os.environ.get("RUN_ID", str(int(time.time())))
    bundle = os.environ["BUNDLE_ID"]
    work = tempfile.mkdtemp()
    key, csr = os.path.join(work, "dist.key"), os.path.join(work, "dist.csr")
    sh("openssl", "req", "-new", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", csr, "-subj", "/CN=FocusHer CI/O=VellunaPrintsDesign/C=DE")
    csr_text = open(csr).read()

    # 0) Alte CI-Zertifikate von früheren Builds widerrufen (Platz für das neue schaffen)
    for c in call("GET", "/certificates", params={"filter[certificateType]": "DISTRIBUTION", "limit": 200})["data"]:
        if "FocusHer CI" in (c["attributes"].get("name") or "") or "FocusHer CI" in (c["attributes"].get("displayName") or ""):
            try:
                call("DELETE", f"/certificates/{c['id']}")
                print("Altes CI-Zertifikat widerrufen:", c["id"])
            except Exception as e:
                print("Konnte altes Zertifikat nicht widerrufen:", e)

    # 1) Verteilungszertifikat anlegen
    body = {"data": {"type": "certificates", "attributes": {"csrContent": csr_text, "certificateType": "DISTRIBUTION"}}}
    try:
        cert = call("POST", "/certificates", json=body)["data"]
    except Exception:
        # Höchstzahl erreicht: ältestes Verteilungszertifikat widerrufen und erneut versuchen
        old = sorted(call("GET", "/certificates", params={"filter[certificateType]": "DISTRIBUTION", "limit": 200})["data"],
                     key=lambda c: c["attributes"].get("expirationDate", ""))
        if old:
            call("DELETE", f"/certificates/{old[0]['id']}")
            print("Ältestes Zertifikat widerrufen:", old[0]["id"])
        cert = call("POST", "/certificates", json=body)["data"]
    cert_id = cert["id"]
    der = base64.b64decode(cert["attributes"]["certificateContent"])
    cer, pem, p12 = (os.path.join(work, n) for n in ("dist.cer", "dist.pem", "dist.p12"))
    open(cer, "wb").write(der)
    sh("openssl", "x509", "-inform", "DER", "-in", cer, "-out", pem)
    pw = uuid.uuid4().hex
    try:
        sh("openssl", "pkcs12", "-export", "-legacy", "-inkey", key, "-in", pem, "-out", p12, "-passout", "pass:" + pw)
    except subprocess.CalledProcessError:
        sh("openssl", "pkcs12", "-export", "-inkey", key, "-in", pem, "-out", p12, "-passout", "pass:" + pw)

    # 2) Schlüsselbund anlegen und importieren
    kc = os.path.expanduser("~/Library/Keychains/fh-ci.keychain-db")
    sh("security", "create-keychain", "-p", pw, kc)
    sh("security", "set-keychain-settings", "-lut", "21600", kc)
    sh("security", "unlock-keychain", "-p", pw, kc)
    sh("security", "import", p12, "-k", kc, "-P", pw, "-T", "/usr/bin/codesign", "-T", "/usr/bin/security")
    sh("security", "set-key-partition-list", "-S", "apple-tool:,apple:,codesign:", "-s", "-k", pw, kc)
    existing = subprocess.run(["security", "list-keychains", "-d", "user"], capture_output=True, text=True).stdout.split()
    sh("security", "list-keychains", "-d", "user", "-s", kc, *[e.strip('"') for e in existing])

    # 3) App-Store-Profil anlegen
    b = call("GET", "/bundleIds", params={"filter[identifier]": bundle, "limit": 5})["data"]
    b = [x for x in b if x["attributes"]["identifier"] == bundle]
    if not b:
        raise SystemExit(f"Bundle-ID {bundle} ist im Entwicklerkonto nicht registriert.")
    name = f"FocusHer AppStore CI {run}"
    prof = call("POST", "/profiles", json={"data": {"type": "profiles", "attributes": {"name": name, "profileType": "IOS_APP_STORE"},
        "relationships": {"bundleId": {"data": {"type": "bundleIds", "id": b[0]["id"]}},
                          "certificates": {"data": [{"type": "certificates", "id": cert_id}]}}}})["data"]
    content = base64.b64decode(prof["attributes"]["profileContent"])
    pdir = os.path.expanduser("~/Library/MobileDevice/Provisioning Profiles")
    os.makedirs(pdir, exist_ok=True)
    # UUID aus dem signierten Profil lesen
    raw = subprocess.run(["security", "cms", "-D"], input=content, capture_output=True, check=True).stdout
    puuid = plistlib.loads(raw)["UUID"]
    open(os.path.join(pdir, puuid + ".mobileprovision"), "wb").write(content)
    for d in (os.path.expanduser("~/Library/Developer/Xcode/UserData/Provisioning Profiles"),):
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, puuid + ".mobileprovision"), "wb").write(content)

    json.dump({"cert_id": cert_id, "profile_id": prof["id"], "keychain": kc}, open(STATE, "w"))
    with open(os.environ["GITHUB_ENV"], "a") as f:
        f.write(f"PROFILE_NAME={name}\nPROFILE_UUID={puuid}\n")
    print("Signatur bereit:", name, puuid)


def cleanup():
    if not os.path.exists(STATE):
        return
    st = json.load(open(STATE))
    # Zertifikat bleibt gültig, sonst wird die Signatur des Builds bei der Einreichung ungültig (ITMS-90035)
    for path in (f"/profiles/{st['profile_id']}",):
        try:
            call("DELETE", path)
        except Exception as e:
            print("Aufräumen fehlgeschlagen:", path, e)
    subprocess.run(["security", "delete-keychain", st["keychain"]])
    print("Profil gelöscht, Zertifikat bleibt gültig.")


if __name__ == "__main__":
    {"setup": setup, "cleanup": cleanup}[sys.argv[1]]()
