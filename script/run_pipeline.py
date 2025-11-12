#!/usr/bin/env python3
"""
Main Pipeline Script
Runs all 5 steps of the deeds processing pipeline sequentially
"""

import sys
import time
from pathlib import Path

# Add parent directory to path to import deeds_pipeline
sys.path.insert(0, str(Path(__file__).parent.parent))

from deeds_pipeline.utils import setup_logger
from deeds_pipeline.step1_json_reformat import run_step1
from deeds_pipeline.step2_ocr_extraction import run_step2
from deeds_pipeline.step3_scraper import run_step3
from deeds_pipeline.step4_geolocation import run_step4
from deeds_pipeline.step5_integration import run_step5


logger = setup_logger("main_pipeline", "pipeline.log")


def run_full_pipeline(start_from_step: int = 1, stop_at_step: int = 5):
    """
    Run the complete pipeline
    
    Args:
        start_from_step: Which step to start from (1-5)
        stop_at_step: Which step to stop at (1-5)
    """
    logger.info("=" * 80)
    logger.info("DEEDS PROCESSING PIPELINE")
    logger.info("=" * 80)
    logger.info(f"Running steps {start_from_step} to {stop_at_step}")
    logger.info("")
    
    start_time = time.time()
    
    try:
        # Step 1: JSON Reformat
        if start_from_step <= 1 <= stop_at_step:
            logger.info("-" * 80)
            logger.info("STEP 1: JSON Reformat (deed_review_id → deed_id)")
            logger.info("-" * 80)
            step1_start = time.time()
            run_step1()
            step1_time = time.time() - step1_start
            logger.info(f"Step 1 completed in {step1_time:.2f} seconds")
            logger.info("")
        
        # Step 2: OCR and Information Extraction
        if start_from_step <= 2 <= stop_at_step:
            logger.info("-" * 80)
            logger.info("STEP 2: OCR and Information Extraction")
            logger.info("-" * 80)
            step2_start = time.time()
            run_step2()
            step2_time = time.time() - step2_start
            logger.info(f"Step 2 completed in {step2_time:.2f} seconds")
            logger.info("")
        
        # Step 3: MassLand Scraper
        if start_from_step <= 3 <= stop_at_step:
            logger.info("-" * 80)
            logger.info("STEP 3: MassLand Scraper")
            logger.info("-" * 80)
            step3_start = time.time()
            run_step3()
            step3_time = time.time() - step3_start
            logger.info(f"Step 3 completed in {step3_time:.2f} seconds")
            logger.info("")
        
        # Step 4: Geolocation
        if start_from_step <= 4 <= stop_at_step:
            logger.info("-" * 80)
            logger.info("STEP 4: Geolocation")
            logger.info("-" * 80)
            step4_start = time.time()
            run_step4()
            step4_time = time.time() - step4_start
            logger.info(f"Step 4 completed in {step4_time:.2f} seconds")
            logger.info("")
        
        # Step 5: Data Integration
        if start_from_step <= 5 <= stop_at_step:
            logger.info("-" * 80)
            logger.info("STEP 5: Data Integration")
            logger.info("-" * 80)
            step5_start = time.time()
            result = run_step5()
            step5_time = time.time() - step5_start
            logger.info(f"Step 5 completed in {step5_time:.2f} seconds")
            logger.info("")
            
            # Print quality report
            if result and "quality_report" in result:
                logger.info("=" * 80)
                logger.info("FINAL QUALITY REPORT")
                logger.info("=" * 80)
                for key, value in result["quality_report"].items():
                    logger.info(f"{key}: {value}")
                logger.info("=" * 80)
        
        total_time = time.time() - start_time
        logger.info("")
        logger.info("=" * 80)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"Total execution time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        logger.info("")
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("PIPELINE FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the deeds processing pipeline")
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        choices=[1, 2, 3, 4, 5],
        help="Which step to start from (default: 1)"
    )
    parser.add_argument(
        "--stop",
        type=int,
        default=5,
        choices=[1, 2, 3, 4, 5],
        help="Which step to stop at (default: 5)"
    )
    
    args = parser.parse_args()
    
    if args.start > args.stop:
        print("Error: --start must be <= --stop")
        sys.exit(1)
    
    run_full_pipeline(start_from_step=args.start, stop_at_step=args.stop)

