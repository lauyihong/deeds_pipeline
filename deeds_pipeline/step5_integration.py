"""
Step 5: Data Integration
Consolidate all processing results into final dataset

Function-based interface for notebook integration.
"""

import pandas as pd
from typing import Dict, List, Any, Tuple
from pathlib import Path

from .utils import setup_logger, load_json, save_json
from .config import STEP4_OUTPUT, STEP5_OUTPUT, STEP5_OUTPUT_CSV


logger = setup_logger("step5_integration", "step5.log")


def _ensure_list(value: Any) -> List:
    """Normalize value to list (empty when None)."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _merge_unique_lists(a: Any, b: Any) -> List:
    """Merge two values (list or scalar) into an ordered unique list."""
    merged: List = []
    for item in _ensure_list(a) + _ensure_list(b):
        if item in (None, "", []):
            continue
        if item not in merged:
            merged.append(item)
    return merged


def _select_best_geolocation(current: Dict, candidate: Dict) -> Dict:
    """Choose the richer geolocation result."""
    if not candidate:
        return current
    if not current:
        return candidate

    def score(geo: Dict) -> Tuple[int, int, float]:
        has_center = int(
            geo.get("cluster_center_lat") is not None and geo.get(
                "cluster_center_lon") is not None
        )
        validated = len(geo.get("validated_streets", [])) if isinstance(
            geo.get("validated_streets"), list) else 0
        confidence = geo.get("confidence") or 0.0
        return has_center, validated, float(confidence)

    return candidate if score(candidate) > score(current) else current


def deduplicate_deed_records(deed_records: List[Dict]) -> List[Dict]:
    """
    Collapse multiple records with the same deed_id into a single merged record.

    This prevents downstream duplication (one row per deed) and retains the richest
    available data across duplicates.
    """
    merged: Dict[str, Dict] = {}
    duplicate_count = 0

    list_fields = [
        "review_ids",
        "grantors",
        "grantees",
        "exact_language_covenants",
        "ocr_results",
        "scraper_results",
        "extracted_streets",
        "extracted_towns",
        "plan_books",
        "plan_pages",
        "lot_numbers",
    ]

    scalar_fields = [
        "city",
        "deed_date",
        "address",
        "is_restrictive_covenant",
        "county",
        "book",
        "page",
        "town",
    ]

    for record in deed_records:
        if not isinstance(record, dict):
            logger.warning(f"Skipping non-dict record during deduplication: {record}")
            continue

        deed_id = str(record.get("deed_id", "")).strip()
        if not deed_id:
            logger.warning("Skipping record without deed_id during deduplication")
            continue

        if deed_id not in merged:
            merged[deed_id] = record.copy()
            continue

        duplicate_count += 1
        base = merged[deed_id]

        # Prefer filled scalar values
        for field in scalar_fields:
            if not base.get(field) and record.get(field):
                base[field] = record.get(field)

        # Merge list-like fields
        for field in list_fields:
            base[field] = _merge_unique_lists(
                base.get(field), record.get(field))

        # Merge flags
        for flag in ["step2_completed", "step3_completed", "step4_completed"]:
            base[flag] = bool(base.get(flag)) or bool(record.get(flag))

        # Merge geolocation
        base["geolocation"] = _select_best_geolocation(
            base.get("geolocation"), record.get("geolocation"))

        # Merge scraped streets count if needed
        streets = base.get("extracted_streets") or []
        base["scraped_street_count"] = len(streets)

    if duplicate_count:
        logger.info(
            f"Deduplicated {duplicate_count} duplicate record(s); {len(merged)} unique deed_id(s) remain")

    return list(merged.values())


def flatten_deed_record(deed_id: str, deed_record: Dict) -> Dict[str, Any]:
    """
    Flatten nested deed record into a single-level dictionary

    Args:
        deed_id: Deed ID
        deed_record: Nested deed record from Step 4

    Returns:
        Flattened dictionary suitable for CSV/DataFrame
    """
    flat = {
        "deed_id": deed_id,
        "review_ids": ",".join(map(str, deed_record.get("review_ids", []))),
        "city": deed_record.get("city"),
        "deed_date": deed_record.get("deed_date"),
        "address": deed_record.get("address"),
        "is_restrictive_covenant": deed_record.get("is_restrictive_covenant"),
        "county": deed_record.get("county"),
    }

    # Add grantor/grantee info (flatten lists to strings)
    grantors = deed_record.get("grantors", [])
    grantees = deed_record.get("grantees", [])
    flat["grantors"] = "; ".join(grantors) if isinstance(
        grantors, list) else grantors
    flat["grantees"] = "; ".join(grantees) if isinstance(
        grantees, list) else grantees

    # Add covenant information
    exact_covenants = deed_record.get("exact_language_covenants", [])
    if exact_covenants:
        flat["covenant_text"] = exact_covenants[0] if isinstance(
            exact_covenants, list) else exact_covenants
    else:
        flat["covenant_text"] = None

    # Add OCR detected covenant from Step 2
    ocr_covenant_detected = False
    ocr_covenant_text = None
    ocr_results = deed_record.get("ocr_results", [])
    if ocr_results:
        for result in ocr_results:
            covenant_detection = result.get("covenant_detection", {})
            if covenant_detection.get("covenant_detected"):
                ocr_covenant_detected = True
                ocr_covenant_text = covenant_detection.get(
                    "corrected_quotation")
                break

    flat["ocr_covenant_detected"] = ocr_covenant_detected
    flat["ocr_covenant_text"] = ocr_covenant_text

    # Add extracted information from Step 2 (Gemini)
    plan_books = []
    plan_pages = []
    lot_numbers = []
    street_addresses = []
    city_towns: List[str] = []

    for result in ocr_results:
        extracted_info = result.get("extracted_info", {})
        if extracted_info.get("plan_book"):
            plan_books.extend(_ensure_list(extracted_info["plan_book"]))
        if extracted_info.get("plan_pages"):
            plan_pages.extend(_ensure_list(extracted_info["plan_pages"]))
        if extracted_info.get("lot_numbers"):
            lot_numbers.extend(_ensure_list(extracted_info["lot_numbers"]))
        if extracted_info.get("street_addresses"):
            street_addresses.extend(_ensure_list(extracted_info["street_addresses"]))
        if extracted_info.get("city_town"):
            city_towns.extend(_ensure_list(extracted_info["city_town"]))

    flat["plan_books"] = "; ".join(sorted(set(str(x) for x in plan_books))) if plan_books else None
    flat["plan_pages"] = "; ".join(sorted(set(str(x) for x in plan_pages))) if plan_pages else None
    flat["lot_numbers"] = "; ".join(sorted(set(str(x) for x in lot_numbers))) if lot_numbers else None
    flat["extracted_streets"] = "; ".join(sorted(set(str(x) for x in street_addresses))) if street_addresses else None
    # Deduplicate towns while ignoring nested lists
    towns_norm: List[str] = []
    for t in city_towns:
        if isinstance(t, list):
            towns_norm.extend([x for x in t if x])
        elif t:
            towns_norm.append(t)
    flat["extracted_towns"] = "; ".join(
        sorted(set(towns_norm))) if towns_norm else None

    # Add scraped streets from Step 3
    scraped_streets = deed_record.get("extracted_streets", [])
    flat["scraped_streets"] = "; ".join(
        scraped_streets) if scraped_streets else None
    flat["scraped_street_count"] = len(
        scraped_streets) if scraped_streets else 0

    # Add geolocation from Step 4
    geolocation = deed_record.get("geolocation")
    if geolocation:
        flat["geo_latitude"] = geolocation.get("cluster_center_lat")
        flat["geo_longitude"] = geolocation.get("cluster_center_lon")
        flat["geo_address"] = geolocation.get("final_address")
        flat["geo_town"] = geolocation.get("primary_town")
        flat["geo_cluster_radius_miles"] = geolocation.get(
            "cluster_radius_miles")
        flat["geo_confidence"] = geolocation.get("confidence")
        flat["geo_validated_street_count"] = len(
            geolocation.get("validated_streets", []))
        flat["geo_invalid_street_count"] = len(
            geolocation.get("invalid_streets", []))
    else:
        flat["geo_latitude"] = None
        flat["geo_longitude"] = None
        flat["geo_address"] = None
        flat["geo_town"] = None
        flat["geo_cluster_radius_miles"] = None
        flat["geo_confidence"] = None
        flat["geo_validated_street_count"] = 0
        flat["geo_invalid_street_count"] = 0

    # Add processing status flags
    flat["step2_completed"] = deed_record.get("step2_completed", False)
    flat["step3_completed"] = deed_record.get("step3_completed", False)
    flat["step4_completed"] = deed_record.get("step4_completed", False)

    return flat


def generate_quality_report(deed_data: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Generate data quality report

    Args:
        deed_data: Processed deed data

    Returns:
        Quality report dictionary
    """
    total_deeds = len(deed_data)

    # Count completions
    step2_completed = sum(1 for d in deed_data.values()
                          if d.get("step2_completed"))
    step3_completed = sum(1 for d in deed_data.values()
                          if d.get("step3_completed"))
    step4_completed = sum(1 for d in deed_data.values()
                          if d.get("step4_completed"))

    # Count covenant detections
    original_covenants = sum(1 for d in deed_data.values()
                             if d.get("is_restrictive_covenant"))
    ocr_covenants = sum(
        1 for d in deed_data.values()
        for r in d.get("ocr_results", [])
        if r.get("covenant_detection", {}).get("covenant_detected")
    )

    # Count geocoded records
    geocoded = sum(
        1 for d in deed_data.values()
        if d.get("geolocation") and d["geolocation"].get("cluster_center_lat")
    )

    # Count records with streets
    with_streets = sum(
        1 for d in deed_data.values()
        if d.get("extracted_streets")
    )

    report = {
        "total_deeds": total_deeds,
        "step2_ocr_completed": step2_completed,
        "step2_completion_rate": f"{(step2_completed/total_deeds*100):.1f}%" if total_deeds > 0 else "0%",
        "step3_scraper_completed": step3_completed,
        "step3_completion_rate": f"{(step3_completed/total_deeds*100):.1f}%" if total_deeds > 0 else "0%",
        "step4_geolocation_completed": step4_completed,
        "step4_completion_rate": f"{(step4_completed/total_deeds*100):.1f}%" if total_deeds > 0 else "0%",
        "original_covenant_count": original_covenants,
        "ocr_detected_covenant_count": ocr_covenants,
        "geocoded_count": geocoded,
        "geocoded_rate": f"{(geocoded/total_deeds*100):.1f}%" if total_deeds > 0 else "0%",
        "with_streets_count": with_streets,
        "with_streets_rate": f"{(with_streets/total_deeds*100):.1f}%" if total_deeds > 0 else "0%",
    }

    return report


