import json, re
from datetime import datetime
from playwright.sync_api import sync_playwright

try:
    api_responses = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Interceptar todas las respuestas JSON/text
        def handle_response(response):
            url = response.url
            if any(x in url for x in ['api', 'json', 'icc', 'datos', 'informe', 'prensa']):
                try:
                    body = response.text()
                    if len(body) > 20 and len(body) < 50000:
                        api_responses.append({"url": url, "status": response.status, "body_sample": body[:500]})
                except:
                    api_responses.append({"url": url, "status": response.status, "error": "no body"})
        
        page.on("response", handle_response)
        
        page.goto("https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-33", 
                  timeout=60000, wait_until="networkidle")
        
        browser.close()

    res = {
        "encontrado": False,
        "api_responses": api_responses[:15],
        "total_responses": len(api_responses),
        "ts": datetime.utcnow().isoformat()
    }

except Exception as e:
    res = {"encontrado": False, "error": str(e)[:300], "ts": datetime.utcnow().isoformat()}

with open("icc-data.json", "w") as f:
    json.dump(res, f, ensure_ascii=False)
print(json.dumps({"total": res.get("total_responses"), "error": res.get("error")}))
