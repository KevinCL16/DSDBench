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

Install dependencies via:
```bash
pip install -r requirements.txt
```

### Evaluation

Evaluate single-bug scenarios:
```bash
python workflow_generic.py --config config/single_bug_eval_agent_config.py
cd benchmark_evaluation
python compute_eval_result.py
```

Evaluate multi-bug scenarios:
```bash
python workflow_generic.py --config config/multi_bug_eval_agent_config.py
cd benchmark_evaluation
python compute_multi_eval_results_improved.py
```

### Dataset Creation

To generate datasets from scratch:
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

# 📃 License

This project is licensed under the [Your Project's License]. Please see the LICENSE file for details.

