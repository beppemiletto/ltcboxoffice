"""
Django Management Command: Load Venue Configuration

This command loads venue seating configuration from JSON or XML files and populates
the database with Row and Seat records for a specific venue.

Usage:
    python manage.py load_venue_config <config_file> [--venue-slug SLUG]
    
Examples:
    # Load Teatro Cambiano configuration
    python manage.py load_venue_config teatro-cambiano.json
    
    # Load from absolute path
    python manage.py load_venue_config C:/path/to/venue.json
    
    # Specify venue by slug
    python manage.py load_venue_config salone-italia.json --venue-slug salone-italia
    
    # Clear existing data before loading
    python manage.py load_venue_config teatro-cambiano.json --clear
"""

import json
import os
from pathlib import Path
from xml.etree import ElementTree as ET

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings

from billboard.models import Venue
from hall.models import Row, Seat


class Command(BaseCommand):
    help = 'Load venue seating configuration from JSON or XML file'

    def add_arguments(self, parser):
        parser.add_argument(
            'config_file',
            type=str,
            help='Path to configuration file (JSON or XML), relative to venue_configs/ or absolute path'
        )
        parser.add_argument(
            '--venue-slug',
            type=str,
            help='Venue slug (if different from config file name)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing rows and seats for this venue before loading'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be loaded without actually saving to database'
        )

    def handle(self, *args, **options):
        config_file = options['config_file']
        venue_slug = options.get('venue_slug')
        clear_existing = options.get('clear', False)
        dry_run = options.get('dry_run', False)

        # Resolve config file path
        config_path = self._resolve_config_path(config_file)
        
        if not config_path.exists():
            raise CommandError(f'Configuration file not found: {config_path}')

        self.stdout.write(f'Loading configuration from: {config_path}')

        # Load configuration
        config_data = self._load_config(config_path)
        
        # Extract venue info
        venue_info = config_data.get('venue', {})
        
        # Determine venue slug
        if not venue_slug:
            venue_slug = venue_info.get('slug', config_path.stem)
        
        self.stdout.write(f'Processing venue: {venue_slug}')

        # Get or create venue
        try:
            venue = Venue.objects.get(slug=venue_slug)
            self.stdout.write(self.style.SUCCESS(f'Found existing venue: {venue.name}'))
        except Venue.DoesNotExist:
            if dry_run:
                self.stdout.write(self.style.WARNING(f'[DRY RUN] Would create venue: {venue_slug}'))
                venue = None
            else:
                # Create venue from config
                venue = self._create_venue(venue_info, venue_slug, config_file)
                self.stdout.write(self.style.SUCCESS(f'Created new venue: {venue.name}'))

        # Clear existing data if requested
        if clear_existing and not dry_run and venue:
            self._clear_venue_data(venue)

        # Load rows and seats
        rows_data = config_data.get('rows', [])
        
        if dry_run:
            self._show_dry_run_summary(rows_data)
        else:
            self._load_venue_data(venue, rows_data)

        self.stdout.write(self.style.SUCCESS('✅ Configuration loaded successfully!'))

    def _resolve_config_path(self, config_file):
        """Resolve configuration file path"""
        path = Path(config_file)
        
        # If absolute path, use it directly
        if path.is_absolute():
            return path
        
        # Try venue_configs directory
        venue_configs_dir = settings.BASE_DIR / 'venue_configs'
        config_path = venue_configs_dir / config_file
        
        if config_path.exists():
            return config_path
        
        # Try current directory
        current_dir_path = Path.cwd() / config_file
        if current_dir_path.exists():
            return current_dir_path
        
        return config_path  # Return default path for error message

    def _load_config(self, config_path):
        """Load configuration from JSON or XML file"""
        file_ext = config_path.suffix.lower()
        
        if file_ext == '.json':
            return self._load_json(config_path)
        elif file_ext == '.xml':
            return self._load_xml(config_path)
        else:
            raise CommandError(f'Unsupported file format: {file_ext}. Use .json or .xml')

    def _load_json(self, config_path):
        """Load JSON configuration"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON file: {e}')

    def _load_xml(self, config_path):
        """Load XML configuration and convert to dict"""
        try:
            tree = ET.parse(config_path)
            root = tree.getroot()
            
            # Convert XML to dict structure
            config_data = {'venue': {}, 'rows': []}
            
            # Parse venue info
            venue_elem = root.find('venue')
            if venue_elem is not None:
                for child in venue_elem:
                    config_data['venue'][child.tag] = child.text
            
            # Parse rows
            rows_elem = root.find('rows')
            if rows_elem is not None:
                for row_elem in rows_elem.findall('row'):
                    row_data = {
                        'name': row_elem.get('name'),
                        'offset_start': int(row_elem.get('offset_start', 0)),
                        'offset_end': int(row_elem.get('offset_end', 0)),
                        'is_active': row_elem.get('is_active', 'true').lower() == 'true',
                        'seats': []
                    }
                    
                    # Parse seats
                    for seat_elem in row_elem.findall('seat'):
                        seat_data = {
                            'num': int(seat_elem.get('num')),
                            'active': seat_elem.get('active', 'true').lower() == 'true'
                        }
                        row_data['seats'].append(seat_data)
                    
                    config_data['rows'].append(row_data)
            
            return config_data
            
        except ET.ParseError as e:
            raise CommandError(f'Invalid XML file: {e}')

    def _create_venue(self, venue_info, venue_slug, config_file):
        """Create venue from configuration"""
        venue_data = {
            'slug': venue_slug,
            'name': venue_info.get('name', venue_slug.replace('-', ' ').title()),
            'address': venue_info.get('address', ''),
            'capacity': venue_info.get('capacity', 0),
            'ba_code_siae': venue_info.get('ba_code_siae', '0050450366484'),
            'local_code_siae': venue_info.get('local_code_siae', '  045'),
        }
        
        return Venue.objects.create(**venue_data)

    def _clear_venue_data(self, venue):
        """Clear existing rows and seats for venue"""
        # Note: In production branch, Seat and Row don't have venue FK yet
        # Clear all seats and rows (multi-venue support coming in feature branch)
        deleted_seats = Seat.objects.all().delete()
        deleted_rows = Row.objects.all().delete()
        
        self.stdout.write(
            self.style.WARNING(
                f'Cleared {deleted_seats[0]} seats and {deleted_rows[0]} rows'
            )
        )

    @transaction.atomic
    def _load_venue_data(self, venue, rows_data):
        """Load rows and seats into database"""
        total_rows = 0
        total_seats = 0
        seat_number = 1
        
        for row_data in rows_data:
            row_name = row_data['name']
            
            # Create or update row (without venue FK in production branch)
            row, created = Row.objects.update_or_create(
                name=row_name,
                defaults={
                    'offset_start': row_data.get('offset_start', 0),
                    'offset_end': row_data.get('offset_end', 0),
                    'is_active': row_data.get('is_active', True)
                }
            )
            
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'  {action} row: {row_name}')
            total_rows += 1
            
            # Create seats for this row (without venue FK in production branch)
            seats_data = row_data.get('seats', [])
            for seat_data in seats_data:
                num_in_row = str(seat_data['num']).zfill(2)
                seat_name = f'{row_name}{num_in_row}'
                
                seat, created = Seat.objects.update_or_create(
                    name=seat_name,
                    defaults={
                        'row': row_name,
                        'num_in_row': num_in_row,
                        'number': seat_number,
                        'active': seat_data.get('active', True)
                    }
                )
                
                seat_number += 1
                total_seats += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n📊 Summary:'))
        self.stdout.write(f'  • Venue: {venue.name} ({venue.slug})')
        self.stdout.write(f'  • Rows loaded: {total_rows}')
        self.stdout.write(f'  • Seats loaded: {total_seats}')
        self.stdout.write(f'  • Capacity: {venue.capacity}')

    def _show_dry_run_summary(self, rows_data):
        """Show what would be loaded without saving"""
        self.stdout.write(self.style.WARNING('\n🔍 DRY RUN - No changes will be saved\n'))
        
        total_seats = 0
        for row_data in rows_data:
            row_name = row_data['name']
            seats_count = len(row_data.get('seats', []))
            total_seats += seats_count
            active_status = '✓ active' if row_data.get('is_active', True) else '✗ inactive'
            
            self.stdout.write(
                f'  Row {row_name}: {seats_count} seats, '
                f'offset_start={row_data.get("offset_start", 0)}, '
                f'offset_end={row_data.get("offset_end", 0)} '
                f'[{active_status}]'
            )
        
        self.stdout.write(f'\n  Total: {len(rows_data)} rows, {total_seats} seats')
