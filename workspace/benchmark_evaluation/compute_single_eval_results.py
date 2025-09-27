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
        eval_type = "single_bug"  # Default for single bug evaluation
        
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
        return 'eval_gpt-4o_rubber_duck_on_bench_v3_succint_err_msg.jsonl'

def main():
    # Use a simple fallback filename that matches the expected pattern
    default_filename = "eval_openai_gpt-oss-120b_single_bug_id_2.jsonl"
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Compute single bug evaluation results')
    parser.add_argument('--result-file', type=str, default=default_filename,
                      help=f'Path to the evaluation results file (default: {default_filename})')
    args = parser.parse_args()
    
    eval_jsonl_file = args.result_file
    ground_truth_jsonl_file = 'bench_final_annotation_single_error.jsonl'
    
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
    
    # Calculate subset_total_errors dynamically
    subset_total_errors = get_subset_total_errors(eval_jsonl_file, ground_truth_jsonl_file)

    # Calculate dimension-wise metrics using the subset_total_errors
    dimension_wise_metrics = calculate_single_bug_evaluation_metrics(eval_jsonl_file, ground_truth_jsonl_file, subset_total_errors)

    # Read JSONL file to count eval results (predictions made) - optional, but good to know
    with open(eval_jsonl_file, 'r', encoding='utf-8') as file:
        records = [json.loads(line) for line in file]
    num_eval_results_counted = 0
    for record in records:
        if record["id"] not in [1, 2, 3, 4, 5, 51, 52, 53, 54, 55, 100, 101, 102, 103, 104, 151, 152, 153, 154, 155]:
            continue
        num_eval_results_counted += len(record["eval_result"])

    # Initialize total scores and max scores (rest of the code remains mostly the same)
    total_cause_line_score = 0
    total_effect_line_score = 0
    total_error_type_score = 0
    total_error_message_score = 0
    max_error_line_score = 0
    max_error_message_score = 0

    # Calculate scores
    for record in records:
        if record["id"] not in [1, 2, 3, 4, 5, 51, 52, 53, 54, 55, 100, 101, 102, 103, 104, 151, 152, 153, 154, 155]:
            continue
        for eval_result in record["eval_result"]:
            total_cause_line_score += eval_result["cause_line_score"]
            total_effect_line_score += eval_result["effect_line_score"]
            total_error_type_score += eval_result["error_type_score"]
            total_error_message_score += eval_result["error_message_score"]
            max_error_line_score += 1
            max_error_message_score += 1

    # Calculate the percentage scores
    cause_line_percentage = (total_cause_line_score / num_eval_results_counted) * 100 if num_eval_results_counted > 0 else 0
    effect_line_percentage = (total_effect_line_score / num_eval_results_counted) * 100 if num_eval_results_counted > 0 else 0
    error_type_percentage = (total_error_type_score / num_eval_results_counted) * 100 if num_eval_results_counted > 0 else 0
    error_message_percentage = (total_error_message_score / num_eval_results_counted) * 100 if num_eval_results_counted > 0 else 0

    # Print the overall scores
    print(f"Total annotated error number (for subset): {subset_total_errors}") # Updated total error count for subset
    print(f"Total detected error number (predictions made): {max_error_line_score}")
    print(f"Number of eval_results counted: {num_eval_results_counted}")
    print(f"\nOverall Cause Line Score: {cause_line_percentage:.2f}%")
    print(f"Overall Effect Line Score: {effect_line_percentage:.2f}%")
    print(f"Overall Error Type Score: {error_type_percentage:.2f}%")
    print(f"Overall Error Message Score: {error_message_percentage:.2f}%")

    model_type = eval_jsonl_file.split("_")[1]
    # Print dimension-wise metrics
    print(f"\n{model_type} Dimension-wise Metrics (Precision, Recall, F1, Accuracy) for Single-Bug Detection:")
    print(json.dumps(dimension_wise_metrics, indent=4))


