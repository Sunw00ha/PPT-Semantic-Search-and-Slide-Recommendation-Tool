from transformers import Blip2Processor, Blip2ForConditionalGeneration
from PIL import Image
import torch
from typing import Dict, List
import os

# Download Salesforce's pre-trained BLIP-2 model from HuggingFace and load it into memory so we can feed it images and get captions back
# This is created as a class to allow us to store self.processor and self.model as instance variables
# load them once and then use them for each image
class Blip2ImageCaptioner:
    def __init__(self, model_name: str = "Salesforce/blip2-opt-2.7b"):
        """
        Initialize the BLIP-2 image captioning model.
        
        Args:
            model_name: Name of the pre-trained BLIP-2 model to use
        """
        self.device = "cpu"
        
        # Load model and processor
        self.processor = Blip2Processor.from_pretrained(model_name)
        self.model = Blip2ForConditionalGeneration.from_pretrained(
            model_name, 
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device)


def generate_caption_for_image_blip2(image_path: str, captioner: Blip2ImageCaptioner) -> str:
    """
    Generate a caption for a single image using BLIP-2.
    
    Args:
        image_path: Path to the image file
        captioner: Initialized Blip2ImageCaptioner instance
    
    Returns:
        Generated caption string
    """
    try:
        # Load and preprocess image
        image = Image.open(image_path).convert('RGB')
        
        # Prepare image for model
        # The model cannot directly process JPEG/PNG. It needs to be converted into a specific number format
        inputs = captioner.processor(image, return_tensors="pt").to(captioner.device, captioner.model.dtype)
        
        # Generate caption
        with torch.no_grad(): # skip tracking
            output_ids = captioner.model.generate(
                **inputs,
                max_length=50,
                num_beams=5,
                do_sample=True,
                temperature=0.7,
                top_p=0.9
            )
        
        # Decode the generated caption --> converting the number output of the model into a string
        caption = captioner.processor.batch_decode(output_ids, skip_special_tokens=True)[0].strip()
        
        return caption
        
    except Exception as e:
        print(f"Error captioning image {image_path}: {e}")
        return "Error generating caption"


def caption_images_from_slides_blip2(slide_images: Dict[int, List[str]], captioner: Blip2ImageCaptioner) -> Dict[int, List[str]]:
    """
    Generate captions for all images from slides using BLIP-2.
    
    Args:
        slide_images: Dictionary mapping slide number to list of image paths
        captioner: Initialized Blip2ImageCaptioner object
    
    Returns:
        Dictionary mapping slide number to list of captions
    """
    slide_captions = {}
    
    for slide_num, image_paths in slide_images.items():
        captions = []
        
        for image_path in image_paths:
            if os.path.exists(image_path):
                caption = generate_caption_for_image_blip2(image_path, captioner)
                captions.append(caption)
            else:
                print(f"Warning: Image file not found: {image_path}")
                captions.append("Image file not found")
        
        slide_captions[slide_num] = captions
    
    return slide_captions


def print_caption_results(slide_captions: Dict[int, List[str]], pptx_path: str = None):
    """
    Pretty print the caption results.
    
    Args:
        slide_captions: Dictionary of slide number to captions mapping
        pptx_path: Optional file path to display
    """
    if pptx_path:
        print(f"BLIP-2 image captioning results for: {pptx_path}")
        print()
    
    if not slide_captions:
        print("No captions generated.")
        return
    
    total_captions = sum(len(captions) for captions in slide_captions.values())
    print(f"Generated {total_captions} captions across {len(slide_captions)} slides:")
    print("-" * 60) # separator line
    
    for slide_num, captions in slide_captions.items():
        print(f"slide {slide_num}:")
        if captions:
            for i, caption in enumerate(captions, 1):
                print(f"  image {i}: {caption}")
        else:
            print("  (no images)")
        print()


# Example usage for testing
if __name__ == "__main__":
    import sys
    from extract_images import extract_images_from_pptx
    
    if len(sys.argv) < 2:
        print("Usage: python caption_images_blip2.py path/to/file.pptx")
        print("Example: python caption_images_blip2.py test_ppts/sample.pptx")
        sys.exit(1)
    
    pptx_path = sys.argv[1]
    
    try:
        # Extract images from PowerPoint
        slide_images = extract_images_from_pptx(pptx_path)
        
        if not slide_images:
            print("No images found in the presentation.")
            sys.exit(0)
        
        # Initialize BLIP-2 captioner
        captioner = Blip2ImageCaptioner()
        
        # Generate captions
        slide_captions = caption_images_from_slides_blip2(slide_images, captioner)
        
        # Print results
        print_caption_results(slide_captions, pptx_path)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1) 
