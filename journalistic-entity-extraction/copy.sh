#!/bin/bash

# Define the directory to search for files
directory="/Users/alexdevoid/Documents/U3_VPA_Wizard/VPA-Wizard/Wizard"

# Find all files in the directory and its subdirectories
files=$(find "$directory" -type f)

# Concatenate filenames and their contents
for file in $files; do
    if [ -f "$file" ]; then
        echo "Filename: $file"
        echo "\`\`\`"
        cat "$file"
        echo "\`\`\`"
        echo # Add an empty line for separation
    else
        echo "File not found: $file"
    fi
done | pbcopy

echo "The filenames and their contents have been copied to the clipboard."
