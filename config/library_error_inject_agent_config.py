from agents.error_suggest_agent.prompt import LIBRARY_SYSTEM_PROMPT, LIBRARY_USER_PROMPT, ERROR_ERASE_PROMPT
from agents.error_suggest_agent.agent import ErrorSuggestAgent


AGENT_CONFIG = {
    'workspace': './workspace/DSEval',
    'agents': [
        {
            'name': 'library_error_multi_step_agent',
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
        'agent': 'library_error_multi_step_agent',
        'method': 'process_sklearn_pandas_code',
        'args': {
            'model_type': 'claude-3-5-sonnet-20240620',
            'data_folder': 'InfiAgent_data/da-dev-tables'
        },
        'input': {'data': 'workspace/InfiAgent/correct_codes/dseval-q-code.jsonl'}, # workspace/InfiAgent/correct_codes/hard_da-dev-q-code-a.jsonl
        'data_range': [0, 30],  # Specify the question IDs you want to process
        'output': 'library_error_multi_step_result',
        'output_type': 'analysis'  # Specify the output type here
    },
]

# [7, 28, 30, 39, 70, 77, 109, 111, 118, 124, 125, 133, 144, 177, 178, 210, 220, 224, 249, 271, 273, 275, 282, 308, 310, 376, 413, 415]
# claude-3-5-sonnet-20240620