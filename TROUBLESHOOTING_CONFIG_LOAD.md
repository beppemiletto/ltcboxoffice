# Troubleshooting: Loading Venue Configurations

## Problem: "HTTP 404: Not Found" when loading venue configuration

### Cause
This error occurs when you try to load a configuration from a venue that **does not have a configuration file uploaded yet**.

### Solution

#### Option 1: Upload an Existing Configuration File

1. **Go to Django Admin**
   - Navigate to: `Admin → Billboard → Venues`
   - Click on the venue you want to configure

2. **Upload Configuration File**
   - Scroll to **"Seating Configuration"** section
   - Click **"Choose File"**
   - Select a `.json` configuration file
   - Click **"Save"**

3. **Return to Configuration Generator**
   - Refresh the page
   - The venue should now show with a ✓ mark
   - You can now load its configuration

#### Option 2: Create a New Configuration

1. **Use the Configuration Generator**
   - Leave the "Load Existing Config" dropdown empty
   - Fill in the venue information manually
   - Add rows and configure seats
   - Download the JSON file
   - Upload it to the venue in Django Admin

#### Option 3: Use an Existing Configuration as Template

1. **Select a venue with ✓ mark** (one that has a configuration)
2. **Load its configuration**
3. **Modify** the venue name, slug, and layout as needed
4. **Download** the new configuration
5. **Upload** to a different venue

---

## How to Identify Venues with Configurations

In the **"Load Existing Config"** dropdown, you'll see:

- ✅ **`Venue Name ✓`** - Has configuration file (can be loaded)
- ❌ **`Venue Name (no config)`** - No configuration file (cannot be loaded)

---

## Quick Workflow

### For First-Time Setup:

```
1. Create configuration in generator
2. Download JSON file
3. Go to Admin → Venues → Select venue
4. Upload JSON file
5. Return to generator
6. Now you can load it
```

### For Editing Existing Configuration:

```
1. Select venue with ✓ mark
2. Click "Load Configuration"
3. Make changes
4. Download updated JSON
5. Upload to same venue in Admin
```

---

## Error Messages and Their Meanings

| Error Message | Meaning | Solution |
|---------------|---------|----------|
| `HTTP 404: Not Found` | Venue has no config file | Upload a config file first |
| `No configuration file found for this venue` | `configuration_file` field is empty | Upload a config via Admin |
| `Configuration file not found on disk` | File was deleted from server | Re-upload the config file |
| `Invalid JSON in configuration file` | File is corrupted | Download a new valid config |

---

## Example: Creating Your First Configuration

### Step 1: Create Configuration
```
1. Access: /billboard/config-generator/
2. Enter venue info:
   - Name: "Teatro Comunale di Cambiano"
   - Slug: "teatro-cambiano" (auto-generated)
   - Capacity: 263
3. Add rows (e.g., A-Q with various seat counts)
4. Download: teatro-cambiano.json
```

### Step 2: Upload to Venue
```
1. Admin → Billboard → Venues
2. Select "Teatro Comunale di Cambiano"
3. Seating Configuration section
4. Upload: teatro-cambiano.json
5. Save
```

### Step 3: Load for Editing
```
1. Return to /billboard/config-generator/
2. Dropdown now shows: "Teatro Comunale di Cambiano ✓"
3. Select it
4. Click "Load Configuration"
5. Configuration loads successfully!
```

---

## Prevention Tips

1. **Always upload configurations** after creating them
2. **Check for ✓ mark** before trying to load
3. **Keep backup copies** of all configuration files
4. **Test with small configs first** (5-10 rows)
5. **Verify file uploaded** by checking venue in Admin

---

## Advanced: Loading Configuration via Shell

If you need to check if a venue has a configuration file programmatically:

```python
from billboard.models import Venue

venue = Venue.objects.get(id=3)
print(f"Has config: {bool(venue.configuration_file)}")
if venue.configuration_file:
    print(f"File path: {venue.configuration_file.path}")
    print(f"File exists: {venue.configuration_file.storage.exists(venue.configuration_file.name)}")
```

---

## Still Having Issues?

### Check These:

1. **Venue exists**: Verify venue ID is correct in Admin
2. **File uploaded**: Check "Seating Configuration" section shows file
3. **File on disk**: Verify file exists in `media/venue_configs/`
4. **Permissions**: Ensure Django can read the uploaded file
5. **File format**: Must be valid JSON with correct structure

### Get More Info:

- Check browser console (F12 → Console tab)
- Look for the "Loading config from:" log message
- Review Django server logs for errors
- Use the test endpoint: `/billboard/api/test/`

---

## Summary

**The 404 error is normal and expected** when trying to load a configuration from a venue that doesn't have one yet.

**Solution**: Either create a new configuration or upload an existing one first, then you can load it for editing.

The dropdown now clearly shows which venues have configurations (✓ mark), making it easier to avoid this error.
