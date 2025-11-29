# Validation Metrics Guide

## What Each Metric Measures

### 1. **Location Radius Match Rate**
- **What it measures**: Does the pipeline geocode produce valid latitude/longitude coordinates?
- **How it works**: Checks if `geo_latitude` and `geo_longitude` are not empty/null
- **Range**: 0-100%
- **Good score**: 70%+ (most deeds successfully geocoded)
- **Example**:
  - ✓ PASS: Deed has lat=42.5623, lon=-71.3452
  - ✗ FAIL: Deed has lat=NaN or lon=NaN

---

### 2. **Street Name Match Rate**
- **What it measures**: Do the streets scraped from MassLand match the ground truth street name?
- **How it works**:
  - Extracts street name from manual address (part before first comma)
  - Parses semicolon-separated streets from pipeline output
  - Checks for exact match or substring match (case-insensitive)
- **Range**: 0-100%
- **Good score**: 50%+ (web scraping is noisy, not all deeds return all streets)
- **Example**:
  - Manual: "Valley Road, Dracut, MA"
  - Pipeline scraped: "VALLEY ROAD; HILLSIDE TERR; LOWELL ST"
  - ✓ MATCH: "VALLEY ROAD" found in pipeline streets

---

### 3. **City/Town Match Rate**
- **What it measures**: Does the geocoded town match the manual ground truth city?
- **How it works**:
  - Extracts city from manual address (part after first comma)
  - Compares with `geo_town` from pipeline (exact match)
- **Range**: 0-100%
- **Good score**: 50%+ (geolocation API may return different town names)
- **Example**:
  - Manual: "Valley Road, Dracut"
  - Pipeline: "geo_town: Dracut"
  - ✓ MATCH

---

### 4. **Average String Similarity**
- **What it measures**: How similar is the full address string from pipeline vs manual?
- **How it works**:
  - Uses sequence matching algorithm (SequenceMatcher)
  - Compares normalized addresses character-by-character
  - Returns percentage of matching characters
- **Range**: 0-100%
- **Why it's low**:
  - Pipeline address: "99, Valley Road, Dracut, MA" (from geocoding API)
  - Manual address: "Valley Road, Dracut" (user-edited)
  - Different format = lower similarity even if same location
- **Good score**: 20%+ (addresses have different formats)

---

### 5. **Average Overall Match Rate**
- **What it measures**: Overall pipeline quality = how many of the 3 main criteria match?
- **How it works**:
  - Counts matches: location_match + street_match + city_match
  - `match_rate = (matches / 3) × 100`
  - Average across all validated deeds
- **Range**: 0-100%
- **Good score**: 60%+ (combination of multiple metrics)
- **Example**:
  - Deed has: location ✓, street ✓, city ✓ = 3/3 = 100%
  - Deed has: location ✓, street ✗, city ✓ = 2/3 = 67%
  - Deed has: location ✗, street ✗, city ✓ = 1/3 = 33%

---

## Current Pipeline Results

```json
{
  "total_validation_deeds": 111,
  "deeds_in_pipeline": 102,
  "deeds_pending": 9,
  "location_radius_match_rate": 80.4,
  "street_name_match_rate": 56.9,
  "city_town_match_rate": 52.9,
  "average_string_similarity": 25.9,
  "average_overall_match_rate": 63.4
}
```

### Interpretation
- **80.4% Location**: Most deeds successfully geocoded ✓
- **56.9% Street Match**: Better than expected for web scraping
- **52.9% City Match**: Reasonable given API variations
- **25.9% String Similarity**: Expected (different formats)
- **63.4% Overall**: Good pipeline quality

---

## Output Files

- **validation_results_detailed.csv**: Row for each deed with all metrics
- **validation_metrics.json**: Summary metrics shown above

---

## Key Insight

The pipeline is **working well** despite lower string similarity scores. The important metrics are:
1. Location geocoding (80%+) ✓
2. Street matching (56%) ✓ Good for web scraping
3. City matching (52%) ✓ Reasonable given API variations

The combined **63.4% overall match rate** indicates the pipeline successfully identifies most deed locations.
