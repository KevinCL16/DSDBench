import json
import argparse
import os
import sys
import importlib

def generate_result_filename_from_config(config_path):
    """
    Generate result filename based on config information.
    
    Args:
        config_path (str): Path to the configuration file
        
    Returns:
        str: Generated filename
    """
    try:
        # Load configuration
        if config_path.endswith('.py'):
            config_path = config_path[:-3]  # Remove .py extension
        
        # Handle absolute path for import
        if os.path.isabs(config_path):
            # For absolute paths, we need to add to sys.path
            config_dir = os.path.dirname(config_path)
            if config_dir not in sys.path:
                sys.path.insert(0, config_dir)
            module_name = os.path.basename(config_path)
            if module_name.endswith('.py'):
                module_name = module_name[:-3]  # Remove .py extension
            config_module = importlib.import_module(module_name)
        else:
            # For relative paths, replace path separators with dots for import
            module_path = config_path.replace('/', '.').replace('\\', '.')
            if module_path.endswith('.py'):
                module_path = module_path[:-3]  # Remove .py extension
            config_module = importlib.import_module(module_path)
        agent_config = config_module.AGENT_CONFIG
        workflow = config_module.WORKFLOW
        
        # Extract information from config
        model_type = None
        data_ids = None
        data_range = None
        eval_type = "multi_bug"  # Multi bug evaluation
        
        # Get model type from workflow
        if workflow and len(workflow) > 0:
            step = workflow[0]
            if 'args' in step and 'model_type' in step['args']:
                model_type = step['args']['model_type']
            if 'data_ids' in step:
                data_ids = step['data_ids']
            if 'data_range' in step:
                data_range = step['data_range']
        
        # Generate filename components
        model_name = model_type.replace('/', '_').replace(':', '_') if model_type else 'unknown_model'
        
        # Handle data IDs and ranges
        if data_range:
            # Handle data range (e.g., [1, 10] means samples 1 to 10)
            start, end = data_range
            id_str = f"range_{start}_{end}"
        elif data_ids:
            if len(data_ids) == 1:
                id_str = f"id_{data_ids[0]}"
            else:
                id_str = f"ids_{'_'.join(map(str, data_ids))}"
        else:
            id_str = "all_ids"
        
        # Generate filename
        filename = f"eval_{model_name}_{eval_type}_{id_str}.jsonl"
        
        # Ensure it's in the workspace directory
        workspace_dir = agent_config.get('workspace', './workspace/benchmark_evaluation')
        if not filename.startswith(workspace_dir):
            filename = os.path.join(workspace_dir, filename)
        
        # Normalize path separators
        filename = os.path.normpath(filename)
        
        return filename
        
    except Exception as e:
        print(f"Warning: Could not generate automatic filename from config: {e}")
        # Fallback to default
        return 'eval_Qwen2.5-72B-Instruct_multi_rubber_duck_CoT_on_multi_bench_v2.jsonl'

def main():
    # Use a simple fallback filename that matches the expected pattern
    default_filename = "eval_Qwen_Qwen2.5-72B-Instruct_multi_bug_ids_4_9_10_109_110_208_309.jsonl"
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Compute multi bug evaluation results')
    parser.add_argument('--result-file', type=str, default=default_filename,
                      help=f'Path to the evaluation results file (default: {default_filename})')
    args = parser.parse_args()
    
    eval_jsonl_file = args.result_file
    ground_truth_jsonl_file = 'bench_final_annotation_multi_errors.jsonl'
    
    # Convert to absolute path if it's a relative path
    if not os.path.isabs(eval_jsonl_file):
        # If it's a relative path, make it relative to the current working directory
        eval_jsonl_file = os.path.abspath(eval_jsonl_file)
    
    # Print the result file being used
    print(f"Using result file: {eval_jsonl_file}")
    
    # Check if the result file exists
    if not os.path.exists(eval_jsonl_file):
        print(f"Error: Result file '{eval_jsonl_file}' not found.")
        print(f"Current working directory: {os.getcwd()}")
        return
    
    model_type = eval_jsonl_file.split("_")[1]

    # Exact Match Metrics per ID
    exact_match_metrics_per_id = calculate_evaluation_scores_exact_match_per_id(eval_jsonl_file, ground_truth_jsonl_file)
    print(f"\n{model_type} Exact Match Metrics per ID (Precision, Recall, F1, Accuracy) for Multi-Bug Detection:")
    print(json.dumps(exact_match_metrics_per_id, indent=4))

