import json
import argparse
import os
from tqdm import tqdm


def count_errors(file_path):
    """
    Count the total number of error versions in a JSONL file.
    
    Args:
        file_path: Path to the JSONL file
        
    Returns:
        total_errors: Number of error versions
        total_queries: Number of queries
    """
    total_errors = 0
    total_queries = 0

    with open(file_path, "r", encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            error_versions = data.get("error_versions", [])
            total_errors += len(error_versions)
            total_queries += 1

    return total_errors, total_queries


def load_jsonl_files(file_paths):
    """
    Read multiple JSONL files and merge all data into a single list.
    
    Args:
        file_paths: List of paths to JSONL files
        
    Returns:
        all_data: List of all data entries
    """
    all_data = []
    for file_path in file_paths:
        with open(file_path, "r", encoding='utf-8') as f:
            for line in f:
                all_data.append(json.loads(line))
    return all_data


def merge_data(data_list):
    """
    Merge data entries based on the question field, combining error_versions.
    Only keep essential fields in error_versions.
    
    Args:
        data_list: List of data entries to merge
        
    Returns:
        merged_data: List of merged data entries
    """
    merged_dict = {}

    for entry in tqdm(data_list, desc="Merging data"):
        question = entry.get("question")
        error_versions = entry.get("error_versions", [])

        # Only keep specified fields for each error_version
        filtered_error_versions = [
            {
                "modified_code": version.get("modified_code"),
                "execution_output": version.get("execution_output"),
                "effect_error_line": version.get("effect_error_line"),
                "cause_error_line": version.get("cause_error_line"),
                "original_line": version.get("original_line", ""),
                "modified_line": version.get("modified_line", "")
            }
            for version in error_versions
        ]

        if question in merged_dict:
            # If question already exists, merge the filtered error_versions
            merged_dict[question]["error_versions"].extend(filtered_error_versions)
        else:
            # If question doesn't exist, create a new entry
            merged_dict[question] = {
                "id": None,  # ID will be reassigned
                "question": question,
                "error_versions": filtered_error_versions
            }

    # Reassign consecutive IDs
    merged_data = []
    for new_id, (question, merged_entry) in enumerate(merged_dict.items(), start=1):
        merged_entry["id"] = new_id
        merged_data.append(merged_entry)

    return merged_data


def save_to_jsonl(data, output_path):
    """
    Save merged data to a new JSONL file.
    
    Args:
        data: List of data entries to save
        output_path: Path to output JSONL file
    """
    with open(output_path, "w", encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Merge multiple annotated JSONL files')
    parser.add_argument('--input', nargs='+', required=True,
                       help='Paths to input JSONL files')
    parser.add_argument('--output', default='workspace/benchmark_evaluation/bench_final_annotation_single_error.jsonl',
                       help='Path to output merged JSONL file')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # 1. Load all JSONL files
    print(f"Loading {len(args.input)} JSONL files...")
    all_data = load_jsonl_files(args.input)
    
    # 2. Merge data based on question
    print(f"Merging {len(all_data)} data entries...")
    merged_data = merge_data(all_data)
    
    # 3. Save merged data to the new JSONL file
    save_to_jsonl(merged_data, args.output)
    print(f"Merged {len(all_data)} data entries into {len(merged_data)} unique questions.")
    print(f"Result saved to {args.output}")
    
    # 4. Count errors in the merged file
    total_errors, total_queries = count_errors(args.output)
    print(f"Total questions in merged file: {total_queries}")
    print(f"Total error versions in merged file: {total_errors}")
