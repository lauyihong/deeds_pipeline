"""
Compare manually edited addresses with pipeline results to validate accuracy
"""

import json
import pandas as pd
from pathlib import Path

# File paths
PROJECT_ROOT = Path(__file__).parent.parent
MANUAL_CSV = PROJECT_ROOT / "data" / "deed_reviews_0123_location_edited - deed_reviews_0123_location.csv"
JSON_FILE = PROJECT_ROOT / "data" / "deed_reviews_northern_middlesex_20251103_110333.json"

print("="*80)
print("COMPARING MANUAL ADDRESSES VS PIPELINE RESULTS")
print("="*80)

# Load manually edited CSV
print(f"\nLoading manually edited CSV: {MANUAL_CSV.name}")
manual_df = pd.read_csv(MANUAL_CSV)
print(f"  Total rows in CSV: {len(manual_df)}")
print(f"  Columns: {list(manual_df.columns)}")

# Load JSON file
print(f"\nLoading JSON file: {JSON_FILE.name}")
with open(JSON_FILE, 'r') as f:
    json_data = json.load(f)
print(f"  Total deed reviews in JSON: {len(json_data)}")

# Extract deed IDs from CSV (where address is not null)
# The address column appears twice in the CSV, use the last one (manually filled)
address_col = [col for col in manual_df.columns if 'address' in col.lower()][-1]
print(f"\nUsing address column: '{address_col}'")

# Filter CSV to only rows with manual addresses
manual_with_address = manual_df[manual_df[address_col].notna() & (manual_df[address_col] != '')]
print(f"\n  Deeds with manual addresses: {len(manual_with_address)}")

# Get unique deed IDs from manual CSV
manual_deed_ids = set(manual_with_address['deed_id'].dropna().astype(str).unique())
print(f"  Unique deed IDs with addresses: {len(manual_deed_ids)}")

# Get deed IDs from JSON
json_deed_ids = set()
for review in json_data:
    if 'deed_id' in review:
        json_deed_ids.add(str(review['deed_id']))

print(f"\n  Unique deed IDs in JSON: {len(json_deed_ids)}")

# Find overlap
overlapping_ids = manual_deed_ids.intersection(json_deed_ids)
print(f"\n{'='*80}")
print(f"OVERLAP ANALYSIS")
print(f"{'='*80}")
print(f"Deeds in manual CSV only: {len(manual_deed_ids - json_deed_ids)}")
print(f"Deeds in JSON only: {len(json_deed_ids - manual_deed_ids)}")
print(f"Deeds in BOTH (overlap): {len(overlapping_ids)}")

# Create comparison table for overlapping deeds
if overlapping_ids:
    print(f"\n{'='*80}")
    print(f"VALIDATION SET: {len(overlapping_ids)} OVERLAPPING DEEDS")
    print(f"{'='*80}")

    # Sample of overlapping deed IDs
    sample_size = min(20, len(overlapping_ids))
    sample_ids = sorted(overlapping_ids)[:sample_size]

    print(f"\nSample deed IDs for validation (first {sample_size}):")
    for deed_id in sample_ids:
        # Get manual address
        manual_row = manual_with_address[manual_with_address['deed_id'].astype(str) == deed_id]
        if not manual_row.empty:
            manual_addr = manual_row.iloc[0][address_col]
            city = manual_row.iloc[0]['city']
            print(f"  Deed {deed_id:>6}: {manual_addr} ({city})")

    # Save validation set to CSV
    validation_output = PROJECT_ROOT / "output" / "validation_deed_ids.csv"
    validation_df = pd.DataFrame({
        'deed_id': sorted(overlapping_ids),
        'has_manual_address': True
    })
    validation_df.to_csv(validation_output, index=False)
    print(f"\n✓ Saved validation deed IDs to: {validation_output}")

    # Create detailed comparison table
    comparison_rows = []
    for deed_id in overlapping_ids:
        manual_row = manual_with_address[manual_with_address['deed_id'].astype(str) == deed_id]
        if not manual_row.empty:
            comparison_rows.append({
                'deed_id': deed_id,
                'manual_address': manual_row.iloc[0][address_col],
                'city': manual_row.iloc[0]['city'],
                'deed_date': manual_row.iloc[0]['deed_date'],
                'is_restrictive_covenant': manual_row.iloc[0]['is_restrictive_covenant']
            })

    comparison_df = pd.DataFrame(comparison_rows)
    comparison_output = PROJECT_ROOT / "output" / "manual_addresses_for_validation.csv"
    comparison_df.to_csv(comparison_output, index=False)
    print(f"✓ Saved manual addresses for validation to: {comparison_output}")

    print(f"\n{'='*80}")
    print(f"NEXT STEPS")
    print(f"{'='*80}")
    print(f"1. Run your pipeline on all {len(json_data)} deeds")
    print(f"2. Extract addresses for the {len(overlapping_ids)} validation deed IDs")
    print(f"3. Compare pipeline addresses vs manual addresses")
    print(f"4. Calculate accuracy metrics:")
    print(f"   - Exact match rate")
    print(f"   - Partial match rate (same street)")
    print(f"   - City/town match rate")

else:
    print("\n⚠️  WARNING: No overlapping deeds found!")
    print("   Check if deed_id fields match between files")

print(f"\n{'='*80}")
print("ANALYSIS COMPLETE")
print(f"{'='*80}")
