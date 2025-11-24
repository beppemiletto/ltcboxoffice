# Venue Configuration Guide

## Overview

This guide explains how to create and manage venue seating configurations for the LTC Box Office system. The configuration system allows you to define custom hall layouts for different venues, including seat arrangements, row configurations, and visual alignment.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Configuration File Format](#configuration-file-format)
3. [Using the Configuration Generator Tool](#using-the-configuration-generator-tool)
4. [Manual Configuration Creation](#manual-configuration-creation)
5. [Uploading Configurations](#uploading-configurations)
6. [Management Commands](#management-commands)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Introduction

### What is a Venue Configuration?

A venue configuration is a JSON or XML file that defines:

- **Venue metadata** (name, slug, capacity, SIAE codes)
- **Row structure** (row letters, offsets, active status)
- **Seat layout** (seat numbers, active/inactive status per seat)

### Why Use Venue Configurations?

- **Multiple Venues**: Support different theaters with unique layouts
- **Flexibility**: Easy to modify and update seating arrangements
- **Visual Alignment**: Control how seats appear on screen with offset configuration
- **Disabled Seats**: Mark specific seats as inactive (broken, reserved, etc.)
- **Event Automation**: Events automatically load correct seating from venue

---

## Configuration File Format

### JSON Structure

```json
{
  "venue": {
    "name": "Teatro Comunale di Cambiano",
    "slug": "teatro-cambiano",
    "capacity": 263,
    "ba_code_siae": "0050450366484",
    "local_code_siae": "  045"
  },
  "rows": [
    {
      "name": "A",
      "offset_start": 4,
      "offset_end": 2,
      "is_active": false,
      "seats": [
        {"num": 5, "active": false},
        {"num": 6, "active": true},
        {"num": 7, "active": true}
      ]
    },
    {
      "name": "B",
      "offset_start": 2,
      "offset_end": 2,
      "is_active": true,
      "seats": [
        {"num": 1, "active": true},
        {"num": 2, "active": true}
      ]
    }
  ]
}
```

### Field Descriptions

#### Venue Section

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Full official name of the venue |
| `slug` | string | Yes | URL-friendly identifier (lowercase, hyphens only) |
| `capacity` | integer | Yes | Total number of active seats (must match actual count) |
| `ba_code_siae` | string | No | 13-digit SIAE administrative code |
| `local_code_siae` | string | No | 5-character SIAE local code |

#### Row Section

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Single letter identifier (A, B, C, etc.) |
| `offset_start` | integer | Yes | Number of empty spaces on the left (for visual alignment) |
| `offset_end` | integer | Yes | Number of empty spaces on the right |
| `is_active` | boolean | Yes | Whether the entire row is available for booking |
| `seats` | array | Yes | Array of seat objects |

#### Seat Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `num` | integer | Yes | Seat number within the row |
| `active` | boolean | Yes | Whether this specific seat is available |

### Validation Rules

1. **Unique row names**: No duplicate row letters
2. **Unique seat numbers**: Within each row, seat numbers must be unique
3. **Capacity match**: Declared capacity must equal the count of active seats
4. **Positive values**: All numeric values must be >= 0
5. **Required fields**: All required fields must be present

---

## Using the Configuration Generator Tool

The Configuration Generator Tool provides a visual, interactive way to create venue configurations without writing JSON manually.

### Accessing the Tool

1. **From Django Admin**:
   - Go to **Admin → Billboard → Venues**
   - Click any venue or create a new one
   - In the "Seating Configuration" section, click **"Open Configuration Generator Tool"**

2. **Direct URL**:
   - Navigate to `/billboard/config-generator/`
   - Requires staff/admin login

### Step-by-Step Guide

#### 1. Enter Venue Information

**Required Fields:**
- **Venue Name**: Full name (e.g., "Teatro Comunale di Cambiano")
  - The slug will auto-generate as you type
- **Venue Slug**: URL identifier (auto-filled, e.g., "teatro-comunale")
- **Total Capacity**: Number of active seats (auto-calculated as you add seats)

**Optional Fields:**
- **BA Code SIAE**: 13-digit code
- **Local Code SIAE**: 5-character code

#### 2. Load Existing Configuration (Optional)

If editing an existing venue:
1. Select venue from **"Load Existing Config"** dropdown
2. Click **"Load Configuration"**
3. Existing configuration will populate the editor

#### 3. Add Rows

**Option A: Add Single Row**

1. Enter **Row Letter** (A, B, C, etc.)
2. Set **First Seat Number** (usually 1)
3. Set **Number of Seats** (how many seats in this row)
4. Set **Offset Start** (empty spaces on left)
5. Set **Offset End** (empty spaces on right)
6. Check/uncheck **"Row is Active"**
7. Click **"Add Row"**

**Example: Creating Row C with 16 seats**
- Row Letter: `C`
- First Seat Number: `3`
- Number of Seats: `16`
- Offset Start: `2`
- Offset End: `2`
- Row is Active: ✓

**Option B: Add Multiple Rows**

1. Fill in the row parameters (seat count, offsets, etc.)
2. Click **"Add Multiple Rows"**
3. Enter starting letter (e.g., "C")
4. Enter number of rows to create (e.g., 5 for C, D, E, F, G)
5. All rows will use the same seat configuration

#### 4. Visual Preview

The **"Visual Hall Layout"** section shows:
- **Stage** at the top
- **Rows** below in order
- **Seats** color-coded:
  - 🟢 **Green**: Active seat
  - ⚫ **Gray**: Inactive seat

**Interactive Features:**
- **Click any seat** to toggle active/inactive
- Changes reflect immediately in statistics

#### 5. Edit Rows

**Edit Row Properties:**
1. Click **"Edit"** button on any row card
2. Modify offsets or active status
3. Click **"Save Changes"**

**Delete Row:**
1. Click **"Delete"** button on any row
2. Confirm deletion

#### 6. Validate Configuration

Before downloading:
1. Click **"Validate Only"** to check for errors
2. Review validation results:
   - ✅ Green: Valid configuration
   - ❌ Red: Errors found (fix before downloading)

**Common Validation Errors:**
- Capacity mismatch (declared ≠ actual active seats)
- Duplicate row names
- Missing required fields
- Invalid offset values

#### 7. Download Configuration

1. Click **"Validate & Download JSON"**
2. Configuration will be validated automatically
3. If valid, a `.json` file will download
4. File name: `{venue-slug}.json`

**Example Output:**
- Venue slug: `teatro-cambiano`
- Downloaded file: `teatro-cambiano.json`

#### 8. Upload to Venue

1. Go to **Django Admin → Billboard → Venues**
2. Edit the target venue (or create new)
3. In **"Seating Configuration"** section:
   - Click **"Choose File"**
   - Select your downloaded `.json` file
   - Click **"Save"**

---

## Manual Configuration Creation

If you prefer to create configurations manually in a text editor:

### Template

```json
{
  "venue": {
    "name": "Your Venue Name",
    "slug": "your-venue-slug",
    "capacity": 100,
    "ba_code_siae": "",
    "local_code_siae": ""
  },
  "rows": []
}
```

### Adding Rows Manually

```json
{
  "name": "A",
  "offset_start": 0,
  "offset_end": 0,
  "is_active": true,
  "seats": [
    {"num": 1, "active": true},
    {"num": 2, "active": true},
    {"num": 3, "active": true}
  ]
}
```

### Tips for Manual Editing

1. **Use a JSON validator** (e.g., jsonlint.com) before uploading
2. **Maintain consistent indentation** (2 or 4 spaces)
3. **Double-check capacity calculation**:
   - Count all seats where `row.is_active == true` AND `seat.active == true`
4. **Verify unique names**:
   - No duplicate row letters
   - No duplicate seat numbers within a row

---

## Uploading Configurations

### Via Django Admin

1. **Navigate**: Admin → Billboard → Venues
2. **Select**: Choose venue or create new
3. **Upload**:
   - Scroll to "Seating Configuration"
   - Click "Choose File"
   - Select your `.json` or `.xml` file
4. **Save**: Click "Save" button

### File Location

Uploaded files are stored in:
```
media/venue_configs/{filename}
```

Example:
- Upload: `teatro-cambiano.json`
- Stored: `media/venue_configs/teatro-cambiano.json`

---

## Management Commands

### Load Venue Configuration into Database

The `load_venue_config` command reads a configuration file and populates the Seat and Row database tables.

#### Basic Usage

```bash
python manage.py load_venue_config teatro-cambiano.json
```

#### With Options

```bash
# Clear existing data before loading
python manage.py load_venue_config teatro-cambiano.json --clear

# Dry run (preview without saving)
python manage.py load_venue_config teatro-cambiano.json --dry-run

# Specify venue by slug
python manage.py load_venue_config custom-config.json --venue-slug my-venue

# Use absolute path
python manage.py load_venue_config C:\path\to\config.json
```

#### Command Options

| Option | Description |
|--------|-------------|
| `--clear` | Delete all existing Seat and Row records before loading |
| `--dry-run` | Preview changes without committing to database |
| `--venue-slug SLUG` | Specify which venue this config belongs to |

#### Output Example

```
Loading venue configuration from: teatro-cambiano.json
✓ Venue: Teatro Comunale di Cambiano (teatro-cambiano)
✓ Capacity: 263 seats
✓ Processing 16 rows...

Row A: 14 seats (0 active, 14 inactive)
Row B: 15 seats (0 active, 15 inactive)
Row C: 16 seats (16 active, 0 inactive)
...

Summary:
- Total rows: 16
- Total seats: 263
- Active seats: 263
- Configuration loaded successfully!
```

---

## Troubleshooting

### Common Issues

#### 1. Capacity Mismatch Error

**Error Message:**
```
Capacity mismatch: declared capacity is 263, but found 250 active seats
```

**Solution:**
- Count all active seats manually
- Update the `capacity` field to match
- OR adjust seat `active` status to match declared capacity

#### 2. Duplicate Row Name

**Error Message:**
```
Row 5: Duplicate row name "C"
```

**Solution:**
- Ensure each row has a unique letter
- Use A, B, C, D... without repeats

#### 3. Configuration File Not Found

**Error Message:**
```
No configuration file found for this venue
```

**Solution:**
- Upload a configuration file in Django Admin
- Check that file was saved successfully
- Verify Venue has `configuration_file` field populated

#### 4. Invalid JSON Format

**Error Message:**
```
Invalid JSON data
```

**Solution:**
- Validate JSON syntax at jsonlint.com
- Check for:
  - Missing commas
  - Unclosed brackets
  - Trailing commas
  - Quote mismatch

#### 5. Seats Not Loading in Events

**Possible Causes:**
- Venue not associated with event
- Configuration file missing or corrupt
- Event JSON not regenerated after config change

**Solution:**
```python
# In Django shell or script
from store.models import Event

event = Event.objects.get(pk=EVENT_ID)
event.save()  # Regenerates seat JSON from venue config
```

---

## Best Practices

### 1. Naming Conventions

- **Venue names**: Use full official names
  - ✅ "Teatro Comunale di Cambiano"
  - ❌ "TC Cambiano"

- **Slugs**: Use lowercase with hyphens
  - ✅ `teatro-comunale-cambiano`
  - ❌ `Teatro_Comunale`

- **Row letters**: Use consecutive letters
  - ✅ A, B, C, D, E...
  - ❌ A, C, E (skip B, D)

### 2. Seat Numbering

- **Start from 1** for most rows (unless venue uses different system)
- **Be consistent** across rows
- **Match physical seat numbers** in the actual venue

### 3. Offset Configuration

Use offsets to create visual curved/tapered halls:

```
Offset Start = 4    Row A    Offset End = 2
          [ ][ ][ ][ ][A5][A6][A7]...[A18][ ][ ]

Offset Start = 2    Row B    Offset End = 2
          [ ][ ][B3][B4][B5]...[B18][ ][ ]

Offset Start = 0    Row C    Offset End = 0
          [C1][C2][C3][C4][C5]...[C20]
```

### 4. Inactive Seats

Mark seats as inactive for:
- **Broken/damaged seats**
- **Reserved seats** (for staff, accessibility)
- **Removed seats** (physical changes to venue)
- **Restricted view** seats (optional)

### 5. Version Control

- **Keep backups** of configuration files
- **Document changes** (e.g., "Removed seats A5-A7 for accessibility")
- **Test before deploying** to production
- **Use descriptive file names**: `teatro-cambiano-2024.json`

### 6. Testing

After creating a configuration:

1. **Validate** using the tool
2. **Upload** to a test venue first
3. **Create test event** using that venue
4. **Verify seat map renders correctly**
5. **Test booking flow** end-to-end

### 7. Documentation

Maintain a venue registry:

| Venue | Slug | Capacity | Config File | Last Updated |
|-------|------|----------|-------------|--------------|
| Teatro Cambiano | teatro-cambiano | 263 | teatro-cambiano.json | 2024-01-15 |
| Auditorium Roma | auditorium-roma | 450 | auditorium-roma.json | 2024-02-20 |

---

## Advanced Topics

### Multiple Venue Support

To support multiple venues:

1. **Create separate configuration files** for each venue
2. **Upload each config** to corresponding Venue record in admin
3. **Associate events** with correct venue:
   ```python
   event = Event.objects.create(
       show=show,
       date_time=datetime,
       venue=Venue.objects.get(slug='teatro-cambiano')
   )
   ```
4. **Event.save()** automatically loads correct seating layout

### Dynamic Capacity Calculation

The system automatically:
- Counts active seats when you modify the configuration
- Updates the capacity field in real-time (in generator tool)
- Validates capacity matches active seat count

### Event Seat State Management

**Configuration → Event Relationship:**

1. **Venue Config** (static): Defines hall structure
   - File: `venue_configs/teatro-cambiano.json`
   - Purpose: Template for all events at this venue

2. **Event State** (dynamic): Tracks booking status
   - File: `hall_jsons/{event_slug}.json`
   - Purpose: Which seats are booked/sold for this specific event

**When Event.save() is called:**
```
Load venue.configuration_file
→ Apply structure to event
→ Overlay current bookings/sales
→ Write to hall_jsons/{event_slug}.json
```

### XML Format (Alternative)

If you prefer XML:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<venue-config>
  <venue>
    <name>Teatro Comunale</name>
    <slug>teatro-comunale</slug>
    <capacity>263</capacity>
  </venue>
  <rows>
    <row>
      <name>A</name>
      <offset_start>4</offset_start>
      <offset_end>2</offset_end>
      <is_active>false</is_active>
      <seats>
        <seat num="5" active="false"/>
        <seat num="6" active="true"/>
      </seats>
    </row>
  </rows>
</venue-config>
```

---

## Quick Reference

### Configuration Generator Workflow

```
1. Open tool: /billboard/config-generator/
2. Enter venue info
3. Add rows (single or bulk)
4. Edit seats visually
5. Validate
6. Download JSON
7. Upload to admin
8. Test with event
```

### Management Command

```bash
python manage.py load_venue_config <file.json> [--clear] [--dry-run]
```

### File Locations

- **Venue configs**: `media/venue_configs/`
- **Event states**: `hall_jsons/`
- **Template**: `templates/billboard/venue_config_generator.html`

---

## Support

### Getting Help

1. **Check validation messages** in the generator tool
2. **Review this guide** for common issues
3. **Test in development** environment first
4. **Contact system administrator** for database issues

### Reporting Issues

Include:
- Configuration file (JSON)
- Error messages
- Steps to reproduce
- Expected vs. actual behavior

---

## Changelog

- **v1.0** (2024): Initial configuration system
  - JSON/XML support
  - Visual configuration generator
  - Admin integration
  - Management commands

---

## Appendix: Example Configurations

### Small Theater (100 seats, 10 rows)

```json
{
  "venue": {
    "name": "Teatro Piccolo",
    "slug": "teatro-piccolo",
    "capacity": 100,
    "ba_code_siae": "",
    "local_code_siae": ""
  },
  "rows": [
    {
      "name": "A",
      "offset_start": 0,
      "offset_end": 0,
      "is_active": true,
      "seats": [
        {"num": 1, "active": true},
        {"num": 2, "active": true},
        {"num": 3, "active": true},
        {"num": 4, "active": true},
        {"num": 5, "active": true},
        {"num": 6, "active": true},
        {"num": 7, "active": true},
        {"num": 8, "active": true},
        {"num": 9, "active": true},
        {"num": 10, "active": true}
      ]
    }
  ]
}
```

### Concert Hall (500 seats, curved)

```json
{
  "venue": {
    "name": "Auditorium Concerto",
    "slug": "auditorium-concerto",
    "capacity": 500,
    "ba_code_siae": "1234567890123",
    "local_code_siae": "CONC1"
  },
  "rows": [
    {
      "name": "A",
      "offset_start": 10,
      "offset_end": 10,
      "is_active": true,
      "seats": [
        {"num": 1, "active": true},
        ...
        {"num": 20, "active": true}
      ]
    },
    {
      "name": "B",
      "offset_start": 5,
      "offset_end": 5,
      "is_active": true,
      "seats": [
        {"num": 1, "active": true},
        ...
        {"num": 30, "active": true}
      ]
    }
  ]
}
```

---

**End of Guide**

For technical implementation details, see the source code in:
- `billboard/views.py`
- `billboard/models.py`
- `templates/billboard/venue_config_generator.html`
