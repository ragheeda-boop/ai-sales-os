# Phase 1C: Import Guide — Companies + Contacts

**Status**: 🟢 Ready to import  
**Date**: March 23, 2026  
**Timeline**: 1-2 hours total (includes test batch + full import)

---

## 📁 CSV Files Ready

| File | Records | Columns | Purpose |
|------|---------|---------|---------|
| `test_100_companies.csv` | 100 | 25 | Test batch - validate import process |
| `test_100_contacts.csv` | 100 | 41 | Test batch - validate relations |
| `IMPORT_companies_3606.csv` | 3,606 | 25 | Full import - all companies |
| `IMPORT_contacts_5898.csv` | 5,898 | 42 | Full import - all contacts |

---

## 🎯 Import Strategy (2-Phase Approach)

### PHASE 1: TEST BATCH (15 minutes)
- Import 100 companies + 100 contacts
- Validate data quality and relations
- Catch any mapping issues early

### PHASE 2: FULL IMPORT (45 minutes)
- Import 3,606 companies + 5,898 contacts
- Execute in sequence: Companies first, then Contacts
- Monitor for completion

---

## 📋 Step-by-Step: Test Batch Import

### Step 1: Import 100 Test Companies

1. **Open Notion** → Navigate to **🏢 Companies** database
2. Click **+** button (top right) → **Import**
3. **Choose CSV** → Upload **`test_100_companies.csv`**
4. **Column Mapping** screen appears:
   - Verify these critical mappings:
     - `Apollo Account Id` → **Apollo Account Id** (TEXT, UNIQUE)
     - `Company Name` → **Company Name** (TITLE)
     - `Domain` → **Domain** (TEXT)
     - Other columns auto-map to matching properties
   - ✅ If all look correct, proceed
   - ⚠️ If something's wrong, cancel and retry
5. Click **Import**
6. **Wait for completion** (30 seconds - 1 minute)
7. **Verify**: Should show ~100 records in Companies database

---

### Step 2: Import 100 Test Contacts

1. **Open Notion** → Navigate to **👤 Contacts** database
2. Click **+** → **Import**
3. **Choose CSV** → Upload **`test_100_contacts.csv`**
4. **Column Mapping** verification:
   - `Apollo Contact Id` → **Apollo Contact Id** (TEXT, UNIQUE)
   - `Full Name` → **Full Name** (TITLE)
   - `Apollo Account Id` → **Apollo Account Id** (TEXT, for linking)
   - `Email` → **Email** (EMAIL)
   - Other columns auto-map
5. Click **Import**
6. **Wait for completion**
7. **Verify**: Should show ~100 records in Contacts database

---

### Step 3: Validate Relations (TEST BATCH)

After both imports complete, **verify data integrity**:

✅ **Check Companies:**
- Open any company record
- Look for **Contact Count** (should be 1+)
- Look for **Contacts** relation (should show linked contacts)

✅ **Check Contacts:**
- Open any contact record
- Look for **Company** relation (should be populated with company name)
- Verify **Email** field has value

✅ **Check One Link:**
- Open a contact in test batch
- Click on **Company** relation
- Should navigate to linked company
- Go back and check **Contact Count** increased

**If relations are working**: ✅ Proceed to full import  
**If relations missing**: ❌ Something went wrong during import, contact support

---

## 📊 Step-by-Step: Full Import

### Step 1: Import 3,606 Companies

1. **Open Notion** → **🏢 Companies** database
2. Click **+** → **Import**
3. **Choose CSV** → Upload **`IMPORT_companies_3606.csv`**
4. **Verify column mapping** (same as test batch)
5. Click **Import**
6. **⏳ Wait for completion** (2-3 minutes for 3,606 records)
7. **Verify count**: Should show 3,606 total records (or 3,706 if test batch wasn't deleted)

---

### Step 2: Import 5,898 Contacts

1. **Open Notion** → **👤 Contacts** database
2. Click **+** → **Import**
3. **Choose CSV** → Upload **`IMPORT_contacts_5898.csv`**
4. **Verify column mapping** (same as test batch)
5. Click **Import**
6. **⏳ Wait for completion** (3-5 minutes for 5,898 records)
7. **Verify count**: Should show 5,898 total records (or 5,998 if test batch wasn't deleted)

---

## ✅ Phase 1D: Final Validation

### Quick Health Checks

```
COMPANIES DATABASE:
☐ Total records: 3,606 (or 3,706 with test batch)
☐ Apollo Account Id: 100% populated and unique
☐ Domain: 100% populated
☐ Contact Count: Numbers visible (1, 2, 3, etc.)
☐ Contacts relation: Visible in column

CONTACTS DATABASE:
☐ Total records: 5,898 (or 5,998 with test batch)
☐ Apollo Contact Id: 100% populated and unique
☐ Full Name: 100% populated
☐ Email: 100% populated (5,898/5,898)
☐ Company relation: All rows linked

RELATIONS:
☐ Pick random contact → Company relation works
☐ Pick random company → Contact Count > 0
☐ Pick random company → Contacts relation shows names
```

### Spot-Check Random Records

1. **Search for a company**: Use Notion search
   - Example: Search "Alkhair" or "Apple" or any company name
   - Open record → Verify all fields populated
   - Check **Contact Count** (should be 2+)
   - Check **Contacts** relation (should show list)

2. **Search for a contact**: 
   - Example: Search a first name
   - Open record → Verify email is present
   - Check **Company** relation (should show company name)
   - Click company → Verify **Contact Count** includes this contact

---

## 🚨 Troubleshooting

### Issue: "Column not found" during import

**Solution**: Column name mismatch  
- Cancel import
- Verify CSV file has correct column headers
- Try again with fresh file

### Issue: Relations not showing after import

**Possible cause**: Apollo Account Id not matching between companies and contacts

**Solution**:
- Verify both databases have same Apollo Account Id values
- Check if import is still processing (can take 5+ minutes)
- Manual relationship linking (last resort): Open contact → type company name in Company field

### Issue: Duplicate records appearing

**Solution**: 
- Check if Apollo Account Id is marked UNIQUE in properties
- If import runs twice, delete extra records

### Issue: Import hangs or takes >10 minutes

**Solution**:
- This is unusual for CSV import
- Try closing and reopening Notion
- If still stuck, start with smaller batch (500 records at a time)

---

## 📝 Import Completion Checklist

- [ ] Test batch companies imported (100)
- [ ] Test batch contacts imported (100)
- [ ] Test batch relations validated
- [ ] Full companies imported (3,606)
- [ ] Full contacts imported (5,898)
- [ ] Total records match expected count
- [ ] Relations verified (sample contacts show companies)
- [ ] Contact Count rollup working (sample companies show >0)
- [ ] Random spot-check passed

---

## 🎉 You're Done!

Once all 5,898 contacts are imported with working relations to 3,606 companies:

✅ **Phase 1C Complete**  
✅ **Phase 1D Complete (validation)**

Your AI Sales OS is now **live in Notion** and ready for:
- Phase 2: Apollo API intent signals
- Phase 3: Lead scoring and tier assignment
- Phase 4: Task + opportunity creation
- Phase 5: Revenue execution

---

**Questions?** Check the Notion workspace for additional guides:
- "Manual Database Creation Guide"
- "Import Data from JSON Guide"
- "Sample Data Preview"

