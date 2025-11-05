"""
Pipeline utility functions for MassLand Records Scraper
Provides helper functions for integration with upstream and downstream systems
"""

import json
import pandas as pd
from typing import Dict, List, Optional, Iterator
from pathlib import Path
import hashlib
import logging
from datetime import datetime


def normalize_metadata(metadata: Dict) -> Dict:
    """
    Normalize metadata format for downstream processing.
    Flattens nested structure and ensures consistent field names.
    
    Args:
        metadata: Raw metadata from scraper
        
    Returns:
        Normalized metadata dictionary
    """
    normalized = {
        "book": metadata.get("book", ""),
        "page": metadata.get("page", ""),
        "status": metadata.get("status", "unknown"),
        "file_date": None,
        "rec_time": None,
        "book_page": None,
        "type_desc": None,
        "town": None,
        "document_details": [],
        "property_info": [],
        "grantor_grantee": [],
        "error_message": None
    }
    
    # Extract from search_result_info
    search_info = metadata.get("metadata", {}).get("search_result_info", {})
    if search_info:
        normalized.update({
            "file_date": search_info.get("file_date"),
            "rec_time": search_info.get("rec_time"),
            "book_page": search_info.get("book_page"),
            "type_desc": search_info.get("type_desc"),
            "town": search_info.get("town")
        })
    
    # Extract document details (first record if available)
    doc_details = metadata.get("metadata", {}).get("document_details", [])
    if doc_details:
        normalized["document_details"] = doc_details
        # Flatten first document detail for easier access
        if len(doc_details) > 0:
            first_detail = doc_details[0]
            normalized.update({
                "doc_number": first_detail.get("Doc. #"),
                "doc_status": first_detail.get("Doc. Status"),
                "consideration": first_detail.get("Consideration")
            })
    
    # Extract property and grantor info
    normalized["property_info"] = metadata.get("metadata", {}).get("property_info", [])
    normalized["grantor_grantee"] = metadata.get("metadata", {}).get("grantor_grantee", [])
    
    # Extract error message if present
    if metadata.get("status") != "success":
        error_info = metadata.get("metadata", {}).get("error")
        if error_info:
            normalized["error_message"] = error_info if isinstance(error_info, str) else str(error_info)
    
    return normalized


def validate_metadata(result: Dict) -> Dict[str, bool]:
    """
    Validate extracted metadata completeness.
    
    Args:
        result: Metadata result to validate
        
    Returns:
        Dictionary with validation flags
    """
    validation = {
        "has_document_details": bool(result.get("metadata", {}).get("document_details")),
        "has_search_info": bool(result.get("metadata", {}).get("search_result_info")),
        "has_town": bool(result.get("metadata", {}).get("search_result_info", {}).get("town")),
        "has_file_date": bool(result.get("metadata", {}).get("search_result_info", {}).get("file_date")),
        "has_book_page": bool(result.get("metadata", {}).get("search_result_info", {}).get("book_page")),
        "has_property_info": bool(result.get("metadata", {}).get("property_info")),
        "has_grantor_grantee": bool(result.get("metadata", {}).get("grantor_grantee")),
        "status_success": result.get("status") == "success"
    }
    
    # Calculate completeness score
    required_fields = ["has_town", "has_file_date", "has_book_page"]
    validation["completeness_score"] = sum(validation.get(f, False) for f in required_fields) / len(required_fields)
    
    return validation


def classify_error(error: Exception) -> str:
    """
    Classify error type for downstream error handling.
    
    Args:
        error: Exception object or error string
        
    Returns:
        Error category string
    """
    error_str = str(error).lower()
    
    if "timeout" in error_str or "connection" in error_str or "network" in error_str:
        return "network_error"
    elif "search" in error_str or "no results" in error_str or "search_failed" in error_str:
        return "search_error"
    elif "metadata" in error_str or "extract" in error_str or "not found" in error_str:
        return "extraction_error"
    elif "browser" in error_str or "driver" in error_str or "chrome" in error_str:
        return "browser_error"
    else:
        return "unknown_error"


class ResultCache:
    """Simple file-based cache for scraping results"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
    
    def _get_cache_key(self, book: str, page: str) -> str:
        """Generate cache key from book and page"""
        return hashlib.md5(f"{book}_{page}".encode()).hexdigest()
    
    def get(self, book: str, page: str) -> Optional[Dict]:
        """Get cached result"""
        cache_file = self.cache_dir / f"{self._get_cache_key(book, page)}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading cache: {e}")
        return None
    
    def set(self, book: str, page: str, result: Dict):
        """Save result to cache"""
        cache_file = self.cache_dir / f"{self._get_cache_key(book, page)}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing cache: {e}")
    
    def clear(self):
        """Clear all cached files"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()


