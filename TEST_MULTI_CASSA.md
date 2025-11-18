# Test Multi-Cassa - Scenario di Verifica

## Prerequisiti
- Server Django in esecuzione: `python manage.py runserver`
- Due browser diversi (o due finestre incognito dello stesso browser)
- Account utente con permessi boxoffice
- Evento attivo con posti disponibili

## Scenario 1: Isolamento Sessioni - Carrelli Separati

### Obiettivo
Verificare che due cassieri possano lavorare simultaneamente con carrelli completamente isolati.

### Passi:
1. **Browser A** (Chrome Incognito #1)
   - Aprire `http://localhost:8000/boxoffice/event_list/`
   - Login come utente boxoffice (es: `ltcboxoffice`)
   - Selezionare un evento
   - Aggiungere posti: **C05, C06, C07**
   - Verificare che il carrello mostri 3 posti

2. **Browser B** (Firefox/Chrome Incognito #2)
   - Aprire `http://localhost:8000/boxoffice/event_list/`
   - Login con lo **stesso utente** (ltcboxoffice)
   - Selezionare lo **stesso evento**
   - Aggiungere posti: **D05, D06, D07**
   - Verificare che il carrello mostri solo 3 posti (D)

3. **Verifica Browser A**
   - Tornare su Browser A
   - Ricaricare la pagina carrello
   - **✅ ATTESO**: Carrello mostra ancora C05, C06, C07 (non D05-D07)

4. **Verifica Browser B**
   - **✅ ATTESO**: Carrello mostra ancora D05, D06, D07 (non C05-C07)

### Risultato Atteso
I due carrelli sono completamente separati. Ogni browser ha il suo `session_id` UUID e vede solo i propri posti.

---

## Scenario 2: Lock Atomico - Race Condition

### Obiettivo
Verificare che il lock transazionale previene il double-booking dello stesso posto fisico.

### Setup:
Preparare due finestre affiancate per eseguire azioni simultanee.

### Passi:
1. **Browser A e B** - Entrambi:
   - Login su boxoffice
   - Aprire lo stesso evento
   - Visualizzare la mappa posti

2. **Simultaneamente** (click quasi contemporanei):
   - **Browser A**: Cliccare sul posto **E08**
   - **Browser B**: Cliccare sullo **stesso posto E08** (entro 1 secondo)

3. **Verificare comportamento**:
   - **Browser A**: 
     - ✅ Posto E08 aggiunto al carrello
     - Posto marcato come "in carrello" (arancione/giallo)
   
   - **Browser B**: 
     - ⚠️ Messaggio di warning: *"Il posto E08 è già stato venduto da un altro operatore."*
     - Posto NON aggiunto al carrello
     - Posto visibile come occupato

4. **Verifica JSON**:
   - Controllare `hall_jsons/evento_XX.json`
   - Il posto E08 deve avere `"status": 4` (in carrello)
   - **Una sola istanza** di status 4 per E08

### Risultato Atteso
Solo un cassiere riesce ad aggiungere il posto. L'altro riceve un warning e deve scegliere un posto diverso.

---

## Scenario 3: Vendita Completa Concorrente

### Obiettivo
Verificare che due cassieri possano completare vendite separate senza interferenze.

### Passi:
1. **Browser A**:
   - Carrello: C05, C06, C07
   - Procedere al pagamento
   - Selezionare metodo: Contanti
   - **Stampare** biglietti
   - Verifica: 3 biglietti stampati per C05-C07

2. **Browser B** (mentre A sta stampando):
   - Carrello: D05, D06, D07
   - Procedere al pagamento
   - Selezionare metodo: Carta
   - **Stampare** biglietti
   - Verifica: 3 biglietti stampati per D05-D07

3. **Verifica Database**:
   - Controllare `SellingSeats`: devono esistere 6 record con session_id diversi
   - Controllare `Payment`: 2 payment record (uno Contanti, uno Carta)
   - Controllare `OrderEvent`: posti correttamente assegnati

4. **Verifica JSON**:
   - C05, C06, C07: `"status": 3` (venduti)
   - D05, D06, D07: `"status": 3` (venduti)

### Risultato Atteso
Entrambe le vendite completate con successo, dati separati, nessun conflitto.

---

## Scenario 4: Abbandono Carrello

### Obiettivo
Verificare che i posti "bloccati" in un carrello tornino disponibili dopo timeout/logout.

### Passi:
1. **Browser A**:
   - Aggiungere posti F05, F06 al carrello
   - **NON completare la vendita**
   - Chiudere il browser (non logout)

2. **Browser B**:
   - Aprire mappa posti
   - Verificare status F05, F06
   - **ATTUALE**: Rimarranno status 4 fino a cleanup manuale
   - **FUTURO**: Implementare timeout automatico

3. **Cleanup Manuale** (per ora):
   - Admin Django: `/admin/boxoffice/sellingseats/`
   - Filtrare per evento
   - Eliminare SellingSeats non finalizzati (senza OrderEvent)

### Risultato Atteso (Attuale)
I posti rimangono "bloccati" status 4. Cleanup manuale necessario.

**TODO Futuro**: Implementare:
- Timestamp su SellingSeats
- Task periodico Celery per liberare posti dopo 15 minuti
- Bottone admin "Libera posti abbandonati"

---

## Scenario 5: Stress Test - 3+ Cassieri

### Obiettivo
Verificare stabilità con multiple sessioni concorrenti.

### Setup:
3 browser (Chrome Incognito, Firefox, Edge)

### Passi:
1. **Tutti i browser**:
   - Login boxoffice
   - Stesso evento
   
2. **Operazioni simultanee**:
   - Browser A: Aggiunge fila C (10 posti)
   - Browser B: Aggiunge fila D (10 posti)
   - Browser C: Aggiunge fila E (10 posti)

3. **Verifica**:
   - Ogni browser ha 10 posti nel proprio carrello
   - Nessun conflitto
   - JSON corretto (30 posti status 4)

4. **Completare vendite**:
   - Browser A: Stampa e chiude (fila C → status 3)
   - Browser B: Stampa e chiude (fila D → status 3)
   - Browser C: Stampa e chiude (fila E → status 3)

### Risultato Atteso
30 posti venduti, 3 transazioni separate, zero errori.

---

## Comandi Debug Utili

### Controllare SellingSeats in memoria
```python
from boxoffice.models import SellingSeats
from store.models import Event

event = Event.objects.get(id=XX)  # ID evento
seats = SellingSeats.objects.filter(event=event)

for s in seats:
    print(f"{s.seat} - Session: {s.session_id[:8]}... - Price: {s.price}")
```

### Pulire carrelli abbandonati
```python
# SellingSeats senza OrderEvent (non finalizzati)
abandoned = SellingSeats.objects.filter(orderevent__isnull=True)
print(f"Found {abandoned.count()} abandoned seats")
abandoned.delete()
```

### Verificare session_id attivi
```python
from django.contrib.sessions.models import Session
from datetime import datetime

active_sessions = Session.objects.filter(expire_date__gte=datetime.now())
print(f"Active sessions: {active_sessions.count()}")
```

---

## Checklist Test

- [ ] Scenario 1: Carrelli isolati ✓
- [ ] Scenario 2: Lock atomico previene double-booking ✓
- [ ] Scenario 3: Vendite concorrenti completate ✓
- [ ] Scenario 4: Gestione abbandono carrello
- [ ] Scenario 5: Stress test 3+ cassieri ✓
- [ ] Verifica logs errori (dovrebbero essere vuoti)
- [ ] Verifica integrità database dopo test
- [ ] Verifica JSON hall status coerente

---

## Metriche Successo

✅ **Sistema Pronto per Produzione SE:**
1. Tutti i carrelli isolati correttamente
2. Zero double-booking su stesso posto
3. Lock transazionale funziona (warning mostrato)
4. Vendite parallele completate senza errori
5. Database coerente dopo stress test

⚠️ **Richiede Attenzione SE:**
- Timeout session causano problemi
- Messaggi warning non mostrati
- Posti "fantasma" nel JSON
- Errori database transaction

❌ **NON Pronto SE:**
- Double-booking possibile
- Carrelli si mescolano tra sessioni
- Crash durante vendite concorrenti

---

## Note Implementazione

**Lock Implementato:**
- `transaction.atomic()` su lettura/scrittura JSON
- Check status posto prima di vendita
- Rollback automatico su errore

**Protezioni Attive:**
- Session ID UUID univoco
- Filtri session_id su tutte le query
- Message framework Django per feedback utente

**Limitazioni Attuali:**
- Carrelli abbandonati richiedono cleanup manuale
- Lock è a livello applicazione (non database row-level)
- File JSON può diventare bottleneck con traffico alto

**Miglioramenti Futuri:**
- Task Celery per timeout carrelli
- Redis cache per JSON
- WebSocket per aggiornamenti real-time posti
- Audit log delle operazioni cassiere
