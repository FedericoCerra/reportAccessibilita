
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import sys
import os
from datetime import datetime
import subprocess

# === CONFIG ===
API_KEY = ***REMOVED***"  # <-- Sostituisci con la tua API key!
MODEL = "gpt-3.5-turbo"
TOKEN_LIMIT = 12000

# === CREA IL CLIENT OPENAI ===
client = OpenAI(api_key=API_KEY)

# === FUNZIONE 1: Estrazione contenuto ===
def estrai_testo_da_url(url):
    try:
        print(f"[INFO] Scaricando contenuto da: {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        for elemento in soup(["script", "style", "noscript"]):
            elemento.extract()

        testo = soup.get_text(separator=' ', strip=True)
        return testo[:TOKEN_LIMIT]
    except Exception as e:
        print(f"[ERRORE] Errore durante il download della pagina: {e}")
        return None

# === FUNZIONE 2: Chiamata API OpenAI ===
def genera_report_accessibilita(testo_pagina):
    prompt = f"""
Sei un esperto di accessibilità web. Analizza il seguente contenuto testuale di una pagina web e crea un report dettagliato secondo le linee guida WCAG 2.1. 
Organizza il report nei seguenti punti:

1. Punti di forza dell’accessibilità
2. Problemi riscontrati (con esempi, se possibile)
3. Suggerimenti di miglioramento concreti
4. Eventuali mancanze tecniche (es. alt mancanti, struttura non semantica)

Contenuto della pagina:
\"\"\"
{testo_pagina}
\"\"\"
"""

    try:
        print("[INFO] Inviando contenuto a ChatGPT (v1)...")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERRORE] Errore nella generazione del report: {e}")
        return None

# === FUNZIONE 3: Salvataggio ===
def salva_report(report, url):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"report_accessibilita_{timestamp}.txt"
    try:
        with open(nome_file, "w", encoding="utf-8") as f:
            f.write(f"Report di accessibilità per: {url}\n\n")
            f.write(report)
        print(f"[✅] Report salvato in: {nome_file}")
    except Exception as e:
        print(f"[ERRORE] Impossibile salvare il file: {e}")

# === FUNZIONE 4: Esegui Lighthouse ===
def esegui_lighthouse(url):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_html = f"report_lighthouse_{timestamp}.html"

    print("[INFO] Eseguendo Lighthouse...")
    try:
        subprocess.run([
            "lighthouse.cmd", url,
            "--output", "html",
            "--output-path", file_html,
            "--quiet",
            "--chrome-flags=--headless"
        ], check=True)
        print(f"[✅] Report Lighthouse salvato in: {file_html}")
        return file_html
    except subprocess.CalledProcessError as e:
        print(f"[ERRORE] Lighthouse ha fallito: {e}")
        return None
    
# === MAIN ===
def main():
    if len(sys.argv) != 2:
        print("Uso: python report_accessibilita.py https://esempio.com")
        return

    url = sys.argv[1]
    contenuto = estrai_testo_da_url(url)
    if not contenuto:
        print("[ERRORE] Contenuto non valido o pagina non accessibile.")
        return

    report = genera_report_accessibilita(contenuto)
    lighthouse_file = esegui_lighthouse(url)

    if report:
        salva_report(report, url)
    else:
        print("[ERRORE] Impossibile generare il report.")

    if lighthouse_file:
        print(f"[INFO] Report Lighthouse disponibile: {lighthouse_file}")


# === AVVIO ===
if __name__ == "__main__":
    main()
