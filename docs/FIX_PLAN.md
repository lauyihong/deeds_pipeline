# Pipeline Fix Plan

Based on [VALIDATION_SUMMARY.md](VALIDATION_SUMMARY.md), there are **3 root causes** of failures affecting **44 deeds** (43% of validated set).

---

## Error 1: Wrong Plan Book/Page Selection (18 deeds)

### Problem
When multiple book/page combinations are extracted, the pipeline uses all of them without filtering. This results in scraping plans from wrong towns.

**Example (Deed 187)**:
- OCR extracted: Book 57, Page 67 (correct - Dracut)
- Pipeline also tried: Book 60, Page 67 (wrong - Chelmsford)
- Result: Used Chelmsford streets instead of Dracut streets

### Root Cause
In `step3_scraper.py`, the `process_single_deed()` function (lines 167-209):
- Iterates through ALL book/page combinations
- Aggregates ALL streets from ALL results
- Does NOT validate that scraped plan's town matches deed's town

### Fix Location
`deeds_pipeline/step3_scraper.py` - `process_single_deed()` function

### Fix Implementation
```python
# After line 195 in process_single_deed(), add town validation:

def process_single_deed(deed_record: Dict, use_cache: bool = True, headless: bool = True) -> Dict:
    ...
    deed_town = deed_record.get("city") or deed_record.get("town")  # From OCR/input

    for book, page in book_pages:
        try:
            result = scraper.process_record(book, page)

            # NEW: Validate scraped plan's town matches deed's town
            scraped_town = result.get("metadata", {}).get("search_result_info", {}).get("town", "")
            if deed_town and scraped_town:
                if scraped_town.upper() != deed_town.upper():
                    logger.warning(f"  Skipping book={book}, page={page}: town mismatch "
                                   f"(scraped={scraped_town}, expected={deed_town})")
                    continue  # Skip this result - wrong town

            scraper_results.append(result)
            streets = extract_streets_from_scraper_result(result)
            all_streets.extend(streets)
            ...
```

### Expected Impact
+18 deeds → Street match improves from 62.7% to ~80%

---

## Error 2: No Plan Book/Page Extracted from OCR (20 deeds)

### Problem
OCR fails to extract plan book/page references for some deeds, resulting in no streets to scrape.

### Root Cause
In `step2_ocr_extraction.py`, the LLM extraction may fail to parse plan references like:
- "Map One of the subdivision" (non-numeric book)
- "Plan 67" without explicit book number
- Unusual formats in older deeds

### Fix Location
`deeds_pipeline/step2_ocr_extraction.py` - extraction prompt and post-processing

### Fix Implementation

**Option A: Improve LLM prompt** (lines ~230-250)
```python
# Add more examples to the extraction prompt:
EXTRACTION_PROMPT = """
...
Extract plan_book and plan_pages. Examples:
- "Book of Plans 57, Plan 67" → plan_book: ["57"], plan_pages: ["67"]
- "recorded in Plan Book 123, Page 45" → plan_book: ["123"], plan_pages: ["45"]
- "shown on a plan recorded in Book 57" → plan_book: ["57"]
- Handle "Map One" as book reference if numeric book not found
...
"""
```

**Option B: Add regex fallback** (new function)
```python
def extract_plan_references_fallback(text: str) -> Tuple[List[str], List[str]]:
    """Regex fallback for plan book/page extraction when LLM fails."""
    books, pages = [], []

    patterns = [
        r'[Bb]ook\s*(?:of\s*)?[Pp]lans?\s*(\d+)',  # "Book of Plans 57"
        r'[Pp]lan\s*[Bb]ook\s*(\d+)',               # "Plan Book 57"
        r'[Bb]ook\s*(\d+)',                          # "Book 57"
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        books.extend(matches)

    page_patterns = [
        r'[Pp]lan\s*(\d+)',                          # "Plan 67"
        r'[Pp]age\s*(\d+)',                          # "Page 67"
    ]
    for pattern in page_patterns:
        matches = re.findall(pattern, text)
        pages.extend(matches)

    return list(set(books)), list(set(pages))
```

### Expected Impact
+10-15 deeds → Has Geolocation improves from 70.6% to ~80-85%

---

## Error 3: Geocoding Returns 0,0 Coordinates (10 deeds)

### Problem
When geocoding fails, coordinates default to 0,0 (Null Island) instead of being marked as failed.

### Root Cause
In `step4_geolocation.py`, the `ClusterResult` dataclass (lines 98-112) returns `cluster_center_lat=0.0, cluster_center_lon=0.0` when no candidates found.

### Fix Location
`deeds_pipeline/step4_geolocation.py` - `ClusterResult` handling

### Fix Implementation
```python
# In validate_and_cluster(), change the empty result handling (lines 98-112):

if not all_candidates:
    return ClusterResult(
        validated_streets=[],
        invalid_streets=streets,
        primary_town="UNKNOWN",
        cluster_center_lat=None,  # Changed from 0.0
        cluster_center_lon=None,  # Changed from 0.0
        cluster_radius_miles=None,  # Changed from 0.0
        final_address=None,
        confidence=0.0,
        geocoding_stats={...},
    )

# Also update step5_integration.py to handle None coordinates properly
```

**Note**: Already fixed in validation script (`validate_pipeline_accuracy.py` line 162) to reject 0,0. But should also fix upstream in step4.

### Expected Impact
Prevents false positives in "has_geolocation" metric. Actual fix is in Error 2 (getting more streets to geocode).

---

## Implementation Priority

| Priority | Error | Fix | Impact | Effort |
|----------|-------|-----|--------|--------|
| 1 | Wrong plan selection | Town validation in step3 | +18 deeds | Low |
| 2 | No plan extracted | Regex fallback in step2 | +10-15 deeds | Medium |
| 3 | 0,0 coordinates | Return None instead | Cleaner data | Low |

---

## Expected Results After Fixes

| Metric | Current | After Fix 1 | After All Fixes |
|--------|---------|-------------|-----------------|
| Town Match | 69.6% | ~85% | ~90% |
| Street Match | 62.7% | ~80% | ~85% |
| Has Geolocation | 70.6% | ~80% | ~85% |
| In Radius | 68.6% | ~80% | ~85% |
| **Overall** | **56.9%** | **~75%** | **~80%** |

---

## Files to Modify

1. `deeds_pipeline/step3_scraper.py` - Add town validation filter
2. `deeds_pipeline/step2_ocr_extraction.py` - Add regex fallback for plan extraction
3. `deeds_pipeline/step4_geolocation.py` - Return None instead of 0,0
4. `deeds_pipeline/step5_integration.py` - Handle None coordinates
