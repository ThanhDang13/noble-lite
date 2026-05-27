#!/bin/bash

set -euo pipefail

LOG_DIR="${HOME}/.local/log/project"
LOG_FILE="${LOG_DIR}/backup.log"

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] $*" | tee -a "${LOG_FILE}"
}

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] SOURCE DESTINATION

Backup files/directories with compression and logging.

OPTIONS:
    -h, --help          Show this help message
    -c, --compress      Compression format (gzip|bzip2|xz) [default: gzip]
    -e, --exclude       Pattern to exclude (can be used multiple times)
    -v, --verbose       Verbose output

ARGUMENTS:
    SOURCE              Source file or directory to backup
    DESTINATION         Destination directory for backup

EXAMPLES:
    $(basename "$0") /home/user /backup/dest
    $(basename "$0") -c xz -e "*.tmp" /etc /backup/etc
    $(basename "$0") --verbose /var/www /backup/www

EOF
}

COMPRESS="gzip"
EXCLUDE_PATTERNS=()
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--compress)
            COMPRESS="$2"
            shift 2
            ;;
        -e|--exclude)
            EXCLUDE_PATTERNS+=("$2")
            shift 2
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
            break
            ;;
    esac
done

if [[ $# -lt 2 ]]; then
    echo "Error: SOURCE and DESTINATION are required" >&2
    show_help
    exit 1
fi

SOURCE="$1"
DESTINATION="$2"

if [[ ! -e "${SOURCE}" ]]; then
    echo "Error: Source '${SOURCE}' does not exist" >&2
    exit 1
fi

if [[ ! -d "${DESTINATION}" ]]; then
    echo "Error: Destination '${DESTINATION}' is not a directory" >&2
    exit 1
fi

mkdir -p "${LOG_DIR}"

TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BASENAME=$(basename "${SOURCE}")
BACKUP_NAME="${BASENAME}_${TIMESTAMP}"

case "${COMPRESS}" in
    gzip)
        ARCHIVE="${DESTINATION}/${BACKUP_NAME}.tar.gz"
        COMPRESS_FLAG="z"
        ;;
    bzip2)
        ARCHIVE="${DESTINATION}/${BACKUP_NAME}.tar.bz2"
        COMPRESS_FLAG="j"
        ;;
    xz)
        ARCHIVE="${DESTINATION}/${BACKUP_NAME}.tar.xz"
        COMPRESS_FLAG="J"
        ;;
    *)
        echo "Error: Invalid compression format: ${COMPRESS}" >&2
        exit 1
        ;;
esac

log "Starting backup: ${SOURCE} -> ${ARCHIVE}"

TAR_OPTS="c${COMPRESS_FLAG}f"
if [[ "${VERBOSE}" == "true" ]]; then
    TAR_OPTS="${TAR_OPTS}v"
fi

EXCLUDE_ARGS=()
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    EXCLUDE_ARGS+=(--exclude="${pattern}")
done

if tar ${TAR_OPTS} "${ARCHIVE}" "${EXCLUDE_ARGS[@]}" -C "$(dirname "${SOURCE}")" "$(basename "${SOURCE}")"; then
    ARCHIVE_SIZE=$(du -h "${ARCHIVE}" | cut -f1)
    log "Backup completed successfully: ${ARCHIVE} (${ARCHIVE_SIZE})"
    exit 0
else
    log "ERROR: Backup failed"
    exit 1
fi
