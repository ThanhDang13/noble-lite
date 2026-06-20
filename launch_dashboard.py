#!/usr/bin/env python3
"""
Quick launcher for the dashboard application.
Run from project root: ./launch_dashboard.py
"""

import sys
from pathlib import Path

# Add dashboard to path
sys.path.insert(0, str(Path(__file__).parent / "dashboard"))

from dashboard.app import main

if __name__ == "__main__":
    print("=" * 60)
    print("Linux System Programming Dashboard")
    print("=" * 60)
    print()
    print("Starting GUI application...")
    print("Logs will be saved to: logs/dashboard_YYYYMMDD.log")
    print()

    try:
        main()
    except KeyboardInterrupt:
        print("\nDashboard closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
