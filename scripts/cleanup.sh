#!/bin/bash

set -euo pipefail

LOG_DIR="${HOME}/.local/log/project"
LOG_FILE="${LOG_DIR}/cleanup.log"

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] $*" | tee -a "${LOG_FILE}"
}

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Clean up old logs, temporary files, and free disk space.

OPTIONS:
    -h, --help          Show this help message
    -d, --days DAYS     Remove files older than DAYS [default: 7]
    -p, --path PATH     Additional path to clean (can be used multiple times)
    -n, --dry-run       Show what would be deleted without deleting
    -v, --verbose       Verbose output

DEFAULT CLEANUP LOCATIONS:
    /tmp/*
    /var/log/*.log (older than specified days)
    /var/tmp/*
    ~/.cache/thumbnails/*

EXAMPLES:
    $(basename "$0") --days 7
    $(basename "$0") -d 30 -p /var/cache/apt
    $(basename "$0") --dry-run --verbose

EOF
}

DAYS=7
CUSTOM_PATHS=()
DRY_RUN=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--days)
            DAYS="$2"
            shift 2
            ;;
        -p|--path)
            CUSTOM_PATHS+=("$2")
            shift 2
            ;;
        -n|--dry-run)
            DRY_RUN=true
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

if ! [[ "${DAYS}" =~ ^[0-9]+$ ]]; then
    echo "Error: DAYS must be a positive integer" >&2
    exit 1
fi

mkdir -p "${LOG_DIR}"

log "Starting cleanup (files older than ${DAYS} days)"

if [[ "${DRY_RUN}" == "true" ]]; then
    log "DRY RUN MODE - no files will be deleted"
fi

TOTAL_FREED=0

cleanup_path() {
    local path="$1"
    local pattern="$2"

    if [[ ! -e "${path}" ]]; then
        [[ "${VERBOSE}" == "true" ]] && log "Skipping non-existent path: ${path}"
        return 0
    fi

    if [[ ! -r "${path}" ]]; then
        [[ "${VERBOSE}" == "true" ]] && log "Skipping unreadable path: ${path}"
        return 0
    fi

    local find_cmd="find ${path} -type f -name '${pattern}' -mtime +${DAYS}"

    if [[ "${DRY_RUN}" == "true" ]]; then
        local count
        count=$(${find_cmd} 2>/dev/null | wc -l) || count=0
        log "Would delete ${count} files from ${path}"
        [[ "${VERBOSE}" == "true" ]] && ${find_cmd} 2>/dev/null || true
    else
        local size_before=$(du -sb "${path}" 2>/dev/null | cut -f1 || echo 0)
        ${find_cmd} -delete 2>/dev/null || true
        local size_after=$(du -sb "${path}" 2>/dev/null | cut -f1 || echo 0)
        local freed=$((size_before - size_after))
        TOTAL_FREED=$((TOTAL_FREED + freed))
        log "Cleaned ${path}: freed $(numfmt --to=iec ${freed} 2>/dev/null || echo ${freed}) bytes"
    fi
}

cleanup_path "/tmp" "*"
cleanup_path "/var/tmp" "*"
cleanup_path "/var/log" "*.log"

if [[ -d "${HOME}/.cache/thumbnails" ]]; then
    cleanup_path "${HOME}/.cache/thumbnails" "*"
fi

for custom_path in "${CUSTOM_PATHS[@]}"; do
    cleanup_path "${custom_path}" "*"
done

if command -v apt-get &> /dev/null && [[ "${DRY_RUN}" == "false" ]]; then
    log "Running apt-get autoremove and autoclean"
    apt-get autoremove -y >> "${LOG_FILE}" 2>&1 || true
    apt-get autoclean -y >> "${LOG_FILE}" 2>&1 || true
fi

if [[ "${DRY_RUN}" == "false" ]]; then
    log "Cleanup completed. Total freed: $(numfmt --to=iec ${TOTAL_FREED} 2>/dev/null || echo ${TOTAL_FREED}) bytes"
else
    log "Dry run completed"
fi
