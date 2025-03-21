from agents.error_suggest_agent.prompt import LIBRARY_SYSTEM_PROMPT, LIBRARY_USER_PROMPT, ERROR_ERASE_PROMPT
from agents.error_suggest_agent.agent import ErrorSuggestAgent


AGENT_CONFIG = {
    'workspace': './workspace',
    'agents': [
        {
            'name': 'library_error_snoop_agent',
            'class': ErrorSuggestAgent,
            'prompts': {
                'system': LIBRARY_SYSTEM_PROMPT,
                'user': LIBRARY_USER_PROMPT,
                'error': ERROR_ERASE_PROMPT
            },
            'kwargs': {
                'query': 'Your default query here'
            }
        },
    ]
}

#
WORKFLOW = [
    {
        'agent': 'library_error_snoop_agent',
        'method': 'run_snoop',
        'args': {
            'model_type': 'llama-3.1-8b-instant',
            'data_folder': 'InfiAgent_data/da-dev-tables'
        },
        'input': {'data': 'workspace/sklearn_pandas_errors/llama-3.1-8b-instant_matplotbench_weak_direct_analysis_with_use_agg.jsonl'},
        # workspace/InfiAgent/correct_codes/hard_da-dev-q-code-a.jsonl
        # workspace/InfiAgent/sklearn_pandas_errors/gpt-4o_dabench_hard_library_errors.jsonl
        'data_range': [0, 75],  # Specify the question IDs you want to process
        'output': 'library_error_snoop_result',
        'output_type': 'analysis'  # Specify the output type here
    },
]

# [7, 28, 30, 39, 70, 77, 109, 111, 118, 124, 125, 133, 144, 177, 178, 210, 220, 224, 249, 271, 273, 275, 282, 308, 310, 376, 413, 415]
# claude-3-5-sonnet-20240620
# workspace/InfiAgent/sklearn_pandas_errors/claude-3-5-sonnet_easy_medium_library_errors.jsonl