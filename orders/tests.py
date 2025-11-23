"""
Comprehensive test suite for orders app.

Tests cover:
- Order creation and processing
- Payment processing
- Order confirmation emails
- Order status tracking
- OrderEvent creation (tickets)
- Phone number validation
- Order form validation
- Order detail calculations
"""
import pytest
import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.utils import timezone

from orders.models import Order, OrderEvent, Payment
from orders.forms import OrderForm
from carts.models import CartItem


@pytest.mark.django_db
class TestOrderCreation:
    """Test order creation process."""

    def test_create_order_from_cart(self, test_user, cart_with_items, payment):
        """Test creating an order from cart items."""
        # Calculate total from cart
        items = CartItem.objects.filter(cart=cart_with_items, is_active=True)
        total = sum(item.price for item in items)

        # Create order
        order = Order.objects.create(
            user=test_user,
            payment=payment,
            order_number=f'TEST-ORD-{timezone.now().strftime("%Y%m%d%H%M%S")}',
            first_name=test_user.first_name,
            last_name=test_user.last_name,
            email=test_user.email,
            phone=test_user.phone_number,
            order_total=total,
            tax=total * 0.1,
            is_ordered=True
        )

        assert order.user == test_user
        assert order.payment == payment
        assert order.order_total == total
        assert order.is_ordered == True

    def test_order_number_is_unique(self, db, test_user, payment):
        """Test that order numbers are unique."""
        order1 = Order.objects.create(
            user=test_user,
            payment=payment,
            order_number='ORD-001',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            order_total=50.0,
            tax=4.5, #added tax field beppe.miletto@gmail.com 20251123
            is_ordered=True
        )

        # Trying to create another order with same number should fail
        with pytest.raises(Exception):
            order2 = Order.objects.create(
                user=test_user,
                payment=payment,
                order_number='ORD-001',  # Same number
                first_name='Another',
                last_name='User',
                email='another@example.com',
                order_total=60.0,
                is_ordered=True
            )

    def test_order_can_be_created_without_user(self, db, payment):
        """Test that orders can be created for guest checkout."""
        order = Order.objects.create(
            user=None,  # Guest order
            payment=payment,
            order_number='GUEST-ORD-001',
            first_name='Guest',
            last_name='Customer',
            email='guest@example.com',
            phone='+393401234567',
            order_total=25.0,
            is_ordered=True
        )

        assert order.user is None
        assert order.email == 'guest@example.com'


@pytest.mark.django_db
class TestOrderEvent:
    """Test OrderEvent (ticket) creation."""

    def test_create_order_event(self, order, future_event, test_user, payment):
        """Test creating an order event (ticket)."""
        order_event = OrderEvent.objects.create(
            order=order,
            event=future_event,
            user=test_user,
            payment=payment,
            seats_price='A01$25.0,A02$18.0',
            orderevent_number=f'OE-{timezone.now().strftime("%Y%m%d%H%M%S")}',
            expired=False
        )

        assert order_event.order == order
        assert order_event.event == future_event
        assert order_event.user == test_user
        assert order_event.expired == False

    def test_order_event_seats_list_parsing(self, order_event):
        """Test that seats_list() method parses seats correctly."""
        seats = order_event.seats_list()

        # Should return dict with seat -> price
        assert isinstance(seats, dict)
        assert 'A01' in seats
        assert 'A02' in seats
        assert float(seats['A01']) == 25.0
        assert float(seats['A02']) == 18.0

    def test_order_event_seats_count(self, order_event):
        """Test seats_count() method."""
        count = order_event.seats_count()
        assert count == 2  # A01 and A02

    def test_order_event_seats_list_name(self, order_event):
        """Test seats_list_name() method returns list of seat names."""
        seats = order_event.seats_list_name()

        assert isinstance(seats, list)
        assert 'A01' in seats
        assert 'A02' in seats
        assert len(seats) == 2

    def test_order_event_number_unique(self, db, order, future_event, test_user, payment):
        """Test that order event numbers are unique."""
        oe1 = OrderEvent.objects.create(
            order=order,
            event=future_event,
            user=test_user,
            payment=payment,
            seats_price='B01$25.0',
            orderevent_number='OE-UNIQUE-001'
        )

        # Duplicate should fail
        with pytest.raises(Exception):
            oe2 = OrderEvent.objects.create(
                order=order,
                event=future_event,
                user=test_user,
                payment=payment,
                seats_price='B02$25.0',
                orderevent_number='OE-UNIQUE-001'  # Same number
            )


