import subprocess
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import json
from datetime import datetime
import os
import sys
import glob

# === CONFIG ===
API_KEY = "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"  # <-- Sostituisci con la tua API key!
MODEL = "gpt-3.5-turbo"
TOKEN_LIMIT = 12000

client = OpenAI(api_key=API_KEY)

# === FUNZIONI ===

def estrai_testo_da_url(url):
    try:
        print(f"[INFO] Scaricando contenuto da: {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        return soup.get_text(separator=' ', strip=True)[:TOKEN_LIMIT]
    except Exception as e:
        print(f"[ERRORE] Impossibile estrarre testo: {e}")
        return None

def genera_report_chatgpt(testo, url):
    prompt = f"""
Sei un esperto di accessibilità web. Analizza il contenuto testuale della seguente pagina secondo le linee guida WCAG 2.1. 

Genera un report con questi punti:
1. ✅ Punti di forza
2. ⚠️ Problemi riscontrati (con esempi)
3. 🛠 Suggerimenti di miglioramento
4. ❌ Errori tecnici (alt mancanti, tag semantici ecc.)

URL: {url}

Contenuto della pagina:
\"\"\"
{testo}
\"\"\"
"""
    try:
        print("[INFO] Chiedendo a GPT-3.5-turbo...")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERRORE] GPT-4o fallito: {e}")
        return None


def esegui_lighthouse(url):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"lh_{timestamp}"

    os.makedirs(output_dir, exist_ok=True)

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

        # Trova i file appena creati
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
            categorie = data["categories"]
            return {
                "Performance": categorie["performance"]["score"] * 100,
                "Accessibility": categorie["accessibility"]["score"] * 100,
                "Best Practices": categorie["best-practices"]["score"] * 100,
                "SEO": categorie["seo"]["score"] * 100,
                "PWA": categorie["pwa"]["score"] * 100
            }
    except Exception as e:
        print(f"[ERRORE] Lettura JSON fallita: {e}")
        return {}

def salva_report(url, report_gpt, scores, lighthouse_html):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"report_accessibilita_{timestamp}.txt"
    try:
        with open(nome_file, "w", encoding="utf-8") as f:
            f.write(f"🌐 Report di Accessibilità Web\n")
            f.write(f"URL analizzato: {url}\n\n")

            f.write("📊 RISULTATI LIGHTHOUSE:\n")
            for k, v in scores.items():
                f.write(f" - {k}: {v:.0f}/100\n")
            f.write(f"\n🔗 Report visivo completo: {lighthouse_html}\n\n")

            f.write("🤖 ANALISI GPT-4o:\n")
            f.write(report_gpt)

        print(f"[✅] Report salvato in: {nome_file}")
    except Exception as e:
        print(f"[ERRORE] Salvataggio fallito: {e}")

# === MAIN ===
def main():
    if len(sys.argv) != 2:
        print("Uso: python report_accessibilita.py https://esempio.com")
        return

    url = sys.argv[1]

    testo = estrai_testo_da_url(url)
    if not testo:
        return

    report_gpt = genera_report_chatgpt(testo, url)
    if not report_gpt:
        return

    json_path, html_path = esegui_lighthouse(url)
    if not json_path:
        return

    scores = estrai_score_lighthouse(json_path)
    salva_report(url, report_gpt, scores, html_path)

if __name__ == "__main__":
    main()
