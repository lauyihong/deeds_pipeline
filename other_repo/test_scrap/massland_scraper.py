#!/usr/bin/env python3
"""
MassLand Records Scraper
Visit https://www.masslandrecords.com/MiddlesexNorth/D/Default.aspx
Search by book and page number, extract metadata information
"""

import csv
import time
import json
from typing import Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class MassLandScraper:
    def __init__(self, headless=False):
        """Initialize browser driver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--headless=new")  # Use new headless mode
        # May not need --no-sandbox on Mac, but keep it anyway
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--window-size=1920,1080")
        # Don't need --disable-gpu on Mac
        # chrome_options.add_argument("--disable-gpu")
        # Remove remote-debugging-port to avoid conflicts
        # chrome_options.add_argument("--remote-debugging-port=9222")
        # Add user agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            print("Browser driver initialized successfully")
        except Exception as e:
            print(f"Browser driver initialization failed: {e}")
            raise
        
    def navigate_to_search_page(self):
        """Navigate to search page"""
        url = "https://www.masslandrecords.com/MiddlesexNorth/D/Default.aspx"
        print(f"Accessing: {url}")
        try:
            self.driver.get(url)
            # Wait for basic page elements to load
            self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)  # Wait for page to fully load
            print("Page loaded successfully")
        except Exception as e:
            print(f"Page loading failed: {e}")
            raise
    
    def setup_search_criteria(self):
        """Setup search criteria: Set Office to Plans, Search Type to Book Search"""
        try:
            print("Setting up search criteria...")
            
            # 1. Set Office to Plans
            print("Setting Office to Plans...")
            office_select = self.wait.until(
                EC.presence_of_element_located((By.ID, "SearchCriteriaOffice1_DDL_OfficeName"))
            )
            office_dropdown = Select(office_select)
            
            # Check current value
            current_office = office_select.get_attribute('value')
            print(f"Current Office value: {current_office}")
            
            # Select Plans
            try:
                office_dropdown.select_by_value("Plans")
                print("✓ Selected Office: Plans")
            except:
                # If not found by value, try by visible text
                try:
                    office_dropdown.select_by_visible_text("Plans")
                    print("✓ Selected Office: Plans (by text)")
                except:
                    print("⚠ Unable to select Plans, trying other methods...")
                    # Try clicking option directly
                    for option in office_dropdown.options:
                        if "Plans" in option.text or option.get_attribute('value') == "Plans":
                            option.click()
                            print("✓ Selected Office: Plans (by click)")
                            break
            
            # Wait for Ajax update (dropdown change triggers page update)
            time.sleep(2)
            
            # 2. Set Search Type to Book Search
            print("Setting Search Type to Book Search...")
            search_type_select = self.wait.until(
                EC.presence_of_element_located((By.ID, "SearchCriteriaName1_DDL_SearchName"))
            )
            search_type_dropdown = Select(search_type_select)
            
            # Check current value
            current_search_type = search_type_select.get_attribute('value')
            print(f"Current Search Type value: {current_search_type}")
            
            # Try multiple possible Book Search option values
            book_search_options = [
                "Plans Book Search",  # Book Search under Plans type
                "Recorded Land Book Search",  # Book Search under Recorded Land type
                "Book Search"  # Generic value
            ]
            
            selected = False
            for option_value in book_search_options:
                try:
                    search_type_dropdown.select_by_value(option_value)
                    print(f"✓ Selected Search Type: {option_value}")
                    selected = True
                    break
                except:
                    continue
            
            # If not found by value, try by visible text
            if not selected:
                try:
                    search_type_dropdown.select_by_visible_text("Book Search")
                    print("✓ Selected Search Type: Book Search (by text)")
                except:
                    # Try finding option containing "Book Search"
                    for option in search_type_dropdown.options:
                        option_text = option.text.strip()
                        if "Book Search" in option_text:
                            option.click()
                            print(f"✓ Selected Search Type: {option_text} (by click)")
                            selected = True
                            break
            
            # Wait for Ajax update
            time.sleep(2)
            
            print("✓ Search criteria setup completed")
            return True
            
        except Exception as e:
            print(f"Failed to setup search criteria: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def search_by_book_page(self, book, page):
        """Enter book and page to perform search"""
        try:
            print(f"Starting search - Book: {book}, Page: {page}")
            
            # First setup search criteria (Office and Search Type)
            if not self.setup_search_criteria():
                print("⚠ Warning: Search criteria setup may have failed, continuing search attempt...")
            
            # Find book input box - use correct ID based on HTML structure
            print("Finding Book input box...")
            book_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "SearchFormEx1_ACSTextBox_Book"))
            )
            book_input.clear()
            book_input.send_keys(str(book))
            print(f"Entered Book: {book}")
            
            # Find page input box
            print("Finding Page input box...")
            page_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "SearchFormEx1_ACSTextBox_PageNumber"))
            )
            page_input.clear()
            page_input.send_keys(str(page))
            print(f"Entered Page: {page}")
            
            # Find and click search button
            print("Finding search button...")
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "SearchFormEx1_btnSearch"))
            )
            search_button.click()
            print("Clicked search button")
            
            # Wait for search results to load - wait for DocList table to appear
            print("Waiting for search results...")
            self.wait.until(
                EC.presence_of_element_located((By.ID, "DocList1_GridView_Document"))
            )
            time.sleep(2)  # Additional wait to ensure content is fully loaded
            print("Search results loaded")
            return True
            
        except TimeoutException as e:
            print(f"Search timeout: {e}")
            # Try to print current page URL and title for debugging
            try:
                print(f"Current URL: {self.driver.current_url}")
                print(f"Page title: {self.driver.title}")
            except:
                pass
            return False
        except NoSuchElementException as e:
            print(f"Element not found: {e}")
            return False
        except Exception as e:
            print(f"Unknown error occurred during search: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_search_results(self):
        """Check search results, return result count"""
        try:
            # Based on HTML structure, search result table is nested in div
            # First find container containing the table
            print("Finding search result table...")
            
            # Method 1: Determine results by File Date link count (most reliable method)
            result_rows = []
            try:
                # Find if File Date links exist
                file_date_links = self.driver.find_elements(By.CSS_SELECTOR, "a[id*='ButtonRow_File Date']")
                if file_date_links:
                    # Find corresponding rows through links
                    for link in file_date_links:
                        try:
                            parent_row = link.find_element(By.XPATH, "./ancestor::tr")
                            if parent_row not in result_rows:
                                result_rows.append(parent_row)
                        except:
                            pass
            except:
                pass
            
            
            # Method 3: If methods 1 and 2 didn't find anything, try finding table nested in ContentContainer
            if not result_rows:
                try:
                    content_container = self.driver.find_element(By.ID, "DocList1_ContentContainer1")
                    # Find all rows containing File Date links in container
                    file_date_links = content_container.find_elements(By.CSS_SELECTOR, "a[id*='ButtonRow_File Date']")
                    for link in file_date_links:
                        try:
                            parent_row = link.find_element(By.XPATH, "./ancestor::tr")
                            if parent_row not in result_rows:
                                result_rows.append(parent_row)
                        except:
                            pass
                except:
                    pass
            
            # Method 4: Directly find rows containing File Date links in entire page (last resort)
            if not result_rows:
                all_file_date_links = self.driver.find_elements(By.CSS_SELECTOR, "a[id*='ButtonRow_File Date']")
                for link in all_file_date_links:
                    try:
                        parent_row = link.find_element(By.XPATH, "./ancestor::tr")
                        if parent_row not in result_rows:
                            result_rows.append(parent_row)
                    except:
                        continue
            
            result_count = len(result_rows)
            print(f"Found {result_count} search result(s)")
            
            if result_count == 0:
                print("⚠ Warning: No search results found")
                # Try to print page structure for debugging
                try:
                    doclist = self.driver.find_element(By.ID, "DocList1_ContentContainer1")
                    print(f"DocList container text length: {len(doclist.text)}")
                except:
                    pass
                return 0
            
            # Print first result information
            if result_count > 0:
                first_row = result_rows[0]
                try:
                    # Try to get File Date, Book/Page and other information
                    cells = first_row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 5:
                        # File Date is in second td (index 1)
                        if cells[1].find_elements(By.TAG_NAME, "a"):
                            file_date = cells[1].find_element(By.TAG_NAME, "a").text.strip()
                        else:
                            file_date = cells[1].text.strip()
                        
                        # Book/Page is in fourth td (index 3)
                        if cells[3].find_elements(By.TAG_NAME, "a"):
                            book_page = cells[3].find_element(By.TAG_NAME, "a").text.strip()
                        else:
                            book_page = cells[3].text.strip()
                        
                        print(f"First result: File Date={file_date}, Book/Page={book_page}")
                except Exception as e:
                    print(f"Error extracting result information: {e}")
            
            return result_count
            
        except Exception as e:
            print(f"Failed to check search results: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def extract_search_result_row_info(self):
        """Extract information from the first search result row before clicking File Date"""
        try:
            print("Extracting search result row information...")
            row_info = {}
            
            # Find the first result row by finding File Date link
            file_date_links = self.driver.find_elements(By.CSS_SELECTOR, "a[id*='ButtonRow_File Date']")
            if not file_date_links:
                print("⚠ No File Date links found, cannot extract row info")
                return row_info
            
            # Get the first File Date link and find its parent row
            first_file_date_link = file_date_links[0]
            first_row = first_file_date_link.find_element(By.XPATH, "./ancestor::tr")
            cells = first_row.find_elements(By.TAG_NAME, "td")
            
            # Extract File Date from the link we found
            try:
                row_info["file_date"] = first_file_date_link.text.strip()
            except:
                row_info["file_date"] = ""
            
            # Find each field by looking for their specific link IDs in the same row
            # Each field has a link with a specific ID pattern
            
            # Extract Rec. Time - look for link with "ButtonRow_Rec. Time"
            try:
                rec_time_link = first_row.find_element(By.CSS_SELECTOR, "a[id*='ButtonRow_Rec. Time']")
                row_info["rec_time"] = rec_time_link.text.strip()
            except:
                try:
                    # If link not found, try to find by position (should be next cell after File Date)
                    file_date_cell = first_file_date_link.find_element(By.XPATH, "./ancestor::td")
                    file_date_index = cells.index(file_date_cell)
                    if file_date_index + 1 < len(cells):
                        rec_time_cell = cells[file_date_index + 1]
                        row_info["rec_time"] = rec_time_cell.text.strip()
                    else:
                        row_info["rec_time"] = ""
                except:
                    row_info["rec_time"] = ""
            
            # Extract Book/Page - look for link with "ButtonRow_Book/Page"
            try:
                book_page_link = first_row.find_element(By.CSS_SELECTOR, "a[id*='ButtonRow_Book/Page']")
                row_info["book_page"] = book_page_link.text.strip()
            except:
                try:
                    # If link not found, try to find by position
                    file_date_cell = first_file_date_link.find_element(By.XPATH, "./ancestor::td")
                    file_date_index = cells.index(file_date_cell)
                    if file_date_index + 2 < len(cells):
                        book_page_cell = cells[file_date_index + 2]
                        row_info["book_page"] = book_page_cell.text.strip()
                    else:
                        row_info["book_page"] = ""
                except:
                    row_info["book_page"] = ""
            
            # Extract Type Desc. - look for link with "ButtonRow_Type Desc."
            try:
                type_desc_link = first_row.find_element(By.CSS_SELECTOR, "a[id*='ButtonRow_Type Desc.']")
                row_info["type_desc"] = type_desc_link.text.strip()
            except:
                try:
                    # If link not found, try to find by position
                    file_date_cell = first_file_date_link.find_element(By.XPATH, "./ancestor::td")
                    file_date_index = cells.index(file_date_cell)
                    if file_date_index + 3 < len(cells):
                        type_desc_cell = cells[file_date_index + 3]
                        row_info["type_desc"] = type_desc_cell.text.strip()
                    else:
                        row_info["type_desc"] = ""
                except:
                    row_info["type_desc"] = ""
            
            # Extract Town - look for link with "ButtonRow_Town"
            try:
                town_link = first_row.find_element(By.CSS_SELECTOR, "a[id*='ButtonRow_Town']")
                row_info["town"] = town_link.text.strip()
            except:
                try:
                    # If link not found, try to find by position
                    file_date_cell = first_file_date_link.find_element(By.XPATH, "./ancestor::td")
                    file_date_index = cells.index(file_date_cell)
                    if file_date_index + 4 < len(cells):
                        town_cell = cells[file_date_index + 4]
                        row_info["town"] = town_cell.text.strip()
                    else:
                        row_info["town"] = ""
                except:
                    row_info["town"] = ""
            
            print(f"✓ Extracted row info: File Date={row_info.get('file_date')}, Rec Time={row_info.get('rec_time')}, Book/Page={row_info.get('book_page')}, Type={row_info.get('type_desc')}, Town={row_info.get('town')}")
            
            return row_info
            
        except Exception as e:
            print(f"Error extracting search result row info: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def click_file_and_extract_metadata(self):
        """Click File Date link and extract metadata"""
        try:
            # 1. First check search results
            result_count = self.check_search_results()
            if result_count == 0:
                return {"error": "No search results found"}
            
            # 2. Extract information from search result row before clicking
            search_row_info = self.extract_search_result_row_info()
            
            # 3. Find and click File Date link of first result
            # File Date link ID format: DocList1_GridView_Document_ctl02_ButtonRow_File Date_0
            print("Finding File Date link...")
            
            file_link = None
            
            # Method 1: Find by ID (first result)
            try:
                file_link = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "DocList1_GridView_Document_ctl02_ButtonRow_File Date_0"))
                )
                print("✓ Found File Date link by ID")
            except:
                # Method 2: Find by CSS selector containing File Date
                try:
                    file_link = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "#DocList1_GridView_Document a[id*='ButtonRow_File Date']"))
                    )
                    print("✓ Found File Date link by CSS selector")
                except:
                    # Method 3: Find by XPath
                    try:
                        file_link = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//table[@id='DocList1_GridView_Document']//a[contains(@id, 'ButtonRow_File Date')]"))
                        )
                        print("✓ Found File Date link by XPath")
                    except:
                        # Method 4: Find first link in second td of first row (File Date column)
                        try:
                            table = self.driver.find_element(By.ID, "DocList1_GridView_Document")
                            first_row = table.find_element(By.CSS_SELECTOR, "tr.DataGridRow")
                            cells = first_row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2:
                                file_link = cells[1].find_element(By.TAG_NAME, "a")
                                print("✓ Found File Date link by table structure")
                        except:
                            pass
            
            if not file_link:
                raise NoSuchElementException("Unable to find File Date link")
            
            # Get link text (for debugging)
            link_text = file_link.text.strip()
            print(f"Preparing to click File Date link: {link_text}")
            
            # To avoid StaleElementReferenceException, use JavaScript click which is more reliable
            try:
                self.driver.execute_script("arguments[0].click();", file_link)
                print("✓ Clicked File Date link (via JavaScript)")
            except:
                # If JavaScript click fails, try direct click
                try:
                    file_link.click()
                    print("✓ Clicked File Date link")
                except Exception as e:
                    # If still fails, re-find link and click
                    print(f"First click failed, re-finding link: {e}")
                    file_link = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a[id*='ButtonRow_File Date']"))
                    )
                    file_link.click()
                    print("✓ Clicked File Date link (after re-finding)")
            
            # 4. Wait for DocDetails area to appear (this is where metadata is displayed)
            print("Waiting for metadata area to load...")
            self.wait.until(
                EC.presence_of_element_located((By.ID, "DocDetails1_DetailsCell"))
            )
            time.sleep(2)  # Wait for Ajax to complete
            
            # 5. Extract metadata from DocDetails area
            metadata = self.extract_metadata()
            
            # 6. Merge search row info with extracted metadata
            if search_row_info:
                metadata["search_result_info"] = search_row_info
            
            return metadata
            
        except TimeoutException as e:
            print(f"Timeout waiting for metadata: {e}")
            return {"error": f"Timeout waiting for metadata: {str(e)}"}
        except NoSuchElementException as e:
            print(f"File Date link not found: {e}")
            return {"error": f"File Date link not found: {str(e)}"}
        except Exception as e:
            print(f"Failed to click File Date or extract metadata: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    def extract_metadata(self):
        """Extract metadata information from DocDetails area"""
        try:
            metadata_dict = {}
            
            # 1. Extract document details (DocDetails1_GridView_Details)
            print("Extracting document details...")
            try:
                details_table = self.driver.find_element(By.ID, "DocDetails1_GridView_Details")
                details_data = self.extract_table_data(details_table)
                if details_data:
                    metadata_dict["document_details"] = details_data
                    print(f"✓ Extracted document details: {len(details_data)} row(s)")
            except NoSuchElementException:
                print("⚠ Document details table not found")
            except Exception as e:
                print(f"Error extracting document details: {e}")
            
            # 2. Extract property information (DocDetails1_GridView_Property)
            print("Extracting property information...")
            try:
                property_table = self.driver.find_element(By.ID, "DocDetails1_GridView_Property")
                property_data = self.extract_table_data(property_table)
                if property_data:
                    metadata_dict["property_info"] = property_data
                    print(f"✓ Extracted property information: {len(property_data)} row(s)")
            except NoSuchElementException:
                print("⚠ Property information table not found")
            except Exception as e:
                print(f"Error extracting property information: {e}")
            
            # 3. Extract Grantor/Grantee information (DocDetails1_GridView_GrantorGrantee)
            print("Extracting Grantor/Grantee information...")
            try:
                grantor_table = self.driver.find_element(By.ID, "DocDetails1_GridView_GrantorGrantee")
                grantor_data = self.extract_table_data(grantor_table)
                if grantor_data:
                    metadata_dict["grantor_grantee"] = grantor_data
                    print(f"✓ Extracted Grantor/Grantee information: {len(grantor_data)} row(s)")
            except NoSuchElementException:
                print("⚠ Grantor/Grantee table not found")
            except Exception as e:
                print(f"Error extracting Grantor/Grantee information: {e}")
            
            # 4. Extract all other DocDetails area content (as backup)
            try:
                doc_details_cells = [
                    "DocDetails1_DetailsCell",
                    "DocDetails1_PropertiesCell",
                    "DocDetails1_TownsCell",
                    "DocDetails1_GrantorGranteeCell",
                    "DocDetails1_DocumentStatusCell",
                    "DocDetails1_ERecordedCell",
                    "DocDetails1_DocumentRefsCell",
                    "DocDetails1_PTAXDocsCell",
                    "DocDetails1_MailBackCell"
                ]
                
                for cell_id in doc_details_cells:
                    try:
                        cell = self.driver.find_element(By.ID, cell_id)
                        text = cell.text.strip()
                        if text and len(text) > 10:
                            # Use simplified ID as key
                            key = cell_id.replace("DocDetails1_", "").replace("Cell", "").lower()
                            if key not in metadata_dict:
                                metadata_dict[key] = text
                    except:
                        continue
            except:
                pass
            
            return metadata_dict if metadata_dict else {"error": "No metadata found"}
            
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    def extract_table_data(self, table_element):
        """Extract data from table, return list of dictionaries"""
        try:
            data = []
            
            # Get table headers
            headers = []
            try:
                header_row = table_element.find_element(By.CSS_SELECTOR, "tr.DataGridHeader, tr th")
                header_cells = header_row.find_elements(By.TAG_NAME, "th")
                headers = [cell.text.strip() for cell in header_cells]
            except:
                # If no header row, try extracting from first row
                pass
            
            # Get data rows
            data_rows = table_element.find_elements(By.CSS_SELECTOR, "tr.DataGridRow")
            
            for row in data_rows:
                row_data = {}
                cells = row.find_elements(By.TAG_NAME, "td")
                
                for i, cell in enumerate(cells):
                    cell_text = cell.text.strip()
                    # If headers exist, use header as key
                    if i < len(headers) and headers[i]:
                        key = headers[i]
                    else:
                        key = f"column_{i}"
                    
                    # If cell contains link, also extract link text
                    try:
                        link = cell.find_element(By.TAG_NAME, "a")
                        link_text = link.text.strip()
                        if link_text:
                            row_data[key] = link_text
                            row_data[f"{key}_link"] = link.get_attribute('href') or ""
                        else:
                            row_data[key] = cell_text
                    except:
                        row_data[key] = cell_text
                
                if row_data:
                    data.append(row_data)
            
            return data
            
        except Exception as e:
            print(f"Error extracting table data: {e}")
            return []
    
    def process_record(self, book: str, page: str) -> Dict:
        """
        Process a single book/page record.
        Designed for pipeline integration.
        
        Args:
            book: Book number
            page: Page number
            
        Returns:
            Dictionary with book, page, metadata, and status
        """
        self.navigate_to_search_page()
        metadata = None
        
        if self.search_by_book_page(book, page):
            metadata = self.click_file_and_extract_metadata()
        
        return {
            "book": book,
            "page": page,
            "metadata": metadata if metadata else {},
            "status": "success" if metadata and "error" not in str(metadata) else "failed"
        }
    
    def process_csv_file(self, csv_file):
        """Process all book and page combinations in CSV file"""
        results = []
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, 1):
                book = row.get('book', '').strip()
                page = row.get('page', '').strip()
                
                if not book or not page:
                    print(f"Skipping empty row: book={book}, page={page}")
                    continue
                
                print(f"\n{'='*60}")
                print(f"Processing record {row_idx}: Book={book}, Page={page}")
                print(f"{'='*60}")
                
                max_retries = 3
                success = False
                
                for attempt in range(max_retries):
                    try:
                        # Check if browser is still valid
                        try:
                            self.driver.current_url
                        except:
                            print("Browser connection lost, reinitializing...")
                            self.close()
                            self.__init__(headless=False)
                        
                        # Navigate to search page (reload before each search)
                        self.navigate_to_search_page()
                        
                        # Execute search
                        if self.search_by_book_page(book, page):
                            # Click file and extract metadata
                            metadata = self.click_file_and_extract_metadata()
                            
                            result = {
                                'book': book,
                                'page': page,
                                'metadata': metadata,
                                'status': 'success' if metadata and 'error' not in str(metadata) else 'failed'
                            }
                            results.append(result)
                            
                            print(f"✓ Completed: Book={book}, Page={page}")
                            if metadata:
                                print(f"Metadata preview: {str(metadata)[:200]}...")
                            success = True
                            break
                        else:
                            if attempt < max_retries - 1:
                                print(f"Search failed, retrying {attempt + 1}/{max_retries}...")
                                time.sleep(3)
                            else:
                                results.append({
                                    'book': book,
                                    'page': page,
                                    'metadata': None,
                                    'status': 'search_failed'
                                })
                                
                    except Exception as e:
                        print(f"Error occurred during processing (attempt {attempt + 1}/{max_retries}): {e}")
                        if attempt < max_retries - 1:
                            print("Waiting before retry...")
                            time.sleep(5)
                            # Try to reinitialize browser
                            try:
                                self.close()
                                self.__init__(headless=False)
                            except:
                                pass
                        else:
                            results.append({
                                'book': book,
                                'page': page,
                                'metadata': None,
                                'status': 'error',
                                'error_message': str(e)
                            })
                
                # Delay between searches
                time.sleep(2)
        
        return results
    
    def save_results(self, results, output_file='massland_output.json'):
        """Save results to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_file}")
    
    def close(self):
        """Close browser"""
        self.driver.quit()
        print("Browser closed")


def main():
    """Main function"""
    scraper = None
    try:
        # Create scraper instance (headless=False means show browser window for debugging)
        scraper = MassLandScraper(headless=False)
        
        # Process CSV file
        csv_file = "massland_input.csv"
        results = scraper.process_csv_file(csv_file)
        
        # Save results
        scraper.save_results(results)
        
        # Print summary
        print(f"\nProcessing completed! Total records processed: {len(results)}")
        success_count = sum(1 for r in results if r['status'] == 'success')
        print(f"Success: {success_count}, Failed: {len(results) - success_count}")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper:
            scraper.close()


if __name__ == "__main__":
    main()

