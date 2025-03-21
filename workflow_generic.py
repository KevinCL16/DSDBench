import io
import sys
import os
from agents.agent_environment import AgentEnvironment
from config.dabench_quantitative_experiment_config import AGENT_CONFIG, WORKFLOW
import importlib


def mainworkflow(config, workflow, update_callback=None):
    print('=========Initializing Agent Environment=========')
    agent_env = AgentEnvironment(config['workspace'], config)

    for agent_config in config['agents']:
        agent_name = agent_config['name']
        # agent_class = get_agent_class(agent_name)
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


if __name__ == "__main__":
    results = mainworkflow(AGENT_CONFIG, WORKFLOW)
    # print(results)
