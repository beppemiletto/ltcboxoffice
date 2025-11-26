# 🔧 Installazione ngrok - Guida Completa

## ⚠️ Problema: Chocolatey Bloccato

Se ricevi errore tipo:
```
Another Chocolatey process is pending...
The running command will be allowed to complete...
```

## ✅ Soluzione Rapida: Fix Chocolatey

### Opzione 1: Script Automatico

```bash
# Esegui come Amministratore
fix_chocolatey.bat
```

Questo script:
1. Termina tutti i processi Chocolatey
2. Rimuove file di lock
3. Pulisce installazioni pending

Poi riprova:
```bash
choco install ngrok
```

### Opzione 2: Comandi Manuali

Apri **PowerShell come Amministratore** ed esegui:

```powershell
# Termina processi Chocolatey
Get-Process | Where-Object {$_.Name -like "*choco*"} | Stop-Process -Force

# Rimuovi file lock
Remove-Item "$env:ProgramData\chocolatey\.chocolatey\*.lock" -Force -ErrorAction SilentlyContinue

# Pulisci pending
Remove-Item "$env:ProgramData\chocolatey\lib-pending\" -Recurse -Force -ErrorAction SilentlyContinue

# Pulisci temp
Remove-Item "$env:TEMP\.chocolatey\" -Recurse -Force -ErrorAction SilentlyContinue
```

Poi:
```powershell
choco install ngrok -y
```

---

## 🎯 Soluzione Alternativa: Installazione Manuale ngrok

**Se Chocolatey continua a dare problemi**, installa ngrok manualmente (2 minuti):

### Passo 1: Download

1. Vai a: **https://ngrok.com/download**
2. Clicca **"Download for Windows (64-bit)"**
3. Scarica il file `ngrok-v3-stable-windows-amd64.zip`

### Passo 2: Estrazione

1. Apri la cartella `Downloads`
2. Fai click destro su `ngrok-v3-stable-windows-amd64.zip`
3. Seleziona **"Estrai tutto..."**
4. Estrai in `C:\ngrok\` (crea la cartella se non esiste)

### Passo 3: Aggiungi al PATH

**Opzione A - PowerShell (Consigliato):**

Apri **PowerShell come Amministratore**:

```powershell
# Aggiungi ngrok al PATH
$env:Path += ";C:\ngrok"

# Rendi permanente
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\ngrok", [EnvironmentVariableTarget]::Machine)
```

**Opzione B - GUI:**

1. Cerca "Variabili d'ambiente" nel menu Start
2. Click "Modifica variabili d'ambiente di sistema"
3. Click "Variabili d'ambiente..."
4. Nella sezione "Variabili di sistema", seleziona **Path**
5. Click "Modifica..."
6. Click "Nuovo"
7. Aggiungi: `C:\ngrok`
8. Click "OK" su tutte le finestre

### Passo 4: Verifica Installazione

Apri **nuovo** terminale (importante: deve essere nuovo) e digita:

```bash
ngrok version
```

Output atteso:
```
ngrok version 3.x.x
```

✅ **Installazione completata!**

---

## 🚀 Configurazione ngrok (Opzionale ma Consigliato)

### Registrazione Account Gratuito

1. Vai a: **https://dashboard.ngrok.com/signup**
2. Registrati (gratis)
3. Copia il tuo **authtoken** dalla dashboard

### Aggiungi Authtoken

```bash
ngrok config add-authtoken TUO_AUTHTOKEN_QUI
```

**Vantaggi con authtoken:**
- Sessioni più lunghe (no timeout 2 ore)
- URL personalizzabili (piano a pagamento)
- Più tunnel simultanei
- Statistiche dettagliate

---

## 🎯 Uso Rapido

### Avvia Tunnel HTTPS

```bash
# Assicurati che Django sia attivo su porta 8000
python manage.py runserver 0.0.0.0:8000

# In un altro terminale:
ngrok http 8000
```

**Output:**
```
ngrok

Session Status                online
Account                       your@email.com
Version                       3.x.x
Region                        United States (us)
Latency                       50ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok.io -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

### Copia l'URL HTTPS

Nel caso sopra: `https://abc123.ngrok.io`

Usalo per accedere allo scanner da smartphone!

---

## 🔍 Dashboard ngrok

