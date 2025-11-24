# 🎯 Prossimi Passi Consigliati

## ✅ Implementazione Corridoi Dinamici - COMPLETATA

L'implementazione core dei corridoi dinamici è **completa e testata**. Tutti i test passano per entrambi i venue (Teatro Cambiano e Salone Italia).

---

## 🚀 Raccomandazioni Immediate

### 1. Test Manuale in Browser (Alta Priorità)

Prima di deployare in produzione, effettuare test manuali:

**Passi**:
1. Avviare server Django:
   ```bash
   . venv/Scripts/activate
   python manage.py runserver
   ```

2. Accedere all'admin: `http://localhost:8000/admin`

3. Testare Teatro Cambiano:
   - Verificare venue ha `teatro-cambiano-v2-with-aisles.json` caricato
   - Creare evento di test per Teatro Cambiano
   - Visualizzare mappa sala evento
   - Verificare:
     - ✅ Corridoio verticale (2 colonne) dopo posto 10
     - ✅ Corridoio orizzontale (1 riga) dopo fila H
     - ✅ Descrizioni visibili

4. Testare Salone Italia:
   - Caricare `salone-italia-poirino.json` in venue Salone Italia
   - Creare evento di test per Salone Italia
   - Visualizzare mappa sala evento
   - Verificare:
     - ✅ NESSUN corridoio verticale (posti continui 1-20)
     - ✅ Corridoio orizzontale (2 righe) dopo fila F
     - ✅ Layout diverso da Cambiano

