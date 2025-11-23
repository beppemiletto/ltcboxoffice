"""
Pytest configuration and shared fixtures for the entire test suite.
This file provides reusable test fixtures and utilities for all test modules.
"""
import os
import json
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import Account, UserProfile
from billboard.models import Section, Show, Venue, SiaeType
from store.models import Event
from carts.models import Cart, CartItem
from orders.models import Order, OrderEvent, Payment
from boxoffice.models import CustomerProfile, PaymentMethod
from subscriptions.models import SubscriptionType, Subscription

# Get the custom user model
User = get_user_model()


@pytest.fixture
def test_password():
    """Standard password for test users."""
    return 'TestPassword123!'


@pytest.fixture
def test_user(db, test_password):
    """Create a standard test user with profile."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    user = User.objects.create_user(
        email='testuser@example.com',
        password=test_password,
        first_name='Test',
        last_name='User',
        username='testuser'
    )
    # Set additional fields and activate user
    user.phone_number = '+393401234567'
    user.is_active = True
    user.save()

    # Create minimal test image
    image_content = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
        b'\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
        b'\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    )
    test_image = SimpleUploadedFile("profile.gif", image_content, content_type="image/gif")

    # Create user profile with image
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'profile_picture': test_image}
    )
    if not created and not profile.profile_picture:
        profile.profile_picture = test_image
        profile.save()

    return user


@pytest.fixture
def test_admin_user(db, test_password):
    """Create an admin user for testing privileged operations."""
    admin = User.objects.create_superuser(
        email='admin@example.com',
        password=test_password,
        first_name='Admin',
        last_name='User',
        username='adminuser'
    )
    admin.phone_number = '+393401234568'
    admin.save()
    return admin


@pytest.fixture
def inactive_user(db, test_password):
    """Create an inactive user for email verification testing."""
    user = User.objects.create_user(
        email='inactive@example.com',
        password=test_password,
        first_name='Inactive',
        last_name='User',
        username='inactiveuser'
    )
    user.phone_number = '+393401234569'
    user.is_active = False
    user.save()
    return user


@pytest.fixture
def siae_type(db):
    """Create a SIAE type for fiscal compliance."""
    return SiaeType.objects.create(
        code='01',
        description='Teatro - Prosa',
        iva=10.0
    )


@pytest.fixture
def section(db):
    """Create a section for organizing shows."""
    return Section.objects.create(
        name='Prosa',
        slug='prosa',
        default_price_full=20.0,
        default_price_reduced=15.0
    )


@pytest.fixture
def venue(db):
    """Create a venue with seating configuration."""
    # Create a temporary JSON configuration file for the venue
    config_data = {
        "rows": [
            {"row": "A", "seats": ["A01", "A02", "A03", "A04", "A05"]},
            {"row": "B", "seats": ["B01", "B02", "B03", "B04", "B05"]},
            {"row": "C", "seats": ["C01", "C02", "C03", "C04", "C05"]}
        ],
        "capacity": 15
    }

    venue = Venue.objects.create(
        name='Teatro Comunale',
        slug='teatro-comunale',
        address='Via Roma 1, Milano',
        capacity=15,
        ba_code_siae='BA001',
        local_code_siae='LOC001'
    )

    return venue


@pytest.fixture
def show(db, section, siae_type):
    """Create a show with all required relationships."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    # Create a minimal 1x1 pixel image for testing
    image_content = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
        b'\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
        b'\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    )
    test_image = SimpleUploadedFile("test_image.gif", image_content, content_type="image/gif")

    return Show.objects.create(
        shw_title='Hamlet',
        shw_author='William Shakespeare',
        shw_director='John Doe',
        shw_code='HAM001',
        slug='hamlet',
        section=section,
        description='A classic tragedy',
        siaetype=siae_type,
        shw_image=test_image,
        is_in_billboard=True,
        is_active=True
    )


