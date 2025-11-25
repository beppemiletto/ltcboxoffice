from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from .models import Show, SiaeType, Venue
import json


# Create your views here.


@staff_member_required
def api_test(request):
    """Simple test endpoint to verify billboard URLs are working"""
    return JsonResponse({
        'status': 'ok',
        'message': 'Billboard API is working',
        'urls_loaded': True
    })


@staff_member_required
def venue_config_generator(request):
    """
    Interactive venue configuration generator tool.
    Allows staff to create hall seating configurations visually.
    """
    venues = Venue.objects.all()

    context = {
        'venues': venues,
        'page_title': 'Venue Configuration Generator',
    }

    return render(request, 'billboard/venue_config_generator.html', context)


@staff_member_required
@require_http_methods(["POST"])
def generate_venue_config(request):
    """
    API endpoint to generate and download venue configuration JSON.
    Receives configuration data from the interactive editor.
    """
    try:
        # Parse the incoming configuration data
        data = json.loads(request.body)

        # Extract venue information
        venue_info = {
            "name": data.get('venue_name', ''),
            "slug": data.get('venue_slug', ''),
            "capacity": int(data.get('capacity', 0)),
            "ba_code_siae": data.get('ba_code_siae', ''),
            "local_code_siae": data.get('local_code_siae', ''),
        }

        # Extract aisles configuration (if present)
        aisles = data.get('aisles', {'horizontal': [], 'vertical': []})
        if aisles and (aisles.get('horizontal') or aisles.get('vertical')):
            venue_info['aisles'] = aisles

        # Extract rows configuration
        rows = data.get('rows', [])

        # Build the complete configuration
        config = {
            "venue": venue_info,
            "rows": rows
        }

        # Validate the configuration
        validation_errors = validate_config(config)
        if validation_errors:
            return JsonResponse({
                'success': False,
                'errors': validation_errors
            }, status=400)

        # Create the JSON response
        response = HttpResponse(
            json.dumps(config, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{venue_info["slug"]}.json"'

        return response

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
def validate_venue_config(request):
    """
    API endpoint to validate venue configuration without downloading.
    Returns validation results and statistics.
    """
    try:
        data = json.loads(request.body)

        # Build configuration
        venue_info = {
            "name": data.get('venue_name', ''),
            "slug": data.get('venue_slug', ''),
            "capacity": int(data.get('capacity', 0)),
            "ba_code_siae": data.get('ba_code_siae', ''),
            "local_code_siae": data.get('local_code_siae', ''),
        }

        # Extract aisles configuration (if present)
        aisles = data.get('aisles', {'horizontal': [], 'vertical': []})
        if aisles and (aisles.get('horizontal') or aisles.get('vertical')):
            venue_info['aisles'] = aisles

        config = {
            "venue": venue_info,
            "rows": data.get('rows', [])
        }

        # Validate
        errors = validate_config(config)

        # Calculate statistics
        stats = calculate_config_stats(config)

        if errors:
            return JsonResponse({
                'valid': False,
                'errors': errors,
                'stats': stats
            })
        else:
            return JsonResponse({
                'valid': True,
                'stats': stats,
                'message': 'Configuration is valid!'
            })

    except Exception as e:
        return JsonResponse({
            'valid': False,
            'error': str(e)
        }, status=400)


@staff_member_required
def load_venue_config(request, venue_id):
    """
    Load existing venue configuration for editing.
    Only accepts GET requests.
    """
    # Ensure GET request
    if request.method != 'GET':
        return JsonResponse({
            'success': False,
            'error': 'Only GET requests allowed'
        }, status=405)

    try:
        venue = get_object_or_404(Venue, pk=venue_id)

        if not venue.configuration_file:
            return JsonResponse({
                'success': False,
                'error': 'No configuration file found for this venue'
            }, status=404)

        # Read the configuration file
        with open(venue.configuration_file.path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        return JsonResponse({
            'success': True,
            'config': config
        })

    except Venue.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Venue not found'
        }, status=404)
    except FileNotFoundError:
        return JsonResponse({
            'success': False,
            'error': 'Configuration file not found on disk'
        }, status=404)
    except json.JSONDecodeError as e:
        return JsonResponse({
            'success': False,
            'error': f'Invalid JSON in configuration file: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error loading configuration: {str(e)}'
        }, status=500)


def validate_config(config):
    """
    Validate venue configuration structure and data.
    Returns list of error messages, empty list if valid.
    """
    errors = []

    # Validate venue information
    venue = config.get('venue', {})

    if not venue.get('name'):
        errors.append('Venue name is required')

    if not venue.get('slug'):
        errors.append('Venue slug is required')

    if not venue.get('capacity') or venue.get('capacity') <= 0:
        errors.append('Venue capacity must be greater than 0')

    # Validate rows
    rows = config.get('rows', [])

    if not rows:
        errors.append('At least one row is required')

    row_names = set()
    total_active_seats = 0

    for idx, row in enumerate(rows):
        row_name = row.get('name')

        if not row_name:
            errors.append(f'Row {idx + 1}: Row name is required')
            continue

        if row_name in row_names:
            errors.append(f'Row {idx + 1}: Duplicate row name "{row_name}"')
        else:
            row_names.add(row_name)

        # Validate offsets
        if 'offset_start' not in row or row['offset_start'] < 0:
            errors.append(f'Row {row_name}: Invalid offset_start')

        if 'offset_end' not in row or row['offset_end'] < 0:
            errors.append(f'Row {row_name}: Invalid offset_end')

        # Validate seats
        seats = row.get('seats', [])

        if not seats:
            errors.append(f'Row {row_name}: At least one seat is required')
            continue

        seat_nums = set()
        for seat_idx, seat in enumerate(seats):
            seat_num = seat.get('num')

            if seat_num is None:
                errors.append(f'Row {row_name}, Seat {seat_idx + 1}: Seat number is required')
                continue

            if seat_num in seat_nums:
                errors.append(f'Row {row_name}: Duplicate seat number {seat_num}')
            else:
                seat_nums.add(seat_num)

            if 'active' not in seat:
                errors.append(f'Row {row_name}, Seat {seat_num}: Active status is required')

            # Count active seats
            if row.get('is_active', True) and seat.get('active', True):
                total_active_seats += 1

    # Validate total capacity matches active seats
    declared_capacity = venue.get('capacity', 0)
    if declared_capacity != total_active_seats:
        errors.append(
            f'Capacity mismatch: declared capacity is {declared_capacity}, '
            f'but found {total_active_seats} active seats'
        )

    # Validate aisles (v2.0 format - optional)
    aisles = venue.get('aisles', {})
    if aisles:
        # Validate horizontal aisles (vertical corridors between seats)
        horizontal_aisles = aisles.get('horizontal', [])
        for idx, aisle in enumerate(horizontal_aisles):
            if 'position' not in aisle or aisle['position'] not in ['after_seat', 'before_seat']:
                errors.append(f'Horizontal aisle {idx + 1}: Invalid position (must be "after_seat" or "before_seat")')

            if 'seat_number' not in aisle or not isinstance(aisle['seat_number'], int):
                errors.append(f'Horizontal aisle {idx + 1}: seat_number is required and must be an integer')

            if 'width' not in aisle or not (1 <= aisle.get('width', 0) <= 5):
                errors.append(f'Horizontal aisle {idx + 1}: width must be between 1 and 5')

            applies_to = aisle.get('applies_to_rows')
            if not applies_to:
                errors.append(f'Horizontal aisle {idx + 1}: applies_to_rows is required')
            elif applies_to != '*':
                if not isinstance(applies_to, list):
                    errors.append(f'Horizontal aisle {idx + 1}: applies_to_rows must be "*" or an array of row names')
                else:
                    # Check that referenced rows exist
                    for row_name in applies_to:
                        if row_name not in row_names:
                            errors.append(f'Horizontal aisle {idx + 1}: references non-existent row "{row_name}"')

        # Validate vertical aisles (horizontal corridors between rows)
        vertical_aisles = aisles.get('vertical', [])
        aisle_positions = set()
        for idx, aisle in enumerate(vertical_aisles):
            if 'position' not in aisle or aisle['position'] not in ['after_row', 'before_row']:
                errors.append(f'Vertical aisle {idx + 1}: Invalid position (must be "after_row" or "before_row")')

            row_name = aisle.get('row_name')
            if not row_name:
                errors.append(f'Vertical aisle {idx + 1}: row_name is required')
            elif row_name not in row_names:
                errors.append(f'Vertical aisle {idx + 1}: references non-existent row "{row_name}"')

            if 'height' not in aisle or not (1 <= aisle.get('height', 0) <= 3):
                errors.append(f'Vertical aisle {idx + 1}: height must be between 1 and 3')

            # Check for duplicate aisle positions
            position_key = f"{aisle.get('position')}_{row_name}"
            if position_key in aisle_positions:
                errors.append(f'Vertical aisle {idx + 1}: Duplicate aisle at same position ({aisle.get("position")} {row_name})')
            else:
                aisle_positions.add(position_key)

    return errors


def calculate_config_stats(config):
    """
    Calculate statistics about the configuration.
    """
    venue = config.get('venue', {})
    rows = config.get('rows', [])

    total_rows = len(rows)
    active_rows = sum(1 for row in rows if row.get('is_active', True))
    inactive_rows = total_rows - active_rows

    total_seats = 0
    active_seats = 0
    inactive_seats = 0

    for row in rows:
        seats = row.get('seats', [])
        row_is_active = row.get('is_active', True)

        for seat in seats:
            total_seats += 1
            seat_is_active = seat.get('active', True)

            if row_is_active and seat_is_active:
                active_seats += 1
            else:
                inactive_seats += 1

    return {
        'venue_name': venue.get('name', ''),
        'declared_capacity': venue.get('capacity', 0),
        'total_rows': total_rows,
        'active_rows': active_rows,
        'inactive_rows': inactive_rows,
        'total_seats': total_seats,
        'active_seats': active_seats,
        'inactive_seats': inactive_seats,
        'capacity_match': venue.get('capacity', 0) == active_seats,
    }
