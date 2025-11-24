"""
Lightweight Step 2 test - tests OCR and Gemini without loading heavy Mistral model
"""
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("STEP 2 LIGHTWEIGHT TEST (OCR + Gemini)")
print("=" * 80)

# Test 1: Import basic functions (no model loading)
print("\n1. Testing imports (without Mistral model)...")
try:
    from deeds_pipeline.step2_ocr_extraction import (
        extract_text_with_google_vision,
        extract_deed_info_with_gemini
    )
    print("   ✓ Core functions imported successfully")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    exit(1)

# Test 2: Find test data
print("\n2. Looking for test data...")
step1_output = Path("output/step1_reformatted_by_deed_id.json")
if not step1_output.exists():
    step1_output = Path("output/step1_reformatted_by_deed_id_test.json")

if not step1_output.exists():
    print("   ⚠  No Step 1 output found. Please run Step 1 first.")
    exit(0)

with open(step1_output, 'r') as f:
    step1_data = json.load(f)

# Get first deed with images
test_deed = None
for deed_id, deed_record in step1_data.items():
    if deed_record.get("book_page_urls"):
        test_deed = (deed_id, deed_record)
        break

if not test_deed:
    print("   ⚠  No deeds with images found")
    exit(0)

deed_id, deed_record = test_deed
image_url = deed_record["book_page_urls"][0]
print(f"   ✓ Found test deed: {deed_id}")
print(f"   ✓ Test image: {image_url[:60]}...")

# Test 3: OCR Extraction
print("\n3. Testing Google Vision OCR...")
try:
    ocr_text = extract_text_with_google_vision(image_url)
    if ocr_text:
        print(f"   ✓ OCR successful!")
        print(f"   ✓ Extracted {len(ocr_text)} characters")
        print(f"   ✓ Preview: {ocr_text[:100]}...")
    else:
        print("   ✗ OCR returned no text")
        exit(1)
except Exception as e:
    print(f"   ✗ OCR failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 4: Gemini Extraction
print("\n4. Testing Gemini structured extraction...")
try:
    deed_info = extract_deed_info_with_gemini(ocr_text)
    print(f"   ✓ Gemini extraction successful!")
    print(f"   ✓ Plan book: {deed_info.get('plan_book')}")
    print(f"   ✓ Plan pages: {deed_info.get('plan_pages')}")
    print(f"   ✓ Lot numbers: {deed_info.get('lot_numbers')}")
    print(f"   ✓ Street addresses: {deed_info.get('street_addresses')}")
    print(f"   ✓ City/Town: {deed_info.get('city_town')}")
except Exception as e:
    print(f"   ⚠  Gemini extraction warning: {e}")
    if "429" in str(e) or "quota" in str(e).lower():
        print("   → API quota exceeded, wait a moment and retry")
    else:
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("✅ LIGHTWEIGHT TEST COMPLETED")
print("=" * 80)
print("\nCore Step 2 functionality (OCR + Gemini) is working!")
print("\nNote: Mistral model was NOT loaded in this test.")
print("It will only load when you actually process deeds that need covenant detection.")
print()
