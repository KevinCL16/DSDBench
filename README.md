# DSDBench-Open

<div align="center">

<img src="assets/title.png" alt="DSDBench-Open" width="500">

**DSDBench-Open: Benchmarking LLMs as Data Science Code Debuggers for Multi-Hop and Multi-Bug Errors**

<p align="center">•
 <a href="#-introduction"> 📖Introduction </a> •
 <a href="#-news">🎉News</a> •
 <a href="#-dsdbench">✨DSDBench</a> •
 <a href="#-methodology">🚀Methodology</a>
</p>
<p align="center">•
 <a href="#%EF%B8%8F-getting-started">⚡️Getting Started</a> •
 <a href="#-experiment-results">📊Experiment Results</a> •
 <a href="#-citation">🔎Citation </a> •
 <a href="#-license">📃License</a>
</p>
</div>

# 📖 Introduction

Debugging data science code is challenging, particularly when multiple logical errors interact in complex ways. Current benchmarks primarily address simple, isolated scenarios, leaving multi-hop, multi-bug error debugging significantly underexplored. **DSDBench-Open** addresses this gap, providing a comprehensive dataset and framework to evaluate and enhance large language models (LLMs) in debugging complex, realistic data science code scenarios.

# 🎉 News

- **March 21, 2024:** DSDBench-Open dataset and evaluation framework officially released! 🎊

# ✨ DSDBench

DSDBench is the first systematic benchmark designed explicitly for data science code debugging, featuring:
- **Realistic Errors:** Logical, runtime errors reflective of real-world data science workflows.
- **Multi-Hop Debugging:** Scenarios where identifying errors requires tracing back through multiple code steps.
- **Multi-Bug Scenarios:** Cases involving concurrent errors within the same code snippet.
- **Comprehensive Annotations:** Includes 1,117 rigorously annotated examples, clearly labeling cause-effect error lines and runtime error messages.

<div align="center">
  <img src="assets/workflow.png" alt="DSDBench framework">
</div>

# 🚀 Methodology

Our contributions include:
- **Automated Error Injection:** Using advanced LLM techniques to systematically introduce realistic runtime errors.
- **Dynamic Error Annotation:** Utilizing runtime tracing (with tools like `snoop`) to accurately capture cause-effect relationships.
- **Rigorous Evaluation Protocols:** Four-dimensional evaluation covering cause lines, effect lines, error types, and error messages.

<div align="center">
  <img src="assets/example.png" alt="DSDBench examples">
</div>

# ⚡️ Getting Started

To begin using DSDBench-Open, follow these steps:

### Installation

You can install DSDBench-Open and its dependencies in one of two ways:

1. Using pip with requirements file:
```bash
pip install -r requirements.txt
```

2. Installing as a package (development mode):
```bash
pip install -e .
```

### Project Structure

The DSDBench-Open repository is organized as follows:

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

### Running Evaluations

DSDBench-Open includes helper scripts to simplify evaluation:

**For single-bug scenarios:**
```bash
python run_single_bug_eval.py
```
This automatically runs the workflow with the single-bug configuration and computes evaluation results.

**For multi-bug scenarios:**
```bash
python run_multi_bug_eval.py
```
This executes the multi-bug workflow and calculates multi-error evaluation metrics.

### Manual Execution

You can also run individual workflow components manually:

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

### Dataset Creation

To generate datasets from scratch, execute the pipeline steps individually:
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

### Configuration Details

The configuration files in the `config/` directory control different aspects of the benchmark:

- `single_bug_eval_agent_config.py`: Configuration for single-bug evaluation scenarios
- `multi_bug_eval_agent_config.py`: Configuration for multi-bug evaluation scenarios
- `data_annotate_agent_config.py`: Configuration for data annotation process
- `library_error_inject_agent_config.py`: Configuration for error injection in libraries
- `error_snoop_agent_config.py`: Configuration for error monitoring
- `weak_llm_direct_analysis_config.py`: Configuration for weak LLM error analysis

To specify a particular configuration file when running the workflow:
```bash
python workflow_generic.py --config config/your_chosen_config.py
```

# 📊 Experiment Results

Evaluations of state-of-the-art LLMs show significant performance challenges in multi-bug debugging scenarios. Notable results include:

| Model            | Cause Line Acc. | Effect Line Acc. | Error Type Acc. | Error Message Acc. |
|------------------|-----------------|------------------|-----------------|--------------------|
| GPT-4o           | 39.0%           | 34.3%            | 30.6%           | 31.4%              |
| Claude 3.5       | 43.7%           | 35.2%            | 36.3%           | 34.0%              |
| Deepseek-V3      | 48.3%           | 34.5%            | 35.9%           | 34.7%              |

Detailed analysis and ablation studies further highlight the benchmark's complexity and utility in diagnosing model limitations.

# 🔎 Citation

If DSDBench-Open aids your research, please cite our work:
```bibtex
@article{your2024dsdbench,
  title={Why Stop at One Error? Benchmarking LLMs as Data Science Code Debuggers for Multi-Hop and Multi-Bug Errors},
  author={Your Name and co-authors},
  journal={Conference/Journal Name},
  year={2024}
}
```