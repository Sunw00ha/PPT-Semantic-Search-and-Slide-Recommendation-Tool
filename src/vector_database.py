"""
Vector Database Management for PPTtool
Handles embedding storage, retrieval, and file management using ChromaDB
"""

import os
import json
import time
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from combine_data import generate_embedding_data_only


class PPTVectorDatabase:
    def __init__(self, db_path: str = "ppt_embeddings_db", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the vector database for PowerPoint slides.
        
        Args:
            db_path: Path to store the ChromaDB database
            model_name: Name of the sentence transformer model
        """
        self.db_path = db_path
        self.model_name = model_name
        self.embedding_model = SentenceTransformer(model_name)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="ppt_slides",
            metadata={"description": "PowerPoint slide embeddings"}
        )
        
        # File tracking — keeps a JSON record of which .pptx files have already been
        # processed and when they were last modified. This avoids re-running the expensive
        # pipeline (BLIP-2 captioning, summarization, embedding) on files that haven't changed.
        self.file_tracker_path = os.path.join(db_path, "file_tracker.json")
        self.file_tracker = self._load_file_tracker()
        
        print(f"Initialized PPT Vector Database with model: {model_name}")
        print(f"Database path: {db_path}")
        print(f"Current slides in database: {self.collection.count()}")
    
    def _load_file_tracker(self) -> Dict:
        """Load file tracking information."""
        if os.path.exists(self.file_tracker_path):
            with open(self.file_tracker_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_file_tracker(self):
        """Save file tracking information."""
        os.makedirs(os.path.dirname(self.file_tracker_path), exist_ok=True)
        with open(self.file_tracker_path, 'w') as f:
            json.dump(self.file_tracker, f, indent=2)
    
    def _get_file_info(self, file_path: str) -> Dict:
        """Get file modification time and size."""
        stat = os.stat(file_path)
        return {
            "last_modified": stat.st_mtime,
            "file_size": stat.st_size,
            "file_path": file_path
        }
    
    # If the file hasn't been modified since last time it was processed it will return False and skip the processing pipeline (BLIP-2 captioning, etc)
    def _needs_processing(self, file_path: str) -> bool:
        """Check if file needs to be processed (new or modified)."""
        if not os.path.exists(file_path):
            return False
        
        current_info = self._get_file_info(file_path)
        stored_info = self.file_tracker.get(file_path, {})
        
        # Process if file is new or modified
        if not stored_info or current_info["last_modified"] > stored_info.get("last_modified", 0):
            return True
        
        return False
    
    def _remove_file_embeddings(self, file_path: str):
        """Remove all embeddings for a specific file."""
        deck_id = os.path.splitext(os.path.basename(file_path))[0]
        
        # Get all documents for this file
        results = self.collection.get(
            where={"deck_id": deck_id}
        )
        
        if results['ids']:
            self.collection.delete(ids=results['ids'])
            print(f"Removed {len(results['ids'])} slides from {deck_id}")
    
    def process_file(self, file_path: str, force_reprocess: bool = False) -> Dict:
        """
        Process a PowerPoint file and add embeddings to the database.
        
        Args:
            file_path: Path to the PowerPoint file
            force_reprocess: If True, reprocess even if file hasn't changed
            
        Returns:
            Dictionary with processing results
        """
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        deck_id = os.path.splitext(os.path.basename(file_path))[0]
        
        # Check if file needs processing
        if not force_reprocess and not self._needs_processing(file_path):
            return {"message": f"File {deck_id} is up to date, skipping processing"}
        
        print(f"Processing file: {file_path}")
        
        try:
            # Remove old embeddings for this file
            self._remove_file_embeddings(file_path)
            
            # Generate slide data
            slides_data = generate_embedding_data_only(file_path)
            
            if not slides_data:
                return {"error": f"No slides found in {file_path}"}
            
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for slide_data in slides_data:
                # Create content string for embedding
                content_parts = []
                if slide_data['text']:
                    content_parts.append(slide_data['text'])
                if slide_data['captions']:
                    content_parts.extend(slide_data['captions'])
                
                content = " ".join(content_parts)
                
                if content:  # Only add slides with content
                    documents.append(content)
                    metadatas.append({
                        "deck_id": deck_id,
                        "slide_index": slide_data['slide_index'],
                        "has_text": slide_data['has_text'],
                        "has_image": slide_data['has_image'],
                        "file_path": file_path,
                        "text": slide_data['text'],
                        "captions": " | ".join(slide_data['captions']) if slide_data['captions'] else ""
                    })
                    ids.append(f"{deck_id}_slide_{slide_data['slide_index']}")
            
            # Add to ChromaDB
            if documents:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                # Update file tracker
                self.file_tracker[file_path] = self._get_file_info(file_path)
                self.file_tracker[file_path]["slide_count"] = len(documents)
                self._save_file_tracker()
                
                return {
                    "success": True,
                    "deck_id": deck_id,
                    "slides_processed": len(documents),
                    "total_slides": len(slides_data)
                }
            else:
                return {"error": f"No content found in slides of {file_path}"}
                
        except Exception as e:
            return {"error": f"Error processing {file_path}: {str(e)}"}
    
    def process_multiple_files(self, file_paths: List[str], force_reprocess: bool = False) -> Dict:
        """
        Process multiple PowerPoint files.
        
        Args:
            file_paths: List of file paths to process
            force_reprocess: If True, reprocess all files
            
        Returns:
            Dictionary with processing results for each file
        """
        results = {}
        
        for file_path in file_paths:
            print(f"\n{'='*60}")
            print(f"Processing: {file_path}")
            print('='*60)
            
            result = self.process_file(file_path, force_reprocess)
            results[file_path] = result
            
            if result.get("success"):
                print(f"[SUCCESS] Successfully processed {result['slides_processed']} slides")
            else:
                print(f"[ERROR] {result.get('error', 'Unknown error')}")
        
        return results
    
    def search_slides(self, query: str, n_results: int = 5, deck_filter: str = None) -> List[Dict]:
        """
        Search for similar slides based on a query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            deck_filter: Optional deck ID to filter results
            
        Returns:
            List of similar slides with metadata
        """
        where_clause = None
        if deck_filter:
            where_clause = {"deck_id": deck_filter}
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_clause
        )
        
        # Format results
        formatted_results = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            formatted_results.append({
                "rank": i + 1,
                "content": doc,
                "deck_id": metadata['deck_id'],
                "slide_index": metadata['slide_index'],
                "similarity_score": 1 - distance,  # Convert distance to similarity
                "has_text": metadata['has_text'],
                "has_image": metadata['has_image'],
                "file_path": metadata['file_path']
            })
        
        return formatted_results
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the database."""
        total_slides = self.collection.count()
        
        # Get unique decks
        results = self.collection.get()
        unique_decks = set(meta['deck_id'] for meta in results['metadatas'])
        
        return {
            "total_slides": total_slides,
            "unique_decks": len(unique_decks),
            "deck_ids": list(unique_decks),
            "tracked_files": len(self.file_tracker)
        }
    
    def list_processed_files(self) -> List[Dict]:
        """List all processed files with their information."""
        files = []
        for file_path, info in self.file_tracker.items():
            files.append({
                "file_path": file_path,
                "deck_id": os.path.splitext(os.path.basename(file_path))[0],
                "last_processed": time.ctime(info.get("last_modified", 0)),
                "slide_count": info.get("slide_count", 0),
                "file_size": info.get("file_size", 0)
            })
        return files
    
    def clear_database(self):
        """Clear all embeddings from the database."""
        # Delete the collection and recreate it
        self.client.delete_collection("ppt_slides")
        self.collection = self.client.create_collection(
            name="ppt_slides",
            metadata={"description": "PowerPoint slide embeddings"}
        )
        
        # Clear file tracker
        self.file_tracker = {}
        self._save_file_tracker()
        
        print("Database cleared successfully")
    
    def reset_system(self):
        """Reset the entire system with confirmation."""
        stats = self.get_database_stats()
        print("WARNING: This will delete ALL processed data!")
        print(f"   - Total slides: {stats['total_slides']}")
        print(f"   - Files: {stats['tracked_files']}")
        print()
        
        confirm = input("Are you sure you want to reset the entire system? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y']:
            self.clear_database()
            print("[SUCCESS] System reset successfully!")
            print("   All PowerPoint data and embeddings have been cleared.")
            print("   You can now start fresh by adding new files.")
        else:
            print("[CANCELLED] Reset cancelled.")
    
    def get_slide_recommendations(self, pptx_path: str, slide_number: int, num_recommendations: int = 5) -> List[Dict]:
        """
        Get recommendations for a specific slide from a PowerPoint file.
        Analyzes the slide on-the-fly and finds similar slides from the database.
        
        Args:
            pptx_path: Path to the PowerPoint file
            slide_number: Slide number to analyze (1-indexed)
            num_recommendations: Number of recommendations to return
            
        Returns:
            List of recommended slides with similarity scores
        """
        print(f"Analyzing slide {slide_number} from: {os.path.basename(pptx_path)}")
        
        try:
            # Get slide data for the specific slide
            slides_data = generate_embedding_data_only(pptx_path)
            
            # Find the specific slide
            target_slide = None
            for slide in slides_data:
                if slide['slide_index'] == slide_number:
                    target_slide = slide
                    break
            
            if not target_slide:
                print(f"ERROR: Slide {slide_number} not found in presentation")
                return []
            
            # Create embedding for the target slide
            content_parts = []
            if target_slide['text']:
                content_parts.append(target_slide['text'])
            if target_slide['captions']:
                content_parts.extend(target_slide['captions'])
            
            content = " ".join(content_parts)
            if not content:
                print("WARNING: Slide has no text or image content to analyze")
                return []
            
            # Generate embedding for the target slide
            target_embedding = self.embedding_model.encode(content, convert_to_tensor=False)
            
            # Search for similar slides in the database
            results = self.collection.query(
                query_embeddings=[target_embedding.tolist()],
                n_results=num_recommendations + 5,  # Get extra to filter out same presentation
                include=['metadatas', 'documents', 'distances']
            )
            
            # Filter out slides from the same presentation
            current_deck_id = os.path.splitext(os.path.basename(pptx_path))[0]
            recommendations = []
            
            for i, metadata in enumerate(results['metadatas'][0]):
                if metadata['deck_id'] != current_deck_id:  # Exclude same presentation
                    recommendations.append({
                        'deck_id': metadata['deck_id'],
                        'slide_index': metadata['slide_index'],
                        'similarity': 1 - results['distances'][0][i],  # Convert distance to similarity
                        'content': results['documents'][0][i][:200] + "..." if len(results['documents'][0][i]) > 200 else results['documents'][0][i],
                        'has_text': metadata.get('has_text', False),
                        'has_image': metadata.get('has_image', False),
                        'text': metadata.get('text', ''),
                        'captions': metadata.get('captions', '')
                    })
                    
                    if len(recommendations) >= num_recommendations:
                        break
            
            print(f"Found {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            print(f"ERROR: Failed to get recommendations: {e}")
            return []


def main():
    """Example usage of the PPTVectorDatabase."""
    # Initialize database
    db = PPTVectorDatabase()
    
    # Example files (update these paths)
    test_files = [
        "test_ppts/combine_data_test/DStest2.pptx",
        "test_ppts/image_testing/image_captioning_test2.pptx"
    ]
    
    # Process files
    print("Processing files...")
    results = db.process_multiple_files(test_files)
    
    # Show results
    print("\nProcessing Results:")
    for file_path, result in results.items():
        print(f"  {file_path}: {result}")
    
    # Search example
    print("\nSearching for 'data structure'...")
    search_results = db.search_slides("data structure", n_results=3)
    
    for result in search_results:
        print(f"  Rank {result['rank']}: {result['deck_id']} Slide {result['slide_index']}")
        print(f"    Similarity: {result['similarity_score']:.3f}")
        print(f"    Content: {result['content'][:100]}...")
        print()
    
    # Show database stats
    stats = db.get_database_stats()
    print(f"Database Stats: {stats}")


if __name__ == "__main__":
    main()
