"""
File scanner module - finds photos and videos on a drive
"""
import os
from pathlib import Path
from typing import List, Set
from datetime import datetime

class FileScanner:
    """Scans drives for photo and video files"""
    
    # Common photo extensions
    PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', 
                       '.webp', '.heic', '.heif'}
    
    # Common video extensions
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', 
                       '.m4v', '.mpg', '.mpeg', '.3gp', '.3g2', '.asf', '.rm', 
                       '.rmvb', '.vob', '.ts', '.mts', '.m2ts'}
    
    # PDF extensions
    PDF_EXTENSIONS = {'.pdf'}
    
    # Paths to exclude (system files, program files, temp files)
    EXCLUDED_PATHS = {
        'windows', 'program files', 'program files (x86)', 'programdata',
        'appdata', 'temp', 'tmp', '$recycle.bin', 'system volume information',
        'pagefile.sys', 'hiberfil.sys', 'swapfile.sys', 'recovery',
        'perflogs', 'msocache', 'intel', 'amd', 'nvidia',
        'internet explorer', 'microsoft edge', 'chrome', 'firefox',
        'opera', 'safari', 'cache', 'cookies', 'history',
        'temporary internet files', 'content.ie5', 'local settings',
        'application data', 'roaming', 'local', 'temp', 'tmp', 'node_modules'
    }
    
    def __init__(self):
        self.found_files: List[Path] = []
        self.scan_stats = {
            'total_scanned': 0,
            'photos_found': 0,
            'videos_found': 0,
            'pdfs_found': 0,
            'excluded': 0
        }
    
    def is_photo(self, file_path: Path) -> bool:
        """Check if file is a photo"""
        return file_path.suffix.lower() in self.PHOTO_EXTENSIONS
    
    def is_video(self, file_path: Path) -> bool:
        """Check if file is a video"""
        return file_path.suffix.lower() in self.VIDEO_EXTENSIONS
    
    def is_pdf(self, file_path: Path) -> bool:
        """Check if file is a PDF"""
        return file_path.suffix.lower() in self.PDF_EXTENSIONS
    
    def is_media_file(self, file_path: Path) -> bool:
        """Check if file is a photo, video, or PDF"""
        return self.is_photo(file_path) or self.is_video(file_path) or self.is_pdf(file_path)
    
    def should_exclude_path(self, file_path: Path) -> bool:
        """
        Determine if a path should be excluded based on common system/program locations
        """
        path_str = str(file_path).lower()
        path_parts = path_str.split(os.sep)
        
        # Check each part of the path
        for part in path_parts:
            # Exclude if any part matches excluded patterns
            if any(excluded in part.lower() for excluded in self.EXCLUDED_PATHS):
                return True
            
            # Exclude hidden/system directories
            if part.startswith('.') and part != '.':
                return True
        
        # Additional checks for common patterns
        # Exclude thumbnail caches
        if 'thumbs.db' in path_str or 'ehthumbs.db' in path_str:
            return True
        
        # Exclude very small files (likely thumbnails or icons)
        # Only check size for files, not directories
        if file_path.is_file():
            try:
                if file_path.stat().st_size < 1024:  # Less than 1KB
                    return True
            except (OSError, PermissionError):
                # If we can't check the size, don't exclude - let it through
                pass
        
        return False
    
    def scan_drive(self, drive_path: str, progress_callback=None) -> List[Path]:
        """
        Scan a drive for photos and videos
        
        Args:
            drive_path: Path to the drive to scan (e.g., 'C:\\' or 'D:\\')
            progress_callback: Optional callback function(current_path, stats)
        
        Returns:
            List of Path objects for found media files
        """
        self.found_files = []
        self.scan_stats = {
            'total_scanned': 0,
            'photos_found': 0,
            'videos_found': 0,
            'pdfs_found': 0,
            'excluded': 0
        }
        
        drive = Path(drive_path)
        if not drive.exists():
            raise ValueError(f"Drive path does not exist: {drive_path}")
        
        # Scan recursively
        try:
            for root, dirs, files in os.walk(drive_path):
                # Update progress
                if progress_callback:
                    progress_callback(root, self.scan_stats)
                
                # Filter out excluded directories to avoid traversing them
                dirs[:] = [d for d in dirs if not self.should_exclude_path(Path(root) / d)]
                
                for file in files:
                    self.scan_stats['total_scanned'] += 1
                    file_path = Path(root) / file
                    
                    # Check if it's a media file
                    if self.is_media_file(file_path):
                        # Check if it should be excluded
                        if not self.should_exclude_path(file_path):
                            self.found_files.append(file_path)
                            if self.is_photo(file_path):
                                self.scan_stats['photos_found'] += 1
                            elif self.is_video(file_path):
                                self.scan_stats['videos_found'] += 1
                            elif self.is_pdf(file_path):
                                self.scan_stats['pdfs_found'] += 1
                        else:
                            self.scan_stats['excluded'] += 1
                            
        except PermissionError as e:
            # Some directories may be inaccessible, continue scanning
            print(f"Permission denied: {e}")
        except KeyboardInterrupt:
            print("Scan interrupted by user")
        
        return self.found_files
    
    def get_file_info(self, file_path: Path) -> dict:
        """Get information about a file"""
        try:
            stat = file_path.stat()
            return {
                'path': str(file_path),
                'name': file_path.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'is_photo': self.is_photo(file_path),
                'is_video': self.is_video(file_path),
                'is_pdf': self.is_pdf(file_path)
            }
        except (OSError, PermissionError) as e:
            return {'error': str(e)}

