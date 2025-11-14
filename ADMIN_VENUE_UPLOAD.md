# Venue Configuration File Upload - Admin Guide

## Panoramica

Il sistema permette di caricare direttamente i file di configurazione delle venue (JSON o XML) tramite l'interfaccia Django Admin. Quando si carica un file, il sistema:

1. Salva il file in `media/venue_configs/`
2. Valida il formato (JSON o XML)
3. **Carica automaticamente** posti e file al salvataggio

## Come Usare

### 1. Creare/Modificare una Venue da Admin

```
http://localhost:8000/admin/billboard/venue/
```

1. Clicca **"Add Venue"** o seleziona venue esistente
2. Compila i campi base:
   - **Name**: Nome della venue (es. "Teatro Comunale di Cambiano")
   - **Slug**: Auto-popolato dal nome (es. "teatro-comunale-di-cambiano")
   - **Address**: Indirizzo completo
   - **Capacity**: Capienza totale (verrà aggiornata automaticamente)

3. Nella sezione **"Seating Configuration"**:
   - Clicca **"Choose File"** accanto a "Configuration file"
   - Seleziona il file JSON o XML con la configurazione posti
   - Il sistema mostrerà:
     - **Format**: json o xml (readonly)
     - **Seats**: Numero posti caricati (readonly)
     - **Rows**: Numero file caricate (readonly)

4. Clicca **"Save"**

### 2. Caricamento Automatico

Quando salvi la venue:
- Se hai caricato un file di configurazione
- E la venue **non ha ancora posti** nel database
- Il sistema **carica automaticamente** la configurazione

**Messaggio di conferma:**
```
Configuration file uploaded. Seats and rows will be loaded automatically.
Check the venue to see 263 seats loaded.
```

### 3. Verificare il Caricamento

Dopo il salvataggio:
1. Torna alla lista venue
2. Controlla la colonna **"Seats"** - dovrebbe mostrare il numero di posti
3. Controlla **"Config File"** - icona ✓ se caricato

Oppure vai a:
- `/admin/hall/seat/` - Vedi tutti i posti per venue
- `/admin/hall/row/` - Vedi tutte le file per venue

## Formato File Configurazione

### JSON Format (Raccomandato)

```json
{
  "venue": {
    "name": "Teatro Comunale di Cambiano",
    "slug": "teatro-cambiano",
    "capacity": 263,
    "ba_code_siae": "0050450366484",
    "local_code_siae": "  045"
  },
  "rows": [
    {
      "name": "A",
      "offset_start": 4,
      "offset_end": 2,
      "is_active": false,
      "seats": [
        {"num": 5, "active": false},
        {"num": 6, "active": false}
      ]
    }
  ]
}
```

### XML Format

```xml
<?xml version="1.0"?>
<venue_config>
  <venue>
    <name>Teatro Comunale di Cambiano</name>
    <slug>teatro-cambiano</slug>
    <capacity>263</capacity>
  </venue>
  <rows>
    <row name="A" offset_start="4" offset_end="2" is_active="false">
      <seat num="5" active="false"/>
      <seat num="6" active="false"/>
    </row>
  </rows>
</venue_config>
```

## Funzionalità Admin Avanzate

### List Display

La lista venue mostra:
- **Name**: Nome venue
- **Slug**: Identificativo URL
- **Capacity**: Capienza
- **Address**: Indirizzo
- **Config File**: ✓ se file caricato, ✗ se mancante
- **Seat Count**: Numero posti nel database

### Filtri
- Filtra per **Capacity** (range di capienza)

### Ricerca
- Cerca per **Name**, **Slug**, **Address**

### Fieldsets Organizzati

**Basic Information:**
- Name, Slug, Address, Capacity

**SIAE Codes** (collassabile):
- BA Code SIAE, Local Code SIAE

**Seating Configuration:**
- Configuration File (upload)
- Format (readonly - json/xml)
- Seat Count (readonly)
- Row Count (readonly)

## Casi d'Uso

### Caso 1: Nuova Venue

```
1. Admin → Add Venue
2. Name: "Salone Italia"
3. Slug: "salone-italia" (auto)
4. Address: "Via Roma 123, Cambiano"
5. Capacity: 150 (temporaneo)
6. Upload: salone-italia.json
7. Save
8. ✅ Sistema carica 150 posti automaticamente
```

### Caso 2: Aggiornare Configurazione Venue Esistente

**ATTENZIONE**: Il caricamento automatico avviene **solo se la venue non ha posti**.

Per aggiornare:
```
1. Elimina posti esistenti:
   - Admin → Seats → Filter by venue
   - Select all → Delete
   - Conferma

2. Modifica venue:
   - Admin → Venue → Edit
   - Upload nuovo file configurazione
   - Save
   - ✅ Posti ricaricati
```

**Oppure usa management command:**
```bash
python manage.py load_venue_config nuovo-file.json --venue-slug salone-italia --clear
```

### Caso 3: Venue Senza File (Manuale)

Se non carichi file di configurazione:
- La venue viene salvata normalmente
- Posti e file devono essere creati manualmente in Admin
- Oppure usa command line: `python manage.py load_venue_config`

