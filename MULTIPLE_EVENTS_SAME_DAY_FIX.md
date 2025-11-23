# Fix: Multiple Events on Same Day

## Problem Summary

The system was unable to handle multiple events on the same day because:

1. **Event Slug Generation**: The slug format was `{show_code}_{YYYYMMDD}_{show_slug}`, which would be identical for multiple events of the same show on the same day.

2. **Ticket Code Generation**: The ticket number format was `{sell_mode}{YYYYMMDD}.{show_pk:04d}.{serial:03d}`, which used the **show's primary key** instead of the **event's primary key**. This caused duplicate ticket numbers when multiple events of the same show occurred on the same day.

## Solution Implemented

### 1. Event Slug Generation ([store/models.py](store/models.py#L26-L38))

**Previous format:**
```
{show_code}_{YYYYMMDD}_{show_slug}
Example: HAM001_20231124_hamlet
```

**New format:**
```
{show_code}_{YYYYMMDD}_{event_pk}_{show_slug}
Example: HAM001_20231124_42_hamlet
```

**Key changes:**
- Added event primary key (pk) to the slug to ensure uniqueness
- For new events (before first save), temporarily uses time component (HHMM)
- After first save, updates slug with proper event pk
- Handles JSON file renaming when slug changes

### 2. Ticket Code Generation

Updated in two locations:

#### [boxoffice/views.py](boxoffice/views.py#L643)
**Previous:**
```python
ticket.number = f"{ticket.sell_mode[0]}{current_event.date_time.strftime('%Y%m%d')}.{show.pk:04d}.{serial:03d}"
```

**New:**
```python
ticket.number = f"{ticket.sell_mode[0]}{current_event.date_time.strftime('%Y%m%d')}.{current_event.pk:04d}.{serial:03d}"
```

#### [tickets/views.py](tickets/views.py#L104)
**Previous:**
```python
ticket.number = f"{ticket.sell_mode[0]}{event.date_time.strftime('%Y%m%d')}.{show.pk:04d}.{serial:03d}"
```

**New:**
```python
ticket.number = f"{ticket.sell_mode[0]}{event.date_time.strftime('%Y%m%d')}.{event.pk:04d}.{serial:03d}"
```

**Ticket number format:**
```
{sell_mode}{YYYYMMDD}.{event_pk:04d}.{serial:03d}
Example: C20231124.0042.001
```

- `C` = Cassa (selling mode: C=Cassa, W=Web, P=Prenotazione)
- `20231124` = Event date
- `0042` = Event PK (4 digits)
- `001` = Serial number within event (3 digits)

### 3. Database Constraints ([tickets/models.py](tickets/models.py#L35-L42))

Added Meta class to Ticket model:
```python
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['number'],
            name='unique_ticket_number',
            condition=models.Q(number__gt='')
        )
    ]
    indexes = [
        models.Index(fields=['event', 'seat'], name='ticket_event_seat_idx'),
    ]
```

- Ensures ticket numbers are unique (excluding empty strings)
- Added database index on `number` field for faster lookups
- Added composite index on `(event, seat)` for better query performance

### 4. Database Migration

Created migration: [tickets/migrations/0017_alter_ticket_number_ticket_ticket_event_seat_idx_and_more.py](tickets/migrations/0017_alter_ticket_number_ticket_ticket_event_seat_idx_and_more.py)

This migration:
- Adds `db_index=True` to the `number` field
- Creates the `ticket_event_seat_idx` index
- Creates the `unique_ticket_number` constraint

### 5. Test Fixtures Updated

Updated all test fixtures to remove hardcoded `event_slug` values in:
- [conftest.py](conftest.py) - 4 fixtures updated
- [store/tests.py](store/tests.py) - 8 fixtures updated
- [tests_integration.py](tests_integration.py) - 3 fixtures updated

All fixtures now rely on auto-generated slugs from the model's `save()` method.

## How It Works

### Event Creation Flow

1. **New Event Created**:
   - Event object created with `show`, `date_time`, prices, etc.
   - `event_slug` is initially generated using time component (HHMM)

2. **First Save**:
   - Event is saved to database and receives a primary key (pk)
   - Event slug is regenerated with the pk
   - Second save updates the slug with the proper format
   - JSON seat file is created

