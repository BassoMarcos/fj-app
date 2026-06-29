import urllib.request, json, re
from datetime import datetime

MESES_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

# El INDEC carga el contenido via un endpoint JSON interno
# Probamos directamente ese endpoint
urls_a_probar = [
    "https://www.indec.gob.ar/ftp/cuadros/economia/icc_03_26.xls",
    "https://www.indec.gob.ar/uploads/informesdeprensa/icc_05_2673538FC44D.pdf",
    "https://www.indec.gob.ar/nivel4Default.asp?id_tema_1=3&id_tema_2=5&id_tema_3=33",
]

results = {}
for url in urls_a_probar:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            content_type = r.headers.get("Content-Type", "")
            size = len(r.read())
            results[url] = {"status": r.status, "type": content_type, "size": size}
    except Exception as e:
        results[url] = {"error": str(e)[:100]}

# También buscar en el HTML principal si hay una URL de API interna
req_main = urllib.request.Request("https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-33",
    headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_main, timeout=30) as r:
    html = r.read().decode("utf-8", errors="ignore")

# Buscar patrones de API o endpoints JSON
api_patterns = re.findall(r'["\']([^"\']*(?:api|json|datos|informes|icc)[^"\']{5,50})["\']', html, re.IGNORECASE)
results["api_patterns"] = list(set(api_patterns))[:20]

with open("icc-data.json", "w") as f:
    json.dump({"encontrado": False, "diag": results, "ts": datetime.utcnow().isoformat()}, f, ensure_ascii=False)
print("OK")
