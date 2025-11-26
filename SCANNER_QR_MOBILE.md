# 📱 Scanner QR Code Mobile - Guida Completa

## Introduzione

Il nuovo sistema di scanner QR Code mobile permette ai cassieri di utilizzare il proprio smartphone come lettore QR Code per validare le prenotazioni. Questo sostituisce completamente la pistola scanner barcode.

## 🎯 Vantaggi

### Rispetto alla Pistola Scanner
- ✅ **Nessun hardware dedicato** - Usa smartphone già in possesso del cassiere
- ✅ **Scansione più veloce** - QR code leggibili da qualsiasi angolazione
- ✅ **Feedback visivo immediato** - Notifiche colorate su validità
- ✅ **Funziona offline** - Memorizza temporaneamente le scansioni
- ✅ **Torcia integrata** - Per ambienti poco illuminati
- ✅ **Inserimento manuale** - Backup in caso di problemi fotocamera

### Sicurezza
- 🔒 **Autenticazione richiesta** - Solo utenti loggati possono accedere
- 🔒 **Validazione server-side** - Ogni QR code verificato centralmente
- 🔒 **Protezione anti-replay** - Previene scansioni duplicate
- 🔒 **Controllo evento** - QR code validati solo per l'evento corrente

## 📋 Requisiti

### Smartphone Compatibili
- **iOS**: iPhone 6s o superiore (iOS 11+)
- **Android**: Android 5.0 (Lollipop) o superiore
- **Browser supportati**:
  - Safari (iOS)
  - Chrome (Android/iOS)
  - Firefox (Android)
  - Samsung Internet

### Permessi Necessari
- ✅ Accesso alla fotocamera
- ✅ Connessione internet (WiFi o dati mobili)
- ✅ Account utente con permessi botteghino

## 🚀 Come Usare lo Scanner

### 1. Accesso allo Scanner

#### Opzione A: Da Desktop/PC della Cassa
1. Accedi al sistema LTC BoxOffice
2. Vai alla pagina dell'evento corrente
3. Clicca sul pulsante **"📱 Scanner QR Mobile"**
4. Si aprirà una nuova scheda ottimizzata per mobile

#### Opzione B: Diretto da Smartphone
1. Fai login a LTC BoxOffice dal browser dello smartphone
2. Naviga all'evento corrente
3. Clicca su **"📱 Scanner QR Mobile"**

> **💡 Consiglio**: Salva il link nei preferiti per accesso rapido!

### 2. Concessione Permessi Fotocamera

Al primo utilizzo, il browser chiederà:
```
"LTC BoxOffice vorrebbe accedere alla fotocamera"
```

- Clicca **"Consenti"** o **"Allow"**
- Il permesso viene ricordato per i successivi accessi

### 3. Scansione QR Code

#### Metodo Standard - Scansione Fotocamera

1. **Inquadra il QR Code**
   - Posiziona lo smartphone sopra il QR code del cliente
   - Mantieni distanza 10-30 cm
   - Il QR code deve essere completamente visibile nel riquadro

2. **Scansione Automatica**
   - Quando il QR code viene rilevato, la scansione è **automatica**
   - Feedback immediato con vibrazione (se supportata)
   - Messaggio colorato in alto:
     - 🟢 **Verde** = Prenotazione valida
     - 🔴 **Rosso** = QR code non valido/già usato
     - 🟡 **Giallo** = Verifica in corso

3. **Dettagli Prenotazione**
   - Numero posti visualizzati
   - Nome cliente
   - Codice ordine
   - Ora scansione

4. **Automatico Redirect**
   - Dopo 1.5 secondi, reindirizza alla pagina di dettaglio ordine
   - Il cassiere può procedere con incasso e stampa biglietti

#### Metodo Alternativo - Inserimento Manuale

Se la fotocamera non funziona o c'è troppa luce:

1. Clicca **"⌨️ Inserimento Manuale"**
2. Digita il codice QR (formato: `00042_000123_000456`)
3. Clicca **"✓ Verifica Codice"**
4. Stessa validazione della scansione automatica

### 4. Funzioni Avanzate

#### 🔦 Torcia/Flash (se disponibile)

- Pulsante rotondo in basso a destra
- Tap per accendere/spegnere
- Utile in ambienti poco illuminati
- Solo su dispositivi supportati

#### 📊 Contatore Scansioni

- Mostra numero di prenotazioni scansionate nella sessione
- Si resetta chiudendo lo scanner

