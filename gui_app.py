#!/usr/bin/env python3
"""
PPT Recommendation System - Desktop Application
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import shutil
import subprocess

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import after adding to path
from vector_database import PPTVectorDatabase
from simple_text_search import SimpleTextSearch

class PPTRecommendationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PPT Recommendation/Search System")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize the systems
        self.vector_db = PPTVectorDatabase()
        self.simple_search = SimpleTextSearch()
        
        # Data storage
        self.embedded_files = []
        self.available_files = []
        self.current_recommendations = []
        self.selected_recommendation = None
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # File Management Tab
        self.file_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.file_frame, text="File Management")
        self.setup_file_management()
        
        # Recommendations Tab
        self.rec_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.rec_frame, text="Recommendations")
        self.setup_recommendations()
        
        # Search Tab
        self.search_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_frame, text="Search")
        self.setup_search()
        
        # Statistics Tab
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="Statistics")
        self.setup_statistics()
    
    def setup_file_management(self):
        """Set up the file management tab."""
        # Title
        title_label = ttk.Label(self.file_frame, text="📁 Embedded Files", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # File list frame
        list_frame = ttk.LabelFrame(self.file_frame, text="Current Files", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for files
        columns = ('Name', 'Slides', 'Status', 'Last Modified')
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.file_tree.heading(col, text=col)
            self.file_tree.column(col, width=150)
        
        # Scrollbar for file tree
        file_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=file_scrollbar.set)
        
        self.file_tree.pack(side='left', fill='both', expand=True)
        file_scrollbar.pack(side='right', fill='y')
        
        # Button frame
        button_frame = ttk.Frame(self.file_frame)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        # Add files button
        add_btn = ttk.Button(button_frame, text="➕ Add Files", command=self.add_files)
        add_btn.pack(side='left', padx=5)
        
        # Refresh button
        refresh_btn = ttk.Button(button_frame, text="🔄 Refresh All", command=self.refresh_all_files)
        refresh_btn.pack(side='left', padx=5)
        
        
        # Clear all button
        clear_btn = ttk.Button(button_frame, text="🧹 Clear All", command=self.clear_all_files)
        clear_btn.pack(side='left', padx=5)
        
        # Refresh status button
        refresh_status_btn = ttk.Button(button_frame, text="🔄 Refresh Status", command=self.load_embedded_files)
        refresh_status_btn.pack(side='left', padx=5)
        
        # Status label
        self.file_status_label = ttk.Label(self.file_frame, text="Ready", foreground='green')
        self.file_status_label.pack(pady=5)
    
    def setup_recommendations(self):
        """Set up the recommendations tab."""
        # Title
        title_label = ttk.Label(self.rec_frame, text="Get Recommendations", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Input frame
        input_frame = ttk.LabelFrame(self.rec_frame, text="Select File and Slide", padding=10)
        input_frame.pack(fill='x', padx=10, pady=5)
        
        # File selection
        ttk.Label(input_frame, text="PowerPoint File:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.rec_file_var = tk.StringVar()
        self.rec_file_combo = ttk.Combobox(input_frame, textvariable=self.rec_file_var, width=50, state='readonly')
        self.rec_file_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Browse button
        browse_btn = ttk.Button(input_frame, text="📁 Browse", command=self.browse_file)
        browse_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Slide number
        ttk.Label(input_frame, text="Slide Number:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.slide_number_var = tk.StringVar()
        slide_entry = ttk.Entry(input_frame, textvariable=self.slide_number_var, width=10)
        slide_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        # Get recommendations button
        get_rec_btn = ttk.Button(input_frame, text="Get Recommendations", command=self.get_recommendations)
        get_rec_btn.grid(row=1, column=2, padx=5, pady=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(self.rec_frame, text="Recommendations", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Results text area
        self.results_text = scrolledtext.ScrolledText(results_frame, height=15, width=80)
        self.results_text.pack(fill='both', expand=True)
        
        
        # Selection frame
        selection_frame = ttk.LabelFrame(self.rec_frame, text="Select Recommendation to Download", padding=10)
        selection_frame.pack(fill='x', padx=10, pady=5)
        
        # Selection dropdown
        selection_row = ttk.Frame(selection_frame)
        selection_row.pack(fill='x', pady=5)
        
        ttk.Label(selection_row, text="Choose recommendation:").pack(side='left', padx=(0, 10))
        
        self.recommendation_var = tk.StringVar()
        self.recommendation_combo = ttk.Combobox(selection_row, textvariable=self.recommendation_var, 
                                               state="readonly", width=30)
        self.recommendation_combo.pack(side='left', padx=(0, 10))
        
        # Individual slide actions frame
        slide_actions_frame = ttk.LabelFrame(self.rec_frame, text="Slide Actions", padding=10)
        slide_actions_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(slide_actions_frame, text="With the recommendation selected above:").pack(anchor='w')
        
        action_buttons_frame = ttk.Frame(slide_actions_frame)
        action_buttons_frame.pack(fill='x', pady=5)
        
        download_btn = ttk.Button(action_buttons_frame, text="Download Slide", command=self.download_selected_slide)
        download_btn.pack(side='left', padx=5)
        
        # Status label
        self.rec_status_label = ttk.Label(self.rec_frame, text="Ready", foreground='green')
        self.rec_status_label.pack(pady=5)
    
    def setup_search(self):
        """Set up the search tab."""
        # Title
        title_label = ttk.Label(self.search_frame, text="🔎 Search Slides", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Search frame
        search_frame = ttk.LabelFrame(self.search_frame, text="Search Query", padding=10)
        search_frame.pack(fill='x', padx=10, pady=5)
        
        # Search input
        ttk.Label(search_frame, text="Search for:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        search_entry.grid(row=0, column=1, padx=5, pady=5)
        search_entry.bind('<Return>', lambda e: self.search_slides())
        
        # Number of results
        ttk.Label(search_frame, text="Results:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.search_num_var = tk.StringVar(value="5")
        num_entry = ttk.Entry(search_frame, textvariable=self.search_num_var, width=5)
        num_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Search button
        search_btn = ttk.Button(search_frame, text="🔍 Search", command=self.search_slides)
        search_btn.grid(row=0, column=4, padx=5, pady=5)
        
        # Results frame
        search_results_frame = ttk.LabelFrame(self.search_frame, text="Search Results", padding=10)
        search_results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Search results text area
        self.search_results_text = scrolledtext.ScrolledText(search_results_frame, height=15, width=80)
        self.search_results_text.pack(fill='both', expand=True)
        
        # Status label
        self.search_status_label = ttk.Label(self.search_frame, text="Ready", foreground='green')
        self.search_status_label.pack(pady=5)
    
    def setup_statistics(self):
        """Set up the statistics tab."""
        # Title
        title_label = ttk.Label(self.stats_frame, text="System Statistics", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Stats frame
        stats_frame = ttk.LabelFrame(self.stats_frame, text="Database Information", padding=10)
        stats_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Stats text area
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=15, width=80)
        self.stats_text.pack(fill='both', expand=True)
        
        # Refresh button
        refresh_stats_btn = ttk.Button(self.stats_frame, text="🔄 Refresh Statistics", command=self.refresh_statistics)
        refresh_stats_btn.pack(pady=10)
    
    def load_data(self):
        """Load initial data."""
        self.load_embedded_files()
        self.load_available_files()
        self.refresh_statistics()
    
    def load_embedded_files(self):
        """Load embedded files into the treeview."""
        try:
            files = self.vector_db.list_processed_files()
            self.embedded_files = files
            
            # Clear existing items
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)
            
            # Add files to treeview
            for file_info in files:
                # Determine status
                status = self.get_file_status(file_info)
                
                self.file_tree.insert('', 'end', values=(
                    os.path.basename(file_info['file_path']),
                    file_info.get('slide_count', file_info.get('slides_processed', 0)),
                    status,
                    file_info['last_processed']
                ))
            
            self.file_status_label.config(text=f"Loaded {len(files)} files", foreground='green')
            
        except Exception as e:
            self.file_status_label.config(text=f"Error loading files: {e}", foreground='red')
    
    def get_file_status(self, file_info):
        """Get the status of a file (Processed, Modified, Error, etc.)."""
        file_path = file_info['file_path']
        
        if not os.path.exists(file_path):
            return "File Missing"
        
        try:
            # Check if file needs processing
            needs_processing = self.vector_db._needs_processing(file_path)
            if needs_processing:
                return "Modified!"
            else:
                return "Processed"
        except Exception:
            return "Unknown?"
    
    def load_available_files(self):
        """Load available files for recommendations."""
        try:
            available_files = []
            for pattern in ['test_ppts/**/*.pptx', '**/*.pptx']:
                for file_path in Path('.').glob(pattern):
                    if file_path.exists():
                        available_files.append(str(file_path))
            
            self.available_files = available_files
            self.rec_file_combo['values'] = [os.path.basename(f) for f in available_files]
            
        except Exception as e:
            print(f"Error loading available files: {e}")
    
    def add_files(self):
        """Add files to the system."""
        file_paths = filedialog.askopenfilenames(
            title="Select PowerPoint Files",
            filetypes=[("PowerPoint files", "*.pptx"), ("All files", "*.*")]
        )
        
        if not file_paths:
            return
        
        # Normalize paths and remove duplicates
        normalized_paths = []
        seen_paths = set()
        
        for file_path in file_paths:
            # Convert to absolute path to handle relative paths consistently
            abs_path = os.path.abspath(file_path)
            if abs_path not in seen_paths:
                normalized_paths.append(abs_path)
                seen_paths.add(abs_path)
            else:
                print(f"Skipping duplicate file: {os.path.basename(file_path)}")
        
        if not normalized_paths:
            self.file_status_label.config(text="No new files to add (all were duplicates)", foreground='orange')
            return
        
        # Check for files already in the system
        existing_files = [f['file_path'] for f in self.embedded_files]
        new_files = []
        already_processed = []
        
        for file_path in normalized_paths:
            if file_path in existing_files:
                already_processed.append(os.path.basename(file_path))
            else:
                new_files.append(file_path)
        
        if not new_files:
            self.file_status_label.config(
                text=f"All files already processed: {', '.join(already_processed)}", 
                foreground='orange'
            )
            return
        
        if already_processed:
            self.file_status_label.config(
                text=f"Processing {len(new_files)} new files, {len(already_processed)} already processed...", 
                foreground='blue'
            )
        else:
            self.file_status_label.config(text="Processing files...", foreground='blue')
        
        self.root.update()
        
        try:
            results = self.vector_db.process_multiple_files(new_files)
            
            successful = 0
            total_slides = 0
            for file_path, result in results.items():
                if 'error' not in result:
                    successful += 1
                    total_slides += result.get('slides_processed', 0)
            
            status_msg = f"Added {successful} files with {total_slides} slides"
            if already_processed:
                status_msg += f" ({len(already_processed)} already processed)"
            
            self.file_status_label.config(text=status_msg, foreground='green')
            
            # Refresh the file list
            self.load_embedded_files()
            
        except Exception as e:
            self.file_status_label.config(text=f"Error adding files: {e}", foreground='red')
    
    def refresh_all_files(self):
        """Refresh all embedded files."""
        if not self.embedded_files:
            messagebox.showwarning("No Files", "No files to refresh.")
            return
        
        if messagebox.askyesno("Refresh Files", "Refresh all files? This will reprocess all embedded files."):
            self.file_status_label.config(text="Refreshing files...", foreground='blue')
            self.root.update()
            
            try:
                file_paths = [file_info['file_path'] for file_info in self.embedded_files]
                results = self.vector_db.process_multiple_files(file_paths, force_reprocess=True)
                
                successful = sum(1 for result in results.values() if 'error' not in result)
                self.file_status_label.config(
                    text=f"Refreshed {successful} files", 
                    foreground='green'
                )
                
                # Refresh the file list
                self.load_embedded_files()
                
            except Exception as e:
                self.file_status_label.config(text=f"Error refreshing files: {e}", foreground='red')
    
    
    def clear_all_files(self):
        """Clear all embedded files."""
        if not self.embedded_files:
            messagebox.showwarning("No Files", "No files to clear.")
            return
        
        if messagebox.askyesno("Clear All Files", "Clear all files? This will remove ALL embeddings permanently."):
            try:
                self.vector_db.clear_database()
                self.file_status_label.config(text="All files cleared", foreground='green')
                self.load_embedded_files()
                
            except Exception as e:
                self.file_status_label.config(text=f"Error clearing files: {e}", foreground='red')
    
    def browse_file(self):
        """Browse for a file to analyze."""
        file_path = filedialog.askopenfilename(
            title="Select PowerPoint File to Analyze",
            filetypes=[("PowerPoint files", "*.pptx"), ("All files", "*.*")]
        )
        
        if file_path:
            self.rec_file_var.set(os.path.basename(file_path))
            # Store the full path for later use
            self.selected_file_path = file_path
    
    def get_recommendations(self):
        """Get recommendations for the selected slide."""
        file_name = self.rec_file_var.get()
        slide_number = self.slide_number_var.get()
        
        if not file_name or not slide_number:
            messagebox.showwarning("Missing Information", "Please select a file and enter a slide number.")
            return
        
        try:
            slide_number = int(slide_number)
        except ValueError:
            messagebox.showerror("Invalid Input", "Slide number must be a number.")
            return
        
        # Get the full file path
        file_path = None
        if hasattr(self, 'selected_file_path'):
            file_path = self.selected_file_path
        else:
            # Find the file in available files
            for f in self.available_files:
                if os.path.basename(f) == file_name:
                    file_path = f
                    break
        
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("File Not Found", f"File {file_name} not found.")
            return
        
        self.rec_status_label.config(text="Analyzing slide and finding recommendations...", foreground='blue')
        self.root.update()
        
        try:
            recommendations = self.vector_db.get_slide_recommendations(file_path, slide_number)
            self.current_recommendations = recommendations
            
            # Display results
            self.results_text.delete(1.0, tk.END)
            
            # Reset selection
            self.selected_recommendation = None
            self.recommendation_var.set("")
            
            if not recommendations:
                self.results_text.insert(tk.END, "No recommendations found.")
                self.recommendation_combo['values'] = []
            else:
                self.results_text.insert(tk.END, f"Found {len(recommendations)} recommendations for slide {slide_number}:\n\n")
                
                # Populate dropdown options
                dropdown_options = []
                for i, rec in enumerate(recommendations, 1):
                    option_text = f"{i}. {rec['deck_id']} - Slide {rec['slide_index']} (Similarity: {rec['similarity']:.3f})"
                    dropdown_options.append(option_text)
                    
                    self.results_text.insert(tk.END, f"{i}. {rec['deck_id']} - Slide {rec['slide_index']}\n")
                    self.results_text.insert(tk.END, f"   Similarity: {rec['similarity']:.3f}\n")
                    
                    # Display separated text and image captions
                    if rec.get('text', '').strip():
                        self.results_text.insert(tk.END, f"   Text: {rec['text']}\n")
                    
                    if rec.get('captions', '').strip():
                        self.results_text.insert(tk.END, f"   Image Captions: {rec['captions']}\n")
                    
                    # Improved type display
                    if rec['has_text'] and rec['has_image']:
                        self.results_text.insert(tk.END, "   Type: Has text and images\n")
                    elif rec['has_text']:
                        self.results_text.insert(tk.END, "   Type: Has text\n")
                    elif rec['has_image']:
                        self.results_text.insert(tk.END, "   Type: Has image(s)\n")
                    
                    self.results_text.insert(tk.END, "\n")
                
                # Set dropdown options
                self.recommendation_combo['values'] = dropdown_options
                if dropdown_options:
                    self.recommendation_combo.set(dropdown_options[0])  # Select first option by default
            
            self.rec_status_label.config(text=f"Found {len(recommendations)} recommendations", foreground='green')
            
        except Exception as e:
            self.rec_status_label.config(text=f"Error getting recommendations: {e}", foreground='red')
            messagebox.showerror("Error", f"Error getting recommendations: {e}")
    
    
    def get_selected_recommendation(self):
        """Get the currently selected recommendation from the dropdown."""
        if not hasattr(self, 'current_recommendations') or not self.current_recommendations:
            return None
        
        selected_text = self.recommendation_var.get()
        if not selected_text:
            return None
        
        # Extract recommendation number from dropdown text (e.g., "1. DStest - Slide 2 (Similarity: 0.850)")
        try:
            # Get the number at the beginning of the selected text
            rec_number = int(selected_text.split('.')[0])
            if 1 <= rec_number <= len(self.current_recommendations):
                return self.current_recommendations[rec_number - 1]
        except (ValueError, IndexError):
            pass
        
        return None
    
    def download_selected_slide(self):
        """Download the selected recommended slide as a new PowerPoint file."""
        rec = self.get_selected_recommendation()
        if not rec:
            messagebox.showwarning("No Selection", "Please click on a recommendation in the text area first.")
            return
        
        # Find the source file
        source_file = None
        for file_info in self.embedded_files:
            if file_info.get('deck_id') == rec['deck_id']:
                source_file = file_info['file_path']
                break
        
        if not source_file or not os.path.exists(source_file):
            messagebox.showerror("File Not Found", f"Source file for {rec['deck_id']} not found.")
            return
        
        # Ask where to save the slide
        slide_num = rec['slide_index']
        default_name = f"{rec['deck_id']}_slide_{slide_num}.pptx"
        
        file_path = filedialog.asksaveasfilename(
            title="Save Slide As",
            defaultextension=".pptx",
            filetypes=[("PowerPoint files", "*.pptx"), ("All files", "*.*")],
            initialfile=default_name
        )
        
        if file_path:
            try:
                self.extract_slide_from_pptx(source_file, slide_num, file_path)
                messagebox.showinfo("Success", f"Slide {slide_num} saved as {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Error extracting slide: {e}")
    
    def extract_slide_from_pptx(self, source_file, slide_num, output_file):
        """Extract a specific slide from a PowerPoint file with full content preservation."""
        try:
            from pptx import Presentation
            from pptx.util import Inches
            from pptx.enum.shapes import MSO_SHAPE
            from pptx.enum.text import PP_ALIGN
            from pptx.dml.color import RGBColor
            import io
            
            # Load the source presentation
            prs = Presentation(source_file)
            
            # Validate slide number
            if not (1 <= slide_num <= len(prs.slides)):
                raise ValueError(f"Slide {slide_num} not found. Presentation has {len(prs.slides)} slides.")
            
            # Create a new presentation with the same slide size
            new_prs = Presentation()
            new_prs.slide_width = prs.slide_width
            new_prs.slide_height = prs.slide_height
            
            # Get the source slide (slide_num is 1-indexed, but list is 0-indexed)
            slide_index = slide_num - 1
            source_slide = prs.slides[slide_index]
            
            # Use a blank layout for the new slide
            blank_layout = new_prs.slide_layouts[6]  # Blank layout
            new_slide = new_prs.slides.add_slide(blank_layout)
            
            # Copy all shapes from source slide to new slide
            for shape in source_slide.shapes:
                try:
                    self._copy_shape_improved(shape, new_slide)
                except Exception as e:
                    print(f"Warning: Could not copy shape: {e}")
                    continue
            
            # Save the new presentation
            new_prs.save(output_file)
            return True
                
        except ImportError:
            messagebox.showerror("Error", "python-pptx library not available for slide extraction.")
        except Exception as e:
            raise Exception(f"Failed to extract slide: {e}")
    
    def _copy_shape_improved(self, source_shape, target_slide):
        """Improved shape copying with better formatting and image preservation."""
        from pptx import Presentation
        from pptx.util import Inches
        from pptx.enum.shapes import MSO_SHAPE
        from pptx.enum.text import PP_ALIGN
        from pptx.dml.color import RGBColor
        import io
        
        # Get shape properties
        left = source_shape.left
        top = source_shape.top
        width = source_shape.width
        height = source_shape.height
        
        # Handle different shape types - check for text content first
        if hasattr(source_shape, 'text_frame') and source_shape.text_frame and source_shape.text_frame.text.strip():
            # Text box or text shape - simplified but effective copying
            textbox = target_slide.shapes.add_textbox(left, top, width, height)
            text_frame = textbox.text_frame
            text_frame.clear()
            
            # Copy text content - ensure text is copied
            for i, paragraph in enumerate(source_shape.text_frame.paragraphs):
                if i == 0:
                    p = text_frame.paragraphs[0]
                else:
                    p = text_frame.add_paragraph()
                
                # Copy the text content first - this is the most important part
                if paragraph.text:
                    p.text = paragraph.text
                
                # Copy paragraph properties safely
                try:
                    p.alignment = paragraph.alignment
                except:
                    pass
                
                # Try to copy basic formatting from the first run
                if paragraph.runs and len(paragraph.runs) > 0:
                    try:
                        first_run = paragraph.runs[0]
                        if first_run.font.name:
                            p.font.name = first_run.font.name
                        if first_run.font.size:
                            p.font.size = first_run.font.size
                        p.font.bold = first_run.font.bold
                        p.font.italic = first_run.font.italic
                        
                        # Copy color if available and has RGB property
                        try:
                            if hasattr(first_run.font.color, 'rgb') and first_run.font.color.rgb:
                                p.font.color.rgb = first_run.font.color.rgb
                        except:
                            pass
                    except Exception as e:
                        print(f"Warning: Could not copy text formatting: {e}")
                        pass
        
        elif source_shape.shape_type == 13:  # MSO_SHAPE.PICTURE
            # Picture - improved image copying
            try:
                # Get the image data
                image = source_shape.image
                if hasattr(image, 'blob') and image.blob:
                    # Create a BytesIO object from the image blob
                    image_stream = io.BytesIO(image.blob)
                    target_slide.shapes.add_picture(image_stream, left, top, width, height)
                else:
                    raise Exception("No image blob available")
            except Exception as e:
                print(f"Could not copy image: {e}")
                # Create a better placeholder
                placeholder = target_slide.shapes.add_shape(
                    MSO_SHAPE.RECTANGLE, left, top, width, height
                )
                placeholder.text = "[Image]"
                placeholder.fill.solid()
                placeholder.fill.fore_color.rgb = RGBColor(240, 240, 240)
                # Add a border
                placeholder.line.color.rgb = RGBColor(200, 200, 200)
                placeholder.line.width = 1
        
        elif source_shape.shape_type in [1, 2, 3, 4, 5]:  # Basic shapes (RECTANGLE, OVAL, etc.)
            # Basic shapes with full formatting
            shape_type = source_shape.shape_type
            new_shape = target_slide.shapes.add_shape(shape_type, left, top, width, height)
            
            # Copy fill properties
            if hasattr(source_shape, 'fill') and source_shape.fill.type:
                if source_shape.fill.type == 1:  # Solid fill
                    new_shape.fill.solid()
                    if source_shape.fill.fore_color.rgb:
                        new_shape.fill.fore_color.rgb = source_shape.fill.fore_color.rgb
                elif source_shape.fill.type == 2:  # Gradient fill
                    new_shape.fill.gradient()
                    # Copy gradient properties if needed
            
            # Copy line properties safely
            try:
                if hasattr(source_shape, 'line') and hasattr(source_shape.line.color, 'rgb') and source_shape.line.color.rgb:
                    new_shape.line.color.rgb = source_shape.line.color.rgb
                    new_shape.line.width = source_shape.line.width
            except:
                pass
            
            # Copy text if it has any
            if hasattr(source_shape, 'text') and source_shape.text:
                new_shape.text = source_shape.text
        
        else:
            # Generic shape - create a better placeholder
            placeholder = target_slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE, left, top, width, height
            )
            placeholder.text = f"[{source_shape.shape_type}]"
            placeholder.fill.solid()
            placeholder.fill.fore_color.rgb = RGBColor(250, 250, 250)
            placeholder.line.color.rgb = RGBColor(200, 200, 200)
    
    
    
    def search_slides(self):
        """Search for slides."""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Empty Query", "Please enter a search query.")
            return
        
        try:
            n_results = int(self.search_num_var.get())
        except ValueError:
            n_results = 5
        
        self.search_status_label.config(text="Searching...", foreground='blue')
        self.root.update()
        
        try:
            results = self.vector_db.search_slides(query, n_results)
            
            # Display results
            self.search_results_text.delete(1.0, tk.END)
            
            if not results:
                self.search_results_text.insert(tk.END, "No results found.")
            else:
                self.search_results_text.insert(tk.END, f"Found {len(results)} results for '{query}':\n\n")
                
                for i, result in enumerate(results, 1):
                    self.search_results_text.insert(tk.END, f"{i}. {result['deck_id']} - Slide {result['slide_index']}\n")
                    self.search_results_text.insert(tk.END, f"   Similarity: {result['similarity_score']:.3f}\n")
                    self.search_results_text.insert(tk.END, f"   Content: {result['content'][:200]}...\n")
                    
                    if result['has_text'] and result['has_image']:
                        self.search_results_text.insert(tk.END, "   Type: [TEXT+IMAGE] Has text and images\n")
                    elif result['has_text']:
                        self.search_results_text.insert(tk.END, "   Type: [TEXT] Text only\n")
                    elif result['has_image']:
                        self.search_results_text.insert(tk.END, "   Type: [IMAGE] Images only\n")
                    
                    self.search_results_text.insert(tk.END, "\n")
            
            self.search_status_label.config(text=f"Found {len(results)} results", foreground='green')
            
        except Exception as e:
            self.search_status_label.config(text=f"Error searching: {e}", foreground='red')
            messagebox.showerror("Error", f"Error searching: {e}")
    
    def refresh_statistics(self):
        """Refresh the statistics display."""
        try:
            stats = self.vector_db.get_database_stats()
            
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, "Database Statistics\n")
            self.stats_text.insert(tk.END, "=" * 30 + "\n\n")
            self.stats_text.insert(tk.END, f"Total slides: {stats['total_slides']}\n")
            self.stats_text.insert(tk.END, f"Unique decks: {stats['unique_decks']}\n")
            self.stats_text.insert(tk.END, f"Tracked files: {stats['tracked_files']}\n\n")
            
            if stats['deck_ids']:
                self.stats_text.insert(tk.END, "Deck IDs:\n")
                for deck_id in stats['deck_ids']:
                    self.stats_text.insert(tk.END, f"  • {deck_id}\n")
            
        except Exception as e:
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, f"Error loading statistics: {e}")

def main():
    """Main function."""
    root = tk.Tk()
    app = PPTRecommendationApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