3. **Multiple Events Same Day**:
   - Each event gets a unique pk
   - Each event gets a unique slug: `TST001_20231124_1_hamlet`, `TST001_20231124_2_hamlet`, etc.
   - Each event gets its own JSON file

### Ticket Generation Flow

1. **Ticket Created for Event**:
   - Ticket references specific event via foreign key
   - Serial number calculated per event: `Ticket.objects.filter(event=event).count() + 1`

2. **Ticket Number Generated**:
   - Uses event.pk, not show.pk
   - Format: `C20231124.0001.001`
   - Different events on same day = different event pks = unique ticket numbers

3. **Database Enforces Uniqueness**:
   - Unique constraint prevents duplicate ticket numbers
   - Raises error if duplicate detected

## Benefits

1. **Unlimited Events Per Day**: No limit to how many events can be scheduled on the same day for the same show
2. **Unique Identification**: Each event and ticket is uniquely identifiable
3. **Data Integrity**: Database constraints prevent duplicates
4. **Better Performance**: Database indexes speed up common queries
5. **SIAE Compliance**: Ticket numbers remain compliant with fiscal requirements

## Migration Instructions

To apply these changes to your database:

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Apply the migration
python manage.py migrate tickets

# Verify migration
python manage.py showmigrations tickets
```

## Testing

A test script has been created at [test_multiple_events_same_day.py](test_multiple_events_same_day.py) that:
1. Creates 3 events on the same day for the same show
2. Verifies all event slugs are unique
3. Creates tickets for each event
4. Verifies all ticket numbers are unique
5. Cleans up test data

Run it with:
```bash
.\venv\Scripts\Activate.ps1
python test_multiple_events_same_day.py
```

## Example Scenarios

### Scenario 1: Two Shows Same Day, Different Times
```
Show: Hamlet (HAM001)
Event 1: 2023-11-24 20:00 -> Slug: HAM001_20231124_1_hamlet
Event 2: 2023-11-24 21:30 -> Slug: HAM001_20231124_2_hamlet

Tickets Event 1: C20231124.0001.001, C20231124.0001.002, ...
Tickets Event 2: C20231124.0002.001, C20231124.0002.002, ...
```

### Scenario 2: Matinee and Evening Performance
```
Show: The Tempest (TMP001)
Event 1: 2023-12-15 15:00 -> Slug: TMP001_20231215_5_tempest
Event 2: 2023-12-15 20:30 -> Slug: TMP001_20231215_6_tempest

Tickets Event 1: C20231215.0005.001, C20231215.0005.002, ...
Tickets Event 2: C20231215.0006.001, C20231215.0006.002, ...
```

## Files Modified

1. [store/models.py](store/models.py) - Event slug generation and save logic
2. [boxoffice/views.py](boxoffice/views.py) - Ticket number generation (boxoffice flow)
3. [tickets/views.py](tickets/views.py) - Ticket number generation (tickets flow)
4. [tickets/models.py](tickets/models.py) - Added Meta class with constraints and indexes
5. [conftest.py](conftest.py) - Updated test fixtures
6. [store/tests.py](store/tests.py) - Updated test fixtures
7. [tests_integration.py](tests_integration.py) - Updated test fixtures

## Files Created

1. [tickets/migrations/0017_alter_ticket_number_ticket_ticket_event_seat_idx_and_more.py](tickets/migrations/0017_alter_ticket_number_ticket_ticket_event_seat_idx_and_more.py)
2. [test_multiple_events_same_day.py](test_multiple_events_same_day.py)
3. [MULTIPLE_EVENTS_SAME_DAY_FIX.md](MULTIPLE_EVENTS_SAME_DAY_FIX.md) (this file)

## Backward Compatibility

**Existing Events**: Existing events will keep their old slugs until they are saved again. When an event is edited and saved, it will automatically get the new slug format with pk included.

**Existing Tickets**: Existing tickets are not affected. Only new tickets will use the new format with event.pk instead of show.pk.

**Database Migration**: The migration is backward-compatible and will not modify existing data, only add new constraints and indexes.

## Notes

- The unique constraint on ticket numbers uses a condition `number__gt=''` to allow empty strings (for tickets not yet assigned a number)
- The event slug temporary format (using HHMM) during initial creation is only used briefly and is replaced with the pk-based format after the first save
- All test fixtures now rely on auto-generated slugs to ensure consistency with production behavior
