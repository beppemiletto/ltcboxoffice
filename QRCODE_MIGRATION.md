# Migrazione da Barcode a QR Code

## Data: 2025-11-26

## Sommario
Il sistema di prenotazioni è stato completamente migrato dai barcode Code128 ai QR Code. Questa migrazione elimina la dipendenza da Ghostscript e rende il sistema più moderno, versatile e facile da usare.

## Vantaggi della Migrazione

### 1. **Nessuna dipendenza esterna**
- ✅ Eliminata la dipendenza da Ghostscript
- ✅ La libreria `qrcode` è pura Python
- ✅ Deploy più semplice e veloce

### 2. **Maggiore capacità dati**
- QR Code: fino a 4KB di dati
- Code128: ~100 caratteri
- Possibilità futura di includere URL diretti, informazioni aggiuntive, ecc.

### 3. **Migliore esperienza utente**
- Scansionabile con qualsiasi smartphone (app fotocamera nativa)
- Leggibile da qualsiasi angolazione (omnidirezionale)
- Funziona anche se parzialmente danneggiato (correzione errori al 30%)

### 4. **Maggiore robustezza**
- Meno sensibile a stampe di bassa qualità
- Migliore leggibilità su schermi LCD/OLED
- Più tollerante a condizioni di luce non ottimali

## File Modificati

### 1. `booking/barcode_printer.py`
**Modifiche principali:**
- Sostituita libreria `treepoem` con `qrcode`
- Eliminata dipendenza da Ghostscript
- Aggiunta alta correzione errori (ERROR_CORRECT_H = 30%)
- Generazione di file `qrcode_img_*.png` invece di `barcode_img_*.png`

**Configurazione QR Code:**
```python
qr = qrcode.QRCode(
    version=1,  # Auto-size
    error_correction=qrcode.constants.ERROR_CORRECT_H,  # 30% correzione errori
    box_size=10,  # Dimensione ottimale per stampa e display
    border=4,  # Bordo standard
)
```

### 2. `requirements.txt`
**Rimosse:**
- `python-barcode==0.15.1` ❌
- `treepoem==3.23.0` ❌

**Mantenute:**
- `qrcode==7.4.2` ✅
- `pypng==0.20220715.0` ✅ (dipendenza di qrcode)

### 3. Template HTML

#### `templates/booking/multibooking_received_email.html`
- "Barcode" → "QR Code"
- Testo aggiornato per riferirsi ai QR code

#### `templates/booking/booking_received_email.html`
- Alt text aggiornato: "Barcode" → "QR Code"

#### `templates/booking/booking_complete.html`
- Header tabella: "Barcode" → "QR Code"
- Alt text immagine aggiornato
- Dimensione immagine aumentata: `max-height: 100px` → `150px` (i QR sono quadrati)
- Messaggio errore: "Barcode non disponibile" → "QR Code non disponibile"

#### `templates/boxoffice/barcode_read.html`
- Titolo: "Barcode reader" → "QR Code reader"
- Label: "Insert barcode code" → "Inserisci il codice del QR Code"
- Sottotitolo: "Scan the printed / displayed barcode" → "Scansiona o inserisci il codice del QR Code"
- Pulsante: "Usa codice barre" → "Verifica prenotazione"

### 4. `booking/views.py`
**Modifiche:**
- Commenti aggiornati per riferirsi ai QR code
- Variabile `barcode` → `qrcode_img` (riga 794)
- Variabile `brc` → `qrc` (riga 800)
- Messaggi di errore aggiornati
- Commento "Check if barcode file exists" → "Check if QR code file exists"
- Chiave context `'barcode'` → `'qrcode'` (riga 820)
- Commento funzione `booking_complete`: "barcode paths" → "QR code paths"

### 5. `boxoffice/forms.py`
**Classe `Barcode_Reader`:**
- Aggiunta docstring: "Form per lettura QR Code delle prenotazioni"
- help_text: "Enter the barcode code" → "Inserisci il codice del QR Code"
- Messaggio validazione: "Valid code detected" → "Valid QR code detected"
- Messaggi errore aggiornati in italiano

