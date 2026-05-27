#!/bin/bash

set -euo pipefail

LOG_DIR="${HOME}/.local/log/project"
LOG_FILE="${LOG_DIR}/timectl.log"

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] $*" | tee -a "${LOG_FILE}"
}

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Manage timezone, NTP, and time synchronization.

OPTIONS:
    -h, --help                  Show this help message
    -s, --status                Show current time/timezone status
    -t, --set-tz TIMEZONE       Set timezone (e.g., Asia/Ho_Chi_Minh)
    -l, --list-tz               List available timezones
    -n, --enable-ntp            Enable NTP synchronization
    -d, --disable-ntp           Disable NTP synchronization
    -m, --set-time TIME         Set system time manually (format: "YYYY-MM-DD HH:MM:SS")
    -r, --set-rtc               Sync RTC (hardware clock) with system time
    -v, --verbose               Verbose output

EXAMPLES:
    $(basename "$0") --status
    $(basename "$0") --set-tz Asia/Ho_Chi_Minh --enable-ntp
    $(basename "$0") --list-tz | grep Asia
    $(basename "$0") --set-time "2026-05-27 15:30:00"
    $(basename "$0") --enable-ntp --set-rtc

EOF
}

STATUS=false
SET_TZ=""
LIST_TZ=false
ENABLE_NTP=false
DISABLE_NTP=false
SET_TIME=""
SET_RTC=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -s|--status)
            STATUS=true
            shift
            ;;
        -t|--set-tz)
            SET_TZ="$2"
            shift 2
            ;;
        -l|--list-tz)
            LIST_TZ=true
            shift
            ;;
        -n|--enable-ntp)
            ENABLE_NTP=true
            shift
            ;;
        -d|--disable-ntp)
            DISABLE_NTP=true
            shift
            ;;
        -m|--set-time)
            SET_TIME="$2"
            shift 2
            ;;
        -r|--set-rtc)
            SET_RTC=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -*)
            echo "Error: Unknown option: $1" >&2
            show_help
            exit 1
            ;;
        *)
            echo "Error: Unexpected argument: $1" >&2
            show_help
            exit 1
            ;;
    esac
done

mkdir -p "${LOG_DIR}"

if [[ "${LIST_TZ}" == "true" ]]; then
    timedatectl list-timezones
    exit 0
fi

if [[ "${STATUS}" == "true" ]]; then
    log "Current time/timezone status:"
    timedatectl status
    exit 0
fi

if [[ -n "${SET_TZ}" ]]; then
    log "Setting timezone to: ${SET_TZ}"

    if ! timedatectl list-timezones | grep -q "^${SET_TZ}$"; then
        echo "Error: Invalid timezone: ${SET_TZ}" >&2
        echo "Use --list-tz to see available timezones" >&2
        exit 1
    fi

    if timedatectl set-timezone "${SET_TZ}"; then
        log "Timezone set successfully to ${SET_TZ}"
        [[ "${VERBOSE}" == "true" ]] && timedatectl status
    else
        log "ERROR: Failed to set timezone"
        exit 1
    fi
fi

if [[ "${ENABLE_NTP}" == "true" ]]; then
    log "Enabling NTP synchronization"

    if timedatectl set-ntp true; then
        log "NTP enabled successfully"

        if command -v systemctl &> /dev/null; then
            systemctl restart systemd-timesyncd 2>/dev/null || true
        fi

        sleep 2

        if [[ "${VERBOSE}" == "true" ]]; then
            timedatectl timesync-status 2>/dev/null || timedatectl status
        fi
    else
        log "ERROR: Failed to enable NTP"
        exit 1
    fi
fi

if [[ "${DISABLE_NTP}" == "true" ]]; then
    log "Disabling NTP synchronization"

    if timedatectl set-ntp false; then
        log "NTP disabled successfully"
    else
        log "ERROR: Failed to disable NTP"
        exit 1
    fi
fi

if [[ -n "${SET_TIME}" ]]; then
    log "Setting system time to: ${SET_TIME}"

    if timedatectl set-ntp false 2>/dev/null; then
        log "NTP disabled to allow manual time setting"
    fi

    if timedatectl set-time "${SET_TIME}"; then
        log "System time set successfully"
        [[ "${VERBOSE}" == "true" ]] && date
    else
        log "ERROR: Failed to set system time"
        exit 1
    fi
fi

if [[ "${SET_RTC}" == "true" ]]; then
    log "Syncing RTC (hardware clock) with system time"

    if hwclock --systohc; then
        log "RTC synced successfully"
        [[ "${VERBOSE}" == "true" ]] && hwclock --show
    else
        log "ERROR: Failed to sync RTC"
        exit 1
    fi
fi

if [[ "${STATUS}" == "false" && -z "${SET_TZ}" && "${LIST_TZ}" == "false" && \
      "${ENABLE_NTP}" == "false" && "${DISABLE_NTP}" == "false" && \
      -z "${SET_TIME}" && "${SET_RTC}" == "false" ]]; then
    echo "Error: No action specified" >&2
    show_help
    exit 1
fi

log "Operation completed successfully"
