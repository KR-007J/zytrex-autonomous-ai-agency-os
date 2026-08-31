#!/usr/bin/env python3
"""Autonomous AI Agency CLI & Background Engine Runner."""

from __future__ import annotations
import sys
import os
import argparse
import json
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.database.db import init_db, get_db_session, LeadRepository
from src.agency.orchestrator import AutonomousAgencyOrchestrator
from src.export.excel_generator import ExcelReportGenerator


def run_agency_autopilot(args, config):
    print("⚡ [Autonomous AI Agency] Starting 24/7 Autopilot Engine...")
    orchestrator = AutonomousAgencyOrchestrator(config)
    orchestrator.start_autopilot(
        interval_seconds=args.interval,
        auto_email=args.auto_email,
        dry_run=args.dry_run,
    )
    print("🟢 Autopilot running in background. Monitoring cycles...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping autopilot...")
        orchestrator.stop_autopilot()


def run_export_excel(args, config):
    print("📊 [Autonomous AI Agency] Generating Master Daily Excel (.xlsx)...")
    generator = ExcelReportGenerator()
    with get_db_session() as session:
        path = generator.generate_daily_master_sheet(session)
        print(f"✅ Excel report saved at: {path}")


def run_status_mode(args, config):
    with get_db_session() as session:
        stats = LeadRepository.get_stats(session)
        leads, _ = LeadRepository.get_leads(session, skip=0, limit=5)
        output = {
            "stats": stats,
            "sample_leads": [l.to_dict() for l in leads],
        }
        print(json.dumps(output, indent=2))


def run_serve_mode(args, config):
    import uvicorn
    print(f"🌐 [Autonomous AI Agency] Starting Mission Control on http://{args.host}:{args.port}...")
    uvicorn.run("src.api.main:app", host=args.host, port=args.port, reload=False)


def main():
    parser = argparse.ArgumentParser(description="Autonomous AI Agency CLI")
    parser.add_argument(
        "--mode",
        choices=["serve", "agency-autopilot", "export-excel", "status"],
        default="serve",
        help="Operational mode",
    )
    parser.add_argument("--interval", type=int, default=1800, help="Autopilot interval in seconds")
    parser.add_argument("--auto-email", action="store_true", default=True, help="Auto-dispatch cold emails")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Simulate email sending safely")
    parser.add_argument("--config", type=str, default=None, help="Custom config path")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host")
    parser.add_argument("--port", type=int, default=8000, help="Port")

    args = parser.parse_args()

    config = load_config(args.config)
    init_db(config.app.database_url)

    if args.mode == "agency-autopilot":
        run_agency_autopilot(args, config)
    elif args.mode == "export-excel":
        run_export_excel(args, config)
    elif args.mode == "status":
        run_status_mode(args, config)
    elif args.mode == "serve":
        run_serve_mode(args, config)


if __name__ == "__main__":
    main()
