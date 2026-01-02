"""
PhotoPuller Core - Business logic for scanning and organizing files
Can be used with or without GUI
"""
from pathlib import Path
from typing import List, Set, Optional, Callable
from scanner import FileScanner
from organizer import FileOrganizer


class PhotoPullerCore:
    """Core PhotoPuller functionality that can run with or without GUI"""
    
    def __init__(self):
        self.scanner = FileScanner()
        self.organizer = None
        self.found_files = []
        self.file_infos = []
        self.excluded_folders = set()
        self.all_found_files = []
        self.all_file_infos = []
    
    def scan(self, source_path: str, 
             scan_photos: bool = True,
             scan_videos: bool = True,
             scan_pdfs: bool = True,
             excluded_folders: Optional[List[str]] = None,
             progress_callback: Optional[Callable] = None) -> List[Path]:
        """
        Scan for files
        
        Args:
            source_path: Path to scan
            scan_photos: Include photos in scan
            scan_videos: Include videos in scan
            scan_pdfs: Include PDFs in scan
            excluded_folders: List of folder paths to exclude
            progress_callback: Optional callback(current_path, stats)
        
        Returns:
            List of found file paths
        """
        # Validate at least one type is selected
        if not scan_photos and not scan_videos and not scan_pdfs:
            raise ValueError("At least one file type must be selected (photos, videos, or PDFs)")
        
        # Set excluded folders
        if excluded_folders:
            self.excluded_folders = {Path(f) for f in excluded_folders}
        else:
            self.excluded_folders = set()
        
        # Scan for files
        self.found_files = self.scanner.scan_drive(source_path, progress_callback)
        
        # Filter by file type
        filtered_files = []
        for file_path in self.found_files:
            is_photo = self.scanner.is_photo(file_path)
            is_video = self.scanner.is_video(file_path)
            is_pdf = self.scanner.is_pdf(file_path)
            
            if (scan_photos and is_photo) or (scan_videos and is_video) or (scan_pdfs and is_pdf):
                filtered_files.append(file_path)
        
        self.found_files = filtered_files
        
        # Get file info for each file
        self.file_infos = []
        for file_path in self.found_files:
            info = self.scanner.get_file_info(file_path)
            self.file_infos.append(info)
        
        # Apply exclusions
        self._apply_exclusions()
        
        # Store original results
        self.all_found_files = self.found_files.copy()
        self.all_file_infos = self.file_infos.copy()
        
        return self.found_files
    
    def _apply_exclusions(self):
        """Filter results based on excluded folders"""
        if not self.excluded_folders:
            return
        
        filtered_files = []
        filtered_infos = []
        
        for file_path, file_info in zip(self.found_files, self.file_infos):
            file_path_str = str(file_path)
            is_excluded = False
            
            for excluded_folder in self.excluded_folders:
                excluded_folder_str = str(excluded_folder)
                if file_path_str.lower().startswith(excluded_folder_str.lower()):
                    is_excluded = True
                    break
            
            if not is_excluded:
                filtered_files.append(file_path)
                filtered_infos.append(file_info)
        
        self.found_files = filtered_files
        self.file_infos = filtered_infos
    
    def add_excluded_folder(self, folder_path: str):
        """Add a folder to the exclusion list"""
        self.excluded_folders.add(Path(folder_path))
        self._apply_exclusions()
    
    def remove_excluded_folder(self, folder_path: str):
        """Remove a folder from the exclusion list"""
        folder = Path(folder_path)
        if folder in self.excluded_folders:
            self.excluded_folders.remove(folder)
            self._apply_exclusions()
    
    def clear_excluded_folders(self):
        """Clear all excluded folders"""
        self.excluded_folders.clear()
        self._apply_exclusions()
    
    def get_scan_stats(self) -> dict:
        """Get statistics about the scan"""
        total_size = sum(info.get('size', 0) for info in self.file_infos if 'error' not in info)
        photos_count = sum(1 for info in self.file_infos if info.get('is_photo', False) and 'error' not in info)
        videos_count = sum(1 for info in self.file_infos if info.get('is_video', False) and 'error' not in info)
        pdfs_count = sum(1 for info in self.file_infos if info.get('is_pdf', False) and 'error' not in info)
        
        return {
            'total_files': len(self.found_files),
            'photos': photos_count,
            'videos': videos_count,
            'pdfs': pdfs_count,
            'total_size_bytes': total_size,
            'total_size_gb': total_size / (1024 * 1024 * 1024),
            'excluded_count': len(self.all_found_files) - len(self.found_files)
        }
    
    def copy_files(self, destination: str,
                   organize_method: str = 'date',
                   dry_run: bool = False,
                   progress_callback: Optional[Callable] = None,
                   file_progress_callback: Optional[Callable] = None) -> List[dict]:
        """
        Copy files to destination
        
        Args:
            destination: Destination directory path
            organize_method: 'date' or 'source'
            dry_run: If True, don't actually copy files, just report what would be copied
            progress_callback: Optional callback(current_file, stats, copy_status=None)
            file_progress_callback: Optional callback(bytes_copied, total_bytes, copy_rate_mbps)
        
        Returns:
            List of copy result dictionaries
        """
        if not self.found_files:
            raise ValueError("No files to copy. Run scan() first.")
        
        if dry_run:
            # In dry-run mode, simulate copying without actually copying
            # Create a temporary organizer to determine destination paths
            temp_organizer = FileOrganizer(destination)
            results = []
            for file_path, file_info in zip(self.found_files, self.file_infos):
                if 'error' in file_info:
                    continue
                
                # Determine where file would be copied
                if organize_method == 'date':
                    dest_path = temp_organizer.organize_by_date(file_path, file_info)
                else:
                    dest_path = temp_organizer.organize_by_source(file_path, file_info)
                
                results.append({
                    'status': 'would_copy',
                    'source': str(file_path),
                    'destination': str(dest_path),
                    'size': file_info.get('size', 0)
                })
                
                if progress_callback:
                    # Simulate progress
                    stats = {
                        'total': len(self.found_files),
                        'copied': len(results),
                        'skipped': 0,
                        'errors': 0,
                        'duplicates': 0
                    }
                    progress_callback(str(file_path), stats, 'would_copy')
            
            return results
        
        # Normal copy mode
        self.organizer = FileOrganizer(destination)
        
        # The organizer's copy_file method already calls progress_callback with (current_file, stats, copy_status)
        # So we can pass it directly
        results = self.organizer.copy_files(
            self.found_files,
            self.file_infos,
            organize_method,
            progress_callback,
            file_progress_callback
        )
        
        return results
    
    def get_copy_stats(self) -> dict:
        """Get statistics about the copy operation"""
        if not self.organizer:
            return {}
        return self.organizer.copy_stats.copy()

