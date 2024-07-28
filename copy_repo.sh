#!/bin/bash

# Define the list of files


files=(
   "/Users/alexdevoid/Documents/TEXTGRAPHAI/README.md"
   "/Users/alexdevoid/Documents/TEXTGRAPHAI/journalistic-entity-extraction/Dockerfile"
    "/Users/alexdevoid/Documents/TEXTGRAPHAI/journalistic-entity-extraction/journalistic_entity_extraction/main.py"
    "/Users/alexdevoid/Documents/TEXTGRAPHAI/journalistic-entity-extraction/journalistic_entity_extraction/services/rag.py"
    "/Users/alexdevoid/Documents/TEXTGRAPHAI/journalistic-entity-extraction/journalistic_entity_extraction/services/knowledge_graph.py"
    "/Users/alexdevoid/Documents/TEXTGRAPHAI/journalistic-entity-extraction/journalistic_entity_extraction/services/retrieval.py"
    "/Users/alexdevoid/Documents/TEXTGRAPHAI/journalistic-entity-extraction/journalistic_entity_extraction/models.py"
    "/Users/alexdevoid/Documents/TEXTGRAPHAI/journalistic-entity-extraction/journalistic_entity_extraction/schemas.py"
    "/Users/alexdevoid/Documents/TEXTGRAPHAI/journalistic-entity-extraction/journalistic_entity_extraction/database.py"
    "/Users/alexdevoid/Documents/TEXTGRAPHAI/graphrag_integration.py"
    "/Users/alexdevoid/Documents/TEXTGRAPHAI/journalistic-entity-extraction/requirements.txt"
    "/Users/alexdevoid/Documents/TEXTGRAPHAI/journalistic-entity-extraction/setup.py"
    "/Users/alexdevoid/Documents/TEXTGRAPHAI/textgraphai/cli.py"
    "/Users/alexdevoid/Documents/TEXTGRAPHAI/textgraphai/core.py"
    "/Users/alexdevoid/Documents/TEXTGRAPHAI/textgraphai/services/rag.py"
    "/Users/alexdevoid/Documents/TEXTGRAPHAI/journalistic-entity-extraction/tests/test_main.py"
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
