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
    
    # TODO: Implement the grouping logic
    # 1. Create a dictionary to hold deed_id as keys
    # 2. Iterate through input_data
    # 3. For each record, extract deed_id
    # 4. Group records by deed_id
    # 5. For each deed_id, consolidate information:
    #    - Collect all review_ids
    #    - Use the most recent/complete information for single-value fields
    #    - Collect unique values for list fields (covenants, URLs, etc.)
    # 6. Return the consolidated dictionary
    
    reformatted_data = {}
    
    logger.info(f"Processing {len(input_data)} deed review records")
    
    # TODO: Your implementation here
    # Example skeleton:
    # for review in input_data:
    #     deed_id = str(review.get("deed_id"))
    #     if deed_id not in reformatted_data:
    #         reformatted_data[deed_id] = initialize_deed_record(deed_id)
    #     merge_review_into_deed(reformatted_data[deed_id], review)
    
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

