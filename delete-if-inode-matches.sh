#!/bin/bash

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    echo "Usage: $0 <file_path> <expected_inode> [<expire_after>]"
    exit 1
fi

FILE_PATH="$1"
EXPECTED_INODE="$2"
EXPIRE_AFTER="$3"

# Verify inode match
if [ ! -e "$FILE_PATH" ] || [ "$(stat -c %i "$FILE_PATH")" -ne "$EXPECTED_INODE" ]; then
    exit 0
fi

# If expire_after is set, check file age
if [ -n "$EXPIRE_AFTER" ]; then
    LAST_ACCESS=$(stat -c %X "$FILE_PATH")
    NOW=$(date +%s)
    AGE_MINUTES=$(( (NOW - LAST_ACCESS) / 60 ))
    if [ "$AGE_MINUTES" -lt "$EXPIRE_AFTER" ]; then
        # reschedule the job in minutes
        REMAINING_MINUTES=$(( EXPIRE_AFTER - AGE_MINUTES ))
        echo "$0 \"$FILE_PATH\" \"$EXPECTED_INODE\" \"$EXPIRE_AFTER\"" | at now + "$REMAINING_MINUTES" minutes
        exit 0
    fi
fi

# Delete the file or directory
gio trash "$FILE_PATH"
