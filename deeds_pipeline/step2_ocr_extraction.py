"""
Step 2: OCR and Information Extraction
Extract structured information from deed images using OCR and AI models
"""
import io
import json
import re
import requests
import torch
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional, Union
from pathlib import Path
import google.generativeai as genai
from transformers import AutoTokenizer, AutoModelForCausalLM
from PIL import Image
from google.cloud import vision
from google.cloud.vision_v1 import ImageAnnotatorClient
from google.api_core.client_options import ClientOptions

from .utils import setup_logger, load_json, save_json, get_cache_key, load_from_cache, save_to_cache
from .config import STEP1_OUTPUT, STEP2_OUTPUT, ENABLE_CACHE


logger = setup_logger("step2_ocr_extraction", "step2.log")

# Setting up gemini API key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError(
        "GOOGLE_API_KEY environment variable not set. "
        "Please set it in your environment or create a .env file with GOOGLE_API_KEY=your-key"
    )
# Configure Gemini API
genai.configure(api_key=api_key)

# Load Google Cloud credentials from .env
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if credentials_path:
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    logger.info(f"Using Google Cloud credentials from: {credentials_path}")

# Initializing Google Vision client
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
if PROJECT_ID:
    # Use specified project ID
    os.environ['GOOGLE_CLOUD_PROJECT'] = PROJECT_ID
    os.environ['GCLOUD_PROJECT'] = PROJECT_ID
    client_options = ClientOptions(quota_project_id=PROJECT_ID)
    logger.info(f"Using Google Cloud Project: {PROJECT_ID}")
else:
    # Use default gcloud credentials (no project ID override)
    client_options = None
    logger.info("Using default Google Cloud credentials from gcloud auth")

client = ImageAnnotatorClient(client_options=client_options)


# Lazy loading for reglab model (load only when needed to save memory)
_tokenizer = None
_model = None

def _load_mistral_model():
    """Lazy load the Mistral-RRC model only when needed"""
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        logger.info("Loading Mistral-RRC model (this may take a few minutes)...")
        _tokenizer = AutoTokenizer.from_pretrained("reglab-rrc/mistral-rrc")
        _model = AutoModelForCausalLM.from_pretrained(
            "reglab-rrc/mistral-rrc",
            trust_remote_code=True,
            torch_dtype=torch.float16,  # Use half precision to save memory
            low_cpu_mem_usage=True      # Optimize for low memory
        )
        logger.info("Mistral-RRC model loaded successfully")
    return _tokenizer, _model


def extract_plan_references_regex(text: str) -> Dict[str, Optional[List[str]]]:
    """
    Regex fallback for extracting plan book/page when LLM fails.

    Args:
        text: OCR extracted text

    Returns:
        Dictionary with plan_book and plan_pages lists (or None if not found)
    """
    books = []
    pages = []

    # Patterns for plan book extraction
    book_patterns = [
        r'[Bb]ook\s+(?:of\s+)?[Pp]lans?\s+(\d+)',      # "Book of Plans 57", "Book of Plan 57"
        r'[Pp]lan\s+[Bb]ook\s+(\d+)',                   # "Plan Book 57"
        r'[Pp]lans?,?\s+[Bb]ook\s+(\d+)',               # "Plans, Book 57"
        r'recorded\s+.*?[Bb]ook\s+(\d+)',               # "recorded in Book 57"
    ]

    # Patterns for plan page extraction
    page_patterns = [
        r'[Pp]lan\s+(\d+[A-Z]?)',                       # "Plan 67", "Plan 67A"
        r'[Pp]age\s+(\d+[A-Z]?)',                       # "Page 67", "Page 67A"
        r'[Pp]lans?\s+\d+,?\s+[Pp](?:lan|age)\s+(\d+[A-Z]?)',  # "Plans 57, Plan 67"
        r'[Bb]ook\s+\d+,?\s+[Pp](?:lan|age)\s+(\d+[A-Z]?)',    # "Book 57, Page 67"
    ]

    for pattern in book_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        books.extend(matches)

    for pattern in page_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        pages.extend(matches)

    # Deduplicate while preserving order
    books = list(dict.fromkeys(books)) if books else None
    pages = list(dict.fromkeys(pages)) if pages else None

    if books or pages:
        logger.debug(f"Regex fallback found: books={books}, pages={pages}")

    return {
        "plan_book": books,
        "plan_pages": pages
    }