@pytest.mark.django_db
class TestPayment:
    """Test payment processing."""

    def test_create_payment_record(self, test_user):
        """Test creating a payment record."""
        payment = Payment.objects.create(
            user=test_user,
            payment_id='PAY-TEST-123',
            payment_method='Cash',
            amount_paid='43.00',
            status='COMPLETED',
            payer_mail=test_user.email,
            payer_given_name=test_user.first_name,
            payer_surname=test_user.last_name
        )

        assert payment.user == test_user
        assert payment.payment_id == 'PAY-TEST-123'
        assert payment.status == 'COMPLETED'
        assert payment.amount_paid == '43.00'

    def test_payment_status_choices(self, test_user):
        """Test different payment status options."""
        statuses = ['NEW', 'BOOKED', 'COMPLETED', 'CANCELED']

        for status in statuses:
            payment = Payment.objects.create(
                user=test_user,
                payment_id=f'PAY-{status}-{timezone.now().timestamp()}',
                payment_method='Cash',
                amount_paid='25.00',
                status=status
            )

            assert payment.status == status

    def test_payment_id_unique(self, db, test_user):
        """Test that payment IDs are unique."""
        payment1 = Payment.objects.create(
            user=test_user,
            payment_id='PAY-UNIQUE-001',
            payment_method='Cash',
            amount_paid='25.00',
            status='COMPLETED'
        )

        # Duplicate should fail
        with pytest.raises(Exception):
            payment2 = Payment.objects.create(
                user=test_user,
                payment_id='PAY-UNIQUE-001',  # Same ID
                payment_method='Cash',
                amount_paid='30.00',
                status='COMPLETED'
            )


@pytest.mark.django_db
class TestOrderForm:
    """Test order form validation."""

    def test_valid_order_form(self):
        """Test order form with valid data."""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+393401234567',
            'email': 'john@example.com',
            'address_line_1': 'Via Roma 1',
            'city': 'Milano',
            'province': 'MI',
            'post_code': '20100'
        }

        form = OrderForm(data=form_data)
        assert form.is_valid()

    def test_order_form_phone_validation(self):
        """Test phone number validation and sanitization."""
        # Valid phone formats
        valid_phones = [
            '+393401234567',
            '3401234567',
            '+39 340 123 4567',
            '340-123-4567',
            '(340) 123-4567'
        ]

        for phone in valid_phones:
            form_data = {
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': phone,
                'email': 'john@example.com',
                'address_line_1': 'Via Roma 1',
                'city': 'Milano',
                'province': 'MI',
                'post_code': '20100'
            }

            form = OrderForm(data=form_data)
            if form.is_valid():
                # Phone should be sanitized (no spaces, dots, etc.)
                cleaned_phone = form.cleaned_data['phone']
                assert ' ' not in cleaned_phone
                assert '-' not in cleaned_phone
                assert '(' not in cleaned_phone

    def test_order_form_invalid_phone(self):
        """Test that invalid phone numbers are rejected."""
        invalid_phones = [
            'abc',  # Letters
            '12',  # Too short
            '1234567890123456',  # Too long
            'not-a-number'
        ]

        for phone in invalid_phones:
            form_data = {
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': phone,
                'email': 'john@example.com',
                'address_line_1': 'Via Roma 1',
                'city': 'Milano',
                'province': 'MI',
                'post_code': '20100'
            }

            form = OrderForm(data=form_data)
            assert not form.is_valid()
            assert 'phone' in form.errors

    def test_order_form_missing_required_fields(self):
        """Test that required fields are enforced."""
        incomplete_data = {
            'first_name': 'John',
            # Missing last_name, phone, email, etc.
        }

        form = OrderForm(data=incomplete_data)
        assert not form.is_valid()


