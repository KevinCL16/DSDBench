# DSDBench-Open

<div align="center">

<img src="assets/title.png" alt="DSDBench-Open" width="500">

**DSDBench-Open: Benchmarking LLMs as Data Science Code Debuggers for Multi-Hop and Multi-Bug Errors**

<p align="center">
 • <a href="#introduction">📖 Introduction</a> •
 <a href="#news">🎉 News</a> •
 <a href="#dsdbench">✨ DSDBench</a> •
 <a href="#methodology">🚀 Methodology</a>
</p>
<p align="center">
 • <a href="#getting-started">⚡️ Getting Started</a> •
 <a href="#experiment-results">📊 Experiment Results</a> •
 <a href="#citation">🔎 Citation</a> •
 <a href="#license">📃 License</a>
</p>
</div>

# Introduction <a name="introduction"></a>

Debugging data science code presents significant challenges, especially when multiple logical errors interact in intricate ways. Existing benchmarks often focus on simple, isolated error scenarios, leaving the debugging of multi-hop, multi-bug errors largely unexplored. **DSDBench-Open** fills this critical gap by offering a comprehensive dataset and evaluation framework designed to assess and improve large language models (LLMs) in debugging complex, real-world data science code problems.

# News <a name="news"></a>

- **March 21, 2024:** DSDBench-Open dataset and evaluation framework officially released! 🎊

# DSDBench <a name="dsdbench"></a>

DSDBench is the first systematic benchmark explicitly created for data science code debugging, featuring:

- **Realistic Errors:** Logical and runtime errors that mirror real-world data science workflows.
- **Multi-Hop Debugging:** Scenarios where error identification requires tracing back through multiple code execution steps.
- **Multi-Bug Scenarios:** Cases involving concurrent errors within a single code snippet.
- **Comprehensive Annotations:** Includes 1,117 meticulously annotated examples, clearly labeling cause-effect error lines and runtime error messages.

<div align="center">
  <img src="assets/workflow.png" alt="DSDBench framework">
</div>

# Methodology <a name="methodology"></a>

Our contributions include:

- **Automated Error Injection:**  Leveraging advanced LLM techniques to systematically introduce realistic runtime errors.
- **Dynamic Error Annotation:** Utilizing runtime tracing (with tools like `snoop`) to accurately capture cause-effect relationships in errors.
- **Rigorous Evaluation Protocols:** Employing a four-dimensional evaluation approach covering cause lines, effect lines, error types, and error messages.

<div align="center">
  <img src="assets/example.png" alt="DSDBench examples">
</div>

# Getting Started <a name="getting-started"></a>

To start using DSDBench-Open, follow these installation and execution steps:

## Installation

You can install DSDBench-Open and its dependencies using one of the following methods:

1. **Using pip with requirements file:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Installing as a package (development mode):**
   ```bash
   pip install -e .
   ```

## Project Structure

The DSDBench-Open repository has the following structure:

```
DSDBench-Open/
├── agents/                   # Agent model implementation directory
├── config/                   # Configuration files directory
│   ├── dabench_quantitative_experiment_config.py
│   ├── single_bug_eval_agent_config.py
│   ├── multi_bug_eval_agent_config.py
│   ├── error_snoop_agent_config.py
│   ├── library_error_inject_agent_config.py
│   ├── weak_llm_direct_analysis_config.py
│   └── data_annotate_agent_config.py
├── workspace/                # Workspace directory
│   ├── benchmark_evaluation/ # Benchmark evaluation directory
│   │   ├── bench_final_annotation_v4.jsonl
│   │   ├── bench_final_annotation_with_multi_errors_v2.jsonl
│   │   ├── compute_eval_result.py
│   │   └── compute_multi_eval_results_improved.py
│   ├── filter_non_executable_data.py
│   ├── find_multi_hop_data.py
│   ├── merge_final_annotation.py
│   └── merge_multiple_errors.py
├── workflow_generic.py      # Main workflow execution script with command line support
├── run_single_bug_eval.py   # Helper script for single-bug evaluation
└── run_multi_bug_eval.py    # Helper script for multi-bug evaluation
```

## Running Evaluations

DSDBench-Open provides helper scripts to simplify the evaluation process:

**For single-bug scenarios:**

```bash
python run_single_bug_eval.py
```
This command automatically runs the workflow using the single-bug configuration and computes the evaluation results.

**For multi-bug scenarios:**

```bash
python run_multi_bug_eval.py
```
This command executes the multi-bug workflow and calculates the multi-error evaluation metrics.

## Manual Execution

For more control, you can run individual workflow components manually:

**For single-bug evaluation:**