def process_deeds_integration(deed_records: List[Dict]) -> Tuple[List[Dict], pd.DataFrame, Dict[str, Any]]:
    """
    FUNCTION-BASED INTERFACE for notebook integration.
    Integrate and flatten deed records for final output.

    Args:
        deed_records: List of deed dictionaries from Step 4

    Returns:
        Tuple of (full_records, flattened_dataframe, quality_report)
    """
    # Normalize input: allow dict keyed by deed_id (from checkpoints)
    if isinstance(deed_records, dict):
        deed_records = list(deed_records.values())

    logger.info(f"Starting Step 5 processing for {len(deed_records)} deed(s)")

    # Deduplicate by deed_id to ensure one record per deed
    deduped_records = deduplicate_deed_records(deed_records)

    # Convert list to dict format for generate_quality_report
    deed_data = {record["deed_id"]: record for record in deduped_records}

    # Flatten records for CSV export
    logger.info("Flattening deed records...")
    flattened_records = []
    for deed_record in deduped_records:
        deed_id = deed_record.get("deed_id", "unknown")
        flat_record = flatten_deed_record(deed_id, deed_record)
        flattened_records.append(flat_record)

    logger.info(
        f"Flattened {len(flattened_records)} records (unique deed_ids)")

    # Generate quality report
    logger.info("Generating quality report...")
    quality_report = generate_quality_report(deed_data)

    # Log quality report
    logger.info("=" * 60)
    logger.info("DATA QUALITY REPORT")
    logger.info("=" * 60)
    for key, value in quality_report.items():
        logger.info(f"{key}: {value}")
    logger.info("=" * 60)

    # Create DataFrame
    df = pd.DataFrame(flattened_records)

    logger.info(f"Step 5 completed for {len(deduped_records)} deed(s)")

    return deduped_records, df, quality_report


