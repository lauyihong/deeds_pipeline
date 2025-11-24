"""
Simple API configuration test (without heavy models)
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("SIMPLE API CONFIGURATION TEST")
print("=" * 80)

# Test 1: Environment Variables
print("\n1. Checking environment variables...")
api_key = os.getenv("GOOGLE_API_KEY")
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

if api_key:
    print(f"   ✓ GOOGLE_API_KEY: {api_key[:10]}...")
else:
    print("   ✗ GOOGLE_API_KEY not set")
    exit(1)

if project_id:
    print(f"   ✓ GOOGLE_CLOUD_PROJECT: {project_id}")
else:
    print("   ✗ GOOGLE_CLOUD_PROJECT not set")
    exit(1)

# Test 2: Gemini API
print("\n2. Testing Gemini API connection...")
try:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    print("   ✓ Gemini API configured successfully")

    # Try a simple test (skip if quota exceeded)
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content("Say OK")
        print(f"   ✓ Gemini API test successful: {response.text.strip()[:20]}")
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            print("   ⚠  Gemini API quota exceeded (will reset soon)")
        else:
            print(f"   ⚠  Gemini test error: {e}")

except Exception as e:
    print(f"   ✗ Gemini API configuration failed: {e}")
    exit(1)

# Test 3: Vision API
print("\n3. Testing Google Cloud Vision API...")
try:
    from google.cloud import vision
    from google.api_core.client_options import ClientOptions

    client_options = ClientOptions(quota_project_id=project_id)
    client = vision.ImageAnnotatorClient(client_options=client_options)
    print("   ✓ Vision API client created successfully")
    print(f"   ✓ Using project: {project_id}")

except Exception as e:
    print(f"   ✗ Vision API initialization failed!")
    print(f"      Error: {e}")
    print("\n   Solutions:")
    print("   1. Run: gcloud auth application-default login")
    print("   2. Or remove GOOGLE_APPLICATION_CREDENTIALS from .env")
    exit(1)

print("\n" + "=" * 80)
print("✅ ALL API CONFIGURATIONS SUCCESSFUL!")
print("=" * 80)
print("\nNext steps:")
print("1. Run: python test_step2.py (full test)")
print("2. Or proceed to use Step 2 in your notebook")
print()
