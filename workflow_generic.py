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
    args = parser.parse_args()
    
    # Load the specified configuration
    print(f"Loading configuration from: {args.config}")
    config, workflow = load_config(args.config)
    
    # Run the workflow
    results = mainworkflow(config, workflow)
    # print(results)
