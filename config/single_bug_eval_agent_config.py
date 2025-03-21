from agents.error_verifier_agent.prompt import RUBBER_DUCK_EVAL_SYSTEM_PROMPT, RUBBER_DUCK_EVAL_USER_PROMPT, RUBBER_DUCK_EVAL_PROMPT, RUBBER_DUCK_ZERO_COT_SYSTEM_PROMPT, RUBBER_DUCK_ZERO_COT_USER_PROMPT
from agents.error_verifier_agent.agent import ErrorVerifierAgent


AGENT_CONFIG = {
    'workspace': './workspace/benchmark_evaluation',
    'agents': [
        {
            'name': 'rubber_duck_eval_agent',
            'class': ErrorVerifierAgent,
            'prompts': {
                'system': RUBBER_DUCK_EVAL_SYSTEM_PROMPT,
                'user': RUBBER_DUCK_EVAL_USER_PROMPT,
                'eval': RUBBER_DUCK_EVAL_PROMPT
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
        'agent': 'rubber_duck_eval_agent',
        'method': 'rubber_duck_eval',
        'args': {
            'model_type': 'gpt-4o',
            'eval_folder': 'workspace/benchmark_evaluation'
        },
        'input': {'data': 'workspace/benchmark_evaluation/bench_final_annotation_v4.jsonl'},
        'data_ids': [63],
        'output': 'rubber_duck_eval_result',
        'output_type': 'analysis'
    },
]

# [144, 178, 550]