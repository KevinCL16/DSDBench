#!/usr/bin/env python
"""
Multi Bug Evaluation Script for DSDBench-Open
This script runs the evaluation for multi-bug scenarios.
"""
import os
import sys
import subprocess

def main():
    # Run the workflow with multi-bug evaluation config
    print("Running workflow with multi-bug evaluation configuration...")
    workflow_cmd = ["python", "workflow_generic.py", "--config", "config/multi_bug_eval_agent_config.py"]
    workflow_process = subprocess.run(workflow_cmd, check=True)
    if workflow_process.returncode != 0:
        print("Error: Workflow execution failed.")
        sys.exit(1)
    
    # Change directory to benchmark_evaluation
    print("\nChanging directory to benchmark_evaluation...")
    os.chdir("workspace/benchmark_evaluation")
    
    # Run evaluation script
    print("Computing evaluation results...")
    eval_cmd = ["python", "compute_multi_eval_results.py"]
    eval_process = subprocess.run(eval_cmd, check=True)
    if eval_process.returncode != 0:
        print("Error: Evaluation computation failed.")
        sys.exit(1)
    
    print("\nMulti-bug evaluation completed successfully.")

if __name__ == "__main__":
    main() 