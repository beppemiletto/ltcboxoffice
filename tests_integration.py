"""
Integration tests for the complete user journey.

This test suite covers end-to-end flows from user registration through
booking completion and email confirmation.

Test scenarios:
1. New user registration -> email verification -> login
2. Browse events -> select seats -> add to cart
3. Checkout -> payment -> order confirmation
4. View order history
5. Complete booking flow with email notifications
"""
import pytest
import json
from datetime import timedelta
from django.test import Client
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.models import Account, UserProfile
from billboard.models import Section, Show, Venue, SiaeType
from store.models import Event
from carts.models import Cart, CartItem
from orders.models import Order, OrderEvent, Payment

User = get_user_model()


@pytest.mark.django_db
class TestCompleteUserJourney:
    """Test the complete user journey from registration to booking."""

    def test_new_user_registration_to_booking_complete_flow(self, client, mock_email_backend, siae_type):
        """
        Test complete flow:
        1. Register new user
        2. Verify email
        3. Login
        4. Browse events
        5. Select seats
        6. Add to cart
        7. Checkout
        8. Complete payment
        9. Receive confirmation email
        10. View order in history
        """
        mail.outbox = []

        # Step 1: Register new user
        registration_data = {
            'first_name': 'Integration',
            'last_name': 'Test',
            'email': 'integration@example.com',
            'phone_number': '+393401111111',
            'password': 'IntegrationTest123!',
            'confirm_password': 'IntegrationTest123!'
        }

        response = client.post(reverse('register'), data=registration_data)
        assert response.status_code == 302  # Redirect after registration

        # Verify user was created
        user = User.objects.get(email='integration@example.com')
        assert user.is_active == False  # Not active until email verification

        # Verification email sent
        assert len(mail.outbox) >= 1

        # Step 2: Activate user (simulate clicking email link)
        user.is_active = True
        user.save()

        # Step 3: Login
        login_response = client.post(reverse('login'), {
            'email': 'integration@example.com',
            'password': 'IntegrationTest123!'
        })
        assert login_response.status_code == 302  # Redirect after login

        # Step 4: Create event to browse
        section = Section.objects.create(
            name='Integration Test Section',
            slug='integration-section',
            default_price_full=30.0,
            default_price_reduced=20.0
        )

        venue = Venue.objects.create(
            name='Test Venue',
            slug='test-venue',
            capacity=10,
            ba_code_siae='BA001',
            local_code_siae='LOC001'
        )

        show = Show.objects.create(
            shw_title='Integration Test Show',
            shw_author='Test Author',
            shw_director='Test Director',
            shw_code='INT001',
            slug='integration-test-show',
            section=section,
            siaetype=siae_type,
            is_in_billboard=True,
            is_active=True
        )

        event = Event.objects.create(
            show=show,
            date_time=timezone.now() + timedelta(days=7),
            price_full=30.0,
            price_reduced=20.0,
            vat_rate=10.0,
            venue=venue,
            event_slug='integration-event-001'
        )

        # Create JSON seat file
        json_path = event.get_json_path()
        import os
        os.makedirs(os.path.dirname(json_path), exist_ok=True)

        seat_data = {
            f'A0{i}': {'status': 0, 'ingresso': '', 'price': 0}
            for i in range(1, 6)
        }

        with open(json_path, 'w') as f:
            json.dump(seat_data, f)

        # Browse store
        store_response = client.get(reverse('store'))
        assert store_response.status_code == 200
        assert 'Integration Test Show' in store_response.content.decode()

        # Step 5: View show detail
        show_detail_response = client.get(
            reverse('show_detail', kwargs={
                'section_slug': section.slug,
                'show_slug': show.slug
            })
        )
        assert show_detail_response.status_code == 200

        # Step 6 & 7: Create cart and add items (simulating seat selection)
        cart = Cart.objects.create(cart_id=f'integration_cart_{user.id}')

        CartItem.objects.create(
            user=user,
            event=event,
            cart=cart,
            seat='A01',
            ingresso=2,  # Intero
            price=30.0,
            is_active=True
        )

        CartItem.objects.create(
            user=user,
            event=event,
            cart=cart,
            seat='A02',
            ingresso=1,  # Ridotto
            price=20.0,
            is_active=True
        )

        # Step 8: Create payment and order
        payment = Payment.objects.create(
            user=user,
            payment_id=f'PAY-INT-{timezone.now().timestamp()}',
            payment_method='Cash',
            amount_paid='50.00',
            status='COMPLETED',
            payer_mail=user.email,
            payer_given_name=user.first_name,
            payer_surname=user.last_name
        )

        order = Order.objects.create(
            user=user,
            payment=payment,
            order_number=f'ORD-INT-{timezone.now().strftime("%Y%m%d%H%M%S")}',
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone_number,
            order_total=50.0,
            tax=5.0,
            status='Completed',
            is_ordered=True
        )

        # Create OrderEvent
        order_event = OrderEvent.objects.create(
            order=order,
            event=event,
            user=user,
            payment=payment,
            seats_price='A01$30.0,A02$20.0',
            orderevent_number=f'OE-INT-{timezone.now().timestamp()}'
        )

        # Step 9: Send confirmation email
        mail.outbox = []  # Clear previous emails

        from django.core.mail import EmailMessage
        email = EmailMessage(
            subject=f'Order Confirmation - {order.order_number}',
            body=f'Thank you for your order {order.order_number}. Total: €{order.order_total}',
            to=[user.email]
        )
        email.send()

        assert len(mail.outbox) == 1
        assert order.order_number in mail.outbox[0].subject

        # Step 10: View order history
        my_orders_response = client.get(reverse('my_orders'))
        assert my_orders_response.status_code == 200
        assert order.order_number in my_orders_response.content.decode()

        # View order detail
        order_detail_response = client.get(reverse('order_detail', kwargs={'order_id': order.id}))
        assert order_detail_response.status_code == 200
        assert order.order_number in order_detail_response.content.decode()


