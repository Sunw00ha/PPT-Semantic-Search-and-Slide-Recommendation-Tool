from sentence_transformers import SentenceTransformer
from combine_data import generate_embedding_data_only
from typing import Dict, List, Tuple
import numpy as np
import json
import os


class SlideEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the slide embedder with a sentence transformer model.
        
        Args:
            model_name: Name of the pre-trained sentence transformer model
        """
        self.model = SentenceTransformer(model_name)
        print(f"Loaded embedding model: {model_name}")
    
    def create_slide_embedding(self, slide_data: Dict) -> Dict:
        """
        Create an embedding for a single slide.
        
        Args:
            slide_data: Dictionary containing slide information
            
        Returns:
            Dictionary with slide data and embedding
        """
        # Combine text and captions into a single string for embedding
        content_parts = []
        
        if slide_data['text']:
            content_parts.append(slide_data['text'])
        
        if slide_data['captions']:
            content_parts.extend(slide_data['captions'])
        
        # Create the content string for embedding
        content = " ".join(content_parts)
        
        # Generate embedding
        if content:
            embedding = self.model.encode(content, convert_to_tensor=False)
            embedding_list = embedding.tolist()  # Convert numpy array to list for JSON serialization
        else:
            embedding_list = []
        
        # Return slide data with embedding
        return {
            **slide_data,
            'content': content,
            'embedding': embedding_list,
            'embedding_dim': len(embedding_list) if embedding_list else 0
        }
    
    def embed_presentation(self, pptx_path: str) -> List[Dict]:
        """
        Generate embeddings for all slides in a presentation.
        
        Args:
            pptx_path: Path to the PowerPoint file
            
        Returns:
            List of dictionaries with slide data and embeddings
        """
        # Get clean slide data
        slides_data = generate_embedding_data_only(pptx_path)
        
        # Generate embeddings for each slide
        embedded_slides = []
        for slide_data in slides_data:
            embedded_slide = self.create_slide_embedding(slide_data)
            embedded_slides.append(embedded_slide)
        
        return embedded_slides


def save_embeddings(embedded_slides: List[Dict], output_path: str):
    """
    Save embeddings to a JSON file.
    
    Args:
        embedded_slides: List of slides with embeddings
        output_path: Path to save the JSON file
    """
    with open(output_path, 'w') as f:
        json.dump(embedded_slides, f, indent=2)
    
    print(f"Saved embeddings to: {output_path}")


def print_embedding_summary(embedded_slides: List[Dict]):
    """Print a summary of the generated embeddings."""
    if not embedded_slides:
        print("No slides to embed.")
        return
    
    total_slides = len(embedded_slides)
    slides_with_embeddings = sum(1 for slide in embedded_slides if slide['embedding'])
    embedding_dim = embedded_slides[0]['embedding_dim'] if embedded_slides else 0
    
    print(f"\nEmbedding Summary:")
    print(f"  Total slides: {total_slides}")
    print(f"  Slides with embeddings: {slides_with_embeddings}")
    print(f"  Embedding dimension: {embedding_dim}")
    
    # Show sample embeddings
    print(f"\nSample slides:")
    for i, slide in enumerate(embedded_slides[:3], 1):
        print(f"  Slide {slide['slide_index']}: {slide['content'][:100]}...")
        print(f"    Has embedding: {bool(slide['embedding'])}")


def embed_multiple_presentations(pptx_paths: List[str], embedder: SlideEmbedder) -> List[Dict]:
    """
    Generate embeddings for multiple PowerPoint presentations.
    
    Args:
        pptx_paths: List of paths to PowerPoint files
        embedder: Initialized SlideEmbedder instance
        
    Returns:
        List of dictionaries with slide data and embeddings from all presentations
    """
    all_embedded_slides = []
    
    for pptx_path in pptx_paths:
        print(f"Processing: {pptx_path}")
        try:
            # Get clean slide data
            slides_data = generate_embedding_data_only(pptx_path)
            
            # Generate embeddings for each slide
            for slide_data in slides_data:
                embedded_slide = embedder.create_slide_embedding(slide_data)
                all_embedded_slides.append(embedded_slide)
                
        except Exception as e:
            print(f"Error processing {pptx_path}: {e}")
            continue
    
    return all_embedded_slides


# Example usage for testing
if __name__ == "__main__":
    # Test with multiple presentations
    pptx_paths = [
        "test_ppts/combine_data_test/DStest2.pptx",
        "test_ppts/image_testing/image_captioning_test2.pptx"
    ]
    
    print("Testing multi-file embedding...")
    embedder = SlideEmbedder()
    
    # Test single file first
    print("\n" + "="*60)
    print("TESTING SINGLE FILE:")
    print("="*60)
    embedded_slides_single = embedder.embed_presentation(pptx_paths[0])
    print_embedding_summary(embedded_slides_single)
    
    # Test multiple files
    print("\n" + "="*60)
    print("TESTING MULTIPLE FILES:")
    print("="*60)
    all_embedded_slides = embed_multiple_presentations(pptx_paths, embedder)
    
    # Save all embeddings
    save_embeddings(all_embedded_slides, "embeddings.json")
    
    # Print summary of all slides
    print_embedding_summary(all_embedded_slides)
