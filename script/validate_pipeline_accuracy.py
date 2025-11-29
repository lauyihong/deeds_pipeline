"""
Validation Script V3: Binary metrics with radius-based location validation
"""

import pandas as pd
import json
import re
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MANUAL_CSV = PROJECT_ROOT / "output" / "manual_addresses_geocoded.csv"
MANUAL_CSV_FALLBACK = PROJECT_ROOT / "output" / "manual_addresses_for_validation.csv"
PIPELINE_CSV = PROJECT_ROOT / "output" / "notebook_final_output.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on Earth (in miles).
    """
    if any(pd.isna(x) for x in [lat1, lon1, lat2, lon2]):
        return None

    R = 3959  # Earth's radius in miles

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def normalize_string(s):
    """Normalize string for comparison"""
    if pd.isna(s) or not s:
        return ""
    s = str(s).upper().strip()
    s = re.sub(r'\s+', ' ', s)
    return s


def normalize_street_name(street):
    """Normalize street name by expanding/standardizing abbreviations"""
    if not street:
        return ""

    street = normalize_string(street)

    # Standard abbreviation mappings (both directions)
    abbreviations = {
        ' TR': ' TERR',
        ' TERRACE': ' TERR',
        ' ROAD': ' RD',
        ' DRIVE': ' DR',
        ' STREET': ' ST',
        ' AVENUE': ' AVE',
        ' LANE': ' LN',
        ' COURT': ' CT',
        ' CIRCLE': ' CIR',
        ' BOULEVARD': ' BLVD',
    }

    # Apply standardization
    for long_form, short_form in abbreviations.items():
        if street.endswith(long_form):
            street = street[:-len(long_form)] + short_form
        elif street.endswith(long_form.strip()):
            street = street[:-len(long_form.strip())] + short_form.strip()

    return street


def normalize_town_name(town):
    """Normalize town name, handling historical names"""
    if pd.isna(town) or not town:
        return ""

    town = normalize_string(town)

    # Historical town name mappings
    historical_names = {
        'VARNUM TOWN': 'DRACUT',
        'VARNUM': 'DRACUT',
        'LONG POND PARK': 'DRACUT',
    }

    return historical_names.get(town, town)


def extract_street_from_address(addr):
    """Extract street name from full address (removes house number)"""
    addr = normalize_string(addr)
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


def check_town_match(pipeline_town, manual_city):
    """Binary: Does pipeline town match manual city? (1 or 0)"""
    if pd.isna(pipeline_town) or pd.isna(manual_city):
        return 0

    # Normalize both town names (handles historical names like "Varnum Town" -> "Dracut")
    pipeline_norm = normalize_town_name(pipeline_town)
    manual_norm = normalize_town_name(manual_city)

    return 1 if pipeline_norm == manual_norm else 0


def check_street_match(scraped_streets_str, manual_street):
    """Binary: Is manual street in scraped streets? (1 or 0)"""
    if not manual_street or pd.isna(scraped_streets_str):
        return 0

    # Normalize manual street (standardize abbreviations)
    manual_norm = normalize_street_name(manual_street)
    if not manual_norm:
        return 0

    if isinstance(scraped_streets_str, str):
        # Normalize all scraped streets
        streets = [normalize_street_name(s.strip()) for s in scraped_streets_str.split(';')]
    else:
        return 0

    # Exact match after normalization
    if manual_norm in streets:
        return 1

    # Extract just the street name without suffix for fuzzy matching
    manual_base = manual_norm.rsplit(' ', 1)[0] if ' ' in manual_norm else manual_norm

    for street in streets:
        street_base = street.rsplit(' ', 1)[0] if ' ' in street else street
        # Match if base names are the same
        if manual_base == street_base:
            return 1
        # Substring match for compound names
        if manual_base in street or street_base in manual_norm:
            return 1

    return 0


def check_has_geolocation(lat, lon):
    """Binary: Does pipeline have valid lat/lon? (1 or 0)"""
    if pd.notna(lat) and pd.notna(lon):
        return 1
    return 0


def check_in_radius(ground_truth_lat, ground_truth_lon, cluster_lat, cluster_lon, radius_miles):
    """
    Binary: Is ground truth location within the cluster radius? (1 or 0)
    This is the most accurate validation - checks if actual address is within predicted area.
    """
    if any(pd.isna(x) for x in [ground_truth_lat, ground_truth_lon, cluster_lat, cluster_lon, radius_miles]):
        return 0

    distance = haversine_distance(ground_truth_lat, ground_truth_lon, cluster_lat, cluster_lon)
    if distance is None:
        return 0

    return 1 if distance <= radius_miles else 0


def main():
    print("=" * 100)
    print("PIPELINE ACCURACY VALIDATION (V3 - Binary Metrics)")
    print("=" * 100)

    # Load data
    print("\n1. Loading data files...")

    # Try geocoded manual CSV first, fallback to original
    if MANUAL_CSV.exists():
        manual_df = pd.read_csv(MANUAL_CSV)
        has_ground_truth_coords = 'ground_truth_latitude' in manual_df.columns
        print(f"   Loaded {len(manual_df)} manual addresses (with geocoding)")
    else:
        manual_df = pd.read_csv(MANUAL_CSV_FALLBACK)
        has_ground_truth_coords = False
        print(f"   Loaded {len(manual_df)} manual addresses (without geocoding)")
        print("   WARNING: Run preprocess_manual_geocoding.py first for radius validation!")

    pipeline_df = pd.read_csv(PIPELINE_CSV)
    print(f"   Loaded {len(pipeline_df)} pipeline records")

    # Validate
    print("\n2. Validating pipeline results...")

    results = []

    for idx, (_, manual_row) in enumerate(manual_df.iterrows()):
        deed_id = str(manual_row['deed_id'])
        ground_truth_address = manual_row['manual_address']
        ground_truth_city = manual_row.get('city', '')
        ground_truth_street = extract_street_from_address(ground_truth_address)

        # Ground truth coordinates (if available)
        ground_truth_lat = manual_row.get('ground_truth_latitude') if has_ground_truth_coords else None
        ground_truth_lon = manual_row.get('ground_truth_longitude') if has_ground_truth_coords else None

        # Find in pipeline by deed_id
        pipeline_rows = pipeline_df[pipeline_df['deed_id'].astype(str) == deed_id]

        if len(pipeline_rows) == 0:
            results.append({
                'deed_id': deed_id,
                'ground_truth_address': ground_truth_address,
                'ground_truth_city': ground_truth_city,
                'ground_truth_street': ground_truth_street,
                'pipeline_town': None,
                'pipeline_streets': None,
                'town_match': 0,
                'street_match': 0,
                'has_geolocation': 0,
                'in_radius': 0,
                'distance_miles': None,
                'status': 'NOT_IN_PIPELINE'
            })
            continue

        pipeline_row = pipeline_rows.iloc[0]

        # Extract pipeline data
        pipeline_town = pipeline_row.get('geo_town')
        pipeline_streets = pipeline_row.get('scraped_streets')
        cluster_lat = pipeline_row.get('geo_latitude')
        cluster_lon = pipeline_row.get('geo_longitude')
        cluster_radius = pipeline_row.get('geo_cluster_radius_miles')

        # Calculate binary metrics
        town_match = check_town_match(pipeline_town, ground_truth_city)
        street_match = check_street_match(pipeline_streets, ground_truth_street)
        has_geo = check_has_geolocation(cluster_lat, cluster_lon)
        in_radius = check_in_radius(ground_truth_lat, ground_truth_lon,
                                     cluster_lat, cluster_lon, cluster_radius)

        # Calculate distance for reference
        distance = haversine_distance(ground_truth_lat, ground_truth_lon, cluster_lat, cluster_lon)

        # Format streets for display (first 3)
        if isinstance(pipeline_streets, str):
            streets_list = [s.strip() for s in str(pipeline_streets).split(';')[:3]]
            streets_display = '; '.join(streets_list)
        else:
            streets_display = 'None'

        results.append({
            'deed_id': deed_id,
            'ground_truth_address': ground_truth_address,
            'ground_truth_city': ground_truth_city,
            'ground_truth_street': ground_truth_street,
            'pipeline_town': pipeline_town,
            'pipeline_streets': streets_display,
            'town_match': town_match,
            'street_match': street_match,
            'has_geolocation': has_geo,
            'in_radius': in_radius,
            'distance_miles': round(distance, 3) if distance else None,
            'status': 'VALIDATED'
        })

    results_df = pd.DataFrame(results)
    validated_df = results_df[results_df['status'] == 'VALIDATED'].copy()
    not_in_pipeline = len(results_df[results_df['status'] == 'NOT_IN_PIPELINE'])

    print(f"   Processed {len(results_df)} deeds")
    print(f"   - {len(validated_df)} found in pipeline")
    print(f"   - {not_in_pipeline} not in pipeline")

    # Calculate metrics
    print("\n3. Calculating accuracy metrics...")
    print("-" * 80)

    if len(validated_df) > 0:
        n = len(validated_df)

        # Binary metrics - count True/1 values
        town_match_count = validated_df['town_match'].sum()
        street_match_count = validated_df['street_match'].sum()
        has_geo_count = validated_df['has_geolocation'].sum()
        in_radius_count = validated_df['in_radius'].sum()

        # Rates
        town_match_rate = (town_match_count / n) * 100
        street_match_rate = (street_match_count / n) * 100
        has_geo_rate = (has_geo_count / n) * 100
        in_radius_rate = (in_radius_count / n) * 100

        # Overall: count of deeds where all 4 metrics are True
        validated_df['all_match'] = (
            (validated_df['town_match'] == 1) &
            (validated_df['street_match'] == 1) &
            (validated_df['has_geolocation'] == 1) &
            (validated_df['in_radius'] == 1)
        ).astype(int)
        all_match_count = validated_df['all_match'].sum()
        all_match_rate = (all_match_count / n) * 100

        # Print results
        print(f"\n   BINARY METRICS (based on {n} validated deeds):")
        print(f"   " + "-" * 70)
        print(f"   1. Town Name Match:       {town_match_count:4}/{n}  = {town_match_rate:6.1f}%")
        print(f"   2. Street Name Match:     {street_match_count:4}/{n}  = {street_match_rate:6.1f}%")
        print(f"   3. Has Geolocation:       {has_geo_count:4}/{n}  = {has_geo_rate:6.1f}%")
        print(f"   4. In Cluster Radius:     {in_radius_count:4}/{n}  = {in_radius_rate:6.1f}%")
        print(f"   " + "-" * 70)
        print(f"   OVERALL (all 4 match):    {all_match_count:4}/{n}  = {all_match_rate:6.1f}%")
        print(f"   " + "-" * 70)

        # Breakdown by match combinations
        print(f"\n   DETAILED BREAKDOWN:")

        # Count deeds by number of metrics matched
        validated_df['metrics_matched'] = (
            validated_df['town_match'] +
            validated_df['street_match'] +
            validated_df['has_geolocation'] +
            validated_df['in_radius']
        )

        for i in range(5):
            count = len(validated_df[validated_df['metrics_matched'] == i])
            pct = (count / n) * 100
            print(f"   - {i}/4 metrics matched: {count:4} deeds ({pct:5.1f}%)")

        # Save detailed results
        results_csv = OUTPUT_DIR / "validation_results_detailed.csv"
        results_df.to_csv(results_csv, index=False)
        print(f"\n   Saved detailed results to: {results_csv.name}")

        # Save metrics JSON
        metrics = {
            "total_validation_deeds": len(manual_df),
            "deeds_in_pipeline": len(validated_df),
            "deeds_not_in_pipeline": not_in_pipeline,
            "metrics": {
                "town_match": {
                    "count": int(town_match_count),
                    "total": n,
                    "rate": round(town_match_rate, 2)
                },
                "street_match": {
                    "count": int(street_match_count),
                    "total": n,
                    "rate": round(street_match_rate, 2)
                },
                "has_geolocation": {
                    "count": int(has_geo_count),
                    "total": n,
                    "rate": round(has_geo_rate, 2)
                },
                "in_radius": {
                    "count": int(in_radius_count),
                    "total": n,
                    "rate": round(in_radius_rate, 2)
                }
            },
            "overall": {
                "all_match_count": int(all_match_count),
                "all_match_rate": round(all_match_rate, 2)
            }
        }

        metrics_file = OUTPUT_DIR / "validation_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"   Saved metrics to: {metrics_file.name}")

        # Sample results
        print("\n4. Sample validation results (first 15):")
        print("-" * 120)
        print(f"{'Deed':>6} | {'Ground Truth Street':25} | {'Pipeline Town':15} | Town | Street | Geo | Radius | Dist(mi)")
        print("-" * 120)

        for _, row in validated_df.head(15).iterrows():
            street = str(row['ground_truth_street'])[:25] if row['ground_truth_street'] else 'N/A'
            town = str(row['pipeline_town'])[:15] if row['pipeline_town'] else 'N/A'
            dist = f"{row['distance_miles']:.2f}" if row['distance_miles'] else 'N/A'

            town_icon = "Y" if row['town_match'] else "N"
            street_icon = "Y" if row['street_match'] else "N"
            geo_icon = "Y" if row['has_geolocation'] else "N"
            radius_icon = "Y" if row['in_radius'] else "N"

            print(f"{row['deed_id']:>6} | {street:25} | {town:15} | {town_icon:^4} | {street_icon:^6} | {geo_icon:^3} | {radius_icon:^6} | {dist:>8}")

    print("\n" + "=" * 100)
    print("VALIDATION COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()
