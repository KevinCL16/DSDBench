from agents.data_analysis_agent.prompt import INITIAL_SYSTEM_PROMPT, INITIAL_USER_PROMPT, ERROR_PROMPT
from agents.data_analysis_agent.agent import DataAnalysisAgent
from agents.error_verifier_agent.prompt import RUBBER_DUCK_EVAL_SYSTEM_PROMPT, RUBBER_DUCK_EVAL_USER_PROMPT

AGENT_CONFIG = {
    'workspace': './workspace/InfiAgent',
    'agents': [
        {
            'name': 'dabench_quantitative_exp_agent',
            'class': DataAnalysisAgent,
            'prompts': {
                'system': INITIAL_SYSTEM_PROMPT,
                'user': INITIAL_USER_PROMPT,
                'error': ERROR_PROMPT,
                'debug_system': RUBBER_DUCK_EVAL_SYSTEM_PROMPT,
                'debug_user': RUBBER_DUCK_EVAL_USER_PROMPT
            },
            'kwargs': {
                'query': 'Your default query here'
            }
        }
    ]
}

#
WORKFLOW = [
    {
        'agent': 'dabench_quantitative_exp_agent',
        'method': 'direct_analysis_with_rubber_duck_debug',
        'args': {
            'model_type': 'Qwen/Qwen2.5-72B-Instruct',
            'file_name': 'plot.png'
        },
        'input': {'data': 'workspace/InfiAgent/correct_codes/hard_da-dev-q-code-a.jsonl'},
        'data_range': [23, 743],  # Specify the question IDs you want to process
        'output': 'dabench_quantitative_exp_result',
        'output_type': 'analysis'  # Specify the output type here
    }
]