# MassLand Records Scraper

Automated scraping script for extracting land record metadata from the MassLand Records website.

## 📋 Feature Overview

This script can:
1. Automatically access the MassLand Records website
2. Search records by Book and Page numbers
3. Extract detailed document metadata information, including:
   - Document details (Doc. #, File Date, Rec Time, Type Desc., Book/Page, Consideration, Doc. Status)
   - Property information (Street #, Street Name, Description)
   - Grantor/Grantee information

## 🏗️ Architecture Design

### Core Class: `MassLandScraper`

The script uses object-oriented design with the following main components:

```
MassLandScraper
├── __init__()              # Initialize browser driver
├── navigate_to_search_page()  # Navigate to search page
├── setup_search_criteria()     # Set search criteria (Office and Search Type)
├── search_by_book_page()      # Execute search
├── check_search_results()     # Check search results
├── click_file_and_extract_metadata()  # Click result and extract metadata
├── extract_metadata()        # Extract metadata data
├── extract_table_data()      # Extract structured data from tables
├── process_csv_file()        # Batch process CSV file
├── save_results()            # Save results to JSON
└── close()                   # Close browser
```

## 🔄 Workflow

### 1. Initialization Phase
```python
scraper = MassLandScraper(headless=False)
```
- Create Chrome browser instance
- Configure browser options (window size, user agent, etc.)
- Initialize WebDriverWait object

### 2. Search Process

For each Book/Page combination, execute the following steps:

#### Step 1: Navigate to Search Page
```
Visit: https://www.masslandrecords.com/MiddlesexNorth/D/Default.aspx
Wait for page to load
```

#### Step 2: Set Search Criteria
```
1. Set Office dropdown → "Plans"
2. Set Search Type dropdown → "Book Search"
3. Wait for Ajax update to complete
```

#### Step 3: Enter Search Parameters
```
1. Enter Book number in Book input field
2. Enter Page number in Page input field
3. Click "Search" button
```

#### Step 4: Wait for Search Results
```
Wait for DocList1_GridView_Document table to appear
Verify search results are loaded
```

#### Step 5: Check Search Results
```
Locate search results via File Date link
Count number of results
Extract basic information from first result (for debugging)
```

#### Step 6: Click File Date Link
```
Locate File Date link (using multiple selector strategies)
Use JavaScript click (to avoid StaleElementReferenceException)
Wait for DocDetails area to load
```

#### Step 7: Extract Metadata
```
Extract three main tables:
1. DocDetails1_GridView_Details - Document details
2. DocDetails1_GridView_Property - Property information
3. DocDetails1_GridView_GrantorGrantee - Grantor/Grantee information
```

### 3. Data Extraction Logic

#### `extract_table_data()` Method
- Extract table headers as dictionary keys
- Iterate through data rows, converting each row to a dictionary
- Process cells containing links, extracting link text and href
- Return list of dictionaries format

#### `extract_metadata()` Method
- Extract three main tables in sequence
- Extract other DocDetails area content as backup
- Return dictionary containing all metadata

## 📁 File Structure

```
test_scrap/
├── massland_scraper.py      # Main script
├── massland_input.csv        # Input file (Book, Page)
├── massland_output.json      # Output file (extracted metadata)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 📥 Input Format

### CSV File Format (`massland_input.csv`)
```csv
book,page
57,21
51,27
```

**Field Description:**
- `book`: Book number (integer or string)
- `page`: Page number (integer or string)

## 📤 Output Format

### JSON File Format (`massland_output.json`)
```json
[
  {
    "book": "57",
    "page": "21",
    "metadata": {
      "document_details": [
        {
          "Doc. #": "5721",
          "File Date": "10/26/1932",
          "Rec Time": "00:00AM",
          "Type Desc.": "PLAN",
          "Book/Page": "00057/21",
          "Consideration": "",
          "Doc. Status": "Verified/Certified"
        }
      ],
      "property_info": [
        {
          "Street #": "",
          "Street Name": "CHRISTIAN ST",
          "Description": ""
        }
      ],
      "grantor_grantee": [
        {
          "column_0": "MIDDLESEX CO-OPERATIVE BANK-LOWELL",
          "column_0_link": "javascript:__doPostBack(...)",
          "column_1": "Grantor"
        }
      ]
    },
    "status": "success"
  }
]
```

**Field Description:**
- `book`: Input Book number
- `page`: Input Page number
- `metadata`: Extracted metadata dictionary
  - `document_details`: Document details list
  - `property_info`: Property information list
  - `grantor_grantee`: Grantor/Grantee information list
- `status`: Processing status ("success" or "failed")

## 🚀 Usage

### Basic Usage

```python
from massland_scraper import MassLandScraper

# Create scraper instance
scraper = MassLandScraper(headless=False)

# Process CSV file
results = scraper.process_csv_file("massland_input.csv")

# Save results
scraper.save_results(results, "massland_output.json")

# Close browser
scraper.close()
```

### Command Line Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run script
python massland_scraper.py
```

### Pipeline Integration

#### Method 1: Import as Module

```python
from massland_scraper import MassLandScraper
import pandas as pd

def process_land_records(book_page_list):
    """
    Process land records list
    
    Args:
        book_page_list: [(book1, page1), (book2, page2), ...]
    
    Returns:
        list: Result list containing metadata
    """
    scraper = MassLandScraper(headless=True)  # Run in background
    results = []
    
    try:
        for book, page in book_page_list:
            # Navigate to search page
            scraper.navigate_to_search_page()
            
            # Execute search
            if scraper.search_by_book_page(book, page):
                # Extract metadata
                metadata = scraper.click_file_and_extract_metadata()
                results.append({
                    'book': book,
                    'page': page,
                    'metadata': metadata,
                    'status': 'success' if metadata and 'error' not in str(metadata) else 'failed'
                })
    finally:
        scraper.close()
    
    return results

# Usage example
book_pages = [(57, 21), (51, 27)]
results = process_land_records(book_pages)
```

#### Method 2: Batch Process DataFrame

```python
import pandas as pd
from massland_scraper import MassLandScraper

def process_dataframe(df):
    """
    Process DataFrame containing Book and Page columns
    
    Args:
        df: pandas DataFrame with 'book' and 'page' columns
    
    Returns:
        DataFrame: New DataFrame with added metadata column
    """
    scraper = MassLandScraper(headless=True)
    results = []
    
    try:
        for _, row in df.iterrows():
            book = str(row['book'])
            page = str(row['page'])
            
            scraper.navigate_to_search_page()
            if scraper.search_by_book_page(book, page):
                metadata = scraper.click_file_and_extract_metadata()
                results.append(metadata)
            else:
                results.append({'error': 'search_failed'})
    finally:
        scraper.close()
    
    df['metadata'] = results
    return df
```

#### Method 3: Asynchronous Processing (for large batches)

```python
from concurrent.futures import ThreadPoolExecutor
from massland_scraper import MassLandScraper

def process_single_record(book, page):
    """Process single record"""
    scraper = MassLandScraper(headless=True)
    try:
        scraper.navigate_to_search_page()
        if scraper.search_by_book_page(book, page):
            metadata = scraper.click_file_and_extract_metadata()
            return {
                'book': book,
                'page': page,
                'metadata': metadata,
                'status': 'success' if metadata and 'error' not in str(metadata) else 'failed'
            }
        return {'book': book, 'page': page, 'status': 'search_failed'}
    finally:
        scraper.close()

def process_batch(book_page_list, max_workers=3):
    """Batch processing (using thread pool)"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(
            lambda x: process_single_record(x[0], x[1]),
            book_page_list
        ))
    return results
```

## ⚙️ Configuration Options

### Initialization Parameters

```python
MassLandScraper(headless=False)
```

- `headless` (bool): 
  - `False`: Show browser window (useful for debugging)
  - `True`: Run in background (suitable for production)

### Custom Wait Times

Modify the following constants in the script:
```python
self.wait = WebDriverWait(self.driver, 20)  # Default 20 second timeout
time.sleep(2)  # Various wait times
```

## 🔧 Error Handling

The script includes multi-layer error handling mechanisms:

1. **Retry Mechanism**: Up to 3 retry attempts per record
2. **Browser Recovery**: Automatically reinitialize if browser connection is lost
3. **Multiple Selector Strategies**: Use multiple methods to locate elements, improving success rate
4. **JavaScript Click**: Avoid StaleElementReferenceException

### Common Errors and Solutions

| Error | Cause | Solution |
|------|------|----------|
| `StaleElementReferenceException` | Element has expired | Use JavaScript click or re-find element |
| `TimeoutException` | Page load timeout | Increase wait time or check network connection |
| `NoSuchElementException` | Element not found | Check if page structure has changed |

## 📊 Performance Optimization Suggestions

1. **Batch Processing**: Consider using asynchronous processing for large amounts of data
2. **Caching Mechanism**: Avoid repeatedly searching the same Book/Page
3. **Delay Settings**: Add appropriate delays between requests to avoid IP blocking
4. **Resource Management**: Ensure browser is closed in finally block

## 🔍 Debugging Tips

### Enable Verbose Logging
The script already includes detailed print statements showing the execution status of each step.

### Use headless=False Mode
```python
scraper = MassLandScraper(headless=False)
```
This allows you to observe the actual browser behavior, making debugging easier.

### Save Intermediate State
```python
# Save page screenshot after search
scraper.driver.save_screenshot(f"search_{book}_{page}.png")

# Save page HTML
with open(f"page_{book}_{page}.html", "w") as f:
    f.write(scraper.driver.page_source)
```

## 📝 Dependencies

```
selenium>=4.15.0
```

Ensure Chrome browser and ChromeDriver are installed (Selenium 4.6+ will automatically manage this).

## 🎯 Key Design Decisions

1. **Using Selenium**: Required because the website uses Ajax dynamic loading, needing a real browser environment
2. **JavaScript Click**: Avoids StaleElementReferenceException issues
3. **Multiple Selector Strategies**: Improves element location success rate
4. **Structured Data Extraction**: Converts table data to dictionary format for easier downstream processing

## 🔄 Pipeline Integration Checklist

- [ ] Ensure Chrome browser is installed
- [ ] Install Python dependencies: `pip install -r requirements.txt`
- [ ] Prepare input CSV file (containing book and page columns)
- [ ] Adjust wait times and retry counts as needed
- [ ] Use `headless=True` in production environment
- [ ] Implement error handling and logging
- [ ] Set appropriate delays to avoid IP blocking
- [ ] Process output JSON data and integrate into downstream systems

## 📞 Support

If you encounter issues, check:
1. Chrome browser version compatibility
2. Network connection status
3. Whether website structure has changed
4. Review detailed error logs

## 📄 License

This project is for learning and research purposes only.