Apri in browser:
```
http://127.0.0.1:4040
```

**Puoi vedere:**
- Tutte le richieste HTTP in tempo reale
- Request/Response completi
- Tempo di risposta
- Headers
- Body JSON

**Utilissimo per debug!**

---

## 💡 Tips ngrok

### URL Statico (Piano Gratuito - Limitato)

L'URL cambia ad ogni riavvio nella versione gratuita.

**Workaround:**
1. Annota l'URL ogni volta
2. Aggiornalo in `settings.py`
3. Riavvia Django

**Oppure:**
Usa `ngrok http 8000 --domain=your-domain.ngrok-free.app` (piano a pagamento $8/mese)

### Terminare ngrok

Premi **Ctrl+C** nel terminale dove hai avviato ngrok.

### Riavviare con Stesso URL

Impossibile con piano gratuito. Ogni restart = nuovo URL.

Piano a pagamento: URL fisso sempre disponibile.

---

## 🆚 Alternative a ngrok (Se Proprio Non Funziona)

### 1. localtunnel (Gratis, URL statico)

```bash
# Installa
npm install -g localtunnel

# Avvia
lt --port 8000 --subdomain mioscannerqr

# Output
# https://mioscannerqr.loca.lt
```

**Pro:** URL statico se disponibile
**Contro:** A volte mostra pagina intermedia "Click Continue"

### 2. serveo (Gratis, SSH-based)

```bash
ssh -R 80:localhost:8000 serveo.net
```

**Pro:** Niente installazione
**Contro:** URL casuale

### 3. Cloudflare Tunnel (Gratis, Production-ready)

```bash
# Installa cloudflared
# https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

cloudflared tunnel --url http://localhost:8000
```

**Pro:** Affidabile, veloce, gratis
**Contro:** Setup più complesso

---

## 🔧 Troubleshooting

### "ngrok: command not found"

**Causa:** PATH non configurato correttamente

**Soluzione:**
1. Verifica percorso installazione: `where ngrok` (PowerShell)
2. Se non trova nulla, ri-aggiungi al PATH (vedi sopra)
3. **Chiudi e riapri** il terminale

### "ERR_NGROK_108"

**Causa:** Porta già in uso

**Soluzione:**
```bash
# Verifica quale processo usa porta 8000
netstat -ano | findstr :8000

# Termina processo (sostituisci PID)
taskkill /PID <PID> /F
```

### ngrok si Chiude Subito

**Causa:** Authtoken non configurato (versione recente richiede account)

**Soluzione:**
1. Registrati su ngrok.com
2. Aggiungi authtoken: `ngrok config add-authtoken TUO_TOKEN`

---

## ✅ Checklist Completa

- [ ] ngrok installato (manuale o Chocolatey)
- [ ] `ngrok version` funziona
- [ ] Account ngrok creato (opzionale ma consigliato)
- [ ] Authtoken configurato
- [ ] Django attivo su porta 8000
- [ ] `ngrok http 8000` avviato
- [ ] URL copiato (es. `https://abc123.ngrok.io`)
- [ ] URL aggiunto a `ALLOWED_HOSTS` in settings.py
- [ ] URL aggiunto a `CSRF_TRUSTED_ORIGINS`
- [ ] Django riavviato
- [ ] Test su smartphone: apri `https://abc123.ngrok.io/boxoffice/qr_scanner/1/`

---

## 🚀 Quick Start Final

```bash
# 1. Fix Chocolatey (se necessario)
fix_chocolatey.bat

# 2. Installa ngrok
choco install ngrok
# OPPURE download manuale + aggiungi al PATH

# 3. Configura authtoken (opzionale)
ngrok config add-authtoken <TUO_TOKEN>

# 4. Avvia Django
python manage.py runserver 0.0.0.0:8000

# 5. Avvia ngrok (altro terminale)
ngrok http 8000

# 6. Copia URL e aggiorna settings.py
# ALLOWED_HOSTS = [..., 'abc123.ngrok.io']
# CSRF_TRUSTED_ORIGINS = [..., 'https://abc123.ngrok.io']

# 7. Riavvia Django

# 8. Test su cellulare!
```

---

**Buon debug! 🎉**

Per ulteriore aiuto, vedi: `DEBUG_QR_SCANNER.md`
