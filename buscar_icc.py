import json, re, ftplib, io
from datetime import datetime

MESES_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

try:
    hoy = datetime.utcnow()
    mes_actual_idx = hoy.month - 1
    mes_anterior_idx = (mes_actual_idx - 1) % 12

    # Conectar al FTP del INDEC
    ftp = ftplib.FTP("ftp.indec.gob.ar", timeout=30)
    ftp.login()
    
    # Listar directorio de construccion
    lines = []
    ftp.retrlines("LIST /Varios/economia/icc/", lines.append)
    ftp.quit()
    
    res = {"encontrado": False, "ftp_lines": lines[:20], "ts": hoy.isoformat()}
except Exception as e:
    res = {"encontrado": False, "error": str(e), "ts": datetime.utcnow().isoformat()}

with open("icc-data.json", "w") as f:
    json.dump(res, f, ensure_ascii=False)
print(json.dumps({"error": res.get("error"), "lines": res.get("ftp_lines", [])[:5]}))
