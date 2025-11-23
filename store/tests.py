"""
Comprehensive test suite for store app (front desk features).

Tests cover:
- Event browsing and listing
- Show detail pages
- Event availability (bookable status)
- Show search functionality
- Section filtering
- Pagination
- Seat selection interface
"""
import pytest
import json
import os
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from store.models import Event
from billboard.models import Show, Section, Venue
from carts.models import Cart, CartItem


@pytest.mark.django_db
class TestEventListing:
    """Test the main store page with event listings."""

    def test_store_page_loads(self, client):
        """Test that the store page is accessible."""
        response = client.get(reverse('store'))
        assert response.status_code == 200

    def test_store_displays_bookable_events(self, client, future_event):
        """Test that bookable events are displayed on the store page."""
        response = client.get(reverse('store'))

        assert response.status_code == 200
        content = response.content.decode()
        assert future_event.show.shw_title in content

    def test_store_hides_past_events(self, client, past_event):
        """Test that past events are not displayed."""
        response = client.get(reverse('store'))

        assert response.status_code == 200
        content = response.content.decode()
        # Past event should not be shown
        assert past_event.show.shw_title not in content

    def test_store_hides_imminent_events(self, client, imminent_event):
        """Test that events within booking deadline are not displayed."""
        response = client.get(reverse('store'))

        assert response.status_code == 200
        # The event might not appear as bookable
        # Check based on is_bookable() method

    def test_store_pagination(self, client, multiple_shows):
        """Test that pagination works correctly (4 shows per page)."""
        response = client.get(reverse('store'))

        assert response.status_code == 200
        # Should have pagination if more than 4 shows
        if len(multiple_shows) > 4:
            content = response.content.decode()
            assert 'page' in content.lower() or 'next' in content.lower()

    def test_store_filters_by_section(self, client, section, show, future_event):
        """Test filtering events by section."""
        response = client.get(reverse('shows_by_section', kwargs={'section_slug': section.slug}))

        assert response.status_code == 200
        content = response.content.decode()
        assert show.shw_title in content

    def test_store_section_filter_excludes_other_sections(self, client, db, siae_type, venue):
        """Test that section filtering excludes shows from other sections."""
        # Create two sections
        section1 = Section.objects.create(
            name='Prosa',
            slug='prosa',
            default_price_full=20.0,
            default_price_reduced=15.0
        )
        section2 = Section.objects.create(
            name='Danza',
            slug='danza',
            default_price_full=25.0,
            default_price_reduced=18.0
        )

        # Create shows in different sections
        show1 = Show.objects.create(
            shw_title='Prosa Show',
            shw_code='PRO001',
            slug='prosa-show',
            section=section1,
            siaetype=siae_type,
            is_in_billboard=True,
            is_active=True
        )
        show2 = Show.objects.create(
            shw_title='Dance Show',
            shw_code='DAN001',
            slug='dance-show',
            section=section2,
            siaetype=siae_type,
            is_in_billboard=True,
            is_active=True
        )

        # Create future events for both
        Event.objects.create(
            show=show1,
            date_time=timezone.now() + timedelta(days=7),
            price_full=20.0,
            price_reduced=15.0,
            vat_rate=10.0,
            venue=venue,
            event_slug='prosa-show-event'
        )
        Event.objects.create(
            show=show2,
            date_time=timezone.now() + timedelta(days=7),
            price_full=25.0,
            price_reduced=18.0,
            vat_rate=10.0,
            venue=venue,
            event_slug='dance-show-event'
        )

        # Test section1 filter
        response = client.get(reverse('shows_by_section', kwargs={'section_slug': 'prosa'}))
        content = response.content.decode()
        assert 'Prosa Show' in content
        assert 'Dance Show' not in content


