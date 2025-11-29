# Validation Metrics Guide (V3 - Binary Metrics)

## Overview

All metrics are **binary** (True/False, 1/0) for clear interpretation.

1. **Town Match** - Loosest (just checks city name)
2. **Street Match** - Medium (checks if street is in scraped list)
3. **Has Geolocation** - Medium (checks if coordinates exist)
4. **In Radius** - Strictest (checks if ground truth is within cluster radius)

---

## Metrics

### 1. Town Name Match (Binary)

- **What it measures**: Does the pipeline's geocoded town match the manual city?
- **How it works**: Exact string comparison (case-insensitive) between `geo_town` and manual `city`
- **Values**: 1 (match) or 0 (no match)
- **Example**:
  - Manual city: "Dracut"
  - Pipeline geo_town: "Dracut"
  - Result: **1** (match)

---

### 2. Street Name Match (Binary)

- **What it measures**: Is the ground truth street name found in the scraped streets?
- **How it works**:
  - Extracts street name from manual address (removes house number)
  - Parses semicolon-separated `scraped_streets` from pipeline
  - Checks for exact or substring match (case-insensitive)
- **Values**: 1 (found) or 0 (not found)
- **Example**:
  - Manual: "23 HILLCREST RD, DRACUT, MA" → Street: "HILLCREST RD"
  - Pipeline scraped_streets: "HILLCREST RD; HILLTOP RD; VALLEY RD"
  - Result: **1** (found)

---

### 3. Has Geolocation (Binary)

- **What it measures**: Did the pipeline produce valid coordinates?
- **How it works**: Checks if `geo_latitude` and `geo_longitude` are both non-null
- **Values**: 1 (has coords) or 0 (no coords)
- **Example**:
  - Pipeline: lat=42.687, lon=-71.365
  - Result: **1** (has geolocation)

---

### 4. In Cluster Radius (Binary)

- **What it measures**: Is the actual ground truth location within the pipeline's predicted cluster radius?
- **How it works**:
  1. Geocodes the manual address to get ground truth lat/lon (preprocessed)
  2. Uses Haversine formula to calculate distance from ground truth to cluster center
  3. Compares distance to `geo_cluster_radius_miles`
- **Values**: 1 (inside radius) or 0 (outside radius)
- **Why this matters**: This is the true test of whether the pipeline correctly locates the deed
- **Example**:
  - Ground truth: lat=42.688, lon=-71.363
  - Cluster center: lat=42.687, lon=-71.365
  - Cluster radius: 0.5 miles
  - Distance: 0.12 miles
  - Result: **1** (0.12 < 0.5, inside radius)

---

## Overall Metric

### All Match (Perfect Score)

- **What it measures**: Deeds where ALL 4 metrics are True
- **Calculation**: `town_match AND street_match AND has_geolocation AND in_radius`
- **Interpretation**: Complete pipeline success for this deed

---

## Detailed Breakdown

The validation also shows how many metrics matched per deed:

- **4/4 matched**: Perfect - all criteria met
- **3/4 matched**: Good - minor issue
- **2/4 matched**: Partial success
- **1/4 matched**: Poor result
- **0/4 matched**: Complete failure

---

## How to Run Validation

### Step 1: Preprocess Manual Addresses (One-time)

```bash
python script/preprocess_manual_geocoding.py
```

This geocodes all manual addresses and saves to `output/manual_addresses_geocoded.csv`.
Takes ~2 minutes (rate-limited to 1 request/second).

### Step 2: Run Validation

```bash
python script/validate_pipeline_accuracy.py
```

---

## Output Files

- **validation_results_detailed.csv**: Per-deed results with all metrics
- **validation_metrics.json**: Summary metrics in JSON format
