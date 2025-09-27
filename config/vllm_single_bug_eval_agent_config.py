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
            'model_type': 'vllm/codellama-7b',  # Use vLLM with CodeLlama-7B model
            'eval_folder': 'workspace/benchmark_evaluation',
        },
        'input': {'data': 'workspace/benchmark_evaluation/bench_final_annotation_single_error.jsonl'},
        'data_ids': [2],
        'output': 'rubber_duck_eval_result',
        'output_type': 'analysis'
    },
]

# Available vLLM models you can use:
# - vllm/llama2-7b
# - vllm/llama2-13b
# - vllm/codellama-7b
# - vllm/codellama-13b
# - vllm/mistral-7b
# - vllm/qwen-7b
# - vllm/qwen-14b
# - vllm/deepseek-coder-6.7b
