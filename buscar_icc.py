import json, re, time
from datetime import datetime
from playwright.sync_api import sync_playwright

MESES_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage"
        ])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            java_script_enabled=True
        )
        page = context.new_page()
        page.goto("https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-33", timeout=60000)
        # Esperar 15 segundos para que el JS cargue el contenido
        page.wait_for_timeout(15000)
        content = page.inner_text("body")
        html = page.content()
        browser.close()

    patron = r"correspondiente a\s+(\w+)\s+de\s+(\d{4})\s+registra una\s+(?:suba|baja)\s+de\s+([\d,\.]+)%"
    m = re.search(patron, content, re.IGNORECASE)
    if not m:
        m = re.search(patron, html, re.IGNORECASE)

    if m:
        mes_indec_nombre = m.group(1).capitalize()
        anio_indec = int(m.group(2))
        pct = float(m.group(3).replace(",", "."))
        mes_indec_idx = next((i for i,n in enumerate(MESES_ES) if n.lower()==mes_indec_nombre.lower()), -1)
        hoy = datetime.utcnow()
        mes_anterior_idx = (hoy.month - 2) % 12
        disponible = (mes_indec_idx == mes_anterior_idx)
        res = {"encontrado": True, "disponible": disponible,
               "mes_indec": mes_indec_nombre, "anio_indec": anio_indec,
               "mes_actual_idx": hoy.month-1, "pct": pct, "ts": hoy.isoformat()}
    else:
        res = {"encontrado": False, "disponible": False,
               "text_len": len(content), "html_len": len(html),
               "text_sample": content[:500], "ts": datetime.utcnow().isoformat()}

except Exception as e:
    res = {"encontrado": False, "disponible": False, "error": str(e)[:300], "ts": datetime.utcnow().isoformat()}

with open("icc-data.json", "w") as f:
    json.dump(res, f, ensure_ascii=False)
print(json.dumps(res))
