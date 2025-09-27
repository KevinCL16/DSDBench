# vLLM Integration for DSDBench

This document explains how to use vLLM (vLLM Inference and Serving) with DSDBench for local model inference.

## Overview

vLLM integration allows you to run DSDBench evaluations using locally hosted language models through vLLM's high-performance inference engine. This provides faster inference, lower costs, and better privacy compared to cloud-based APIs.

## Setup

### 1. Install vLLM

First, install vLLM and its dependencies:

```bash
# Install vLLM (requires CUDA)
pip install vllm

# Or install from source for latest features
pip install git+https://github.com/vllm-project/vllm.git
```

### 2. Configure Environment

Copy the example environment file and update it:

```bash
cp .env.vllm.example .env
```

Edit `.env` file with your configuration:

```bash
# Custom cache directory (change to your preferred location)
HF_CACHE_DIR=D:\AI_Models\huggingface

# vLLM Server Configuration
VLLM_API_KEY=EMPTY
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_HOST=localhost
VLLM_PORT=8000

# Model Parameters
VLLM_TEMPERATURE=0
VLLM_MAX_TOKENS=4096
VLLM_TOP_P=1.0
```

### 2.1. Set Up Custom Cache Directory (Optional)

By default, Hugging Face downloads models to your system drive. To use a different location:

**Windows:**
```bash
# Run the setup script
setup_cache.bat

# Or manually set environment variables
setx HF_CACHE_DIR "D:\AI_Models\huggingface"
```

**Linux/Mac:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export HF_CACHE_DIR="/path/to/your/ai_models/huggingface"
```

**Verify setup:**
```bash
python setup_cache.py
```

### 3. Start vLLM Server

Start a vLLM server with your desired model:

```bash
# For CodeLlama-7B (recommended for code tasks)
python -m vllm.entrypoints.openai.api_server \
    --model codellama/CodeLlama-7b-Instruct-hf \
    --port 8000

# For CodeLlama-13B (better performance, requires more GPU memory)
python -m vllm.entrypoints.openai.api_server \
    --model codellama/CodeLlama-13b-Instruct-hf \
    --port 8000

# For Llama2-7B
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-chat-hf \
    --port 8000

# For Mistral-7B
python -m vllm.entrypoints.openai.api_server \
    --model mistralai/Mistral-7B-Instruct-v0.1 \
    --port 8000

# For Qwen-7B
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen-7B-Chat \
    --port 8000

# For DeepSeek-Coder-6.7B
python -m vllm.entrypoints.openai.api_server \
    --model deepseek-ai/deepseek-coder-6.7b-instruct \
    --port 8000
```

### 4. Verify Server Status

Check if your vLLM server is running:

```bash
curl http://localhost:8000/health
```

You should see a response like:
```json
{"status": "healthy"}
```

## Usage

### Running Evaluations with vLLM

#### Single Bug Evaluation

```bash
# Use the provided vLLM single bug evaluation script
python run_vllm_single_bug_eval.py

# Or specify a custom config
python run_vllm_single_bug_eval.py --config config/vllm_single_bug_eval_agent_config.py

# Or specify a custom result file
python run_vllm_single_bug_eval.py --result-file my_vllm_results.jsonl
```

#### Multi Bug Evaluation

```bash
# Use the generic workflow with vLLM multi bug config
python workflow_generic.py --config config/vllm_multi_bug_eval_agent_config.py
```

### Customizing Models

You can easily switch between different models by modifying the configuration files:

1. **Edit config files**: Update `model_type` in the workflow configuration
2. **Available models**: 
   - `vllm/llama2-7b`
   - `vllm/llama2-13b`
   - `vllm/codellama-7b`
   - `vllm/codellama-13b`
   - `vllm/mistral-7b`
   - `vllm/qwen-7b`
   - `vllm/qwen-14b`
   - `vllm/deepseek-coder-6.7b`

### Example Configuration

```python
WORKFLOW = [
    {
        'agent': 'rubber_duck_eval_agent',
        'method': 'rubber_duck_eval',
        'args': {
            'model_type': 'vllm/codellama-7b',  # Use CodeLlama-7B via vLLM
            'eval_folder': 'workspace/benchmark_evaluation',
        },
        'input': {'data': 'workspace/benchmark_evaluation/bench_final_annotation_single_error.jsonl'},
        'data_ids': [2],
        'output': 'rubber_duck_eval_result',
        'output_type': 'analysis'
    },
]
```

## Performance Tips

### GPU Memory Requirements

- **CodeLlama-7B**: ~14GB VRAM
- **CodeLlama-13B**: ~26GB VRAM
- **Llama2-7B**: ~14GB VRAM
- **Llama2-13B**: ~26GB VRAM
- **Mistral-7B**: ~14GB VRAM
- **Qwen-7B**: ~14GB VRAM
- **DeepSeek-Coder-6.7B**: ~14GB VRAM

### Optimization Options

For better performance, you can add these flags when starting vLLM server:

```bash
# Enable tensor parallelism for multi-GPU setups
python -m vllm.entrypoints.openai.api_server \
    --model codellama/CodeLlama-7b-Instruct-hf \
    --port 8000 \
    --tensor-parallel-size 2

# Use quantization for memory efficiency
python -m vllm.entrypoints.openai.api_server \
    --model codellama/CodeLlama-7b-Instruct-hf \
    --port 8000 \
    --quantization awq

# Set custom batch size
python -m vllm.entrypoints.openai.api_server \
    --model codellama/CodeLlama-7b-Instruct-hf \
    --port 8000 \
    --max-model-len 4096
```

## Troubleshooting

### Common Issues

1. **Server not responding**: Make sure vLLM server is running and accessible
2. **CUDA out of memory**: Reduce model size or use quantization
3. **Model not found**: Ensure the model name is correct and available
4. **Connection refused**: Check if the port is correct and not blocked

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check server logs for detailed error messages.

## Comparison with Other Backends

| Backend | Speed | Cost | Privacy | Setup |
|---------|-------|------|---------|-------|
| OpenRouter | Medium | High | Low | Easy |
| vLLM | High | Low | High | Medium |
| THU API | Medium | Medium | Medium | Easy |

vLLM provides the best performance and privacy for local inference, making it ideal for research and development scenarios where you have access to powerful GPU hardware.

## Advanced Configuration

For advanced users, you can customize the vLLM client behavior by modifying `agents/config/vllm.py` or `agents/vllm_client.py`.

### Custom Model Configurations

Add new model configurations in `agents/config/vllm.py`:

```python
VLLM_MODEL_CONFIGS['my-custom-model'] = {
    'model_name': 'my-org/my-custom-model',
    'max_tokens': 8192,
    'temperature': 0.1,
}
```

### Custom Client Behavior

Modify `agents/vllm_client.py` to add custom retry logic, error handling, or response processing.
