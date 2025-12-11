# Deeds Pipeline

A comprehensive data processing pipeline for analyzing historical property deed records, detecting restrictive covenants, extracting geographic information, and generating interactive visualizations.

## Overview

This pipeline processes deed review data through 5 sequential steps:

1. **JSON Reformat**: Convert from `deed_review_id` indexing to `deed_id` indexing
2. **OCR & Extraction**: Extract text via Google Vision, detect covenants via Mistral-RRC, structure data via Gemini
3. **Web Scraping**: Scrape MassLand Records for property book/page references
4. **Geolocation**: Geocode addresses using Nominatim OSM API with clustering validation
5. **Data Integration**: Consolidate all results and export to JSON/CSV

**Status**: ✅ All pipeline steps fully implemented and operational

## Project Structure

```
deeds_pipeline/
├── data/                                    # Input data directory
│   └── deed_reviews_northern_middlesex_20251103_110333.json
├── deeds_pipeline/                          # Main package (core logic)
│   ├── config.py                            # Configuration settings
│   ├── step1_json_reformat.py              # Step 1: JSON reformat
│   ├── step2_ocr_extraction.py             # Step 2: OCR and extraction
│   ├── step3_scraper.py                    # Step 3: Web scraping
│   ├── step4_geolocation.py                # Step 4: Geolocation
│   ├── step5_integration.py                # Step 5: Data integration
│   └── utils/common.py                      # Shared utilities
├── script/                                  # Execution interfaces
│   ├── nbsample.ipynb                      # Interactive notebook (MAIN INTERFACE)
│   ├── run_pipeline.py                     # CLI batch processor
│   ├── plot_covenant_hotspots.py           # Generate interactive map
│   ├── validate_pipeline_accuracy.py       # Quality validation
│   └── preprocess_manual_geocoding.py      # Data preprocessing utility
├── output/                                  # Generated outputs
│   ├── notebook_final_output.json          # Final results (from notebook)
│   ├── notebook_final_output.csv           # Flattened data (from notebook)
│   ├── covenant_hotspots.html              # Interactive heatmap visualization
│   └── step[1-5]_*.json                    # Intermediate step outputs
├── tests/                                   # Unit and integration tests
├── cache/                                   # Auto-managed cache (excluded from git)
├── logs/                                    # Execution logs (excluded from git)
├── requirements.txt                         # Python dependencies
├── .env.example                             # Example environment variables
└── README.md                                # This file
```

## Installation

### 1. Clone the repository

```bash
cd /path/to/deeds_pipeline
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required API keys:
- `GOOGLE_VISION_PROJECT_ID`: For Google Cloud Vision OCR
- `GEMINI_API_KEY`: For Gemini AI extraction
- `GOOGLE_MAPS_API_KEY`: For geolocation services

### 5. Install Chrome/ChromeDriver (for Step 3)

Step 3 uses Selenium for web scraping. Ensure you have:
- Google Chrome browser installed
- ChromeDriver (Selenium 4.6+ manages this automatically)

## Usage

### Primary Method: Interactive Notebook (Recommended)

```bash
jupyter notebook script/nbsample.ipynb
```

This is the **recommended interface** for running the pipeline. It provides:
- 📊 **Interactive execution**: Run steps cell-by-cell with intermediate visualization
- 🔍 **Debugging**: Inspect data at each step
- 📈 **Progress monitoring**: Real-time logs and progress bars
- 🗺️ **Auto-visualization**: Generates interactive maps automatically
- 💾 **Checkpoints**: Save intermediate results for debugging

The notebook includes:
- Cell-by-cell execution of all 5 pipeline steps
- Data quality reports and statistics
- Interactive Folium map generation
- Result preview and analysis

### Alternative: CLI Batch Processing

For automated/production runs:

```bash
# Run the full pipeline (Steps 1-5)
python script/run_pipeline.py

# Run specific step range
python script/run_pipeline.py --start 1 --stop 3

# Run single step
python script/run_pipeline.py --start 2 --stop 2
```

### Post-Processing: Generate Visualizations

After pipeline completion:

```bash
# Generate interactive covenant hotspot heatmap
python script/plot_covenant_hotspots.py