def calculate_single_bug_evaluation_metrics(eval_jsonl_file_path, ground_truth_file_path, total_errors):
    """
    Calculates evaluation metrics (Precision, Recall, F1-score, Accuracy) for each dimension
    (cause_line, effect_line, error_type, error_message) for single-bug detection,
    using the updated TP, FP, FN definitions.

    Args:
        eval_jsonl_file_path (str): Path to the evaluation JSONL file.
        ground_truth_file_path (str): Path to the ground truth JSONL file.
        total_errors (int): **Total number of ground truth error instances in the evaluation subset.**

    Returns:
        dict: A dictionary containing aggregated metrics for each dimension.
    """

    dimension_metrics_overall = {  # Initialize overall metrics for each dimension
        "cause_line": {"TP": 0, "FP": 0, "FN": 0},
        "effect_line": {"TP": 0, "FP": 0, "FN": 0},
        "error_type": {"TP": 0, "FP": 0, "FN": 0},
        "error_message": {"TP": 0, "FP": 0, "FN": 0},
    }

    num_eval_results = 0

    with open(eval_jsonl_file_path, 'r', encoding='utf-8') as f:
        records = [json.loads(line) for line in f]

        for record in records:
            eval_results = record["eval_result"]
            if record["id"] not in [1, 2, 3, 4, 5, 51, 52, 53, 54, 55, 100, 101, 102, 103, 104, 151, 152, 153, 154, 155]:
                continue
            for eval_result in eval_results:
                num_eval_results += 1
                for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
                    score_key = f"{dimension}_score"
                    if dimension != "error_message":
                        is_tp_dimension = eval_result[score_key] == 1
                    else:
                        is_tp_dimension = eval_result[score_key] >= 0.75

                    if is_tp_dimension:
                        dimension_metrics_overall[dimension]["TP"] += 1
                    else:
                        dimension_metrics_overall[dimension]["FP"] += 1

    aggregated_dimension_metrics = {}

    for dimension in ["cause_line", "effect_line", "error_type", "error_message"]:
        dimension_metrics_overall[dimension]["FN"] = max(0, total_errors - (dimension_metrics_overall[dimension]["TP"] + dimension_metrics_overall[dimension]["FP"]))
        tp = dimension_metrics_overall[dimension]["TP"]
        fp = dimension_metrics_overall[dimension]["FP"]
        fn = dimension_metrics_overall[dimension]["FN"]

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn + fp) if (tp + fn + fp) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = tp / total_errors if total_errors > 0 else 0

        aggregated_dimension_metrics[dimension] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "accuracy": accuracy,
            "TP": tp,
            "FP": fp,
            "FN": fn,
        }

    return aggregated_dimension_metrics


def get_subset_total_errors(eval_jsonl_file_path, ground_truth_file_path):
    """
    Calculates the total number of ground truth errors for the subset of data
    present in the eval_jsonl_file.

    Args:
        eval_jsonl_file_path (str): Path to the evaluation JSONL file.
        ground_truth_file_path (str): Path to the ground truth JSONL file.

    Returns:
        int: Total number of ground truth errors in the evaluation subset.
    """
    eval_ids = set()
    with open(eval_jsonl_file_path, 'r') as f:
        for line in f:
            record = json.loads(line)
            if record["id"] not in [1, 2, 3, 4, 5, 51, 52, 53, 54, 55, 100, 101, 102, 103, 104, 151, 152, 153, 154,
                                    155]:
                continue
            eval_ids.add(record["id"]) # Assuming each record in eval_jsonl has an "id"

    subset_total_errors = 0
    with open(ground_truth_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            if data["id"] in eval_ids: # Check if the ground truth data's ID is in the eval IDs
                error_versions = data.get("error_versions", [])
                subset_total_errors += len(error_versions)
    return subset_total_errors


if __name__ == "__main__":
    main()