#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <file_path> <expected_inode>"
    exit 1
fi

FILE_PATH="$1"
EXPECTED_INODE="$2"

if [ -e "$FILE_PATH" ]; then
    ACTUAL_INODE=$(stat -c %i "$FILE_PATH")
    if [ "$ACTUAL_INODE" -eq "$EXPECTED_INODE" ]; then
        rm -r "$FILE_PATH"
    fi
fi

