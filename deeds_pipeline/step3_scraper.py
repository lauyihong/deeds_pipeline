"""
Step 3: MassLand Scraper
Scrape additional geographic information from MassLand Records website
"""

from typing import Dict, List, Optional
from pathlib import Path

from .utils import setup_logger, load_json, save_json, get_cache_key, load_from_cache, save_to_cache
from .config import STEP2_OUTPUT, STEP3_OUTPUT, ENABLE_CACHE, CHROME_HEADLESS


logger = setup_logger("step3_scraper", "step3.log")


def initialize_scraper():
    """
    Initialize MassLandScraper instance
    
    Returns:
        MassLandScraper instance
    """
    
    # TODO: Import and initialize MassLandScraper
    # Reference: other_repo/test_scrap/massland_scraper.py
    # Class: MassLandScraper
    
    # TODO: Your implementation here
    # Example:
    # from other_repo.test_scrap.massland_scraper import MassLandScraper
    # scraper = MassLandScraper(headless=CHROME_HEADLESS)
    # return scraper
    
    logger.info("MassLandScraper initialized (placeholder)")
    return None


def extract_book_page_from_deed(deed_record: Dict) -> List[tuple]:
    """
    Extract book and page numbers from deed record
    
    Args:
        deed_record: Deed record with OCR results from Step 2
    
    Returns:
        List of (book, page) tuples to scrape
    """
    book_pages = []
    
    # Extract from OCR results
    ocr_results = deed_record.get("ocr_results", [])
    
    for result in ocr_results:
        extracted_info = result.get("extracted_info", {})
        plan_books = extracted_info.get("plan_book", [])
        plan_pages = extracted_info.get("plan_pages", [])
        
        if plan_books and plan_pages:
            # Match books with pages
            for book in plan_books:
                for page in plan_pages:
                    book_pages.append((book, page))
    
    # Remove duplicates
    book_pages = list(set(book_pages))
    
    return book_pages


def scrape_massland_record(scraper, book: str, page: str) -> Optional[Dict]:
    """
    Scrape a single book/page record from MassLand
    
    Args:
        scraper: MassLandScraper instance
        book: Book number
        page: Page number
    
    Returns:
        Scraped metadata dictionary or None if failed
    """
    
    # TODO: Implement scraping logic
    # 1. Navigate to search page
    # 2. Search by book and page
    # 3. Extract metadata (property info, streets, etc.)
    # 4. Return structured data
    
    # Reference: other_repo/test_scrap/massland_scraper.py
    # Method: scraper.process_record(book, page)
    
    logger.debug(f"Scraping book={book}, page={page}")
    
    # TODO: Your implementation here
    # Example:
    # scraper.navigate_to_search_page()
    # if scraper.search_by_book_page(book, page):
    #     metadata = scraper.click_file_and_extract_metadata()
    #     return metadata
    # return None
    
    return {
        "book": book,
        "page": page,
        "metadata": {},
        "status": "placeholder"
    }


def extract_streets_from_metadata(metadata: Dict) -> List[str]:
    """
    Extract street names from scraped metadata
    
    Args:
        metadata: Scraped metadata from MassLand
    
    Returns:
        List of street names
    """
    streets = []
    
    # Extract from property_info
    property_info = metadata.get("metadata", {}).get("property_info", [])
    
    for prop in property_info:
        street_name = prop.get("Street Name")
        if street_name:
            streets.append(street_name)
    
    return list(set(streets))  # Remove duplicates


def process_deed_scraping(deed_record: Dict, scraper) -> Dict:
    """
    Process scraping for a single deed record
    
    Args:
        deed_record: Deed record from Step 2
        scraper: MassLandScraper instance
    
    Returns:
        Deed record with added scraper results
    """
    deed_id = deed_record.get("deed_id")
    
    # Check cache
    if ENABLE_CACHE:
        cache_key = get_cache_key("step3", deed_id)
        cached = load_from_cache(cache_key)
        if cached:
            logger.info(f"Deed {deed_id}: Loaded from cache")
            return cached
    
    # Extract book/page numbers to scrape
    book_pages = extract_book_page_from_deed(deed_record)
    
    if not book_pages:
        logger.warning(f"Deed {deed_id}: No book/page numbers found")
        deed_record["scraper_results"] = []
        deed_record["step3_completed"] = True
        return deed_record
    
    logger.info(f"Deed {deed_id}: Scraping {len(book_pages)} book/page combinations")
    
    scraper_results = []
    all_streets = []
    
    for book, page in book_pages:
        logger.info(f"Deed {deed_id}: Scraping book={book}, page={page}")
        
        metadata = scrape_massland_record(scraper, book, page)
        
        if metadata:
            scraper_results.append(metadata)
            
            # Extract streets
            streets = extract_streets_from_metadata(metadata)
            all_streets.extend(streets)
    
    # Remove duplicate streets
    all_streets = list(set(all_streets))
    
    deed_record["scraper_results"] = scraper_results
    deed_record["extracted_streets"] = all_streets
    deed_record["step3_completed"] = True
    
    # Save to cache
    if ENABLE_CACHE:
        save_to_cache(cache_key, deed_record)
    
    return deed_record


def run_step3(input_file: Path = STEP2_OUTPUT, output_file: Path = STEP3_OUTPUT) -> Dict[str, Dict]:
    """
    Run Step 3: Scrape MassLand records
    
    Args:
        input_file: Path to Step 2 output file
        output_file: Path to Step 3 output file
    
    Returns:
        Deed data with scraper results
    """
    logger.info(f"Starting Step 3: MassLand Scraper")
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    
    scraper = None
    
    try:
        # Load input data
        logger.info("Loading Step 2 output...")
        deed_data = load_json(input_file)
        logger.info(f"Loaded {len(deed_data)} deed records")
        
        # Initialize scraper
        logger.info("Initializing MassLandScraper...")
        scraper = initialize_scraper()
        
        # Process each deed
        processed_data = {}
        total = len(deed_data)
        
        for idx, (deed_id, deed_record) in enumerate(deed_data.items(), 1):
            logger.info(f"Processing deed {deed_id} ({idx}/{total})")
            processed_data[deed_id] = process_deed_scraping(deed_record, scraper)
        
        # Save output
        logger.info("Saving processed data...")
        save_json(processed_data, output_file)
        logger.info(f"Step 3 completed. Output saved to {output_file}")
        
        return processed_data
        
    except Exception as e:
        logger.error(f"Error in Step 3: {e}", exc_info=True)
        raise
        
    finally:
        # Close scraper
        if scraper:
            try:
                scraper.close()
                logger.info("MassLandScraper closed")
            except Exception as e:
                logger.warning(f"Error closing scraper: {e}")


if __name__ == "__main__":
    run_step3()