@pytest.fixture
def future_event(db, show, venue):
    """Create a bookable event in the future."""
    event_datetime = timezone.now() + timedelta(days=7)

    event = Event.objects.create(
        show=show,
        date_time=event_datetime,
        price_full=25.0,
        price_reduced=18.0,
        vat_rate=10.0,
        venue=venue,
        event_slug=f"hamlet-{event_datetime.strftime('%Y%m%d')}",
        sold_out=False,
        booking_deadline_hours=3
    )

    # Create the JSON seat status file for this event
    json_path = event.get_json_path()
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    seat_status = {
        "A01": {"status": 0, "ingresso": "", "price": 0},
        "A02": {"status": 0, "ingresso": "", "price": 0},
        "A03": {"status": 0, "ingresso": "", "price": 0},
        "A04": {"status": 0, "ingresso": "", "price": 0},
        "A05": {"status": 0, "ingresso": "", "price": 0},
        "B01": {"status": 0, "ingresso": "", "price": 0},
        "B02": {"status": 0, "ingresso": "", "price": 0},
        "B03": {"status": 0, "ingresso": "", "price": 0},
        "B04": {"status": 0, "ingresso": "", "price": 0},
        "B05": {"status": 0, "ingresso": "", "price": 0},
        "C01": {"status": 0, "ingresso": "", "price": 0},
        "C02": {"status": 0, "ingresso": "", "price": 0},
        "C03": {"status": 0, "ingresso": "", "price": 0},
        "C04": {"status": 0, "ingresso": "", "price": 0},
        "C05": {"status": 0, "ingresso": "", "price": 0}
    }

    with open(json_path, 'w') as f:
        json.dump(seat_status, f)

    return event


@pytest.fixture
def past_event(db, show, venue):
    """Create a non-bookable past event."""
    event_datetime = timezone.now() - timedelta(days=7)

    event = Event.objects.create(
        show=show,
        date_time=event_datetime,
        price_full=25.0,
        price_reduced=18.0,
        vat_rate=10.0,
        venue=venue,
        event_slug=f"hamlet-past-{event_datetime.strftime('%Y%m%d')}",
        sold_out=False,
        booking_deadline_hours=3
    )

    return event


@pytest.fixture
def imminent_event(db, show, venue):
    """Create an event within the booking deadline (non-bookable)."""
    # Create an event that's 2 hours away (within the 3-hour deadline)
    event_datetime = timezone.now() + timedelta(hours=2)

    event = Event.objects.create(
        show=show,
        date_time=event_datetime,
        price_full=25.0,
        price_reduced=18.0,
        vat_rate=10.0,
        venue=venue,
        event_slug=f"hamlet-imminent-{event_datetime.strftime('%Y%m%d%H%M')}",
        sold_out=False,
        booking_deadline_hours=3
    )

    return event


@pytest.fixture
def cart(db):
    """Create a shopping cart."""
    return Cart.objects.create(
        cart_id='test_cart_id_123'
    )


@pytest.fixture
def cart_with_items(db, test_user, future_event, cart):
    """Create a cart with some items."""
    item1 = CartItem.objects.create(
        user=test_user,
        event=future_event,
        cart=cart,
        seat='A01',
        ingresso=2,  # Intero (Full price)
        price=25.0,
        is_active=True
    )

    item2 = CartItem.objects.create(
        user=test_user,
        event=future_event,
        cart=cart,
        seat='A02',
        ingresso=1,  # Ridotto (Reduced)
        price=18.0,
        is_active=True
    )

    return cart


@pytest.fixture
def payment_method(db):
    """Create a payment method for testing."""
    return PaymentMethod.objects.create(
        name='Cash',
        slug='cash',
        code='CASH',
        account_type='Cassa',
        commission_model='No commission'
    )


@pytest.fixture
def payment(db, test_user):
    """Create a payment record."""
    return Payment.objects.create(
        user=test_user,
        payment_id=f'PAY-{timezone.now().strftime("%Y%m%d%H%M%S")}',
        payment_method='Cash',
        amount_paid='43.00',
        status='COMPLETED',
        payer_mail=test_user.email,
        payer_given_name=test_user.first_name,
        payer_surname=test_user.last_name
    )


