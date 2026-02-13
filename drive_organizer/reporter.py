"""
Report Generator Module for Drive Organizer v2
================================================
Generates scan reports, migration summaries, and detailed analytics.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

from .categorizer import DriveFile, MigrationAction, ScanReport
from .utils import C, format_size


class ReportGenerator:
    """
    Generates comprehensive reports for Drive Organizer operations.
    Supports console output, JSON export, and Markdown export.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def generate_scan_report(
        self,
        files: Dict[str, DriveFile],
        folders: Dict[str, Any],
    ) -> ScanReport:
        """Generate a scan report from collected file data."""
        report = ScanReport()
        report.total_files = len(files)
        report.total_folders = len(folders) if isinstance(folders, dict) else 0

        ext_counts: Counter = Counter()
        for f in files.values():
            report.total_size_bytes += f.size
            ext = f.extension or "(no extension)"
            ext_counts[ext] += 1

            if f.is_duplicate:
                report.duplicate_count += 1
            if not f.suggested_destination:
                report.uncategorized_count += 1

            # Count by category
            from .config import (
                MUSIC_EXTENSIONS, IMAGE_EXTENSIONS,
                CODE_EXTENSIONS, DOCUMENT_EXTENSIONS,
            )
            if f.extension in MUSIC_EXTENSIONS:
                report.music_files += 1
            elif f.extension in IMAGE_EXTENSIONS:
                report.image_files += 1
            elif f.extension in CODE_EXTENSIONS:
                report.code_files += 1
            elif f.extension in DOCUMENT_EXTENSIONS:
                report.document_files += 1

        report.file_type_counts = dict(ext_counts.most_common())
        return report

    def print_scan_report(self, report: ScanReport) -> None:
        """Print a formatted scan report to console."""
        print(f"\n{C.BG_BLUE}{C.WHITE}{C.BOLD} SCAN REPORT {C.RESET}")
        print(f"{C.CYAN}{'─' * 60}{C.RESET}")
        print(f"  {C.GREEN}Total files   :{C.RESET} {C.BOLD}{report.total_files}{C.RESET}")
        print(f"  {C.GREEN}Total folders :{C.RESET} {C.BOLD}{report.total_folders}{C.RESET}")
        print(f"  {C.GREEN}Total size    :{C.RESET} {C.BOLD}{format_size(report.total_size_bytes)}{C.RESET}")
        print(f"  {C.YELLOW}Duplicates    :{C.RESET} {C.BOLD}{report.duplicate_count}{C.RESET}")
        print(f"  {C.YELLOW}Uncategorized :{C.RESET} {C.BOLD}{report.uncategorized_count}{C.RESET}")

        print(f"\n  {C.CYAN}{C.BOLD}File Categories:{C.RESET}")
        print(f"    Music files    : {report.music_files}")
        print(f"    Document files : {report.document_files}")
        print(f"    Image files    : {report.image_files}")
        print(f"    Code files     : {report.code_files}")

        if report.file_type_counts:
            print(f"\n  {C.CYAN}{C.BOLD}Top File Types:{C.RESET}")
            for ext, count in list(report.file_type_counts.items())[:15]:
                bar = "█" * min(count, 40)
                print(f"    {C.BLUE}{ext:<15}{C.RESET} {C.GREEN}{count:>5}{C.RESET} {C.MAGENTA}{bar}{C.RESET}")

        print(f"{C.CYAN}{'─' * 60}{C.RESET}\n")

    def print_migration_summary(
        self,
        actions: List[MigrationAction],
        stats: Dict[str, Any],
    ) -> None:
        """Print migration execution summary."""
        print(f"\n{C.BG_YELLOW}{C.WHITE}{C.BOLD} MIGRATION SUMMARY {C.RESET}")
        print(f"{C.CYAN}{'─' * 60}{C.RESET}")
        print(f"  {C.GREEN}Total planned  :{C.RESET} {C.BOLD}{stats.get('total_planned', 0)}{C.RESET}")
        print(f"  {C.GREEN}Executed       :{C.RESET} {C.BOLD}{stats.get('executed', 0)}{C.RESET}")
        print(f"  {C.YELLOW}Skipped        :{C.RESET} {C.BOLD}{stats.get('skipped', 0)}{C.RESET}")
        print(f"  {C.RED}Errors         :{C.RESET} {C.BOLD}{stats.get('errors', 0)}{C.RESET}")

        if stats.get("dry_run"):
            print(f"\n  {C.YELLOW}{C.BOLD}This was a DRY RUN — no changes were made.{C.RESET}")

        # Action type breakdown
        type_counts: Counter = Counter()
        for a in actions:
            type_counts[a.action_type] += 1

        if type_counts:
            print(f"\n  {C.CYAN}{C.BOLD}Action Breakdown:{C.RESET}")
            for atype, count in type_counts.most_common():
                print(f"    {atype:<20} : {count}")

        print(f"{C.CYAN}{'─' * 60}{C.RESET}\n")

    def export_json(
        self,
        report: ScanReport,
        actions: List[MigrationAction],
        stats: Dict[str, Any],
        path: str = "drive_organizer_report.json",
    ) -> None:
        """Export full report to JSON."""
        from dataclasses import asdict
        data = {
            "timestamp": datetime.now().isoformat(),
            "scan_report": asdict(report),
            "migration_stats": stats,
            "actions": [asdict(a) for a in actions],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.logger.info(f"Report exported to {path}")

    def export_markdown(
        self,
        report: ScanReport,
        actions: List[MigrationAction],
        stats: Dict[str, Any],
        path: str = "drive_organizer_report.md",
    ) -> None:
        """Export report as Markdown."""
        lines = [
            f"# Drive Organizer Report",
            f"",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## Scan Summary",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Files | {report.total_files} |",
            f"| Total Folders | {report.total_folders} |",
            f"| Total Size | {format_size(report.total_size_bytes)} |",
            f"| Duplicates | {report.duplicate_count} |",
            f"| Uncategorized | {report.uncategorized_count} |",
            f"| Music Files | {report.music_files} |",
            f"| Document Files | {report.document_files} |",
            f"| Image Files | {report.image_files} |",
            f"| Code Files | {report.code_files} |",
            f"",
            f"## Migration Summary",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Planned | {stats.get('total_planned', 0)} |",
            f"| Executed | {stats.get('executed', 0)} |",
            f"| Skipped | {stats.get('skipped', 0)} |",
            f"| Errors | {stats.get('errors', 0)} |",
            f"",
        ]

        if report.file_type_counts:
            lines.append("## Top File Types")
            lines.append("")
            lines.append("| Extension | Count |")
            lines.append("|-----------|-------|")
            for ext, count in list(report.file_type_counts.items())[:20]:
                lines.append(f"| {ext} | {count} |")
            lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        self.logger.info(f"Markdown report exported to {path}")
