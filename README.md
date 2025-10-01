
# Web Accessibility Analyzer

Questo progetto permette di **analizzare automaticamente l’accessibilità di un sito web** secondo le linee guida **WCAG 2.1**, combinando:

- **[Lighthouse](https://github.com/GoogleChrome/lighthouse)** per audit automatici (Performance, Accessibility, SEO, Best Practices).  
- **OpenAI GPT** per analisi semantiche e approfondimenti sugli errori.  
- **Selenium + Chrome DevTools** per catturare screenshot full-page.  

I risultati vengono salvati in report individuali per ogni URL e successivamente aggregati in un **report comparativo** che evidenzia gli errori più comuni tra i diversi siti analizzati.

---

## Funzionalità principali
- Estrazione automatica di **HTML, CSS e JavaScript** da una pagina web.  
- Analisi WCAG 2.1 tramite **GPT** con evidenziazione dei problemi critici e suggerimenti.  
- Audit Lighthouse completo con punteggi per Performance, Accessibility, SEO e Best Practices.  
- **Screenshot full page** con Chrome DevTools.  
- Generazione report Markdown `.md` con:
  - Screenshot della pagina
  - Risultati Lighthouse
  - Analisi GPT  
- Report aggregato finale che evidenzia:
  - Errori più comuni
  - Quante pagine presentano ciascun problema
  - Tabella con ID fittizi per anonimizzare le matricole
  - Elenco sintetico delle priorità

---

## Requisiti
- **Python 3.9+**
- **Node.js** (necessario per Lighthouse CLI)
- **Google Chrome** installato sul sistema

---

## Installazione

### 1. Clona il repository
```bash
git clone https://github.com/<tuo-repo>/web-accessibility-analyzer.git
cd web-accessibility-analyzer
```
### 2. Crea e attiva un ambiente virtuale
```bash
python -m venv venv
```
# Linux / MacOS
```bash
source venv/bin/activate
```
# Windows
```bash
venv\Scripts\activate
```
### 3. Installa le dipendenze Python
```bash
pip install -r requirements.txt
```

### 4. Installa Lighthouse (globalmente via npm)
```bash
npm install -g lighthouse
```

### 5. Configura le variabili d’ambiente

Crea un file .env nella root del progetto e inserisci la tua API key di OpenAI:

```bash
OPENAI_API_KEY=la_tua_chiave_api
```
## Utilizzo
Analisi di un singolo sito
python main.py https://esempio.com


Questo genererà una cartella in reports/<matricola>/ contenente:

report_accessibilita_<timestamp>.md → report completo

screenshot.png → screenshot della pagina

*.report.json → report Lighthouse in JSON

*.report.html → report Lighthouse in HTML

Analisi aggregata di tutti i report
```bash
python aggrega_report.py
```

Questo creerà un file:

finalReport/report.md


con la sintesi degli errori comuni.



## Output atteso

Un report per ogni sito analizzato contenente:

Screenshot della pagina

Risultati Lighthouse con punteggi (Performance, Accessibility, Best Practices, SEO)

Analisi GPT con:

Panoramica generale

Errori critici con esempi

Punti di forza

Azioni prioritarie

E un report finale aggregato che mostra:

Errori più frequenti

Tabella errori × ID

Elenco delle problematiche più rilevanti da affrontare

🛠️ Dipendenze principali

requests

beautifulsoup4

selenium

webdriver-manager

python-dotenv

openai

Lighthouse
 (via Node.js)