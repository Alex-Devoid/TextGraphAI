#!/bin/bash

# Define the list of files


files=(
# "/Users/alexdevoid/Documents/TextGraphAI/app/templates/upload.html"
# "/Users/alexdevoid/Documents/TextGraphAI/app/tasks.py"
# "/Users/alexdevoid/Documents/TextGraphAI/app/routes.py"
# "/Users/alexdevoid/Documents/TextGraphAI/app/settings.yaml"
# "/Users/alexdevoid/Documents/TextGraphAI/celeryconfig.py"
# "/Users/alexdevoid/Documents/TextGraphAI/docker-compose.yml"
# "/Users/alexdevoid/Documents/TextGraphAI/Dockerfile.celery"
# "/Users/alexdevoid/Documents/TextGraphAI/run.py"
# /Users/alexdevoid/Documents/TextGraphAI/app/output/20240802-020954/reports/indexing-engine.log
# /Users/alexdevoid/Documents/TextGraphAI/app/output/20240802-020954/reports/logs.json
/Users/alexdevoid/Documents/TextGraphAI/app/tasks.py
/Users/alexdevoid/Documents/TextGraphAI/app/settings.yaml

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