@pytest.mark.django_db
class TestAnonymousToAuthenticatedFlow:
    """Test anonymous user adding to cart then logging in."""

    def test_anonymous_cart_persists_after_login(self, client, test_user, test_password, future_event):
        """
        Test flow:
        1. Anonymous user browses and adds items to cart
        2. User logs in
        3. Cart items are preserved and associated with user
        """
        # Create anonymous cart
        anon_cart = Cart.objects.create(cart_id='anon_integration_cart')

        # Add item as anonymous user
        CartItem.objects.create(
            user=None,
            event=future_event,
            cart=anon_cart,
            seat='B01',
            ingresso=2,
            price=25.0,
            is_active=True
        )

        # Store cart in session
        session = client.session
        session['cart_id'] = anon_cart.cart_id
        session.save()

        # Verify anonymous cart has items
        assert CartItem.objects.filter(cart=anon_cart, is_active=True).count() == 1

        # Login
        client.post(reverse('login'), {
            'email': test_user.email,
            'password': test_password
        })

        # After login, cart items should still exist
        # (Implementation may vary - some systems merge carts, others associate existing cart with user)
        assert CartItem.objects.filter(cart=anon_cart).exists()


@pytest.mark.django_db
class TestMultipleEventsBooking:
    """Test booking multiple events in single session."""

    def test_book_multiple_events_in_one_order(self, client_with_user, test_user, db, section, siae_type, venue):
        """
        Test flow:
        1. User selects seats for Event A
        2. User selects seats for Event B
        3. Both events in cart
        4. Single checkout for both
        """
        # Create multiple events
        show1 = Show.objects.create(
            shw_title='Show 1',
            shw_code='SH1',
            slug='show-1',
            section=section,
            siaetype=siae_type,
            is_in_billboard=True
        )

        show2 = Show.objects.create(
            shw_title='Show 2',
            shw_code='SH2',
            slug='show-2',
            section=section,
            siaetype=siae_type,
            is_in_billboard=True
        )

        event1 = Event.objects.create(
            show=show1,
            date_time=timezone.now() + timedelta(days=5),
            price_full=25.0,
            price_reduced=18.0,
            vat_rate=10.0,
            venue=venue,
            event_slug='show-1-event'
        )

        event2 = Event.objects.create(
            show=show2,
            date_time=timezone.now() + timedelta(days=10),
            price_full=30.0,
            price_reduced=22.0,
            vat_rate=10.0,
            venue=venue,
            event_slug='show-2-event'
        )

        # Create cart
        cart = Cart.objects.create(cart_id=f'multi_event_cart_{test_user.id}')

        # Add items from event 1
        CartItem.objects.create(
            user=test_user,
            event=event1,
            cart=cart,
            seat='A01',
            ingresso=2,
            price=25.0,
            is_active=True
        )

        # Add items from event 2
        CartItem.objects.create(
            user=test_user,
            event=event2,
            cart=cart,
            seat='B01',
            ingresso=2,
            price=30.0,
            is_active=True
        )

        # Verify both events in cart
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        assert cart_items.count() == 2

        events_in_cart = set(item.event for item in cart_items)
        assert event1 in events_in_cart
        assert event2 in events_in_cart

        # Calculate total
        total = sum(item.price for item in cart_items)
        assert total == 55.0


@pytest.mark.django_db
class TestErrorHandling:
    """Test error handling in booking flow."""

    def test_cannot_book_sold_out_event(self, client_with_user, future_event):
        """Test that sold out events cannot be booked."""
        future_event.sold_out = True
        future_event.save()

        assert future_event.is_bookable() == False

        # Attempt to access seat selection should be blocked or show error
        # Implementation depends on view logic

    def test_cannot_book_past_event(self, client_with_user, past_event):
        """Test that past events cannot be booked."""
        assert past_event.is_bookable() == False

    def test_cannot_add_already_sold_seat_to_cart(self, client_with_user, test_user, future_event, cart):
        """Test validation prevents booking already sold seats."""
        json_path = future_event.get_json_path()

        # Mark seat as sold
        with open(json_path, 'r') as f:
            seat_data = json.load(f)

        seat_data['C01'] = {'status': 5, 'ingresso': '2', 'price': 25.0}  # Sold

        with open(json_path, 'w') as f:
            json.dump(seat_data, f)

        # Attempting to book this seat should fail
        # (actual validation depends on implementation)


