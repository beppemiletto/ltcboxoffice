# Quick Start - Running Tests

## Initial Setup (One Time)

Ensure you have pytest and dependencies installed:

```bash
pip install pytest pytest-django pytest-cov faker factory-boy
```

## Running Tests

### 1. Run All Tests

```bash
pytest
```

### 2. Run Tests with Coverage

```bash
pytest --cov=. --cov-report=html --cov-report=term
```

Then open the coverage report:

```bash
# Windows
start htmlcov\index.html

# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

### 3. Run Specific Test Categories

```bash
# User registration and authentication
pytest accounts/tests.py -v

# Event browsing and display
pytest store/tests.py -v

# Shopping cart
pytest carts/tests.py -v

# Orders and payments
pytest orders/tests.py -v

# Integration tests (complete user journeys)
pytest tests_integration.py -v
```

### 4. Run Specific Test Class

```bash
# Example: Run only user registration tests
pytest accounts/tests.py::TestUserRegistration -v

# Example: Run only event availability tests
pytest store/tests.py::TestEventAvailability -v
```

### 5. Run Specific Test

```bash
# Example: Test user registration flow
pytest accounts/tests.py::TestUserRegistration::test_successful_registration -v

# Example: Test complete booking journey
pytest tests_integration.py::TestCompleteUserJourney::test_new_user_registration_to_booking_complete_flow -vv
```

### 6. Run Tests by Keyword

```bash
# Run all tests related to email
pytest -k "email" -v

# Run all tests related to cart
pytest -k "cart" -v

# Run all tests related to registration
pytest -k "registration" -v
```

### 7. Verbose Output

```bash
# Show test names
pytest -v

# Show test names and print statements
pytest -vv -s
```

## Expected Output

When you run `pytest`, you should see something like:

```
================================ test session starts =================================
platform win32 -- Python 3.10.x, pytest-7.4.3, pluggy-1.3.0
django: settings: ltcboxoffice.settings.development (from ini)
rootdir: C:\Users\Asus\projects\python\ltcboxoffice
plugins: django-4.7.0, cov-4.1.0
collected 185 items

accounts/tests.py ........................................          [ 21%]
store/tests.py ..................................................   [ 48%]
carts/tests.py .................................                     [ 67%]
orders/tests.py ...........................................         [ 91%]
tests_integration.py ...............                                [100%]

================================ 185 passed in 45.23s ================================
```

## Test Files Overview

```
conftest.py                 # Shared fixtures (users, events, carts, etc.)
tests_integration.py        # End-to-end user journey tests
accounts/tests.py           # User registration, login, profile tests
store/tests.py              # Event browsing, seat selection tests
carts/tests.py              # Shopping cart management tests
orders/tests.py             # Order creation, payment, email tests
```

## Total Test Count

- **50+ test classes**
- **185+ test methods**

## Common Issues

### Issue: Tests fail due to missing database

**Solution:**
```bash
pytest --create-db
```

### Issue: Import errors

**Solution:**
```bash
# Make sure you're in the project root directory
cd C:\Users\Asus\projects\python\ltcboxoffice
pytest
```

### Issue: JSON file conflicts

**Solution:** Tests auto-cleanup JSON files. If issues persist:
```bash
# Manually remove
del /s /q static\json\*.json  # Windows
rm -rf static/json/*.json      # Linux/macOS
```

## Coverage Report

After running with coverage:

```bash
pytest --cov=. --cov-report=html
```

The HTML report shows:
- ✅ Overall coverage percentage
- ✅ Per-file coverage breakdown
- ✅ Line-by-line highlighting
- ✅ Missing lines that need tests

## Quick Test Examples

### Test User Registration
```bash
pytest accounts/tests.py::TestUserRegistration -v
```

Expected: 7 tests pass (registration, email verification, validation, etc.)

### Test Complete Booking Flow
```bash
pytest tests_integration.py::TestCompleteUserJourney::test_new_user_registration_to_booking_complete_flow -vv
```

Expected: Full journey from registration to order confirmation

### Test Email Sending
```bash
pytest -k "email" -v
```

Expected: All email-related tests (verification, order confirmation, etc.)

### Test Cart Management
```bash
pytest carts/tests.py -v
```

Expected: 35+ tests for cart operations (add, remove, pricing, etc.)

## Next Steps

1. **Run all tests to verify setup:**
   ```bash
   pytest -v
   ```

2. **Generate coverage report:**
   ```bash
   pytest --cov=. --cov-report=html
   open htmlcov/index.html
   ```

3. **Review failing tests (if any)** and adjust based on your actual implementation

4. **Add tests for any custom features** specific to your application

## Documentation

- **[TEST_SUMMARY.md](TEST_SUMMARY.md)** - Overview of all tests
- **[TESTING.md](TESTING.md)** - Detailed testing documentation
- **[conftest.py](conftest.py)** - Available test fixtures

## Support

If tests fail or you need help:

1. Check error messages carefully
2. Review [TESTING.md](TESTING.md) for troubleshooting
3. Verify fixture availability in [conftest.py](conftest.py)
4. Ensure database is created: `pytest --create-db`

---

**Ready to test!** Run `pytest -v` to get started.