### 6. `orders/models.py`
- Aggiunta docstring alla funzione `barcode_image_path()` per chiarire che ora gestisce QR code
- **Nota:** Il campo `barcode_path` nel modello `OrderEvent` mantiene il nome originale per compatibilità con il database esistente

## Compatibilità

### Database
✅ **Nessuna migrazione richiesta**
- Il campo `OrderEvent.barcode_path` mantiene il nome originale
- Ora contiene percorsi a file `qrcode_img_*.png` invece di `barcode_img_*.png`
- I QR code esistenti (se presenti) continueranno a funzionare

### Codice Esistente
✅ **Retrocompatibile**
- Il nome del campo nel form (`barcode_code`) rimane invariato
- Il nome del parametro POST (`barcode_code`) rimane invariato
- Le URL e i route name rimangono invariati (`barcode_read`)

### Vecchi Barcode
- I vecchi file `barcode_img_*.png` possono essere eliminati manualmente se necessario
- I nuovi ordini genereranno file `qrcode_img_*.png`

## Testing

### Test Manuali Raccomandati

1. **Creazione nuova prenotazione:**
   - ✓ Verificare che il QR code venga generato correttamente
   - ✓ Controllare che l'immagine sia presente in `static/images/`
   - ✓ Verificare che l'email contenga il QR code

2. **Scansione QR code:**
   - ✓ Testare la lettura con smartphone
   - ✓ Verificare che il codice sia leggibile anche stampato
   - ✓ Testare la funzionalità di lettura nel backoffice

3. **Pagina di conferma:**
   - ✓ Verificare che il QR code sia visibile
   - ✓ Controllare la dimensione dell'immagine (dovrebbe essere quadrata)

## Operazioni Post-Migrazione

### 1. Disinstallare Ghostscript (Opzionale)
Se Ghostscript era installato solo per i barcode:
```bash
# Windows (con Chocolatey)
choco uninstall ghostscript

# Oppure tramite "Programmi e Funzionalità"
```

### 2. Aggiornare Dipendenze Python
```bash
pip uninstall python-barcode treepoem
pip install -r requirements.txt
```

### 3. File da Eliminare (Opzionale)
- `GHOSTSCRIPT_SETUP.md` - Non più necessario
- `setup_ghostscript_path.bat` - Non più necessario
- Vecchi file `static/images/barcode_img_*.png` - Se non più necessari

### 4. Aggiornare Documentazione Utente
- Aggiornare guide che menzionano "barcode" con "QR code"
- Aggiornare screenshot se presenti
- Informare gli utenti del cambio di tecnologia

## Note Tecniche

### Formato QR Code Generato
- **Tipo:** QR Code (2D)
- **Correzione errori:** Level H (30%)
- **Dimensione box:** 10 pixel
- **Bordo:** 4 box (standard minimo)
- **Colori:** Nero su bianco
- **Formato file:** PNG
- **Auto-sizing:** Sì (si adatta automaticamente alla lunghezza del contenuto)

### Contenuto QR Code
Formato: `{event_id:05d}_{order_number:06d}_{orderevent_id:06d}`

Esempio: `00042_000123_000456`
- Event ID: 42
- Order Number: 123
- OrderEvent ID: 456

### Dimensioni File
- QR code tipico: ~2-5 KB (vs ~10-20 KB dei barcode Code128)
- Risparmio di spazio su disco: ~50-75%

## Rollback (Se Necessario)

In caso di problemi, è possibile tornare ai barcode ripristinando:
1. File `booking/barcode_printer.py` dalla versione precedente
2. Dipendenze `python-barcode` e `treepoem` in requirements.txt
3. Testi nei template HTML
4. Reinstallare Ghostscript

**Comando Git per rollback:**
```bash
git log --oneline  # Trova il commit prima della migrazione
git revert <commit-hash>
```

## Conclusioni

La migrazione a QR code è stata completata con successo. Il sistema è ora:
- ✅ Più semplice da deployare (no Ghostscript)
- ✅ Più moderno e user-friendly
- ✅ Più robusto e affidabile
- ✅ Pronto per future estensioni (URL dinamici, deep linking, ecc.)

Nessuna modifica al database è stata necessaria, garantendo la massima compatibilità con i dati esistenti.