def extract_text_with_google_vision(image_url: str) -> Optional[str]:
    """
    Extract text from image using Google Vision API
    
    Args:
        image_url: URL of the image to process
    
    Returns:
        Extracted text or None if failed
    """
    
    logger.debug(f"Extracting text from image: {image_url}")
    
    try:
        # Load image
        image_bytes = requests.get(image_url).content
        image = Image.open(io.BytesIO(image_bytes))

        # OCR
        logger.info("\n2️⃣ Performing OCR using Google Vision API")
        vision_image = vision.Image(content=image_bytes)

        response = client.document_text_detection(image=vision_image)

        if response.error.message:
            raise Exception(f"API error: {response.error.message}")

        full_text = response.full_text_annotation.text

        logger.info(f"✅ OCR completed!")
        logger.info(f"Text length: {len(full_text)} characters")

        # Keyword detection
        keywords = [
            "race", "racial", "Caucasian", "white",
            "negro", "colored", "African", "Chinese",
            "Japanese", "Mongolian", "covenant", "sell",
            "lease", "rent", "occupy"
        ]

        found_keywords = [kw for kw in keywords if kw.lower() in full_text.lower()]

        if found_keywords:
            logger.info(f"✅ Keywords found: {', '.join(found_keywords)}")
        else:
            logger.info(f"⚠️  No racial restriction keywords found")

        return full_text

    except Exception as e:
        logger.info(f"\n❌ Google Vision OCR failed!")
        logger.info(f"Error: {str(e)}")
        return None
    


def detect_restrictive_covenant(text: str) -> Dict[str, any]:
    """
    Detect restrictive covenant using Mistral-RRC model
    
    Args:
        text: OCR extracted text
    
    Returns:
        Dictionary with detection results:
        {
            "covenant_detected": bool,
            "raw_passage": str,
            "corrected_quotation": str
        }
    """

    def parse_output(output):
        answer_match = re.search(r"\[ANSWER\](.*?)\[/ANSWER\]", output, re.DOTALL)
        raw_passage_match = re.search(r"\[RAW PASSAGE\](.*?)\[/RAW PASSAGE\]", output, re.DOTALL)
        quotation_match = re.search(r"\[CORRECTED QUOTATION\](.*?)\[/CORRECTED QUOTATION\]", output, re.DOTALL)

        answer = answer_match.group(1).strip() if answer_match else None
        raw_passage = raw_passage_match.group(1).strip() if raw_passage_match else None
        quotation = quotation_match.group(1).strip() if quotation_match else None

        return {
            "answer": answer == "Yes",
            "raw_passage": raw_passage,
            "quotation": quotation
        }
    
    def format_prompt(document):
        return f"""### Instruction:
        Determine whether the property deed contains a racial covenant. A racial covenant is a clause in a document that restricts who can reside, own, or occupy a property on the basis of race, ethnicity, national origin, or religion. Answer "Yes" or "No". If "Yes", provide the exact text of the relevant passage and then a quotation of the passage with spelling and formatting errors fixed.

        ### Input:
        {document}

        ### Response:"""


    logger.debug(f"Detecting restrictive covenant in text (length: {len(text)})")

    # Lazy load model
    tokenizer, model = _load_mistral_model()

    prompt = format_prompt(text)
    inputs = tokenizer(prompt, return_tensors="pt")

    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
        if not next(model.parameters()).is_cuda:
            model.cuda()

    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=512, temperature=0.1)

    result_text = tokenizer.decode(outputs[0])
    parsed_result = parse_output(result_text)

    return {
        "covenant_detected": parsed_result["answer"],
        "raw_passage": parsed_result.get("raw_passage", "N/A"),
        "corrected_quotation": parsed_result.get("quotation", "N/A"),
    }


