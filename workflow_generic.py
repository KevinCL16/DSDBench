import io
import sys
import os
import argparse
import importlib
from agents.agent_environment import AgentEnvironment
from config.dabench_quantitative_experiment_config import AGENT_CONFIG, WORKFLOW


def mainworkflow(config, workflow, update_callback=None):
    print('=========Initializing Agent Environment=========')
    agent_env = AgentEnvironment(config['workspace'], config)

    for agent_config in config['agents']:
        agent_name = agent_config['name']
        agent_env.add_agent(
            agent_name,
            agent_config['class'],
            prompts=agent_config['prompts'],
            **agent_config.get('kwargs', {})
        )

    results = agent_env.run_workflow(workflow)

    return results


def get_agent_class(agent_name):
    module_name = f"agents.{agent_name.lower()}"
    class_name = ''.join(word.capitalize() for word in agent_name.split('_'))

    try:
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    except (ImportError, AttributeError):
        raise ValueError(f"Agent class for '{agent_name}' not found")


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
        return 'workspace/benchmark_evaluation/eval_result.jsonl'

def load_config(config_path):
    """
    Dynamically load configuration from a specified Python file.
    
    Args:
        config_path: Path to the configuration Python file
        
    Returns:
        tuple: (AGENT_CONFIG, WORKFLOW) from the specified config file
    """
    # Extract the module name from the path
    if config_path.endswith('.py'):
        config_path = config_path[:-3]  # Remove .py extension
    
    # Replace path separators with dots for import
    module_path = config_path.replace('/', '.').replace('\\', '.')
    
    try:
        # Import the specified module
        config_module = importlib.import_module(module_path)
        return config_module.AGENT_CONFIG, config_module.WORKFLOW
    except (ImportError, AttributeError) as e:
        print(f"Error loading configuration from {config_path}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='DSDBench-Open: Data Science Debugging Benchmark')
    parser.add_argument('--config', type=str, default='config/dabench_quantitative_experiment_config.py',
                      help='Path to the configuration file (default: config/dabench_quantitative_experiment_config.py)')
    parser.add_argument('--result-file', type=str, default=None,
                      help='Path to save the evaluation results (default: auto-generated from config)')
    args = parser.parse_args()
    
    # Load the specified configuration
    print(f"Loading configuration from: {args.config}")
    config, workflow = load_config(args.config)
    
    # Generate result file path if not provided
    if args.result_file is None:
        args.result_file = generate_result_filename_from_config(args.config)
        print(f"Auto-generated result file: {args.result_file}")
    
    # Update workflow with result file path
    for step in workflow:
        if 'args' in step:
            step['args']['result_file'] = args.result_file
    
    # Run the workflow
    results = mainworkflow(config, workflow)
    # print(results)
