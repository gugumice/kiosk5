#!/bin/bash

CONFIG_FILE="/etc/cups/cups-browsed.conf"
BACKUP_FILE="/etc/cups/cups-browsed.conf.bak"

backup_config_file() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        printf "Error: Configuration file not found: %s\n" "$CONFIG_FILE" >&2
        return 1
    fi
    cp "$CONFIG_FILE" "$BACKUP_FILE" || {
        printf "Error: Failed to create backup file: %s\n" "$BACKUP_FILE" >&2
        return 1
    }
}

sanitize_and_replace_protocols() {
    local tmpfile; tmpfile=$(mktemp)
    if ! sed -E 's/^\s*BrowseRemoteProtocols\s+dnssd\s*$/BrowseRemoteProtocols none/' "$CONFIG_FILE" > "$tmpfile"; then
        printf "Error: Failed to process configuration file\n" >&2
        rm -f "$tmpfile"
        return 1
    fi

    if ! grep -q '^BrowseRemoteProtocols none$' "$tmpfile"; then
        printf "Error: Replacement did not occur, pattern not found\n" >&2
        rm -f "$tmpfile"
        return 1
    fi

    mv "$tmpfile" "$CONFIG_FILE" || {
        printf "Error: Failed to update configuration file\n" >&2
        rm -f "$tmpfile"
        return 1
    }
}

main() {
    backup_config_file || return 1
    sanitize_and_replace_protocols || return 1
    printf "Configuration updated successfully: %s\n" "$CONFIG_FILE"
}

main