# 🌐 Report di Accessibilità Web
**URL analizzato:** [https://saw.dibris.unige.it/~s5513839/SAW_Project/index.php](https://saw.dibris.unige.it/~s5513839/SAW_Project/index.php)

## 📊 RISULTATI LIGHTHOUSE:
- **Performance**: 95/100
- **Accessibility**: 100/100
- **Best Practices**: 100/100
- **SEO**: 91/100
- **PWA**: N/A

🔗 **[JSON Lighthouse](report.report.json)**, **[HTML Lighthouse](report.report.html)**

## 🤖 ANALISI GPT:
### Analisi della pagina web secondo le linee guida WCAG 2.1:

#### Contenuto Testuale:
1. ✅ Il testo è ben strutturato e comprensibile.
2. ⚠️ Alcuni termini potrebbero non essere accessibili a tutti gli utenti, come "GMTK GameJam 2024" e "Dam".
3. 🛠 Suggerimento: Considerare l'aggiunta di spiegazioni o definizioni per i termini meno comuni.

#### Regole CSS:
1. ✅ Il CSS è ben organizzato e utilizzato per migliorare l'aspetto visivo della pagina.
2. ⚠️ Alcuni colori potrebbero non avere un contrasto sufficiente per utenti con disabilità visive.
3. 🛠 Suggerimento: Verificare e migliorare il contrasto dei colori per garantire una migliore leggibilità.

#### JavaScript:
1. ✅ Lo script JavaScript è utilizzato per gestire interazioni utente come apertura di popup e invio di donazioni.
2. ⚠️ Alcuni popup potrebbero non essere accessibili a utenti con disabilità motorie che non possono utilizzare il mouse.
3. 🛠 Suggerimento: Aggiungere la possibilità di chiudere i popup con la tastiera e migliorare l'accessibilità generale.

#### Errori Tecnici:
1. ❌ Mancano attributi "alt" per le immagini, come nel tag video.
2. ❌ Alcuni elementi non utilizzano tag semantici appropriati, come i pulsanti senza essere all'interno di un tag `<button>`.
3. ❌ Il focus non è gestito correttamente per alcune interazioni, come la chiusura dei popup.
4. ❌ Alcuni script potrebbero non essere accessibili a utenti con tecnologie assistive.

In generale, la pagina ha buoni contenuti testuali e utilizza CSS e JavaScript per migliorare l'esperienza utente. Tuttavia, ci sono alcune aree di miglioramento per garantire un'accessibilità web completa secondo le linee guida WCAG 2.1.