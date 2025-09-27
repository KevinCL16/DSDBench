from agents.error_verifier_agent.prompt import MULTI_RUBBER_DUCK_EVAL_SYSTEM_PROMPT, MULTI_RUBBER_DUCK_EVAL_USER_PROMPT, MULTI_RUBBER_DUCK_EVAL_PROMPT, MULTI_RUBBER_DUCK_ZERO_COT_SYSTEM_PROMPT, MULTI_RUBBER_DUCK_ZERO_COT_USER_PROMPT
from agents.error_verifier_agent.agent import ErrorVerifierAgent


AGENT_CONFIG = {
    'workspace': './workspace/benchmark_evaluation',
    'agents': [
        {
            'name': 'multi_rubber_duck_eval_agent',
            'class': ErrorVerifierAgent,
            'prompts': {
                'system': MULTI_RUBBER_DUCK_ZERO_COT_SYSTEM_PROMPT,
                'user': MULTI_RUBBER_DUCK_ZERO_COT_USER_PROMPT,
                'eval': MULTI_RUBBER_DUCK_EVAL_PROMPT
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
        'agent': 'multi_rubber_duck_eval_agent',
        'method': 'multi_rubber_duck_eval',
        'args': {
            'model_type': 'openai/gpt-oss-120b',
            'eval_folder': 'workspace/benchmark_evaluation',
            'result_file': 'workspace/benchmark_evaluation/eval_multi_bug_result.jsonl'
        },
        'input': {'data': 'workspace/benchmark_evaluation/bench_final_annotation_multi_errors.jsonl'},
        'data_ids': [1],
        'output': 'multi_rubber_duck_eval_result',
        'output_type': 'analysis'
    },
]
