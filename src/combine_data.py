from typing import Dict, List
from extract_text import extract_text_from_pptx
from image_captioning_pipeline_blip2 import run_image_captioning_pipeline_blip2

# Global summarizer variable for lazy loading
summarizer = None


def get_summarizer():
    """Lazy-load the HuggingFace summarization pipeline when needed."""
    global summarizer
    if summarizer is None:
        try:
            from transformers import pipeline
            summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
        except ImportError:
            print("HuggingFace Transformers not installed. Summarization will be skipped.")
            summarizer = None
    return summarizer


def summarize_text_if_long(text: str, threshold_words: int = 150, target_max_words: int = 40) -> str:
    """
    Summarize text if it exceeds the threshold word count using a local transformer model.

    Args:
        text: The original slide text
        threshold_words: Only summarize if text exceeds this many words
        target_max_words: Approximate target length for the summary

    Returns:
        Either the original text or a summarized version
    """
    words = text.split()
    if len(words) <= threshold_words:
        return text.strip()

    summarizer_model = get_summarizer()
    if summarizer_model is None:
        return text.strip()

    try:
        # HuggingFace summarizers use token-based max_length; ~1.5x words
        summary = summarizer_model(
            text,
            max_length=target_max_words * 2,  # tokens ~2x target words
            min_length=max(15, target_max_words // 2),
            do_sample=False
        )[0]["summary_text"]
        return summary.strip()
    except Exception as e:
        print(f"Summarization failed: {e}")
        return text.strip()


def combine_slide_text_and_captions(
    slide_texts: Dict[int, str],
    slide_captions: Dict[int, List[str]],
    summarize_long: bool = True,
    threshold_words: int = 150
) -> Dict[int, str]:
    """
    Combine slide text and image captions into a unified string for each slide.
    Optionally summarize long slide text for better embedding performance.
    """
    combined = {}
    slide_nums = sorted(set(slide_texts.keys()) | set(slide_captions.keys()))

    for slide_num in slide_nums:
        text = slide_texts.get(slide_num, "").strip()
        captions = slide_captions.get(slide_num, [])

        # Optionally summarize long slides
        if summarize_long and text:
            text = summarize_text_if_long(text, threshold_words=threshold_words)

        # Format captions
        caption_str = "\n".join([f"- {cap}" for cap in captions]) if captions else "(no images)"

        # Combine text and captions
        combined_text = f"Slide Text:\n{text if text else '(no text)'}\n\nImage Captions:\n{caption_str}"
        combined[slide_num] = combined_text

    return combined


def print_combined_slide_data(combined: Dict[int, str], pptx_path: str = None):
    """Pretty-print the combined slide data."""
    if pptx_path:
        print(f"Combined slide data for: {pptx_path}\n")

    for slide_num, content in combined.items():
        print(f"Slide {slide_num}:\n{content}\n{'-'*60}")


def combine_slide_data_for_embeddings(
    slide_texts: Dict[int, str],
    slide_captions: Dict[int, List[str]],
    deck_id: str = "unknown_deck",
    summarize_long: bool = True,
    threshold_words: int = 150
) -> List[Dict]:
    """
    Combine slide text and captions into a clean format optimized for embeddings.
    Treats placeholder text (when there is no text on a slide or image to caption) as metadata, not content.
    
    Args:
        slide_texts: Dictionary mapping slide number to text
        slide_captions: Dictionary mapping slide number to list of captions
        deck_id: Identifier for the PowerPoint deck
        summarize_long: Whether to summarize long text
        threshold_words: Word threshold for summarization
    
    Returns:
        List of dictionaries with clean slide data for embedding
    """
    slides_data = []
    slide_nums = sorted(set(slide_texts.keys()) | set(slide_captions.keys()))
    
    for slide_num in slide_nums:
        text = slide_texts.get(slide_num, "").strip()
        captions = slide_captions.get(slide_num, [])
        
        # Clean up text - remove placeholder messages
        if text == "There is no text on this slide":
            text = ""
        
        # Optionally summarize long text (same as regular format)
        if summarize_long and text:
            text = summarize_text_if_long(text, threshold_words=threshold_words)
        
        # Clean up captions - remove placeholder messages
        clean_captions = [cap for cap in captions if cap not in ["(no images)", "No images to caption"]]
        
        # Create clean slide data
        slide_data = {
            "deck_id": deck_id,
            "slide_index": slide_num,
            "text": text,
            "captions": clean_captions,
            "has_text": bool(text),
            "has_image": bool(clean_captions)
        }
        
        slides_data.append(slide_data)
    
    return slides_data


def generate_embedding_data_only(pptx_path: str) -> List[Dict]:
    """
    Generate only the embedding-ready data without verbose output.
    Optimized for the embedding phase.
    
    Args:
        pptx_path: Path to the PowerPoint file
    
    Returns:
        List of dictionaries with clean slide data for embedding
    """
    import os
    
    # Extract data
    slide_texts = extract_text_from_pptx(pptx_path)
    slide_captions = run_image_captioning_pipeline_blip2(pptx_path)
    
    # Create embedding-ready format
    deck_id = os.path.splitext(os.path.basename(pptx_path))[0]
    slides_data = combine_slide_data_for_embeddings(slide_texts, slide_captions, deck_id)
    
    return slides_data


def print_embedding_ready_data(slides_data: List[Dict], pptx_path: str = None):
    """Print the embedding-ready data in a clear format."""
    if pptx_path:
        print(f"Embedding-ready data for: {pptx_path}")
        print("=" * 60)
    
    for slide in slides_data:
        print(f"Slide {slide['slide_index']}:")
        print(f"  Deck ID: {slide['deck_id']}")
        print(f"  Has text: {slide['has_text']}")
        print(f"  Has image: {slide['has_image']}")
        
        if slide['text']:
            print(f"  Text: {slide['text']}")
        
        if slide['captions']:
            print(f"  Captions: {slide['captions']}")
        
        print("-" * 40)


# Example usage for testing this branch
if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) < 2:
        print("Usage: python combine_slide_data.py path/to/file.pptx")
        print("Example: python combine_slide_data.py test_ppts/sample.pptx")
        sys.exit(1)

    pptx_path = sys.argv[1]

    try:
        # Step 1: Extract slide text
        slide_texts = extract_text_from_pptx(pptx_path)

        # Step 2: Generate image captions with BLIP-2
        slide_captions = run_image_captioning_pipeline_blip2(pptx_path)

        # Step 3: Combine into unified slide descriptions with optional summarization
        combined = combine_slide_text_and_captions(slide_texts, slide_captions, summarize_long=True)

        # Step 4: Print combined data for review
        print_combined_slide_data(combined, pptx_path)
        
        print("\n" + "="*80)
        print("EMBEDDING-READY FORMAT:")
        print("="*80)
        
        # Step 5: Create embedding-ready format
        deck_id = os.path.splitext(os.path.basename(pptx_path))[0]
        slides_data = combine_slide_data_for_embeddings(slide_texts, slide_captions, deck_id)
        print_embedding_ready_data(slides_data, pptx_path)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
