# Deeds Pipeline User Guide

**Complete guide for using, updating, and maintaining the restrictive covenants analysis pipeline**

## Table of Contents

1. [What's Included in This Package](#whats-included)
2. [Getting Started](#getting-started)
3. [Step-by-Step Tutorial: Running the Pipeline](#step-by-step-tutorial)
4. [Updating Maps and Datasets](#updating-maps-and-datasets)
5. [Running Custom Reports](#running-custom-reports)
6. [Data Dictionary & Metadata](#data-dictionary--metadata)
7. [Maintenance Guide](#maintenance-guide)
8. [Troubleshooting](#troubleshooting)

---

## What's Included

This package contains a complete data processing pipeline for analyzing historical property deed records and detecting restrictive covenants. Here's what you have:

### Core Pipeline Components

```
📦 Deeds Pipeline Package
├── 🔧 Processing Engine (deeds_pipeline/)
│   ├── Step 1: JSON Reformat
│   ├── Step 2: OCR & AI Extraction (Google Vision, Gemini, Mistral-RRC)
│   ├── Step 3: Web Scraping (MassLand Records)
│   ├── Step 4: Geolocation (OpenStreetMap + Clustering)
│   └── Step 5: Data Integration & Export
│
├── 📊 User Interfaces (script/)
│   ├── nbsample.ipynb - Interactive Jupyter Notebook (PRIMARY)
│   ├── run_pipeline.py - Command-line batch processor
│   ├── plot_covenant_hotspots.py - Map visualization generator
│   └── validate_pipeline_accuracy.py - Quality validation tool
│
├── 📁 Data (data/)
│   └── deed_reviews_northern_middlesex_20251103_110333.json (4.5 MB input)
│
├── 📈 Outputs (output/)
│   ├── notebook_final_output.json - Complete results (8.8 MB)
│   ├── notebook_final_output.csv - Spreadsheet format (227 KB)
│   └── covenant_hotspots.html - Interactive map (352 KB)
│
└── 📚 Documentation
    ├── README.md - Technical overview
    ├── QUICKSTART.md - Quick start guide
    └── USER_GUIDE.md - This comprehensive guide
```

### What This System Does

1. **Processes historical deed records** from Massachusetts (Northern Middlesex County)
2. **Detects restrictive covenants** using AI (racial/ethnic discrimination language)
3. **Geocodes properties** to map locations with clustering validation
4. **Generates interactive visualizations** showing covenant spread over time (1881-1958)
5. **Exports data** in multiple formats for analysis

### What You Get

- **570 deed records** processed and analyzed
- **542 successfully geocoded** properties (95.1% success rate)
- **Interactive heatmap** with time slider showing covenant evolution
- **Quality reports** with validation metrics
- **Structured data** ready for further research

---

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- **Python 3.8+** installed
- **Jupyter Notebook** for interactive use
- **Google Chrome browser** for web scraping
- **API access** (see below)

### Required API Keys

The pipeline uses three external services:

1. **Google Cloud Vision API** - OCR text extraction

   - Create project at https://console.cloud.google.com
   - Enable Vision API
   - Set `GOOGLE_VISION_PROJECT_ID` in `.env`

2. **Google Gemini API** - Structured data extraction

   - Get API key at https://ai.google.dev
   - Set `GEMINI_API_KEY` in `.env`

3. **Google Maps API** (Optional)
   - Used for enhanced geolocation
   - Falls back to OpenStreetMap if not provided

### Installation

```bash
# 1. Navigate to project directory
cd deeds_pipeline

# 2. Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
nano .env  # Edit and add your API keys

# 5. Verify installation
jupyter notebook  # Should open in browser
```

---

## Step-by-Step Tutorial

### Tutorial 1: Running the Full Pipeline (First Time)

**Time Required**: 2-4 hours (depending on dataset size)
**Interface**: Jupyter Notebook (Interactive)

#### Step 1: Launch the Notebook

```bash
# Start Jupyter Notebook
jupyter notebook script/nbsample.ipynb
```

Your browser will open showing the notebook interface.

#### Step 2: Execute Cell 1 - Environment Setup

**What it does**: Imports required libraries and sets up project paths

```python
# Cell 1: Environment Setup and Imports
import sys
import json
from pathlib import Path
import pandas as pd
from IPython.display import display

# Project root directory
PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'script' else Path.cwd()
print(f"Project root: {PROJECT_ROOT}")
```

**Expected Output**:

```
Project root: /path/to/deeds_pipeline
✓ All imports successful
✓ nest_asyncio applied for Jupyter compatibility
```

**Action**: Click "Run" or press `Shift+Enter`

#### Step 3: Execute Cells 2-4 - Steps 1-2 (Data Loading & OCR)

**Cell 2**: Step 1 - JSON Reformat

```python
from deeds_pipeline.step1_json_reformat import run_step1
result = run_step1()
```

**What happens**:

- Loads raw deed review data (742 records)
- Groups by deed_id (consolidates to 570 unique deeds)
- Saves to `output/step1_reformatted_by_deed_id.json`

**Duration**: ~1 second

---

**Cell 3**: Step 2 - OCR Extraction (LONGEST STEP)

```python
from deeds_pipeline.step2_ocr_extraction import run_step2
result = run_step2()
```

**What happens**:

- Processes deed images through Google Cloud Vision OCR
- Detects restrictive covenants using Mistral-RRC model
- Extracts structured data (addresses, dates) via Gemini API
- Shows progress bar for each deed

**Duration**: 1-3 hours (depends on number of images and API speed)

**Expected Output**:

```
Processing deed 1612 (1/570)
  Processing 2 images for deed 1612
  ✅ OCR completed! Text length: 2722 characters
  ✅ Keywords found: race, Caucasian, lease

Processing deed 1613 (2/570)
  ...
```

**💡 Tip**: This step can be interrupted and resumed. Results are cached.

#### Step 4: Execute Cells 5-7 - Steps 3-4 (Web Scraping & Geolocation)

**Cell 5**: Step 3 - Web Scraping

**What happens**:

- Opens Chrome browser (you'll see it)
- Scrapes MassLand Records website for property details
- Extracts street addresses for geolocation
- Fresh browser session per deed

**Duration**: 30-60 minutes

**Expected Output**:

```
[1/570] Processing deed 5767
  Browser driver initialized successfully
  Accessing: https://www.masslandrecords.com/...
  ✓ Found 1 search result(s)
  ✓ Extracted property information: 1 row(s)
  ✓ Deed 5767: Completed. Found 1 unique street(s)
```

---

**Cell 6**: Step 4 - Geolocation

**What happens**:

- Geocodes street addresses using OpenStreetMap API
- Validates locations using DBSCAN clustering
- Calculates confidence scores

**Duration**: 10-20 minutes

**Expected Output**:

```
[1/570] Processing deed 5767
  Geocoding 1 street(s)
  ✓ Cluster center: (42.6606, -71.2845)
  ✓ Confidence: 65.0%

Geocoded 542/570 deeds (95.1%)
Average confidence: 78%
```

#### Step 5: Execute Cell 8 - Step 5 (Integration)

**What happens**:

- Consolidates all processing results
- Generates quality report
- Exports to JSON and CSV

**Duration**: 5-10 seconds

**Expected Output**:

```
✓ JSON output: output/notebook_final_output.json
✓ CSV output: output/notebook_final_output.csv

Quality Report:
  total_deeds: 570
  geocoded_count: 542
  geocoded_rate: 95.1%
  avg_confidence: 0.78
```

#### Step 6: View Results

**Cell 9**: Create Interactive Map (Optional)

This cell generates an interactive Folium map showing all geocoded properties.

**To view final outputs**:

1. **JSON results**: `output/notebook_final_output.json`
2. **CSV results**: `output/notebook_final_output.csv`
3. **Interactive map**: Open in browser after running Cell 9

---

### Tutorial 2: Generating the Covenant Hotspot Visualization

After completing the pipeline, generate the time-slider heatmap:

```bash
# Run the visualization script
python script/plot_covenant_hotspots.py
```

**What happens**:

- Reads `output/notebook_final_output.csv`
- Creates heatmap with time slider (1881-1958)
- Saves to `output/covenant_hotspots.html`

**Output**:

```
Saved map to output/covenant_hotspots.html
```

**To view**:

1. Open `output/covenant_hotspots.html` in web browser
2. Use time slider at bottom to see covenant spread over time
3. Toggle "Static Hotspots" layer in top-right control
4. Click on hotspots for details

**Features**:

- **Time slider**: Years 1881-1958 + Unknown
- **Static layer**: Toggle-able overview
- **Color gradient**: Yellow (low) → Red → Dark red (high intensity)
- **Layer control**: Top-right corner

---

## Updating Maps and Datasets

### Scenario 1: Add New Deed Records

**When**: You receive new deed review data to process

**Steps**:

1. **Prepare new data file**

   ```bash
   # Place new data in data/ directory
   cp /path/to/new_deeds.json data/deed_reviews_new_batch.json
   ```

2. **Update configuration**

   ```python
   # Edit deeds_pipeline/config.py
   INPUT_JSON = DATA_DIR / "deed_reviews_new_batch.json"
   ```

3. **Run pipeline on new data**

   ```bash
   jupyter notebook script/nbsample.ipynb
   # OR for CLI:
   python script/run_pipeline.py
   ```

4. **Merge with existing results** (optional)

   ```python
   # Python script to merge JSON files
   import json

   # Load existing results
   with open('output/notebook_final_output.json', 'r') as f:
       existing = json.load(f)

   # Load new results
   with open('output/step5_final_integrated.json', 'r') as f:
       new_data = json.load(f)

   # Merge deeds
   existing['deeds'].update(new_data['deeds'])

   # Update metadata
   existing['metadata']['total_deeds'] = len(existing['deeds'])

   # Save merged results
   with open('output/merged_results.json', 'w') as f:
       json.dump(existing, f, indent=2)
   ```

5. **Regenerate visualization**
   ```bash
   python script/plot_covenant_hotspots.py
   ```

### Scenario 2: Update Existing Records (Re-geocode)

**When**: Geocoding failed for some records or you want to improve accuracy

**Steps**:

1. **Identify failed geocoding**

   ```python
   import pandas as pd

   df = pd.read_csv('output/notebook_final_output.csv')
   failed = df[df['geo_latitude'].isna()]
   print(f"Failed: {len(failed)} out of {len(df)}")
   print(failed[['deed_id', 'scraped_streets']])
   ```

2. **Run only Step 4 (Geolocation)**

   ```bash
   python script/run_pipeline.py --start 4 --stop 4
   ```

3. **Check improvements**
   ```python
   df_new = pd.read_csv('output/step5_final_integrated.csv')
   improved = len(df_new[df_new['geo_latitude'].notna()]) - len(df[df['geo_latitude'].notna()])
   print(f"Improved: {improved} additional properties geocoded")
   ```

### Scenario 3: Update Visualization Parameters

**When**: You want to change heatmap appearance (radius, colors, blur)

**Steps**:

1. **Edit visualization script**

   ```python
   # Open script/plot_covenant_hotspots.py

   # Find HeatMapWithTime configuration (around line 165)
   HeatMapWithTime(
       data=time_data,
       index=labels,
       radius=45,      # ← Change this (default 45)
       blur=0.85,      # ← Change this (0-1)
       max_opacity=0.6,  # ← Change this (0-1)
       min_opacity=0.3,  # ← Change this (0-1)
       gradient={       # ← Modify colors
           "0.10": "#fff3bf",  # Yellow
           "0.25": "#fdc777",  # Orange
           "0.45": "#f07c4a",  # Light red
           "0.65": "#d73027",  # Red
           "0.90": "#9b0000",  # Dark red
           "1.0": "#5a0000",   # Darkest red
       },
   )
   ```

2. **Regenerate map**

   ```bash
   python script/plot_covenant_hotspots.py
   ```

3. **Refresh browser** to view `output/covenant_hotspots.html`

**Parameter Guide**:

- `radius`: Hotspot size (10-50, default 45)
- `blur`: Edge softness (0.5-1.0, default 0.85)
- `max_opacity`: Maximum intensity (0.4-0.8, default 0.6)
- `gradient`: Color scale (hex colors)

---

## Running Custom Reports

### Report 1: Covenant Detection Statistics

**Purpose**: Count covenants by decade, city, or exclusion type

```python
import pandas as pd

# Load data
df = pd.read_csv('output/notebook_final_output.csv')

# Parse year from deed_date
df['year'] = pd.to_datetime(df['deed_date'], errors='coerce').dt.year
df['decade'] = (df['year'] // 10) * 10

# Count by decade
decade_counts = df.groupby('decade').size()
print("Covenants by Decade:")
print(decade_counts)

# Count by city
city_counts = df.groupby('city').size().sort_values(ascending=False)
print("\nTop 10 Cities:")
print(city_counts.head(10))

# Covenant detection rate
covenant_detected = df['covenant_detected'].sum()
total = len(df)
print(f"\nCovenant Detection Rate: {covenant_detected}/{total} ({covenant_detected/total*100:.1f}%)")
```

### Report 2: Geocoding Quality Analysis

**Purpose**: Identify low-confidence geocoding for manual review

```python
import pandas as pd

df = pd.read_csv('output/notebook_final_output.csv')

# Low confidence geocoding (< 50%)
low_confidence = df[df['geo_confidence'] < 0.5].copy()
low_confidence = low_confidence[['deed_id', 'geo_address', 'geo_confidence', 'scraped_streets']]

print(f"Low Confidence Geocoding: {len(low_confidence)} records")
low_confidence.to_csv('output/low_confidence_review.csv', index=False)
print("Saved to: output/low_confidence_review.csv")

# Summary statistics
print(f"\nGeocoding Statistics:")
print(f"  Total geocoded: {df['geo_latitude'].notna().sum()}/{len(df)}")
print(f"  Average confidence: {df['geo_confidence'].mean():.1%}")
print(f"  Median confidence: {df['geo_confidence'].median():.1%}")
print(f"  High confidence (>80%): {(df['geo_confidence'] > 0.8).sum()}")
```

### Report 3: Spatial Clustering Analysis

**Purpose**: Find geographic clusters of covenants

```python
import pandas as pd
from sklearn.cluster import DBSCAN
import numpy as np

df = pd.read_csv('output/notebook_final_output.csv')

# Get geocoded properties
geocoded = df[df['geo_latitude'].notna()].copy()
coords = geocoded[['geo_latitude', 'geo_longitude']].values

# DBSCAN clustering (epsilon in degrees, ~0.01 = ~1km)
clustering = DBSCAN(eps=0.01, min_samples=5).fit(coords)
geocoded['cluster'] = clustering.labels_

# Count clusters
n_clusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
print(f"Found {n_clusters} geographic clusters")

# Top 10 largest clusters
cluster_sizes = geocoded[geocoded['cluster'] != -1].groupby('cluster').size()
top_clusters = cluster_sizes.sort_values(ascending=False).head(10)

print("\nTop 10 Largest Clusters:")
for cluster_id, size in top_clusters.items():
    cluster_deeds = geocoded[geocoded['cluster'] == cluster_id]
    center_lat = cluster_deeds['geo_latitude'].mean()
    center_lon = cluster_deeds['geo_longitude'].mean()
    cities = cluster_deeds['city'].value_counts()
    print(f"  Cluster {cluster_id}: {size} deeds at ({center_lat:.4f}, {center_lon:.4f})")
    print(f"    Cities: {dict(cities.head(3))}")
```

### Report 4: Validation Against Ground Truth

**Purpose**: Compare pipeline results with manually verified data

```bash
# Run validation script
python script/validate_pipeline_accuracy.py
```

**Output**:

- `output/validation_results_detailed.csv` - Per-deed comparison
- `output/validation_metrics.json` - Accuracy metrics
- Console output with summary statistics

**Validation Metrics** (binary):

1. **Town Name Match**: Pipeline town matches manual city (Y/N, % success)
2. **Street Name Match**: Manual street found in scraped streets (Y/N, % success)
3. **Has Geolocation**: Pipeline has valid coordinates (Y/N, % success)
4. **In Cluster Radius**: Ground truth within predicted cluster area (Y/N, % success)
5. **Overall Match**: All 4 metrics true (%, ultimate accuracy measure)
6. **Distance**: Reference metric (miles from cluster center to ground truth)

---

## Data Dictionary & Metadata

### Input Data Schema

**File**: `data/deed_reviews_northern_middlesex_20251103_110333.json`

| Field                               | Type        | Description              | Example                  |
| ----------------------------------- | ----------- | ------------------------ | ------------------------ |
| `deed_review_id`                    | Integer     | Unique review identifier | 14                       |
| `deed_id`                           | Integer     | Deed document identifier | 1612                     |
| `city`                              | String/Null | City name                | "Lowell"                 |
| `deed_date`                         | String      | Deed recording date      | "1942-06-06"             |
| `addresses`                         | Array       | Street addresses         | ["123 Main St"]          |
| `is_restrictive_covenant`           | Boolean     | Manual review flag       | true                     |
| `exact_language_covenants`          | Array       | Extracted covenant text  | ["No person of..."]      |
| `grantors`                          | String      | Property sellers         | "John Smith, Jane Smith" |
| `grantees`                          | String      | Property buyers          | "Bob Johnson"            |
| `additional_locational_information` | String      | Extra location details   | "Near park"              |
| `exclusion_types`                   | Array       | Types of restrictions    | ["White people only"]    |
| `county`                            | String      | County name              | "Northern Middlesex"     |
| `full_texts`                        | Array       | Complete deed text       | [...]                    |
| `book_page_urls`                    | Array       | MassLand image URLs      | ["https://..."]          |

**Metadata**:

- **Source**: Massachusetts Covenants Project
- **Date Range**: 1881-1958
- **Geographic Scope**: Northern Middlesex County
- **Total Records**: 742 reviews → 570 unique deeds
- **File Size**: 4.5 MB
- **Format**: JSON array of objects

### Output Data Schema

**File**: `output/notebook_final_output.csv`

| Column                        | Type    | Description                | Example               |
| ----------------------------- | ------- | -------------------------- | --------------------- |
| `deed_id`                     | String  | Unique deed identifier     | "1612"                |
| `deed_date`                   | String  | ISO date                   | "1942-06-06"          |
| `city`                        | String  | City name                  | "Lowell"              |
| `county`                      | String  | County name                | "Northern Middlesex"  |
| `covenant_detected`           | Boolean | AI-detected covenant flag  | true                  |
| `ocr_text_length`             | Integer | Total OCR characters       | 5250                  |
| `scraped_streets`             | String  | Pipe-separated streets     | "Main St\|Oak Rd"     |
| `scraped_street_count`        | Integer | Number of streets found    | 2                     |
| `geo_latitude`                | Float   | Cluster center latitude    | 42.6511               |
| `geo_longitude`               | Float   | Cluster center longitude   | -71.3541              |
| `geo_confidence`              | Float   | Geocoding confidence (0-1) | 0.85                  |
| `geo_cluster_radius_miles`    | Float   | Property area radius       | 0.82                  |
| `geo_town`                    | String  | Geocoded town name         | "Lowell"              |
| `geo_address`                 | String  | Final geocoded address     | "Main St, Lowell, MA" |
| `step2_ocr_completed`         | Boolean | Step 2 success flag        | true                  |
| `step3_scraper_completed`     | Boolean | Step 3 success flag        | true                  |
| `step4_geolocation_completed` | Boolean | Step 4 success flag        | true                  |

**Metadata**:

- **Format**: CSV with headers
- **Encoding**: UTF-8
- **Size**: ~227 KB (570 rows)
- **Missing Values**: Empty string or null
- **Generated**: By Step 5 integration

### Visualization Data

**File**: `output/covenant_hotspots.html`

- **Format**: Self-contained HTML with embedded JavaScript
- **Size**: ~352 KB
- **Libraries**: Leaflet.js, Folium, HeatMapWithTime plugin
- **Interactivity**: Time slider, layer toggle, zoom/pan
- **Time Range**: 1881-1958 (25 time frames)
- **Basemap**: CartoDB Positron
- **Projection**: Web Mercator (EPSG:3857)

**Heatmap Parameters**:

- `radius`: 45 pixels
- `blur`: 0.85 (0-1 scale)
- `max_opacity`: 0.6
- `min_opacity`: 0.3
- `gradient`: 6-stop yellow→red scale

---

## Troubleshooting

### Issue: Pipeline Stops During Step 2 (OCR)

**Symptoms**: Notebook cell running for hours, then crashes

**Causes**:

- API quota exceeded
- Network timeout
- Out of memory

**Solutions**:

1. **Check API quota**

   - Google Cloud Console → Vision API → Quotas
   - Increase quota or wait for reset (usually 24 hours)

2. **Resume from cache**

   ```bash
   # Pipeline automatically resumes where it left off
   # Just re-run the cell
   ```

3. **Process in smaller batches**
   ```python
   # Edit deeds_pipeline/config.py
   BATCH_SIZE = 5  # Reduce from default 10
   ```

### Issue: Geocoding Returns Low Confidence

**Symptoms**: Many properties with `geo_confidence < 0.5`

**Causes**:

- Street addresses too vague ("Main Street")
- No street addresses found in scraping
- Cluster validation fails (streets far apart)

**Solutions**:

1. **Review specific cases**

   ```python
   import pandas as pd
   df = pd.read_csv('output/notebook_final_output.csv')
   low_conf = df[df['geo_confidence'] < 0.5]
   print(low_conf[['deed_id', 'scraped_streets', 'geo_town']])
   ```

2. **Manual address enrichment**

   ```python
   # Create manual_addresses.csv with:
   # deed_id,manual_address,city,state
   # 1612,"123 Main Street","Lowell","MA"

   # Then run preprocess script
   python script/preprocess_manual_geocoding.py
   ```

3. **Adjust clustering parameters**
   ```python
   # Edit deeds_pipeline/step4_geolocation.py
   # Find StreetClusteringValidator initialization
   # Adjust eps (distance threshold) and min_samples
   ```

### Issue: Chrome/Selenium Errors in Step 3

**Symptoms**: "ChromeDriver not found" or browser crashes

**Solutions**:

1. **Update Chrome and ChromeDriver**

   ```bash
   # Chrome auto-updates, but verify:
   google-chrome --version

   # Selenium 4.6+ auto-manages ChromeDriver
   pip install --upgrade selenium
   ```

2. **Run in visible mode (debugging)**

   ```python
   # Edit deeds_pipeline/config.py
   CHROME_HEADLESS = False
   ```

3. **Clear Selenium cache**
   ```bash
   rm -rf ~/.cache/selenium
   ```

### Issue: Map Visualization Not Displaying

**Symptoms**: Blank page or JavaScript errors in `covenant_hotspots.html`

**Solutions**:

1. **Check browser console**

   - Open `covenant_hotspots.html`
   - Press F12 → Console tab
   - Look for error messages

2. **Common fix: Re-generate with correct parameters**

   ```bash
   # Ensure data file exists
   ls -lh output/notebook_final_output.csv

   # Re-run visualization
   python script/plot_covenant_hotspots.py
   ```

3. **Verify blur parameter** (must be 0-1, not integer)
   ```python
   # In plot_covenant_hotspots.py
   blur=0.85  # ✓ Correct
   # NOT blur=10  # ✗ Wrong - causes errors
   ```

### Issue: Validation Script Fails

**Symptoms**: `FileNotFoundError: manual_addresses_geocoded.csv`

**Solution**:

```bash
# This file contains ground truth data for validation
# If missing, validation cannot run
# Either:
# 1. Skip validation (not critical)
# 2. Create ground truth file:
#    output/manual_addresses_geocoded.csv
#    with columns: deed_id,latitude,longitude,address
```

### Getting Help

**Error logs**:

```bash
# Check logs for detailed error messages
cat logs/pipeline.log
cat logs/step2.log  # For Step 2 errors
cat logs/step3.log  # For Step 3 errors
```

**Community resources**:

- Folium documentation: https://python-visualization.github.io/folium/
- Selenium docs: https://selenium-python.readthedocs.io/
- Google Cloud Vision: https://cloud.google.com/vision/docs

**Contact**:

- For pipeline issues: Check logs first
- For data questions: Review data dictionary
- For API issues: Check provider status pages

---

## Appendix: Quick Reference

### Common Commands

```bash
# Start pipeline (interactive)
jupyter notebook script/nbsample.ipynb

# Start pipeline (batch)
python script/run_pipeline.py

# Generate visualization
python script/plot_covenant_hotspots.py

# Run validation
python script/validate_pipeline_accuracy.py

# Clean cache
rm -rf cache/*

# View logs
tail -f logs/pipeline.log
```

### File Locations

| Type         | Location                            | Description               |
| ------------ | ----------------------------------- | ------------------------- |
| Input data   | `data/deed_reviews_*.json`          | Raw deed reviews          |
| Final output | `output/notebook_final_output.json` | Complete results          |
| CSV export   | `output/notebook_final_output.csv`  | Spreadsheet format        |
| Map          | `output/covenant_hotspots.html`     | Interactive visualization |
| Config       | `deeds_pipeline/config.py`          | Settings                  |
| Logs         | `logs/*.log`                        | Execution logs            |
| Cache        | `cache/`                            | Auto-managed              |

### Key Metrics to Track

- **Processing Rate**: Deeds/hour (Step 2: ~10-20, Step 3: ~8-12)
- **Geocoding Success**: Target >90%
- **Average Confidence**: Target >75%
- **API Costs**: Monitor Google Cloud billing
- **Data Quality**: Run validation quarterly

---

**Document Version**: 1.0
**Last Updated**: December 2024
**Maintained By**: Deeds Pipeline Project Team
