from agents.data_analysis_agent.prompt import INITIAL_SYSTEM_PROMPT, INITIAL_USER_PROMPT, ERROR_PROMPT
from agents.data_analysis_agent.agent import DataAnalysisAgent
from agents.error_suggest_agent.agent import ErrorSuggestAgent
from agents.error_suggest_agent.prompt import LIBRARY_SYSTEM_PROMPT, LIBRARY_USER_PROMPT, ERROR_ERASE_PROMPT

AGENT_CONFIG = {
    'workspace': './workspace/DSEval',
    'agents': [
        {
            'name': 'weak_direct_analysis_agent',
            'class': DataAnalysisAgent,
            'prompts': {
                'system': INITIAL_SYSTEM_PROMPT,
                'user': INITIAL_USER_PROMPT,
                'error': ERROR_PROMPT
            },
            'kwargs': {
                'query': 'Your default query here'
            }
        },
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
        'agent': 'weak_direct_analysis_agent',
        'method': 'weak_direct_analysis',
        'args': {
            'model_type': 'llama-3.1-8b-instant',
            'file_name': 'plot.png'
        },
        'input': {'data': 'workspace/InfiAgent/correct_codes/dseval-q-code.jsonl'},
        'data_range': [0, 30],  # Specify the question IDs you want to process
        'output': 'weak_direct_analysis_result',
        'output_type': 'analysis'  # Specify the output type here
    },
    {
        'agent': 'library_error_snoop_agent',
        'method': 'run_snoop',
        'args': {
            'model_type': 'llama-3.1-8b-instant',
            'data_folder': 'InfiAgent_data/da-dev-tables'
        },
        'input': {'data': 'workspace/DSEval/sklearn_pandas_errors/llama-3.1-8b-instant_dseval_weak_direct_analysis.jsonl'},
        # workspace/InfiAgent/correct_codes/hard_da-dev-q-code-a.jsonl
        # workspace/InfiAgent/sklearn_pandas_errors/gpt-4o_dabench_hard_library_errors.jsonl
        'data_range': [0, 30],  # Specify the question IDs you want to process
        'output': 'library_error_snoop_result',
        'output_type': 'analysis'  # Specify the output type here
    },
]