## Validazione File

Il sistema valida automaticamente:
- ✅ **Formato**: Solo .json o .xml accettati
- ✅ **Sintassi**: File deve essere valido JSON/XML
- ✅ **Struttura**: Deve contenere sezioni "venue" e "rows"
- ✅ **Dati**: Campi obbligatori presenti

**In caso di errore:**
- File viene salvato comunque
- Posti NON vengono caricati
- Controlla log Django per dettagli errore
- Correggi file e ricarica

## Metodi Model Disponibili

### `venue.get_config_file_path()`
Ritorna path assoluto al file configurazione.

```python
>>> venue = Venue.objects.get(slug='teatro-cambiano')
>>> venue.get_config_file_path()
'/path/to/media/venue_configs/teatro-cambiano.json'
```

### `venue.get_config_file_format()`
Ritorna formato file: 'json', 'xml', o None.

```python
>>> venue.get_config_file_format()
'json'
```

### `venue.seats.all()`
Tutti i posti della venue.

```python
>>> venue.seats.count()
263
>>> venue.seats.filter(active=True).count()
234
```

### `venue.rows.all()`
Tutte le file della venue.

```python
>>> venue.rows.count()
15
>>> venue.rows.filter(is_active=True)
<QuerySet [Row: Q, Row: P, ...]>
```

## Troubleshooting

### File caricato ma nessun posto creato

**Causa**: Venue aveva già posti nel database.

**Soluzione**:
```python
# Django shell
from billboard.models import Venue
venue = Venue.objects.get(slug='teatro-cambiano')
venue.seats.all().delete()
venue.rows.all().delete()

# Ri-salva venue da admin per trigger auto-load
```

### Errore "Failed to auto-load configuration"

**Causa**: File malformato o path non valido.

**Debugging**:
```bash
# Controlla log Django
tail -f logs/django.log

# Testa file manualmente
python manage.py load_venue_config venue-file.json --dry-run
```

### File non appare in lista

**Causa**: Permessi file system o MEDIA_ROOT non configurato.

**Verifica**:
```python
# settings.py
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# urls.py (development)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### Capacity non si aggiorna automaticamente

**Nota**: Il campo capacity NON viene aggiornato automaticamente dal file.

**Aggiorna manualmente**:
```python
venue = Venue.objects.get(slug='teatro-cambiano')
venue.capacity = venue.seats.filter(active=True).count()
venue.save()
```

## Best Practices

### ✅ DO

- Testa file configurazione con `--dry-run` prima di caricare
- Usa nomi file descrittivi: `teatro-cambiano-2025.json`
- Mantieni backup dei file configurazione
- Verifica numero posti dopo caricamento
- Documenta modifiche alla configurazione

### ❌ DON'T

- Non caricare file di dimensioni enormi (>1MB)
- Non modificare file mentre venue è in uso
- Non eliminare file configurazione dopo upload (è referenziato)
- Non usare caratteri speciali nei nomi file

## File Location

I file caricati vengono salvati in:
```
media/
└── venue_configs/
    ├── teatro-cambiano.json
    ├── salone-italia.xml
    └── biblioteca.json
```

**Nota**: Directory `media/` non è versionata in Git (.gitignore).

## Sicurezza

- ✅ Solo admin autenticati possono caricare file
- ✅ Solo formati .json e .xml accettati
- ✅ File salvati in directory dedicata (no execute)
- ✅ Validazione sintassi prima di processing
- ⚠️ Assicurati che MEDIA_ROOT abbia permessi corretti

## Integrazione con Command Line

Oltre all'interfaccia admin, puoi caricare configurazioni via command line:

```bash
# Load configuration from uploaded file
python manage.py load_venue_config venue_configs/teatro-cambiano.json --venue-slug teatro-cambiano

# Clear existing data before loading
python manage.py load_venue_config teatro-cambiano.json --clear

# Preview what would be loaded without saving
python manage.py load_venue_config teatro-cambiano.json --dry-run
```

**Command Options:**
- `config_file`: Path to JSON/XML file (relative to venue_configs/ or absolute)
- `--venue-slug`: Specify venue slug (optional, derived from filename if not provided)
- `--clear`: Clear existing seats and rows before loading
- `--dry-run`: Preview changes without saving to database

**Note:** In the current production branch, the command clears ALL seats and rows when using `--clear` since multi-venue FK relationships are not yet implemented. Full multi-venue support will be available after merging the `feature/venue-management` branch.

## Integrazione con Workflow Git

### Development
```bash
# Carica file in dev
python manage.py runserver
# Admin → Upload file
# File salvato in media/venue_configs/ (non versionato)
```

### Production
```bash
# 1. Esporta configurazione da dev
python manage.py export_venue_config teatro-cambiano

# 2. Commit file in venue_configs/ (source control)
git add venue_configs/teatro-cambiano.json
git commit -m "Add Teatro Cambiano configuration"

# 3. Deploy to production
git pull origin production

# 4. Carica via admin o command
python manage.py load_venue_config venue_configs/teatro-cambiano.json
```

---

**Ultimo aggiornamento**: 2025-11-14  
**Versione**: 1.0
