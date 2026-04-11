# Notion Company↔Contact Relation Linking — Complete Execution Prompt

## MISSION
You need to link every Contact in the Notion Contacts database to its matching Company in the Companies database using the **Apollo Account Id** as the matching key.

---

## DATABASE DETAILS

### Companies Database
- **Database ID:** `331e04a62da74afe9ab6b0efead39200`
- **Data Source:** `collection://79a7f859-07f8-40a0-bfcf-6b17f2742c8e`
- **Total Records:** 3,606
- **Primary Key:** `Apollo Account Id` (text field)
- **Title Field:** `Company Name`

### Contacts Database
- **Database ID:** `9ca842d20aa9460bbdd958d0aa940d9c`
- **Data Source:** `collection://ac1dc287-a97d-4dea-ae62-7415e8118514`
- **Total Records:** 5,901 (5,898 have Apollo Account Id, 3 are blank)
- **Primary Key:** `Apollo Contact Id` (text field)
- **Linking Key:** `Apollo Account Id` (text field — same value as in Companies)
- **Relation Field to Update:** `Company` (relation to Companies data source)
- **Title Field:** `Full Name`

### Relation Schema
The `Company` field on Contacts is a **relation** property pointing to `collection://79a7f859-07f8-40a0-bfcf-6b17f2742c8e`.

To set it, you update the contact page with:
```json
{
  "Company": "[\"https://www.notion.so/<company_page_id>\"]"
}
```

---

## MATCHING LOGIC

```
For each Contact:
  1. Read its "Apollo Account Id"
  2. Find the Company page that has the same "Apollo Account Id"
  3. Update the Contact's "Company" relation with the Company's page URL
```

- If a contact has NO Apollo Account Id → skip it, log as orphan
- If a contact's Apollo Account Id has NO matching company → skip it, log as unmatched
- If a contact already has a Company relation set → skip it (don't overwrite)

---

## EXECUTION STRATEGY

### The API Limitation
The Notion query-database-view tool returns **maximum 100 records per query** with no pagination cursor. You must use filtered views to extract data in batches.

### Step 1: Build the Company Map
Create a helper view on the Companies database and extract ALL companies using **prefix-based filtering** on Apollo Account Id.

```
All Apollo Account IDs start with "6" and have two main prefixes:
- "68..." (~475 companies)
- "69..." (~3,131 companies)
```

**Approach:**
1. Create a table view `_CompanyMapper` on the Companies DB with SHOW "Apollo Account Id"
2. For each prefix below, update the view filter to `FILTER "Apollo Account Id" CONTAINS "<prefix>"`, query, and extract `{Apollo Account Id → page URL}` pairs
3. Use progressively longer prefixes for groups > 100

**Prefix distribution (4-char):**
```
68b4: 384  → needs 5-char split (68b41: ?, 68b42: ?)
694a: 550  → needs 5-char split (694a9: ?, 694ab: ?)
695b: 1235 → needs 6-char+ splits
6953: 222  → needs 5-char split
698c: 245  → needs 5-char split
6965: 168  → needs 5-char split
6971: 182  → needs 5-char split
6970: 134  → needs 5-char split
6955: 105  → needs 5-char split
687f: 63   → single query
6914: 32   → single query
6949: 27   → single query
697a: 26   → single query
6996: 33   → single query
69ad: 32   → single query
698a: 14   → single query
698d: 7    → single query
(all others: <10 each)
```

**For large prefixes:** Keep adding characters until each group ≤ 100. Example:
- `695b` (1,235) → split to `695b9`, `695ba`, `695bb`, etc.
- If `695ba` still > 100 → split to `695ba9`, `695bac`, etc.

**Parsing query results:**
Results may be saved to files. Parse with:
```python
import json
with open(filepath, 'r') as f:
    raw = json.load(f)
data = json.loads(raw[0]['text'])
results = data['results']  # list of dicts
for r in results:
    apollo_account_id = r['Apollo Account Id']
    page_url = r['url']  # this is the Notion page URL
```

### Step 2: Build the Contact List
Same approach on Contacts database:
1. Create a table view `_ContactMapper` on the Contacts DB with SHOW "Full Name", "Apollo Account Id", "Company"
2. Use prefix-based filtering on `Apollo Contact Id` (different field than Apollo Account Id!)
3. Extract: `{contact page URL, Apollo Account Id, current Company relation}`

**Contact Apollo Contact Id prefix distribution (4-char):**
```
694a: 1,897 → needs deep splits
695b: 1,675 → needs deep splits
6953: 719   → needs deep splits
698c: 462   → needs deep splits
6965: 266   → needs splits
6971: 229   → needs splits
6970: 210   → needs splits
698a: 66    → single query
6996: 61    → single query
698d: 49    → single query
69ad: 46    → single query
699a: 32    → single query
6977: 29    → single query
69a3: 26    → single query
(all others: <25 each)
```

**IMPORTANT:** Filter contacts by `Apollo Contact Id` field (not Apollo Account Id!) since that's the unique identifier per contact.

### Step 3: Execute the Linking
For each contact:
1. Look up its `Apollo Account Id` in the Company Map
2. If found AND the contact's current `Company` relation is empty:
   ```
   notion-update-page:
     page_id: <contact_page_id>
     command: update_properties
     properties: {"Company": "[\"<company_page_url>\"]"}
   ```
3. Log the result

**Execute updates in parallel batches of 3-5** for speed.

### Step 4: Verify
After all updates:
1. Query the Contacts "By Company" view to see grouped contacts
2. Count how many contacts now have Company relations set
3. Report: linked count, skipped count, orphan count, error count

---

## CRITICAL RULES

1. **NEVER overwrite existing Company relations** — only fill empty ones
2. **Company URLs must come from the Companies database** (page URLs starting with `https://www.notion.so/32c69edd...` from the Companies view queries). Do NOT use contact page URLs.
3. **The matching key is Apollo Account Id** — present in both tables, used to match contacts to companies
4. **Apollo Contact Id ≠ Apollo Account Id** — they are different fields!
5. **Validate before updating:** Ensure the company_url ≠ contact_url (they must be different pages)
6. **Log everything:** Track progress with counts after each batch

---

## EXPECTED RESULTS

- ~5,839 contacts should be linkable (those with Apollo Account Id matching a company)
- ~62 contacts will be unmatched (3 missing Apollo Account Id + 59 ambiguous company names from the source data)
- 0 errors expected if matching logic is correct

---

## ALREADY COMPLETED

- 51 contacts have already been linked (C-Suite batch from prior session)
- Skip any contact that already has a Company relation value

---

## VIEW CLEANUP

After completion, delete the helper views:
- `_CompanyMapper`
- `_ContactMapper`
- Any other `_LinkHelper*` or `_PrefixHelper*` views created during execution
