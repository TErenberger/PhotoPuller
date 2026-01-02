"""
File organizer module - copies files to organized folder structure
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import hashlib
import time

class FileOrganizer:
    """Organizes and copies files to a destination with sensible folder structure"""
    
    def __init__(self, destination_root: str):
        """
        Initialize organizer
        
        Args:
            destination_root: Root directory where files will be copied
        """
        self.destination_root = Path(destination_root)
        self.destination_root.mkdir(parents=True, exist_ok=True)
        self.copy_stats = {
            'total': 0,
            'copied': 0,
            'skipped': 0,
            'errors': 0,
            'duplicates': 0
        }
        self.processed_files = {}  # Track file hashes to avoid duplicates
    
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file for duplicate detection"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (OSError, PermissionError):
            return ""
    
    def is_from_downloads(self, file_path: Path) -> bool:
        """
        Check if file path contains 'downloads' folder (case-insensitive)
        
        Returns True if file is from a downloads folder
        """
        path_str = str(file_path).lower()
        path_parts = path_str.split(os.sep)
        return 'downloads' in path_parts
    
    def organize_by_date(self, file_path: Path, file_info: dict) -> Path:
        """
        Organize file by date (year/month structure)
        
        Returns destination path
        """
        # Check if file is from downloads folder - place directly in Downloads folder
        if self.is_from_downloads(file_path):
            dest_dir = self.destination_root / "Downloads"
            dest_dir.mkdir(parents=True, exist_ok=True)
            return dest_dir / file_path.name
        
        # Get modification date or creation date
        date = file_info.get('modified', file_info.get('created', datetime.now()))
        
        # Create folder structure: Year/Month
        year = date.year
        month = f"{date.month:02d}"
        
        # Determine subfolder based on file type
        if file_info.get('is_photo'):
            subfolder = "Photos"
        elif file_info.get('is_video'):
            subfolder = "Videos"
        elif file_info.get('is_pdf'):
            subfolder = "PDFs"
        else:
            subfolder = "Media"
        
        dest_dir = self.destination_root / subfolder / str(year) / month
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        return dest_dir / file_path.name
    
    def organize_by_source(self, file_path: Path, file_info: dict) -> Path:
        """
        Organize file by source drive/folder
        
        Returns destination path
        """
        # Check if file is from downloads folder - place directly in Downloads folder
        if self.is_from_downloads(file_path):
            dest_dir = self.destination_root / "Downloads"
            dest_dir.mkdir(parents=True, exist_ok=True)
            return dest_dir / file_path.name
        
        # Get the drive letter or top-level folder name
        parts = Path(file_path).parts
        if len(parts) > 0:
            source_name = parts[0].replace(':', '').replace('\\', '')
        else:
            source_name = "Unknown"
        
        # Determine subfolder based on file type
        if file_info.get('is_photo'):
            subfolder = "Photos"
        elif file_info.get('is_video'):
            subfolder = "Videos"
        elif file_info.get('is_pdf'):
            subfolder = "PDFs"
        else:
            subfolder = "Media"
        
        dest_dir = self.destination_root / subfolder / source_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        return dest_dir / file_path.name
    
    def handle_duplicate_name(self, dest_path: Path) -> Path:
        """Handle duplicate filenames by appending a number"""
        if not dest_path.exists():
            return dest_path
        
        stem = dest_path.stem
        suffix = dest_path.suffix
        parent = dest_path.parent
        
        counter = 1
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
    
    def copy_file_with_progress(self, source: Path, dest: Path, 
                                file_size: int, 
                                file_progress_callback=None) -> bool:
        """
        Copy a file with progress tracking
        
        Args:
            source: Source file path
            dest: Destination file path
            file_size: Size of the file in bytes
            file_progress_callback: Optional callback(bytes_copied, total_bytes, copy_rate_mbps)
        
        Returns:
            True if successful, False otherwise
        """
        chunk_size = 1024 * 1024  # 1 MB chunks
        bytes_copied = 0
        start_time = time.time()
        last_update_time = start_time
        
        try:
            with open(source, 'rb') as src, open(dest, 'wb') as dst:
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    
                    dst.write(chunk)
                    bytes_copied += len(chunk)
                    
                    # Update progress periodically (every 0.1 seconds or so)
                    current_time = time.time()
                    if current_time - last_update_time >= 0.1 or bytes_copied == file_size:
                        elapsed = current_time - start_time
                        copy_rate = (bytes_copied / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                        
                        if file_progress_callback:
                            file_progress_callback(bytes_copied, file_size, copy_rate)
                        
                        last_update_time = current_time
            
            # Preserve file metadata
            shutil.copystat(source, dest)
            return True
            
        except Exception:
            # Clean up partial file on error
            if dest.exists():
                try:
                    dest.unlink()
                except:
                    pass
            return False
    
    def copy_file(self, file_path: Path, file_info: dict, 
                  organize_method: str = 'date', 
                  progress_callback=None,
                  file_progress_callback=None) -> Dict[str, any]:
        """
        Copy a file to the destination with organization
        
        Args:
            file_path: Source file path
            file_info: File information dictionary
            organize_method: 'date' or 'source'
            progress_callback: Optional callback function(current_file, stats)
            file_progress_callback: Optional callback function(bytes_copied, total_bytes, copy_rate_mbps)
        
        Returns:
            Dictionary with copy result information
        """
        self.copy_stats['total'] += 1
        
        try:
            # Check for duplicates by hash
            file_hash = self.get_file_hash(file_path)
            if file_hash and file_hash in self.processed_files:
                self.copy_stats['duplicates'] += 1
                result = {
                    'status': 'duplicate',
                    'source': str(file_path),
                    'existing': self.processed_files[file_hash]
                }
                if progress_callback:
                    progress_callback(str(file_path), self.copy_stats, 'duplicate')
                return result
            
            # Determine destination path
            if organize_method == 'date':
                dest_path = self.organize_by_date(file_path, file_info)
            else:
                dest_path = self.organize_by_source(file_path, file_info)
            
            # Handle duplicate filenames
            dest_path = self.handle_duplicate_name(dest_path)
            
            # Check if file already exists at destination
            if dest_path.exists():
                # Compare sizes
                if file_path.stat().st_size == dest_path.stat().st_size:
                    self.copy_stats['skipped'] += 1
                    result = {
                        'status': 'skipped',
                        'source': str(file_path),
                        'destination': str(dest_path),
                        'reason': 'File already exists'
                    }
                    if progress_callback:
                        progress_callback(str(file_path), self.copy_stats, 'skipped')
                    return result
            
            # Copy the file with progress tracking
            file_size = file_path.stat().st_size
            success = self.copy_file_with_progress(
                file_path, dest_path, file_size, file_progress_callback
            )
            
            if success:
                self.copy_stats['copied'] += 1
                
                # Track processed file
                if file_hash:
                    self.processed_files[file_hash] = str(dest_path)
                
                # Update progress with status
                if progress_callback:
                    progress_callback(str(file_path), self.copy_stats, 'copied')
                
                return {
                    'status': 'copied',
                    'source': str(file_path),
                    'destination': str(dest_path)
                }
            else:
                raise Exception("File copy failed")
            
        except PermissionError as e:
            self.copy_stats['errors'] += 1
            result = {
                'status': 'error',
                'source': str(file_path),
                'error': f'Permission denied: {e}'
            }
            if progress_callback:
                progress_callback(str(file_path), self.copy_stats, 'error')
            return result
        except Exception as e:
            self.copy_stats['errors'] += 1
            result = {
                'status': 'error',
                'source': str(file_path),
                'error': str(e)
            }
            if progress_callback:
                progress_callback(str(file_path), self.copy_stats, 'error')
            return result
    
    def copy_files(self, files: List[Path], file_infos: List[dict],
                   organize_method: str = 'date',
                   progress_callback=None,
                   file_progress_callback=None) -> List[Dict]:
        """
        Copy multiple files
        
        Args:
            files: List of source file paths
            file_infos: List of file information dictionaries
            organize_method: 'date' or 'source'
            progress_callback: Optional callback function(current_file, stats)
            file_progress_callback: Optional callback function(bytes_copied, total_bytes, copy_rate_mbps)
        
        Returns:
            List of copy result dictionaries
        """
        results = []
        
        for file_path, file_info in zip(files, file_infos):
            result = self.copy_file(file_path, file_info, organize_method, 
                                  progress_callback, file_progress_callback)
            results.append(result)
        
        return results


