from pptx import Presentation
from typing import Dict, List, Tuple
import os
import tempfile
from PIL import Image
import io


def extract_images_from_pptx(pptx_path: str, output_dir: str = None) -> Dict[int, List[str]]:
    """
    Extracts images from each slide in a .pptx file and saves them as PNG files.
    
    Args:
        pptx_path: Path to the PowerPoint file.
        output_dir: Directory to save extracted images. If None, uses a temp directory.
    
    Returns:
        Dictionary mapping slide number (1-indexed) to list of image file paths.
    """
    # Check if file exists
    if not os.path.exists(pptx_path):
        raise FileNotFoundError(f"PowerPoint file not found: {pptx_path}")
    
    # Create output directory if not provided
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="pptx_images_")
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        prs = Presentation(pptx_path)
    except Exception as e:
        raise ValueError(f"Error opening PowerPoint file: {e}")
    
    slide_images = {}
    
    for slide_num, slide in enumerate(prs.slides, start=1):
        image_paths = []
        image_count = 0
        
        for shape in slide.shapes:
            if hasattr(shape, 'image'):
                try:
                    # Get image data
                    image_data = shape.image.blob
                    image_format = shape.image.ext
                    
                    # Create filename
                    image_filename = f"slide_{slide_num}_image_{image_count + 1}.{image_format}"
                    image_path = os.path.join(output_dir, image_filename)
                    
                    # Save image
                    with open(image_path, 'wb') as f:
                        f.write(image_data)
                    
                    image_paths.append(image_path)
                    image_count += 1
                    
                except Exception as e:
                    print(f"Warning: Could not extract image from slide {slide_num}: {e}")
                    continue
        
        slide_images[slide_num] = image_paths
    
    return slide_images


def print_image_extraction_results(slide_images: Dict[int, List[str]], pptx_path: str = None):
    """
    Pretty print the image extraction results.
    
    Args:
        slide_images: Dictionary of slide number to image paths mapping
        pptx_path: Optional file path to display
    """
    if pptx_path:
        print(f"Extracted images from: {pptx_path}")
        print()
    
    if not slide_images:
        print("No images found in the presentation.")
        return
    
    total_images = sum(len(images) for images in slide_images.values())
    print(f"Found {total_images} images across {len(slide_images)} slides:")
    print("-" * 60)
    
    for slide_num, image_paths in slide_images.items():
        print(f"slide {slide_num}:")
        if image_paths:
            for i, image_path in enumerate(image_paths, 1):
                print(f"  image {i}: {os.path.basename(image_path)}")
        else:
            print("  (no images)")
        print()


# Example usage for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extract_images.py path/to/file.pptx [output_directory]")
        print("Example: python extract_images.py test_ppts/sample.pptx")
        sys.exit(1)
    
    pptx_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        slide_images = extract_images_from_pptx(pptx_path, output_dir)
        print_image_extraction_results(slide_images, pptx_path)
        
        if output_dir:
            print(f"Images saved to: {output_dir}")
        else:
            print("Images saved to temporary directory")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1) 