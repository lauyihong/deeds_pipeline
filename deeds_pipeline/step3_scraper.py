"""
Step 3: MassLand Scraper
Scrape additional geographic information from MassLand Records website

Function-based interface for notebook integration.

Input format (list of dicts):
[
  {
    "deed_id": str,
    "county": str (e.g., "Middlesex County"),
    "town": Optional[str],
    "book": str|int,
    "page": str|int,
    # OR alternatively:
    "book_page_urls": List[str]  # Will extract book/page from URLs
  }
]

Output format (same list augmented):
[
  {
    ... (all input fields),
    "scraper_results": [{"book": str, "page": str, "status": str, "metadata": dict}],
    "extracted_streets": List[str],
    "town": str (filled if missing),
    "step3_completed": true
  }
]
"""

from __future__ import annotations

import re
import sys
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Import stable scraper from other_repo
sys.path.insert(0, str(Path(__file__).parent.parent / "other_repo" / "test_scrap"))
from massland_scraper import MassLandScraper

from .utils import setup_logger, load_json, save_json, get_cache_key, load_from_cache, save_to_cache
from .config import STEP2_OUTPUT, STEP3_OUTPUT, ENABLE_CACHE, CHROME_HEADLESS


logger = setup_logger("step3_scraper", "step3.log")


def extract_book_page_from_urls(urls: List[str]) -> List[Tuple[str, str]]:
    """
    Extract book/page pairs from MassLand URLs.
    Example URL: https://www.masslandrecords.com/...?Book=57&Page=21

    Returns: List of (book, page) tuples
    """
    pairs = []
    for url in urls:
        # Match patterns like Book=57&Page=21 or book=57&page=21
        match = re.search(r'[Bb]ook=(\d+).*?[Pp]age=(\d+)', url)
        if match:
            book = match.group(1)
            page = match.group(2)
            pairs.append((book, page))
    return sorted(set(pairs))


def extract_book_page_from_deed(deed_record: Dict) -> List[Tuple[str, str]]:
    """
    Extract book/page pairs from deed record.
    Supports multiple input formats:
    1. Direct fields: deed_record["book"] and deed_record["page"]
    2. book_page_pairs list: [{"book": "57", "page": "21"}, ...]
    3. book_page_urls list: Extract from URL query parameters
    4. OCR results: Extract plan_book/plan_pages from step2 extracted_info

    Returns: List of (book, page) tuples
    """
    pairs = []

    # Format 1: Direct fields
    if "book" in deed_record and "page" in deed_record:
        book = str(deed_record["book"]).strip()
        page = str(deed_record["page"]).strip()
        if book and page:
            pairs.append((book, page))

    # Format 2: book_page_pairs list
    for item in deed_record.get("book_page_pairs", []):
        book = str(item.get("book", "")).strip()
        page = str(item.get("page", "")).strip()
        if book and page:
            pairs.append((book, page))

    # Format 3: Extract from URLs
    urls = deed_record.get("book_page_urls", [])
    if urls:
        url_pairs = extract_book_page_from_urls(urls)
        pairs.extend(url_pairs)
    
    # Format 4: Extract from OCR results (plan_book/plan_pages from step2)
    ocr_results = deed_record.get("ocr_results", [])
    for ocr_result in ocr_results:
        extracted_info = ocr_result.get("extracted_info", {})
        if extracted_info:
            plan_book = extracted_info.get("plan_book")
            plan_pages = extracted_info.get("plan_pages")
            if plan_book and plan_pages:
                # Handle both list and single value cases
                books = plan_book if isinstance(plan_book, list) else [plan_book]
                pages = plan_pages if isinstance(plan_pages, list) else [plan_pages]
                for book in books:
                    for page_num in pages:
                        pairs.append((str(book), str(page_num)))

    # Dedupe and sort
    return sorted(set(pairs))


def extract_streets_from_scraper_result(scraper_result: Dict) -> List[str]:
    """Extract street names from scraper metadata"""
    streets: List[str] = []
    property_info = scraper_result.get("metadata", {}).get("property_info", [])
    for prop in property_info:
        name = prop.get("Street Name") or prop.get("street_name")
        if name:
            streets.append(name.strip())
    return sorted(set(streets))


