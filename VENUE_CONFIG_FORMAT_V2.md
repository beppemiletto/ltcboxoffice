# Venue Configuration Format v2.0 - With Aisles/Corridors

## Overview

This document describes the extended venue configuration format that supports defining aisles (corridors) between seats and between rows.

---

## New Features

### 1. Horizontal Aisles (Corridoi Longitudinali)
Corridors that run vertically between columns of seats (e.g., between seat 10 and 11).

### 2. Vertical Aisles (Corridoi Trasversali)
Corridors that run horizontally between rows (e.g., between row H and row I).

---

## JSON Structure

```json
{
  "venue": {
    "name": "Teatro Comunale di Cambiano",
    "slug": "teatro-cambiano",
    "capacity": 263,
    "ba_code_siae": "0050450366484",
    "local_code_siae": "  045",
    "aisles": {
      "horizontal": [
        {
          "position": "after_seat",
          "seat_number": 10,
          "width": 2,
          "applies_to_rows": ["C", "D", "E", "F", "G", "H", "I", "L", "M", "N", "O", "P", "Q"],
          "description": "Main central aisle"
        }
      ],
      "vertical": [
        {
          "position": "after_row",
          "row_name": "H",
          "height": 1,
          "description": "Transversal aisle for emergency exit"
        }
      ]
    }
  },
  "rows": [
    {
      "name": "C",
      "offset_start": 2,
      "offset_end": 2,
      "is_active": true,
      "seats": [
        {"num": 3, "active": true},
        {"num": 4, "active": true},
        {"num": 5, "active": true},
        {"num": 6, "active": true},
        {"num": 7, "active": true},
        {"num": 8, "active": true},
        {"num": 9, "active": true},
        {"num": 10, "active": true},
        {"num": 11, "active": true},
        {"num": 12, "active": true},
        {"num": 13, "active": true},
        {"num": 14, "active": true},
        {"num": 15, "active": true},
        {"num": 16, "active": true},
        {"num": 17, "active": true},
        {"num": 18, "active": true}
      ]
    }
  ]
}
```

---

## Field Definitions

### Venue → Aisles Section

#### `aisles` (object, optional)
Container for all aisle definitions.

#### `aisles.horizontal` (array, optional)
Defines vertical corridors between columns of seats.

