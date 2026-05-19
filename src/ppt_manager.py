"""
PPT Manager - User interface for managing PowerPoint files and searching slides
"""

import os
import sys
from pathlib import Path
from typing import List, Dict
from vector_database import PPTVectorDatabase


class PPTManager:
    def __init__(self, db_path: str = "ppt_embeddings_db"):
        """Initialize the PPT Manager."""
        self.db = PPTVectorDatabase(db_path)
        print("PPT Manager initialized!")
        print(f"Database contains {self.db.get_database_stats()['total_slides']} slides")
    
    def add_files(self, file_paths: List[str], force_reprocess: bool = False):
        """
        Add PowerPoint files to the database.
        
        Args:
            file_paths: List of file paths to add
            force_reprocess: If True, reprocess files even if they haven't changed
        """
        print(f"\n{'='*60}")
        print("ADDING FILES TO DATABASE")
        print('='*60)
        
        # Validate files exist
        valid_files = []
        for file_path in file_paths:
            if os.path.exists(file_path) and file_path.lower().endswith('.pptx'):
                valid_files.append(file_path)
            else:
                print(f"[ERROR] Skipping invalid file: {file_path}")
        
        if not valid_files:
            print("No valid PowerPoint files found!")
            return
        
        # Process files
        results = self.db.process_multiple_files(valid_files, force_reprocess)
        
        # Show summary
        print(f"\n{'='*60}")
        print("PROCESSING SUMMARY")
        print('='*60)
        
        total_slides = 0
        successful_files = 0
        
        for file_path, result in results.items():
            if result.get("success"):
                successful_files += 1
                total_slides += result.get("slides_processed", 0)
                print(f"[SUCCESS] {os.path.basename(file_path)}: {result['slides_processed']} slides")
            else:
                print(f"[ERROR] {os.path.basename(file_path)}: {result.get('error', 'Unknown error')}")
        
        print(f"\nSuccessfully processed {successful_files} files with {total_slides} total slides")
        print(f"Database now contains {self.db.get_database_stats()['total_slides']} slides")
    
    def search_slides(self, query: str, n_results: int = 5, deck_filter: str = None):
        """
        Search for slides based on a query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            deck_filter: Optional deck ID to filter results
        """
        print(f"\n{'='*60}")
        print(f"SEARCHING FOR: '{query}'")
        if deck_filter:
            print(f"Filtering by deck: {deck_filter}")
        print('='*60)
        
        results = self.db.search_slides(query, n_results, deck_filter)
        
        if not results:
            print("No results found.")
            return
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['deck_id']} - Slide {result['slide_index']}")
            print(f"   Similarity: {result['similarity_score']:.3f}")
            print(f"   Content: {result['content'][:200]}...")
            if result['has_text'] and result['has_image']:
                print("   [TEXT+IMAGE] Has text and images")
            elif result['has_text']:
                print("   [TEXT] Text only")
            elif result['has_image']:
                print("   [IMAGE] Images only")
    
    def get_recommendations(self, pptx_path: str, slide_number: int, num_recommendations: int = 5):
        """
        Get recommendations for a specific slide from a PowerPoint file.
        
        Args:
            pptx_path: Path to the PowerPoint file
            slide_number: Slide number to analyze (1-indexed)
            num_recommendations: Number of recommendations to return
        """
        print(f"\n{'='*60}")
        print(f"GETTING RECOMMENDATIONS FOR SLIDE {slide_number}")
        print(f"From: {os.path.basename(pptx_path)}")
        print('='*60)
        
        # Validate file exists
        if not os.path.exists(pptx_path):
            print(f"[ERROR] File not found: {pptx_path}")
            return
        
        if not pptx_path.lower().endswith('.pptx'):
            print(f"[ERROR] File is not a PowerPoint file: {pptx_path}")
            return
        
        # Get recommendations
        recommendations = self.db.get_slide_recommendations(pptx_path, slide_number, num_recommendations)
        
        if not recommendations:
            print("No recommendations found.")
            return
        
        print(f"\nFound {len(recommendations)} recommendations:")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['deck_id']} - Slide {rec['slide_index']}")
            print(f"   Similarity: {rec['similarity']:.3f}")
            print(f"   Content: {rec['content']}")
            if rec['has_text'] and rec['has_image']:
                print("   [TEXT+IMAGE] Has text and images")
            elif rec['has_text']:
                print("   [TEXT] Text only")
            elif rec['has_image']:
                print("   [IMAGE] Images only")
    
    def list_files(self):
        """List all processed files."""
        print(f"\n{'='*60}")
        print("PROCESSED FILES")
        print('='*60)
        
        files = self.db.list_processed_files()
        
        if not files:
            print("No files processed yet.")
            return
        
        for file_info in files:
            print(f"[FILE] {file_info['deck_id']}")
            print(f"   File: {file_info['file_path']}")
            print(f"   Slides: {file_info['slide_count']}")
            print(f"   Last processed: {file_info['last_processed']}")
            print()
    
    def show_stats(self):
        """Show database statistics."""
        stats = self.db.get_database_stats()
        
        print(f"\n{'='*60}")
        print("DATABASE STATISTICS")
        print('='*60)
        print(f"Total slides: {stats['total_slides']}")
        print(f"Unique decks: {stats['unique_decks']}")
        print(f"Tracked files: {stats['tracked_files']}")
        
        if stats['deck_ids']:
            print(f"\nDeck IDs:")
            for deck_id in stats['deck_ids']:
                print(f"  - {deck_id}")
    
    def refresh_files(self, file_paths: List[str] = None):
        """
        Refresh files (reprocess even if unchanged).
        
        Args:
            file_paths: Specific files to refresh, or None to refresh all
        """
        if file_paths is None:
            # Refresh all files
            file_paths = list(self.db.file_tracker.keys())
        
        if not file_paths:
            print("No files to refresh.")
            return
        
        print(f"Refreshing {len(file_paths)} files...")
        self.add_files(file_paths, force_reprocess=True)
    
    def clear_database(self):
        """Clear all data from the database."""
        confirm = input("Are you sure you want to clear the entire database? (yes/no): ")
        if confirm.lower() == 'yes':
            self.db.clear_database()
            print("Database cleared successfully!")
        else:
            print("Operation cancelled.")
    
    def reset_system(self):
        """Reset the entire system with confirmation."""
        self.db.reset_system()


