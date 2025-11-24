"""
Test script for Step 2: OCR and Information Extraction
Tests with a small subset of data to verify configuration
"""
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Check if all required environment variables are set"""
    print("=" * 80)
    print("STEP 2 CONFIGURATION CHECK")
    print("=" * 80)

    required_vars = {
        "GOOGLE_API_KEY": "Gemini API Key",
        "GOOGLE_CLOUD_PROJECT": "Google Cloud Project ID"
    }

    optional_vars = {
        "GOOGLE_APPLICATION_CREDENTIALS": "Google Cloud Vision Credentials (optional if using gcloud auth)"
    }

    print("\n✓ Required Environment Variables:")
    all_present = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"  ✓ {var}: {masked_value}")
        else:
            print(f"  ✗ {var}: NOT SET ({description})")
            all_present = False

    print("\n✓ Optional Environment Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  ✓ {var}: {value}")
        else:
            print(f"  - {var}: Not set ({description})")

    if not all_present:
        print("\n❌ Missing required environment variables!")
        print("   Please update your .env file and try again.")
        return False

    print("\n✓ All required environment variables are set!")
    return True


def check_dependencies():
    """Check if all required Python packages are installed"""
    print("\n" + "=" * 80)
    print("DEPENDENCY CHECK")
    print("=" * 80)

    dependencies = {
        "google.generativeai": "google-generativeai",
        "google.cloud.vision": "google-cloud-vision",
        "transformers": "transformers",
        "torch": "torch",
        "PIL": "pillow"
    }

    all_installed = True
    for module_name, package_name in dependencies.items():
        try:
            __import__(module_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ✗ {package_name} - NOT INSTALLED")
            all_installed = False

    if not all_installed:
        print("\n❌ Missing dependencies!")
        print("   Install with: pip install -r requirements.txt")
        return False

    print("\n✓ All dependencies are installed!")
    return True


def test_google_vision():
    """Test Google Cloud Vision API connection"""
    print("\n" + "=" * 80)
    print("GOOGLE CLOUD VISION API TEST")
    print("=" * 80)

    try:
        from google.cloud import vision
        from google.api_core.client_options import ClientOptions

        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        client_options = ClientOptions(quota_project_id=project_id)
        client = vision.ImageAnnotatorClient(client_options=client_options)

        print(f"  ✓ Vision API client initialized successfully")
        print(f"  ✓ Using project: {project_id}")
        return True

    except Exception as e:
        print(f"  ✗ Vision API initialization failed!")
        print(f"     Error: {e}")
        print("\n  Possible solutions:")
        print("  1. Run: gcloud auth application-default login")
        print("  2. Or set GOOGLE_APPLICATION_CREDENTIALS to your service account JSON file")
        return False


def test_gemini():
    """Test Gemini API connection"""
    print("\n" + "=" * 80)
    print("GOOGLE GEMINI API TEST")
    print("=" * 80)

    try:
        import google.generativeai as genai

        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)

        print(f"  ✓ Gemini API configured successfully")

        # Try a simple test
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content("Say 'API test successful' in exactly those words.")

        print(f"  ✓ Gemini API test successful")
        print(f"     Response: {response.text.strip()[:50]}...")
        return True

    except Exception as e:
        print(f"  ✗ Gemini API test failed!")
        print(f"     Error: {e}")
        print("\n  Possible solutions:")
        print("  1. Check your GOOGLE_API_KEY in .env file")
        print("  2. Get a new key from: https://aistudio.google.com/app/apikey")
        return False


def test_transformers_model():
    """Test Hugging Face transformers model loading"""
    print("\n" + "=" * 80)
    print("HUGGING FACE MODEL CHECK")
    print("=" * 80)

    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch

        print("  ⚠  Note: First-time model download may take several minutes (15-20GB)")
        print("  ⚠  Checking if model is already cached...")

        model_name = "reglab-rrc/mistral-rrc"

        # Check if model is cached
        from pathlib import Path
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        if cache_dir.exists():
            model_files = list(cache_dir.glob("*mistral-rrc*"))
            if model_files:
                print(f"  ✓ Model found in cache: {cache_dir}")
            else:
                print(f"  ⚠  Model not in cache. Will download on first run.")

        print(f"  ✓ Transformers library is ready")
        print(f"  ✓ Model: {model_name}")

        if torch.cuda.is_available():
            print(f"  ✓ CUDA available - GPU acceleration enabled")
        else:
            print(f"  ⚠  CUDA not available - using CPU (will be slower)")

        return True

    except Exception as e:
        print(f"  ✗ Model check failed!")
        print(f"     Error: {e}")
        return False


def test_step2_import():
    """Test importing Step 2 module"""
    print("\n" + "=" * 80)
    print("STEP 2 MODULE IMPORT TEST")
    print("=" * 80)

    try:
        from deeds_pipeline.step2_ocr_extraction import (
            extract_text_with_google_vision,
            detect_restrictive_covenant,
            extract_deed_info_with_gemini,
            process_deed_images
        )

        print("  ✓ All Step 2 functions imported successfully")
        return True

    except Exception as e:
        print(f"  ✗ Import failed!")
        print(f"     Error: {e}")
        return False


def test_with_sample_data():
    """Test Step 2 with a minimal sample"""
    print("\n" + "=" * 80)
    print("SAMPLE DATA TEST")
    print("=" * 80)

    # Check if Step 1 output exists
    step1_output = Path("output/step1_reformatted_by_deed_id.json")
    if not step1_output.exists():
        step1_output = Path("output/step1_reformatted_by_deed_id_test.json")

    if not step1_output.exists():
        print("  ⚠  No Step 1 output found. Skipping sample test.")
        print("     Run Step 1 first to generate test data.")
        return None

    try:
        with open(step1_output, 'r') as f:
            step1_data = json.load(f)

        # Get first deed with book_page_urls
        test_deed = None
        for deed_id, deed_record in step1_data.items():
            if deed_record.get("book_page_urls"):
                test_deed = (deed_id, deed_record)
                break

        if not test_deed:
            print("  ⚠  No deeds with book_page_urls found in Step 1 output")
            return None

        deed_id, deed_record = test_deed
        print(f"  ✓ Found test deed: {deed_id}")
        print(f"     Images: {len(deed_record.get('book_page_urls', []))}")

        # Import and test
        from deeds_pipeline.step2_ocr_extraction import process_deed_images

        print(f"\n  → Processing deed {deed_id}...")
        print("     (This may take 1-2 minutes for the first image)")

        result = process_deed_images(deed_record)

        if result.get("step2_completed"):
            print(f"  ✓ Step 2 processing completed!")
            print(f"     OCR results: {len(result.get('ocr_results', []))}")

            # Show first result details
            if result.get('ocr_results'):
                first_result = result['ocr_results'][0]
                print(f"\n  Sample OCR result:")
                print(f"     Text length: {len(first_result.get('ocr_text', ''))} characters")
                print(f"     Covenant detected: {first_result['covenant_detection']['covenant_detected']}")
                if first_result['extracted_info'].get('street_addresses'):
                    print(f"     Streets found: {first_result['extracted_info']['street_addresses']}")

            return True
        else:
            print(f"  ✗ Processing failed")
            return False

    except Exception as e:
        print(f"  ✗ Sample test failed!")
        print(f"     Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("STEP 2 CONFIGURATION AND FUNCTIONALITY TEST")
    print("=" * 80)
    print()

    results = []

    # Run checks
    results.append(("Environment Variables", check_environment()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Google Cloud Vision", test_google_vision()))
    results.append(("Google Gemini", test_gemini()))
    results.append(("Transformers Model", test_transformers_model()))
    results.append(("Step 2 Import", test_step2_import()))

    # Optional: Test with sample data
    sample_result = test_with_sample_data()
    if sample_result is not None:
        results.append(("Sample Data Processing", sample_result))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")

    all_passed = all(r for _, r in results)

    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("=" * 80)
        print("\nStep 2 is ready to use!")
        print("\nNext steps:")
        print("  1. Run the full pipeline: python -m deeds_pipeline.step2_ocr_extraction")
        print("  2. Or use in your notebook: from deeds_pipeline.step2_ocr_extraction import run_step2")
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 80)
        print("\nPlease fix the failed tests before running Step 2.")
        print("See error messages above for troubleshooting steps.")
    print()

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
