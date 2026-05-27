from extract_images import extract_images_from_pptx
from caption_images_blip2 import Blip2ImageCaptioner, caption_images_from_slides_blip2
from typing import Dict, List
import os

_captioner_instance = None


def _get_captioner() -> Blip2ImageCaptioner:
    """Load the BLIP-2 model once and reuse it across all calls."""
    global _captioner_instance
    if _captioner_instance is None:
        _captioner_instance = Blip2ImageCaptioner()
    return _captioner_instance


def run_image_captioning_pipeline_blip2(pptx_path: str) -> Dict[int, List[str]]:
    """
    Complete pipeline: extract images from PowerPoint and generate captions using BLIP-2.
    
    Args:
        pptx_path: Path to the PowerPoint file
    
    Returns:
        Dictionary mapping slide number (1-indexed) to list of image captions.
        Empty list for slides with no images.
    """
    # Step 1: Extract images from slides
    slide_images = extract_images_from_pptx(pptx_path)
    
    # if no images are found, return an empty dictionary
    if not slide_images or not any(slide_images.values()):
        return {slide_num: [] for slide_num in slide_images}
    
    # Step 2: Get BLIP-2 captioning model (loaded once, reused across files)
    captioner = _get_captioner()
    
    # Step 3: Generate captions for all images
    slide_captions = caption_images_from_slides_blip2(slide_images, captioner)
    
    return slide_captions


def print_pipeline_results(slide_captions: Dict[int, List[str]], pptx_path: str = None):
    """
    Print the final results in the requested format.
    
    Args:
        slide_captions: Dictionary of slide number to captions mapping
        pptx_path: Optional file path to display
    """
    if pptx_path:
        print(f"BLIP-2 image captioning results for: {pptx_path}")
        print()
    
    if not slide_captions:
        return
    
    for slide_num, captions in slide_captions.items():
        print(f"slide {slide_num}:")
        if captions:
            for caption in captions:
                print(f"  {caption}")
        else:
            print("  No images to caption")
        print()


# Example usage for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python image_captioning_pipeline_blip2.py path/to/file.pptx")
        print("Example: python image_captioning_pipeline_blip2.py test_ppts/sample.pptx")
        sys.exit(1)
    
    pptx_path = sys.argv[1]
    
    try:
        # Run the complete pipeline
        slide_captions = run_image_captioning_pipeline_blip2(pptx_path)
        
        # Print results in the requested format
        print_pipeline_results(slide_captions, pptx_path)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1) 
