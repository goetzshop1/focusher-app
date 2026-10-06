# FocusHer – App für iOS (später Android)

Reizarmer Alltagsmanager für Erwachsene mit ADHS: KI-Zerleger, Energie-Filter,
Deadlines mit echten Erinnerungen, Funken-Journal. Jahresabo 29,99 € über Apple.

## Aufbau
- `src/app.html` – die komplette App-Oberfläche (dieselbe wie in der Vorschau)
- `src/bridge.js` – Verbindung zum iPhone: Abo (RevenueCat), Erinnerungen, KI, Feedback
- `scripts/build-web.mjs` – baut daraus den Ordner `www/`
- `assets/` – App-Symbol und Startbild
- Server für KI und Feedback: Base44-App „FocusHer Dashboard“ (Funktionen `fhDecompose`, `fhFeedback`, Tabelle `Feedback`)

## Einmalig einrichten (GitHub → Settings → Secrets and variables → Actions)
- Secret `APPSTORE_P8`: Inhalt der Datei `AuthKey_Z7T5YKSW7U.p8` (derselbe Schlüssel wie bei Velluna)
- Secret `REVENUECAT_IOS_KEY`: öffentlicher iOS-Schlüssel aus RevenueCat (beginnt mit `appl_`)
- Variable `APPLE_TEAM_ID`: Team-ID aus developer.apple.com → Mitgliedschaft (10 Zeichen)

## Neue Version hochladen
Actions → „iOS bauen und zu App Store Connect hochladen“ → Run workflow → Versionsnummer eingeben.
Nach 10–30 Minuten steht der Build in TestFlight.
