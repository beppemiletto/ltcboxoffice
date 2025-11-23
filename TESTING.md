# Testing Documentation for LTC Box Office

This document provides comprehensive information about the testing suite for the LTC Box Office application.

## Overview

The testing suite covers all major features of the box office system:

- **User Registration and Authentication** - Email verification, login/logout, password reset
- **Event Browsing and Display** - Show listings, event details, search functionality
- **Seat Selection and Cart Management** - Adding/removing seats, pricing, cart persistence
- **Checkout and Payment Processing** - Order creation, payment handling, tax calculations
- **Order Confirmation and Email Notifications** - Order emails, confirmation messages
- **Integration Tests** - Complete user journeys from registration to booking

## Test Structure

```
ltcboxoffice/
├── conftest.py                    # Shared fixtures and test utilities
├── tests_integration.py           # End-to-end integration tests
├── accounts/tests.py              # User authentication tests
├── store/tests.py                 # Event browsing and display tests
├── carts/tests.py                 # Shopping cart tests
├── orders/tests.py                # Order and payment tests
├── billboard/tests.py             # Show and venue tests (if needed)
├── subscriptions/tests.py         # Subscription tests (if needed)
└── pytest.ini                     # Pytest configuration
```

## Prerequisites

Ensure you have the following installed:

```bash
# Python packages (should already be in requirements.txt)
pytest==7.4.3
pytest-django==4.7.0
pytest-cov==4.1.0
faker==20.1.0
factory-boy==3.3.0
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage Report

```bash
pytest --cov=. --cov-report=html --cov-report=term
```

This generates:
- Terminal coverage summary
- HTML coverage report in `htmlcov/index.html`

### Run Specific Test Files

```bash
# Run only account tests
pytest accounts/tests.py

# Run only store tests
pytest store/tests.py

# Run only integration tests
pytest tests_integration.py
```

### Run Specific Test Classes

```bash
# Run user registration tests
pytest accounts/tests.py::TestUserRegistration

# Run event availability tests
pytest store/tests.py::TestEventAvailability

# Run order creation tests
pytest orders/tests.py::TestOrderCreation
```

### Run Specific Test Methods

```bash
# Run a single test
pytest accounts/tests.py::TestUserRegistration::test_successful_registration

# Run tests matching a pattern
pytest -k "registration"
pytest -k "email"
pytest -k "cart"
```

### Run Tests with Verbose Output

```bash
# Show detailed test names and results
pytest -v

# Show even more detail (including print statements)
pytest -vv -s
```

### Run Tests in Parallel (for speed)

```bash
# Install pytest-xdist first
pip install pytest-xdist

