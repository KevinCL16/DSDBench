#!/usr/bin/env python
"""
Single Bug Evaluation Script for DSDBench-Open
This script runs the evaluation for single-bug scenarios.
"""
import os
import sys
import subprocess
import argparse
import json
import importlib

def generate_result_filename(config_path):
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
        
        # Replace path separators with dots for import
        module_path = config_path.replace('/', '.').replace('\\', '.')
        
        # Import the specified module
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
        
        # For run_single_bug_eval.py, we want a relative path since we'll change directory
        # The file will be created in workspace/benchmark_evaluation directory
        # So we just need the filename, not the full path
        
        return filename
        
    except Exception as e:
        print(f"Warning: Could not generate automatic filename from config: {e}")
        # Fallback to default
        return 'workspace/benchmark_evaluation/eval_result.jsonl'

def main():
    # Generate default filename from config
    config_path = "config/single_bug_eval_agent_config.py"
    default_filename = generate_result_filename(config_path)
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='DSDBench-Open: Single Bug Evaluation')
    parser.add_argument('--result-file', type=str, default=default_filename,
                      help=f'Path to save the evaluation results (default: {default_filename})')
    args = parser.parse_args()
    
    # Print the result file being used
    print(f"Using result file: {args.result_file}")
    
    # Run the workflow with single-bug evaluation config
    print("Running workflow with single-bug evaluation configuration...")
    workflow_cmd = ["python", "workflow_generic.py", "--config", "config/single_bug_eval_agent_config.py", "--result-file", args.result_file]
    workflow_process = subprocess.run(workflow_cmd, check=True)
    if workflow_process.returncode != 0:
        print("Error: Workflow execution failed.")
        sys.exit(1)
    
    # Store the original directory before changing
    original_dir = os.getcwd()
    
    # Change directory to benchmark_evaluation
    print("\nChanging directory to benchmark_evaluation...")
    os.chdir("workspace/benchmark_evaluation")
    
    # Convert result file path to absolute path if it's relative
    # Since we're now in workspace/benchmark_evaluation, use current directory as base
    if not os.path.isabs(args.result_file):
        result_file_path = os.path.abspath(args.result_file)
    else:
        # If it's absolute, check if it's in the current directory
        if args.result_file.startswith(original_dir):
            # Convert to relative path from current directory
            result_file_path = os.path.basename(args.result_file)
        else:
            result_file_path = args.result_file
    
    # Run evaluation script
    print("Computing evaluation results...")
    eval_cmd = ["python", "compute_single_eval_results.py", "--result-file", result_file_path]
    eval_process = subprocess.run(eval_cmd, check=True)
    if eval_process.returncode != 0:
        print("Error: Evaluation computation failed.")
        sys.exit(1)
    
    print("\nSingle-bug evaluation completed successfully.")


if __name__ == "__main__":
    main()
