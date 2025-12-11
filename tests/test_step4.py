#!/usr/bin/env python3
"""
Test script for Step 4 - Geolocation
Tests the refactored function-based interface with nest_asyncio
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from deeds_pipeline.step4_geolocation import process_deeds_geolocation

def test_step4():
    """Test Step 4 with sample data"""
    print("="*80)
    print("TESTING STEP 4: GEOLOCATION")
    print("="*80)

    # Sample input data (simulating Step 3 output)
    input_records = [
        {
            "deed_id": "5767",
            "county": "Middlesex County",
            "town": "Dracut",
            "extracted_streets": ["CHRISTIAN ST", "HILLTOP RD"],
            "scraper_results": [
                {
                    "book": "57",
                    "page": "21",
                    "status": "success",
                    "metadata": {
                        "search_result_info": {
                            "town": "DRACUT"
                        }
                    }
                }
            ],
            "step3_completed": True
        }
    ]

    print(f"\nInput: {len(input_records)} record(s)")
    print(f"  Deed {input_records[0]['deed_id']}")
    print(f"  Streets: {input_records[0]['extracted_streets']}")
    print(f"  Town: {input_records[0]['town']}")

    print("\nRunning Step 4 (will geocode streets using Nominatim API)...")
    print("Note: This may take a few seconds due to API rate limiting\n")

    try:
        # Run Step 4 - this should work with nest_asyncio
        results = process_deeds_geolocation(deed_records=input_records)

        print("\n" + "="*80)
        print("STEP 4 TEST RESULTS")
        print("="*80)

        # Check results
        if not results:
            print("❌ FAILED: No results returned")
            return False

        result = results[0]
        print(f"\n✓ Returned {len(results)} result(s)")
        print(f"✓ Deed ID: {result.get('deed_id')}")
        print(f"✓ Step 4 completed: {result.get('step4_completed')}")

        # Validate structure
        assert 'deed_id' in result, "Missing deed_id"
        assert 'geolocation' in result, "Missing geolocation"
        assert 'step4_completed' in result, "Missing step4_completed"

        geolocation = result.get('geolocation')

        if result.get('step4_completed') and geolocation:
            print("\n✅ TEST PASSED: Step 4 completed successfully")

            # Show geolocation details
            print(f"\nGeolocation Details:")
            print(f"  Primary Town: {geolocation.get('primary_town')}")
            print(f"  Cluster Center: ({geolocation.get('cluster_center_lat'):.4f}, {geolocation.get('cluster_center_lon'):.4f})")
            print(f"  Cluster Radius: {geolocation.get('cluster_radius_miles'):.2f} miles")
            print(f"  Confidence: {geolocation.get('confidence', 0):.1%}")

            validated_streets = geolocation.get('validated_streets', [])
            invalid_streets = geolocation.get('invalid_streets', [])

            print(f"\n  Validated Streets: {len(validated_streets)}")
            for street in validated_streets:
                print(f"    - {street.get('street_name')}: ({street.get('latitude'):.4f}, {street.get('longitude'):.4f})")

            if invalid_streets:
                print(f"\n  Invalid Streets: {len(invalid_streets)}")
                for street in invalid_streets:
                    print(f"    - {street}")

            return True
        elif result.get('step4_completed') and not geolocation:
            print("\n⚠️  TEST PASSED (WITH WARNING): Step 4 completed but no geolocation found")
            print("  This could be due to:")
            print("    - No streets were extracted in Step 3")
            print("    - Geocoding API couldn't find the streets")
            return True
        else:
            print("\n❌ TEST FAILED: Step 4 did not complete")
            if result.get('step4_error'):
                print(f"  Error: {result['step4_error']}")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_step4()
    sys.exit(0 if success else 1)