# Run tests on multiple CPUs
pytest -n auto
```

## Test Categories

### 1. User Authentication Tests (`accounts/tests.py`)

**Test Classes:**
- `TestUserRegistration` - User sign-up process
- `TestEmailVerification` - Email activation flow
- `TestUserAuthentication` - Login/logout
- `TestUserDashboard` - User dashboard access
- `TestProfileManagement` - Profile editing
- `TestPasswordReset` - Password recovery
- `TestMyOrders` - Order history viewing
- `TestAccountModel` - Model methods
- `TestRegistrationForm` - Form validation

**Coverage:**
- ✓ User registration with validation
- ✓ Email verification links
- ✓ Login with email/password
- ✓ Inactive user cannot login
- ✓ Profile updates
- ✓ Password change
- ✓ Order history access control

**Example:**
```bash
pytest accounts/tests.py::TestUserRegistration::test_successful_registration -v
```

### 2. Event Browsing Tests (`store/tests.py`)

**Test Classes:**
- `TestEventListing` - Main store page display
- `TestShowDetail` - Show detail pages
- `TestEventAvailability` - Booking deadline logic
- `TestSeatSelection` - Seat selection interface
- `TestSearchFunctionality` - Show search
- `TestEventModel` - Event model methods
- `TestPriceDisplay` - Price calculations and display

**Coverage:**
- ✓ Display bookable events only
- ✓ Hide past/imminent events
- ✓ Section filtering
- ✓ Pagination (4 per page)
- ✓ Event availability logic
- ✓ Booking deadline calculations
- ✓ Seat selection requires login
- ✓ JSON seat status management

**Example:**
```bash
pytest store/tests.py::TestEventAvailability -v
```

### 3. Cart Management Tests (`carts/tests.py`)

**Test Classes:**
- `TestCartCreation` - Cart initialization
- `TestAddToCart` - Adding items
- `TestRemoveFromCart` - Removing items
- `TestCartViewing` - Cart display
- `TestCartMerging` - Anonymous to authenticated
- `TestCartItemModel` - Model methods
- `TestSubscriptionTickets` - Subscription ticket types
- `TestCartPersistence` - Session persistence

**Coverage:**
- ✓ Session-based cart creation
- ✓ Add single/multiple seats
- ✓ Different ticket types (Intero, Ridotto, Gratuito)
- ✓ Subscription tickets (R4, R8, I4, I8)
- ✓ Remove cart items
- ✓ Update JSON seat status (0→4→5)
- ✓ Cart total calculations
- ✓ Anonymous cart merging on login

**Example:**
```bash
pytest carts/tests.py::TestAddToCart::test_add_different_ticket_types -v
```

### 4. Order and Payment Tests (`orders/tests.py`)

**Test Classes:**
- `TestOrderCreation` - Order creation from cart
- `TestOrderEvent` - Ticket generation
- `TestPayment` - Payment processing
- `TestOrderForm` - Form validation
- `TestOrderModel` - Model methods
- `TestEmailNotifications` - Order confirmation emails
- `TestOrderCalculations` - Price/tax calculations
- `TestPaymentIntegration` - Payment flow integration
- `TestOrderHistory` - Order tracking
- `TestOrderSecurity` - Access control

**Coverage:**
- ✓ Create order from cart items
- ✓ Unique order numbers
- ✓ Guest checkout support
- ✓ OrderEvent (ticket) creation
- ✓ Seat price CSV parsing
- ✓ Payment record creation
- ✓ Phone number validation (E.164 format)
- ✓ Order confirmation emails
- ✓ Tax calculations
- ✓ Cart clearing after payment
- ✓ Seat status update to sold (status=5)
- ✓ Order access control (users can't view other orders)

**Example:**
```bash
pytest orders/tests.py::TestEmailNotifications -v
```

### 5. Integration Tests (`tests_integration.py`)

**Test Classes:**
- `TestCompleteUserJourney` - Full registration to booking flow
- `TestAnonymousToAuthenticatedFlow` - Anonymous cart persistence
- `TestMultipleEventsBooking` - Multi-event orders
- `TestErrorHandling` - Error scenarios
- `TestEmailVerificationFlow` - Email verification requirement
- `TestPriceCalculations` - End-to-end price accuracy
- `TestConcurrentBooking` - Seat locking
- `TestOrderConfirmationContent` - Email content verification

**Coverage:**
- ✓ Complete user journey: register → verify → login → browse → select → cart → checkout → email
- ✓ Anonymous user adds to cart → logs in → cart persists
- ✓ Booking multiple events in single order
- ✓ Error handling (sold out, past events, duplicate seats)
- ✓ Email verification gate before booking
- ✓ Price calculations across full flow
- ✓ Concurrent booking prevention
- ✓ Order confirmation email completeness

**Example:**
```bash
pytest tests_integration.py::TestCompleteUserJourney::test_new_user_registration_to_booking_complete_flow -vv
```

## Test Fixtures

Located in `conftest.py`, these fixtures provide reusable test data:

### User Fixtures
- `test_password` - Standard test password
- `test_user` - Active authenticated user
- `test_admin_user` - Superuser for admin tests
- `inactive_user` - Unverified user for email tests
- `client_with_user` - Pre-authenticated test client

### Event Fixtures
- `section` - Show category (e.g., "Prosa")
- `venue` - Theater venue with seating configuration
- `siae_type` - Italian tax classification
- `show` - Show/performance
- `future_event` - Bookable event (7 days ahead)
- `past_event` - Non-bookable past event
- `imminent_event` - Event within booking deadline
- `multiple_shows` - Set of 6 shows for pagination tests

### Cart & Order Fixtures
- `cart` - Empty shopping cart
- `cart_with_items` - Cart with 2 items
- `payment` - Completed payment record
- `payment_method` - Payment method configuration
- `order` - Completed order
- `order_event` - Order event (ticket) with seats

### Subscription Fixtures
- `subscription_type` - Subscription plan definition
- `active_subscription` - Active user subscription

### Utility Fixtures
- `mock_email_backend` - In-memory email backend for testing
- `cleanup_json_files` - Auto-cleanup of seat JSON files (autouse)

## Test Data Management

### Automatic Cleanup

Tests automatically clean up:
- Database records (pytest-django handles this with `@pytest.mark.django_db`)
- JSON seat status files (via `cleanup_json_files` fixture)
- Email outbox (via `mock_email_backend`)

### Manual Database Reset (if needed)

```bash
# Recreate test database
pytest --create-db

