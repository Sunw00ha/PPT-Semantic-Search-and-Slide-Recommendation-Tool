from pptx import Presentation
from typing import Dict, List
import os


def extract_text_from_pptx(pptx_path: str) -> Dict[int, str]:
    """
    Extracts all text from each slide in a .pptx file.
    
    Args:
        pptx_path: Path to the PowerPoint file.
    
    Returns:
        Dictionary mapping slide number (1-indexed) to combined text.
    """
    # Check if file exists
    if not os.path.exists(pptx_path):
        raise FileNotFoundError(f"PowerPoint file not found: {pptx_path}")
    
    try:
        prs = Presentation(pptx_path)
    except Exception as e:
        raise ValueError(f"Error opening PowerPoint file: {e}")
    
    slide_text = {}

    # python-pptx library has two ways of extracting text from slides:
    # 1. shape.text (for simple text)
    # 2. shape.text_frame (for more complex text layouts)
    # we use shape.text for now 
    for i, slide in enumerate(prs.slides, start=1):
        texts: List[str] = []

        # Extract text from all shapes in the slide
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text:
                cleaned = shape.text.strip()
                if cleaned:
                    texts.append(cleaned)

        # Join all text with newlines and clean up
        combined_text = "\n".join(texts) if texts else "There is no text on this slide"
        slide_text[i] = combined_text

    return slide_text


def print_slide_text(slide_text: Dict[int, str], file_path: str = None) -> None:
    """
    Pretty print the extracted slide text.
    
    Args:
        slide_text: Dictionary of slide number to text mapping
        file_path: Optional file path to display
    """
    if file_path:
        print(f"Extracted text from: {file_path}")
        print()
    
    if not slide_text:
        print("No text found in the presentation.")
        return
    
    for slide_num, text in slide_text.items():
        print(f"slide {slide_num}:")
        if text:
            print(text)
        else:
            print("")
        # TODO: Consider how to handle slides with no text based on needs of image captioning and embedding tasks
        print()


# allow for testing of certain files in test_ppts folder directly from terminal
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extract_text.py path/to/file.pptx")
        print("Example: python extract_text.py test_ppts/sample.pptx")
        sys.exit(1)
    
    path = sys.argv[1]
    
    try:
        text_data = extract_text_from_pptx(path)
        print_slide_text(text_data, path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
