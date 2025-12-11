# Pipeline Validation Summary

## Validation Methodology

**Ground Truth**: 111 manually verified deed addresses with geocoded coordinates.

**Binary Metrics** (1 = pass, 0 = fail):
1. **Town Match**: Pipeline's `geo_town` matches manual city
2. **Street Match**: Manual street name appears in pipeline's `scraped_streets`
3. **Has Geolocation**: Pipeline has valid lat/lon (not null or 0,0)
4. **In Radius**: Ground truth coordinates fall within pipeline's `geo_cluster_radius_miles`

## Results (102 deeds found in pipeline)

| Metric | Pass | Rate |
|--------|------|------|
| Town Match | 71/102 | 69.6% |
| Street Match | 64/102 | 62.7% |
| Has Geolocation | 72/102 | 70.6% |
| In Radius | 70/102 | 68.6% |
| **All 4 Pass** | **58/102** | **56.9%** |

## Root Causes of Failures

### 1. No Geolocation (30 deeds)
- **20 deeds**: No plan book/page extracted from OCR → no streets to scrape
- **10 deeds**: Coordinates set to 0,0 (failed geocoding)

### 2. Wrong Streets Scraped (18 deeds)
Pipeline extracted wrong plan book/page from OCR text, resulting in streets from unrelated subdivisions.

**Example - Deed 187**:
- OCR text: "Book of Plans **57**, Plan 67" (Varnum Town, Dracut)
- Pipeline used: Book **60**, Page 67 (Chelmsford subdivision)
- Result: Scraped "CHELMSFORD ST; ROADWAY" instead of "HILLTOP RD"

### 3. Town Extraction Issues (31 deeds)
- Pipeline returns "UNKNOWN" when geocoding fails
- Some historical town names not mapped (e.g., "Varnum Town" → Dracut)

## Key Finding

**The validation metrics accurately reflect pipeline performance.** Low scores are due to genuine pipeline issues:
1. OCR failing to extract plan book/page references
2. Plan book/page selection choosing wrong combination when multiple exist
3. Geocoding failures defaulting to 0,0 coordinates

## Files

- `output/validation_results_detailed.csv` - Per-deed validation results
- `output/validation_metrics.json` - Aggregate metrics
- `script/validate_pipeline_accuracy.py` - Validation script
- `output/manual_addresses_geocoded.csv` - Ground truth data
