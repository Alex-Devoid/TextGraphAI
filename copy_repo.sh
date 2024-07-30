#!/bin/bash

# Define the list of files


files=(
"/Users/alexdevoid/Documents/TextGraphAI/Dockerfile.celery"
/Users/alexdevoid/Documents/TextGraphAI/Dockerfile
)


# Concatenate filenames and their contents
for file in "${files[@]}"; do
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
