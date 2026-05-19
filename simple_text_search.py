#!/usr/bin/env python3
"""
Simple PowerPoint Text Search System
A working version that processes PowerPoint files and provides text-based search functionality
without requiring heavy ML dependencies.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple
import re

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from extract_text import extract_text_from_pptx


class SimpleTextSearch:
    def __init__(self, data_file: str = "ppt_text_data.json"):
        """Initialize the simple text search system."""
        self.data_file = data_file
        self.slides_data = self._load_data()
        print(f"Simple Text Search initialized with {len(self.slides_data)} slides")
    
    def _load_data(self) -> List[Dict]:
        """Load slide data from JSON file."""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_data(self):
        """Save slide data to JSON file."""
        with open(self.data_file, 'w') as f:
            json.dump(self.slides_data, f, indent=2)
    
    def add_file(self, file_path: str) -> Dict:
        """Add a PowerPoint file to the search index."""
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        deck_id = os.path.splitext(os.path.basename(file_path))[0]
        print(f"Processing file: {file_path}")
        
        try:
            # Extract text only
            slide_texts = extract_text_from_pptx(file_path)
            
            # Process slides
            file_slides = []
            for slide_num, text in slide_texts.items():
                # Clean up placeholders
                if text == "There is no text on this slide":
                    text = ""
                
                if text.strip():  # Only add slides with text
                    slide_data = {
                        "deck_id": deck_id,
                        "slide_index": slide_num,
                        "text": text.strip(),
                        "content": text.strip(),
                        "has_text": True,
                        "has_image": False,  # We're not processing images in this version
                        "file_path": file_path
                    }
                    file_slides.append(slide_data)
            
            # Add to existing data
            self.slides_data.extend(file_slides)
            self._save_data()
            
            return {
                "success": True,
                "deck_id": deck_id,
                "slides_processed": len(file_slides),
                "total_slides": len(slide_texts)
            }
            
        except Exception as e:
            return {"error": f"Error processing {file_path}: {str(e)}"}
    
    def search_slides(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for slides using simple text matching."""
        if not self.slides_data:
            return []
        
        query_lower = query.lower()
        results = []
        
        for slide in self.slides_data:
            content = slide.get('content', '').lower()
            
            # Simple scoring based on word matches
            score = 0
            query_words = query_lower.split()
            
            for word in query_words:
                if word in content:
                    score += 1
                    # Bonus for exact phrase matches
                    if query_lower in content:
                        score += 2
            
            if score > 0:
                results.append({
                    "slide": slide,
                    "score": score,
                    "content": slide['content']
                })
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Format results
        formatted_results = []
        for i, result in enumerate(results[:n_results], 1):
            slide = result['slide']
            formatted_results.append({
                "rank": i,
                "deck_id": slide['deck_id'],
                "slide_index": slide['slide_index'],
                "score": result['score'],
                "content": result['content'][:200] + "..." if len(result['content']) > 200 else result['content'],
                "has_text": slide['has_text'],
                "has_image": slide['has_image'],
                "file_path": slide['file_path']
            })
        
        return formatted_results
    
    def list_files(self) -> List[Dict]:
        """List all processed files."""
        files = {}
        for slide in self.slides_data:
            deck_id = slide['deck_id']
            file_path = slide['file_path']
            
            if deck_id not in files:
                files[deck_id] = {
                    "deck_id": deck_id,
                    "file_path": file_path,
                    "slide_count": 0
                }
            files[deck_id]["slide_count"] += 1
        
        return list(files.values())
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        return {
            "total_slides": len(self.slides_data),
            "unique_decks": len(set(slide['deck_id'] for slide in self.slides_data)),
            "files": self.list_files()
        }
    
    def clear_data(self) -> Dict:
        """Clear all data and reset the system."""
        try:
            # Clear in-memory data
            self.slides_data = []
            
            # Remove data file if it exists
            if os.path.exists(self.data_file):
                os.remove(self.data_file)
                print(f"✅ Removed data file: {self.data_file}")
            
            # Save empty data
            self._save_data()
            
            return {
                "success": True,
                "message": "All data cleared successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error clearing data: {str(e)}"
            }
    
    def reset_system(self) -> Dict:
        """Reset the system with confirmation."""
        print("    WARNING: This will delete ALL processed data!")
        print(f"   - Total slides: {len(self.slides_data)}")
        print(f"   - Files: {len(self.list_files())}")
        print()
        
        confirm = input("Are you sure you want to clear all data? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y']:
            result = self.clear_data()
            if result['success']:
                print("System reset successfully!")
                print("   All PowerPoint data has been cleared.")
                print("   You can now start fresh by adding new files.")
            else:
                print(f"Error: {result['error']}")
            return result
        else:
            print("Reset cancelled.")
            return {"success": False, "message": "Reset cancelled by user"}


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Simple PPT Text Search System")
        print("\nUsage:")
        print("  python simple_text_search.py add <file1> <file2> ...    - Add PowerPoint files")
        print("  python simple_text_search.py search <query>             - Search slides")
        print("  python simple_text_search.py list                       - List files")
        print("  python simple_text_search.py stats                      - Show stats")
        print("  python simple_text_search.py clear                      - Clear all data")
        print("  python simple_text_search.py reset                      - Reset system (with confirmation)")
        return
    
    search = SimpleTextSearch()
    command = sys.argv[1].lower()
    
    if command == 'add':
        if len(sys.argv) < 3:
            print("Usage: python simple_text_search.py add <file1> <file2> ...")
            return
        
        file_paths = sys.argv[2:]
        print(f"Adding {len(file_paths)} files...")
        
        for file_path in file_paths:
            result = search.add_file(file_path)
            if result.get("success"):
                print(f"{os.path.basename(file_path)}: {result['slides_processed']} slides")
            else:
                print(f"{os.path.basename(file_path)}: {result.get('error', 'Unknown error')}")
    
    elif command == 'search':
        if len(sys.argv) < 3:
            print("Usage: python simple_text_search.py search <query>")
            return
        
        query = " ".join(sys.argv[2:])
        print(f"Searching for: '{query}'")
        
        results = search.search_slides(query)
        
        if not results:
            print("No results found.")
            return
        
        for result in results:
            print(f"\n{result['rank']}. {result['deck_id']} - Slide {result['slide_index']}")
            print(f"   Score: {result['score']}")
            print(f"   Content: {result['content']}")
            if result['has_text'] and result['has_image']:
                print("Has text and images")
            elif result['has_text']:
                print("Text only")
            elif result['has_image']:
                print("Images only")
    
    elif command == 'list':
        files = search.list_files()
        if not files:
            print("No files processed yet.")
            return
        
        for file_info in files:
            print(f"{file_info['deck_id']}")
            print(f"   File: {file_info['file_path']}")
            print(f"   Slides: {file_info['slide_count']}")
            print()
    
    elif command == 'stats':
        stats = search.get_stats()
        print(f"Total slides: {stats['total_slides']}")
        print(f"Unique decks: {stats['unique_decks']}")
        
        if stats['files']:
            print("\nFiles:")
            for file_info in stats['files']:
                print(f"  - {file_info['deck_id']}: {file_info['slide_count']} slides")
    
    elif command == 'clear':
        print("Clearing all data...")
        result = search.clear_data()
        if result['success']:
            print("All data cleared successfully!")
        else:
            print(f"Error: {result['error']}")
    
    elif command == 'reset':
        search.reset_system()
    
    else:
        print(f"Unknown command: {command}")
        print("Use 'python simple_text_search.py' to see available commands.")


if __name__ == "__main__":
    main()