#### 🕐 Ultima Scansione

- Visualizza dettagli ultima scansione valida
- Utile per conferma visiva

## ⚡ Workflow Completo in Cassa

### Scenario Tipico

```
1. Cliente arriva in cassa
   ↓
2. Cliente mostra QR code (smartphone o stampato)
   ↓
3. Cassiere apre Scanner QR Mobile sul proprio smartphone
   ↓
4. Cassiere inquadra QR code del cliente
   ↓
5. ✓ Scansione automatica + vibrazione
   ↓
6. Messaggio verde: "✓ Prenotazione valida!"
   ↓
7. Visualizzati: posti, nome, totale
   ↓
8. Click automatico su dettaglio ordine
   ↓
9. Cassiere procede con incasso
   ↓
10. Stampa biglietti
   ↓
11. Cliente riceve biglietti e va in sala
```

### Durata Media
- ⏱️ Scansione QR: **< 1 secondo**
- ⏱️ Validazione server: **< 0.5 secondi**
- ⏱️ Totale per cliente: **< 2 secondi**

## 🔧 Risoluzione Problemi

### La Fotocamera non si Attiva

**Possibili Cause:**
- Permessi fotocamera negati
- Browser non supportato
- Fotocamera in uso da altra app

**Soluzioni:**
1. **Controlla permessi browser**
   - iOS Safari: Impostazioni → Safari → Fotocamera
   - Chrome Android: Impostazioni → Privacy → Fotocamera

2. **Ricarica la pagina**
   - Pull-down per ricaricare

3. **Usa inserimento manuale**
   - Fallback sempre disponibile

### QR Code Non Viene Letto

**Possibili Cause:**
- QR code danneggiato
- Troppa luce/riflessi
- QR code troppo piccolo
- Smartphone troppo vicino/lontano

**Soluzioni:**
1. **Regola distanza**: 15-25 cm ideale
2. **Cambia angolazione**: evita riflessi
3. **Usa torcia**: se troppo buio
4. **Inserimento manuale**: digita il codice

### Messaggio "QR code non valido"

**Significati:**
- ❌ **Prenotazione non trovata**: codice errato/inesistente
- ❌ **Evento sbagliato**: QR code di un altro spettacolo
- ❌ **Già utilizzata**: prenotazione già evasa

**Azioni:**
1. Verifica con il cliente l'evento
2. Controlla se ha più prenotazioni
3. Cerca manualmente nel sistema per nome/cognome

### Connessione Lenta

**Soluzioni:**
1. **Usa WiFi del teatro** invece di dati mobili
2. **Minimizza app in background**
3. **Riavvia browser** se necessario

### Scanner si Blocca/Lagga

**Soluzioni:**
1. **Chiudi altre schede browser**
2. **Chiudi app in background**
3. **Riavvia browser**
4. **Ultima risorsa**: riavvia smartphone

## 🔒 Sicurezza e Privacy

### Dati Trattati
- **Solo validazione**: nessun dato personale memorizzato sul dispositivo
- **Server-side**: tutte le verifiche sul server Django
- **HTTPS**: comunicazioni criptate
- **CSRF Protection**: protezione contro attacchi

### Best Practices
- ✅ Fai logout quando finisci il turno
- ✅ Non condividere le credenziali di accesso
- ✅ Usa solo su WiFi sicura (del teatro)
- ✅ Non screenshot di QR code clienti
- ✅ Segnala anomalie al responsabile

## 📱 Installazione Come App (PWA)

### iPhone/iPad (Safari)

1. Apri scanner mobile in Safari
2. Tap icona **Condividi** (quadrato con freccia)
3. Scorri e tap **"Aggiungi a Home"**
4. Rinomina: "Scanner QR - LTC"
5. Tap **"Aggiungi"**

✅ Icona comparirà sulla home screen
✅ Aprirà a schermo intero (niente barre browser)
✅ Esperienza app nativa

### Android (Chrome)

1. Apri scanner mobile in Chrome
2. Menu (⋮) → **"Aggiungi a schermata Home"**
3. Rinomina: "Scanner QR - LTC"
4. Tap **"Aggiungi"**

✅ Icona sulla home screen
✅ Funziona offline (cache)

## 📊 Statistiche e Monitoraggio

### Contatori Disponibili
- **Scansioni totali**: per sessione
- **Ultima scansione**: timestamp e dettagli
- **Tasso successo**: scansioni valide vs totali

