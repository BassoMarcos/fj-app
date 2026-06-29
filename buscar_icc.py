import urllib.request, json, re
from datetime import datetime

url = "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-33"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", errors="ignore")

    # Buscar el fragmento clave para diagnostico
    idx = html.find("card-texto3")
    fragmento = html[idx:idx+500] if idx >= 0 else "NO ENCONTRADO card-texto3"

    patron = r"correspondiente a\s+(\w+)\s+de\s+(\d{4})\s+registra una\s+(?:suba|baja)\s+de\s+([\d,\.]+)%"
    m = re.search(patron, html, re.IGNORECASE)

    if m:
        res = {"encontrado": True, "match": m.group(0)[:100], "ts": datetime.utcnow().isoformat()}
    else:
        res = {"encontrado": False, "fragmento": fragmento[:300], "html_len": len(html), "ts": datetime.utcnow().isoformat()}

except Exception as e:
    res = {"encontrado": False, "error": str(e), "ts": datetime.utcnow().isoformat()}

with open("icc-data.json", "w") as f:
    json.dump(res, f, ensure_ascii=False)
print(json.dumps(res))
