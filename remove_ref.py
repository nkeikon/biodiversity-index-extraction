import re
from pathlib import Path

def check_for_references(txt_path):
    """
    Check if a text file contains a reference section using improved pattern matching.
    """
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        lines = text.split('\n')
        text_lower = text.lower()
        
        # 1. Look for reference section headers (more specific patterns)
        reference_header_patterns = [
            r'^references\s*$',
            r'^bibliography\s*$',
            r'^literature\s+cited\s*$',
            r'^works\s+cited\s*$',
            r'^\d+\.?\s*references\s*$',  # "7. References" or "7 References"
            r'^\d+\.\s*bibliography\s*$'
        ]
        
        header_found = False
        header_line_idx = -1
        
        for i, line in enumerate(lines):
            line_clean = line.strip().lower()
            for pattern in reference_header_patterns:
                if re.match(pattern, line_clean):
                    header_found = True
                    header_line_idx = i
                    break
            if header_found:
                break
        
        # 2. Look for consecutive reference-style entries
        def count_reference_entries_after_header(start_idx):
            """Count reference-style entries after a header"""
            if start_idx == -1:
                return 0, 0
            
            ref_count = 0
            consecutive_refs = 0
            max_consecutive = 0
            
            for i in range(start_idx + 1, min(start_idx + 50, len(lines))):
                if i >= len(lines):
                    break
                    
                line = lines[i].strip()
                
                if not line:
                    if consecutive_refs > 0:
                        consecutive_refs = 0
                    continue
                
                # Reference patterns
                ref_patterns = [
                    r'^[A-Z][a-z]+,\s+[A-Z]\..*\(\d{4}\)',  # Smith, J. ... (2020)
                    r'^[A-Z][a-z]+\s+[A-Z]\.,.*\(\d{4}\)',  # Smith J., ... (2020)
                    r'^[A-Z][a-z]+,\s+[A-Z][a-z]+.*\(\d{4}\)',  # Smith, John ... (2020)
                    r'^[A-Z][a-z]+\s+et\s+al\..*\(\d{4}\)',  # Smith et al. ... (2020)
                    r'^\[\d+\]',  # [1], [2], etc.
                    r'^\d+\.',    # 1., 2., etc.
                    r'.*doi:\s*10\.\d+',
                    r'.*https?://',
                ]
                
                is_reference = False
                for pattern in ref_patterns:
                    if re.search(pattern, line):
                        is_reference = True
                        break
                
                if is_reference:
                    ref_count += 1
                    consecutive_refs += 1
                    max_consecutive = max(max_consecutive, consecutive_refs)
                else:
                    consecutive_refs = 0
                    if ref_count > 0:
                        non_ref_streak = 0
                        for j in range(i, min(i + 3, len(lines))):
                            if j < len(lines) and lines[j].strip():
                                if not any(re.search(p, lines[j]) for p in ref_patterns):
                                    non_ref_streak += 1
                        if non_ref_streak >= 3:
                            break
            
            return ref_count, max_consecutive
        
        # 3. Look for reference clusters anywhere in the document
        def find_reference_clusters():
            """Find clusters of reference-like entries anywhere in the document"""
            clusters = []
            current_cluster = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_cluster > 0:
                        if current_cluster >= 3:
                            clusters.append(current_cluster)
                        current_cluster = 0
                    continue
                
                ref_patterns = [
                    r'^[A-Z][a-z]+,\s+[A-Z]\..*\(\d{4}\)',
                    r'^[A-Z][a-z]+\s+[A-Z]\.,.*\(\d{4}\)',
                    r'^[A-Z][a-z]+,\s+[A-Z][a-z]+.*\(\d{4}\)',
                    r'^[A-Z][a-z]+\s+et\s+al\..*\(\d{4}\)',
                    r'^\[\d+\].*\(\d{4}\)',
                    r'^\d+\..*\(\d{4}\)',
                ]
                
                is_reference = any(re.search(pattern, line) for pattern in ref_patterns)
                
                if is_reference:
                    current_cluster += 1
                else:
                    if current_cluster >= 3:
                        clusters.append(current_cluster)
                    current_cluster = 0
            
            if current_cluster >= 3:
                clusters.append(current_cluster)
            
            return clusters
        
        ref_count_after_header, max_consecutive_after_header = count_reference_entries_after_header(header_line_idx)
        reference_clusters = find_reference_clusters()
        largest_cluster = max(reference_clusters) if reference_clusters else 0
        
        likely_has_references = (
            (header_found and ref_count_after_header >= 3) or
            (largest_cluster >= 5) or
            (len(reference_clusters) > 0 and sum(reference_clusters) >= 8)
        )
        
        return {
            'file': txt_path.name,
            'has_reference_header': header_found,
            'refs_after_header': ref_count_after_header,
            'max_consecutive_refs': max_consecutive_after_header,
            'reference_clusters': reference_clusters,
            'largest_cluster': largest_cluster,
            'total_clustered_refs': sum(reference_clusters),
            'likely_has_references': likely_has_references
        }
        
    except Exception as e:
        return {
            'file': txt_path.name,
            'error': str(e)
        }

def analyze_reference_sections(folder_path):
    """
    Analyze all text files in a folder for reference sections - only show files with references.
    """
    folder = Path(folder_path)
    txt_files = list(folder.rglob("*.txt"))
    
    if not txt_files:
        print(f"No .txt files found in {folder_path}")
        return
    
    results = []
    files_with_references = []
    
    print(f"Analyzing {len(txt_files)} text files for reference sections...\n")
    print("FILES THAT LIKELY CONTAIN REFERENCES:")
    print("="*50)
    
    for txt_file in txt_files:
        result = check_for_references(txt_file)
        results.append(result)
        
        if 'error' not in result and result['likely_has_references']:
            files_with_references.append(result)
            
            print(f"✅ {result['file']}")
            
            if result['has_reference_header']:
                print(f"   📋 Reference header found, {result['refs_after_header']} refs follow")
            if result['largest_cluster'] > 0:
                print(f"   📚 Largest reference cluster: {result['largest_cluster']} entries")
            if result['reference_clusters']:
                print(f"   🔢 Reference clusters: {result['reference_clusters']}")
            print()
    
    total_files = len(results)
    files_with_refs_count = len(files_with_references)
    files_with_errors = sum(1 for r in results if 'error' in r)
    
    print("="*60)
    print("SUMMARY:")
    print(f"Total files analyzed: {total_files}")
    print(f"Files with reference sections: {files_with_refs_count}")
    print(f"Files without reference sections: {total_files - files_with_refs_count - files_with_errors}")
    print(f"Files with errors: {files_with_errors}")
    
    if files_with_errors > 0:
        print(f"\nFiles with errors: {files_with_errors}")
    
    return results

if __name__ == "__main__":
    folder_path = "/path/to/your/converted/text/files" 