@pytest.fixture
def order(db, test_user, payment):
    """Create a complete order."""
    return Order.objects.create(
        user=test_user,
        payment=payment,
        order_number=f'ORD-{timezone.now().strftime("%Y%m%d%H%M%S")}',
        first_name=test_user.first_name,
        last_name=test_user.last_name,
        phone=test_user.phone_number,
        email=test_user.email,
        address_line_1='Via Roma 1',
        city='Milano',
        province='MI',
        post_code='20100',
        order_total=43.0,
        tax=3.91,
        status='Completed',
        is_ordered=True
    )


@pytest.fixture
def order_event(db, order, future_event, test_user, payment):
    """Create an order event (ticket)."""
    return OrderEvent.objects.create(
        order=order,
        event=future_event,
        user=test_user,
        payment=payment,
        seats_price='A01$25.0,A02$18.0',
        orderevent_number=f'OE-{timezone.now().strftime("%Y%m%d%H%M%S")}',
        expired=False
    )


@pytest.fixture
def customer_profile(db):
    """Create a box office customer profile."""
    return CustomerProfile.objects.create(
        first_name='Walk',
        last_name='In',
        email='walkin@example.com',
        phone_number='+393401234570',
        address='Via Milano 10',
        city='Roma',
        province='RM',
        post_code='00100'
    )


@pytest.fixture
def subscription_type(db):
    """Create a subscription type."""
    return SubscriptionType.objects.create(
        name='Abbonamento 4 ingressi ridotti',
        code_prefix='R4',
        type='REDUCED',
        price=Decimal('60.00'),
        discount_percent=Decimal('16.67'),
        max_events=4,
        valid_days=365,
        is_active=True
    )


@pytest.fixture
def active_subscription(db, test_user, subscription_type, payment):
    """Create an active subscription for a user."""
    return Subscription.objects.create(
        user=test_user,
        subscription_type=subscription_type,
        valid_from=timezone.now().date(),
        valid_to=timezone.now().date() + timedelta(days=365),
        events_included=4,
        events_used=0,
        payment=payment,
        status='ACTIVE'
    )


@pytest.fixture
def client_with_user(client, test_user, test_password):
    """Provide an authenticated client."""
    client.login(email=test_user.email, password=test_password)
    return client


@pytest.fixture
def multiple_shows(db, section, siae_type, venue):
    """Create multiple shows with events for testing pagination and filtering."""
    shows = []
    for i in range(6):
        show = Show.objects.create(
            shw_title=f'Show {i+1}',
            shw_author=f'Author {i+1}',
            shw_director=f'Director {i+1}',
            shw_code=f'SHW00{i+1}',
            slug=f'show-{i+1}',
            section=section,
            description=f'Description for show {i+1}',
            siaetype=siae_type,
            is_in_billboard=True,
            is_active=True
        )

        # Create a future event for each show
        event_datetime = timezone.now() + timedelta(days=i+1)
        Event.objects.create(
            show=show,
            date_time=event_datetime,
            price_full=20.0 + i,
            price_reduced=15.0 + i,
            vat_rate=10.0,
            venue=venue,
            event_slug=f'show-{i+1}-{event_datetime.strftime("%Y%m%d")}',
            sold_out=False,
            booking_deadline_hours=3
        )

        shows.append(show)

    return shows


@pytest.fixture(autouse=True)
def cleanup_json_files():
    """Automatically clean up JSON seat files after each test."""
    yield
    # Cleanup happens after the test
    json_dir = os.path.join(settings.BASE_DIR, 'static', 'json')
    if os.path.exists(json_dir):
        for root, dirs, files in os.walk(json_dir):
            for file in files:
                if file.endswith('.json'):
                    try:
                        os.remove(os.path.join(root, file))
                    except Exception:
                        pass


@pytest.fixture
def mock_email_backend(settings):
    """Configure Django to use the in-memory email backend for testing."""
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    return settings
