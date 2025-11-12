"""
Step 3: MassLand Scraper
Scrape additional geographic information from MassLand Records website

Input contract per deed (refined):
- deed_id: str
- county: str (e.g., "Middlesex County")
- town: Optional[str] (preferred if known)
- book_page_pairs: List[{"book": str|int, "page": str|int}]

Augmented output per deed:
- scraper_results: [ { book, page, status, metadata } ]
- extracted_streets: unique street names from metadata.property_info[*]."Street Name"
- town: if missing, set from search_result_info.town when available
- step3_completed: true
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

from .utils import setup_logger, load_json, save_json, get_cache_key, load_from_cache, save_to_cache
from .config import STEP2_OUTPUT, STEP3_OUTPUT, ENABLE_CACHE, CHROME_HEADLESS


logger = setup_logger("step3_scraper", "step3.log")


# --- Minimal embedded MassLandScraper (adapted from other_repo/test_scrap) ---
class MassLandScraper:
    def __init__(self, headless: bool = True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        # Stealth/robustness options
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.driver = webdriver.Chrome(options=chrome_options)
        # Remove navigator.webdriver flag
        try:
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
        except Exception:
            pass
        self.wait = WebDriverWait(self.driver, 25)

    def navigate_to_search_page(self):
        url = "https://www.masslandrecords.com/MiddlesexNorth/D/Default.aspx"
        self.driver.get(url)
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

    def setup_search_criteria(self):
        # Office -> Plans with multiple fallbacks
        office_select = self.wait.until(
            EC.presence_of_element_located((By.ID, "SearchCriteriaOffice1_DDL_OfficeName"))
        )
        office_dropdown = Select(office_select)
        selected = False
        for val in ("Plans",):
            try:
                office_dropdown.select_by_value(val)
                selected = True
                break
            except Exception:
                pass
        if not selected:
            try:
                office_dropdown.select_by_visible_text("Plans")
                selected = True
            except Exception:
                # Try direct option click
                for opt in office_dropdown.options:
                    if "Plans" in opt.text or opt.get_attribute("value") == "Plans":
                        opt.click()
                        selected = True
                        break
        time.sleep(2)
        # Search Type -> Book Search with multiple labels
        search_type_select = self.wait.until(
            EC.presence_of_element_located((By.ID, "SearchCriteriaName1_DDL_SearchName"))
        )
        dropdown = Select(search_type_select)
        selected = False
        for label in ("Plans Book Search", "Recorded Land Book Search", "Book Search"):
            try:
                dropdown.select_by_visible_text(label)
                selected = True
                break
            except Exception:
                continue
        if not selected:
            # last resort: click option containing 'Book Search'
            for opt in dropdown.options:
                if "Book Search" in opt.text:
                    opt.click()
                    selected = True
                    break
        time.sleep(2)

    def search_by_book_page(self, book: str, page: str) -> bool:
        try:
            if not self._page_has("SearchFormEx1_ACSTextBox_Book"):
                self.setup_search_criteria()
            book_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "SearchFormEx1_ACSTextBox_Book"))
            )
            book_input.clear(); book_input.send_keys(str(book))
            page_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "SearchFormEx1_ACSTextBox_PageNumber"))
            )
            page_input.clear(); page_input.send_keys(str(page))
            search_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "SearchFormEx1_btnSearch"))
            )
            try:
                search_btn.click()
            except Exception:
                # use JS click fallback
                self.driver.execute_script("arguments[0].click();", search_btn)
            self.wait.until(EC.presence_of_element_located((By.ID, "DocList1_GridView_Document")))
            time.sleep(1)
            return True
        except Exception:
            return False

    def _page_has(self, element_id: str) -> bool:
        try:
            self.driver.find_element(By.ID, element_id)
            return True
        except Exception:
            return False

    def check_search_results(self) -> int:
        links = self.driver.find_elements(By.CSS_SELECTOR, "a[id*='ButtonRow_File Date']")
        return len(links)

    def extract_search_row_info(self) -> Dict:
        info = {}
        try:
            link = self.driver.find_elements(By.CSS_SELECTOR, "a[id*='ButtonRow_File Date']")[0]
            row = link.find_element(By.XPATH, "./ancestor::tr")
            cells = row.find_elements(By.TAG_NAME, "td")
            # File Date
            info["file_date"] = link.text.strip()
            # Rec Time
            try:
                info["rec_time"] = row.find_element(By.CSS_SELECTOR, "a[id*='ButtonRow_Rec. Time']").text.strip()
            except Exception:
                info["rec_time"] = cells[2].text.strip() if len(cells) > 2 else ""
            # Book/Page
            try:
                info["book_page"] = row.find_element(By.CSS_SELECTOR, "a[id*='ButtonRow_Book/Page']").text.strip()
            except Exception:
                info["book_page"] = ""
            # Type
            try:
                info["type_desc"] = row.find_element(By.CSS_SELECTOR, "a[id*='ButtonRow_Type Desc.']").text.strip()
            except Exception:
                info["type_desc"] = ""
            # Town
            try:
                info["town"] = row.find_element(By.CSS_SELECTOR, "a[id*='ButtonRow_Town']").text.strip()
            except Exception:
                info["town"] = ""
        except Exception:
            pass
        return info

    def click_file_and_extract_metadata(self) -> Dict:
        if self.check_search_results() == 0:
            return {"error": "no_results"}
        search_row_info = self.extract_search_row_info()
        # Click first File Date link (JS click)
        link = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#DocList1_GridView_Document a[id*='ButtonRow_File Date']")))
        self.driver.execute_script("arguments[0].click();", link)
        self.wait.until(EC.presence_of_element_located((By.ID, "DocDetails1_DetailsCell")))
        time.sleep(1)
        metadata = self.extract_metadata()
        if search_row_info:
            metadata["search_result_info"] = search_row_info
        return metadata

    def extract_metadata(self) -> Dict:
        out: Dict = {}
        # Document details
        try:
            details = self._extract_table("DocDetails1_GridView_Details")
            if details:
                out["document_details"] = details
        except Exception:
            pass
        # Property info
        try:
            props = self._extract_table("DocDetails1_GridView_Property")
            if props:
                out["property_info"] = props
        except Exception:
            pass
        # Grantor/grantee
        try:
            gg = self._extract_table("DocDetails1_GridView_GrantorGrantee")
            if gg:
                out["grantor_grantee"] = gg
        except Exception:
            pass
        return out if out else {"error": "no_metadata"}

    def _extract_table(self, table_id: str) -> List[Dict]:
        table = self.driver.find_element(By.ID, table_id)
        rows = table.find_elements(By.CSS_SELECTOR, "tr.DataGridRow")
        # headers
        headers = []
        try:
            header_row = table.find_element(By.CSS_SELECTOR, "tr.DataGridHeader, tr th")
            header_cells = header_row.find_elements(By.TAG_NAME, "th")
            headers = [c.text.strip() for c in header_cells]
        except Exception:
            pass
        data: List[Dict] = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            record = {}
            for i, cell in enumerate(cells):
                key = headers[i] if i < len(headers) and headers[i] else f"column_{i}"
                try:
                    link = cell.find_element(By.TAG_NAME, "a")
                    text = link.text.strip() or cell.text.strip()
                    record[key] = text
                    record[f"{key}_link"] = link.get_attribute("href") or ""
                except Exception:
                    record[key] = cell.text.strip()
            if record:
                data.append(record)
        return data

    def process_record(self, book: str, page: str) -> Dict:
        self.navigate_to_search_page()
        status = self.search_by_book_page(book, page)
        metadata = self.click_file_and_extract_metadata() if status else None
        return {
            "book": str(book),
            "page": str(page),
            "metadata": metadata or {},
            "status": "success" if metadata and "error" not in str(metadata) else "failed",
        }

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass


def initialize_scraper() -> MassLandScraper:
    logger.info("MassLandScraper initialized")
    return MassLandScraper(headless=CHROME_HEADLESS)


def extract_book_page_from_deed(deed_record: Dict) -> List[Tuple[str, str]]:
    """Extract book/page pairs from deed_record['book_page_pairs']"""
    pairs = []
    for item in deed_record.get("book_page_pairs", []):
        book = str(item.get("book", "")).strip()
        page = str(item.get("page", "")).strip()
        if book and page:
            pairs.append((book, page))
    # dedupe
    return sorted(set(pairs))


def scrape_massland_record(scraper: MassLandScraper, book: str, page: str) -> Optional[Dict]:
    logger.debug(f"Scraping book={book}, page={page}")
    try:
        return scraper.process_record(book, page)
    except Exception as e:
        logger.warning(f"Scrape failed for {book}/{page}: {e}")
        return {"book": str(book), "page": str(page), "metadata": {"error": str(e)}, "status": "error"}


def extract_streets_from_scraper_result(scraper_result: Dict) -> List[str]:
    streets: List[str] = []
    property_info = scraper_result.get("metadata", {}).get("property_info", [])
    for prop in property_info:
        name = prop.get("Street Name") or prop.get("street_name")
        if name:
            streets.append(name.strip())
    return sorted(set(streets))


def process_deed_scraping(deed_record: Dict, scraper: MassLandScraper) -> Dict:
    deed_id = deed_record.get("deed_id")

    # Cache
    if ENABLE_CACHE:
        cache_key = get_cache_key("step3", deed_id)
        cached = load_from_cache(cache_key)
        if cached:
            logger.info(f"Deed {deed_id}: Loaded from cache")
            return cached

    book_pages = extract_book_page_from_deed(deed_record)
    if not book_pages:
        logger.warning(f"Deed {deed_id}: No book/page numbers found")
        deed_record["scraper_results"] = []
        deed_record["extracted_streets"] = []
        deed_record["step3_completed"] = True
        return deed_record

    logger.info(f"Deed {deed_id}: Scraping {len(book_pages)} book/page combinations")

    scraper_results: List[Dict] = []
    all_streets: List[str] = []
    town_from_results: Optional[str] = deed_record.get("town") or None

    for book, page in book_pages:
        result = scrape_massland_record(scraper, book, page)
        scraper_results.append(result)
        streets = extract_streets_from_scraper_result(result)
        all_streets.extend(streets)
        # capture town if available
        if not town_from_results:
            town = result.get("metadata", {}).get("search_result_info", {}).get("town")
            if town:
                town_from_results = town

    deed_record["scraper_results"] = scraper_results
    deed_record["extracted_streets"] = sorted(set(all_streets))
    if town_from_results and not deed_record.get("town"):
        deed_record["town"] = town_from_results
    deed_record["step3_completed"] = True

    if ENABLE_CACHE:
        save_to_cache(cache_key, deed_record)

    return deed_record


def run_step3(input_file: Path = STEP2_OUTPUT, output_file: Path = STEP3_OUTPUT) -> Dict[str, Dict]:
    logger.info(f"Starting Step 3: MassLand Scraper")
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")

    scraper: Optional[MassLandScraper] = None
    try:
        deed_data = load_json(input_file)
        logger.info(f"Loaded {len(deed_data)} deed records")

        scraper = initialize_scraper()

        processed_data: Dict[str, Dict] = {}
        total = len(deed_data)
        for idx, (deed_id, deed_record) in enumerate(deed_data.items(), 1):
            logger.info(f"Processing deed {deed_id} ({idx}/{total})")
            processed_data[deed_id] = process_deed_scraping(deed_record, scraper)

        save_json(processed_data, output_file)
        logger.info(f"Step 3 completed. Output saved to {output_file}")
        return processed_data

    except Exception as e:
        logger.error(f"Error in Step 3: {e}", exc_info=True)
        raise
    finally:
        if scraper:
            try:
                scraper.close()
            except Exception:
                pass


if __name__ == "__main__":
    run_step3()