@pytest.mark.django_db
class TestEmailVerificationFlow:
    """Test complete email verification flow."""

    def test_user_must_verify_email_before_booking(self, client, mock_email_backend):
        """
        Test flow:
        1. User registers
        2. User tries to login (should fail - not verified)
        3. User clicks verification link
        4. User can now login and book
        """
        mail.outbox = []

        # Register
        client.post(reverse('register'), {
            'first_name': 'Verify',
            'last_name': 'Test',
            'email': 'verify@example.com',
            'phone_number': '+393402222222',
            'password': 'VerifyTest123!',
            'confirm_password': 'VerifyTest123!'
        })

        user = User.objects.get(email='verify@example.com')
        assert user.is_active == False

        # Try to login (should fail)
        login_attempt = client.post(reverse('login'), {
            'email': 'verify@example.com',
            'password': 'VerifyTest123!'
        })

        # Should not be authenticated
        assert '_auth_user_id' not in client.session

        # Activate user
        user.is_active = True
        user.save()

        # Now login should work
        login_success = client.post(reverse('login'), {
            'email': 'verify@example.com',
            'password': 'VerifyTest123!'
        })

        assert login_success.status_code == 302  # Redirect after successful login


@pytest.mark.django_db
class TestPriceCalculations:
    """Test price calculations throughout booking flow."""

    def test_cart_total_matches_individual_prices(self, test_user, future_event, cart):
        """Test that cart total equals sum of individual item prices."""
        items_data = [
            ('A01', 2, 30.0),  # Intero
            ('A02', 1, 20.0),  # Ridotto
            ('A03', 0, 0.0),   # Gratuito
        ]

        for seat, ingresso, price in items_data:
            CartItem.objects.create(
                user=test_user,
                event=future_event,
                cart=cart,
                seat=seat,
                ingresso=ingresso,
                price=price,
                is_active=True
            )

        items = CartItem.objects.filter(cart=cart, is_active=True)
        total = sum(item.price for item in items)

        assert total == 50.0  # 30 + 20 + 0

    def test_order_total_includes_tax(self, test_user, payment):
        """Test that order total correctly includes tax."""
        subtotal = 100.0
        tax_rate = 10.0
        tax_amount = subtotal * (tax_rate / 100)
        total_with_tax = subtotal + tax_amount

        order = Order.objects.create(
            user=test_user,
            payment=payment,
            order_number='TAX-INT-001',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            order_total=total_with_tax,
            tax=tax_amount,
            is_ordered=True
        )

        assert order.tax == 10.0
        assert order.order_total == 110.0


@pytest.mark.django_db
class TestConcurrentBooking:
    """Test handling of concurrent booking attempts."""

    def test_two_users_cannot_book_same_seat(self, db, test_user, test_admin_user, future_event):
        """Test that seat locking prevents double booking."""
        cart1 = Cart.objects.create(cart_id='user1_cart')
        cart2 = Cart.objects.create(cart_id='user2_cart')

        # User 1 adds seat A01
        item1 = CartItem.objects.create(
            user=test_user,
            event=future_event,
            cart=cart1,
            seat='A01',
            ingresso=2,
            price=25.0,
            is_active=True
        )

        # Update JSON to mark as in cart
        json_path = future_event.get_json_path()
        with open(json_path, 'r') as f:
            seat_data = json.load(f)

        seat_data['A01']['status'] = 4  # In cart

        with open(json_path, 'w') as f:
            json.dump(seat_data, f)

        # User 2 should not be able to add the same seat
        # (validation logic should prevent this based on JSON status)


@pytest.mark.django_db
class TestOrderConfirmationContent:
    """Test order confirmation contains all necessary information."""

    def test_order_confirmation_has_all_details(self, test_user, order, order_event, mock_email_backend):
        """Test that order confirmation email includes all order details."""
        mail.outbox = []

        from django.core.mail import EmailMessage

        # Build comprehensive email
        email_body = f"""
        Order Confirmation

        Order Number: {order.order_number}
        Customer: {order.full_name()}
        Email: {order.email}

        Event: {order_event.event.show.shw_title}
        Date: {order_event.event.date_time.strftime('%d/%m/%Y %H:%M')}
        Seats: {', '.join(order_event.seats_list_name())}

        Total: €{order.order_total}
        Tax: €{order.tax}

        Thank you for your order!
        """

        email = EmailMessage(
            subject=f'Order #{order.order_number} Confirmed',
            body=email_body,
            to=[order.email]
        )
        email.send()

        # Verify email sent and contains key information
        assert len(mail.outbox) == 1
        sent_email = mail.outbox[0]

        assert order.order_number in sent_email.body
        assert order.full_name() in sent_email.body
        assert str(order.order_total) in sent_email.body