5. Testare Backward Compatibility:
   - Verificare eventi esistenti (creati prima dell'update)
   - Dovrebbero funzionare senza errori
   - Potrebbe non avere corridoi (formato v1.0)

**Cosa Cercare**:
- ❌ Errori console JavaScript
- ❌ Errori template Django
- ❌ Layout rotto
- ✅ Corridoi renderizzati correttamente
- ✅ Posti cliccabili
- ✅ Selezione funzionante

---

## 📋 Attività Consigliate (In Ordine di Priorità)

### Priorità 1: Deploy e Monitoring (IMMEDIATO)

1. **Backup Database**
   ```bash
   python manage.py dumpdata > backup_before_aisles.json
   ```

2. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: Implementa corridoi dinamici configurabili per venue

   - Rimuove hardcoded corridor positions da template
   - Aggiunge supporto aisles in formato config v2.0
   - Crea template tags per rendering dinamico corridoi
   - Supporta Teatro Cambiano (corridoio centrale) e Salone Italia (no corridoio)
   - Backward compatible con configurazioni v1.0
   - Test suite completa (100% passed)"
   ```

3. **Deploy Staging** (se disponibile)
   - Testare in ambiente staging prima di produzione

4. **Monitor Logs** (primi giorni dopo deploy)
   - Controllare errori Django logs
   - Verificare feedback utenti
   - Monitorare performance template rendering

### Priorità 2: Aggiornare Venue Esistenti (BREVE TERMINE)

1. **Audit Venue Correnti**
   - Elencare tutti i venue nel database
   - Verificare quali hanno configuration_file
   - Identificare quali usano hardcoded corridors

2. **Migrare a v2.0 Format**
   - Per ogni venue con corridoi hardcoded:
     - Creare configurazione v2.0 con aisles
     - Testare configurazione con validation API
     - Caricare in venue
     - Rigenerare eventi recenti

3. **Rigenerare Event JSON**
   - Eventi esistenti hanno JSON v1.0 senza aisles
   - Opzioni:
     - **A) Lazy update**: Eventi si aggiornano al primo edit
     - **B) Batch update**: Script per rigenerare tutti gli eventi
     ```python
     # Script esempio
     from billboard.models import Event
     for event in Event.objects.filter(venue__configuration_file__isnull=False):
         event.save()  # Triggers JSON regeneration
     ```

### Priorità 3: Configuration Generator UI (MEDIO TERMINE)

Attualmente il configuration generator **non** supporta visualmente i corridoi. Gli utenti devono:
- Generare configurazione base senza corridoi
- Aggiungere manualmente sezione `aisles` al JSON
- Validare tramite API

**Improvement**:
Aggiungere sezione "Aisles" nell'interfaccia [templates/billboard/venue_config_generator.html](templates/billboard/venue_config_generator.html):

```html
<!-- Sezione Aisles da aggiungere -->
<div class="card">
    <h3>Corridoi (Aisles)</h3>

    <!-- Horizontal Aisles -->
    <div>
        <h4>Corridoi Verticali (tra posti)</h4>
        <button onclick="addHorizontalAisle()">+ Aggiungi</button>
        <div id="horizontal-aisles-list"></div>
    </div>

    <!-- Vertical Aisles -->
    <div>
        <h4>Corridoi Orizzontali (tra file)</h4>
        <button onclick="addVerticalAisle()">+ Aggiungi</button>
        <div id="vertical-aisles-list"></div>
    </div>
</div>
```

**Features**:
- Form per aggiungere horizontal aisle (seat_number, width, applies_to_rows)
- Form per aggiungere vertical aisle (row_name, height)
- Preview visual dei corridoi nella mappa
- Drag-and-drop per posizionare corridoi
- Validazione real-time

**Effort**: ~4-6 ore sviluppo + test

### Priorità 4: Documentazione Utente (MEDIO TERMINE)

1. **User Guide per Admin**
   - Come creare configurazione con corridoi
   - Esempi pratici per layout comuni
   - Troubleshooting

2. **Video Tutorial** (opzionale)
   - Screencast creazione venue config
   - Demo configurazione corridoi
   - 5-10 minuti

3. **Admin Help Text**
   - Aggiungere tooltip nell'admin Django
   - Spiegare campo `configuration_file`
   - Link a documentazione

### Priorità 5: Ottimizzazioni (LUNGO TERMINE)

1. **Performance**
   - Cache template tags results
   - Minimize template tag lookups
   - Profile rendering time

2. **UI/UX**
   - Stili CSS avanzati per corridoi
   - Colori personalizzabili
   - Icone direzionali per uscite

3. **Accessibility**
   - ARIA labels per corridoi
   - Screen reader support
   - Keyboard navigation

4. **Advanced Features**
   - Corridoi diagonali
   - Corridoi con nomi custom
   - Zone (orchestra, galleria, palchi)

---

## 🔍 Potenziali Issues da Monitorare

### 1. Template Tags Performance

Se venue ha molte file/posti (>500), il rendering template potrebbe essere lento.

**Soluzione**:
- Caching dei risultati template tags
- Pre-calcolare posizioni corridoi

### 2. Colspan Calculations

Il `colspan="21"` nel template è hardcoded. Se venue ha più di 20 posti per fila:

**Soluzione**:
```django
<td colspan="{{ total_columns }}">
```
Calcolare `total_columns` dinamicamente in view.

### 3. JavaScript Seat Selection

Il JavaScript `seat_name` array è ancora hardcoded (linee 145-161 in hall_detail.html).

**Potenziale Issue**: Se venue ha layout molto diverso, selezione posti potrebbe non funzionare.

**Soluzione** (priorità media):
- Generare `seat_name` array dinamicamente da Django
- Template tag `{% get_all_seat_names %}`

### 4. Migration Path per Eventi Vecchi

Eventi creati prima dell'update hanno JSON v1.0:
```json
{"A01": {"status": "0", "name": "A01"}, ...}
```

**Current**: View gestisce backward compatibility.

**Potential Issue**: Se admin modifica venue config, eventi vecchi non si aggiornano automaticamente.

**Soluzione**:
- Signal su Venue.save() per rigenerare eventi associati
- Oppure: Button admin "Rigenera tutti gli eventi"

---

## 📊 Metriche di Successo

Per valutare se l'implementazione ha successo:

### Metriche Tecniche
- ✅ Zero errori Django logs relativi a aisles
- ✅ Template rendering time < 100ms
- ✅ Tutti i test automatici passano
- ✅ Backward compatibility: eventi vecchi funzionano

### Metriche Utente
- ✅ Admin riesce a creare venue config con corridoi
- ✅ Frontend mostra layout corretto per ogni venue
- ✅ Utenti riescono a selezionare posti senza problemi
- ✅ Zero confusion su layout sala

### Metriche Business
- ✅ Possibilità di aggiungere nuovi venue rapidamente
- ✅ Riduzione tempo setup nuovo venue (da ore a minuti)
- ✅ Flessibilità per eventi speciali con layout custom

---

## 🎯 Roadmap Consigliata

### Settimana 1-2: Stabilizzazione
- [x] Implementazione core corridoi
- [x] Test suite automatica
- [ ] Test manuali in browser
- [ ] Deploy staging
- [ ] Monitor logs

### Settimana 3-4: Migration
- [ ] Audit venue esistenti
- [ ] Creare configs v2.0 per venue correnti
- [ ] Rigenerare eventi recenti
- [ ] Documentazione utente base

### Mese 2: Enhancement
- [ ] Configuration generator UI update
- [ ] Video tutorial
- [ ] Admin improvements
- [ ] Feedback utenti

### Mese 3+: Advanced Features
- [ ] Performance optimizations
- [ ] Advanced layout features
- [ ] Analytics su uso corridoi
- [ ] A/B testing layout diversi

---

## 🆘 Supporto e Troubleshooting

### Se Eventi Non Mostrano Corridoi

1. Verificare venue ha configuration_file con formato v2.0
2. Verificare evento è stato creato DOPO upload config
3. Se evento vecchio, rigenerare: Edit evento → Save
4. Controllare `media/hall_jsons/{event-slug}.json` contiene `"aisles"`

### Se Template Da Errore

1. Verificare `{% load aisle_helpers %}` presente
2. Verificare `hall/templatetags/__init__.py` esiste (anche vuoto)
3. Restart Django server dopo modifiche template tags
4. Check Django logs per dettagli errore

### Se Corridoi Non Renderizzano

1. Inspect elemento HTML - verificare `<td class="aisle-horizontal">` presente
2. Verificare `aisles` context variable in template
3. Debug template tags:
   ```python
   print(f"Aisles data: {aisles}")
   print(f"Checking aisle after row {row}, seat {seat}")
   ```

### Contatti

- GitHub Issues: [Crea issue](https://github.com/your-repo/issues)
- Documentazione: `AISLES_IMPLEMENTATION_SUMMARY.md`
- Test Script: `test_aisles_rendering.py`

---

## ✅ Checklist Pre-Deploy

Prima di deployare in produzione:

- [ ] ✅ Tutti i test automatici passano (`test_aisles_rendering.py`)
- [ ] Test manuale Teatro Cambiano completo
- [ ] Test manuale Salone Italia completo
- [ ] Test backward compatibility con evento vecchio
- [ ] Backup database effettuato
- [ ] Commit Git con messaggio descrittivo
- [ ] Documentazione aggiornata
- [ ] Team notificato delle modifiche
- [ ] Rollback plan definito
- [ ] Monitoring attivo

---

**Documento creato**: 2025-01-24
**Status implementazione core**: ✅ COMPLETA
**Pronto per**: Test manuali → Staging → Production

**Prossima azione consigliata**: Test manuale in browser con entrambi i venue.
