"""
PhotoPuller CLI - Command-line interface for headless operation
"""
import argparse
import sys
import json
from pathlib import Path
from photopuller_core import PhotoPullerCore


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='PhotoPuller - Find and organize photos, videos, and PDFs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan and copy photos and videos from C: to D:\\Backup
  python photopuller_cli.py -s C:\\ -d D:\\Backup --photos --videos
  
  # Dry run to see what would be copied
  python photopuller_cli.py -s C:\\ -d D:\\Backup --dry-run
  
  # Scan only PDFs with excluded folders
  python photopuller_cli.py -s C:\\ -d D:\\Backup --pdfs --exclude "C:\\Windows" "C:\\Program Files"
        """
    )
    
    parser.add_argument('-s', '--source', required=True,
                       help='Source path to scan (drive or directory)')
    parser.add_argument('-d', '--destination', required=True,
                       help='Destination path to copy files to')
    
    # File type filters
    parser.add_argument('--photos', action='store_true', default=False,
                       help='Include photos in scan')
    parser.add_argument('--videos', action='store_true', default=False,
                       help='Include videos in scan')
    parser.add_argument('--pdfs', action='store_true', default=False,
                       help='Include PDFs in scan')
    
    # Excluded folders
    parser.add_argument('--exclude', nargs='*', default=[],
                       help='List of folder paths to exclude')
    
    # Organization method
    parser.add_argument('--organize-by', choices=['date', 'source'], default='date',
                       help='Organization method: date (Year/Month) or source (by drive)')
    
    # Dry run
    parser.add_argument('--dry-run', action='store_true',
                       help='Scan and report what would be copied without actually copying')
    
    # Output format
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    
    # Quiet mode
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Suppress progress output')
    
    args = parser.parse_args()
    
    # Default to all file types if none specified
    scan_photos = args.photos if (args.photos or args.videos or args.pdfs) else True
    scan_videos = args.videos if (args.photos or args.videos or args.pdfs) else True
    scan_pdfs = args.pdfs if (args.photos or args.videos or args.pdfs) else True
    
    # Initialize core
    core = PhotoPullerCore()
    
    # Progress callback
    def progress_callback(current_path, stats):
        if not args.quiet:
            pdfs = stats.get('pdfs_found', 0)
            print(f"\rScanning: {current_path[:60]}... | "
                  f"Found: {stats['photos_found']} photos, {stats['videos_found']} videos, {pdfs} PDFs", 
                  end='', flush=True)
    
    try:
        # Scan
        if not args.quiet:
            print(f"Scanning: {args.source}")
            print("File types: ", end='')
            types = []
            if scan_photos:
                types.append("Photos")
            if scan_videos:
                types.append("Videos")
            if scan_pdfs:
                types.append("PDFs")
            print(", ".join(types))
            if args.exclude:
                print(f"Excluding: {', '.join(args.exclude)}")
            print()
        
        found_files = core.scan(
            args.source,
            scan_photos=scan_photos,
            scan_videos=scan_videos,
            scan_pdfs=scan_pdfs,
            excluded_folders=args.exclude,
            progress_callback=progress_callback
        )
        
        if not args.quiet:
            print()  # New line after progress
            print("Scan complete!")
        
        # Get stats
        stats = core.get_scan_stats()
        
        if not args.quiet:
            print(f"\nScan Results:")
            print(f"  Total files: {stats['total_files']}")
            print(f"  Photos: {stats['photos']}")
            print(f"  Videos: {stats['videos']}")
            print(f"  PDFs: {stats['pdfs']}")
            print(f"  Total size: {stats['total_size_gb']:.2f} GB")
            print(f"  Excluded: {stats['excluded_count']}")
        
        if not found_files:
            if not args.quiet:
                print("\nNo files found to copy.")
            return 0
        
        # Copy files
        if not args.quiet:
            mode = "DRY RUN - " if args.dry_run else ""
            print(f"\n{mode}Copying files to: {args.destination}")
            print(f"Organization method: {args.organize_by}")
        
        def copy_progress(current_file, copy_stats):
            if not args.quiet:
                print(f"\rCopying: {Path(current_file).name[:50]}... | "
                      f"Copied: {copy_stats['copied']}, Skipped: {copy_stats['skipped']}, "
                      f"Errors: {copy_stats['errors']}", end='', flush=True)
        
        results = core.copy_files(
            args.destination,
            organize_method=args.organize_by,
            dry_run=args.dry_run,
            progress_callback=copy_progress
        )
        
        if not args.quiet:
            print()  # New line after progress
        
        # Get copy stats
        copy_stats = core.get_copy_stats()
        
        if args.json:
            # Output JSON
            output = {
                'scan': stats,
                'copy': copy_stats if not args.dry_run else {'dry_run': True},
                'files': [
                    {
                        'source': str(f),
                        'destination': r.get('destination', ''),
                        'status': r.get('status', '')
                    }
                    for f, r in zip(found_files, results)
                ]
            }
            print(json.dumps(output, indent=2))
        else:
            # Output summary
            if not args.quiet:
                if args.dry_run:
                    print(f"\nDry run complete! Would copy {len(results)} files.")
                else:
                    print(f"\nCopy Results:")
                    print(f"  Copied: {copy_stats.get('copied', 0)}")
                    print(f"  Skipped: {copy_stats.get('skipped', 0)}")
                    print(f"  Errors: {copy_stats.get('errors', 0)}")
                    print(f"  Duplicates: {copy_stats.get('duplicates', 0)}")
        
        return 0
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        if not args.quiet:
            print("\n\nOperation cancelled by user.")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())


