"""
Run covenant detection separately using Mistral-RRC model

This script processes Step 2 output and adds covenant detection results.
Use this after completing the main pipeline on a machine with better specs.

Usage:
    python run_covenant_detection.py
    python run_covenant_detection.py --input step2_output.json --output step2_with_covenants.json
    python run_covenant_detection.py --limit 10  # Test with 10 deeds first
"""
import argparse
from pathlib import Path
from tqdm import tqdm
import logging

# Suppress verbose logging
logging.getLogger('step2_ocr_extraction').setLevel(logging.WARNING)

from deeds_pipeline.step2_ocr_extraction import (
    detect_restrictive_covenant,
    load_json,
    save_json,
    STEP2_OUTPUT
)

def run_covenant_detection(input_file, output_file, limit=None):
    """
    Add covenant detection to existing Step 2 results

    Args:
        input_file: Path to Step 2 output JSON
        output_file: Path to save updated results
        limit: Optional limit for testing
    """
    print("=" * 80)
    print("COVENANT DETECTION (MISTRAL-RRC MODEL)")
    print("=" * 80)
    print(f"\nInput:  {input_file}")
    print(f"Output: {output_file}")

    # Load data
    print("\n📂 Loading Step 2 data...")
    deed_data = load_json(input_file)

    if limit:
        deed_items = list(deed_data.items())[:limit]
        print(f"✓ Loaded {len(deed_data)} deeds (processing first {limit} for testing)")
    else:
        deed_items = list(deed_data.items())
        print(f"✓ Loaded {len(deed_data)} deeds")

    # Statistics
    stats = {
        "total": len(deed_items),
        "processed": 0,
        "covenants_detected": 0,
        "already_done": 0,
        "no_ocr_text": 0,
        "errors": []
    }

    print(f"\n🤖 Running Mistral-RRC covenant detection...")
    print("⚠️  This may take 1-2 minutes per deed on CPU")

    with tqdm(total=len(deed_items), desc="Processing", unit="deed") as pbar:
        for deed_id, deed_record in deed_items:
            ocr_results = deed_record.get("ocr_results", [])

            if not ocr_results:
                stats["no_ocr_text"] += 1
                pbar.update(1)
                continue

            for ocr_result in ocr_results:
                # Skip if already processed
                covenant_note = ocr_result.get("covenant_detection", {}).get("note")
                if covenant_note != "Mistral model skipped for speed. Run separately later.":
                    stats["already_done"] += 1
                    continue

                ocr_text = ocr_result.get("ocr_text")
                if not ocr_text:
                    stats["no_ocr_text"] += 1
                    continue

                try:
                    # Run Mistral model
                    covenant_result = detect_restrictive_covenant(ocr_text)

                    # Update result
                    ocr_result["covenant_detection"] = covenant_result

                    stats["processed"] += 1
                    if covenant_result.get("covenant_detected"):
                        stats["covenants_detected"] += 1

                except Exception as e:
                    stats["errors"].append(f"Deed {deed_id}: {str(e)[:100]}")
                    ocr_result["covenant_detection"] = {
                        "covenant_detected": False,
                        "error": str(e)
                    }

            pbar.update(1)
            pbar.set_postfix({
                "processed": stats["processed"],
                "covenants": stats["covenants_detected"],
                "errors": len(stats["errors"])
            })

    # Save results
    print(f"\n💾 Saving results...")
    save_json(deed_data, output_file)

    # Print summary
    print("\n" + "=" * 80)
    print("COVENANT DETECTION COMPLETED")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"  Total deeds:              {stats['total']}")
    print(f"  Images processed:         {stats['processed']}")
    print(f"  Covenants detected:       {stats['covenants_detected']}")
    print(f"  Already processed:        {stats['already_done']}")
    print(f"  No OCR text:              {stats['no_ocr_text']}")
    print(f"  Errors:                   {len(stats['errors'])}")

    if stats['errors']:
        print(f"\n⚠️  Errors encountered:")
        for error in stats['errors'][:5]:
            print(f"  - {error}")
        if len(stats['errors']) > 5:
            print(f"  ... and {len(stats['errors']) - 5} more")

    print(f"\n✓ Output saved to: {output_file}")
    print()

    return deed_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run covenant detection on Step 2 results")
    parser.add_argument(
        "--input",
        type=Path,
        default=STEP2_OUTPUT,
        help="Input file (Step 2 output)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file (defaults to input file with '_with_covenants' suffix)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of deeds to process (for testing)"
    )

    args = parser.parse_args()

    # Default output file
    if args.output is None:
        input_path = Path(args.input)
        args.output = input_path.parent / f"{input_path.stem}_with_covenants{input_path.suffix}"

    result = run_covenant_detection(args.input, args.output, args.limit)
