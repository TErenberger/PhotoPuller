"""
GUI module for PhotoPuller application
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import subprocess
import os
import json
from photopuller_core import PhotoPullerCore

# Try to import PIL/Pillow for thumbnail support (optional)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class PhotoPullerGUI:
    """Main GUI application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PhotoPuller - Find & Organize Photos & Videos")
        self.root.geometry("1200x800")
        
        # Set Windows native theme
        style = ttk.Style()
        # Try to use Windows native theme (vista, xpnative, or winnative)
        try:
            style.theme_use('vista')  # Windows Vista/7/10/11 theme
        except:
            try:
                style.theme_use('xpnative')  # Windows XP theme fallback
            except:
                style.theme_use('winnative')  # Classic Windows theme fallback
        
        # Configure native Windows styling
        style.configure('Title.TLabel', font=('Segoe UI', 10, 'bold'))
        style.configure('Heading.TLabel', font=('Segoe UI', 9))
        style.configure('Status.TLabel', font=('Segoe UI', 8))
        
        self.core = PhotoPullerCore()  # Use core class for business logic
        self.file_to_item_map = {}  # Map file paths to treeview items
        self.file_copy_status = {}  # Track copy status for each file
        self.scan_photos = tk.BooleanVar(value=True)  # Filter for photos
        self.scan_videos = tk.BooleanVar(value=True)  # Filter for videos
        self.scan_pdfs = tk.BooleanVar(value=True)  # Filter for PDFs
        
        # Path to excluded folders JSON file (in same directory as script)
        self.excluded_folders_file = Path(__file__).parent / "excluded_folders.json"
        
        # Load excluded folders on startup
        self.load_excluded_folders()
        
        self.setup_ui()
        
        # Populate excluded folders listbox after UI is created
        self.update_excluded_listbox()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main container with Windows-style padding
        main_frame = ttk.Frame(self.root, padding="12")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)  # Results column gets more space
        main_frame.rowconfigure(0, weight=1)
        
        # Left column container
        left_column = ttk.Frame(main_frame)
        left_column.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 8))
        left_column.columnconfigure(0, weight=1)
        
        # Source drive selection
        source_frame = ttk.LabelFrame(left_column, text="Source Drive", padding="12")
        source_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        
        self.source_var = tk.StringVar(value="C:\\")
        source_entry = ttk.Entry(source_frame, textvariable=self.source_var, width=32)
        source_entry.grid(row=0, column=0, padx=(0, 6), pady=4, sticky=(tk.W, tk.E))
        source_frame.columnconfigure(0, weight=1)
        
        # Button frame for better alignment
        button_frame = ttk.Frame(source_frame)
        button_frame.grid(row=0, column=1, padx=(0, 0))
        
        ttk.Button(button_frame, text="Browse...", 
                  command=self.browse_source, width=12).grid(row=0, column=0, padx=(0, 4))
        
        ttk.Button(button_frame, text="Scan Drive", 
                  command=self.start_scan, width=12).grid(row=0, column=1, padx=0)
        
        # File type filters
        filter_frame = ttk.Frame(source_frame)
        filter_frame.grid(row=1, column=0, columnspan=2, pady=(8, 0), sticky=tk.W)
        
        ttk.Label(filter_frame, text="Scan for:", style='Heading.TLabel').grid(row=0, column=0, padx=(0, 8))
        ttk.Checkbutton(filter_frame, text="Photos", variable=self.scan_photos).grid(row=0, column=1, padx=6)
        ttk.Checkbutton(filter_frame, text="Videos", variable=self.scan_videos).grid(row=0, column=2, padx=6)
        ttk.Checkbutton(filter_frame, text="PDFs", variable=self.scan_pdfs).grid(row=0, column=3, padx=6)
        
        # Scan progress
        progress_frame = ttk.LabelFrame(left_column, text="Scan Progress", padding="12")
        progress_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        progress_frame.columnconfigure(0, weight=1)
        
        self.scan_progress_var = tk.StringVar(value="Ready to scan")
        progress_label = ttk.Label(progress_frame, textvariable=self.scan_progress_var, 
                                  anchor=tk.W, justify=tk.LEFT, style='Status.TLabel')
        progress_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 4))
        
        # Current file being scanned (on its own line)
        self.scan_current_file_var = tk.StringVar(value="")
        current_file_label = ttk.Label(progress_frame, textvariable=self.scan_current_file_var, 
                                       anchor=tk.W, justify=tk.LEFT, style='Status.TLabel',
                                       foreground="gray")
        current_file_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 6))
        
        self.scan_progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate', length=200)
        self.scan_progress_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=0)
        
        # Excluded folders section
        excluded_frame = ttk.LabelFrame(left_column, text="Excluded Folders", padding="12")
        excluded_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        
        self.excluded_listbox = tk.Listbox(excluded_frame, height=4, relief=tk.SUNKEN, 
                                           borderwidth=1, font=('Segoe UI', 9))
        self.excluded_listbox.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))
        excluded_frame.columnconfigure(0, weight=1)
        
        # Bind double-click to edit exclusion
        self.excluded_listbox.bind('<Double-Button-1>', lambda e: self.edit_exclusion())
        
        # Button frame for better alignment
        excluded_button_frame = ttk.Frame(excluded_frame)
        excluded_button_frame.grid(row=1, column=0, columnspan=3)
        
        ttk.Button(excluded_button_frame, text="Edit", 
                  command=self.edit_exclusion, width=10).grid(row=0, column=0, padx=(0, 4))
        ttk.Button(excluded_button_frame, text="Remove", 
                  command=self.remove_exclusion, width=10).grid(row=0, column=1, padx=(0, 4))
        ttk.Button(excluded_button_frame, text="Clear All", 
                  command=self.clear_all_exclusions, width=10).grid(row=0, column=2, padx=0)
        
        # Destination selection
        dest_frame = ttk.LabelFrame(left_column, text="Destination", padding="12")
        dest_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        
        self.dest_var = tk.StringVar()
        dest_entry = ttk.Entry(dest_frame, textvariable=self.dest_var, width=32)
        dest_entry.grid(row=0, column=0, padx=(0, 6), pady=4, sticky=(tk.W, tk.E))
        dest_frame.columnconfigure(0, weight=1)
        # Trace destination changes to update copy button state
        self.dest_var.trace_add('write', lambda *args: self.update_copy_button_state())
        
        ttk.Button(dest_frame, text="Browse...", 
                  command=self.browse_destination, width=12).grid(row=0, column=1, padx=0)
        
        # Organization method
        org_frame = ttk.Frame(dest_frame)
        org_frame.grid(row=1, column=0, columnspan=2, pady=(8, 0), sticky=tk.W)
        
        ttk.Label(org_frame, text="Organize by:", style='Heading.TLabel').grid(row=0, column=0, padx=(0, 8))
        self.org_method_var = tk.StringVar(value="date")
        ttk.Radiobutton(org_frame, text="Date", variable=self.org_method_var, 
                       value="date").grid(row=0, column=1, padx=8)
        ttk.Radiobutton(org_frame, text="Source", variable=self.org_method_var, 
                       value="source").grid(row=0, column=2, padx=8)
        
        # Copy button
        self.copy_button = ttk.Button(dest_frame, text="Copy Files", 
                                      command=self.start_copy, state=tk.DISABLED, width=20)
        self.copy_button.grid(row=2, column=0, columnspan=2, pady=(12, 0))
        
        # Copy progress
        copy_progress_frame = ttk.LabelFrame(left_column, text="Copy Progress", padding="12")
        copy_progress_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=0)
        copy_progress_frame.columnconfigure(0, weight=1)
        
        self.copy_progress_var = tk.StringVar(value="")
        ttk.Label(copy_progress_frame, textvariable=self.copy_progress_var, 
                 style='Status.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 4))
        
        # Overall progress bar
        self.copy_progress_bar = ttk.Progressbar(copy_progress_frame, mode='determinate', length=200)
        self.copy_progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 6))
        
        # Current file being copied
        self.copy_current_file_var = tk.StringVar(value="")
        current_file_label = ttk.Label(copy_progress_frame, textvariable=self.copy_current_file_var, 
                                      anchor=tk.W, justify=tk.LEFT, style='Status.TLabel',
                                      foreground="gray")
        current_file_label.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 4))
        
        # Per-file progress bar
        self.copy_file_progress_bar = ttk.Progressbar(copy_progress_frame, mode='determinate', length=200)
        self.copy_file_progress_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 4))
        
        # Copy rate display
        self.copy_rate_var = tk.StringVar(value="")
        copy_rate_label = ttk.Label(copy_progress_frame, textvariable=self.copy_rate_var, 
                                   anchor=tk.W, justify=tk.LEFT, style='Status.TLabel',
                                   foreground="blue")
        copy_rate_label.grid(row=4, column=0, sticky=tk.W, pady=0)
        
        # Right column - Results
        results_frame = ttk.LabelFrame(main_frame, text="Scan Results", padding="12")
        results_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(8, 0))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)  # Treeview row
        results_frame.rowconfigure(1, weight=0)  # Thumbnail row (fixed size)
        
        # Results treeview
        tree_frame = ttk.Frame(results_frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 8))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Configure Treeview style for native Windows look
        style = ttk.Style()
        style.configure("Treeview", font=('Segoe UI', 9), rowheight=22)
        style.configure("Treeview.Heading", font=('Segoe UI', 9, 'bold'))
        
        self.results_tree = ttk.Treeview(tree_frame, columns=("File Path", "Type", "Size", "Date"), 
                                        show="tree headings", height=15)
        self.results_tree.heading("#0", text="Status")
        self.results_tree.heading("File Path", text="File Path")
        self.results_tree.heading("Type", text="Type")
        self.results_tree.heading("Size", text="Size")
        self.results_tree.heading("Date", text="Modified")
        
        self.results_tree.column("#0", width=90, anchor=tk.W)
        self.results_tree.column("File Path", width=280, anchor=tk.W)
        self.results_tree.column("Type", width=70, anchor=tk.W)
        self.results_tree.column("Size", width=90, anchor=tk.W)
        self.results_tree.column("Date", width=130, anchor=tk.W)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Create context menu for right-click
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Open File Location", command=self.open_file_location)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Exclude Parent Folder", command=self.exclude_parent_folder)
        
        # Bind right-click to show context menu
        self.results_tree.bind("<Button-3>", self.show_context_menu)
        
        # Bind selection event to update thumbnail
        self.results_tree.bind("<<TreeviewSelect>>", self.on_treeview_select)
        
        # Thumbnail preview frame (fixed size, 16:9 aspect ratio)
        # 640x360 for 16:9 ratio (width:height = 16:9)
        self.THUMBNAIL_WIDTH = 640
        self.THUMBNAIL_HEIGHT = 360
        self.preview_collapsed = False  # Track collapse state
        
        thumbnail_frame = ttk.LabelFrame(results_frame, text="Preview", padding="12")
        thumbnail_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        thumbnail_frame.columnconfigure(0, weight=1)
        
        # Header frame with toggle button
        preview_header_frame = ttk.Frame(thumbnail_frame)
        preview_header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        
        # Toggle button for collapse/expand
        self.preview_toggle_button = ttk.Button(
            preview_header_frame, 
            text="▼",  # Down arrow = expanded
            command=self.toggle_preview,
            width=3
        )
        self.preview_toggle_button.grid(row=0, column=0, padx=(0, 6))
        
        # Label for "Preview" text
        preview_label = ttk.Label(preview_header_frame, text="Preview", style='Heading.TLabel')
        preview_label.grid(row=0, column=1, sticky=tk.W)
        
        # Thumbnail display area with fixed size using Canvas for better control
        self.thumbnail_canvas_frame = ttk.Frame(thumbnail_frame)
        self.thumbnail_canvas_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Use Canvas for fixed-size image display
        self.thumbnail_canvas = tk.Canvas(self.thumbnail_canvas_frame, 
                                          width=self.THUMBNAIL_WIDTH, 
                                          height=self.THUMBNAIL_HEIGHT,
                                          bg='white', relief=tk.SUNKEN, borderwidth=1)
        self.thumbnail_canvas.grid(row=0, column=0)
        self.thumbnail_canvas_id = None  # Keep reference to canvas image item
        self.current_thumbnail_image = None  # Keep reference to prevent garbage collection
        
        # Text label for placeholder (centered on canvas)
        self.thumbnail_text_id = self.thumbnail_canvas.create_text(
            self.THUMBNAIL_WIDTH // 2, 
            self.THUMBNAIL_HEIGHT // 2,
            text="Select a file to preview",
            font=('Segoe UI', 9),
            fill='gray'
        )
        
        # File info label below thumbnail
        self.thumbnail_info_var = tk.StringVar(value="")
        self.thumbnail_info_label = ttk.Label(thumbnail_frame, textvariable=self.thumbnail_info_var,
                                         anchor=tk.CENTER, justify=tk.CENTER,
                                         style='Status.TLabel', wraplength=self.THUMBNAIL_WIDTH - 40)
        self.thumbnail_info_label.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(8, 0))
        
        # Stats label
        self.stats_var = tk.StringVar(value="No files found yet")
        ttk.Label(results_frame, textvariable=self.stats_var, style='Status.TLabel').grid(row=2, column=0, pady=(0, 0))
    
    def browse_source(self):
        """Browse for source drive/directory"""
        path = filedialog.askdirectory(title="Select Source Drive/Directory")
        if path:
            self.source_var.set(path)
    
    def browse_destination(self):
        """Browse for destination directory"""
        path = filedialog.askdirectory(title="Select Destination Directory")
        if path:
            self.dest_var.set(path)
            # Update copy button state after setting destination
            self.update_copy_button_state()
    
    def start_scan(self):
        """Start scanning in a separate thread"""
        source = self.source_var.get()
        if not source:
            messagebox.showerror("Error", "Please select a source drive")
            return
        
        # Disable scan button and start progress
        self.scan_progress_bar.start()
        self.scan_progress_var.set("Scanning...")
        self.scan_current_file_var.set("")
        
        # Start scan in thread
        thread = threading.Thread(target=self.scan_drive, args=(source,))
        thread.daemon = True
        thread.start()
    
    def scan_drive(self, source_path):
        """Scan drive for files (runs in thread)"""
        try:
            def progress_callback(current_path, stats):
                self.root.after(0, self.update_scan_progress, current_path, stats)
            
            # Get filter settings
            scan_photos = self.scan_photos.get()
            scan_videos = self.scan_videos.get()
            scan_pdfs = self.scan_pdfs.get()
            
            # Get excluded folders as list of strings
            excluded_folders = [str(f) for f in self.core.excluded_folders]
            
            # Use core to scan
            self.core.scan(
                source_path,
                scan_photos=scan_photos,
                scan_videos=scan_videos,
                scan_pdfs=scan_pdfs,
                excluded_folders=excluded_folders,
                progress_callback=progress_callback
            )
            
            # Update UI on main thread
            self.root.after(0, self.scan_complete)
            
        except ValueError as e:
            self.root.after(0, lambda: messagebox.showwarning("No Filter Selected", str(e)))
            self.root.after(0, self.scan_failed)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Scan Error", str(e)))
            self.root.after(0, self.scan_failed)
    
    def update_scan_progress(self, current_path, stats):
        """Update scan progress (called from main thread)"""
        # Update stats on first line
        pdfs_count = stats.get('pdfs_found', 0)
        self.scan_progress_var.set(
            f"Found: {stats.get('photos_found', 0)} photos, {stats.get('videos_found', 0)} videos, {pdfs_count} PDFs"
        )
        
        # Show current file path on second line (truncate if too long)
        max_path_length = 60
        if len(current_path) > max_path_length:
            # Show just the last part of the path (filename and parent folder)
            path_parts = current_path.replace('\\', '/').split('/')
            if len(path_parts) > 1:
                # Try to show last folder and filename
                display_path = '/'.join(path_parts[-2:])
            else:
                display_path = path_parts[-1] if path_parts else current_path
            
            # If still too long, truncate with ellipsis
            if len(display_path) > max_path_length:
                display_path = "..." + display_path[-(max_path_length-3):]
        else:
            display_path = current_path
        
        self.scan_current_file_var.set(f"Scanning: {display_path}")
    
    def scan_complete(self):
        """Handle scan completion"""
        self.scan_progress_bar.stop()
        stats = self.core.get_scan_stats()
        self.scan_progress_var.set(
            f"Scan complete! Found {stats['total_files']} files "
            f"({stats['photos']} photos, {stats['videos']} videos, {stats['pdfs']} PDFs)"
        )
        self.scan_current_file_var.set("")
        
        # Apply exclusions and update display
        self.apply_exclusions()
        
        # Update copy button state
        self.update_copy_button_state()
    
    def update_copy_button_state(self):
        """Update the copy button state based on current conditions"""
        if not self.copy_button:
            return
        
        # Enable button if: destination is set AND there are files to copy
        has_destination = bool(self.dest_var.get().strip())
        has_files = len(self.core.found_files) > 0
        
        if has_destination and has_files:
            self.copy_button.config(state=tk.NORMAL)
        else:
            self.copy_button.config(state=tk.DISABLED)
    
    def update_excluded_listbox(self):
        """Update the excluded folders listbox display"""
        if hasattr(self, 'excluded_listbox'):
            self.excluded_listbox.delete(0, tk.END)
            for folder in sorted(self.core.excluded_folders):
                self.excluded_listbox.insert(tk.END, str(folder))
    
    def apply_exclusions(self):
        """Filter results based on excluded folders"""
        # Use core's files and infos
        self.found_files = self.core.found_files
        self.file_infos = self.core.file_infos
        self.all_found_files = self.core.all_found_files
        self.all_file_infos = self.core.all_file_infos
        
        # Update excluded folders listbox
        self.update_excluded_listbox()
        
        # Populate results tree
        self.results_tree.delete(*self.results_tree.get_children())
        # Preserve copy statuses when repopulating (e.g., after exclusion changes)
        preserved_statuses = self.file_copy_status.copy()
        self.file_to_item_map.clear()
        self.file_copy_status.clear()
        
        for file_path, file_info in zip(self.found_files, self.file_infos):
            if 'error' not in file_info:
                if file_info.get('is_photo', False):
                    file_type = "Photo"
                elif file_info.get('is_video', False):
                    file_type = "Video"
                elif file_info.get('is_pdf', False):
                    file_type = "PDF"
                else:
                    file_type = "Unknown"
                size_mb = file_info['size'] / (1024 * 1024)
                date_str = file_info['modified'].strftime("%Y-%m-%d %H:%M")
                file_path_str = str(file_path)
                
                # Preserve status if file was previously in the list, otherwise default to "Not Copied"
                status = preserved_statuses.get(file_path_str, "Not Copied")
                self.file_copy_status[file_path_str] = status
                
                item = self.results_tree.insert("", tk.END, text=status,
                                                values=(file_path_str, file_type, f"{size_mb:.2f} MB", date_str))
                self.file_to_item_map[file_path_str] = item
        
        # Update stats using core
        stats = self.core.get_scan_stats()
        self.stats_var.set(
            f"Showing: {stats['total_files']} files (Excluded: {stats['excluded_count']}), "
            f"{stats['photos']} photos, {stats['videos']} videos, {stats['pdfs']} PDFs, "
            f"Total size: {stats['total_size_gb']:.2f} GB"
        )
    
    def scan_failed(self):
        """Handle scan failure"""
        self.scan_progress_bar.stop()
        self.scan_progress_var.set("Scan failed")
        self.scan_current_file_var.set("")
    
    def start_copy(self):
        """Start copying files in a separate thread"""
        destination = self.dest_var.get()
        if not destination:
            messagebox.showerror("Error", "Please select a destination directory")
            return
        
        if not self.found_files:
            messagebox.showerror("Error", "No files to copy. Please scan first.")
            return
        
        # Disable copy button and start progress
        if self.copy_button:
            self.copy_button.config(state=tk.DISABLED)
        self.copy_progress_bar['maximum'] = len(self.found_files)
        self.copy_progress_bar['value'] = 0
        self.copy_file_progress_bar['value'] = 0
        self.copy_file_progress_bar['maximum'] = 100
        self.copy_progress_var.set("Copying files...")
        self.copy_current_file_var.set("")
        self.copy_rate_var.set("")
        
        # Reset all file statuses to "Not Copied" (except those already copied)
        for file_path_str, item in self.file_to_item_map.items():
            if self.file_copy_status.get(file_path_str, "Not Copied") not in ['✓ Copied', '⊘ Skipped', '✗ Error', '↻ Duplicate']:
                self.results_tree.item(item, text="Not Copied")
                self.file_copy_status[file_path_str] = "Not Copied"
        
        # Start copy in thread
        organize_method = self.org_method_var.get()
        thread = threading.Thread(target=self.copy_files, args=(destination, organize_method))
        thread.daemon = True
        thread.start()
    
    def copy_files(self, destination, organize_method):
        """Copy files (runs in thread)"""
        try:
            def progress_callback(current_file, stats, copy_status=None):
                self.root.after(0, self.update_copy_progress, current_file, stats, copy_status)
            
            def file_progress_callback(bytes_copied, total_bytes, copy_rate_mbps):
                self.root.after(0, self.update_file_copy_progress, 
                              bytes_copied, total_bytes, copy_rate_mbps)
            
            # Use core to copy files
            results = self.core.copy_files(
                destination,
                organize_method=organize_method,
                dry_run=False,
                progress_callback=progress_callback,
                file_progress_callback=file_progress_callback
            )
            
            # Update UI on main thread
            self.root.after(0, self.copy_complete, results)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Copy Error", str(e)))
            self.root.after(0, self.copy_failed)
    
    def update_copy_progress(self, current_file, stats, copy_status=None):
        """Update copy progress (called from main thread)"""
        self.copy_progress_bar['value'] = stats['copied'] + stats['skipped'] + stats['errors']
        self.copy_progress_var.set(
            f"Copied: {stats['copied']}, Skipped: {stats['skipped']}, "
            f"Errors: {stats['errors']}, Duplicates: {stats['duplicates']}"
        )
        
        # Update current file display (truncate if too long)
        file_name = Path(current_file).name
        if len(file_name) > 60:
            file_name = "..." + file_name[-57:]
        self.copy_current_file_var.set(f"Copying: {file_name}")
        
        # Update status in treeview
        if current_file in self.file_to_item_map:
            item = self.file_to_item_map[current_file]
            if copy_status:
                # Update with final status
                status_text = {
                    'copied': '✓ Copied',
                    'skipped': '⊘ Skipped',
                    'error': '✗ Error',
                    'duplicate': '↻ Duplicate',
                    'would_copy': '✓ Would Copy'  # For dry-run
                }.get(copy_status, 'Unknown')
                self.results_tree.item(item, text=status_text)
                self.file_copy_status[current_file] = status_text
            else:
                # Update to "Copying" status
                self.results_tree.item(item, text="Copying...")
                self.file_copy_status[current_file] = "Copying..."
    
    def update_file_copy_progress(self, bytes_copied, total_bytes, copy_rate_mbps):
        """Update per-file copy progress (called from main thread)"""
        # Update per-file progress bar
        if total_bytes > 0:
            progress_percent = (bytes_copied / total_bytes) * 100
            self.copy_file_progress_bar['maximum'] = total_bytes
            self.copy_file_progress_bar['value'] = bytes_copied
            
            # Update copy rate display
            bytes_mb = bytes_copied / (1024 * 1024)
            total_mb = total_bytes / (1024 * 1024)
            self.copy_rate_var.set(
                f"{bytes_mb:.2f} MB / {total_mb:.2f} MB ({progress_percent:.1f}%) - "
                f"Speed: {copy_rate_mbps:.2f} MB/s"
            )
        else:
            self.copy_file_progress_bar['value'] = 0
            self.copy_rate_var.set("")
    
    def copy_complete(self, results):
        """Handle copy completion"""
        stats = self.core.get_copy_stats()
        self.copy_progress_var.set(
            f"Copy complete! Copied: {stats.get('copied', 0)}, "
            f"Skipped: {stats.get('skipped', 0)}, Errors: {stats.get('errors', 0)}, "
            f"Duplicates: {stats.get('duplicates', 0)}"
        )
        self.copy_progress_bar['value'] = stats.get('total', 0)
        self.copy_file_progress_bar['value'] = 0
        self.copy_current_file_var.set("")
        self.copy_rate_var.set("")
        
        if self.copy_button:
            self.copy_button.config(state=tk.NORMAL)
        
        messagebox.showinfo(
            "Copy Complete",
            f"Copy operation completed!\n\n"
            f"Copied: {stats.get('copied', 0)} files\n"
            f"Skipped: {stats.get('skipped', 0)} files\n"
            f"Errors: {stats.get('errors', 0)} files\n"
            f"Duplicates: {stats.get('duplicates', 0)} files"
        )
    
    def copy_failed(self):
        """Handle copy failure"""
        self.copy_progress_var.set("Copy failed")
        self.copy_file_progress_bar['value'] = 0
        self.copy_current_file_var.set("")
        self.copy_rate_var.set("")
        if self.copy_button:
            self.copy_button.config(state=tk.NORMAL)
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        # Select the item under the cursor
        item = self.results_tree.identify_row(event.y)
        if item:
            self.results_tree.selection_set(item)
            # Show context menu at cursor position
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
    
    def open_file_location(self):
        """Open the selected file's location in Windows File Explorer"""
        selection = self.results_tree.selection()
        if not selection:
            return
        
        # Get the file path from the selected item
        # Since Status is in the text column (#0), file path is in the values array (first column)
        item = selection[0]
        values = self.results_tree.item(item, "values")
        
        if not values or len(values) == 0:
            messagebox.showwarning("Warning", "No file path found for selected item")
            return
        
        # File path is the first value in the values array
        file_path_str = values[0]
        
        if not file_path_str:
            messagebox.showwarning("Warning", "No file path found for selected item")
            return
        
        try:
            file_path = Path(file_path_str)
            if not file_path.exists():
                messagebox.showerror("Error", f"File does not exist:\n{file_path_str}")
                return
            
            # Open the folder containing the file in Windows Explorer
            # Use explorer.exe with /select to highlight the file
            folder_path = file_path.parent
            subprocess.Popen(f'explorer.exe /select,"{file_path}"', shell=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file location:\n{str(e)}")
    
    def exclude_parent_folder(self):
        """Exclude the parent folder of the selected file"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file first")
            return
        
        # Get the file path from the selected item
        # Since Status is in the text column (#0), file path is in the values array (first column)
        item = selection[0]
        values = self.results_tree.item(item, "values")
        
        if not values or len(values) == 0:
            messagebox.showwarning("Warning", "No file path found for selected item")
            return
        
        # File path is the first value in the values array
        file_path_str = values[0]
        
        if not file_path_str:
            messagebox.showwarning("Warning", "No file path found for selected item")
            return
        
        try:
            file_path = Path(file_path_str)
            parent_folder = file_path.parent
            
            # Add to excluded folders using core
            self.core.add_excluded_folder(str(parent_folder))
            
            # Save excluded folders to file
            self.save_excluded_folders()
            
            # Reapply exclusions to update the display
            self.apply_exclusions()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to exclude folder:\n{str(e)}")
    
    def toggle_preview(self):
        """Toggle the preview section between collapsed and expanded"""
        self.preview_collapsed = not self.preview_collapsed
        
        if self.preview_collapsed:
            # Collapse: hide the preview content
            self.thumbnail_canvas_frame.grid_remove()
            self.thumbnail_info_label.grid_remove()
            # Update button to show right arrow (collapsed)
            self.preview_toggle_button.config(text="▶")
        else:
            # Expand: show the preview content
            self.thumbnail_canvas_frame.grid()
            self.thumbnail_info_label.grid()
            # Update button to show down arrow (expanded)
            self.preview_toggle_button.config(text="▼")
    
    def on_treeview_select(self, event=None):
        """Handle treeview selection event to update thumbnail"""
        selection = self.results_tree.selection()
        if not selection:
            # Clear thumbnail if nothing is selected
            self.clear_thumbnail()
            return
        
        # Get the file path from the selected item
        item = selection[0]
        values = self.results_tree.item(item, "values")
        
        if not values or len(values) == 0:
            self.clear_thumbnail()
            return
        
        file_path_str = values[0]
        if not file_path_str:
            self.clear_thumbnail()
            return
        
        # Load and display thumbnail
        self.load_thumbnail(file_path_str)
    
    def clear_thumbnail(self):
        """Clear the thumbnail display"""
        # Clear canvas
        self.thumbnail_canvas.delete("all")
        # Recreate placeholder text
        self.thumbnail_text_id = self.thumbnail_canvas.create_text(
            self.THUMBNAIL_WIDTH // 2, 
            self.THUMBNAIL_HEIGHT // 2,
            text="Select a file to preview",
            font=('Segoe UI', 9),
            fill='gray'
        )
        self.thumbnail_info_var.set("")
        self.current_thumbnail_image = None
        self.thumbnail_canvas_id = None
    
    def load_thumbnail(self, file_path_str):
        """Load and display thumbnail for the given file path"""
        try:
            file_path = Path(file_path_str)
            if not file_path.exists():
                self.thumbnail_canvas.delete("all")
                self.thumbnail_canvas.create_text(
                    self.THUMBNAIL_WIDTH // 2, 
                    self.THUMBNAIL_HEIGHT // 2,
                    text="File not found",
                    font=('Segoe UI', 9),
                    fill='red'
                )
                self.thumbnail_info_var.set("")
                return
            
            # Find the file info to determine file type
            file_info = None
            if hasattr(self, 'found_files') and hasattr(self, 'file_infos'):
                try:
                    idx = self.found_files.index(file_path)
                    file_info = self.file_infos[idx]
                except (ValueError, IndexError):
                    pass
            
            # Determine file type
            is_photo = file_info.get('is_photo', False) if file_info else False
            is_video = file_info.get('is_video', False) if file_info else False
            is_pdf = file_info.get('is_pdf', False) if file_info else False
            
            # Get file size for display
            try:
                file_size = file_path.stat().st_size
                size_mb = file_size / (1024 * 1024)
                size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{file_size / 1024:.2f} KB"
            except:
                size_str = "Unknown size"
            
            # Update file info label
            file_name = file_path.name
            file_type_str = "Photo" if is_photo else ("Video" if is_video else ("PDF" if is_pdf else "File"))
            self.thumbnail_info_var.set(f"{file_name}\n{file_type_str} • {size_str}")
            
            # Load thumbnail based on file type
            if is_photo and PIL_AVAILABLE:
                self.load_photo_thumbnail(file_path)
            elif is_video:
                self.load_video_thumbnail(file_path)
            elif is_pdf:
                self.load_pdf_thumbnail(file_path)
            else:
                # Unsupported or no PIL available
                self.thumbnail_canvas.delete("all")
                if not PIL_AVAILABLE and is_photo:
                    self.thumbnail_canvas.create_text(
                        self.THUMBNAIL_WIDTH // 2, 
                        self.THUMBNAIL_HEIGHT // 2,
                        text="Install Pillow\n(pip install Pillow)\nto preview images",
                        font=('Segoe UI', 9),
                        fill='gray',
                        justify=tk.CENTER
                    )
                else:
                    self.thumbnail_canvas.create_text(
                        self.THUMBNAIL_WIDTH // 2, 
                        self.THUMBNAIL_HEIGHT // 2,
                        text="Preview not available\nfor this file type",
                        font=('Segoe UI', 9),
                        fill='gray',
                        justify=tk.CENTER
                    )
                    
        except Exception as e:
            self.thumbnail_canvas.delete("all")
            self.thumbnail_canvas.create_text(
                self.THUMBNAIL_WIDTH // 2, 
                self.THUMBNAIL_HEIGHT // 2,
                text=f"Error loading preview:\n{str(e)}",
                font=('Segoe UI', 9),
                fill='red',
                justify=tk.CENTER
            )
            self.thumbnail_info_var.set("")
    
    def load_photo_thumbnail(self, file_path):
        """Load and display photo thumbnail with fixed 16:9 aspect ratio"""
        try:
            # Load and resize image to fit within 16:9 bounds
            img = Image.open(file_path)
            
            # Calculate size maintaining aspect ratio and fitting within 16:9 bounds
            img_width, img_height = img.size
            img_aspect = img_width / img_height
            target_aspect = 16 / 9
            
            if img_aspect > target_aspect:
                # Image is wider, fit to width
                new_width = self.THUMBNAIL_WIDTH
                new_height = int(self.THUMBNAIL_WIDTH / img_aspect)
            else:
                # Image is taller, fit to height
                new_height = self.THUMBNAIL_HEIGHT
                new_width = int(self.THUMBNAIL_HEIGHT * img_aspect)
            
            # Resize image (use LANCZOS for quality)
            try:
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            except AttributeError:
                # Older PIL versions use Image.LANCZOS directly
                img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert to PhotoImage for Tkinter
            photo = ImageTk.PhotoImage(img)
            
            # Clear canvas and display image
            self.thumbnail_canvas.delete("all")
            # Center the image on the canvas
            x_pos = self.THUMBNAIL_WIDTH // 2
            y_pos = self.THUMBNAIL_HEIGHT // 2
            self.thumbnail_canvas_id = self.thumbnail_canvas.create_image(
                x_pos, y_pos, anchor=tk.CENTER, image=photo
            )
            self.current_thumbnail_image = photo  # Keep reference
            
        except Exception as e:
            self.thumbnail_canvas.delete("all")
            self.thumbnail_canvas.create_text(
                self.THUMBNAIL_WIDTH // 2, 
                self.THUMBNAIL_HEIGHT // 2,
                text=f"Error loading image:\n{str(e)}",
                font=('Segoe UI', 9),
                fill='red',
                justify=tk.CENTER
            )
    
    def load_video_thumbnail(self, file_path):
        """Load and display video thumbnail (placeholder for now)"""
        # For videos, we could use ffmpeg or Windows thumbnail extraction
        # For now, just show a placeholder
        self.thumbnail_canvas.delete("all")
        self.thumbnail_canvas.create_text(
            self.THUMBNAIL_WIDTH // 2, 
            self.THUMBNAIL_HEIGHT // 2,
            text="📹 Video File\n\nVideo preview requires\nadditional libraries",
            font=('Segoe UI', 9),
            fill='gray',
            justify=tk.CENTER
        )
    
    def load_pdf_thumbnail(self, file_path):
        """Load and display PDF thumbnail (placeholder for now)"""
        # For PDFs, we could use pdf2image or similar
        # For now, just show a placeholder
        self.thumbnail_canvas.delete("all")
        self.thumbnail_canvas.create_text(
            self.THUMBNAIL_WIDTH // 2, 
            self.THUMBNAIL_HEIGHT // 2,
            text="📄 PDF File\n\nPDF preview requires\nadditional libraries",
            font=('Segoe UI', 9),
            fill='gray',
            justify=tk.CENTER
        )
    
    def edit_exclusion(self):
        """Edit the selected excluded folder path"""
        selection = self.excluded_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a folder to edit")
            return
        
        index = selection[0]
        folder_str = self.excluded_listbox.get(index)
        folder_path = Path(folder_str)
        
        # Create a dialog to edit the path
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Excluded Folder")
        edit_window.geometry("500x100")
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        ttk.Label(edit_window, text="Folder Path:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        path_var = tk.StringVar(value=str(folder_path))
        path_entry = ttk.Entry(edit_window, textvariable=path_var, width=55)
        path_entry.grid(row=0, column=1, padx=(0, 12), pady=12, sticky=(tk.W, tk.E))
        edit_window.columnconfigure(1, weight=1)
        
        def save_changes():
            new_path_str = path_var.get().strip()
            if not new_path_str:
                messagebox.showwarning("Warning", "Path cannot be empty")
                return
            
            # Remove old path and add new path using core
            self.core.remove_excluded_folder(folder_str)
            self.core.add_excluded_folder(new_path_str)
            
            # Save excluded folders to file
            self.save_excluded_folders()
            
            # Reapply exclusions to update the display
            self.apply_exclusions()
            edit_window.destroy()
        
        def cancel():
            edit_window.destroy()
        
        def on_enter(event):
            """Handle Enter key press"""
            save_changes()
        
        # Bind Enter key to save
        path_entry.bind('<Return>', on_enter)
        edit_window.bind('<Return>', on_enter)
        
        button_frame = ttk.Frame(edit_window)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(0, 12))
        ttk.Button(button_frame, text="Save", command=save_changes, width=12).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(button_frame, text="Cancel", command=cancel, width=12).grid(row=0, column=1, padx=0)
        
        path_entry.focus()
        path_entry.select_range(0, tk.END)
    
    def remove_exclusion(self):
        """Remove the selected folder from exclusions"""
        selection = self.excluded_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a folder to remove from exclusions")
            return
        
        index = selection[0]
        folder_str = self.excluded_listbox.get(index)
        
        # Remove from excluded folders using core
        self.core.remove_excluded_folder(folder_str)
        
        # Save excluded folders to file
        self.save_excluded_folders()
        
        # Reapply exclusions to update the display
        self.apply_exclusions()
    
    def clear_all_exclusions(self):
        """Clear all folder exclusions"""
        if not self.core.excluded_folders:
            messagebox.showinfo("Info", "No folders are currently excluded")
            return
        
        result = messagebox.askyesno("Clear Exclusions", 
                                     f"Are you sure you want to clear all {len(self.core.excluded_folders)} folder exclusions?")
        if result:
            self.core.clear_excluded_folders()
            # Save excluded folders to file
            self.save_excluded_folders()
            self.apply_exclusions()
    
    def load_excluded_folders(self):
        """Load excluded folders from JSON file"""
        try:
            if self.excluded_folders_file.exists():
                with open(self.excluded_folders_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    excluded_folders = data.get('excluded_folders', [])
                    # Add each folder to the core
                    for folder_path in excluded_folders:
                        self.core.add_excluded_folder(folder_path)
        except (json.JSONDecodeError, IOError, OSError) as e:
            # If file is corrupted or can't be read, just start with empty list
            print(f"Warning: Could not load excluded folders: {e}")
    
    def save_excluded_folders(self):
        """Save excluded folders to JSON file"""
        try:
            # Convert Path objects to strings for JSON serialization
            excluded_folders = [str(folder) for folder in self.core.excluded_folders]
            data = {
                'excluded_folders': excluded_folders
            }
            with open(self.excluded_folders_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            # If we can't save, show a warning but don't crash
            print(f"Warning: Could not save excluded folders: {e}")
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