# Validate pipeline accuracy against ground truth
python script/validate_pipeline_accuracy.py
```

### Advanced: Run Individual Steps

For debugging specific steps:

```bash
python -m deeds_pipeline.step1_json_reformat
python -m deeds_pipeline.step2_ocr_extraction
# etc.
```

## Pipeline Steps in Detail

### Step 1: JSON Reformat
**Input**: `data/deed_reviews_northern_middlesex_20251103_110333.json`
**Output**: `output/step1_reformatted_by_deed_id.json`

Groups multiple deed reviews by `deed_id` and consolidates metadata. Transforms review-centric data structure to deed-centric.

### Step 2: OCR and Information Extraction
**Input**: `output/step1_reformatted_by_deed_id.json`
**Output**: `output/step2_ocr_extracted.json`

Processes deed images through three AI services:
- **Google Cloud Vision OCR**: Extract text from deed images
- **Mistral-RRC Model**: Detect restrictive covenant language
- **Gemini API**: Extract structured information (addresses, dates, parties)

Implements keyword detection for covenant-related terms (race, Caucasian, lease restrictions, etc.).

### Step 3: Web Scraping
**Input**: `output/step2_ocr_extracted.json`
**Output**: `output/step3_scraper_data.json`

Automates MassLand Records website scraping using Selenium:
- Searches by book/page numbers
- Extracts property details, grantor/grantee information
- Collects street addresses for geolocation
- Fresh browser session per deed to prevent session pollution

### Step 4: Geolocation
**Input**: `output/step3_scraper_data.json`
**Output**: `output/step4_geolocation.json`

Geocodes street addresses using OpenStreetMap Nominatim API:
- Asynchronous HTTP requests for performance
- **Street Clustering Validation**: Uses DBSCAN clustering to identify primary property location
- Calculates cluster center coordinates and radius
- Confidence scoring based on cluster density

### Step 5: Data Integration
**Input**: `output/step4_geolocation.json`
**Output**:
- `output/notebook_final_output.json` (full nested structure)
- `output/notebook_final_output.csv` (flattened for analysis)

Consolidates all processing results and generates comprehensive quality reports including:
- Processing completion rates per step
- Geocoding success rate and average confidence
- Covenant detection statistics

## Output Files

### Primary Outputs

**1. `output/notebook_final_output.json`** - Complete nested data structure
```json
{
  "metadata": {
    "total_deeds": 570,
    "quality_report": {
      "geocoded_count": 542,
      "geocoded_rate": "95.1%",
      "avg_confidence": 0.78,
      ...
    }
  },
  "deeds": {
    "1612": {
      "deed_id": "1612",
      "deed_date": "1942-06-06",
      "county": "Northern Middlesex",
      "ocr_results": [...],
      "scraper_results": [...],
      "geolocation": {
        "cluster_center_lat": 42.6511,
        "cluster_center_lon": -71.3541,
        "cluster_radius_miles": 0.82,
        "confidence": 0.85,
        "validated_streets": ["Main Street", "Oak Road"]
      }
    }
  }
}
```

**2. `output/notebook_final_output.csv`** - Flattened for spreadsheet analysis

Columns include:
- `deed_id`, `city`, `deed_date`, `county`
- `covenant_detected` (boolean)
- `scraped_streets`, `scraped_street_count`
- `geo_latitude`, `geo_longitude`, `geo_confidence`
- `geo_cluster_radius_miles`, `geo_town`
- Processing status flags (`step2_ocr_completed`, etc.)

**3. `output/covenant_hotspots.html`** - Interactive Folium heatmap visualization

Features:
- **Time slider**: Visualize covenant hotspots across years (1881-1958)
- **Static heatmap layer**: Toggle-able overview layer
- **Layer control**: Switch between time-based and static views
- **Custom gradient**: Color-coded intensity (yellow → red → dark red)
- **Clickable markers**: Hover for deed details (generated by `plot_covenant_hotspots.py`)

### Intermediate Outputs

- `output/step1_reformatted_by_deed_id.json`
- `output/step2_ocr_extracted.json`
- `output/step3_scraper_data.json`
- `output/step4_geolocation.json`
- `output/notebook_step3_checkpoint.json` (from notebook execution)
- `output/notebook_step4_checkpoint.json` (from notebook execution)

## Configuration

Edit `deeds_pipeline/config.py` to customize:
- Input/output file paths
- Batch sizes
- API timeout settings
- Cache settings
- Logging levels

## Caching

The pipeline includes built-in caching to avoid re-processing:
- Each step checks for cached results before processing
- Cache expires after 30 days (configurable)
- Disable caching by setting `ENABLE_CACHE = False` in `config.py`

## Logging

Logs are saved to the `logs/` directory:
- `pipeline.log`: Main pipeline execution log
- `step1.log`, `step2.log`, etc.: Individual step logs

Log level can be configured in `config.py` (default: INFO).

## Error Handling

The pipeline includes robust error handling:
- Each step can be run independently
- Errors are logged with full stack traces
- Failed records are tracked and reported
- Cache allows resuming from failures

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test files
pytest tests/test_step2.py
pytest tests/test_end_to_end.py
```

### Adding New Features

To extend the pipeline:
1. Add new utility functions to `deeds_pipeline/utils/common.py`
2. Update `config.py` with new configuration options
3. Modify step files as needed
4. Update test files and documentation

## Troubleshooting

### Common Issues

**Issue**: Google Vision API authentication fails  
**Solution**: Ensure `GOOGLE_VISION_PROJECT_ID` is set and you're authenticated with Google Cloud

**Issue**: Selenium can't find Chrome  
**Solution**: Install Chrome browser and ensure it's in your PATH

**Issue**: Out of memory during processing  
**Solution**: Reduce `BATCH_SIZE` in `config.py`

**Issue**: API rate limits  
**Solution**: The pipeline includes caching and retry logic. Consider processing in smaller batches.

## Contributing

This is an internal research tool. For major changes:
1. Test on a small subset of data first
2. Update documentation
3. Add logging for new features

## License

Internal use only.

## Contact

For questions or issues, contact the project maintainer.
