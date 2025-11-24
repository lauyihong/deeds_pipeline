"""
Clean wrapper for Step 2 with better output formatting
"""
import sys
from pathlib import Path
from tqdm import tqdm
import logging

# Suppress verbose logging
logging.getLogger('step2_ocr_extraction').setLevel(logging.WARNING)

from deeds_pipeline.step2_ocr_extraction import (
    run_step2,
    load_json,
    STEP1_OUTPUT,
    STEP2_OUTPUT
)

def run_step2_with_progress(input_file=None, output_file=None, limit=None):
    """
    Run Step 2 with clean progress output

    Args:
        input_file: Path to Step 1 output (optional)
        output_file: Path to save Step 2 output (optional)
        limit: Maximum number of deeds to process (for testing)
    """
    input_file = Path(input_file) if input_file else STEP1_OUTPUT
    output_file = Path(output_file) if output_file else STEP2_OUTPUT

    print("=" * 80)
    print("STEP 2: OCR AND INFORMATION EXTRACTION")
    print("=" * 80)
    print(f"\nInput:  {input_file}")
    print(f"Output: {output_file}")

    # Load data
    print("\n📂 Loading Step 1 data...")
    deed_data = load_json(input_file)
    total_deeds = len(deed_data)

    if limit:
        deed_items = list(deed_data.items())[:limit]
        print(f"✓ Loaded {total_deeds} deeds (processing first {limit} for testing)")
    else:
        deed_items = list(deed_data.items())
        print(f"✓ Loaded {total_deeds} deeds")

    # Statistics
    stats = {
        "total": len(deed_items),
        "cached": 0,
        "processed": 0,
        "ocr_success": 0,
        "ocr_failed": 0,
        "errors": []
    }

    # Import here to avoid early initialization
    from deeds_pipeline.step2_ocr_extraction import process_deed_images, ENABLE_CACHE, get_cache_key, load_from_cache

    print(f"\n🔄 Processing deeds...")
    processed_data = {}

    # Use tqdm for progress bar
    with tqdm(total=len(deed_items), desc="Processing", unit="deed") as pbar:
        for deed_id, deed_record in deed_items:
            # Check cache first
            if ENABLE_CACHE:
                cache_key = get_cache_key("step2", deed_id)
                cached = load_from_cache(cache_key)
                if cached:
                    stats["cached"] += 1
                    processed_data[deed_id] = cached
                    pbar.update(1)
                    pbar.set_postfix({
                        "cached": stats["cached"],
                        "new": stats["processed"],
                        "errors": len(stats["errors"])
                    })
                    continue

            # Process deed
            try:
                result = process_deed_images(deed_record)
                processed_data[deed_id] = result
                stats["processed"] += 1

                # Count OCR results
                ocr_results = result.get("ocr_results", [])
                if ocr_results:
                    stats["ocr_success"] += len([r for r in ocr_results if r.get("ocr_text")])
                    stats["ocr_failed"] += len([r for r in ocr_results if not r.get("ocr_text")])

            except Exception as e:
                stats["errors"].append(f"Deed {deed_id}: {str(e)[:100]}")
                processed_data[deed_id] = deed_record
                processed_data[deed_id]["step2_completed"] = False
                processed_data[deed_id]["error"] = str(e)

            pbar.update(1)
            pbar.set_postfix({
                "cached": stats["cached"],
                "new": stats["processed"],
                "errors": len(stats["errors"])
            })

    # Save output
    print(f"\n💾 Saving results...")
    from deeds_pipeline.step2_ocr_extraction import save_json
    save_json(processed_data, output_file)

    # Print summary
    print("\n" + "=" * 80)
    print("STEP 2 COMPLETED")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"  Total deeds:        {stats['total']}")
    print(f"  From cache:         {stats['cached']}")
    print(f"  Newly processed:    {stats['processed']}")
    print(f"  OCR successful:     {stats['ocr_success']}")
    print(f"  OCR failed:         {stats['ocr_failed']}")
    print(f"  Errors:             {len(stats['errors'])}")

    if stats['errors']:
        print(f"\n⚠️  Errors encountered:")
        for error in stats['errors'][:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(stats['errors']) > 5:
            print(f"  ... and {len(stats['errors']) - 5} more")

    print(f"\n✓ Output saved to: {output_file}")
    print()

    return processed_data


if __name__ == "__main__":
    # Parse command line arguments
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

    result = run_step2_with_progress(limit=limit)
