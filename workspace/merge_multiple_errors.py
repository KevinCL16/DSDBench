import json
import itertools
import random


def restore_original_code(modified_code, error_versions):
    """
    Restore the initial error-free code by replacing modified lines with original lines,
    handling missing or empty values.
    """
    lines = modified_code.split("\n")
    for error in error_versions:
        original_line = error.get("original_line", "").strip()
        modified_line = error.get("modified_line", "").strip()
        if original_line and modified_line:
            # Replace modified lines with original lines
            lines = [original_line if line.strip() == modified_line else line for line in lines]
    return "\n".join(lines)


def merge_errors_all_combinations(data_entry):
    """
    Merge multiple errors into one modified_code by randomly selecting some errors from error_versions.
    Handle missing values gracefully and ensure at least two errors are present for merging.
    """
    error_versions = data_entry.get("error_versions", [])
    if len(error_versions) < 2:
        return None  # Skip entries with less than 2 errors

    modified_code = error_versions[0]["modified_code"]  # Take the first version's code as the base

    # Step 1: Restore the original error-free code
    original_code = restore_original_code(modified_code, error_versions)

    all_combinations_info = []
    # Step 2: Iterate through all combinations of errors (from 2 up to the total number of errors)
    for num_errors_to_merge in range(2, len(error_versions) + 1):
        for selected_errors in itertools.combinations(error_versions, num_errors_to_merge):
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


def generate_multiple_merged_samples(data_entry, num_samples):
    """
    Generate multiple merged error samples from a single data entry by randomly selecting from all possible combinations.
    """
    all_combinations = merge_errors_all_combinations(data_entry)
    if not all_combinations:
        return []  # Return empty list if no combinations are generated (less than 2 errors)

    num_combinations_available = len(all_combinations)
    num_samples_to_generate = min(num_samples, num_combinations_available) # Ensure not to sample more than available combinations

    merged_samples = random.sample(all_combinations, num_samples_to_generate) # Randomly sample from all combinations
    return merged_samples


def main(input_file, output_file):
    # Read JSONL data
    with open(input_file, 'r') as file:
        data = [json.loads(line) for line in file]

    # Generate merged error samples for each entry and add IDs
    all_merged_samples = []
    print(f"目前有{len(data)}条可供合并的数据")
    merged_sample_id_counter = 0  # Initialize counter for merged sample IDs
    for entry in data:
        merged_samples = generate_multiple_merged_samples(entry, num_samples=8)
        for sample in merged_samples:
            sample['id'] = merged_sample_id_counter  # Assign unique ID
            merged_sample_id_counter += 1  # Increment counter
            all_merged_samples.append(sample)

    print(f"生成了{len(all_merged_samples)}条多错误数据")
    # Save results to a new JSONL file
    with open(output_file, 'w') as file:
        for sample in all_merged_samples:
            file.write(json.dumps(sample) + '\n')

    print(f"Merged samples saved to {output_file}")


if __name__ == "__main__":
    input_file = r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\benchmark_evaluation\bench_annotation_for_multi_error_generation.jsonl"  # 输入文件路径
    output_file = r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\benchmark_evaluation\bench_final_annotation_with_multi_errors_v2.jsonl"  # 输出文件路径
    main(input_file, output_file)
