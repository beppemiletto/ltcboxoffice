# Subscription Management System - Implementation Guide

## Overview
Implemented a complete subscription management system that allows users to purchase and use season tickets (abbonamenti) for events. The system tracks subscription usage and automatically deducts events when users book tickets using their subscriptions.

## Database Schema

### SubscriptionType
Defines the different types of subscriptions available:
- **R4**: 4 events, ridotto (reduced price)
- **R8**: 8 events, ridotto
- **I4**: 4 events, intero (full price)
- **I8**: 8 events, intero

Fields:
- `name`: Subscription type name
- `code_prefix`: R4, R8, I4, or I8
- `price`: Total subscription cost
- `discount_percent`: Discount percentage
- `max_events`: Number of events included (4 or 8)
- `valid_days`: Validity period in days (365)
- `is_active`: Active status

### Subscription
Individual subscription instances purchased by users:
- `subscription_type`: FK to SubscriptionType
- `user`: FK to Account (customer)
- `subscription_number`: Auto-generated unique code (e.g., "R4-0001")
- `payment`: FK to Payment record
- `purchase_date`: When subscription was purchased
- `valid_from` / `valid_to`: Validity period
- `events_included`: Number of events (copied from type)
- `events_used`: Counter incremented when used
- `is_active`: Active status

Methods:
- `remaining_events()`: Returns events_included - events_used
- `is_valid()`: Checks if current date is within validity period
- `can_use()`: Returns True if valid and has remaining events

### SubscriptionUsage
Tracks each time a subscription is used:
- `subscription`: FK to Subscription
- `event`: FK to Event
- `seat`: Seat number (e.g., "C05")
- `used_at`: Timestamp of usage
- Unique constraint on (subscription, event, seat)

## Price Code Mapping

Extended the existing price code system (0=gratuito, 1=ridotto, 2=intero) with subscription codes:

```python
SUBSCRIPTION_PRICE_CODES = {
    'R4': 3,  # Abbonamento Ridotto 4 eventi
    'R8': 4,  # Abbonamento Ridotto 8 eventi
    'I4': 5,  # Abbonamento Intero 4 eventi
    'I8': 6,  # Abbonamento Intero 8 eventi
}
```

**CartItem.ingresso** field choices:
- 0: Gratuito (free)
- 1: Ridotto (reduced)
- 2: Intero (full price)
- **3: Abbonamento R4** (NEW)
- **4: Abbonamento R8** (NEW)
- **5: Abbonamento I4** (NEW)
- **6: Abbonamento I8** (NEW)

## Code Changes

### 1. Models (`carts/models.py`)
Extended `CartItem.INGRESSI` choices to include codes 3-6:
```python
INGRESSI = (
    (0,'Gratuito'), 
    (1,'Ridotto'), 
    (2,'Intero'),
    (3,'Abbonamento R4'),
    (4,'Abbonamento R8'),
    (5,'Abbonamento I4'),
    (6,'Abbonamento I8'),
)
```

Updated `ingressi_strings` list to include subscription names.

**Migration**: `carts/migrations/0009_alter_cartitem_ingresso.py`

### 2. Utility Functions (`subscriptions/utils.py`)
Created helper functions:

- `get_user_active_subscriptions(user)`: Returns QuerySet of valid subscriptions for user
- `get_subscription_price_options(user)`: Returns list of subscription options with remaining events
- `is_subscription_price_code(code)`: Checks if price code is 3-6
- `get_subscription_by_price_code(user, price_code)`: Finds subscription matching the code
- `can_use_subscription(subscription, event)`: Validates subscription can be used

### 3. Cart Views (`carts/views.py`)
Modified to handle subscription codes:

**`plus_ingresso()` / `minus_ingresso()`**:
- Now cycle through 0-6 instead of 0-2
- Set `item.price = 0.0` for subscription codes (3-6)
- Use `is_subscription_price_code()` to detect subscription usage

**`cart()`**:
- Import `get_subscription_price_options`
- Pass `subscription_options` to template context
- Shows available subscriptions for authenticated users

### 4. Cart Template (`templates/store/cart.html`)
Added subscription info card in sidebar:
```django
{% if subscription_options %}
<div class="card mt-3">
  <div class="card-body">
    <h5 class="card-title">I tuoi abbonamenti</h5>
    <p class="small text-muted">Usa i pulsanti +/- nella colonna "Tipo Ingresso" per selezionare un abbonamento.</p>
    <hr>
    {% for option in subscription_options %}
    <dl class="dlist-align">
      <dt>{{ option.name }}:</dt>
      <dd class="text-right">
        {% if option.remaining > 0 %}
            <span class="badge badge-success">{{ option.remaining }} eventi disponibili</span>
        {% else %}
            <span class="badge badge-warning">Esaurito</span>
        {% endif %}
      </dd>
    </dl>
    {% endfor %}
  </div>
</div>
{% endif %}
```

### 5. Booking Flow (`booking/views.py`)
Modified `booking_payments()` to handle subscription usage:

**Added imports**:
```python
from subscriptions.models import SubscriptionUsage
from subscriptions.utils import is_subscription_price_code, get_subscription_by_price_code
```

**After JSON update, before UserEvent**:
```python
# Handle subscription usage if this is a subscription-based ticket
if is_subscription_price_code(item.ingresso):
    subscription = get_subscription_by_price_code(current_user, item.ingresso)
    if subscription:
        # Create SubscriptionUsage record
        usage = SubscriptionUsage(
            subscription=subscription,
            event=event,
            seat=seat,
        )
        usage.save()
        
        # Increment events_used counter
        subscription.events_used += 1
        subscription.save()
```

## User Flow

### Booking with Subscription

1. **User selects seats** in `hall_detail.html`
   - Seats added to cart with default `ingresso=2` (intero)

2. **User views cart** at `/cart/`
   - Sidebar shows "I tuoi abbonamenti" card with available subscriptions
   - User clicks +/- buttons to change `ingresso` from 2 (Intero) to 3-6 (Abbonamento)
   - Price automatically set to €0.00 for subscription codes

3. **User proceeds to checkout**
   - Total excludes subscription-based items (price = 0)
   - Only pays for non-subscription tickets

4. **Booking confirmation** (`booking_payments`)
   - For subscription codes (3-6):
     - Creates `SubscriptionUsage` record linking subscription → event → seat
     - Increments `subscription.events_used` counter
     - No payment charged for this ticket
   - For regular codes (0-2):
     - Standard payment processing

5. **Email confirmation** sent with booking details

### Admin Interface

Access Django admin at `/admin/subscriptions/`:

**SubscriptionType**:
- View/edit subscription types (R4, R8, I4, I8)
- Configure pricing, validity, event limits

**Subscription**:
- View all customer subscriptions
- Filter by type, validity, user
- See remaining events with visual indicators:
  - ✓ (green): Has remaining events and is valid
  - ✗ (red): No events remaining or expired
  - ⚠ (yellow): Warnings

**SubscriptionUsage**:
- Track all usage history
- Filter by subscription, event, date
- See which seats were used

## Data Import

Imported 14 existing subscriptions from `Abbonamenti2025-26.xlsx`:
- **10 × R4** (4 events ridotto)
- **2 × I4** (4 events intero)
- **1 × R8** (8 events ridotto)
- **1 × I8** (8 events intero)

Command: `python manage.py import_subscriptions`

## Testing Checklist

- [x] Database models created and migrated
- [x] Admin interface functional
- [x] Subscription data imported from Excel
- [x] Cart displays subscription options for authenticated users
- [x] +/- buttons cycle through all price codes including subscriptions
- [x] Price correctly set to €0.00 for subscription codes
- [ ] **TODO**: Test complete booking flow with subscription code
- [ ] **TODO**: Verify SubscriptionUsage record created
- [ ] **TODO**: Verify events_used counter incremented
- [ ] **TODO**: Test subscription exhaustion (used all events)
- [ ] **TODO**: Test subscription expiration (past valid_to date)

## Next Steps (Future Features)

1. **Boxoffice Validation Interface**
   - Barcode scanning at entrance
   - Real-time subscription validation
   - Seat assignment confirmation

2. **Subscription Purchase Flow**
   - Frontend form to buy new subscriptions
   - Payment integration
   - Automatic subscription activation

3. **Usage Analytics**
   - Subscription usage reports
   - Revenue analysis (subscription vs single tickets)
   - Popular events for subscription holders

4. **Email Notifications**
   - Subscription expiration warnings
   - Low events remaining alerts
   - Usage confirmation emails

## Files Modified

### Created:
- `subscriptions/models.py`
- `subscriptions/admin.py`
- `subscriptions/utils.py`
- `subscriptions/management/commands/import_subscriptions.py`
- `subscriptions/migrations/*.py`

### Modified:
- `carts/models.py` - Extended INGRESSI choices
- `carts/views.py` - Subscription handling in cart
- `templates/store/cart.html` - Subscription info display
- `booking/views.py` - SubscriptionUsage creation
- `ltcboxoffice/settings/base.py` - Added 'subscriptions' to INSTALLED_APPS

## Configuration

### Settings
In `ltcboxoffice/settings/base.py`:
```python
INSTALLED_APPS = [
    # ...
    'subscriptions',
    # ...
]
```

### Price Code Reference
```python
# Standard codes (existing)
0 = Gratuito (Free)
1 = Ridotto (Reduced)
2 = Intero (Full price)

# Subscription codes (NEW)
3 = Abbonamento R4 (4 events reduced)
4 = Abbonamento R8 (8 events reduced)
5 = Abbonamento I4 (4 events full)
6 = Abbonamento I8 (8 events full)
```

## Support

For questions or issues:
1. Check Django admin logs
2. Query SubscriptionUsage table for audit trail
3. Verify subscription validity with `subscription.can_use()`
4. Check CartItem.ingresso values in cart

## License
Part of LTC BoxOffice system - Internal use only
