import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up custom Hugging Face cache directory
def setup_hf_cache():
    """Set up custom Hugging Face cache directory if not already set."""
    cache_dir = os.getenv('HF_CACHE_DIR', 'E:/AI_Models/huggingface')
    
    # Only set if not already configured
    if not os.environ.get('HF_HOME'):
        os.environ['HF_HOME'] = cache_dir
        os.environ['TRANSFORMERS_CACHE'] = os.path.join(cache_dir, 'transformers')
        os.environ['HF_HUB_CACHE'] = os.path.join(cache_dir, 'hub')
        
        # Create directories if they don't exist
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(os.path.join(cache_dir, 'transformers'), exist_ok=True)
        os.makedirs(os.path.join(cache_dir, 'hub'), exist_ok=True)

# Initialize cache setup
setup_hf_cache()

# vLLM Configuration
VLLM_API_KEY = os.getenv('VLLM_API_KEY', 'EMPTY')  # Usually empty for local vLLM servers
VLLM_BASE_URL = os.getenv('VLLM_BASE_URL', 'http://localhost:8000/v1')  # Default vLLM server URL
VLLM_TEMPERATURE = float(os.getenv('VLLM_TEMPERATURE', '0'))

# vLLM Model Configuration
# You can override these in your .env file
VLLM_MODEL_NAME = os.getenv('VLLM_MODEL_NAME', 'meta-llama/Llama-2-7b-chat-hf')
VLLM_MAX_TOKENS = int(os.getenv('VLLM_MAX_TOKENS', '4096'))
VLLM_TOP_P = float(os.getenv('VLLM_TOP_P', '1.0'))
VLLM_FREQUENCY_PENALTY = float(os.getenv('VLLM_FREQUENCY_PENALTY', '0.0'))
VLLM_PRESENCE_PENALTY = float(os.getenv('VLLM_PRESENCE_PENALTY', '0.0'))

# vLLM Server Configuration
VLLM_HOST = os.getenv('VLLM_HOST', 'localhost')
VLLM_PORT = int(os.getenv('VLLM_PORT', '8000'))
VLLM_WORKER_USE_RAY = os.getenv('VLLM_WORKER_USE_RAY', 'false').lower() == 'true'
VLLM_TENSOR_PARALLEL_SIZE = int(os.getenv('VLLM_TENSOR_PARALLEL_SIZE', '1'))

# Supported model configurations for easy switching
VLLM_MODEL_CONFIGS = {
    'llama2-7b': {
        'model_name': 'meta-llama/Llama-2-7b-chat-hf',
        'max_tokens': 4096,
        'temperature': 0,
    },
    'llama2-13b': {
        'model_name': 'meta-llama/Llama-2-13b-chat-hf',
        'max_tokens': 4096,
        'temperature': 0,
    },
    'codellama-7b': {
        'model_name': 'codellama/CodeLlama-7b-Instruct-hf',
        'max_tokens': 4096,
        'temperature': 0,
    },
    'codellama-13b': {
        'model_name': 'codellama/CodeLlama-13b-Instruct-hf',
        'max_tokens': 4096,
        'temperature': 0,
    },
    'mistral-7b': {
        'model_name': 'mistralai/Mistral-7B-Instruct-v0.1',
        'max_tokens': 4096,
        'temperature': 0,
    },
    'qwen-7b': {
        'model_name': 'Qwen/Qwen-7B-Chat',
        'max_tokens': 4096,
        'temperature': 0,
    },
    'qwen-14b': {
        'model_name': 'Qwen/Qwen-14B-Chat',
        'max_tokens': 4096,
        'temperature': 0,
    },
    'deepseek-coder-6.7b': {
        'model_name': 'deepseek-ai/deepseek-coder-6.7b-instruct',
        'max_tokens': 4096,
        'temperature': 0,
    },
}