def interactive_mode():
    """Run the PPT Manager in interactive mode."""
    manager = PPTManager()
    
    print("\n" + "="*60)
    print("PPT MANAGER - Interactive Mode")
    print("="*60)
    print("Commands:")
    print("  add <file1> <file2> ...  - Add PowerPoint files")
    print("  search <query>           - Search for slides")
    print("  recommend <file> <slide> - Get recommendations for a specific slide")
    print("  list                     - List processed files")
    print("  stats                    - Show database statistics")
    print("  refresh [files...]       - Refresh files (reprocess)")
    print("  clear                    - Clear database")
    print("  reset                    - Reset system (with confirmation)")
    print("  quit                     - Exit")
    print("="*60)
    
    while True:
        try:
            command = input("\nEnter command: ").strip().split()
            
            if not command:
                continue
            
            cmd = command[0].lower()
            
            if cmd == 'quit' or cmd == 'exit':
                print("Goodbye!")
                break
            
            elif cmd == 'add':
                if len(command) < 2:
                    print("Usage: add <file1> <file2> ...")
                    continue
                file_paths = command[1:]
                manager.add_files(file_paths)
            
            elif cmd == 'search':
                if len(command) < 2:
                    print("Usage: search <query>")
                    continue
                query = " ".join(command[1:])
                manager.search_slides(query)
            
            elif cmd == 'recommend':
                if len(command) < 3:
                    print("Usage: recommend <file_path> <slide_number>")
                    print("Example: recommend test_ppts/sample.pptx 3")
                    continue
                try:
                    file_path = command[1]
                    slide_number = int(command[2])
                    manager.get_recommendations(file_path, slide_number)
                except ValueError:
                    print("Error: Slide number must be an integer")
                    continue
            
            elif cmd == 'list':
                manager.list_files()
            
            elif cmd == 'stats':
                manager.show_stats()
            
            elif cmd == 'refresh':
                file_paths = command[1:] if len(command) > 1 else None
                manager.refresh_files(file_paths)
            
            elif cmd == 'clear':
                manager.clear_database()
            
            elif cmd == 'reset':
                manager.reset_system()
            
            else:
                print(f"Unknown command: {cmd}")
                print("Type 'quit' to exit or use one of the commands above.")
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("PPT Manager - PowerPoint Slide Search System")
        print("\nUsage:")
        print("  python ppt_manager.py interactive                    - Run in interactive mode")
        print("  python ppt_manager.py add <file1> <file2> ...       - Add files")
        print("  python ppt_manager.py search <query>                - Search slides")
        print("  python ppt_manager.py recommend <file> <slide>      - Get recommendations")
        print("  python ppt_manager.py list                          - List files")
        print("  python ppt_manager.py stats                         - Show stats")
        print("  python ppt_manager.py clear                         - Clear database")
        print("  python ppt_manager.py reset                         - Reset system")
        return
    
    manager = PPTManager()
    command = sys.argv[1].lower()
    
    if command == 'interactive':
        interactive_mode()
    
    elif command == 'add':
        if len(sys.argv) < 3:
            print("Usage: python ppt_manager.py add <file1> <file2> ...")
            return
        file_paths = sys.argv[2:]
        manager.add_files(file_paths)
    
    elif command == 'search':
        if len(sys.argv) < 3:
            print("Usage: python ppt_manager.py search <query>")
            return
        query = " ".join(sys.argv[2:])
        manager.search_slides(query)
    
    elif command == 'recommend':
        if len(sys.argv) < 4:
            print("Usage: python ppt_manager.py recommend <file_path> <slide_number>")
            print("Example: python ppt_manager.py recommend test_ppts/sample.pptx 3")
            return
        try:
            file_path = sys.argv[2]
            slide_number = int(sys.argv[3])
            manager.get_recommendations(file_path, slide_number)
        except ValueError:
            print("Error: Slide number must be an integer")
            return
    
    elif command == 'list':
        manager.list_files()
    
    elif command == 'stats':
        manager.show_stats()
    
    elif command == 'clear':
        manager.clear_database()
    
    elif command == 'reset':
        manager.reset_system()
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
