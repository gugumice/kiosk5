#!/usr/bin/env bash

CONFIG_FILE=""

sanitize_config_file() {
    if [[ -z "$CONFIG_FILE" ]]; then
        printf "Error: No config file path provided\n" >&2
        return 1
    fi

    if [[ ! -f "$CONFIG_FILE" ]]; then
        printf "Error: Config file not found: %s\n" "$CONFIG_FILE" >&2
        return 1
    fi

    if [[ ! -r "$CONFIG_FILE" || ! -w "$CONFIG_FILE" ]]; then
        printf "Error: Config file is not readable or writable: %s\n" "$CONFIG_FILE" >&2
        return 1
    fi
}

modify_config_file() {
    local temp_file; temp_file=$(mktemp) || return 1
    local found=0
    local line;

    sed -i '/^# Additional overlays.*/a dtoverlay=pi3-disable-wifi\ndtoverlay=pi3-disable-bt' "$temp_file"

    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" =~ ^dtoverlay=vc4-kms-v3d$ ]]; then
            printf "#%s\n" "$line" >> "$temp_file"
            printf "dtoverlay=vc4-kms-dsi-7inch\n" >> "$temp_file"
            printf "gpu_mem=256\n" >> "$temp_file"
            found=1
        else
            printf "%s\n" "$line" >> "$temp_file"
        fi
    done < "$CONFIG_FILE"

    if [[ "$found" -eq 0 ]]; then
        rm -f "$temp_file"
        printf "Error: Target dtoverlay line not found in config file\n" >&2
        return 1
    fi

    mv "$temp_file" "$CONFIG_FILE"
}

main() {
    if [[ $# -ne 1 ]]; then
        printf "Usage: %s <path_to_config_file>\n" "$0" >&2
        return 1
    fi

    CONFIG_FILE="$1"

    if ! sanitize_config_file; then
        return 1
    fi

    if ! modify_config_file; then
        return 1
    fi
}

main "$@"
