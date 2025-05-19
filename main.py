import subprocess
import requests
from bs4 import BeautifulSoup
import openai
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import sys
import glob
import re

# === CONFIG ===
load_dotenv()
MODEL = "gpt-3.5-turbo"
TOKEN_LIMIT = 12000
openai.api_key = os.getenv("OPENAI_API_KEY")

# === FUNZIONI ===

def estrai_testo_css_js_da_url(url):
    try:
        print(f"[INFO] Scaricando contenuto da: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Rimuovo <noscript>
        for tag in soup(["noscript"]):
            tag.extract()

        # Estrazione testo
        testo = soup.get_text(separator=' ', strip=True)[:TOKEN_LIMIT]

        # Estrazione CSS
        css = ''
        for style in soup.find_all("style"):
            if style.string:
                css += style.string + "\n"
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if href:
                full = requests.compat.urljoin(url, href)
                try:
                    r2 = requests.get(full, timeout=10)
                    css += f"\n/* from {full} */\n" + r2.text + "\n"
                except Exception as e:
                    print(f"[WARNING] Impossibile scaricare CSS {full}: {e}")
        css = css[:TOKEN_LIMIT]

        # Estrazione JS
        js = ''
        for script in soup.find_all("script"):
            if script.string and not script.get("src"):
                js += script.string + "\n"
        for script in soup.find_all("script", src=True):
            src = script.get("src")
            full = requests.compat.urljoin(url, src)
            try:
                r3 = requests.get(full, timeout=10)
                js += f"\n/* from {full} */\n" + r3.text + "\n"
            except Exception as e:
                print(f"[WARNING] Impossibile scaricare JS {full}: {e}")
        js = js[:TOKEN_LIMIT]

        return testo, css, js
    except Exception as e:
        print(f"[ERRORE] estrai_testo_css_js_da_url: {e}")
        return None, None, None


def genera_report_chatgpt(testo, css, js, url):
    prompt = f"""
Sei un esperto di accessibilità web. Analizza il contenuto testuale, le regole CSS e il JavaScript della seguente pagina secondo le linee guida WCAG 2.1.

URL: {url}

--- Testo ---
{testo}

--- CSS ---
{css}

--- JavaScript ---
{js}

Per ogni sezione, genera:
1. ✅ Punti di forza
2. ⚠️ Problemi riscontrati (con esempi)
3. 🛠 Suggerimenti di miglioramento
4. ❌ Errori tecnici (es. alt mancanti, tag semantici, contrasto, focus, script non accessibili)
"""
    try:
        print("[INFO] Chiedendo a ChatGPT...")
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
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
        # Trova i file generati
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


def salva_report(url, report_gpt, scores, json_path, html_path, reports_dir):
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
            # Link locali ai report Lighthouse
            json_fname = os.path.basename(json_path)
            html_fname = os.path.basename(html_path)
            f.write(f"\n🔗 **[JSON Lighthouse]({json_fname})**, **[HTML Lighthouse]({html_fname})**\n\n")
            f.write("## 🤖 ANALISI GPT:\n")
            f.write(report_gpt)
        print(f"[✅] Report .md salvato in: {nome_file_md}")
    except Exception as e:
        print(f"[ERRORE] Salvataggio fallito: {e}")

# === MAIN ===
def main():
    if len(sys.argv) != 2:
        print("Uso: python main2.py https://esempio.com/profilo/s5513839")
        return

    url = sys.argv[1]
    # Determina matricola e cartella
    match = re.search(r"s\w{7}", url)
    matricola = match.group(0) if match else "sconosciuto"
    reports_dir = os.path.join("reports", matricola)
    os.makedirs(reports_dir, exist_ok=True)

    testo, css, js = estrai_testo_css_js_da_url(url)
    if not testo:
        return

    report_gpt = genera_report_chatgpt(testo, css, js, url)
    if not report_gpt:
        return

    # Esegui Lighthouse direttamente nella cartella della matricola
    json_path, html_path = esegui_lighthouse(url, reports_dir)
    if not json_path:
        return

    scores = estrai_score_lighthouse(json_path)
    salva_report(url, report_gpt, scores, json_path, html_path, reports_dir)

if __name__ == "__main__":
    main()
