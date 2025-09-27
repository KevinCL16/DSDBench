#!/usr/bin/env python
"""
vLLM Single Bug Evaluation Script for DSDBench-Open
This script runs the evaluation for single-bug scenarios using vLLM backend.
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
        eval_type = "single_bug_vllm"  # Mark as vLLM evaluation
        
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
        
        return filename
        
    except Exception as e:
        print(f"Warning: Could not generate automatic filename from config: {e}")
        # Fallback to default
        return 'workspace/benchmark_evaluation/eval_result_vllm.jsonl'


def check_vllm_server():
    """Check if vLLM server is running."""
    try:
        from agents.vllm_client import check_vllm_server_health
        if check_vllm_server_health():
            print("✓ vLLM server is running and healthy")
            return True
        else:
            print("✗ vLLM server is not responding")
            return False
    except Exception as e:
        print(f"✗ Error checking vLLM server: {e}")
        return False


def main():
    # Check vLLM server first
    print("Checking vLLM server status...")
    if not check_vllm_server():
        print("\nPlease make sure your vLLM server is running before proceeding.")
        print("You can start a vLLM server with:")
        print("python -m vllm.entrypoints.openai.api_server --model <model_name> --port 8000")
        sys.exit(1)
    
    # Generate default filename from config
    config_path = "config/vllm_single_bug_eval_agent_config.py"
    default_filename = generate_result_filename(config_path)
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='DSDBench-Open: vLLM Single Bug Evaluation')
    parser.add_argument('--result-file', type=str, default=default_filename,
                      help=f'Path to save the evaluation results (default: {default_filename})')
    parser.add_argument('--config', type=str, default=config_path,
                      help=f'Path to vLLM configuration file (default: {config_path})')
    args = parser.parse_args()
    
    # Print the result file being used
    print(f"Using result file: {args.result_file}")
    print(f"Using config file: {args.config}")
    
    # Run the workflow with vLLM single-bug evaluation config
    print("Running workflow with vLLM single-bug evaluation configuration...")
    workflow_cmd = ["python", "workflow_generic.py", "--config", args.config, "--result-file", args.result_file]
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
    
    print("\nvLLM single-bug evaluation completed successfully.")


if __name__ == "__main__":
    main()
