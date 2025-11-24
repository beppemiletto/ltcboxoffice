# Quick Start: Venue Configuration Generator

## 5-Minute Setup Guide

This guide will help you create your first venue configuration in under 5 minutes.

---

## Access the Tool

### Option 1: From Django Admin
1. Go to Django Admin
2. Navigate to **Billboard → Venues**
3. Click any venue (or create new)
4. Scroll to **"Seating Configuration"** section
5. Click **"Open Configuration Generator Tool"** button

### Option 2: Direct URL
1. Navigate to: `/billboard/config-generator/`
2. Login with staff credentials if prompted

---

## Create Your First Configuration

### Step 1: Venue Information (30 seconds)

Fill in the left sidebar:

```
Venue Name: Teatro Comunale
Venue Slug: teatro-comunale (auto-fills)
Total Capacity: 0 (will auto-calculate)
BA Code SIAE: (optional)
Local Code SIAE: (optional)
```

### Step 2: Add Rows (2 minutes)

**For a simple 100-seat theater:**

1. **Row A:**
   - Row Letter: `A`
   - First Seat: `1`
   - Number of Seats: `10`
   - Offset Start: `0`
   - Offset End: `0`
   - Row is Active: ✓
   - Click **"Add Row"**

2. **Rows B-J (bulk add):**
   - Keep settings: First Seat `1`, Seats `10`
   - Click **"Add Multiple Rows"**
   - Enter starting letter: `B`
   - Enter number of rows: `9`
   - Click OK

**Result:** 10 rows (A-J), 10 seats each = 100 total seats

### Step 3: Review & Edit (1 minute)

**Visual Preview:**
- Check the "Visual Hall Layout" section
- Green seats = active
- Gray seats = inactive
- Click any seat to toggle

**Statistics:**
- Total Rows: 10
- Active Seats: 100
- Capacity Match: ✓

**Optional edits:**
- Click "Edit" on any row to change offsets
- Click individual seats to deactivate broken/reserved seats
- Delete rows if needed

### Step 4: Download (30 seconds)

1. Click **"Validate & Download JSON"**
2. If validation passes, file downloads automatically
3. File name: `teatro-comunale.json`

### Step 5: Upload to Venue (30 seconds)

1. Return to Django Admin
2. Go to **Billboard → Venues**
3. Edit the venue (or create new)
4. Scroll to **"Seating Configuration"**
5. Click **"Choose File"**
6. Select `teatro-comunale.json`
7. Click **"Save"**

---

## Done! 🎉

Your venue configuration is now ready. When you create events for this venue, they will automatically use this seating layout.

---

## Test Your Configuration

### Create a Test Event

```python
# In Django shell or admin
event = Event.objects.create(
    show=my_show,
    venue=Venue.objects.get(slug='teatro-comunale'),
    date_time='2024-12-25 20:00:00'
)
```

### View Seat Map

1. Navigate to event detail page
2. Click seat selection
3. Verify layout matches your configuration

---

## Common Patterns

### Small Theater (50-100 seats)
- 5-10 rows
- 10-15 seats per row
- No offsets (straight rows)

### Medium Theater (200-300 seats)
- 12-16 rows
- 15-20 seats per row
- Small offsets (2-4) for curved appearance

### Large Theater (500+ seats)
- 20+ rows
- Variable seats per row
- Large offsets for curved/tapered design

---

## Example: Teatro Cambiano (Actual Configuration)

**Venue Info:**
- Name: Teatro Comunale di Cambiano
- Slug: teatro-cambiano
- Capacity: 263 seats
- 16 rows (A-Q)

**Row Configuration:**
| Row | Seats | Offset Start | Offset End | Active |
|-----|-------|--------------|------------|--------|
| A   | 14    | 4            | 2          | No     |
| B   | 15    | 3            | 2          | No     |
| C   | 16    | 2            | 2          | Yes    |
| D-E | 16    | 2            | 2          | Yes    |
| F-N | 18    | 1            | 1          | Yes    |
| O-Q | 20    | 0            | 0          | Yes    |

This creates a tapered hall that widens toward the back.

---

## Tips for Success

### 1. Start Simple
- Begin with uniform rows (same seat count)
- Add complexity later (offsets, inactive seats)

### 2. Use Visual Preview
- Check layout before downloading
- Verify seats are colored correctly
- Test clicking seats to toggle

### 3. Match Physical Layout
- Use actual seat numbers from venue
- Mark broken/reserved seats as inactive
- Test offset values for proper alignment

### 4. Validate Before Uploading
- Click "Validate Only" first
- Fix any errors
- Then "Validate & Download"

### 5. Keep Backups
- Save JSON files in version control
- Name files descriptively: `teatro-cambiano-2024.json`
- Document changes in comments

---

## Troubleshooting

### "Capacity mismatch" error
**Solution:** Click "Validate Only" to see declared vs actual capacity. Update the capacity field to match active seats.

### Seats not showing in event
**Solution:** Verify venue is associated with event. Re-save event to regenerate seat map.

### Can't access tool
**Solution:** Ensure you're logged in as staff/admin user.

### JSON won't download
**Solution:** Check browser allows downloads. Look for validation errors first.

---

## Next Steps

After creating your first configuration:

1. **Read full guide:** `VENUE_CONFIGURATION_GUIDE.md`
2. **Create more venues:** Use "Load Existing Config" to copy and modify
3. **Test thoroughly:** Create test events and verify seat selection works
4. **Document changes:** Keep a venue registry with updates

---

## Advanced Features

### Bulk Row Creation
- Set parameters once
- Add 10+ rows at once
- Saves time for large theaters

### Load Existing Configuration
- Select venue from dropdown
- Click "Load Configuration"
- Edit and re-export

### Row Editing
- Click "Edit" on any row
- Modify offsets without recreating
- Change active status

### Individual Seat Control
- Click any seat in visual preview
- Toggle active/inactive
- Mark specific broken seats

---

## Support

### Resources
- **Full Documentation:** `VENUE_CONFIGURATION_GUIDE.md`
- **Implementation Details:** `VENUE_CONFIG_GENERATOR_SUMMARY.md`
- **Test Suite:** `test_venue_config_tool.py`

### Getting Help
1. Check validation messages
2. Review documentation
3. Test in development first
4. Contact system administrator

---

## Configuration Template

Copy this template for manual editing:

```json
{
  "venue": {
    "name": "Your Venue Name",
    "slug": "your-venue-slug",
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
        {"num": 2, "active": true}
      ]
    }
  ]
}
```

---

## Summary

1. **Access:** `/billboard/config-generator/`
2. **Configure:** Enter venue info, add rows
3. **Validate:** Check for errors
4. **Download:** Get JSON file
5. **Upload:** Add to venue in admin
6. **Test:** Create event and verify

**Time:** 5 minutes for basic configuration
**Difficulty:** Easy (no coding required)
**Result:** Production-ready venue seating layout

---

**Ready to create more complex configurations?**
See [VENUE_CONFIGURATION_GUIDE.md](VENUE_CONFIGURATION_GUIDE.md) for advanced features and detailed instructions.