### Log Server
Ogni scansione viene loggata con:
- Timestamp
- Utente cassiere
- Evento
- Codice QR
- Esito (valido/non valido)
- IP dispositivo

## 🆚 Confronto: Scanner Mobile vs Pistola Barcode

| Caratteristica | Pistola Barcode | Scanner QR Mobile |
|----------------|-----------------|-------------------|
| **Hardware** | Dedicato (~€200) | Smartphone esistente |
| **Setup** | Ghostscript + drivers | Solo browser |
| **Velocità** | ~2-3 secondi | < 1 secondo |
| **Angolazione** | Unidirezionale | Omnidirezionale |
| **Feedback** | Solo beep | Visivo + tattile + sonoro |
| **Portabilità** | Cablato/Bluetooth | Completamente mobile |
| **Manutenzione** | Batterie/cavi | Nessuna |
| **Backup** | Solo manuale | Scan + manuale |
| **Costo** | Hardware + software | €0 |

## 🔄 Migrazione dalla Pistola

### Fase di Transizione (Consigliata: 2-4 settimane)

**Settimana 1-2**: Dual Mode
- Mantieni pistola barcode funzionante
- Testa scanner mobile in parallelo
- Forma cassieri sull'uso

**Settimana 3-4**: Scanner Mobile Primario
- Scanner mobile come metodo principale
- Pistola come backup
- Monitora feedback cassieri

**Dopo 1 Mese**: Solo Scanner Mobile
- Dismetti pistola barcode
- Disinstalla Ghostscript (opzionale)
- Completo passaggio a QR code

### Training Cassieri

**Durata**: 10-15 minuti per cassiere

1. **Demo live** (5 min)
   - Mostra apertura scanner
   - Esegui scansione di test
   - Mostra gestione errori

2. **Pratica supervisionata** (5 min)
   - Cassiere scansiona 5-10 QR code
   - Correzioni in tempo reale

3. **Q&A** (5 min)
   - Risolvi dubbi
   - Distribuisci questa guida

## 📞 Supporto

### In Caso di Problemi Urgenti

1. **Fallback immediato**: Usa scanner desktop
2. **Inserimento manuale**: Sempre disponibile
3. **Ricerca per nome**: Sistema tradizionale

### Contatti Supporto Tecnico

- **Email**: [supporto tecnico]
- **Telefono**: [numero]
- **Orari**: Durante eventi

### Segnalazione Bug

Invia a supporto con:
- Modello smartphone
- Browser e versione
- Screenshot errore
- Passi per riprodurre

## 📈 Metriche di Successo

### Target KPI

- ✅ **Tempo medio scansione**: < 2 secondi
- ✅ **Tasso successo scansioni**: > 95%
- ✅ **Soddisfazione cassieri**: > 4/5
- ✅ **Riduzione code**: -30%

### Feedback Post-Evento

Dopo ogni evento, valuta:
- Numero scansioni totali
- Problemi riscontrati
- Tempo risparmiato vs pistola
- Suggerimenti miglioramento

## 🔮 Funzionalità Future

### In Roadmap

- [ ] **Modalità offline completa** - Cache prenotazioni
- [ ] **Statistiche live** - Dashboard in tempo reale
- [ ] **Multi-evento** - Switch rapido tra eventi
- [ ] **Scansione batch** - Gruppi di clienti
- [ ] **Integrazione NFC** - Biglietti contactless
- [ ] **Face ID/Touch ID** - Login biometrico

---

## 📝 Changelog

### v1.0.0 (2025-11-26)
- ✨ Release iniziale scanner QR mobile
- ✨ API validazione server-side
- ✨ Supporto torcia dispositivi
- ✨ Inserimento manuale fallback
- ✨ Feedback visivo/tattile/sonoro
- ✨ Contatori e statistiche sessione

---

## ✅ Checklist Pre-Evento

Prima di ogni spettacolo, verifica:

- [ ] WiFi teatro funzionante
- [ ] Smartphone cassieri carichi (>50%)
- [ ] Login cassieri attivi
- [ ] Scanner testato con QR code di prova
- [ ] Permessi fotocamera concessi
- [ ] Questa guida accessibile (stampata/digitale)
- [ ] Numero supporto tecnico a disposizione

---

**🎭 Buon lavoro con il nuovo scanner QR Code mobile!**

Per domande o suggerimenti, contatta il team di sviluppo.
