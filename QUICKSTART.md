# Quick Start Guide

## Installation

### 1. Install Dependencies

```bash
cd deeds_pipeline
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required API keys:
- `GOOGLE_VISION_PROJECT_ID` - Google Cloud Vision OCR
- `GEMINI_API_KEY` - Gemini AI extraction
- `GOOGLE_MAPS_API_KEY` - (Optional, uses OpenStreetMap by default)

### 3. Install Chrome

Step 3 (web scraping) requires Chrome browser for Selenium automation.

## Running the Pipeline

### ⭐ Primary Method: Interactive Notebook (Recommended)

```bash
jupyter notebook script/nbsample.ipynb
```

This is the **main interface** for the pipeline, offering:
- 📊 **Step-by-step execution** with data preview
- 🔍 **Interactive debugging** and data exploration
- 📈 **Real-time progress** monitoring
- 🗺️ **Auto-generated** interactive maps
- 💾 **Checkpoints** saved at each step

The notebook runs all 5 pipeline steps sequentially and generates:
- `output/notebook_final_output.json` - Complete results
- `output/notebook_final_output.csv` - Flattened data
- `output/covenant_hotspots.html` - Interactive map (via plot script)

### Alternative: CLI Batch Processing

```bash
# Run full pipeline (all 5 steps)
python script/run_pipeline.py

# Run specific step range
python script/run_pipeline.py --start 1 --stop 3

# Run single step for debugging
python script/run_pipeline.py --start 2 --stop 2
```

## Post-Processing

### Generate Interactive Hotspot Map

```bash
python script/plot_covenant_hotspots.py
```

Creates `output/covenant_hotspots.html` with:
- Time slider showing covenant spread from 1881-1958
- Toggle-able static heatmap overlay
- Layer control for different visualizations
- Custom color gradient (yellow → red → dark red)

### Validate Pipeline Accuracy

```bash
python script/validate_pipeline_accuracy.py
```

Compares pipeline results against ground truth data and generates validation metrics.

## Output Files

Primary outputs in `output/` directory:
- `notebook_final_output.json` - Full nested structure with all processing results
- `notebook_final_output.csv` - Flattened data for spreadsheet analysis
- `covenant_hotspots.html` - Interactive Folium heatmap visualization
- `step[1-5]_*.json` - Intermediate outputs from each pipeline step

## Configuration

Edit `deeds_pipeline/config.py` to customize:
- Input/output file paths
- Batch sizes and timeout settings
- Chrome headless mode (`CHROME_HEADLESS = False` for debugging)
- Cache settings (`ENABLE_CACHE`)
- Log levels

## Troubleshooting

**Chrome not found**
- Ensure Chrome browser is installed and in PATH
- Set `CHROME_HEADLESS = False` in config.py to see what's happening

**API authentication errors**
- Verify API keys in `.env` file
- For Google Vision: authenticate with `gcloud auth application-default login`

**Out of memory**
- Reduce `BATCH_SIZE` in config.py
- Process data in smaller batches

**API rate limits**
- Pipeline includes caching and retry logic
- Wait a few minutes and resume from the last successful step

## Next Steps

1. ✅ Pipeline is fully implemented
2. 🚀 Run `jupyter notebook script/nbsample.ipynb`
3. 📊 Analyze results in `output/` directory
4. 🗺️ View interactive map at `output/covenant_hotspots.html`