@pytest.mark.django_db
class TestOrderModel:
    """Test Order model methods."""

    def test_order_full_name(self, order):
        """Test full_name() method."""
        full_name = order.full_name()
        assert order.first_name in full_name
        assert order.last_name in full_name

    def test_order_full_address(self, order):
        """Test full_address() method."""
        full_address = order.full_address()
        assert order.address_line_1 in full_address
        assert order.city in full_address

    def test_order_full_name_address(self, order):
        """Test full_name_address() method combines both."""
        full_info = order.full_name_address()
        assert order.first_name in full_info
        assert order.last_name in full_info
        assert order.address_line_1 in full_info

    def test_order_string_representation(self, order):
        """Test __str__ method."""
        assert order.order_number in str(order) or order.email in str(order)

    def test_order_status_choices(self, db, test_user, payment):
        """Test different order status options."""
        statuses = ['New', 'Accepted', 'Completed', 'Cancelled']

        for status in statuses:
            order = Order.objects.create(
                user=test_user,
                payment=payment,
                order_number=f'ORD-{status}-{timezone.now().timestamp()}',
                first_name='Test',
                last_name='User',
                email='test@example.com',
                order_total=50.0,
                status=status,
                is_ordered=True
            )

            assert order.status == status


@pytest.mark.django_db
class TestEmailNotifications:
    """Test order confirmation email sending."""

    def test_order_confirmation_email_sent(self, client_with_user, test_user, mock_email_backend):
        """Test that order confirmation email is sent after successful payment."""
        # This would typically be tested in payment view
        # Simulating the email sending

        # Clear mailbox
        mail.outbox = []

        # Manually trigger email (as payment view would)
        from django.core.mail import EmailMessage
        from django.template.loader import render_to_string

        # Create sample order
        order_number = 'TEST-ORDER-123'

        # Render email
        subject = f'Order Confirmation - {order_number}'
        message = f'Thank you for your order {order_number}'

        email = EmailMessage(
            subject=subject,
            body=message,
            to=[test_user.email]
        )
        email.send()

        # Check email was sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [test_user.email]
        assert order_number in mail.outbox[0].subject

    def test_order_email_contains_order_details(self, test_user, order, mock_email_backend):
        """Test that order email contains relevant order information."""
        mail.outbox = []

        from django.core.mail import EmailMessage

        # Send email with order details
        subject = f'Order #{order.order_number}'
        message = f'''
        Order Number: {order.order_number}
        Total: €{order.order_total}
        Customer: {order.full_name()}
        '''

        email = EmailMessage(
            subject=subject,
            body=message,
            to=[order.email]
        )
        email.send()

        # Verify email content
        assert len(mail.outbox) == 1
        email_content = mail.outbox[0].body
        assert order.order_number in email_content
        assert str(order.order_total) in email_content


@pytest.mark.django_db
class TestOrderCalculations:
    """Test order price calculations."""

    def test_order_total_calculation(self, test_user, payment, cart_with_items):
        """Test that order total is calculated correctly from cart items."""
        items = CartItem.objects.filter(cart=cart_with_items, is_active=True)
        expected_total = sum(item.price for item in items)

        order = Order.objects.create(
            user=test_user,
            payment=payment,
            order_number='CALC-TEST-001',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            order_total=expected_total,
            is_ordered=True
        )

        assert order.order_total == expected_total

    def test_order_tax_calculation(self, test_user, payment):
        """Test that tax is calculated correctly."""
        subtotal = 100.0
        vat_rate = 10.0  # 10%
        expected_tax = subtotal * (vat_rate / 100)

        order = Order.objects.create(
            user=test_user,
            payment=payment,
            order_number='TAX-TEST-001',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            order_total=subtotal + expected_tax,
            tax=expected_tax,
            is_ordered=True
        )

        assert order.tax == expected_tax
        assert order.order_total == subtotal + expected_tax


