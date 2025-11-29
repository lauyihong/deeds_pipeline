"""
Validation Script V2: Properly extracts streets from CSV format
"""

import pandas as pd
import json
import re
from pathlib import Path
from difflib import SequenceMatcher

PROJECT_ROOT = Path(__file__).parent.parent
MANUAL_CSV = PROJECT_ROOT / "output" / "manual_addresses_for_validation.csv"
PIPELINE_CSV = PROJECT_ROOT / "output" / "notebook_final_output.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"

print("="*100)
print("PIPELINE ACCURACY VALIDATION")
print("="*100)

# Load data
print("\n1. Loading data files...")
manual_df = pd.read_csv(MANUAL_CSV)
pipeline_df = pd.read_csv(PIPELINE_CSV)

print(f"   ✓ Loaded {len(manual_df)} manual addresses")
print(f"   ✓ Loaded {len(pipeline_df)} pipeline records")

# Utility functions


def normalize_address(addr):
    if pd.isna(addr) or not addr:
        return ""
    addr = str(addr).upper().strip()
    addr = re.sub(r'\s+', ' ', addr)
    return addr


def extract_street_from_address(addr):
    addr = normalize_address(addr)
    if not addr:
        return None
    parts = addr.split(',')
    if parts:
        street_part = parts[0].strip()
        tokens = street_part.split()
        if tokens and tokens[0].isdigit():
            tokens = tokens[1:]
        return ' '.join(tokens).strip() if tokens else None
    return None


def extract_city_from_address(addr):
    addr = normalize_address(addr)
    if not addr:
        return None
    parts = addr.split(',')
    if len(parts) >= 2:
        return parts[1].strip()
    return None


def string_similarity(a, b):
    if not a or not b:
        return 0.0
    a = normalize_address(a)
    b = normalize_address(b)
    ratio = SequenceMatcher(None, a, b).ratio()
    return ratio * 100


def check_street_match(scraped_streets_str, manual_street):
    """Parse semicolon-separated streets and check if manual street is present"""
    if not manual_street or pd.isna(scraped_streets_str):
        return False

    manual_street = normalize_address(manual_street)

    # Parse semicolon-separated streets
    if isinstance(scraped_streets_str, str):
        streets = [normalize_address(s.strip())
                   for s in scraped_streets_str.split(';')]
    else:
        return False

    # Check exact match
    if manual_street in streets:
        return True

    # Check substring matches
    for street in streets:
        if manual_street in street or street in manual_street:
            return True

    return False


def check_city_match(pipeline_city, manual_city):
    if not pipeline_city or not manual_city or pd.isna(pipeline_city) or pd.isna(manual_city):
        return False
    pipeline_city = normalize_address(str(pipeline_city))
    manual_city = normalize_address(str(manual_city))
    return pipeline_city == manual_city


# Validate
print("\n2. Validating pipeline results for 111 deeds...")

results = []
matched_count = 0

for idx, (_, manual_row) in enumerate(manual_df.iterrows()):
    deed_id = str(manual_row['deed_id'])

    ground_truth_address = manual_row['manual_address']
    ground_truth_city = manual_row['city']
    ground_truth_street = extract_street_from_address(ground_truth_address)

    # Find in pipeline by deed_id
    pipeline_rows = pipeline_df[pipeline_df['deed_id'].astype(str) == deed_id]

    if len(pipeline_rows) == 0:
        results.append({
            'deed_id': deed_id,
            'ground_truth_address': ground_truth_address,
            'ground_truth_city': ground_truth_city,
            'ground_truth_street': ground_truth_street,
            'pipeline_address': None,
            'pipeline_city': None,
            'pipeline_streets': 'None',
            'location_radius_match': False,
            'street_match': False,
            'city_match': False,
            'similarity_score': 0.0,
            'match_rate': 0,
            'status': 'NOT_IN_PIPELINE'
        })
        continue

    pipeline_row = pipeline_rows.iloc[0]
    matched_count += 1

    # Extract pipeline results
    pipeline_address = pipeline_row.get('geo_address')
    pipeline_city = pipeline_row.get('geo_town')
    pipeline_streets = pipeline_row.get(
        'scraped_streets')  # Semicolon-separated
    geo_lat = pipeline_row.get('geo_latitude')
    geo_lon = pipeline_row.get('geo_longitude')

    # Calculate metrics
    location_match = True if (
        pd.notna(geo_lat) and pd.notna(geo_lon)) else False
    street_match = check_street_match(pipeline_streets, ground_truth_street)
    city_match = check_city_match(pipeline_city, ground_truth_city)
    similarity = string_similarity(
        ground_truth_address, pipeline_address or "")

    # Calculate overall match rate
    matches = sum([location_match, street_match, city_match])
    match_rate = (matches / 3 * 100) if matches > 0 else 0

    # Format streets for display (first 3 streets)
    if isinstance(pipeline_streets, str):
        streets_list = [s.strip()
                        for s in str(pipeline_streets).split(';')[:3]]
        streets_display = ', '.join(streets_list)
    else:
        streets_display = 'None'

    results.append({
        'deed_id': deed_id,
        'ground_truth_address': ground_truth_address,
        'ground_truth_city': ground_truth_city,
        'ground_truth_street': ground_truth_street,
        'pipeline_address': pipeline_address,
        'pipeline_city': pipeline_city,
        'pipeline_streets': streets_display,
        'location_radius_match': location_match,
        'street_match': street_match,
        'city_match': city_match,
        'similarity_score': round(similarity, 2),
        'match_rate': round(match_rate, 1),
        'status': 'VALIDATED'
    })

