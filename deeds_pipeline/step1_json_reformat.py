"""
Step 1: JSON Reformat
Convert deed reviews from deed_review_id indexing to deed_id indexing
"""

from typing import Dict, List, Any
from pathlib import Path

from .utils import setup_logger, load_json, save_json
from .config import INPUT_JSON, STEP1_OUTPUT


logger = setup_logger("step1_json_reformat", "step1.log")


def reformat_deed_reviews(input_data: List[Dict]) -> Dict[str, Dict]:
    """
    Reformat deed reviews data from deed_review_id to deed_id indexing
    
    This function groups multiple deed reviews by their deed_id and consolidates
    the information into a single record per deed.
    
    Args:
        input_data: List of deed review records (indexed by deed_review_id)
    
    Returns:
        Dictionary of deed records indexed by deed_id
        
    Example output structure:
    {
        "1612": {
            "deed_id": 1612,
            "reviews": {
                "14":{
                "city": null,
                "deed_date": "1942-06-06",
                "addresses": [],
                "is_restrictive_covenant": true,
                "exact_language_covenants": ["..."],
                "grantors": ["Fred E. Kroker", "Ethel W. Kroker"],
                "grantees": ["Timothy F. Keane", "Anna M. Keane"],
                "additional_locational_information": ["..."],
                "exclusion_types": ["White people only"],
                "county": "Northern Middlesex",
                "full_texts": ["..."]
                },
                
                "15":{
                
                    },            
                "city": null, # REPEAT THE FIRST INFO AS THE GROUND TRUTH. FOR NOW
                "deed_date": "1942-06-06",
                "addresses": [],
                "grantors": ["Fred E. Kroker", "Ethel W. Kroker"],
                "grantees": ["Timothy F. Keane", "Anna M. Keane"],
                "additional_locational_information": ["..."],
                "exclusion_types": ["White people only"],
                "county": "Northern Middlesex",
                "full_texts": ["..."]
                
                }
        }
    }
    """
    
    reformatted_data = {}
    
    logger.info(f"Processing {len(input_data)} deed review records")
    
    for review in input_data:
        deed_id = str(review.get("deed_id"))
        deed_review_id = str(review.get("deed_review_id"))
        
        if deed_id not in reformatted_data:
            reformatted_data[deed_id] = {
                "deed_id": deed_id,
                "reviews": {}
            }
            reformatted_data[deed_id]["city"] = review.get("city")
            reformatted_data[deed_id]["deed_date"] = review.get("deed_date")
            reformatted_data[deed_id]["addresses"] = review.get("addresses")
            reformatted_data[deed_id]["grantors"] = review.get("grantors")
            reformatted_data[deed_id]["grantees"] = review.get("grantees")
            reformatted_data[deed_id]["additional_locational_information"] = review.get("additional_locational_information")
            reformatted_data[deed_id]["exclusion_types"] = review.get("exclusion_types")
            reformatted_data[deed_id]["county"] = review.get("county")
            reformatted_data[deed_id]["full_texts"] = review.get("full_texts")
            reformatted_data[deed_id]["book_page_urls"] = review.get("book_page_urls")
        
        transformed_review = {
            "city": review.get("city"),
            "deed_date": review.get("deed_date"),
            "addresses": review.get("addresses"),
            "is_restrictive_covenant": review.get("is_restrictive_covenant"),
            "exact_language_covenants": review.get("exact_language_covenants"),
            "grantors": review.get("grantors"),
            "grantees": review.get("grantees"),
            "additional_locational_information": review.get("additional_locational_information"),
            "exclusion_types": review.get("exclusion_types"),
            "county": review.get("county"),
            "full_texts": review.get("full_texts"),
            "book_page_urls": review.get("book_page_urls")
        }

        reformatted_data[deed_id]["reviews"][deed_review_id] = transformed_review

    logger.info(f"Consolidated into {len(reformatted_data)} unique deed records")
    return reformatted_data


def run_step1(input_file: Path = INPUT_JSON, output_file: Path = STEP1_OUTPUT) -> Dict[str, Dict]:
    """
    Run Step 1: Load input JSON and reformat by deed_id
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
    
    Returns:
        Reformatted deed data dictionary
    """
    logger.info(f"Starting Step 1: JSON Reformat")
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    
    try:
        # Load input data
        logger.info("Loading input data...")
        input_data = load_json(input_file)
        logger.info(f"Loaded {len(input_data)} records")
        
        # Reformat data
        logger.info("Reformatting data by deed_id...")
        reformatted_data = reformat_deed_reviews(input_data)
        
        # Save output
        logger.info("Saving reformatted data...")
        save_json(reformatted_data, output_file)
        logger.info(f"Step 1 completed. Output saved to {output_file}")
        
        return reformatted_data
        
    except Exception as e:
        logger.error(f"Error in Step 1: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_step1()