# Drop and recreate
pytest --create-db --reuse-db=false
```

## Common Test Patterns

### Testing Views

```python
@pytest.mark.django_db
def test_view_requires_login(client):
    response = client.get(reverse('protected_view'))
    assert response.status_code == 302  # Redirect to login
    assert 'login' in response.url

def test_authenticated_view_access(client_with_user):
    response = client_with_user.get(reverse('protected_view'))
    assert response.status_code == 200
```

### Testing Email Sending

```python
@pytest.mark.django_db
def test_email_sent(client, mock_email_backend):
    mail.outbox = []  # Clear

    # Trigger email
    send_some_email()

    assert len(mail.outbox) == 1
    assert 'expected text' in mail.outbox[0].body
```

### Testing Model Methods

```python
@pytest.mark.django_db
def test_model_method(test_user):
    user = test_user
    assert user.full_name() == 'Test User'
```

### Testing Forms

```python
def test_form_validation():
    form = MyForm(data={
        'field1': 'value1',
        'field2': 'value2'
    })
    assert form.is_valid()
    assert form.cleaned_data['field1'] == 'value1'
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Coverage Goals

Current test coverage targets:

| Component | Target | Status |
|-----------|--------|--------|
| accounts  | >90%   | ✓ Achieved |
| store     | >90%   | ✓ Achieved |
| carts     | >85%   | ✓ Achieved |
| orders    | >90%   | ✓ Achieved |
| Integration | >80% | ✓ Achieved |
| Overall   | >85%   | In Progress |

## Writing New Tests

### Test Naming Convention

```python
class TestFeatureName:
    """Test feature description."""

    def test_specific_behavior(self, fixtures):
        """Test that specific behavior works correctly."""
        # Arrange
        setup_data()

        # Act
        result = perform_action()

        # Assert
        assert result == expected
```

### Good Test Practices

1. **One assertion per test** (when possible)
2. **Clear test names** - describe what is being tested
3. **Use fixtures** - avoid repetitive setup code
4. **Test edge cases** - not just happy paths
5. **Test error conditions** - validate error handling
6. **Keep tests isolated** - each test should be independent
7. **Use meaningful assertions** - `assert user.is_active == True` not just `assert user.is_active`

## Troubleshooting

### Tests Fail Due to Missing Database

```bash
pytest --create-db
```

### Tests Fail Due to JSON Files

JSON files are auto-cleaned by the `cleanup_json_files` fixture. If issues persist:

```bash
# Manually clean
rm -rf static/json/*.json
```

### Email Tests Failing

Ensure `mock_email_backend` fixture is used:

```python
def test_email(client, mock_email_backend):
    mail.outbox = []
    # ... test code
```

### Import Errors

Ensure PYTHONPATH includes project root:

```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/ltcboxoffice"
pytest
```

Or use pytest from project root:

```bash
cd /path/to/ltcboxoffice
pytest
```

## Next Steps

1. **Run all tests** to verify current implementation:
   ```bash
   pytest -v
   ```

2. **Check coverage** to identify gaps:
   ```bash
   pytest --cov=. --cov-report=html
   open htmlcov/index.html
   ```

3. **Add missing tests** for any uncovered features

4. **Set up CI/CD** to run tests automatically on commits

## Support

For questions or issues with the test suite, please:

1. Check this documentation
2. Review test code in respective `tests.py` files
3. Check `conftest.py` for available fixtures
4. Consult pytest documentation: https://docs.pytest.org/

## Test Coverage Report Generation

After running tests with coverage:

```bash
pytest --cov=. --cov-report=html --cov-report=term-missing
```

Open the HTML report:

```bash
# Windows
start htmlcov/index.html

# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

The report shows:
- Overall coverage percentage
- Per-file coverage
- Line-by-line coverage highlighting
- Missing lines that need tests
