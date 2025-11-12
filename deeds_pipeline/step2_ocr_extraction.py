"""
Step 2: OCR and Information Extraction
Extract structured information from deed images using OCR and AI models
"""

from typing import Dict, List, Optional
from pathlib import Path

from .utils import setup_logger, load_json, save_json, get_cache_key, load_from_cache, save_to_cache
from .config import STEP1_OUTPUT, STEP2_OUTPUT, ENABLE_CACHE


logger = setup_logger("step2_ocr_extraction", "step2.log")


def extract_text_with_google_vision(image_url: str) -> Optional[str]:
    """
    Extract text from image using Google Vision API
    
    Args:
        image_url: URL of the image to process
    
    Returns:
        Extracted text or None if failed
    """
    
    # TODO: Implement Google Vision OCR
    # 1. Download image from URL
    # 2. Call Google Vision API for text detection
    # 3. Extract full_text_annotation.text
    # 4. Return extracted text
    
    # Reference: other_repo/mistral_rrc_updated.ipynb
    # Function: extract_text_with_google_vision()
    
    logger.debug(f"Extracting text from image: {image_url}")
    
    # TODO: Your implementation here
    # Example:
    # from google.cloud import vision
    # client = vision.ImageAnnotatorClient()
    # image = vision.Image()
    # image.source.image_uri = image_url
    # response = client.document_text_detection(image=image)
    # return response.full_text_annotation.text
    
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
    
    # TODO: Implement Mistral-RRC covenant detection
    # 1. Format prompt using format_prompt()
    # 2. Call Mistral-RRC model for generation
    # 3. Parse output using parse_output()
    # 4. Return structured result
    
    # Reference: other_repo/mistral_rrc_updated.ipynb
    # Functions: format_prompt(), parse_output()
    # Model: "reglab-rrc/mistral-rrc"
    
    logger.debug(f"Detecting restrictive covenant in text (length: {len(text)})")
    
    # TODO: Your implementation here
    # Example:
    # from transformers import AutoTokenizer, AutoModelForCausalLM
    # tokenizer = AutoTokenizer.from_pretrained("reglab-rrc/mistral-rrc")
    # model = AutoModelForCausalLM.from_pretrained("reglab-rrc/mistral-rrc")
    # prompt = format_prompt(text)
    # inputs = tokenizer(prompt, return_tensors="pt")
    # outputs = model.generate(**inputs, max_new_tokens=512)
    # result = tokenizer.decode(outputs[0])
    # return parse_output(result)
    
    return {
        "covenant_detected": False,
        "raw_passage": None,
        "corrected_quotation": None
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
    
    # TODO: Implement Gemini extraction
    # 1. Format prompt with OCR text
    # 2. Call Gemini API (gemini-2.5-flash model)
    # 3. Parse JSON response
    # 4. Return structured data
    
    # Reference: other_repo/mistral_rrc_updated.ipynb
    # Function: extract_deed_info_with_gemini()
    
    logger.debug(f"Extracting deed info with Gemini (text length: {len(ocr_text)})")
    
    # TODO: Your implementation here
    # Example:
    # from google import genai
    # client = genai.Client(api_key=GEMINI_API_KEY)
    # prompt = f"""Extract structured info from deed text: {ocr_text}
    # Return as JSON with keys: plan_book, plan_pages, lot_numbers, street_addresses, city_town"""
    # response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    # return json.loads(response.text)
    
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
        covenant_result = detect_restrictive_covenant(ocr_text)
        
        # Extract structured information
        deed_info = extract_deed_info_with_gemini(ocr_text)
        
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


def run_step2(input_file: Path = STEP1_OUTPUT, output_file: Path = STEP2_OUTPUT) -> Dict[str, Dict]:
    """
    Run Step 2: OCR and information extraction
    
    Args:
        input_file: Path to Step 1 output file
        output_file: Path to Step 2 output file
    
    Returns:
        Deed data with OCR and extraction results
    """
    logger.info(f"Starting Step 2: OCR and Information Extraction")
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    
    try:
        # Load input data
        logger.info("Loading Step 1 output...")
        deed_data = load_json(input_file)
        logger.info(f"Loaded {len(deed_data)} deed records")
        
        # Process each deed
        processed_data = {}
        total = len(deed_data)
        
        for idx, (deed_id, deed_record) in enumerate(deed_data.items(), 1):
            logger.info(f"Processing deed {deed_id} ({idx}/{total})")
            processed_data[deed_id] = process_deed_images(deed_record)
        
        # Save output
        logger.info("Saving processed data...")
        save_json(processed_data, output_file)
        logger.info(f"Step 2 completed. Output saved to {output_file}")
        
        return processed_data
        
    except Exception as e:
        logger.error(f"Error in Step 2: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_step2()

