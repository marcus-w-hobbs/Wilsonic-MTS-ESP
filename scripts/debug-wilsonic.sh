#!/bin/bash
# debug-wilsonic.sh - Run Wilsonic with crash capture for AI debugging
# Usage: ./scripts/debug-wilsonic.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$PROJECT_DIR/Builds/MacOSX/build/Debug"
APP_PATH="$BUILD_DIR/Wilsonic.app/Contents/MacOS/Wilsonic"
LOG_FILE="/tmp/wilsonic-debug-$(date +%Y%m%d-%H%M%S).log"

echo "=== Wilsonic Debug Runner ===" | tee "$LOG_FILE"
echo "Timestamp: $(date)" | tee -a "$LOG_FILE"
echo "App path: $APP_PATH" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Check if app exists
if [ ! -f "$APP_PATH" ]; then
    echo "ERROR: App not found at $APP_PATH" | tee -a "$LOG_FILE"
    echo "Building first..." | tee -a "$LOG_FILE"

    xcodebuild -project "$PROJECT_DIR/Builds/MacOSX/Wilsonic.xcodeproj" \
        -scheme "Wilsonic - Standalone Plugin" \
        -configuration Debug \
        build 2>&1 | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "=== Running under LLDB ===" | tee -a "$LOG_FILE"
echo "The app will launch. If it crashes, the backtrace will be captured." | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Run under lldb with crash handlers
# -o runs commands at start
# -k runs commands on crash/stop
lldb \
    -o "settings set auto-confirm true" \
    -o "run" \
    -k "echo '\\n=== CRASH DETECTED ===\\n'" \
    -k "thread backtrace all" \
    -k "echo '\\n=== FRAME VARIABLES ===\\n'" \
    -k "frame variable" \
    -k "echo '\\n=== REGISTERS ===\\n'" \
    -k "register read" \
    -k "quit" \
    "$APP_PATH" 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=== Session Complete ===" | tee -a "$LOG_FILE"
echo "Full log saved to: $LOG_FILE"

# Also check for any crash reports
echo ""
echo "=== Recent Crash Reports ==="
ls -lt ~/Library/Logs/DiagnosticReports/ 2>/dev/null | grep -i wilsonic | head -5 || echo "No crash reports found"
