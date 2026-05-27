#!/bin/bash

set -euo pipefail

LOG_DIR="${HOME}/.local/log/project"
LOG_FILE="${LOG_DIR}/scheduler.log"

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] $*" | tee -a "${LOG_FILE}"
}

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] COMMAND

Set up cron jobs or systemd timers for scheduled tasks.

OPTIONS:
    -h, --help              Show this help message
    -t, --type TYPE         Scheduler type (cron|systemd) [default: cron]
    -s, --schedule SPEC     Schedule specification
                            For cron: "0 2 * * *" (2 AM daily)
                            For systemd: "daily", "hourly", "weekly", or OnCalendar spec
    -n, --name NAME         Job/timer name [required for systemd]
    -u, --user USER         Run as user [default: current user]
    -l, --list              List existing jobs/timers
    -r, --remove NAME       Remove job/timer by name
    -v, --verbose           Verbose output

ARGUMENTS:
    COMMAND                 Command to schedule (required unless --list or --remove)

EXAMPLES:
    $(basename "$0") -s "0 2 * * *" "/usr/local/bin/backup.sh /data /backup"
    $(basename "$0") -t systemd -s daily -n backup "/usr/local/bin/backup.sh"
    $(basename "$0") --list
    $(basename "$0") --remove backup

EOF
}

TYPE="cron"
SCHEDULE=""
NAME=""
USER="${USER:-$(whoami)}"
LIST=false
REMOVE=""
VERBOSE=false
COMMAND=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--type)
            TYPE="$2"
            shift 2
            ;;
        -s|--schedule)
            SCHEDULE="$2"
            shift 2
            ;;
        -n|--name)
            NAME="$2"
            shift 2
            ;;
        -u|--user)
            USER="$2"
            shift 2
            ;;
        -l|--list)
            LIST=true
            shift
            ;;
        -r|--remove)
            REMOVE="$2"
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
            COMMAND="$1"
            shift
            ;;
    esac
done

mkdir -p "${LOG_DIR}"

list_cron() {
    log "Listing cron jobs for user ${USER}:"
    crontab -l -u "${USER}" 2>/dev/null || echo "No crontab for ${USER}"
}

list_systemd() {
    log "Listing systemd timers:"
    systemctl list-timers --all
}

remove_cron() {
    local job_name="$1"
    log "Removing cron job containing: ${job_name}"
    local temp_cron=$(mktemp)
    crontab -l -u "${USER}" 2>/dev/null | grep -v "${job_name}" > "${temp_cron}" || true
    crontab -u "${USER}" "${temp_cron}"
    rm -f "${temp_cron}"
    log "Cron job removed"
}

remove_systemd() {
    local timer_name="$1"
    log "Removing systemd timer: ${timer_name}"
    systemctl stop "${timer_name}.timer" 2>/dev/null || true
    systemctl disable "${timer_name}.timer" 2>/dev/null || true
    rm -f "/etc/systemd/system/${timer_name}.service"
    rm -f "/etc/systemd/system/${timer_name}.timer"
    systemctl daemon-reload
    log "Systemd timer removed"
}

add_cron() {
    local schedule="$1"
    local command="$2"

    log "Adding cron job: ${schedule} ${command}"

    local temp_cron=$(mktemp)
    crontab -l -u "${USER}" 2>/dev/null > "${temp_cron}" || true
    echo "${schedule} ${command}" >> "${temp_cron}"
    crontab -u "${USER}" "${temp_cron}"
    rm -f "${temp_cron}"

    log "Cron job added successfully"
}

add_systemd() {
    local schedule="$1"
    local name="$2"
    local command="$3"

    if [[ -z "${name}" ]]; then
        echo "Error: --name is required for systemd timers" >&2
        exit 1
    fi

    log "Creating systemd timer: ${name}"

    local service_file="/etc/systemd/system/${name}.service"
    local timer_file="/etc/systemd/system/${name}.timer"

    cat > "${service_file}" << EOF
[Unit]
Description=${name} scheduled task

[Service]
Type=oneshot
User=${USER}
ExecStart=${command}
EOF

    local on_calendar="${schedule}"
    case "${schedule}" in
        hourly) on_calendar="hourly" ;;
        daily) on_calendar="daily" ;;
        weekly) on_calendar="weekly" ;;
        monthly) on_calendar="monthly" ;;
    esac

    cat > "${timer_file}" << EOF
[Unit]
Description=${name} timer

[Timer]
OnCalendar=${on_calendar}
Persistent=true

[Install]
WantedBy=timers.target
EOF

    systemctl daemon-reload
    systemctl enable "${name}.timer"
    systemctl start "${name}.timer"

    log "Systemd timer created and started"
}

if [[ "${LIST}" == "true" ]]; then
    case "${TYPE}" in
        cron) list_cron ;;
        systemd) list_systemd ;;
        *) echo "Error: Invalid type: ${TYPE}" >&2; exit 1 ;;
    esac
    exit 0
fi

if [[ -n "${REMOVE}" ]]; then
    case "${TYPE}" in
        cron) remove_cron "${REMOVE}" ;;
        systemd) remove_systemd "${REMOVE}" ;;
        *) echo "Error: Invalid type: ${TYPE}" >&2; exit 1 ;;
    esac
    exit 0
fi

if [[ -z "${COMMAND}" ]]; then
    echo "Error: COMMAND is required" >&2
    show_help
    exit 1
fi

if [[ -z "${SCHEDULE}" ]]; then
    echo "Error: --schedule is required" >&2
    show_help
    exit 1
fi

case "${TYPE}" in
    cron)
        add_cron "${SCHEDULE}" "${COMMAND}"
        ;;
    systemd)
        add_systemd "${SCHEDULE}" "${NAME}" "${COMMAND}"
        ;;
    *)
        echo "Error: Invalid type: ${TYPE}" >&2
        exit 1
        ;;
esac
