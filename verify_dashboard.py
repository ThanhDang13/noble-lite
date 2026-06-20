#!/usr/bin/env python3
"""
Quick verification script - checks dashboard structure and dependencies
"""

import sys
from pathlib import Path

def check_structure():
    """Verify all dashboard files exist."""
    print("Checking dashboard structure...")

    required_files = [
        "dashboard/__init__.py",
        "dashboard/app.py",
        "dashboard/README.md",
        "dashboard/utils/__init__.py",
        "dashboard/utils/logger.py",
        "dashboard/utils/privilege.py",
        "dashboard/utils/process_runner.py",
        "dashboard/panels/__init__.py",
        "dashboard/panels/kernel_panel.py",
        "dashboard/panels/process_manager_panel.py",
        "dashboard/panels/file_manager_panel.py",
        "dashboard/panels/network_monitor_panel.py",
        "dashboard/panels/socket_server_panel.py",
        "dashboard/panels/socket_client_panel.py",
        "dashboard/panels/scripts_panel.py",
        "dashboard/panels/logs_panel.py",
    ]

    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
            print(f"  ✗ {file}")
        else:
            print(f"  ✓ {file}")

    return len(missing) == 0

def check_dependencies():
    """Check Python dependencies."""
    print("\nChecking dependencies...")

    deps = {
        'tkinter': 'python3-tk',
        'pathlib': 'built-in',
        'subprocess': 'built-in',
        'threading': 'built-in',
        'queue': 'built-in',
    }

    missing = []
    for module, package in deps.items():
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError:
            print(f"  ✗ {module} (install: sudo apt-get install {package})")
            missing.append((module, package))

    return len(missing) == 0

def check_binaries():
    """Check if userspace binaries exist."""
    print("\nChecking binaries...")

    binaries = [
        "userspace/process-manager/process-manager",
        "userspace/file-manager/file-manager",
        "userspace/network-monitor/network-monitor",
        "userspace/socket-server/socket-server",
        "userspace/socket-client/socket-client",
    ]

    for binary in binaries:
        path = Path(binary)
        if path.exists():
            print(f"  ✓ {binary}")
        else:
            print(f"  ✗ {binary} (not built)")

def main():
    print("=" * 60)
    print("Dashboard Verification")
    print("=" * 60)
    print()

    structure_ok = check_structure()
    deps_ok = check_dependencies()
    check_binaries()

    print()
    print("=" * 60)
    if structure_ok and deps_ok:
        print("✓ Dashboard is ready to use!")
        print()
        print("Launch with: python3 launch_dashboard.py")
        return 0
    else:
        print("✗ Dashboard has missing dependencies")
        print()
        print("Run: ./setup_dashboard.sh")
        return 1

if __name__ == "__main__":
    sys.exit(main())
