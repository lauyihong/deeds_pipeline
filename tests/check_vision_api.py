"""
Quick test to check Google Vision API configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("GOOGLE VISION API CONFIGURATION CHECK")
print("=" * 80)

# Check environment
print("\n1. Environment Variables:")
project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

if project_id:
    print(f"   ⚠️  GOOGLE_CLOUD_PROJECT: {project_id}")
    print(f"      This should be commented out in .env to use gcloud default!")
else:
    print(f"   ✓ GOOGLE_CLOUD_PROJECT: Not set (using gcloud default)")

if creds_path:
    print(f"   ⚠️  GOOGLE_APPLICATION_CREDENTIALS: {creds_path}")
else:
    print(f"   ✓ GOOGLE_APPLICATION_CREDENTIALS: Not set (using gcloud default)")

# Test Vision API
print("\n2. Testing Google Vision API...")
try:
    from google.cloud import vision
    from google.api_core.client_options import ClientOptions

    # Create client WITHOUT specifying project ID
    client = vision.ImageAnnotatorClient()

    print("   ✓ Vision API client created successfully")
    print("   ✓ Using default gcloud credentials")

    # Try a simple test (just to check permissions)
    print("\n3. Testing with a sample image...")

    # Use a simple test image URL
    test_url = "https://ma-covenants.dataplusfeminism.mit.edu/api/book_pages/1149307/show_page.jpg"

    import requests
    image_bytes = requests.get(test_url).content

    vision_image = vision.Image(content=image_bytes)
    response = client.document_text_detection(image=vision_image)

    if response.error.message:
        print(f"   ✗ API Error: {response.error.message}")
    else:
        text = response.full_text_annotation.text
        print(f"   ✓ OCR successful!")
        print(f"   ✓ Extracted {len(text)} characters")
        print(f"   ✓ Preview: {text[:100]}...")

except Exception as e:
    print(f"   ✗ Error: {e}")
    print("\n   Solutions:")
    print("   1. Make sure you've run: gcloud auth application-default login")
    print("   2. Check your .env file - comment out GOOGLE_CLOUD_PROJECT")
    print("   3. Enable Vision API: gcloud services enable vision.googleapis.com")

print("\n" + "=" * 80)
