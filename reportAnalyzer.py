import os
import glob
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"



def raccogli_report(base_dir="reports"):
    """Raccoglie un file .md per matricola dentro le sottocartelle"""
    reports = []
    cartelle = glob.glob(os.path.join(base_dir, "*"))  # tutte le sottocartelle
    
    for cartella in cartelle:
        md_files = glob.glob(os.path.join(cartella, "*.md"))
        if not md_files:
            print(f"[WARNING] Nessun report .md in {cartella}")
            continue
        
        report_path = md_files[0]  # prendo l'unico .md
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                contenuto = f.read()
                reports.append({
                    "matricola": os.path.basename(cartella),
                    "contenuto": contenuto
                })
        except Exception as e:
            print(f"[ERRORE] Non riesco a leggere {report_path}: {e}")
    
    return reports

def analizza_report_comuni(reports):
    """Invia tutti i report a GPT e chiede gli errori più comuni"""
    if not reports:
        print("[ERRORE] Nessun report trovato.")
        return None
    
    # Costruisco il testo con tutti i report
    testo = "\n\n---\n\n".join([
        f"Report matricola {r['matricola']}:\n{r['contenuto']}" for r in reports
    ])

    prompt = f"""
Sei un esperto di accessibilità web. Ti fornisco i report di più siti web (uno per matricola).
Analizza i contenuti e dimmi:

1. Quali sono gli errori più comuni tra i vari report.
2. Quante matricole presentano ciascun errore.
3. Se ci sono differenze interessanti (alcuni siti che non hanno un errore comune).
4. Un elenco sintetico dei problemi principali da affrontare in priorità.

Ecco i report:

{testo}
"""
    try:
        print("[INFO] Chiedendo a GPT di analizzare i report...")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERRORE] GPT fallito: {e}")
        return None

# === MAIN ===
def main():
    reports = raccogli_report("reports")
    risultato = analizza_report_comuni(reports)
    
    if risultato:
        print("\n ANALISI DEI REPORT \n")
        print(risultato)

if __name__ == "__main__":
    main()