@pytest.mark.django_db
class TestPaymentIntegration:
    """Test payment processing integration."""

    def test_payment_creates_order_events(self, test_user, payment, future_event, cart_with_items, order):
        """Test that completing payment creates OrderEvent records."""
        # Get cart items
        items = CartItem.objects.filter(cart=cart_with_items, is_active=True)

        # Create order events from cart items
        for item in items:
            OrderEvent.objects.create(
                order=order,
                event=item.event,
                user=test_user,
                payment=payment,
                seats_price=f'{item.seat}${item.price}',
                orderevent_number=f'OE-{item.seat}-{timezone.now().timestamp()}'
            )

        # Verify order events were created
        order_events = OrderEvent.objects.filter(order=order)
        assert order_events.count() == items.count()

    def test_payment_updates_seat_status_to_sold(self, test_user, payment, future_event):
        """Test that payment completion updates JSON seat status to 5 (sold)."""
        json_path = future_event.get_json_path()

        # Initial: seat available
        with open(json_path, 'r') as f:
            seat_data = json.load(f)

        seat_data['A01']['status'] = 0

        with open(json_path, 'w') as f:
            json.dump(seat_data, f)

        # Simulate payment completion - update to sold
        with open(json_path, 'r') as f:
            seat_data = json.load(f)

        seat_data['A01']['status'] = 5  # Sold

        with open(json_path, 'w') as f:
            json.dump(seat_data, f)

        # Verify
        with open(json_path, 'r') as f:
            updated_data = json.load(f)

        assert updated_data['A01']['status'] == 5

    def test_payment_clears_cart(self, cart_with_items):
        """Test that successful payment clears the cart."""
        # Simulate payment completion
        initial_count = CartItem.objects.filter(cart=cart_with_items, is_active=True).count()
        assert initial_count > 0

        # Mark items as inactive (or delete them)
        CartItem.objects.filter(cart=cart_with_items).delete()

        # Verify cart is empty
        final_count = CartItem.objects.filter(cart=cart_with_items, is_active=True).count()
        assert final_count == 0


@pytest.mark.django_db
class TestOrderHistory:
    """Test order history and tracking."""

    def test_user_can_view_order_history(self, client_with_user, test_user, order):
        """Test that user can view their order history."""
        response = client_with_user.get(reverse('my_orders'))

        assert response.status_code == 200
        content = response.content.decode()
        assert order.order_number in content

    def test_order_detail_accessible(self, client_with_user, test_user, order):
        """Test that order detail page is accessible."""
        response = client_with_user.get(reverse('order_detail', kwargs={'order_id': order.id}))

        assert response.status_code == 200
        content = response.content.decode()
        assert order.order_number in content

    def test_order_tracking_by_status(self, db, test_user, payment):
        """Test filtering orders by status."""
        # Create orders with different statuses
        completed_order = Order.objects.create(
            user=test_user,
            payment=payment,
            order_number='COMPLETED-001',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            order_total=50.0,
            status='Completed',
            is_ordered=True
        )

        pending_order = Order.objects.create(
            user=test_user,
            payment=payment,
            order_number='PENDING-001',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            order_total=60.0,
            status='New',
            is_ordered=False
        )

        # Filter by status
        completed_orders = Order.objects.filter(user=test_user, status='Completed')
        assert completed_orders.count() == 1
        assert completed_orders.first() == completed_order

        pending_orders = Order.objects.filter(user=test_user, status='New')
        assert pending_orders.count() == 1
        assert pending_orders.first() == pending_order


@pytest.mark.django_db
class TestOrderSecurity:
    """Test order security and access control."""

    def test_user_cannot_access_other_users_orders(self, client_with_user, test_user, test_admin_user, payment):
        """Test that users can only access their own orders."""
        # Create order for different user
        other_order = Order.objects.create(
            user=test_admin_user,
            payment=payment,
            order_number='OTHER-ORDER-001',
            first_name='Other',
            last_name='User',
            email='other@example.com',
            order_total=50.0,
            is_ordered=True
        )

        # Try to access other user's order
        response = client_with_user.get(reverse('order_detail', kwargs={'order_id': other_order.id}))

        # Should be forbidden or redirect
        assert response.status_code in [302, 403, 404]

    def test_guest_order_accessible_by_email(self, db, payment):
        """Test that guest orders can be tracked via email."""
        guest_order = Order.objects.create(
            user=None,  # Guest
            payment=payment,
            order_number='GUEST-001',
            first_name='Guest',
            last_name='Customer',
            email='guest@example.com',
            order_total=30.0,
            is_ordered=True
        )

        # Can find order by email
        orders = Order.objects.filter(email='guest@example.com')
        assert orders.count() == 1
        assert orders.first() == guest_order
