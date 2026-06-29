import urllib.request, json, re
from datetime import datetime

MESES_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

# El INDEC tiene una página de informes técnicos con los links a los PDFs
# Probar la URL de informes técnicos que vimos en el HTML
url = "https://www.indec.gob.ar/indec/web/Institucional/Indec/InformesTecnicos"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", errors="ignore")
    
    # Buscar links a PDFs del ICC
    icc_links = re.findall(r'icc_\d{2}_[A-F0-9]+\.pdf', html, re.IGNORECASE)
    # Buscar cualquier link a PDF que tenga ICC
    pdf_links = re.findall(r'href=["\']([^"\']*icc[^"\']*\.pdf)["\']', html, re.IGNORECASE)
    
    res = {
        "encontrado": False,
        "url_probada": url,
        "html_len": len(html),
        "icc_links": icc_links[:10],
        "pdf_links": pdf_links[:10],
        "sample": html[5000:5500],
        "ts": datetime.utcnow().isoformat()
    }
except Exception as e:
    res = {"encontrado": False, "error": str(e), "ts": datetime.utcnow().isoformat()}

with open("icc-data.json", "w") as f:
    json.dump(res, f, ensure_ascii=False)
print("OK")
