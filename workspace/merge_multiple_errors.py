import json
import itertools
import random
import argparse
import os
from tqdm import tqdm


def restore_original_code(modified_code, error_versions):
    """
    Restore the initial error-free code by replacing modified lines with original lines.
    
    Args:
        modified_code: Code with errors
        error_versions: List of error versions containing original and modified lines
        
    Returns:
        Original code with errors corrected
    """
    lines = modified_code.split("\n")
    for error in error_versions:
        original_line = error.get("original_line", "").strip()
        modified_line = error.get("modified_line", "").strip()
        if original_line and modified_line:
            # Replace modified lines with original lines
            lines = [original_line if line.strip() == modified_line else line for line in lines]
    return "\n".join(lines)


def merge_errors_all_combinations(data_entry, max_combinations=None):
    """
    Merge multiple errors into one modified_code by generating combinations of errors.
    
    Args:
        data_entry: Data entry containing error versions
        max_combinations: Maximum number of combinations to generate per entry
        
    Returns:
        List of merged error combinations
    """
    error_versions = data_entry.get("error_versions", [])
    if len(error_versions) < 2:
        return []  # Skip entries with less than 2 errors

    modified_code = error_versions[0]["modified_code"]  # Take the first version's code as the base

    # Step 1: Restore the original error-free code
    original_code = restore_original_code(modified_code, error_versions)

    all_combinations_info = []
    # Step 2: Iterate through all combinations of errors (from 2 up to the total number of errors)
    for num_errors_to_merge in range(2, min(len(error_versions) + 1, 5)):  # Limit to 4 errors max
        combinations = list(itertools.combinations(error_versions, num_errors_to_merge))
        
        # Limit the number of combinations per error count if max_combinations is specified
        if max_combinations and len(combinations) > max_combinations // (len(error_versions) - 1):
            combinations = random.sample(combinations, max_combinations // (len(error_versions) - 1))
        
        for selected_errors in combinations:
            # Step 3: Apply the selected errors to the original code
            merged_code_lines = original_code.split("\n")
            for error in selected_errors:
                original_line = error.get("original_line", "").strip()
                modified_line = error.get("modified_line", "").strip()
                if original_line and modified_line:
                    # Replace the original line with the modified line
                    merged_code_lines = [modified_line if line.strip() == original_line else line for line in
                                        merged_code_lines]

            # Step 4: Merge other information
            combined_error_info = {
                "question": data_entry.get("question"),
                "modified_code": "\n".join(merged_code_lines),
                "error_count": num_errors_to_merge,
                "execution_outputs": [error.get("execution_output", "") for error in selected_errors],
                "effect_error_lines": [error.get("effect_error_line", "") for error in selected_errors],
                "cause_error_lines": [error.get("cause_error_line", "") for error in selected_errors],
                "original_sample_id": data_entry.get("id", "unknown")
            }
            all_combinations_info.append(combined_error_info)

    return all_combinations_info


def generate_multi_bug_dataset(input_file, output_file, samples_per_entry=5, max_total_samples=None):
    """
    Generate a dataset with multiple bugs per entry from single-bug annotations.
    
    Args:
        input_file: Path to input JSONL file with single-bug annotations
        output_file: Path to output JSONL file for multi-bug dataset
        samples_per_entry: Number of multi-bug samples to generate per entry
        max_total_samples: Maximum total samples in the output dataset
    """
    # Read JSONL data
    with open(input_file, 'r', encoding='utf-8') as file:
        data = [json.loads(line) for line in file]

    # Generate merged error samples for each entry and add IDs
    all_merged_samples = []
    print(f"Processing {len(data)} entries for multi-bug generation")
    
    for entry in tqdm(data, desc="Generating multi-bug samples"):
        # Calculate max combinations based on the total samples limit
        max_combinations = None
        if max_total_samples:
            max_combinations = max(1, max_total_samples // len(data))
        
        merged_samples = merge_errors_all_combinations(entry, max_combinations)
        
        # Limit samples per entry
        if merged_samples and len(merged_samples) > samples_per_entry:
            merged_samples = random.sample(merged_samples, samples_per_entry)
            
        for sample in merged_samples:
            sample['id'] = len(all_merged_samples)  # Assign unique ID
            all_merged_samples.append(sample)
            
            # Check if we've reached the maximum total samples
            if max_total_samples and len(all_merged_samples) >= max_total_samples:
                break
                
        # Check again after processing this entry
        if max_total_samples and len(all_merged_samples) >= max_total_samples:
            break

    print(f"Generated {len(all_merged_samples)} multi-bug samples")
    
    # Save results to a new JSONL file
    with open(output_file, 'w', encoding='utf-8') as file:
        for sample in all_merged_samples:
            file.write(json.dumps(sample, ensure_ascii=False) + '\n')

    print(f"Multi-bug dataset saved to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate multi-bug dataset from single-bug annotations')
    parser.add_argument('--input', default='workspace/benchmark_evaluation/bench_final_annotation_single_error.jsonl',
                       help='Path to input JSONL file with single-bug annotations')
    parser.add_argument('--output', default='workspace/benchmark_evaluation/bench_final_annotation_multi_errors.jsonl',
                       help='Path to output JSONL file for multi-bug dataset')
    parser.add_argument('--samples_per_entry', type=int, default=5,
                       help='Number of multi-bug samples to generate per entry')
    parser.add_argument('--max_total_samples', type=int, default=None,
                       help='Maximum total samples in the output dataset')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Generate multi-bug dataset
    generate_multi_bug_dataset(
        args.input, 
        args.output, 
        samples_per_entry=args.samples_per_entry,
        max_total_samples=args.max_total_samples
    )
