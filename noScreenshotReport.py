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


load_dotenv()
MODEL = "gpt-4o-mini"
TOKEN_LIMIT = 1000000
openai.api_key = os.getenv("OPENAI_API_KEY")



def estrai_html_css_js_da_url(url):
    try:
        print(f"[INFO] Scaricando contenuto da: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # HTML completo come stringa
        html = response.text[0:TOKEN_LIMIT]
        
        soup = BeautifulSoup(html, 'html.parser')

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
        return html, css, js
    except Exception as e:
        print(f"[ERRORE] estrai_html_css_js_da_url: {e}")
        return None, None, None



def genera_report_chatgpt(html, css, js, url):
    prompt = f"""
Sei un esperto di accessibilità web. Analizza il seguente sito secondo le WCAG 2.1.

URL: {url}

--- HTML ---
{html}

--- CSS ---
{css}

--- JavaScript ---
{js}

Obiettivi:
- Fornisci una panoramica generale sull'accessibilità della pagina.
- Evidenzia in modo chiaro e conciso gli **errori principali** (es. attributi alt mancanti, uso scorretto dei tag semantici, contrasto insufficiente, problemi di focus, script non accessibili, ecc.).
- Raggruppa le problematiche simili (non ripetere lo stesso tipo di errore più volte).
- Elenca i **3-5 problemi più critici** con **esempi di codice se presenti**.
- Indica eventuali **punti di forza** e **azioni prioritarie** per migliorare l'accessibilità.

Output richiesto:
1. **Sintesi generale** (livello di accessibilità percepito)
2. **Errori critici** (in elenco puntato, con esempi evidenziati)
3. **Punti di forza**
4. **Raccomandazioni prioritarie**

"""
    try:
        print("[INFO] Chiedendo a ChatGPT...")
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
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

#glob.glob per trovare i file generati
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

            return scores
    except Exception as e:
        print(f"[ERRORE] Lettura JSON fallita: {e}")
        return {}


def salva_report(url, report_gpt, scores, json_path, html_path, reports_dir):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = os.path.join(reports_dir, f"report_accessibilita_{timestamp}.md")
    try:
        print(f"[INFO] Salvando report in: {reports_dir}")
        with open(nome_file, "w", encoding="utf-8") as f:
            f.write(f"# Report di Accessibilità Web\n")
            f.write(f"**URL analizzato:** [{url}]({url})\n\n")
            f.write("## RISULTATI LIGHTHOUSE:\n")
            for key, value in scores.items():
                if value is None:
                    f.write(f"- **{key}**: N/A\n")
                else:
                    f.write(f"- **{key}**: {value:.0f}/100\n")

            json_fname = os.path.basename(json_path)
            html_fname = os.path.basename(html_path)
            f.write(f"\n **[JSON Lighthouse]({json_fname})**, **[HTML Lighthouse]({html_fname})**\n\n")
            f.write("## ANALISI GPT:\n")
            f.write(report_gpt)
        print(f"[✅] Report .md salvato in: {nome_file}")
    except Exception as e:
        print(f"[ERRORE] Salvataggio fallito: {e}")

# === MAIN ===
def main():
    if len(sys.argv) != 2:
        print("Uso: python main2.py https://saw.dibris.unige.it/~s5513839/")
        return

    url = sys.argv[1]

  
    match = re.search(r"s\w{7}", url)
    matricola = match.group(0) if match else "sconosciuto"
    reports_dir = os.path.join("reports", matricola)
    os.makedirs(reports_dir, exist_ok=True)

    html, css, js = estrai_html_css_js_da_url(url)
    if not html or not css or not js:
        print("[ERRORE] Estrazione fallita, terminazione.")
        return

    report_gpt = genera_report_chatgpt(html, css, js, url)
    if not report_gpt:
        return

    json_path, html_path = esegui_lighthouse(url, reports_dir)
    if not json_path:
        return

    scores = estrai_score_lighthouse(json_path)
    salva_report(url, report_gpt, scores, json_path, html_path, reports_dir)

if __name__ == "__main__":
    main()
