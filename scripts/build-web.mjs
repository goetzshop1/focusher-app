// Baut den Ordner www/ für die App:
// - src/app.html (die FocusHer-Oberfläche) in ein vollständiges HTML-Dokument einbetten
// - Schriften lokal mitliefern (funktioniert offline)
// - src/bridge.js mit esbuild bündeln
// - config.js aus Umgebungsvariablen schreiben
import { readFileSync, writeFileSync, mkdirSync, copyFileSync, existsSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { build } from "esbuild";

const root = new URL("..", import.meta.url).pathname;
const www = join(root, "www");
mkdirSync(join(www, "fonts"), { recursive: true });

// 1) Schriften
const fonts = [
  { pkg: "@fontsource/atkinson-hyperlegible", family: "Atkinson Hyperlegible", files: [["latin-400-normal", 400, "normal"], ["latin-700-normal", 700, "normal"], ["latin-400-italic", 400, "italic"]] },
  { pkg: "@fontsource/bricolage-grotesque", family: "Bricolage Grotesque", files: [["latin-500-normal", 500, "normal"], ["latin-700-normal", 700, "normal"]] },
];
let css = "";
for (const f of fonts) {
  const dir = join(root, "node_modules", f.pkg, "files");
  const slug = f.pkg.split("/")[1];
  for (const [name, weight, style] of f.files) {
    const file = `${slug}-${name}.woff2`;
    const src = join(dir, file);
    if (!existsSync(src)) { console.warn("Schrift fehlt:", file, readdirSync(dir).slice(0, 5)); continue; }
    copyFileSync(src, join(www, "fonts", file));
    css += `@font-face{font-family:"${f.family}";font-style:${style};font-weight:${weight};font-display:swap;src:url("fonts/${file}") format("woff2")}\n`;
  }
}
writeFileSync(join(www, "fonts.css"), css);

// 2) Konfiguration
const cfg = {
  version: process.env.APP_VERSION || "1.0.0",
  apiBase: process.env.FH_API_BASE || "https://base44.app/api/apps/6ac55f2ebe297f016feac28a/functions",
  apiKey: process.env.FH_API_KEY || "fh-app-2026-velluna",
  revenuecatIos: process.env.REVENUECAT_IOS_KEY || "appl_MBEknWSUPSAUcZaMboYCiBKYWNT", // öffentlicher SDK-Schlüssel, darf in der App stehen
  revenuecatAndroid: process.env.REVENUECAT_ANDROID_KEY || "",
  entitlement: "focusher_pro",
  priceLabel: "29,99 €",
};
writeFileSync(join(www, "config.js"), "window.FOCUSHER_CONFIG = " + JSON.stringify(cfg, null, 2) + ";\n");

// 3) Bridge bündeln
await build({
  entryPoints: [join(root, "src", "bridge.js")],
  bundle: true, format: "iife", target: ["safari15", "chrome100"], minify: true,
  outfile: join(www, "bridge.js"), logLevel: "warning",
});

// 4) HTML zusammensetzen
let body = readFileSync(join(root, "src", "app.html"), "utf8");
body = body.replace(/<link rel="preconnect"[^>]*>\s*/g, "")
           .replace(/<link rel="stylesheet" href="https:\/\/fonts\.googleapis\.com[^>]*>/, '<link rel="stylesheet" href="fonts.css">');
const title = (body.match(/<title>[\s\S]*?<\/title>/) || ["<title>FocusHer</title>"])[0];
body = body.replace(title, "");
const head = `<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="format-detection" content="telephone=no">
${title}
<style>
:root{color-scheme:dark}
html{-webkit-text-size-adjust:100%;touch-action:manipulation;padding-top:env(safe-area-inset-top,0px)}
body{margin:0;touch-action:manipulation;-webkit-tap-highlight-color:transparent;overscroll-behavior-y:none}
img{max-width:100%}
[hidden]{display:none!important}
</style>
<script src="config.js"></script>
<script src="bridge.js"></script>
</head>
<body>
`;
writeFileSync(join(www, "index.html"), head + body + "\n</body>\n</html>\n");
console.log("www/ gebaut, Version", cfg.version, "RevenueCat iOS:", cfg.revenuecatIos ? "gesetzt" : "FEHLT");