def run_step5(input_file: Path = STEP4_OUTPUT,
              output_json: Path = STEP5_OUTPUT,
              output_csv: Path = STEP5_OUTPUT_CSV) -> Dict[str, Any]:
    """
    FILE-BASED INTERFACE (legacy/CLI mode).
    Run Step 5: Data integration and export.

    Args:
        input_file: Path to Step 4 output file
        output_json: Path to final JSON output
        output_csv: Path to final CSV output

    Returns:
        Dictionary with integrated data and quality report
    """
    logger.info("Starting Step 5: Data Integration (file-based mode)")
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output JSON: {output_json}")
    logger.info(f"Output CSV: {output_csv}")

    try:
        # Load input data (dict format: {deed_id: {...}, ...})
        deed_data = load_json(input_file)
        logger.info(f"Loaded {len(deed_data)} deed records")

        # Convert dict to list format for process_deeds_integration
        deed_records = list(deed_data.values())

        # Process using function interface
        processed_records, df, quality_report = process_deeds_integration(
            deed_records)

        # Convert back to dict format for JSON output
        deed_data_final = {
            record["deed_id"]: record
            for record in processed_records
        }

        # Save JSON output (full nested structure)
        logger.info("Saving full JSON output...")
        final_output = {
            "metadata": {
                "total_deeds": len(deed_data_final),
                "quality_report": quality_report
            },
            "deeds": deed_data_final
        }
        save_json(final_output, output_json)

        # Save CSV output (flattened structure)
        logger.info("Saving CSV output...")
        df.to_csv(output_csv, index=False, encoding='utf-8')

        logger.info("Step 5 completed.")
        logger.info(f"JSON output: {output_json}")
        logger.info(f"CSV output: {output_csv}")

        return {
            "quality_report": quality_report,
            "total_records": len(processed_records)
        }

    except Exception as e:
        logger.error(f"Error in Step 5: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_step5()
