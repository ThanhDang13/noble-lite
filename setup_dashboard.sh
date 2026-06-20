#!/bin/bash
# Quick setup script for the dashboard

echo "==================================================================="
echo "Linux System Programming Dashboard - Setup"
echo "==================================================================="
echo

# Check Python version
echo "Checking Python version..."
python3 --version

# Check if tkinter is installed
echo
echo "Checking Tkinter..."
if python3 -c "import tkinter" 2>/dev/null; then
    echo "✓ Tkinter is installed"
else
    echo "✗ Tkinter is NOT installed"
    echo
    echo "Installing Tkinter..."
    echo "Running: sudo apt-get install -y python3-tk"
    sudo apt-get update
    sudo apt-get install -y python3-tk
fi

# Create logs directory
echo
echo "Creating logs directory..."
mkdir -p logs
echo "✓ logs/ created"

# Check binaries
echo
echo "Checking userspace binaries..."
for binary in userspace/*/; do
    binary_name=$(basename "$binary")
    binary_path="${binary}${binary_name}"
    if [ -f "$binary_path" ] && [ -x "$binary_path" ]; then
        echo "  ✓ $binary_name"
    else
        echo "  ✗ $binary_name (not built or not executable)"
    fi
done

# Check kernel module
echo
echo "Checking kernel module..."
if [ -f "kernel/monitor-module/monitor.ko" ]; then
    echo "  ✓ monitor.ko"
else
    echo "  ✗ monitor.ko (not built)"
fi

# Check scripts
echo
echo "Checking scripts..."
for script in scripts/*.sh; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        echo "  ✓ $(basename $script)"
    else
        echo "  ✗ $(basename $script) (not executable)"
        chmod +x "$script" 2>/dev/null && echo "    → Made executable"
    fi
done

echo
echo "==================================================================="
echo "Setup complete!"
echo
echo "To launch the dashboard, run:"
echo "  python3 launch_dashboard.py"
echo
echo "Or:"
echo "  cd dashboard && python3 app.py"
echo "==================================================================="