```bash
python workflow_generic.py --config config/single_bug_eval_agent_config.py
cd workspace/benchmark_evaluation
python compute_eval_result.py
```

**For multi-bug evaluation:**

```bash
python workflow_generic.py --config config/multi_bug_eval_agent_config.py
cd workspace/benchmark_evaluation
python compute_multi_eval_results_improved.py
```

## Dataset Creation

To generate datasets from scratch, execute the pipeline steps in the following order:

```bash
python workflow_generic.py --config config/data_annotate_agent_config.py
python workflow_generic.py --config config/library_error_inject_agent_config.py
python workflow_generic.py --config config/error_snoop_agent_config.py
python workflow_generic.py --config config/weak_llm_direct_analysis_config.py
cd workspace
python filter_non_executable_data.py
python find_multi_hop_data.py
python merge_final_annotation.py
python merge_multiple_errors.py
```

## Configuration Details

The configuration files in the `config/` directory manage different aspects of the benchmark. Here's a brief overview:

- `single_bug_eval_agent_config.py`: Configuration for single-bug evaluation scenarios.
- `multi_bug_eval_agent_config.py`: Configuration for multi-bug evaluation scenarios.
- `data_annotate_agent_config.py`: Configuration for the data annotation process.
- `library_error_inject_agent_config.py`: Configuration for error injection in libraries.
- `error_snoop_agent_config.py`: Configuration for error monitoring.
- `weak_llm_direct_analysis_config.py`: Configuration for weak LLM error analysis.

To use a specific configuration file when running the workflow, use the `--config` argument:

```bash
python workflow_generic.py --config config/your_chosen_config.py
```

### Configuration Structure

Each configuration file adheres to a standard structure defined as follows:

```python
AGENT_CONFIG = {
    'workspace': './workspace/path',  # Base workspace directory
    'agents': [
        {
            'name': 'agent_name',     # Name of the agent
            'class': AgentClass,      # The agent class to instantiate
            'prompts': {              # Prompts used by the agent
                'system': SYSTEM_PROMPT,
                'user': USER_PROMPT,
                'eval': EVAL_PROMPT,
                # Other prompts as needed
            },
            'kwargs': {               # Additional agent parameters
                'query': 'Default query',
                # Other parameters as needed
            }
        },
        # Additional agents as needed
    ]
}

WORKFLOW = [
    {
        'agent': 'agent_name',        # Name of the agent to run
        'method': 'method_name',      # Agent method to execute
        'args': {                     # Arguments for the method
            'model_type': 'gpt-4o',   # LLM model to use
            'eval_folder': 'workspace/results'  # Output location
        },
        'input': {'data': 'path/to/input.jsonl'},  # Input data source
        'data_ids': [1, 2, 3],        # Optional specific data IDs to process
        'output': 'result_name',      # Name for the output
        'output_type': 'analysis'     # Type of output
    },
    # Additional workflow steps as needed
]
```

### Customizing Agent Parameters

Agents can be customized by modifying the `kwargs` dictionary within their configuration. Common parameters include:

- `query`:  Default query text used by the agent.
- `data_information`: Additional data context provided to the agent.

### Model Selection

The `model_type` parameter in workflow steps specifies the LLM to be used for evaluation:

- `gpt-4o`: OpenAI GPT-4o model.
- `Qwen/Qwen2.5-72B-Instruct`: Qwen 2.5 model.
- `deepseek/deepseek-v3`: DeepSeek v3 model.

Different models can be configured for various evaluation scenarios to facilitate performance comparisons.

# Experiment Results <a name="experiment-results"></a>

Evaluations of state-of-the-art LLMs reveal significant challenges in multi-bug debugging scenarios. Key results are summarized below:

| Model            | Cause Line Acc. | Effect Line Acc. | Error Type Acc. | Error Message Acc. |
|------------------|-----------------|------------------|-----------------|--------------------|
| GPT-4o           | 39.0%           | 34.3%            | 30.6%           | 31.4%              |
| Claude 3.5       | 43.7%           | 35.2%            | 36.3%           | 34.0%              |
| Deepseek-V3      | 48.3%           | 34.5%            | 35.9%           | 34.7%              |

Detailed analysis and ablation studies further emphasize the benchmark's complexity and its value in diagnosing model limitations.

# Citation <a name="citation"></a>

If DSDBench-Open is helpful in your research, please cite our work using the following BibTeX entry:

```bibtex
@article{your2024dsdbench,
  title={Why Stop at One Error? Benchmarking LLMs as Data Science Code Debuggers for Multi-Hop and Multi-Bug Errors},
  author={Your Name and co-authors},
  journal={Conference/Journal Name},
  year={2024}
}
```
