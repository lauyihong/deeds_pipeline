#!/usr/bin/env python3
"""
Test script for Step 3 - Web Scraping
Tests the refactored function-based interface
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from deeds_pipeline.step3_scraper import process_deeds_scraping

def test_step3():
    """Test Step 3 with sample data"""
    print("="*80)
    print("TESTING STEP 3: WEB SCRAPING")
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

    print(f"\nInput: {len(input_records)} record(s)")
    print(f"  Deed {input_records[0]['deed_id']}: Book {input_records[0]['book']}, Page {input_records[0]['page']}")

    print("\nRunning Step 3 (this will open a browser window)...")
    print("Note: Using headless=True to run in background\n")

    try:
        # Run Step 3
        results = process_deeds_scraping(
            deed_records=input_records,
            headless=True  # Run in background
        )

        print("\n" + "="*80)
        print("STEP 3 TEST RESULTS")
        print("="*80)

        # Check results
        if not results:
            print("❌ FAILED: No results returned")
            return False

        result = results[0]
        print(f"\n✓ Returned {len(results)} result(s)")
        print(f"✓ Deed ID: {result.get('deed_id')}")
        print(f"✓ Step 3 completed: {result.get('step3_completed')}")
        print(f"✓ Scraper results: {len(result.get('scraper_results', []))} item(s)")
        print(f"✓ Extracted streets: {result.get('extracted_streets', [])}")

        # Validate structure
        assert 'deed_id' in result, "Missing deed_id"
        assert 'scraper_results' in result, "Missing scraper_results"
        assert 'extracted_streets' in result, "Missing extracted_streets"
        assert 'step3_completed' in result, "Missing step3_completed"

        if result.get('step3_completed'):
            print("\n✅ TEST PASSED: Step 3 completed successfully")

            # Show detailed results
            if result.get('scraper_results'):
                scraper_result = result['scraper_results'][0]
                print(f"\nScraper Details:")
                print(f"  Status: {scraper_result.get('status')}")
                print(f"  Book: {scraper_result.get('book')}")
                print(f"  Page: {scraper_result.get('page')}")

                metadata = scraper_result.get('metadata', {})
                if metadata and 'error' not in metadata:
                    print(f"  Metadata keys: {list(metadata.keys())}")

                    # Show property info if available
                    prop_info = metadata.get('property_info', [])
                    if prop_info:
                        print(f"\n  Property Info ({len(prop_info)} items):")
                        for prop in prop_info[:3]:  # Show first 3
                            street = prop.get('Street Name', 'N/A')
                            print(f"    - Street: {street}")

            return True
        else:
            print("\n❌ TEST FAILED: Step 3 did not complete")
            if result.get('step3_error'):
                print(f"  Error: {result['step3_error']}")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_step3()
    sys.exit(0 if success else 1)
