import pandas as pd
from pathlib import Path
from collections import defaultdict
import re

output_root = Path("/path/to/input/directory")

index_to_documents = defaultdict(set)

for txt_path in output_root.rglob("*.txt"): 
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read().lower()

        # NORMALIZE TEXT SAME WAY AS `index_extraction.py`
        tokens = re.findall(r"\b\w+\b", text)  # Extract individual words
        text_normalized = " ".join(tokens)  

        relative_path = str(txt_path.relative_to(output_root))
      
        # known_indices_dict is in `indices.py`
        for index_key, patterns in known_indices_dict.items():
            for pattern in patterns:
                if re.search(pattern, text_normalized):  
                    index_to_documents[index_key].add(relative_path)
                    break  # Only count once per index per document
    except Exception as e:
        print(f"Error processing file {txt_path}: {e}")
        continue

summary_data = []
for idx, docs in sorted(index_to_documents.items(), key=lambda x: -len(x[1])):
    summary_data.append({
        "index": idx,
        "mention_count": len(docs),
        "documents": "; ".join(sorted(docs)),
    })

summary_df = pd.DataFrame(summary_data)
