"""
Preprocess manual addresses: geocode each address to get lat/lon
Run this once before validation to create geocoded manual addresses file.

Includes fixes for:
1. Street abbreviations (TR → TERRACE, etc.)
2. Empty city values (extracted from address)
3. Wrong city names (TYNGSBORO, LOWELL, WESTFORD → DRACUT)
"""

import pandas as pd
import time
import re
import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MANUAL_CSV = PROJECT_ROOT / "output" / "manual_addresses_for_validation.csv"
OUTPUT_CSV = PROJECT_ROOT / "output" / "manual_addresses_geocoded.csv"


def fix_wrong_city_in_address(address):
    """Fix addresses with wrong city names - these streets are in Dracut"""
    if not address:
        return address

    # Known wrong city mappings (street is actually in Dracut)
    wrong_cities = [
        ("TYNGSBORO, MA 01879", "DRACUT, MA 01826"),
        ("LOWELL, MA 01853", "DRACUT, MA 01826"),
        ("WESTFORD, MA 01886", "DRACUT, MA 01826"),
    ]

    fixed = address
    for wrong, correct in wrong_cities:
        if wrong in fixed.upper():
            fixed = re.sub(re.escape(wrong), correct, fixed, flags=re.IGNORECASE)
            print(f"   Fixed city: {address[:40]}... → {correct}")

    return fixed


def extract_city_from_address(address):
    """Extract city name from address string"""
    if not address:
        return None

    # Pattern: ', CITYNAME, MA' or ', CITYNAME , MA'
    match = re.search(r',\s*([A-Za-z\s]+?)\s*,?\s*MA', address, re.IGNORECASE)
    if match:
        return match.group(1).strip().title()
    return None


def normalize_address(address):
    """Normalize address by expanding common abbreviations"""
    if not address:
        return address

    # Common street abbreviations
    replacements = [
        (" TR,", " TERRACE,"),
        (" TR ", " TERRACE "),
        (" RD,", " ROAD,"),
        (" RD ", " ROAD "),
        (" DR,", " DRIVE,"),
        (" DR ", " DRIVE "),
        (" ST,", " STREET,"),
        (" ST ", " STREET "),
        (" AVE,", " AVENUE,"),
        (" AVE ", " AVENUE "),
        (" LN,", " LANE,"),
        (" LN ", " LANE "),
        (" CT,", " COURT,"),
        (" CT ", " COURT "),
    ]

    normalized = address.upper()
    for old, new in replacements:
        normalized = normalized.replace(old, new)

    return normalized


def geocode_address(address):
    """Geocode an address using Nominatim API with fallback attempts"""
    if pd.isna(address) or not address:
        return None, None

    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "DeedsPipelineValidation/1.0"}

    # Try multiple address formats
    addresses_to_try = [
        address,  # Original
        normalize_address(address),  # Expanded abbreviations
    ]

    for addr in addresses_to_try:
        params = {
            "q": addr,
            "format": "json",
            "limit": 1,
            "countrycodes": "us"
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                results = response.json()
                if results:
                    return float(results[0]["lat"]), float(results[0]["lon"])
        except Exception as e:
            print(f"   Error geocoding '{addr}': {e}")

        time.sleep(0.5)  # Small delay between attempts

    return None, None


def main():
    print("=" * 80)
    print("PREPROCESSING: Geocoding Manual Addresses")
    print("=" * 80)

    # Load manual addresses
    print("\n1. Loading manual addresses...")
    df = pd.read_csv(MANUAL_CSV)
    print(f"   Loaded {len(df)} addresses")

    # Step 2: Fix wrong city names in addresses
    print("\n2. Fixing wrong city names in addresses...")
    for idx, row in df.iterrows():
        fixed_addr = fix_wrong_city_in_address(row['manual_address'])
        if fixed_addr != row['manual_address']:
            df.loc[idx, 'manual_address'] = fixed_addr

    # Step 3: Fill empty city values from address
    print("\n3. Filling empty city values...")
    empty_count = df['city'].isna().sum()
    print(f"   Found {empty_count} empty city values")

    for idx, row in df.iterrows():
        if pd.isna(row['city']):
            city = extract_city_from_address(row['manual_address'])
            if city:
                df.loc[idx, 'city'] = city

    filled_count = empty_count - df['city'].isna().sum()
    print(f"   Filled {filled_count} city values from addresses")

    # Step 4: Geocode each address
    print("\n4. Geocoding addresses (this may take a few minutes)...")
    latitudes = []
    longitudes = []

    for idx, row in df.iterrows():
        address = row['manual_address']
        print(f"   [{idx+1}/{len(df)}] Geocoding: {address[:50]}...")

        lat, lon = geocode_address(address)
        latitudes.append(lat)
        longitudes.append(lon)

        # Rate limiting: Nominatim requires 1 request per second
        time.sleep(1.1)

    # Add geocoded columns
    df['ground_truth_latitude'] = latitudes
    df['ground_truth_longitude'] = longitudes

    # Summary
    geocoded_count = sum(1 for lat in latitudes if lat is not None)
    print(f"\n5. Geocoding complete:")
    print(f"   - Successfully geocoded: {geocoded_count}/{len(df)}")
    print(f"   - Failed: {len(df) - geocoded_count}")

    if len(df) - geocoded_count > 0:
        print("\n   Failed addresses:")
        for idx, row in df.iterrows():
            if pd.isna(df.loc[idx, 'ground_truth_latitude']):
                print(f"     - {row['deed_id']}: {row['manual_address'][:50]}...")

    # Save
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n6. Saved to: {OUTPUT_CSV}")
    print("=" * 80)


if __name__ == "__main__":
    main()
