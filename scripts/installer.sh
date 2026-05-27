#!/bin/bash

set -euo pipefail

LOG_DIR="${HOME}/.local/log/project"
LOG_FILE="${LOG_DIR}/installer.log"

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] $*" | tee -a "${LOG_FILE}"
}

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] PACKAGE [PACKAGE...]

Wrapper for installing packages via apt/dpkg with logging.

OPTIONS:
    -h, --help              Show this help message
    -r, --remove            Remove packages instead of installing
    -u, --update            Update package lists before installing
    -y, --yes               Assume yes to all prompts
    -s, --simulate          Simulate installation (dry run)
    -f, --file FILE         Install from .deb file
    -l, --list              List installed packages
    -i, --info PACKAGE      Show package information
    -v, --verbose           Verbose output

ARGUMENTS:
    PACKAGE                 Package name(s) to install/remove

EXAMPLES:
    $(basename "$0") nginx
    $(basename "$0") -u -y nginx mysql-server
    $(basename "$0") --remove apache2
    $(basename "$0") --file /tmp/package.deb
    $(basename "$0") --info nginx
    $(basename "$0") --list | grep nginx

EOF
}

REMOVE=false
UPDATE=false
YES=false
SIMULATE=false
DEB_FILE=""
LIST=false
INFO=""
VERBOSE=false
PACKAGES=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -r|--remove)
            REMOVE=true
            shift
            ;;
        -u|--update)
            UPDATE=true
            shift
            ;;
        -y|--yes)
            YES=true
            shift
            ;;
        -s|--simulate)
            SIMULATE=true
            shift
            ;;
        -f|--file)
            DEB_FILE="$2"
            shift 2
            ;;
        -l|--list)
            LIST=true
            shift
            ;;
        -i|--info)
            INFO="$2"
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
            PACKAGES+=("$1")
            shift
            ;;
    esac
done

mkdir -p "${LOG_DIR}"

if [[ "${LIST}" == "true" ]]; then
    dpkg -l
    exit 0
fi

if [[ -n "${INFO}" ]]; then
    apt-cache show "${INFO}"
    exit 0
fi

if [[ -n "${DEB_FILE}" ]]; then
    if [[ ! -f "${DEB_FILE}" ]]; then
        echo "Error: File not found: ${DEB_FILE}" >&2
        exit 1
    fi

    log "Installing from .deb file: ${DEB_FILE}"

    if [[ "${SIMULATE}" == "true" ]]; then
        log "SIMULATE: Would install ${DEB_FILE}"
        dpkg-deb --info "${DEB_FILE}"
        exit 0
    fi

    if dpkg -i "${DEB_FILE}"; then
        log "Package installed successfully from ${DEB_FILE}"
    else
        log "ERROR: dpkg failed, attempting to fix dependencies"
        apt-get install -f -y
    fi
    exit 0
fi

if [[ ${#PACKAGES[@]} -eq 0 ]]; then
    echo "Error: No packages specified" >&2
    show_help
    exit 1
fi

APT_OPTS=()
if [[ "${YES}" == "true" ]]; then
    APT_OPTS+=("-y")
fi

if [[ "${SIMULATE}" == "true" ]]; then
    APT_OPTS+=("--dry-run")
fi

if [[ "${VERBOSE}" == "true" ]]; then
    APT_OPTS+=("-V")
fi

if [[ "${UPDATE}" == "true" ]]; then
    log "Updating package lists"
    apt-get update | tee -a "${LOG_FILE}"
fi

if [[ "${REMOVE}" == "true" ]]; then
    log "Removing packages: ${PACKAGES[*]}"

    if apt-get remove "${APT_OPTS[@]}" "${PACKAGES[@]}" 2>&1 | tee -a "${LOG_FILE}"; then
        log "Packages removed successfully"

        if [[ "${YES}" == "true" && "${SIMULATE}" == "false" ]]; then
            log "Running autoremove"
            apt-get autoremove -y | tee -a "${LOG_FILE}"
        fi
    else
        log "ERROR: Failed to remove packages"
        exit 1
    fi
else
    log "Installing packages: ${PACKAGES[*]}"

    if apt-get install "${APT_OPTS[@]}" "${PACKAGES[@]}" 2>&1 | tee -a "${LOG_FILE}"; then
        log "Packages installed successfully"
    else
        log "ERROR: Failed to install packages"
        exit 1
    fi
fi
