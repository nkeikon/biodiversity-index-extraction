import re
from pathlib import Path
from collections import defaultdict
import pandas as pd

converted_root = Path("/path/to/Redacted_Proposals_converted")

def normalize_index_phrase(phrase):
    """
    Normalize index phrases by:
    - Converting to lowercase.
    - Stripping leading/trailing non-word characters.
    - Removing leading stopwords (e.g., "the", "of", "a", "an", "and").
    """
    phrase = phrase.lower().strip()
    phrase = re.sub(r'^[\W_]+|[\W_]+$', '', phrase)  # Remove non-word chars at start/end
    phrase = re.sub(r'^(the|of|a|an|and)\s+', '', phrase)  # Remove leading stopwords
    return phrase

# Step 1: Process all text files to extract raw index phrases
results = []

for txt_path in converted_root.rglob("*.txt"):
    folder = txt_path.parent.relative_to(converted_root)  # Get the folder relative to the root
    filename = txt_path.stem  # Get the filename without the .txt extension
    found_indices = set()

    try:
        with txt_path.open("r", encoding="utf-8") as f:
            text = f.read()

        # Tokenize the text into individual words (lowercased)
        tokens = re.findall(r"\b\w+\b", text.lower())

        # Extract phrases containing "index" or "indices" and their preceding words
        for i, token in enumerate(tokens):
            if token in ["index", "indices"]:
                start = max(i - 3, 0)  # Grab up to 3 tokens before the keyword
                phrase = " ".join(tokens[start:i+1]).strip()
                found_indices.add(phrase)
    except Exception as e:
        found_indices.add(f"Error reading {txt_path.name}: {e}")

    # If no indices were found, mark as "None"
    if not found_indices:
        found_indices.add("None")

    results.append({
        "folder": str(folder),
        "filename": f"{filename}.txt",
        "indices_found": "; ".join(sorted(found_indices))
    })

# Step 2: Normalize and clean the index phrases
index_to_files = defaultdict(set)

for result in results:
    index_phrases = result["indices_found"].split("; ")
    filename = f"{result['folder']}/{result['filename']}"
    for phrase in index_phrases:
        if phrase and phrase != "None":
            cleaned = normalize_index_phrase(phrase)
            index_to_files[cleaned].add(filename)

# Step 3: Prepare data for the summary DataFrame
summary_data = [
    {
        "index_phrase": phrase,                          # Normalized index phrase
        "mention_count": len(files),                    # Count of documents where the phrase appears
        "documents": "; ".join(sorted(files))           # List of filenames where the phrase is found
    }
    for phrase, files in sorted(index_to_files.items(), key=lambda x: -len(x[1])) 
]