**Horizontal Aisle Object:**
```json
{
  "position": "after_seat",        // or "before_seat"
  "seat_number": 10,               // Seat number where aisle appears
  "width": 2,                      // Width in seat-units (1-5)
  "applies_to_rows": ["C", "D"],  // Array of row names (or "*" for all)
  "description": "Main aisle"      // Optional description
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `position` | string | Yes | `"after_seat"` or `"before_seat"` |
| `seat_number` | integer | Yes | Seat number where aisle is positioned |
| `width` | integer | Yes | Width of aisle in seat-widths (1-5) |
| `applies_to_rows` | array/string | Yes | Row names or `"*"` for all rows |
| `description` | string | No | Human-readable description |

#### `aisles.vertical` (array, optional)
Defines horizontal corridors between rows.

**Vertical Aisle Object:**
```json
{
  "position": "after_row",        // or "before_row"
  "row_name": "H",                // Row name where aisle appears
  "height": 1,                    // Height in row-units (1-3)
  "description": "Emergency exit" // Optional description
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `position` | string | Yes | `"after_row"` or `"before_row"` |
| `row_name` | string | Yes | Row name where aisle is positioned |
| `height` | integer | Yes | Height of aisle in row-heights (1-3) |
| `description` | string | No | Human-readable description |

---

## Examples

### Example 1: Teatro Comunale di Cambiano

**Features:**
- Central vertical aisle between seat 10 and 11 (all rows)
- Horizontal aisle after row H

```json
{
  "venue": {
    "name": "Teatro Comunale di Cambiano",
    "slug": "teatro-cambiano",
    "capacity": 263,
    "aisles": {
      "horizontal": [
        {
          "position": "after_seat",
          "seat_number": 10,
          "width": 2,
          "applies_to_rows": "*",
          "description": "Central corridor"
        }
      ],
      "vertical": [
        {
          "position": "after_row",
          "row_name": "H",
          "height": 1,
          "description": "Transversal emergency corridor"
        }
      ]
    }
  },
  "rows": [...]
}
```

### Example 2: Salone Italia Poirino

**Features:**
- No central vertical aisle
- Horizontal aisle after row F (different position)

```json
{
  "venue": {
    "name": "Salone Italia Poirino",
    "slug": "salone-italia-poirino",
    "capacity": 300,
    "aisles": {
      "horizontal": [],
      "vertical": [
        {
          "position": "after_row",
          "row_name": "F",
          "height": 2,
          "description": "Main transversal corridor"
        }
      ]
    }
  },
  "rows": [...]
}
```

### Example 3: Multiple Aisles

```json
{
  "venue": {
    "name": "Large Auditorium",
    "slug": "large-auditorium",
    "capacity": 500,
    "aisles": {
      "horizontal": [
        {
          "position": "after_seat",
          "seat_number": 8,
          "width": 2,
          "applies_to_rows": ["A", "B", "C", "D", "E"],
          "description": "Left aisle"
        },
        {
          "position": "after_seat",
          "seat_number": 16,
          "width": 2,
          "applies_to_rows": ["A", "B", "C", "D", "E"],
          "description": "Right aisle"
        }
      ],
      "vertical": [
        {
          "position": "after_row",
          "row_name": "E",
          "height": 2,
          "description": "Front section divider"
        },
        {
          "position": "after_row",
          "row_name": "K",
          "height": 2,
          "description": "Back section divider"
        }
      ]
    }
  },
  "rows": [...]
}
```

---

## Backward Compatibility

### Old Format (v1.0) - Still Supported

```json
{
  "venue": {
    "name": "Teatro Example",
    "slug": "teatro-example",
    "capacity": 100
  },
  "rows": [...]
}
```

**Behavior:**
- If `aisles` section is missing, no aisles are rendered
- Old configurations continue to work without modification

---

## Validation Rules

### Horizontal Aisles
1. `seat_number` must exist in at least one row
2. `width` must be between 1 and 5
3. `applies_to_rows` must reference existing rows or be `"*"`
4. `position` must be `"after_seat"` or `"before_seat"`

### Vertical Aisles
1. `row_name` must reference an existing row
2. `height` must be between 1 and 3
3. `position` must be `"after_row"` or `"before_row"`
4. Cannot have two aisles in same position

---

## Rendering Guidelines

### Horizontal Aisles
- Render as empty space with width equal to `width * seat_width`
- Visual: Gray vertical stripe or dashed line
- CSS class: `aisle-horizontal`

### Vertical Aisles
- Render as empty row with height equal to `height * row_height`
- Visual: Gray horizontal stripe or dashed line
- CSS class: `aisle-vertical`

---

## Use Cases

### Use Case 1: Simple Theater
No aisles needed - seats are close together.

```json
{
  "venue": {...},
  "rows": [...]
}
```

### Use Case 2: Standard Theater
One central vertical aisle, one horizontal aisle for emergency exit.

```json
{
  "venue": {
    "aisles": {
      "horizontal": [{"after": 10, "width": 2}],
      "vertical": [{"after": "H", "height": 1}]
    }
  }
}
```

### Use Case 3: Cinema Complex
Multiple vertical aisles (left, center, right) and section dividers.

```json
{
  "venue": {
    "aisles": {
      "horizontal": [
        {"after": 5, "width": 2},
        {"after": 15, "width": 3},
        {"after": 25, "width": 2}
      ],
      "vertical": [
        {"after": "D", "height": 2},
        {"after": "H", "height": 2}
      ]
    }
  }
}
```

---

## Migration Guide

### From v1.0 to v2.0

**Step 1:** Add `aisles` section to venue
```json
{
  "venue": {
    "name": "...",
    "aisles": {
      "horizontal": [],
      "vertical": []
    }
  }
}
```

**Step 2:** Define aisles based on physical layout
- Walk through the venue
- Identify corridors
- Note their positions (after which seat/row)
- Measure approximate width/height

**Step 3:** Add aisle definitions
```json
{
  "horizontal": [
    {
      "position": "after_seat",
      "seat_number": 10,
      "width": 2,
      "applies_to_rows": "*"
    }
  ]
}
```

**Step 4:** Validate and test
- Use configuration generator to visualize
- Verify aisles appear in correct positions
- Test with actual event rendering

---

## Benefits

1. **Venue-Specific**: Each venue can define its own aisle layout
2. **Flexible**: Support for any number of aisles
3. **Accurate**: Matches physical venue layout
4. **Visual**: Aisles are clearly visible in seat map
5. **Backward Compatible**: Old configs still work

---

## Technical Implementation

### Data Flow

```
Venue Config JSON (with aisles)
    ↓
Event.save() → _load_seats_from_venue_config()
    ↓
event_hall JSON (with aisle metadata)
    ↓
hall_detail template → renders aisles
    ↓
User sees accurate seat map with corridors
```

### Template Rendering

```django
{% for row in rows %}
  <tr>
    {% for seat in row.seats %}
      <td>{{ seat.num }}</td>

      {% if has_aisle_after_seat(seat.num, row.name) %}
        <td class="aisle-horizontal" colspan="{{ aisle_width }}"></td>
      {% endif %}
    {% endfor %}
  </tr>

  {% if has_aisle_after_row(row.name) %}
    <tr class="aisle-vertical" style="height: {{ aisle_height }}px"></tr>
  {% endif %}
{% endfor %}
```

---

## Future Enhancements

1. **Curved aisles**: Support for non-straight corridors
2. **Aisle naming**: Give names to aisles (e.g., "Main Aisle", "Exit A")
3. **Accessibility markers**: Mark wheelchair-accessible aisles
4. **Emergency exits**: Link aisles to emergency exit locations
5. **3D visualization**: Render aisles in 3D seat map

---

## Summary

The v2.0 format adds flexible aisle support to venue configurations:
- **Horizontal aisles** (vertical corridors between seats)
- **Vertical aisles** (horizontal corridors between rows)
- **Per-venue configuration** (no more hardcoded positions)
- **Backward compatible** (v1.0 configs still work)

This allows accurate representation of any theater layout, from simple halls to complex multi-section auditoriums.
