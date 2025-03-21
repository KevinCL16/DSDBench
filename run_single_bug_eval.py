#!/usr/bin/env python
"""
Single Bug Evaluation Script for DSDBench-Open
This script runs the evaluation for single-bug scenarios.
"""
import os
import sys
import subprocess

def main():
    # Run the workflow with single-bug evaluation config
    print("Running workflow with single-bug evaluation configuration...")
    workflow_cmd = ["python", "workflow_generic.py", "--config", "config/single_bug_eval_agent_config.py"]
    workflow_process = subprocess.run(workflow_cmd, check=True)
    if workflow_process.returncode != 0:
        print("Error: Workflow execution failed.")
        sys.exit(1)
    
    # Change directory to benchmark_evaluation
    print("\nChanging directory to benchmark_evaluation...")
    os.chdir("workspace/benchmark_evaluation")
    
    # Run evaluation script
    print("Computing evaluation results...")
    eval_cmd = ["python", "compute_eval_result.py"]
    eval_process = subprocess.run(eval_cmd, check=True)
    if eval_process.returncode != 0:
        print("Error: Evaluation computation failed.")
        sys.exit(1)
    
    print("\nSingle-bug evaluation completed successfully.")

if __name__ == "__main__":
    main() 