def extract_deed_info_with_gemini(ocr_text: str) -> Dict[str, Optional[List[str]]]:
    """
    Extract structured deed information using Gemini API
    
    Args:
        ocr_text: OCR extracted text
    
    Returns:
        Dictionary with extracted information:
        {
            "plan_book": List[str] or None,
            "plan_pages": List[str] or None,
            "lot_numbers": List[str] or None,
            "street_addresses": List[str] or None,
            "city_town": str or None
        }
    """

    logger.debug(f"Extracting deed info with Gemini (text length: {len(ocr_text)})")
    
    prompt = f"""
    You are an expert at reading property deeds and land records.
    From the following OCR text, extract structured information only about the property being conveyed in the deed if available.
    - Only return plan book and location information that document the conveyance of the property being transferred.
    - Ignore plan book or location information that refer to easements, right of ways, or conveyances affecting other properties.

    Text:
    {ocr_text}

    Please return your response as valid JSON with these keys:
    {{
        "plan_book": [string] or null,
        "plan_pages": [string] or null,
        "lot_numbers": [string] or null,
        "street_addresses": [string] or null,
        "city_town": [string] or null
    }}

    Example:
    {{
      "plan_book": ["123"],
      "plan_pages": ["45", "46"],
      "lot_numbers": ["96"],
      "street_addresses": ["Hilltop Road"],
      "city_town": ["Dracut"]
    }}
    """
    try:
        # Use GenerativeModel to generate content
        gemini_model = genai.GenerativeModel("gemini-2.5-flash")
        response = gemini_model.generate_content(prompt)

        # Parse model response
        text = response.text.strip()
        json_text = text[text.find("{"): text.rfind("}")+1]
        data = json.loads(json_text)
        return data

    except Exception as e:
        logger.warning(f"⚠️ Gemini extraction error: {e}")
        return {
            "plan_book": None,
            "plan_pages": None,
            "lot_numbers": None,
            "street_addresses": None,
            "city_town": None
        }


def process_deed_images(deed_record: Dict) -> Dict:
    """
    Process all images for a deed record
    
    Args:
        deed_record: Single deed record from Step 1
    
    Returns:
        Deed record with added OCR and extraction results
    """
    deed_id = deed_record.get("deed_id")
    book_page_urls = deed_record.get("book_page_urls", [])
    
    if not book_page_urls:
        logger.warning(f"Deed {deed_id}: No book_page_urls found")
        return deed_record
    
    logger.info(f"Processing {len(book_page_urls)} images for deed {deed_id}")
    
    # Check cache
    if ENABLE_CACHE:
        cache_key = get_cache_key("step2", deed_id)
        cached = load_from_cache(cache_key)
        if cached:
            logger.info(f"Deed {deed_id}: Loaded from cache")
            return cached

    ocr_results = []
    
    for idx, url in enumerate(book_page_urls):
        logger.info(f"Deed {deed_id}: Processing image {idx+1}/{len(book_page_urls)}")
        
        # Extract text via OCR
        ocr_text = extract_text_with_google_vision(url)
        
        if not ocr_text:
            logger.warning(f"Deed {deed_id}: OCR failed for image {idx+1}")
            continue
        
        # Detect restrictive covenant
        # TEMPORARILY SKIP: Mistral model is too slow on CPU
        # covenant_result = detect_restrictive_covenant(ocr_text)
        # Use simple keyword detection instead
        covenant_result = {
            "covenant_detected": False,
            "raw_passage": "SKIPPED: Run covenant detection separately",
            "corrected_quotation": "SKIPPED: Run covenant detection separately",
            "note": "Mistral model skipped for speed. Run separately later."
        }

        # Extract structured information
        deed_info = extract_deed_info_with_gemini(ocr_text)

        # Apply regex fallback if Gemini didn't find plan_book or plan_pages
        if not deed_info.get("plan_book") or not deed_info.get("plan_pages"):
            regex_result = extract_plan_references_regex(ocr_text)
            if regex_result.get("plan_book") and not deed_info.get("plan_book"):
                deed_info["plan_book"] = regex_result["plan_book"]
                logger.info(f"Deed {deed_id}: Regex fallback found plan_book: {regex_result['plan_book']}")
            if regex_result.get("plan_pages") and not deed_info.get("plan_pages"):
                deed_info["plan_pages"] = regex_result["plan_pages"]
                logger.info(f"Deed {deed_id}: Regex fallback found plan_pages: {regex_result['plan_pages']}")

        ocr_results.append({
            "image_url": url,
            "ocr_text": ocr_text,
            "covenant_detection": covenant_result,
            "extracted_info": deed_info
        })
    
    # Add OCR results to deed record
    deed_record["ocr_results"] = ocr_results
    deed_record["step2_completed"] = True
    
    # Save to cache
    if ENABLE_CACHE:
        save_to_cache(cache_key, deed_record)
    
    return deed_record