def calculate_ground_truth_error_counts(ground_truth_file_path):
    """
    Calculates the number of ground truth errors for each ID from the ground truth JSONL file.
    (rest of the function remains the same)
    """
    gt_error_counts = {}
    with open(ground_truth_file_path, 'r') as f:
        for line in f:
            gt_data = json.loads(line)
            id_val = gt_data['id']
            if id_val not in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310]:
                continue
            # Assuming cause_error_lines (or effect_error_lines) indicates the number of GT errors
            gt_error_count = len(gt_data.get('cause_error_lines', []) or gt_data.get('effect_error_lines', []))
            gt_error_counts[id_val] = gt_error_count
    return gt_error_counts

def calculate_evaluation_scores_exact_match_per_id(eval_jsonl_file_path, ground_truth_file_path):
    """
    Calculates evaluation metrics based on exact match of predicted and ground truth error sets,
    evaluated PER ID (per data instance).

    TP: For an ID, model predicts exactly the same set of errors as ground truth in at least one version.
    FP: For an ID, model predicts a different set of errors in ALL versions, and at least one version is non-empty.
    FN: For an ID, ground truth has errors, but model predicts an empty set of errors in ALL versions (or eval_result is empty).
    """
    gt_error_counts_dict = calculate_ground_truth_error_counts(ground_truth_file_path) # Get GT error counts per ID

    dimension_metrics_overall = {  # Initialize overall dimension metrics
        "cause_line": {"TP": 0, "FP": 0, "FN": 0, "Total_IDs": 0},
        # Added GT_Instances to track total GT instances per dimension
        "effect_line": {"TP": 0, "FP": 0, "FN": 0, "Total_IDs": 0},
        "error_type": {"TP": 0, "FP": 0, "FN": 0, "Total_IDs": 0},
        "error_message": {"TP": 0, "FP": 0, "FN": 0, "Total_IDs": 0},
    }

    with open(eval_jsonl_file_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            id_val = data['id']
            if id_val not in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310]:
                continue
            eval_results_list = data['eval_result'] # list of error versions
            gt_error_count = gt_error_counts_dict.get(id_val, 0)
            for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
                dimension_metrics_overall[dimension]["Total_IDs"] += 1

            is_tp_for_id = False # Flag to check if it's TP for this ID
            all_versions_empty = True # Flag to check if all versions are empty predictions

            if eval_results_list:
                all_versions_empty = False
                for error_version_eval_results in eval_results_list:
                    if len(error_version_eval_results) != gt_error_count:
                        for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
                            dimension_metrics_overall[dimension]["FP"] += 1
                    else:
                        for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
                            for single_error_eval in error_version_eval_results:
                                score_key = f"{dimension}_score"
                                try:
                                    is_fp_dimension = (
                                        single_error_eval[score_key] != 1 if dimension != "error_message" else
                                        single_error_eval[score_key] < 0.75)
                                except KeyError as e:
                                    print(f"{e}\nid:{id_val}")

                                if is_fp_dimension:
                                    dimension_metrics_overall[dimension]["FP"] += 1
                                    break
                            if not is_fp_dimension:
                                dimension_metrics_overall[dimension]["TP"] += 1

            else:
                if all_versions_empty:  # All versions are empty predictions -> FN
                    for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
                        dimension_metrics_overall[dimension]["FN"] += 1

    aggregated_dimension_metrics = {}
    for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
        tp = dimension_metrics_overall[dimension]["TP"]
        fp = dimension_metrics_overall[dimension]["FP"]
        # Corrected FN calculation: FN = Total Ground Truth Instances - (TP + FP) for each dimension
        fn = dimension_metrics_overall[dimension]["FN"]
        total_ids = dimension_metrics_overall[dimension]["Total_IDs"]

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn + fp) if (tp + fn + fp) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = tp / total_ids if total_ids > 0 else 0 # Accuracy: Exact match IDs / Total IDs

        aggregated_dimension_metrics[dimension] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "accuracy": accuracy,
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "Total_IDs": dimension_metrics_overall[dimension]["Total_IDs"]
        }

    return aggregated_dimension_metrics


if __name__ == "__main__":
    main()