class PipelineLogger:
    """Structured logging for pipeline operations"""
    
    def __init__(self, name: str = "pipeline", log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def log_record(self, book: str, page: str, status: str, 
                   duration: float, metadata: Optional[Dict] = None):
        """Log single record processing result"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "book": book,
            "page": page,
            "status": status,
            "duration_seconds": round(duration, 2),
            "has_town": bool(metadata and metadata.get("search_result_info", {}).get("town")),
            "has_document_details": bool(metadata and metadata.get("document_details"))
        }
        self.logger.info(json.dumps(log_entry))
    
    def log_batch_summary(self, total: int, success: int, failed: int, 
                         duration: float):
        """Log batch processing summary"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "type": "batch_summary",
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": round(success / total if total > 0 else 0, 3),
            "duration_seconds": round(duration, 2)
        }
        self.logger.info(json.dumps(summary))


def export_to_dataframe(results: List[Dict]) -> pd.DataFrame:
    """
    Convert results to pandas DataFrame for downstream analysis.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        pandas DataFrame with flattened structure
    """
    rows = []
    for result in results:
        row = {
            "book": result.get("book", ""),
            "page": result.get("page", ""),
            "status": result.get("status", ""),
        }
        
        # Flatten search_result_info
        search_info = result.get("metadata", {}).get("search_result_info", {})
        row.update({
            "file_date": search_info.get("file_date"),
            "rec_time": search_info.get("rec_time"),
            "book_page": search_info.get("book_page"),
            "type_desc": search_info.get("type_desc"),
            "town": search_info.get("town")
        })
        
        # Flatten document_details (first record)
        doc_details = result.get("metadata", {}).get("document_details", [])
        if doc_details and len(doc_details) > 0:
            first_detail = doc_details[0]
            row.update({
                "doc_number": first_detail.get("Doc. #"),
                "doc_status": first_detail.get("Doc. Status"),
                "consideration": first_detail.get("Consideration")
            })
        
        # Flatten property_info (first record)
        property_info = result.get("metadata", {}).get("property_info", [])
        if property_info and len(property_info) > 0:
            first_prop = property_info[0]
            row.update({
                "street_number": first_prop.get("Street #"),
                "street_name": first_prop.get("Street Name"),
                "property_description": first_prop.get("Description")
            })
        
        # Extract first grantor/grantee
        grantor_grantee = result.get("metadata", {}).get("grantor_grantee", [])
        if grantor_grantee and len(grantor_grantee) > 0:
            first_gg = grantor_grantee[0]
            row.update({
                "grantor_grantee_name": first_gg.get("column_0", ""),
                "grantor_grantee_type": first_gg.get("column_1", "")
            })
        
        rows.append(row)
    
    return pd.DataFrame(rows)


def export_to_parquet(results: List[Dict], output_file: str):
    """
    Export results to Parquet format (efficient for large datasets).
    
    Args:
        results: List of result dictionaries
        output_file: Output file path
    """
    df = export_to_dataframe(results)
    df.to_parquet(output_file, index=False)


def read_input_records(input_file: str) -> List[Dict]:
    """
    Read input records from CSV file.
    Compatible with upstream pipeline output.
    
    Args:
        input_file: Path to input CSV file
        
    Returns:
        List of record dictionaries with 'book' and 'page' keys
    """
    records = []
    try:
        df = pd.read_csv(input_file)
        for _, row in df.iterrows():
            records.append({
                "book": str(row.get("book", "")).strip(),
                "page": str(row.get("page", "")).strip()
            })
    except Exception as e:
        print(f"Error reading input file: {e}")
    
    return records


def export_results(results: List[Dict], output_file: str, format: str = "json"):
    """
    Export results in specified format for downstream pipeline.
    
    Args:
        results: List of result dictionaries
        output_file: Output file path
        format: Output format ('json', 'csv', 'parquet')
    """
    if format.lower() == "json":
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    elif format.lower() == "csv":
        df = export_to_dataframe(results)
        df.to_csv(output_file, index=False)
    elif format.lower() == "parquet":
        export_to_parquet(results, output_file)
    else:
        raise ValueError(f"Unsupported format: {format}")


def process_record_wrapper(scraper, book: str, page: str, 
                          cache: Optional[ResultCache] = None) -> Dict:
    """
    Wrapper function for processing single record with caching.
    
    Args:
        scraper: MassLandScraper instance
        book: Book number
        page: Page number
        cache: Optional ResultCache instance
        
    Returns:
        Processed result dictionary
    """
    # Check cache first
    if cache:
        cached = cache.get(book, page)
        if cached:
            return cached
    
    # Process record
    scraper.navigate_to_search_page()
    result = None
    if scraper.search_by_book_page(book, page):
        result = scraper.click_file_and_extract_metadata()
    
    # Format result
    formatted_result = {
        "book": book,
        "page": page,
        "metadata": result if result else {},
        "status": "success" if result and "error" not in str(result) else "failed"
    }
    
    # Cache successful results
    if cache and formatted_result["status"] == "success":
        cache.set(book, page, formatted_result)
    
    return formatted_result

