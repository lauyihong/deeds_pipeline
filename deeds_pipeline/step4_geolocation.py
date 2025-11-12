"""
Step 4: Geolocation
Geocode street addresses and calculate cluster centers
"""

from typing import Dict, List, Optional
from pathlib import Path

from .utils import setup_logger, load_json, save_json, get_cache_key, load_from_cache, save_to_cache
from .config import STEP3_OUTPUT, STEP4_OUTPUT, ENABLE_CACHE


logger = setup_logger("step4_geolocation", "step4.log")


def initialize_clustering_validator():
    """
    Initialize StreetClusteringValidator instance
    
    Returns:
        StreetClusteringValidator instance
    """
    
    # TODO: Import and initialize StreetClusteringValidator
    # Reference: other_repo/deed_geo_indexing/test_clustering_validator.py
    # Class: StreetClusteringValidator (imported from app.services)
    
    # TODO: Your implementation here
    # Example:
    # from app.services.street_clustering_validator import StreetClusteringValidator
    # validator = StreetClusteringValidator()
    # return validator
    
    logger.info("StreetClusteringValidator initialized (placeholder)")
    return None


async def geocode_streets(validator, streets: List[str], county: str, state: str, town: str) -> Dict:
    """
    Geocode street addresses and calculate cluster center
    
    Args:
        validator: StreetClusteringValidator instance
        streets: List of street names
        county: County name
        state: State name
        town: Town name
    
    Returns:
        Dictionary with geocoding results:
        {
            "validated_streets": [...],
            "invalid_streets": [...],
            "primary_town": str,
            "cluster_center_lat": float,
            "cluster_center_lon": float,
            "final_address": str,
            "cluster_radius_miles": float,
            "confidence": float
        }
    """
    
    # TODO: Implement geocoding logic
    # 1. Call validator.validate_and_cluster()
    # 2. Extract validated streets with lat/lon
    # 3. Calculate cluster center
    # 4. Return structured result
    
    # Reference: other_repo/deed_geo_indexing/test_clustering_validator.py
    # Method: validator.validate_and_cluster(streets, county, state, town)
    
    logger.debug(f"Geocoding {len(streets)} streets in {town}, {county}, {state}")
    
    # TODO: Your implementation here
    # Example:
    # cluster_result = await validator.validate_and_cluster(
    #     streets=streets,
    #     county=county,
    #     state=state,
    #     town=town
    # )
    # return {
    #     "validated_streets": [
    #         {
    #             "street_name": s.street_name,
    #             "latitude": s.latitude,
    #             "longitude": s.longitude,
    #             "address": s.address,
    #             "town": s.town
    #         }
    #         for s in cluster_result.validated_streets
    #     ],
    #     "invalid_streets": cluster_result.invalid_streets,
    #     "primary_town": cluster_result.primary_town,
    #     "cluster_center_lat": cluster_result.cluster_center_lat,
    #     "cluster_center_lon": cluster_result.cluster_center_lon,
    #     "final_address": cluster_result.final_address,
    #     "cluster_radius_miles": cluster_result.cluster_radius_miles,
    #     "confidence": cluster_result.confidence
    # }
    
    return {
        "validated_streets": [],
        "invalid_streets": [],
        "primary_town": town,
        "cluster_center_lat": None,
        "cluster_center_lon": None,
        "final_address": None,
        "cluster_radius_miles": None,
        "confidence": 0.0
    }


async def process_deed_geolocation(deed_record: Dict, validator) -> Dict:
    """
    Process geolocation for a single deed record
    
    Args:
        deed_record: Deed record from Step 3
        validator: StreetClusteringValidator instance
    
    Returns:
        Deed record with added geolocation results
    """
    deed_id = deed_record.get("deed_id")
    
    # Check cache
    if ENABLE_CACHE:
        cache_key = get_cache_key("step4", deed_id)
        cached = load_from_cache(cache_key)
        if cached:
            logger.info(f"Deed {deed_id}: Loaded from cache")
            return cached
    
    # Get streets from Step 3
    streets = deed_record.get("extracted_streets", [])
    
    if not streets:
        logger.warning(f"Deed {deed_id}: No streets found")
        deed_record["geolocation"] = None
        deed_record["step4_completed"] = True
        return deed_record
    
    # Get county and town information
    county = deed_record.get("county", "")
    
    # Try to get town from OCR results
    town = None
    ocr_results = deed_record.get("ocr_results", [])
    for result in ocr_results:
        extracted_info = result.get("extracted_info", {})
        city_town = extracted_info.get("city_town")
        if city_town:
            town = city_town
            break
    
    if not town:
        logger.warning(f"Deed {deed_id}: No town information found")
        town = ""
    
    state = "Massachusetts"  # Default for this dataset
    
    logger.info(f"Deed {deed_id}: Geocoding {len(streets)} streets in {town}, {county}")
    
    # Geocode streets
    geolocation_result = await geocode_streets(validator, streets, county, state, town)
    
    deed_record["geolocation"] = geolocation_result
    deed_record["step4_completed"] = True
    
    # Save to cache
    if ENABLE_CACHE:
        save_to_cache(cache_key, deed_record)
    
    return deed_record


async def run_step4_async(input_file: Path = STEP3_OUTPUT, output_file: Path = STEP4_OUTPUT) -> Dict[str, Dict]:
    """
    Run Step 4: Geolocation (async version)
    
    Args:
        input_file: Path to Step 3 output file
        output_file: Path to Step 4 output file
    
    Returns:
        Deed data with geolocation results
    """
    logger.info(f"Starting Step 4: Geolocation")
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    
    try:
        # Load input data
        logger.info("Loading Step 3 output...")
        deed_data = load_json(input_file)
        logger.info(f"Loaded {len(deed_data)} deed records")
        
        # Initialize validator
        logger.info("Initializing StreetClusteringValidator...")
        validator = initialize_clustering_validator()
        
        # Process each deed
        processed_data = {}
        total = len(deed_data)
        
        for idx, (deed_id, deed_record) in enumerate(deed_data.items(), 1):
            logger.info(f"Processing deed {deed_id} ({idx}/{total})")
            processed_data[deed_id] = await process_deed_geolocation(deed_record, validator)
        
        # Save output
        logger.info("Saving processed data...")
        save_json(processed_data, output_file)
        logger.info(f"Step 4 completed. Output saved to {output_file}")
        
        return processed_data
        
    except Exception as e:
        logger.error(f"Error in Step 4: {e}", exc_info=True)
        raise


def run_step4(input_file: Path = STEP3_OUTPUT, output_file: Path = STEP4_OUTPUT) -> Dict[str, Dict]:
    """
    Run Step 4: Geolocation (sync wrapper)
    
    Args:
        input_file: Path to Step 3 output file
        output_file: Path to Step 4 output file
    
    Returns:
        Deed data with geolocation results
    """
    import asyncio
    return asyncio.run(run_step4_async(input_file, output_file))


if __name__ == "__main__":
    run_step4()