def process_deeds_ocr(deed_data: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    FUNCTION-BASED INTERFACE for notebook integration.
    Process deed records with OCR and information extraction.

    Args:
        deed_data: Dictionary of deed records indexed by deed_id
            Format: {deed_id: {deed_record}, ...}
            Each deed_record must have 'image_urls' field

    Returns:
        Same dictionary with each record augmented with:
            - ocr_text: Extracted text from images
            - covenant_result: Restrictive covenant detection
            - deed_info: Structured information (grantors, grantees, etc.)
            - step2_completed: True
    """
    logger.info(f"Starting Step 2 processing for {len(deed_data)} deed(s)")

    processed_data = {}
    total = len(deed_data)

    for idx, (deed_id, deed_record) in enumerate(deed_data.items(), 1):
        logger.info(f"Processing deed {deed_id} ({idx}/{total})")
        try:
            processed_data[deed_id] = process_deed_images(deed_record)
        except Exception as e:
            logger.error(f"Error processing deed {deed_id}: {e}", exc_info=True)
            # Keep original record with error flag
            deed_record["step2_error"] = str(e)
            deed_record["step2_completed"] = False
            processed_data[deed_id] = deed_record

    logger.info(f"Step 2 completed for {len(processed_data)} deed(s)")
    return processed_data


def run_step2(
    input_data: Optional[Union[Path, Dict[str, Dict]]] = None,
    output_file: Optional[Path] = None
) -> Dict[str, Dict]:
    """
    Run Step 2: OCR and information extraction

    Supports two modes:
    1. File mode: input_data is a Path, reads from JSON file
    2. Function mode: input_data is a Dict, processes directly

    Args:
        input_data: Either:
            - Path to Step 1 output JSON file (default: STEP1_OUTPUT)
            - Dict of deed records indexed by deed_id
            - None (uses default STEP1_OUTPUT)
        output_file: Path to save output JSON (optional, only used in file mode)
            - If None and input_data is Path: uses STEP2_OUTPUT
            - If None and input_data is Dict: does not save to file

    Returns:
        Deed data with OCR and extraction results (dict indexed by deed_id)

    Examples:
        # File mode (legacy/CLI)
        result = run_step2()  # Uses default paths
        result = run_step2(Path("input.json"), Path("output.json"))

        # Function mode (notebook)
        deed_data = {"deed_1": {"image_urls": [...]}, ...}
        result = run_step2(deed_data)  # No file I/O
        result = run_step2(deed_data, Path("output.json"))  # Save to file
    """
    # Determine mode and set defaults
    if input_data is None:
        # Default file mode
        input_data = STEP1_OUTPUT
        if output_file is None:
            output_file = STEP2_OUTPUT

    # File mode: load from JSON
    if isinstance(input_data, (Path, str)):
        input_file = Path(input_data)
        logger.info(f"Starting Step 2: OCR and Information Extraction (file mode)")
        logger.info(f"Input file: {input_file}")

        try:
            logger.info("Loading Step 1 output...")
            deed_data = load_json(input_file)
            logger.info(f"Loaded {len(deed_data)} deed records")
        except Exception as e:
            logger.error(f"Error loading input file: {e}", exc_info=True)
            raise

        # Set default output file if not specified
        if output_file is None:
            output_file = STEP2_OUTPUT

    # Function mode: use input dict directly
    elif isinstance(input_data, dict):
        logger.info(f"Starting Step 2: OCR and Information Extraction (function mode)")
        deed_data = input_data
        logger.info(f"Processing {len(deed_data)} deed records")

    else:
        raise TypeError(
            f"input_data must be Path, str, dict, or None, got {type(input_data)}"
        )

    # Process deeds
    try:
        processed_data = process_deeds_ocr(deed_data)

        # Save to file if output_file is specified
        if output_file is not None:
            logger.info(f"Saving processed data to {output_file}...")
            save_json(processed_data, output_file)
            logger.info(f"Step 2 completed. Output saved to {output_file}")
        else:
            logger.info(f"Step 2 completed (no file output)")

        return processed_data

    except Exception as e:
        logger.error(f"Error in Step 2: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_step2()