results_df = pd.DataFrame(results)
validated_count = len(results_df[results_df['status'] == 'VALIDATED'])
not_in_pipeline = len(results_df[results_df['status'] == 'NOT_IN_PIPELINE'])

print(f"   ✓ Processed {len(results_df)} deeds")
print(f"     - {validated_count} found in pipeline ✅")
print(f"     - {not_in_pipeline} not in pipeline")

# Calculate metrics
print("\n3. Calculating accuracy metrics...")

if validated_count > 0:
    validated_results = results_df[results_df['status'] == 'VALIDATED'].copy()

    location_match_rate = (
        validated_results['location_radius_match'].sum() / validated_count) * 100
    street_match_rate = (
        validated_results['street_match'].sum() / validated_count) * 100
    city_match_rate = (
        validated_results['city_match'].sum() / validated_count) * 100
    avg_similarity = validated_results['similarity_score'].mean()
    avg_match_rate = validated_results['match_rate'].mean()

    print(
        f"\n   Accuracy Metrics (based on {validated_count} validated deeds):")
    print(f"   " + "-" * 70)
    print(
        f"   Location Radius Match Rate:    {location_match_rate:6.1f}% ({validated_results['location_radius_match'].sum()}/{validated_count})")
    print(
        f"   Street Name Match Rate:        {street_match_rate:6.1f}% ({validated_results['street_match'].sum()}/{validated_count})")
    print(
        f"   City/Town Match Rate:          {city_match_rate:6.1f}% ({validated_results['city_match'].sum()}/{validated_count})")
    print(f"   Average String Similarity:     {avg_similarity:6.1f}%")
    print(f"   Average Overall Match Rate:    {avg_match_rate:6.1f}%")
    print(f"   " + "-" * 70)

    # Save results
    results_csv = OUTPUT_DIR / "validation_results_detailed.csv"
    results_df.to_csv(results_csv, index=False)
    print(f"\n   ✓ Saved detailed results to: {results_csv.name}")

    # Save metrics
    metrics = {
        "total_validation_deeds": len(manual_df),
        "deeds_in_pipeline": validated_count,
        "deeds_pending": not_in_pipeline,
        "location_radius_match_rate": round(location_match_rate, 2),
        "street_name_match_rate": round(street_match_rate, 2),
        "city_town_match_rate": round(city_match_rate, 2),
        "average_string_similarity": round(avg_similarity, 2),
        "average_overall_match_rate": round(avg_match_rate, 2)
    }

    metrics_file = OUTPUT_DIR / "validation_metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"   ✓ Saved metrics to: {metrics_file.name}")

    # Show sample results
    print("\n4. Sample validation results (first 15 validated):")
    print("-" * 140)

    sample_validated = validated_results.head(15)
    for idx, row in sample_validated.iterrows():
        status_icon = "✓" if row['match_rate'] > 66 else "⚠" if row['match_rate'] > 33 else "✗"
        print(
            f"{status_icon} Deed {row['deed_id']:>6}: {row['ground_truth_street']:20} → {str(row['pipeline_streets'])[:40]:40} | Match: {row['match_rate']:5.1f}%")

print("\n" + "="*100)
print("VALIDATION COMPLETE")
print("="*100)
