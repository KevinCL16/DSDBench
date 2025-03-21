from agents.data_analysis_agent.prompt import INITIAL_SYSTEM_PROMPT, INITIAL_USER_PROMPT, ERROR_PROMPT
from agents.error_verifier_agent.prompt import ERROR_VERIFIER_SYSTEM_PROMPT, ERROR_VERIFIER_USER_PROMPT
from agents.data_analysis_agent.agent import DataAnalysisAgent
from agents.error_verifier_agent.agent import ErrorVerifierAgent

AGENT_CONFIG = {
    'workspace': './workspace/InfiAgent',
    'agents': [
        {
            'name': 'data_annotate_agent',
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
            'name': 'error_verifier',
            'class': ErrorVerifierAgent,
            'prompts': {
                'system': ERROR_VERIFIER_SYSTEM_PROMPT,
                'user': ERROR_VERIFIER_USER_PROMPT
            }
        }
    ]
}

WORKFLOW = [
    {
        'type': 'loop',
        'condition': 'no_errors',
        'steps': [
            {
                'agent': 'data_annotate_agent',
                'method': 'run',
                'args': {
                    'model_type': 'claude-3-5-sonnet-20240620',
                    'file_name': 'plot.png'
                },
                'input': {'data': 'InfiAgent_data/easy_medium_modified_da-dev-questions.jsonl'},
                'data_range': [27, 760],
                'output': 'data_analysis_result',
                'output_type': 'code',
                'debug_method': 'debug_run'
            },
            {
                'agent': 'error_verifier',
                'method': 'run_with_other_agent',
                'args': {
                    'model_type': 'gpt-4o',
                    'from_prev_agent': {'from': 'data_analysis_result'}
                },
                'output': 'verification_result',
                'output_type': 'analysis'
            }
        ]
    }
]