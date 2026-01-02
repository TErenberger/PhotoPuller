"""
GUI module for PhotoPuller application
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import subprocess
import os
from photopuller_core import PhotoPullerCore

class PhotoPullerGUI:
    """Main GUI application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PhotoPuller - Find & Organize Photos & Videos")
        self.root.geometry("1200x800")
        
        self.core = PhotoPullerCore()  # Use core class for business logic
        self.file_to_item_map = {}  # Map file paths to treeview items
        self.file_copy_status = {}  # Track copy status for each file
        self.scan_photos = tk.BooleanVar(value=True)  # Filter for photos
        self.scan_videos = tk.BooleanVar(value=True)  # Filter for videos
        self.scan_pdfs = tk.BooleanVar(value=True)  # Filter for PDFs
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)  # Results column gets more space
        main_frame.rowconfigure(0, weight=1)
        
        # Left column container
        left_column = ttk.Frame(main_frame)
        left_column.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_column.columnconfigure(0, weight=1)
        
        # Source drive selection
        source_frame = ttk.LabelFrame(left_column, text="Source Drive", padding="10")
        source_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.source_var = tk.StringVar(value="C:\\")
        source_entry = ttk.Entry(source_frame, textvariable=self.source_var, width=30)
        source_entry.grid(row=0, column=0, padx=5)
        
        ttk.Button(source_frame, text="Browse...", 
                  command=self.browse_source).grid(row=0, column=1, padx=5)
        
        ttk.Button(source_frame, text="Scan Drive", 
                  command=self.start_scan).grid(row=0, column=2, padx=5)
        
        # File type filters
        filter_frame = ttk.Frame(source_frame)
        filter_frame.grid(row=1, column=0, columnspan=3, pady=5, sticky=tk.W)
        
        ttk.Label(filter_frame, text="Scan for:").grid(row=0, column=0, padx=5)
        ttk.Checkbutton(filter_frame, text="Photos", variable=self.scan_photos).grid(row=0, column=1, padx=5)
        ttk.Checkbutton(filter_frame, text="Videos", variable=self.scan_videos).grid(row=0, column=2, padx=5)
        ttk.Checkbutton(filter_frame, text="PDFs", variable=self.scan_pdfs).grid(row=0, column=3, padx=5)
        
        # Scan progress
        progress_frame = ttk.LabelFrame(left_column, text="Scan Progress", padding="10")
        progress_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        progress_frame.columnconfigure(0, weight=1)
        
        self.scan_progress_var = tk.StringVar(value="Ready to scan")
        progress_label = ttk.Label(progress_frame, textvariable=self.scan_progress_var, 
                                  anchor=tk.W, justify=tk.LEFT)
        progress_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # Current file being scanned (on its own line)
        self.scan_current_file_var = tk.StringVar(value="")
        current_file_label = ttk.Label(progress_frame, textvariable=self.scan_current_file_var, 
                                       anchor=tk.W, justify=tk.LEFT, foreground="gray")
        current_file_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        
        self.scan_progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.scan_progress_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Excluded folders section
        excluded_frame = ttk.LabelFrame(left_column, text="Excluded Folders", padding="10")
        excluded_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.excluded_listbox = tk.Listbox(excluded_frame, height=3)
        self.excluded_listbox.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        excluded_frame.columnconfigure(0, weight=1)
        
        # Bind double-click to edit exclusion
        self.excluded_listbox.bind('<Double-Button-1>', lambda e: self.edit_exclusion())
        
        ttk.Button(excluded_frame, text="Edit", 
                  command=self.edit_exclusion).grid(row=1, column=0, padx=5, pady=2)
        ttk.Button(excluded_frame, text="Remove", 
                  command=self.remove_exclusion).grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(excluded_frame, text="Clear All", 
                  command=self.clear_all_exclusions).grid(row=1, column=2, padx=5, pady=2)
        
        # Destination selection
        dest_frame = ttk.LabelFrame(left_column, text="Destination", padding="10")
        dest_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.dest_var = tk.StringVar()
        dest_entry = ttk.Entry(dest_frame, textvariable=self.dest_var, width=30)
        dest_entry.grid(row=0, column=0, padx=5)
        # Trace destination changes to update copy button state
        self.dest_var.trace_add('write', lambda *args: self.update_copy_button_state())
        
        ttk.Button(dest_frame, text="Browse...", 
                  command=self.browse_destination).grid(row=0, column=1, padx=5)
        
        # Organization method
        org_frame = ttk.Frame(dest_frame)
        org_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        ttk.Label(org_frame, text="Organize by:").grid(row=0, column=0, padx=2)
        self.org_method_var = tk.StringVar(value="date")
        ttk.Radiobutton(org_frame, text="Date", variable=self.org_method_var, 
                       value="date").grid(row=0, column=1, padx=2)
        ttk.Radiobutton(org_frame, text="Source", variable=self.org_method_var, 
                       value="source").grid(row=0, column=2, padx=2)
        
        # Copy button
        self.copy_button = ttk.Button(dest_frame, text="Copy Files", 
                                      command=self.start_copy, state=tk.DISABLED)
        self.copy_button.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Copy progress
        copy_progress_frame = ttk.LabelFrame(left_column, text="Copy Progress", padding="10")
        copy_progress_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        copy_progress_frame.columnconfigure(0, weight=1)
        
        self.copy_progress_var = tk.StringVar(value="")
        ttk.Label(copy_progress_frame, textvariable=self.copy_progress_var).grid(row=0, column=0, sticky=tk.W)
        
        # Overall progress bar
        self.copy_progress_bar = ttk.Progressbar(copy_progress_frame, mode='determinate')
        self.copy_progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Current file being copied
        self.copy_current_file_var = tk.StringVar(value="")
        current_file_label = ttk.Label(copy_progress_frame, textvariable=self.copy_current_file_var, 
                                      anchor=tk.W, justify=tk.LEFT, foreground="gray")
        current_file_label.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # Per-file progress bar
        self.copy_file_progress_bar = ttk.Progressbar(copy_progress_frame, mode='determinate')
        self.copy_file_progress_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Copy rate display
        self.copy_rate_var = tk.StringVar(value="")
        copy_rate_label = ttk.Label(copy_progress_frame, textvariable=self.copy_rate_var, 
                                   anchor=tk.W, justify=tk.LEFT, foreground="blue")
        copy_rate_label.grid(row=4, column=0, sticky=tk.W, pady=2)
        
        # Right column - Results
        results_frame = ttk.LabelFrame(main_frame, text="Scan Results", padding="10")
        results_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Results treeview
        tree_frame = ttk.Frame(results_frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        self.results_tree = ttk.Treeview(tree_frame, columns=("File Path", "Type", "Size", "Date"), show="tree headings", height=15)
        self.results_tree.heading("#0", text="Status")
        self.results_tree.heading("File Path", text="File Path")
        self.results_tree.heading("Type", text="Type")
        self.results_tree.heading("Size", text="Size")
        self.results_tree.heading("Date", text="Modified")
        
        self.results_tree.column("#0", width=90)
        self.results_tree.column("File Path", width=280)
        self.results_tree.column("Type", width=70)
        self.results_tree.column("Size", width=90)
        self.results_tree.column("Date", width=130)
        
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
        
        # Stats label
        self.stats_var = tk.StringVar(value="No files found yet")
        ttk.Label(results_frame, textvariable=self.stats_var).grid(row=1, column=0, pady=5)
    
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
    
    def apply_exclusions(self):
        """Filter results based on excluded folders"""
        # Use core's files and infos
        self.found_files = self.core.found_files
        self.file_infos = self.core.file_infos
        self.all_found_files = self.core.all_found_files
        self.all_file_infos = self.core.all_file_infos
        
        # Update excluded folders listbox
        self.excluded_listbox.delete(0, tk.END)
        for folder in sorted(self.core.excluded_folders):
            self.excluded_listbox.insert(tk.END, str(folder))
        
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
            
            # Reapply exclusions to update the display
            self.apply_exclusions()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to exclude folder:\n{str(e)}")
    
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
        path_entry = ttk.Entry(edit_window, textvariable=path_var, width=50)
        path_entry.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        edit_window.columnconfigure(1, weight=1)
        
        def save_changes():
            new_path_str = path_var.get().strip()
            if not new_path_str:
                messagebox.showwarning("Warning", "Path cannot be empty")
                return
            
            # Remove old path and add new path using core
            self.core.remove_excluded_folder(folder_str)
            self.core.add_excluded_folder(new_path_str)
            
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
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Save", command=save_changes).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel).grid(row=0, column=1, padx=5)
        
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
            self.apply_exclusions()
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

