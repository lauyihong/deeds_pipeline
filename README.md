# Deeds Pipeline

A comprehensive data processing pipeline for analyzing deed reviews and extracting geographic information from historical property records.

## Overview

This pipeline processes deed review data through 5 sequential steps:

1. **JSON Reformat**: Convert from `deed_review_id` indexing to `deed_id` indexing
2. **OCR & Extraction**: Extract text and structured information from deed images
3. **Web Scraping**: Scrape additional geographic data from MassLand Records
4. **Geolocation**: Geocode addresses and calculate property locations
5. **Data Integration**: Consolidate all results into final dataset

## Project Structure

```
deeds_pipeline/
├── data/                          # Input data directory
│   └── deed_reviews_northern_middlesex_20251103_110333.json
├── deeds_pipeline/                # Main package
│   ├── __init__.py
│   ├── config.py                  # Configuration settings
│   ├── step1_json_reformat.py    # Step 1: JSON reformat
│   ├── step2_ocr_extraction.py   # Step 2: OCR and extraction
│   ├── step3_scraper.py          # Step 3: Web scraping
│   ├── step4_geolocation.py      # Step 4: Geolocation
│   ├── step5_integration.py      # Step 5: Data integration
│   └── utils/                     # Utility functions
│       ├── __init__.py
│       └── common.py
├── script/
│   └── run_pipeline.py           # Main pipeline runner
├── output/                        # Output directory (created automatically)
├── cache/                         # Cache directory (created automatically)
├── logs/                          # Log files (created automatically)
├── requirements.txt               # Python dependencies
├── .env.example                   # Example environment variables
└── README.md                      # This file
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

### Run the full pipeline

```bash
python script/run_pipeline.py
```

### Run specific steps

```bash
# Run steps 1-3 only
python script/run_pipeline.py --start 1 --stop 3

# Run step 2 only
python script/run_pipeline.py --start 2 --stop 2

# Resume from step 3
python script/run_pipeline.py --start 3 --stop 5
```

### Run individual steps

```bash
# Step 1
python -m deeds_pipeline.step1_json_reformat

# Step 2
python -m deeds_pipeline.step2_ocr_extraction

# Step 3
python -m deeds_pipeline.step3_scraper

# Step 4
python -m deeds_pipeline.step4_geolocation

# Step 5
python -m deeds_pipeline.step5_integration
```

## Pipeline Steps in Detail

### Step 1: JSON Reformat

**Input**: `data/deed_reviews_northern_middlesex_20251103_110333.json`  
**Output**: `output/step1_reformatted_by_deed_id.json`

Groups multiple deed reviews by `deed_id` and consolidates information.

**TODO**: Implement the grouping logic in `reformat_deed_reviews()`.

### Step 2: OCR and Information Extraction

**Input**: `output/step1_reformatted_by_deed_id.json`  
**Output**: `output/step2_ocr_extracted.json`

Processes deed images through:
- Google Cloud Vision OCR
- Mistral-RRC model for covenant detection
- Gemini API for structured information extraction

**TODO**: 
- Implement `extract_text_with_google_vision()`
- Implement `detect_restrictive_covenant()`
- Implement `extract_deed_info_with_gemini()`

**Reference**: `other_repo/mistral_rrc_updated.ipynb`

### Step 3: Web Scraping

**Input**: `output/step2_ocr_extracted.json`  
**Output**: `output/step3_scraper_data.json`

Scrapes MassLand Records website for additional property information.

**TODO**:
- Implement `initialize_scraper()`
- Implement `scrape_massland_record()`

**Reference**: `other_repo/test_scrap/massland_scraper.py`

### Step 4: Geolocation

**Input**: `output/step3_scraper_data.json`  
**Output**: `output/step4_geolocation.json`

Geocodes street addresses and calculates property cluster centers.

**TODO**:
- Implement `initialize_clustering_validator()`
- Implement `geocode_streets()`

**Reference**: `other_repo/deed_geo_indexing/test_clustering_validator.py`

### Step 5: Data Integration

**Input**: `output/step4_geolocation.json`  
**Output**: 
- `output/step5_final_integrated.json` (full nested structure)
- `output/step5_final_integrated.csv` (flattened for analysis)

Consolidates all processing results and generates quality reports.

**Status**: ✅ Fully implemented

## Output Files

### JSON Output

The final JSON output contains:
```json
{
  "metadata": {
    "total_deeds": 100,
    "quality_report": { ... }
  },
  "deeds": {
    "1612": {
      "deed_id": 1612,
      "review_ids": [14, 15],
      "ocr_results": [...],
      "scraper_results": [...],
      "geolocation": { ... }
    }
  }
}
```

### CSV Output

Flattened structure with columns including:
- Basic deed information (deed_id, city, deed_date, etc.)
- Covenant detection results
- Extracted streets and locations
- Geocoded coordinates
- Processing status flags

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

### Implementing TODO Functions

The framework is complete, but Steps 1-4 have placeholder functions marked with `# TODO`.

To implement a TODO function:
1. Find the function marked with `# TODO` in the respective step file
2. Review the reference code in `other_repo/`
3. Implement the logic following the provided function signature
4. Test with a small dataset first

### Adding New Features

To extend the pipeline:
1. Add new utility functions to `deeds_pipeline/utils/common.py`
2. Update `config.py` with new settings
3. Modify step files as needed
4. Update this README

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
