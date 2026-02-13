"""
Drive Organizer v2 — CLI Entry Point
======================================
Main entry point for the Drive Organizer application.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from googleapiclient.discovery import build

from .config import VERSION, FOLDER_ARCHITECTURE, DriveOrganizerConfig
from .utils import C, print_banner, setup_logging
from .auth import DriveAuthenticator
from .operations import DriveOperations
from .categorizer import DriveFile, FileCategorizer, DuplicateDetector, ScanReport
from .music_organizer import MusicOrganizer
from .migrator import FolderArchitect, FileMigrator
from .reporter import ReportGenerator


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Drive Organizer v2 — Google Drive Analysis, Reorganization & Migration",
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=True,
        help="Show what would happen without making changes (default: True)",
    )
    parser.add_argument(
        "--execute", action="store_true",
        help="Actually execute migrations (disables dry-run)",
    )
    parser.add_argument(
        "--scan-only", action="store_true",
        help="Only scan and report, don't plan migrations",
    )
    parser.add_argument(
        "--music-only", action="store_true",
        help="Only organize music files",
    )
    parser.add_argument(
        "--build-folders", action="store_true",
        help="Only build the folder architecture",
    )
    parser.add_argument(
        "--credentials", type=str, default="credentials.json",
        help="Path to OAuth credentials JSON",
    )
    parser.add_argument(
        "--token", type=str, default="token.json",
        help="Path to token file",
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to JSON config file",
    )
    parser.add_argument(
        "--output-dir", type=str, default=".",
        help="Directory for output reports",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--version", action="version", version=f"Drive Organizer v{VERSION}",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Load config
    if args.config:
        config = DriveOrganizerConfig.from_json(args.config)
    else:
        config = DriveOrganizerConfig()

    config.credentials_file = args.credentials
    config.token_file = args.token
    config.output_dir = args.output_dir
    config.dry_run = not args.execute
    config.verbose = args.verbose
    config.scan_only = args.scan_only
    config.music_only = args.music_only

    # Setup
    print_banner(VERSION)
    logger = setup_logging()
    logger.info(f"Drive Organizer v{VERSION} starting...")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")

    if config.dry_run:
        print(f"  {C.YELLOW}{C.BOLD}DRY RUN MODE — no changes will be made{C.RESET}\n")

    # Authenticate
    print(f"{C.CYAN}Authenticating with Google Drive API...{C.RESET}")
    auth = DriveAuthenticator(
        credentials_file=config.credentials_file,
        token_file=config.token_file,
        logger=logger,
    )
    creds = auth.authenticate()
    ops = DriveOperations(creds, config, logger)
    print(f"{C.GREEN}Authenticated successfully{C.RESET}\n")

    # Build folder architecture
    print(f"{C.CYAN}Building folder architecture...{C.RESET}")
    architect = FolderArchitect(ops, logger)
    folder_map = architect.build_architecture()
    print(f"{C.GREEN}Folder architecture ready ({len(folder_map)} folders){C.RESET}\n")

    if args.build_folders:
        print(f"{C.GREEN}{C.BOLD}Folder architecture built. Exiting.{C.RESET}\n")
        return

    # Scan all files
    print(f"{C.CYAN}Scanning all files in Drive...{C.RESET}")
    raw_files = ops.list_all_files()
    logger.info(f"Found {len(raw_files)} files")

    # Convert to DriveFile objects
    files = {}
    folders = {}
    for rf in raw_files:
        mime = rf.get("mimeType", "")
        if mime == "application/vnd.google-apps.folder":
            folders[rf["id"]] = rf
        else:
            df = DriveFile(
                id=rf["id"],
                name=rf.get("name", ""),
                mime_type=mime,
                size=int(rf.get("size", 0)),
                md5_checksum=rf.get("md5Checksum", ""),
                parents=rf.get("parents", []),
                created_time=rf.get("createdTime", ""),
                modified_time=rf.get("modifiedTime", ""),
            )
            files[rf["id"]] = df

    # Generate scan report
    reporter = ReportGenerator(logger)
    scan_report = reporter.generate_scan_report(files, folders)
    reporter.print_scan_report(scan_report)

    if args.scan_only:
        reporter.export_json(scan_report, [], {}, f"{config.output_dir}/scan_report.json")
        reporter.export_markdown(scan_report, [], {}, f"{config.output_dir}/scan_report.md")
        print(f"{C.GREEN}{C.BOLD}Scan complete. Reports saved.{C.RESET}\n")
        return

    # Plan migration
    print(f"{C.CYAN}Planning file migration...{C.RESET}")
    migrator = FileMigrator(ops, config, logger)
    actions = migrator.plan_migration(files, folder_map)
    migrator.save_plan(f"{config.output_dir}/migration_plan.json")

    # Execute migration
    stats = migrator.execute(folder_map, dry_run=config.dry_run)

    # Print summary
    reporter.print_migration_summary(actions, stats)
    reporter.export_json(scan_report, actions, stats, f"{config.output_dir}/drive_organizer_report.json")
    reporter.export_markdown(scan_report, actions, stats, f"{config.output_dir}/drive_organizer_report.md")

    print(f"{C.GREEN}{C.BOLD}Complete!{C.RESET} Reports saved to {config.output_dir}/\n")


if __name__ == "__main__":
    main()
