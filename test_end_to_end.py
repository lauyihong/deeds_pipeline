#!/usr/bin/env python3
"""
End-to-End Integration Test for Steps 3-5
Tests the complete pipeline with function-based interfaces
"""

import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from deeds_pipeline.step3_scraper import process_deeds_scraping
from deeds_pipeline.step4_geolocation import process_deeds_geolocation
from deeds_pipeline.step5_integration import process_deeds_integration

def test_end_to_end():
    """Test complete pipeline Steps 3->4->5"""
    print("="*80)
    print("END-TO-END INTEGRATION TEST: STEPS 3-5")
    print("="*80)

    # Sample input data
    input_records = [
        {
            "deed_id": "5767",
            "book": "57",
            "page": "21",
            "county": "Middlesex County",
            "town": "Dracut"
        }
    ]

    print(f"\nStarting with {len(input_records)} input record(s)")
    print(f"  Deed {input_records[0]['deed_id']}: Book {input_records[0]['book']}, Page {input_records[0]['page']}")

    try:
        # STEP 3: Web Scraping
        print("\n" + "-"*80)
        print("STEP 3: WEB SCRAPING")
        print("-"*80)
        step3_results = process_deeds_scraping(
            deed_records=input_records,
            headless=True
        )

        if not step3_results or not step3_results[0].get('step3_completed'):
            print("❌ Step 3 failed")
            return False

        print(f"✓ Step 3 completed: {len(step3_results)} records processed")
        print(f"  Streets extracted: {step3_results[0].get('extracted_streets', [])}")

        # STEP 4: Geolocation
        print("\n" + "-"*80)
        print("STEP 4: GEOLOCATION")
        print("-"*80)
        step4_results = process_deeds_geolocation(deed_records=step3_results)

        if not step4_results or not step4_results[0].get('step4_completed'):
            print("❌ Step 4 failed")
            return False

        print(f"✓ Step 4 completed: {len(step4_results)} records processed")
        geolocation = step4_results[0].get('geolocation')
        if geolocation:
            print(f"  Coordinates: ({geolocation.get('cluster_center_lat'):.4f}, {geolocation.get('cluster_center_lon'):.4f})")
            print(f"  Confidence: {geolocation.get('confidence', 0):.1%}")

        # STEP 5: Integration
        print("\n" + "-"*80)
        print("STEP 5: DATA INTEGRATION")
        print("-"*80)
        final_records, final_df, quality_report = process_deeds_integration(deed_records=step4_results)

        if final_df is None or len(final_df) == 0:
            print("❌ Step 5 failed")
            return False

        print(f"✓ Step 5 completed: {len(final_df)} records in final output")
        print(f"\nQuality Report:")
        for key, value in quality_report.items():
            print(f"  {key}: {value}")

        # Save outputs
        output_dir = PROJECT_ROOT / "output"
        output_dir.mkdir(exist_ok=True)

        # Save JSON
        json_file = output_dir / "test_e2e_output.json"
        with open(json_file, 'w') as f:
            json.dump({
                "metadata": {"quality_report": quality_report},
                "deeds": {r["deed_id"]: r for r in final_records}
            }, f, indent=2)

        # Save CSV
        csv_file = output_dir / "test_e2e_output.csv"
        final_df.to_csv(csv_file, index=False)

        print("\n" + "="*80)
        print("✅ END-TO-END TEST PASSED")
        print("="*80)
        print(f"\nOutputs saved:")
        print(f"  JSON: {json_file}")
        print(f"  CSV:  {csv_file}")

        print(f"\nFinal DataFrame Shape: {final_df.shape}")
        print(f"Columns: {list(final_df.columns)[:10]}...")  # Show first 10 columns

        # Show sample data
        print(f"\nSample Output (first record):")
        first_row = final_df.iloc[0]
        print(f"  Deed ID: {first_row.get('deed_id')}")
        print(f"  County: {first_row.get('county')}")
        print(f"  Scraped Streets: {first_row.get('scraped_streets')}")
        print(f"  Geo Latitude: {first_row.get('geo_latitude')}")
        print(f"  Geo Longitude: {first_row.get('geo_longitude')}")
        print(f"  Geo Confidence: {first_row.get('geo_confidence')}")
        print(f"  Step 3 Completed: {first_row.get('step3_completed')}")
        print(f"  Step 4 Completed: {first_row.get('step4_completed')}")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_end_to_end()
    sys.exit(0 if success else 1)
