import subprocess
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import sys
import glob
import re
import base64
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# === CONFIG ===
load_dotenv()
MODEL = "gpt-4o-mini"
TOKEN_LIMIT = 1000000
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === FUNZIONI ===

def estrai_html_css_js_da_url(url):
    try:
        print(f"[INFO] Scaricando contenuto da: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html = response.text[:TOKEN_LIMIT]

        print(f"[DEBUG] HTML scaricato: {len(response.text)} caratteri (tagliato a {len(html)})")
        print(f"[DEBUG] Anteprima HTML:\n{html[:500]}\n---\n")

        soup = BeautifulSoup(html, 'html.parser')

        # CSS
        css = ''
        for style in soup.find_all("style"):
            if style.string:
                css += style.string + "\n"
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if href:
                full = requests.compat.urljoin(url, href)
                try:
                    print(f"[INFO] Scarico CSS esterno: {full}")
                    r2 = requests.get(full, timeout=10)
                    css += f"\n/* from {full} */\n" + r2.text + "\n"
                except Exception as e:
                    print(f"[WARNING] Impossibile scaricare CSS {full}: {e}")
        css = css[:TOKEN_LIMIT]

        print(f"[DEBUG] CSS estratto: {len(css)} caratteri")
        print(f"[DEBUG] Anteprima CSS:\n{css[:300]}\n---\n")

        # JS
        js = ''
        for script in soup.find_all("script"):
            if script.string and not script.get("src"):
                js += script.string + "\n"
        for script in soup.find_all("script", src=True):
            src = script.get("src")
            full = requests.compat.urljoin(url, src)
            try:
                print(f"[INFO] Scarico JS esterno: {full}")
                r3 = requests.get(full, timeout=10)
                js += f"\n/* from {full} */\n" + r3.text + "\n"
            except Exception as e:
                print(f"[WARNING] Impossibile scaricare JS {full}: {e}")
        js = js[:TOKEN_LIMIT]

        print(f"[DEBUG] JS estratto: {len(js)} caratteri")
        print(f"[DEBUG] Anteprima JS:\n{js[:300]}\n---\n")

        return html, css, js
    except Exception as e:
        print(f"[ERRORE] estrai_html_css_js_da_url: {e}")
        return None, None, None


def screenshot_full_cdp(url, output_path='screenshot.png', width=1920):
    """Cattura screenshot a pagina intera"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument(f"--window-size={width},1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--hide-scrollbars")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.get(url)

    total_height = driver.execute_script("""
        return Math.max(
            document.body.scrollHeight,
            document.documentElement.scrollHeight
        );
    """)

    driver.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": width,
            "height": total_height,
            "deviceScaleFactor": 1,
            "mobile": False
        }
    )

    result = driver.execute_cdp_cmd("Page.captureScreenshot", {
        "fromSurface": True,
        "captureBeyondViewport": True
    })
    img_data = base64.b64decode(result["data"])
    with open(output_path, "wb") as f:
        f.write(img_data)

    print(f"[✅] Screenshot salvato in: {output_path}")
    driver.quit()
    return output_path

def genera_report_chatgpt(html, css, js, url, screenshot_path=None):
    user_content = [
        {"type": "text", "text": f"""
Sei un esperto di accessibilità web. Analizza il seguente sito secondo le WCAG 2.1.

URL: {url}

--- HTML ---
{html}

--- CSS ---
{css}

--- JavaScript ---
{js}

Obiettivi:
- Panoramica generale sull'accessibilità della pagina.
- Evidenzia gli errori principali (alt mancanti, semantica errata, contrasto insufficiente, focus, script non accessibili, ecc.).
- Raggruppa le problematiche simili.
- Elenca i 3-5 problemi più critici con esempi.
- Indica i punti di forza e le azioni prioritarie.
"""}
    ]

    # Se c'è lo screenshot, lo aggiungiamo al prompt
    if screenshot_path:
        with open(screenshot_path, "rb") as img_file:
            img_b64 = base64.b64encode(img_file.read()).decode()
            user_content.append(
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
            )

    try:
        print("[INFO] Chiedendo a ChatGPT...")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": user_content}],
            temperature=0,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERRORE] GPT fallito: {e}")
        return None

def esegui_lighthouse(url, output_dir):
    print("[INFO] Eseguendo Lighthouse...")
    try:
        subprocess.run([
            "lighthouse.cmd" if os.name == "nt" else "lighthouse", url,
            "--output=json",
            "--output=html",
            f"--output-path={output_dir}/report",
            "--quiet",
            "--chrome-flags=--headless"
        ], check=True)
        json_path = glob.glob(f"{output_dir}/*.report.json")[0]
        html_path = glob.glob(f"{output_dir}/*.report.html")[0]
        return json_path, html_path
    except Exception as e:
        print(f"[ERRORE] Lighthouse fallito: {e}")
        return None, None

def estrai_score_lighthouse(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            categorie = data.get("categories", {})
            scores = {
                "Performance": categorie.get("performance", {}).get("score", 0) * 100,
                "Accessibility": categorie.get("accessibility", {}).get("score", 0) * 100,
                "Best Practices": categorie.get("best-practices", {}).get("score", 0) * 100,
                "SEO": categorie.get("seo", {}).get("score", 0) * 100,
            }
            pwa_score = categorie.get("pwa", {}).get("score")
            scores["PWA"] = pwa_score * 100 if pwa_score is not None else None
            return scores
    except Exception as e:
        print(f"[ERRORE] Lettura JSON fallita: {e}")
        return {}

def salva_report(url, report_gpt, scores, json_path, html_path, screenshot_path, reports_dir):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file_md = os.path.join(reports_dir, f"report_accessibilita_{timestamp}.md")
    try:
        print(f"[INFO] Salvando report in: {reports_dir}")
        with open(nome_file_md, "w", encoding="utf-8") as f:
            f.write(f"# 🌐 Report di Accessibilità Web\n")
            f.write(f"**URL analizzato:** [{url}]({url})\n\n")
            f.write("## 📊 RISULTATI LIGHTHOUSE:\n")
            for k, v in scores.items():
                if v is None:
                    f.write(f"- **{k}**: N/A\n")
                else:
                    f.write(f"- **{k}**: {v:.0f}/100\n")
            json_fname = os.path.basename(json_path)
            html_fname = os.path.basename(html_path)
            f.write(f"\n🔗 **[JSON Lighthouse]({json_fname})**, **[HTML Lighthouse]({html_fname})**\n\n")
            if screenshot_path:
                f.write(f"![Screenshot della pagina]({os.path.basename(screenshot_path)})\n\n")
            f.write("## 🤖 ANALISI GPT:\n")
            f.write(report_gpt)
        print(f"[✅] Report .md salvato in: {nome_file_md}")
    except Exception as e:
        print(f"[ERRORE] Salvataggio fallito: {e}")

# === MAIN ===
def main():
    if len(sys.argv) != 2:
        print("Uso: python main.py https://esempio.com/profilo/s5513839")
        return

    url = sys.argv[1]
    match = re.search(r"s\w{7}", url)
    matricola = match.group(0) if match else "sconosciuto"
    reports_dir = os.path.join("reports", matricola)
    os.makedirs(reports_dir, exist_ok=True)

    html, css, js = estrai_html_css_js_da_url(url)
    if not html or not css:
        print("[ERRORE] Estrazione fallita, terminazione.")
        return

    screenshot_path = screenshot_full_cdp(url, os.path.join(reports_dir, "screenshot.png"))
    report_gpt = genera_report_chatgpt(html, css, js, url, screenshot_path)
    if not report_gpt:
        return

    json_path, html_path = esegui_lighthouse(url, reports_dir)
    if not json_path:
        return

    scores = estrai_score_lighthouse(json_path)
    salva_report(url, report_gpt, scores, json_path, html_path, screenshot_path, reports_dir)

if __name__ == "__main__":
    main()
