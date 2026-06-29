import json, re, subprocess, sys
from datetime import datetime

# Instalar playwright
subprocess.run([sys.executable, "-m", "pip", "install", "playwright", "-q"], check=True)
subprocess.run([sys.executable, "-m", "playwright", "install", "chromium", "--with-deps"], 
               check=True, capture_output=True)

from playwright.sync_api import sync_playwright

MESES_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-33", timeout=30000)
        # Esperar que cargue el contenido dinamico
        page.wait_for_selector(".card-texto3", timeout=20000)
        content = page.text_content(".card-texto3")
        browser.close()

    patron = r"correspondiente a\s+(\w+)\s+de\s+(\d{4})\s+registra una\s+(?:suba|baja)\s+de\s+([\d,\.]+)%"
    m = re.search(patron, content, re.IGNORECASE)

    if m:
        mes_indec_nombre = m.group(1).capitalize()
        anio_indec = int(m.group(2))
        pct = float(m.group(3).replace(",", "."))

        mes_indec_idx = next((i for i,n in enumerate(MESES_ES) 
                              if n.lower() == mes_indec_nombre.lower()), -1)
        hoy = datetime.utcnow()
        mes_actual_idx = hoy.month - 1
        mes_anterior_idx = (mes_actual_idx - 1) % 12
        disponible = (mes_indec_idx == mes_anterior_idx)

        res = {
            "encontrado": True,
            "disponible": disponible,
            "mes_indec": mes_indec_nombre,
            "anio_indec": anio_indec,
            "mes_actual_idx": mes_actual_idx,
            "pct": pct,
            "ts": hoy.isoformat()
        }
    else:
        res = {"encontrado": False, "disponible": False, 
               "error": "Texto encontrado pero no coincide patron", 
               "content_sample": content[:200],
               "ts": datetime.utcnow().isoformat()}

except Exception as e:
    res = {"encontrado": False, "disponible": False, 
           "error": str(e), "ts": datetime.utcnow().isoformat()}

with open("icc-data.json", "w") as f:
    json.dump(res, f, ensure_ascii=False)
print(json.dumps(res))