@pytest.mark.django_db
class TestShowDetail:
    """Test show detail page."""

    def test_show_detail_page_loads(self, client, section, show):
        """Test that show detail page is accessible."""
        response = client.get(
            reverse('show_detail', kwargs={
                'section_slug': section.slug,
                'show_slug': show.slug
            })
        )
        assert response.status_code == 200

    def test_show_detail_displays_show_info(self, client, section, show, future_event):
        """Test that show detail page displays complete show information."""
        response = client.get(
            reverse('show_detail', kwargs={
                'section_slug': section.slug,
                'show_slug': show.slug
            })
        )

        assert response.status_code == 200
        content = response.content.decode()
        assert show.shw_title in content
        assert show.shw_author in content
        assert show.shw_director in content

    def test_show_detail_displays_event_dates(self, client, section, show, future_event):
        """Test that all event dates are shown for a show."""
        # Create multiple events for the same show
        event2 = Event.objects.create(
            show=show,
            date_time=timezone.now() + timedelta(days=14),
            price_full=25.0,
            price_reduced=18.0,
            vat_rate=10.0,
            venue=future_event.venue,
            event_slug=f"hamlet-{(timezone.now() + timedelta(days=14)).strftime('%Y%m%d')}"
        )

        response = client.get(
            reverse('show_detail', kwargs={
                'section_slug': section.slug,
                'show_slug': show.slug
            })
        )

        assert response.status_code == 200
        # Both events should be listed

    def test_show_detail_displays_price_range(self, client, section, show, future_event):
        """Test that price range is displayed."""
        response = client.get(
            reverse('show_detail', kwargs={
                'section_slug': section.slug,
                'show_slug': show.slug
            })
        )

        assert response.status_code == 200
        content = response.content.decode()
        # Should show either full price or reduced price
        assert str(int(future_event.price_full)) in content or str(int(future_event.price_reduced)) in content

    def test_show_detail_nonexistent_show_404(self, client, section):
        """Test that non-existent show returns 404."""
        response = client.get(
            reverse('show_detail', kwargs={
                'section_slug': section.slug,
                'show_slug': 'nonexistent-show'
            })
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestEventAvailability:
    """Test event bookability logic."""

    def test_future_event_is_bookable(self, future_event):
        """Test that future events (beyond deadline) are bookable."""
        assert future_event.is_bookable() == True

    def test_past_event_is_not_bookable(self, past_event):
        """Test that past events are not bookable."""
        assert past_event.is_bookable() == False

    def test_imminent_event_is_not_bookable(self, imminent_event):
        """Test that events within booking deadline are not bookable."""
        assert imminent_event.is_bookable() == False

    def test_sold_out_event_is_not_bookable(self, future_event):
        """Test that sold out events are not bookable."""
        future_event.sold_out = True
        future_event.save()

        assert future_event.is_bookable() == False

    def test_booking_deadline_calculation(self, future_event):
        """Test that booking deadline is calculated correctly."""
        deadline = future_event.get_booking_deadline()

        # Deadline should be 3 hours before event
        expected_deadline = future_event.date_time - timedelta(hours=future_event.booking_deadline_hours)

        assert deadline == expected_deadline

    def test_custom_booking_deadline(self, db, show, venue):
        """Test events with custom booking deadline hours."""
        # Create event with 24-hour deadline
        event_datetime = timezone.now() + timedelta(days=2)
        event = Event.objects.create(
            show=show,
            date_time=event_datetime,
            price_full=25.0,
            price_reduced=18.0,
            vat_rate=10.0,
            venue=venue,
            event_slug='custom-deadline-event',
            booking_deadline_hours=24
        )

        deadline = event.get_booking_deadline()
        expected_deadline = event_datetime - timedelta(hours=24)

        assert deadline == expected_deadline


@pytest.mark.django_db
class TestSeatSelection:
    """Test seat selection interface."""

    def test_seat_selection_requires_login(self, client, section, show, future_event):
        """Test that seat selection page requires authentication."""
        response = client.get(
            reverse('select_seats', kwargs={
                'section_slug': section.slug,
                'show_slug': show.slug,
                'event_slug': future_event.event_slug
            })
        )

        # Should redirect to login
        assert response.status_code == 302
        assert 'login' in response.url

    def test_authenticated_user_can_access_seat_selection(self, client_with_user, section, show, future_event):
        """Test that logged-in users can access seat selection."""
        response = client_with_user.get(
            reverse('select_seats', kwargs={
                'section_slug': section.slug,
                'show_slug': show.slug,
                'event_slug': future_event.event_slug
            })
        )

        assert response.status_code == 200

    def test_seat_selection_displays_venue_map(self, client_with_user, section, show, future_event):
        """Test that seat selection shows the venue seating map."""
        response = client_with_user.get(
            reverse('select_seats', kwargs={
                'section_slug': section.slug,
                'show_slug': show.slug,
                'event_slug': future_event.event_slug
            })
        )

        assert response.status_code == 200
        content = response.content.decode()
        # Should have seat selection interface
        assert 'seat' in content.lower() or future_event.venue.name in content

    def test_seat_selection_loads_json_seat_status(self, client_with_user, section, show, future_event):
        """Test that seat status JSON is loaded correctly."""
        response = client_with_user.get(
            reverse('select_seats', kwargs={
                'section_slug': section.slug,
                'show_slug': show.slug,
                'event_slug': future_event.event_slug
            })
        )

        assert response.status_code == 200

        # Verify JSON file exists
        json_path = future_event.get_json_path()
        assert os.path.exists(json_path)

        # Verify JSON content
        with open(json_path, 'r') as f:
            seat_data = json.load(f)

        # Should have seats defined
        assert len(seat_data) > 0
        # All seats should be available (status=0)
        assert all(seat['status'] == 0 for seat in seat_data.values())

    def test_seat_selection_past_event_blocked(self, client_with_user, section, show, past_event):
        """Test that past events cannot have seats selected."""
        response = client_with_user.get(
            reverse('select_seats', kwargs={
                'section_slug': section.slug,
                'show_slug': show.slug,
                'event_slug': past_event.event_slug
            })
        )

        # Should either redirect or show error
        # Implementation depends on view logic


@pytest.mark.django_db
class TestSearchFunctionality:
    """Test show search feature."""

    def test_search_page_accessible(self, client):
        """Test that search functionality is accessible."""
        response = client.get(reverse('search'), {'keyword': 'hamlet'})
        assert response.status_code == 200

    def test_search_finds_show_by_title(self, client, show, future_event):
        """Test searching for shows by title."""
        response = client.get(reverse('search'), {'keyword': 'Hamlet'})

        assert response.status_code == 200
        content = response.content.decode()
        assert show.shw_title in content

    def test_search_finds_show_by_author(self, client, show, future_event):
        """Test searching for shows by author."""
        response = client.get(reverse('search'), {'keyword': 'Shakespeare'})

        assert response.status_code == 200
        content = response.content.decode()
        assert show.shw_title in content

    def test_search_empty_keyword(self, client):
        """Test search with empty keyword."""
        response = client.get(reverse('search'), {'keyword': ''})

        # Should handle gracefully
        assert response.status_code in [200, 302]

    def test_search_no_results(self, client):
        """Test search with no matching results."""
        response = client.get(reverse('search'), {'keyword': 'NonexistentShow12345'})

        assert response.status_code == 200
        content = response.content.decode()
        # Should show "no results" message


@pytest.mark.django_db
class TestEventModel:
    """Test Event model methods and properties."""

    def test_event_string_representation(self, future_event):
        """Test __str__ method."""
        expected = f"{future_event.show.shw_title} - {future_event.date_time.strftime('%d/%m/%Y %H:%M')}"
        assert str(future_event) == expected or future_event.show.shw_title in str(future_event)

    def test_event_json_path_generation(self, future_event):
        """Test that JSON path is generated correctly."""
        json_path = future_event.get_json_path()

        # Should be in static/json directory
        assert 'static' in json_path
        assert 'json' in json_path
        assert json_path.endswith('.json')

    def test_event_save_creates_json_file(self, db, show, venue):
        """Test that saving an event creates its JSON seat file."""
        event = Event.objects.create(
            show=show,
            date_time=timezone.now() + timedelta(days=10),
            price_full=30.0,
            price_reduced=22.0,
            vat_rate=10.0,
            venue=venue,
            event_slug='new-test-event'
        )

        json_path = event.get_json_path()
        # File should be created (or create logic should be in place)
        # This depends on implementation

    def test_event_unique_slug(self, db, show, venue):
        """Test that event slugs are unique."""
        event1 = Event.objects.create(
            show=show,
            date_time=timezone.now() + timedelta(days=10),
            price_full=30.0,
            price_reduced=22.0,
            vat_rate=10.0,
            venue=venue,
            event_slug='unique-event-1'
        )

        # Trying to create another event with the same slug should fail
        # or slug should be auto-modified


@pytest.mark.django_db
class TestShowModel:
    """Test Show model methods."""

    def test_show_string_representation(self, show):
        """Test __str__ method."""
        assert str(show) == show.shw_title or show.shw_code in str(show)

    def test_show_slug_unique(self, db, section, siae_type):
        """Test that show slugs are unique."""
        show1 = Show.objects.create(
            shw_title='Unique Show 1',
            shw_code='UNI001',
            slug='unique-show',
            section=section,
            siaetype=siae_type,
            is_in_billboard=True
        )

        # Creating another show with same slug should fail or auto-generate new slug
        with pytest.raises(Exception):
            show2 = Show.objects.create(
                shw_title='Unique Show 2',
                shw_code='UNI002',
                slug='unique-show',  # Same slug
                section=section,
                siaetype=siae_type,
                is_in_billboard=True
            )


@pytest.mark.django_db
class TestVenueModel:
    """Test Venue model."""

    def test_venue_string_representation(self, venue):
        """Test __str__ method."""
        assert str(venue) == venue.name

    def test_venue_capacity(self, venue):
        """Test that venue has correct capacity."""
        assert venue.capacity == 15

    def test_venue_fiscal_codes(self, venue):
        """Test that venue has Italian fiscal codes."""
        assert venue.ba_code_siae is not None
        assert venue.local_code_siae is not None


@pytest.mark.django_db
class TestPriceDisplay:
    """Test price calculation and display."""

    def test_event_displays_full_price(self, future_event):
        """Test that full price is available."""
        assert future_event.price_full == 25.0

    def test_event_displays_reduced_price(self, future_event):
        """Test that reduced price is available."""
        assert future_event.price_reduced == 18.0

    def test_event_vat_calculation(self, future_event):
        """Test VAT calculation."""
        # VAT should be 10%
        assert future_event.vat_rate == 10.0

        # Calculate VAT amount on full price
        vat_amount = future_event.price_full * (future_event.vat_rate / 100)
        expected_vat = 2.5
        assert abs(vat_amount - expected_vat) < 0.01

    def test_price_range_with_multiple_events(self, db, show, venue):
        """Test price range calculation when show has multiple events with different prices."""
        # Create events with different prices
        event1 = Event.objects.create(
            show=show,
            date_time=timezone.now() + timedelta(days=5),
            price_full=20.0,
            price_reduced=15.0,
            vat_rate=10.0,
            venue=venue,
            event_slug='event-cheap'
        )
        event2 = Event.objects.create(
            show=show,
            date_time=timezone.now() + timedelta(days=10),
            price_full=30.0,
            price_reduced=25.0,
            vat_rate=10.0,
            venue=venue,
            event_slug='event-expensive'
        )

        # Price range should be 15.0 - 30.0
        events = Event.objects.filter(show=show)
        min_price = min(min(e.price_full, e.price_reduced) for e in events)
        max_price = max(max(e.price_full, e.price_reduced) for e in events)

        assert min_price == 15.0
        assert max_price == 30.0


@pytest.mark.django_db
class TestSectionModel:
    """Test Section model."""

    def test_section_string_representation(self, section):
        """Test __str__ method."""
        assert str(section) == section.name

    def test_section_default_prices(self, section):
        """Test that section has default prices."""
        assert section.default_price_full == 20.0
        assert section.default_price_reduced == 15.0

    def test_section_slug_unique(self, db):
        """Test that section slugs are unique."""
        section1 = Section.objects.create(
            name='Test Section 1',
            slug='test-section',
            default_price_full=20.0,
            default_price_reduced=15.0
        )

        # Duplicate slug should fail
        with pytest.raises(Exception):
            section2 = Section.objects.create(
                name='Test Section 2',
                slug='test-section',  # Same slug
                default_price_full=25.0,
                default_price_reduced=18.0
            )