def process_single_deed(deed_record: Dict, use_cache: bool = True, headless: bool = True) -> Dict:
    """
    Process a single deed record with scraping (creates fresh browser instance).

    Args:
        deed_record: Dict with deed_id, book/page info, county, town, etc.
        use_cache: Whether to check/save cache
        headless: Whether to run browser in headless mode

    Returns:
        Same dict augmented with scraper_results, extracted_streets, step3_completed
    """
    deed_id = deed_record.get("deed_id", "unknown")

    # Check cache first
    if use_cache and ENABLE_CACHE:
        cache_key = get_cache_key("step3", deed_id)
        cached = load_from_cache(cache_key)
        if cached:
            logger.info(f"Deed {deed_id}: Loaded from cache")
            return cached

    # Extract book/page pairs
    book_pages = extract_book_page_from_deed(deed_record)
    if not book_pages:
        logger.warning(f"Deed {deed_id}: No book/page numbers found")
        deed_record["scraper_results"] = []
        deed_record["extracted_streets"] = []
        deed_record["step3_completed"] = True
        return deed_record

    logger.info(f"Deed {deed_id}: Scraping {len(book_pages)} book/page combination(s)")

    # Create fresh browser for this deed (KEY FIX: fresh browser per deed)
    scraper = MassLandScraper(headless=headless)

    try:
        scraper_results: List[Dict] = []
        all_streets: List[str] = []
        town_from_results: Optional[str] = deed_record.get("town") or None

        # Get expected town from deed record for validation
        expected_town = deed_record.get("city") or deed_record.get("town")
        if expected_town:
            expected_town = expected_town.upper().strip()

        for book, page in book_pages:
            logger.debug(f"  Scraping book={book}, page={page}")
            try:
                result = scraper.process_record(book, page)

                # Validate scraped plan's town matches deed's expected town
                scraped_town = result.get("metadata", {}).get("search_result_info", {}).get("town", "")
                if scraped_town:
                    scraped_town_upper = scraped_town.upper().strip()
                else:
                    scraped_town_upper = ""

                # If we have expected town and scraped town, check they match
                if expected_town and scraped_town_upper and scraped_town_upper != expected_town:
                    logger.warning(f"  Skipping book={book}, page={page}: town mismatch "
                                   f"(scraped={scraped_town}, expected={expected_town})")
                    # Still record the result but don't extract streets from it
                    result["town_mismatch"] = True
                    result["expected_town"] = expected_town
                    result["scraped_town"] = scraped_town
                    scraper_results.append(result)
                    continue  # Skip extracting streets from this mismatched plan

                scraper_results.append(result)

                # Extract streets only from matching plans
                streets = extract_streets_from_scraper_result(result)
                all_streets.extend(streets)

                # Capture town if available
                if not town_from_results:
                    town = result.get("metadata", {}).get("search_result_info", {}).get("town")
                    if town:
                        town_from_results = town

            except Exception as e:
                logger.warning(f"  Scrape failed for {book}/{page}: {e}")
                scraper_results.append({
                    "book": str(book),
                    "page": str(page),
                    "metadata": {"error": str(e)},
                    "status": "error"
                })

        # Augment deed record
        deed_record["scraper_results"] = scraper_results
        deed_record["extracted_streets"] = sorted(set(all_streets))
        if town_from_results and not deed_record.get("town"):
            deed_record["town"] = town_from_results
        deed_record["step3_completed"] = True

        # Save to cache
        if use_cache and ENABLE_CACHE:
            save_to_cache(cache_key, deed_record)

        logger.info(f"Deed {deed_id}: Completed. Found {len(all_streets)} unique street(s)")
        return deed_record

    finally:
        # ALWAYS close browser
        try:
            scraper.close()
        except Exception as e:
            logger.warning(f"Error closing scraper: {e}")


def process_deeds_scraping(deed_records: List[Dict], headless: bool = True) -> List[Dict]:
    """
    FUNCTION-BASED INTERFACE for notebook integration.
    Process multiple deed records with web scraping.

    Args:
        deed_records: List of deed dictionaries. Each must have:
            - deed_id: str
            - book + page: str/int, OR book_page_pairs, OR book_page_urls
            - county: str (optional)
            - town: str (optional)
        headless: Whether to run browser in headless mode

    Returns:
        Same list with each dict augmented with:
            - scraper_results: List of scraper results
            - extracted_streets: List of street names
            - town: Filled if missing
            - step3_completed: True
    """
    logger.info(f"Starting Step 3 processing for {len(deed_records)} deed(s)")

    processed_records = []
    for idx, deed_record in enumerate(deed_records, 1):
        deed_id = deed_record.get("deed_id", f"unknown_{idx}")
        logger.info(f"[{idx}/{len(deed_records)}] Processing deed {deed_id}")

        try:
            processed = process_single_deed(
                deed_record,
                use_cache=ENABLE_CACHE,
                headless=headless
            )
            processed_records.append(processed)
        except Exception as e:
            logger.error(f"Deed {deed_id} failed: {e}", exc_info=True)
            # Return original record with error flag
            deed_record["scraper_results"] = []
            deed_record["extracted_streets"] = []
            deed_record["step3_error"] = str(e)
            deed_record["step3_completed"] = False
            processed_records.append(deed_record)

    logger.info(f"Step 3 completed for {len(processed_records)} deed(s)")
    return processed_records


def run_step3(input_file: Path = STEP2_OUTPUT, output_file: Path = STEP3_OUTPUT) -> Dict[str, Dict]:
    """
    FILE-BASED INTERFACE (legacy/CLI mode).
    Read deed data from JSON file, process with scraping, write to JSON file.

    Args:
        input_file: Path to Step 2 output JSON (dict indexed by deed_id)
        output_file: Path to write Step 3 output JSON

    Returns:
        Processed deed data (dict indexed by deed_id)
    """
    logger.info(f"Starting Step 3: MassLand Scraper (file-based mode)")
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")

    try:
        # Load input data (dict format: {deed_id: {...}, ...})
        deed_data = load_json(input_file)
        logger.info(f"Loaded {len(deed_data)} deed records")

        # Convert dict to list format for process_deeds_scraping
        deed_records = list(deed_data.values())

        # Process using function interface
        processed_records = process_deeds_scraping(
            deed_records,
            headless=CHROME_HEADLESS
        )

        # Convert back to dict format for output
        processed_data = {
            record["deed_id"]: record
            for record in processed_records
        }

        # Save to file
        save_json(processed_data, output_file)
        logger.info(f"Step 3 completed. Output saved to {output_file}")
        return processed_data

    except Exception as e:
        logger.error(f"Error in Step 3: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_step3()

