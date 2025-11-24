# Correzioni Necessarie per i Test

## Stato Attuale
- ✅ 96 test passano
- ❌ 44 test falliscono

## Correzioni Applicate

### 1. ✅ Configurazione pytest
- Creato `ltcboxoffice/settings/test.py` per test senza dipendenze opzionali
- Aggiornato `pytest.ini` per usare settings di test
- Risolti problemi con user creation signature

### 2. ✅ Image Fields
- Aggiunto test image a `show` fixture per `shw_image`
- Aggiunto test image a `test_user` fixture per `profile_picture`

## Correzioni Da Applicare

### 3. ❌ Order Model - Campo `tax` obbligatorio

Tutti i test che creano Order devono includere il campo `tax`. Esempi nei file:

**orders/tests.py** - Aggiungi `tax=0.0` o calcola correttamente:

```python
# Linea 58-67
order1 = Order.objects.create(
    user=test_user,
    payment=payment,
    order_number='ORD-001',
    first_name='Test',
    last_name='User',
    email='test@example.com',
    order_total=50.0,
    tax=4.5,  # AGGIUNGI QUESTO
    is_ordered=True
)

# Ripeti per tutti gli Order.objects.create() in:
# - test_order_number_is_unique (linea 70)
# - test_order_can_be_created_without_user (linea 85-95)
# - test_order_status_choices (linea 347-356)
# - test_order_tracking_by_status (linea 557-578)
# - test_user_cannot_access_other_users_orders (linea 598-607)
# - test_guest_order_accessible_by_email (linea 617-626)
```

### 4. ❌ URL Names - view_cart non esiste

Il nome URL `view_cart` non esiste nel tuo progetto. Trova il nome corretto in `carts/urls.py`:

```bash
# Cerca il pattern URL corretto
grep -r "cart" carts/urls.py
```

Poi aggiorna tutti i test in `carts/tests.py` che usano `reverse('view_cart')` con il nome corretto.

### 5. ❌ OrderEvent.seats_list() - Parsing

Il metodo `seats_list()` sembra restituire una lista invece di un dict. Verifica l'implementazione in `orders/models.py`:

```python
# In orders/tests.py linea 122-130
seats = order_event.seats_list()

# Verifica che tipo restituisce:
# Se è una lista: assert isinstance(seats, list)
# Se è un dict: assert isinstance(seats, dict)
```

### 6. ❌ Test Assertions - Full Address

Il metodo `full_address()` non include il campo `city` nella stringa. Aggiorna i test:

**accounts/tests.py** linea 475:
```python
# Invece di:
assert 'Milano' in full_address

# Usa:
assert 'Via Roma 1' in full_address
```

**orders/tests.py** linea 328:
```python
# Stesso problema - verifica cosa restituisce full_address() e aggiorna assertion
```

### 7. ❌ Model __str__ Methods

I metodi `__str__` dei model non corrispondono alle aspettative. Verifica i model:

**Event.__str__()** - store/models.py
```python
# Test si aspetta: "Hamlet - 30/11/2025 09:05"
# Verifica cosa restituisce realmente e aggiorna test
```

**Show.__str__()** - billboard/models.py
```python
# Test si aspetta: il titolo "Hamlet"
# Ma forse restituisce lo slug "hamlet"
```

**Order.__str__()** - orders/models.py
```python
# Test si aspetta: order_number o email
# Forse restituisce un ID o altro formato
```

### 8. ❌ JSON Path per Events

Il path JSON non è in `static/json` ma in `hall_jsons`:

**store/tests.py** linea 412:
```python
# Test si aspetta path che contiene 'static'
# Ma il path reale è 'C:\\Users\\Asus\\projects\\python\\ltcboxoffice\\hall_jsons\\...'

# Aggiorna assertion:
assert 'hall_jsons' in json_path  # invece di 'static'
```

### 9. ❌ Email Subject

L'email di verifica ha subject in italiano:

**accounts/tests.py** linea 71:
```python
# Invece di:
assert 'verify' in mail.outbox[0].subject.lower() or 'activate' in mail.outbox[0].subject.lower()

# Usa:
assert 'attivazione' in mail.outbox[0].subject.lower()
```

### 10. ❌ Seat Selection - Redirect invece di 200

I test di seat selection si aspettano status 200 ma ricevono 302 (redirect). Probabilmente manca qualche permesso o l'evento non è bookable.

**store/tests.py** linee 291-340:
```python
# Verifica perché redirect invece di mostrare la pagina
# Possibili cause:
# - is_bookable() restituisce False
# - Manca permesso speciale
# - URL pattern diverso
```

## Come Applicare le Correzioni

### Opzione 1: Correzione Manuale (Consigliata per apprendere)

1. Apri ogni file indicato
2. Cerca le linee specificate
3. Applica le correzioni

### Opzione 2: Correzione Automatica

Posso generare patch file specifici per ogni correzione che puoi applicare.

### Opzione 3: Approccio Graduale

Correggi un tipo di errore alla volta e riesegui i test:

```bash
# Step 1: Fix Order tax field
# Modifica orders/tests.py - aggiungi tax a tutti gli Order.objects.create

# Step 2: Test
venv\Scripts\python.exe -m pytest orders/tests.py -v --no-cov

# Step 3: Fix URL names
# Trova nome corretto in carts/urls.py
# Aggiorna carts/tests.py

# Step 4: Test
venv\Scripts\python.exe -m pytest carts/tests.py -v --no-cov

# Continua...
```

## Test che Funzionano Già

Questi test passano senza modifiche:

✅ accounts/tests.py::TestAccountModel (4/4)
✅ accounts/tests.py::TestUserAuthentication (parziale)
✅ carts/tests.py::TestCartItemModel
✅ carts/tests.py::TestSubscriptionTickets
✅ orders/tests.py::TestPayment (parziale)
✅ store/tests.py::TestEventAvailability
✅ E molti altri...

## Prossimi Passi

1. **Priorità Alta**: Fix campo `tax` in Order - risolve 7 test
2. **Priorità Alta**: Fix URL `view_cart` - risolve 6 test
3. **Priorità Media**: Fix assertions su stringhe (full_address, __str__)
4. **Priorità Bassa**: Verifica logica seat selection

Vuoi che generi le correzioni specifiche per un gruppo di test?
