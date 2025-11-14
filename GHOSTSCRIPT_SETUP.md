# Ghostscript Setup for Barcode Generation

## Problema

Il sistema di prenotazione genera codici a barre per gli ordini utilizzando la libreria `treepoem`, che richiede **Ghostscript** per funzionare.

Senza Ghostscript installato, vedrai questo errore:
```
treepoem.TreepoemError: Cannot determine path to ghostscript, is it installed?
```

## Soluzione: Installare Ghostscript

### Opzione 1: Chocolatey (Consigliato per Windows)

**Apri PowerShell come Amministratore** e esegui:

```powershell
choco install ghostscript -y
```

### Opzione 2: Download Manuale

1. Vai a https://www.ghostscript.com/releases/gsdnld.html
2. Scarica **Ghostscript AGPL Release** per Windows (64-bit o 32-bit)
3. Installa l'eseguibile scaricato
4. Durante l'installazione, assicurati che venga aggiunto al PATH di sistema

### Opzione 3: winget (Windows 11/10)

```powershell
winget install --id Artifex.Ghostscript
```

## Verifica Installazione

Dopo l'installazione, verifica che Ghostscript sia nel PATH:

```powershell
# Per 64-bit
where.exe gswin64c

# Per 32-bit
where.exe gswin32c

# Verifica versione
gswin64c --version
```

Dovresti vedere un output simile a:
```
C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe
```

## Configurazione PATH (se necessario)

Se Ghostscript è installato ma non viene trovato, aggiungi al PATH:

### Metodo Automatico
```cmd
setup_ghostscript_path.bat
```

### Metodo Manuale PowerShell
```powershell
# Aggiungi al PATH della sessione corrente
$env:Path += ";C:\Program Files\gs\gs10.06.0\bin"

# Aggiungi permanentemente al PATH utente
$gsPath = "C:\Program Files\gs\gs10.06.0\bin"
[Environment]::SetEnvironmentVariable("Path", "$env:Path;$gsPath", "User")
```

Dopo aver modificato il PATH:
1. Chiudi tutti i terminali
2. Chiudi VS Code
3. Riapri VS Code
4. Riavvia Django: `python manage.py runserver`

## Riavvia Django

Dopo aver installato Ghostscript:

1. Chiudi il server Django (CTRL+C)
2. Riavvia il server: `python manage.py runserver`
3. Riprova la prenotazione

## Comportamento Temporaneo Senza Ghostscript

Se Ghostscript non è installato, il sistema:
- ✅ Completa comunque la prenotazione (non crasha)
- ⚠️ Crea un placeholder per il codice a barre
- 📝 Logga un warning nei log
- 📧 L'email viene inviata ma senza immagine del codice a barre

**I codici a barre potranno essere generati successivamente** una volta installato Ghostscript.

## Troubleshooting

### "Accesso negato" durante installazione Chocolatey

Apri PowerShell **come Amministratore**:
1. Click destro su PowerShell
2. Seleziona "Esegui come amministratore"
3. Riprova il comando di installazione

### Ghostscript installato ma non trovato

Aggiungi manualmente al PATH:
1. Cerca dove è installato: `C:\Program Files\gs\gs10.XX.X\bin\`
2. Apri "Variabili d'ambiente" dal Pannello di Controllo
3. Aggiungi il path bin di Ghostscript alla variabile PATH
4. Riavvia PowerShell/terminale

### Verifica Python trova Ghostscript

```python
python -c "import treepoem; treepoem.generate_barcode('code128', 'TEST').save('test.png')"
```

Se funziona, crea un file `test.png` con il codice a barre.

## Alternative (Non Raccomandate)

Se non puoi installare Ghostscript per motivi di sicurezza/permessi:

1. **Usa un altro sistema per i barcode**: Modifica `barcode_printer.py` per usare `python-barcode` invece di `treepoem`
2. **Genera barcode via API esterna**: Usa servizi come barcode.tec-it.com
3. **Disabilita barcode**: Rimuovi la funzionalità (non consigliato)

## Links Utili

- Ghostscript Official: https://www.ghostscript.com/
- Treepoem Documentation: https://github.com/adamchainz/treepoem
- Chocolatey: https://chocolatey.org/

---

**Ultimo aggiornamento**: 2025-11-14
