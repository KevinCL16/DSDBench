# DSDBench-Open

DSDBench-Open is a comprehensive data science and data analysis code library that includes two major functional modules: (1) data annotation tools for creating and annotating code error datasets; (2) model evaluation tools for assessing the performance of large language models on annotated benchmark datasets.

## Project Structure

```
DSDBench-Open/
├── agents/                   # Agent model implementation directory
│   ├── agent_environment/    # Agent environment framework
│   ├── data_analysis_agent/  # Data analysis agent
│   ├── error_verifier_agent/ # Error verification agent
│   ├── error_suggest_agent/  # Error suggestion agent
│   ├── generic_agent/        # Generic agent base class
│   ├── utils.py              # Utility functions
│   └── openai_chatComplete.py # OpenAI API interface
├── config/                   # Configuration files directory
│   ├── dabench_quantitative_experiment_config.py # Quantitative experiment config
│   ├── single_bug_eval_agent_config.py           # Single-bug evaluation config
│   ├── multi_bug_eval_agent_config.py            # Multi-bug evaluation config
│   ├── error_snoop_agent_config.py               # Error monitoring agent config
│   ├── library_error_inject_agent_config.py      # Library error injection config
│   ├── weak_llm_direct_analysis_config.py        # Weak LLM direct analysis config
│   └── data_annotate_agent_config.py             # Data annotation config
├── benchmark_evaluation/     # Benchmark evaluation directory
│   ├── bench_final_annotation_v4.jsonl              # Benchmark annotation dataset
│   ├── bench_final_annotation_with_multi_errors_v2.jsonl  # Multi-error annotation dataset
│   ├── compute_eval_result.py                      # Evaluation calculation script
│   └── compute_multi_eval_results_improved.py      # Multi-error evaluation script
├── workspace/                # Workspace directory
│   ├── merge_final_annotation.py  # Merge annotation results
│   ├── merge_multiple_errors.py   # Merge multiple error annotations
│   ├── filter_non_executable_data.py # Filter non-executable data
│   └── find_multi_hop_data.py     # Find and annotate error lines
└── workflow_generic.py      # Main workflow execution script
```

## Functionality Overview

### Data Annotation Tools

1. **Error Verification System**: Uses `error_verifier_agent` to verify error behavior and type
2. **Error Suggestion System**: Uses `error_suggest_agent` to provide error fix suggestions
3. **Annotation Workflow**: Organizes annotation process through configuration files and workflow scripts
4. **Data Processing Tools**: Scripts for filtering, merging, and processing annotation data

### Model Evaluation System

1. **Code Generation and Analysis Testing**: Evaluates model's ability to generate and analyze code
2. **Error Diagnosis Testing**: Tests model's ability to identify and diagnose code errors
3. **Multi-Error Scenario Testing**: Evaluates model's handling of complex scenarios with multiple errors

## Data Format

The format of the annotated dataset (e.g., `bench_final_annotation_v4.jsonl`) is:

```json
{
  "id": "Numeric ID",
  "question": "Task description",
  "error_versions": [
    {
      "modified_code": "Code with error",
      "execution_output": "Execution output with error info",
      "effect_error_line": "Error effect line",
      "cause_error_line": "Error cause line"
    },
    ...
  ]
}
```

## Annotation Process

DSDBench-Open uses the following process to convert existing data science benchmarks into error-containing datasets:

1. **Correct Code Generation**:
   - Configure using `config/data_annotate_agent_config.py`
   - Process original benchmark data through `workflow_generic.py`
   - Generate correct code implementations (`correct_code`)

2. **Error Injection**:
   - Configure using `config/library_error_inject_agent_config.py`
   - Inject logical errors into code lines that use data science Python libraries
   - Generate code versions containing errors

3. **Execution Monitoring**:
   - Configure using `config/error_snoop_agent_config.py`
   - Use the snoop tool to monitor code runtime information
   - Collect interpreter errors and detailed code execution information
   - Annotate the `execution_output` field

4. **Weak LLM Error Annotation**:
   - Configure using `config/weak_llm_direct_analysis_config.py`
   - Analyze errors generated directly by weaker LLMs
   - Capture and annotate systematic error patterns from these models

5. **Data Filtering and Processing**:
   - Use `workspace/filter_non_executable_data.py` to filter out successfully executed samples
   - Retain code samples with errors

6. **Error Line Annotation**:
   - Use `workspace/find_multi_hop_data.py` to locate and annotate error lines
   - Annotate the `cause_error_line` and `effect_error_line` fields

7. **Data Merging**:
   - Use `workspace/merge_final_annotation.py` to merge annotation results from different benchmarks
   - Use `workspace/merge_multiple_errors.py` to convert single-error annotations to multi-error annotations

Through this process, DSDBench-Open creates high-quality error diagnosis datasets from existing data science benchmarks.

## Usage

### Running Evaluation Experiments

1. Select an appropriate configuration file in the `config/` directory
2. Execute the workflow script:
   ```bash
   python workflow_generic.py
   ```

### Creating New Annotated Data

1. Configure the annotation process:
   ```bash
   # 1. Generate correct code
   python workflow_generic.py --config config/data_annotate_agent_config.py
   
   # 2. Inject errors
   python workflow_generic.py --config config/library_error_inject_agent_config.py
   
   # 3. Monitor execution information
   python workflow_generic.py --config config/error_snoop_agent_config.py
   
   # 4. Annotate weak LLM errors
   python workflow_generic.py --config config/weak_llm_direct_analysis_config.py
   
   # 5. Process and merge data
   python workspace/filter_non_executable_data.py
   python workspace/find_multi_hop_data.py
   python workspace/merge_final_annotation.py
   python workspace/merge_multiple_errors.py
   ```

### Evaluating Model Performance on DSDBench

1. Run single-bug evaluation:
   ```bash
   # Configure the single-bug evaluation
   python workflow_generic.py --config config/single_bug_eval_agent_config.py
   
   # Calculate evaluation metrics
   cd benchmark_evaluation
   python compute_eval_result.py
   ```

2. Run multi-bug evaluation:
   ```bash
   # Configure the multi-bug evaluation
   python workflow_generic.py --config config/multi_bug_eval_agent_config.py
   
   # Calculate multi-error evaluation metrics
   cd benchmark_evaluation
   python compute_multi_eval_results_improved.py
   ```

## Evaluation Metrics

Model evaluation is based on the following dimensions:
- **cause_line**: Whether the model can correctly identify the cause line of the error
- **effect_line**: Whether the model can correctly identify the effect line of the error
- **error_type**: Whether the model can correctly classify the error type
- **error_message**: Whether the model can provide a correct explanation of the error

## Annotation Guidelines

When creating new annotated data, ensure:
1. Each error example includes necessary fields such as `modified_code` and `execution_output`
2. Error causes and effect lines are accurately marked
3. Code can be executed and produces the expected error information

## Agent System

The project uses an agent-based architecture, where core agents include:

1. **GenericAgent**: Base class for all agents, providing fundamental functionality
2. **DataAnalysisAgent**: Agent for parsing and analyzing data
3. **ErrorVerifierAgent**: Agent for verifying and analyzing code errors
4. **ErrorSuggestAgent**: Agent for providing error fix suggestions

These agents work together in workflows, coordinated and managed by `AgentEnvironment`.

## Contribution Guidelines

Contributions of new datasets, agent implementations, or evaluation methods are welcome. Please ensure:
1. Adherence to existing code structure and naming conventions
2. Sufficient documentation for new features
3. All tests pass

## License

[License information]