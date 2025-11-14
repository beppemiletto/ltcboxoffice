#!/usr/bin/env python
"""Test script to verify venue configuration loading in Event JSON generation"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ltcboxoffice.settings')
django.setup()

from store.models import Event
from billboard.models import Venue
import json

# Get test event
event = Event.objects.first()
print(f'Event: {event.event_slug}')
print(f'Venue: {event.venue.name}')
print(f'Config file: {event.venue.get_config_file_path()}')

# Regenerate JSON
print('\nRegenerating event JSON...')
event.save()

# Load and verify generated JSON
json_path = event.get_json_path()
with open(json_path, 'r') as f:
    hall_data = json.load(f)

print(f'\nGenerated JSON:')
print(f'  Path: {json_path}')
print(f'  Total seats: {len(hall_data)}')
print(f'  Sample seats: {list(hall_data.keys())[:10]}')

# Verify no A or B rows (they are inactive)
rows_in_json = set(seat_data['row'] for seat_data in hall_data.values())
print(f'\nRows in JSON: {sorted(rows_in_json)}')
print(f'  Contains row A: {"A" in rows_in_json} (should be False)')
print(f'  Contains row B: {"B" in rows_in_json} (should be False)')
print(f'  Contains row C: {"C" in rows_in_json} (should be True)')

print('\n✅ Test completed successfully!' if len(hall_data) == 234 else '\n❌ Unexpected seat count')
