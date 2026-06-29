import urllib.request, json, re
from datetime import datetime

MESES_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

url = "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-33"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", errors="ignore")

    # El HTML estatico contiene los links a los PDFs de los informes
    # Buscar el link al PDF del ultimo informe: icc_MM_YYYYXXXXXXXX.pdf
    # Ejemplo: icc_05_2673538FC44D.pdf -> mes 05 = Mayo
    patron_pdf = r'icc_(\d{2})_[A-F0-9]+\.pdf'
    matches = re.findall(patron_pdf, html, re.IGNORECASE)

    # Mostrar los primeros matches para diagnostico
    res = {
        "encontrado": False,
        "pdf_matches": matches[:10],
        "html_sample": html[15000:15500].replace('"', "'"),
        "ts": datetime.utcnow().isoformat()
    }

except Exception as e:
    res = {"encontrado": False, "error": str(e), "ts": datetime.utcnow().isoformat()}

with open("icc-data.json", "w") as f:
    json.dump(res, f, ensure_ascii=False)
print(json.dumps(res))
