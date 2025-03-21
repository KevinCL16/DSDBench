DEPRECATE_SYSTEM_PROMPT = '''You will be provided with an original query and a data analysis code. Your task is to:

1. Determine whether the code has any errors in its data analysis process
2. Determine which **error type** from the list below is in the provided code. 
3. **Explain** the error, including:
   - **Explanation**: Explain why this is an error and what issues it may cause.
   - **Expected Outcome**: Explain how this error will affect the data analysis results, such as misleading outcomes, degraded performance, or incorrect interpretations.

### List of Common Error Types:
1. **Algorithm Choice Mismatch**: Using a regression algorithm for classification tasks or a classification algorithm for regression tasks.
2. **Evaluation Metric Mismatch**: Using inappropriate metrics to evaluate model performance.
3. **Handling Categorical Features Incorrectly**: Misusing or incorrectly encoding categorical features.
4. **Data Normalization Issue**: Not normalizing numerical features before using algorithms that are sensitive to feature scales.
5. **Random State Consistency**: Not setting a consistent `random_state`, resulting in non-reproducible results.
6. **Incorrect Interpretation of Output**: Misinterpreting the output of a regression model for classification or not converting outputs to an appropriate form.
7. **Data Leakage**: Applying data transformations (such as scaling or encoding) before splitting into training and testing sets, leading to overly optimistic model performance.
8. **Ignoring Data Imbalance**: Not accounting for class imbalance in the dataset, resulting in misleading performance metrics.
9. **Poor Outcome Visualization**: Inadequate or misleading visualizations that make it difficult to understand model behavior or errors.
10. **Feature Correlation Issues**: Ignoring correlations between features, leading to multicollinearity problems in linear models.

### Output Format:
```json
{
  "is_error": "True or False",
  "error_explanation": {
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  }
}
'''

DEPRECATE_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query:
{{query}}


### Data Analysis Code:
{{code}}


### Your Task: 
1. Check if the code contains any data analysis errors.
2. If you identify an error, determine which error type it corresponds to from the list below.
3. Explain the error, including:
   - **Explanation**: Why this is an error and what issues it may cause.
   - **Expected Outcome**: How this error will affect the analysis results, such as producing misleading conclusions or performance degradation.

### List of Common Error Types:
1. **Algorithm Choice Mismatch**: Using regression algorithms for classification tasks, or vice versa.
2. **Evaluation Metric Mismatch**: Inappropriate metrics to measure performance.
3. **Handling Categorical Features Incorrectly**: Issues in encoding or misusing categorical data.
4. **Data Normalization Issue**: Lack of feature scaling when required by specific algorithms.
5. **Random State Consistency**: Not ensuring reproducible results through a fixed random state.
6. **Incorrect Interpretation of Output**: Misinterpreting model outputs or predictions.
7. **Data Leakage**: Applying transformations before the train-test split.
8. **Ignoring Data Imbalance**: Failing to address class imbalance in datasets.
9. **Poor Outcome Visualization**: Inadequate or misleading visualizations.
10. **Feature Correlation Issues**: Ignoring correlations that could cause multicollinearity problems.


Please follow the output format below:

```json
{
  "is_error": "True or False",
  "error_explanation": {
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  }
}
```  
'''

ERROR_ERASE_PROMPT = '''You are given the following incorrect data analysis code.

### Incorrect Data Analysis Code:
{{code}}

There some places in the code where errors are explicitly stated.

Your task is to only remove the explicit description of the errors in the code (mainly in comments), but leave the error code unaltered.
'''

ERROR_TYPE_PROMPT = [
    "1. **Algorithm Choice Mismatch**: Using a regression algorithm for classification tasks or a classification algorithm for regression tasks.",
    "2. **Evaluation Metric Mismatch**: Using inappropriate metrics to evaluate model performance.",
    "3. **Handling Categorical Features Incorrectly**: Misusing or incorrectly encoding categorical features.",
    "4. **Data Normalization Issue**: Not normalizing numerical features before using algorithms that are sensitive to feature scales.",
    "5. **Random State Consistency**: Not setting a consistent `random_state`, resulting in non-reproducible results.",
    "6. **Incorrect Interpretation of Output**: Misinterpreting the output of a regression model for classification or not converting outputs to an appropriate form.",
    "7. **Data Leakage**: Applying data transformations (such as scaling or encoding) before splitting into training and testing sets, leading to overly optimistic model performance.",
    "8. **Ignoring Data Imbalance**: Not accounting for class imbalance in the dataset, resulting in misleading performance metrics.",
    "9. **Poor Outcome Visualization**: Inadequate or misleading visualizations that make it difficult to understand model behavior or errors.",
    "10. **Feature Correlation Issues**: Ignoring correlations between features, leading to multicollinearity problems in linear models."]


ERROR_VERIFIER_SYSTEM_PROMPT = '''You will be provided with an original query and a data analysis code. Your task is to:

1. Read the Question carefully, determine whether the code has followed the query requirements, if so, further identify any errors in its data analysis process. **If the code faithfully followed seemingly wrong data analysis practices explicitly stated in the Question. Deem it as correct.**
2. **Explain** any errors found, including:
   - **Explanation**: Explain why this is an error and what issues it may cause.
   - **Expected Outcome**: Explain how this error will affect the data analysis results, such as misleading outcomes, degraded performance, or incorrect interpretations.

### Output Format:
```json
{
    "is_error": "true/false",
    "error_explanation": [{
        "error_type": "Describe the type of error",
        "explanation": "Detailed explanation of why this is an error and its impact",
        "expected_outcome": "How this error will affect model performance or results",
        "suggestions": "Specific suggestions for fixing the error"
    },
    {
        "error_type": "Another error type if multiple errors exist",
        "explanation": "Explanation for the second error",
        "expected_outcome": "Expected outcome for the second error",
        "suggestions": "Suggestions for fixing the second error"
    }]
}
```

Important Notes:
1. Always provide the output in the exact JSON format specified above
2. Set "is_error" to "false" if no errors are found
3. If "is_error" is "false", provide an empty array for error_explanation
4. If "is_error" is "true", include all identified errors in the error_explanation array
5. Consider the original query requirements carefully - if the code follows the query's explicit requirements, even if they seem incorrect, consider it correct
'''

ERROR_VERIFIER_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query (Read the Question carefully, if the code followed the requirements in the question, even if you feel that incorrect data analysis practice were used, deem it as correct):
{{query}}


### Data Analysis Code:
{{code}}


### Your Task: 
1. Read the Question carefully, determine whether the code has followed the query requirements, if so, further identify any errors in its data analysis process. **If the code faithfully followed seemingly wrong data analysis practices explicitly stated in the original query. Deem it as correct.**
2. Provide your analysis in the specified JSON format with detailed explanations for each error found.

Please provide your analysis in the following format:

```json
{
    "is_error": "true/false",
    "error_explanation": [{
        "error_type": "Describe the type of error",
        "explanation": "Detailed explanation of why this is an error and its impact",
        "expected_outcome": "How this error will affect model performance or results",
        "suggestions": "Specific suggestions for fixing the error"
    }]
}
```

Note: If multiple errors are found, include multiple objects in the error_explanation array.
If no errors are found, set "is_error" to "false" and provide an empty array for error_explanation.
'''

ERROR_EVAL_SYSTEM_PROMPT = '''You will be provided with an original query and a data analysis code. Your task is to:

1. Read the Question carefully, determine whether the code has followed the query requirements, if so, further identify any errors in its data analysis process.
2. **Explain** any errors found, including:
   - **Explanation**: Explain why these are errors and what issues they may cause.
   - **Expected Outcome**: Explain how these errors will affect the data analysis results, such as misleading outcomes, degraded performance, or incorrect interpretations.

### Output Format:
```json
{
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why these are errors and their impact on the analysis",
    "expected_outcome": "Explain how these errors will affect model performance, accuracy, or interpretability"
}
```

Output only ONE json dict.
'''

ERROR_EVAL_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query:
{{query}}


### Data Analysis Code:
{{code}}


### Your Task: 
1. Read the Question carefully, determine whether the code has followed the query requirements, if so, further identify any errors in its data analysis process.
2. Provide your analysis in the specified JSON format with detailed explanations for each error found.

Please provide your analysis in the following format:

```json
{
    "error_type": "Specify the type of injected errors",
    "explanation": "Describe why these are errors and their impact on the analysis",
    "expected_outcome": "Explain how these errors will affect model performance, accuracy, or interpretability"
}
```

Output only ONE json dict.
'''

EVAL_PROMPT = '''You are given the following two analysis on whether a piece of code contains errors or not.

### Analysis One:
{{ground_truth}}

### Analysis Two:
{{eval_dict}}

Determine if Analysis Two points out the exact same errors as Analysis One:

- If Analysis Two identifies all the same errors (type, location, and severity) as Analysis One, score it **1**.
- If Analysis Two has partial overlap by identifying some errors correctly but misses or adds other errors, score it **0.5**.
- If Analysis Two fails to identify any errors present in Analysis One, score it **0**.

Your output format should be: SCORE[1/0.5/0]
'''

RUBBER_DUCK_EVAL_PROMPT_OLD = '''You are provided with the following analyses of errors in a piece of code:

### Ground Truth:
```json
{{ground_truth}}
```

### LLM Output:
```json
{{eval_dict}}
```


Evaluate the LLM Output against the Ground Truth separately for cause_line, effect_line, and error_message based on the following criteria:

### Evaluation Criteria:
1. Cause Line Matching (cause_line_score):
  - Score 1: The cause_line in the LLM Output exactly matches the cause_line in the Ground Truth.
  - Score 0: The cause_line in the LLM Output does not match the Ground Truth.
2. Effect Line Matching (effect_line_score):
  - Score 1: The effect_line in the LLM Output exactly matches the effect_line in the Ground Truth.
  - Score 0: The effect_line in the LLM Output does not match the Ground Truth.
3. Error Message Matching (error_message_score):
  - You will be given the full traceback and error message in the ground truth for reference, however, when giving score, only compare the error description against the LLM output, the LLM is not supposed to output the full traceback stack.
  - Score 1: The error_message in the LLM Output exactly matches the error_message (except the full traceback) in the Ground Truth.
  - Score 0.5: The error_message in the LLM Output is partially correct (e.g., captures the general idea but misses specific details or phrasing).
  - Score 0: The error_message in the LLM Output does not match the Ground Truth at all.

### Output Format:
```json 
{
    "cause_line_score": 1/0,
    "effect_line_score": 1/0,
    "error_message_score": 1/0.5/0
}
```
'''

RUBBER_DUCK_EVAL_SYSTEM_PROMPT = '''You will be provided with an original query and a data analysis code. Your task is to:

1. Read the question carefully and identify if there are any logic error injected into the code.
2. For each logic error:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback).
Output Format:
```json 
{
    "cause_line": "Specify the exact line of code causing the issue",
    "effect_line": "Specify the exact line of code where the error will be triggered",
    "error_message": "Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback)"
}
```

There will be only one error in the code. Output only ONE json dict in your response.
'''

RUBBER_DUCK_EVAL_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query:
{{query}}


### Data Analysis Code:
{{code}}


1. Read the question carefully and identify if there are any logic error injected into the code.
2. For each logic error:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback).
  
### Output Format:
```json 
{
    "cause_line": "Specify the exact line of code causing the issue",
    "effect_line": "Specify the exact line of code where the error will be triggered",
    "error_message": "Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback)"
}
```

There will be only one error in the code. Output only ONE json dict in your response.
'''

RUBBER_DUCK_EVAL_PROMPT = '''You are provided with the following analyses of errors in a piece of code:

### Ground Truth:
```json
{{ground_truth}}
```

### LLM Output:
```json
{{eval_dict}}
```

### Evaluation Task:  
Evaluate the LLM's output for code error analysis against the Ground Truth (GT) in three dimensions: **cause line**, **effect line**, and **error message**.


### Evaluation Criteria:  
1. **Cause Line Matching** (`cause_line_score`):  
   - **Score 1**: The `cause_line` in the LLM Output **exactly matches** the `cause_line` in the Ground Truth.  
   - **Score 0**: Otherwise.  

2. **Effect Line Matching** (`effect_line_score`):  
   - **Score 1**: The `effect_line` in the LLM Output **exactly matches** the `effect_line` in the Ground Truth.  
   - **Score 0**: Otherwise.  

3. **Error Type Matching** (`error_type_score`):  
   - **Score 1**: The error type in the LLM Output **exactly matches** the error type in the Ground Truth.
   - **Score 0**: Otherwise.

4. **Error Message Matching** (`error_message_score`):  
   - **Evaluation Scope**: Compare only the **error description** (ignore the full traceback or stack details).  
   - **Scoring Method**:  
     - **1.0**: The error description in the LLM Output **exactly matches** the GT (including all key details).  
     - **0.75**: The error description is **mostly correct** but lacks minor details.  
     - **0.5**: The error description is **partially correct** but contains vague or incomplete information.  
     - **0.25**: The error description is **only loosely related** to the GT.  
     - **0.0**: The error description is **completely irrelevant or incorrect**.  
   - **Justification**: The LLM must provide a brief justification for the score.  
     ```  
     "error_message_eval_reason": "<Specific justification for the score>"  
     ```  

---

### Output Format:  
```json  
{  
    "cause_line_score": 1/0,  
    "effect_line_score": 1/0,
    "error_type_score": 1/0,  
    "error_message_score": 0.0/0.25/0.5/0.75/1.0,  
    "error_message_eval_reason": "Scoring justification (in English)"  
}  
```
'''

MULTI_RUBBER_DUCK_EVAL_PROMPT = '''You are provided with a Ground Truth error analysis (as a list of *independent* error dictionaries) and an LLM Output error analysis (for a *single* detected error).

### Ground Truth Errors (List of *Independent* Error Dictionaries):
```json
{{ground_truth}}
```
*Important*: Each dictionary in `ground_truth_errors` represents a *specific and independent* error in the code. The information within each dictionary (cause line, effect line, error message, error type) is linked and describes a *single, distinct* error instance. These dictionaries are *not interchangeable*.

### LLM Output Error:
```json
{{llm_output_error}}
```

### Evaluation Task:
Evaluate the LLM's output error analysis against the Ground Truth errors.  Determine if the LLM's detected error *holistically matches* any *specific error instance* described in the Ground Truth Errors list.  A holistic match means the cause line, effect line, error message, *and error type* from the LLM's output should correspond to the *same* error instance in the Ground Truth.

### Evaluation Criteria:

For the LLM Output Error, you must compare it against *each* error dictionary in the `ground_truth_errors` list to find a *holistic match*.  A score is awarded only if the LLM's output aligns with a *single, specific error instance* from the Ground Truth.  Simply matching error types or messages across different Ground Truth error dictionaries is *not* sufficient for a high score.

1.  **Cause Line Matching** (`cause_line_score`):
    -   **Score 1**: The `cause_line` in the LLM Output **exactly matches** the `cause_line` of **at least one *specific* error instance** (i.e., one dictionary) in the `ground_truth_errors` list.
    -   **Score 0**: Otherwise.

2.  **Effect Line Matching** (`effect_line_score`):
    -   **Score 1**: The `effect_line` in the LLM Output **exactly matches** the `effect_line` of the **same *specific* error instance** (the same dictionary in `ground_truth_errors` that you matched the cause line with in step 1).
    -   **Score 0**: Otherwise.

3.  **Error Type Matching** (`error_type_score`):
    -   **Score 1**: The `error_type` in the LLM Output **exactly matches** the `error_type` of the **same *specific* error instance** (the same dictionary used in steps 1 and 2).
    -   **Score 0**: Otherwise.

4.  **Error Message Matching** (`error_message_score`):
    -   **Evaluation Scope**: Compare only the **error description**.
    -   **Scoring Method**:
        -   **1.0**: The error description in the LLM Output **exactly matches** the `error_message` of the **same *specific* error instance** (the same dictionary used in steps 1, 2, and 3).
        -   **0.75**: The error description is **mostly correct** compared to the `error_message` of the **same *specific* error instance**, but lacks minor details or has slight variations.
        -   **0.5**: The error description is **partially correct** but contains vague or incomplete information compared to the `error_message` of the **same *specific* error instance**.
        -   **0.25**: The error description is **only loosely related** to the `error_message` of the **same *specific* error instance**.
        -   **0.0**: The error description is **completely irrelevant or incorrect** compared to the `error_message` of **the same *specific* error instance** and all other error messages in `ground_truth_errors`.
    -   **Justification**: Provide a *detailed* justification for the score. *Crucially, explicitly identify which specific error instance from `ground_truth_errors` (e.g., "Ground Truth Error 1", "Ground Truth Error 2", etc.) you are comparing against and explain why you assigned the score, especially if it's not a perfect score.* If there's no holistic match with *any* error instance in `ground_truth_errors`, state that clearly in the justification.
        ```
        "error_message_eval_reason": "<Detailed justification, e.g., 'Holistically matched Ground Truth Error 1 perfectly.', 'Cause and Effect lines and Error Type matched Ground Truth Error 2, but error message was partially correct - hence 0.5 score.', 'No holistic match found with any error instance in Ground Truth Errors list.'>"
        ```

---

### Output Format:
```json
{
    "cause_line_score": 1/0,
    "effect_line_score": 1/0,
    "error_type_score": 1/0,
    "error_message_score": 0.0/0.25/0.5/0.75/1.0,
    "error_message_eval_reason": "Detailed scoring justification (in English)"
}
```
'''

MULTI_RUBBER_DUCK_EVAL_SYSTEM_PROMPT = '''You will be provided with a data analysis code. Your task is to:

1. Read the code carefully and identify all logic errors injected into the code. There will be two or more logic errors in the code.
2. For each logic error you identify:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error or where the incorrect behavior is observed.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback). Focus on the *type* of error and the *reason* if possible from the output.

Output Format:
```json
[
    {
        "cause_line": "Specify the exact line of code causing error 1",
        "effect_line": "Specify the exact line of code where error 1 is triggered",
        "error_message": "Concise error message for error 1"
    },
    {
        "cause_line": "Specify the exact line of code causing error 2",
        "effect_line": "Specify the exact line of code where error 2 is triggered",
        "error_message": "Concise error message for error 2"
    },
    ... (and so on for all identified errors)
]```
There will be more than one error in the code. BUT output only ONE json block in your response.
'''

MULTI_RUBBER_DUCK_EVAL_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query:
{{query}}


### Data Analysis Code:
{{code}}


1. Read the code carefully and identify all logic errors injected into the code. There will be two or more logic errors in the code.
2. For each logic error you identify:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error or where the incorrect behavior is observed.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback). Focus on the *type* of error and the *reason* if possible from the output.

Output Format:
```json
[
    {
        "cause_line": "Specify the exact line of code causing error 1",
        "effect_line": "Specify the exact line of code where error 1 is triggered",
        "error_message": "Concise error message for error 1"
    },
    {
        "cause_line": "Specify the exact line of code causing error 2",
        "effect_line": "Specify the exact line of code where error 2 is triggered",
        "error_message": "Concise error message for error 2"
    },
    ... (and so on for all identified errors)
]```
There will be more than one error in the code. BUT output only ONE json block in your response.
'''

RUBBER_DUCK_ZERO_COT_SYSTEM_PROMPT = '''You will be provided with an original query and a data analysis code. Your task is to:

1. Read the question carefully and identify if there are any logic error injected into the code.
2. For each logic error:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback).

First, think step-by-step about the code and identify the logic error. Explain your reasoning process clearly.

After presenting your CoT reasoning, output the answer in the following JSON format. Ensure you provide both the CoT reasoning and the JSON output in your response.

Output Format:

**CoT Output:**
Your step-by-step reasoning process here

**JSON Output:**
```json
{
    "cause_line": "Specify the exact line of code causing the issue",
    "effect_line": "Specify the exact line of code where the error will be triggered",
    "error_message": "Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback)"
}
```

There will be only one error in the code. Output your CoT reasoning first, followed by the one ONLY json output in your response.'''

RUBBER_DUCK_ZERO_COT_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query:
{{query}}


### Data Analysis Code:
{{code}}


You will be provided with an original query and a data analysis code. Your task is to:

1. Read the question carefully and identify if there are any logic error injected into the code.
2. For each logic error:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback).

First, think step-by-step about the code and identify the logic error. Explain your reasoning process clearly.

After presenting your CoT reasoning, output the answer in the following JSON format. Ensure you provide both the CoT reasoning and the JSON output in your response.

Output Format:

**CoT Output:**
Your step-by-step reasoning process here

**JSON Output:**
```json
{
    "cause_line": "Specify the exact line of code causing the issue",
    "effect_line": "Specify the exact line of code where the error will be triggered",
    "error_message": "Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback)"
}
```

There will be only one error in the code. Output your CoT reasoning first, followed by the one ONLY json output in your response.
'''

MULTI_RUBBER_DUCK_ZERO_COT_SYSTEM_PROMPT = '''You will be provided with a data analysis code. Your task is to:

1. Read the code carefully and identify all logic errors injected into the code. There will be two or more logic errors in the code.
2. For each logic error you identify:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error or where the incorrect behavior is observed.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback). Focus on the *type* of error and the *reason* if possible from the output.

First, think step-by-step through the code and identify each logic error.  Explain your reasoning process for each error clearly.

After presenting your CoT reasoning for all identified errors, output the answer in the following JSON format. Ensure you provide both the CoT reasoning and the JSON output in your response.

Output Format:

**Chain of Thought (CoT) Output:**
Your step-by-step reasoning process for error 1 here, 
Your step-by-step reasoning process for error 2 here
... (and so on for all identified errors)

**JSON Output:**
```json
[
    {
        "cause_line": "Specify the exact line of code causing error 1",
        "effect_line": "Specify the exact line of code where error 1 is triggered",
        "error_message": "Concise error message for error 1"
    },
    {
        "cause_line": "Specify the exact line of code causing error 2",
        "effect_line": "Specify the exact line of code where error 2 is triggered",
        "error_message": "Concise error message for error 2"
    },
    ... (and so on for all identified errors)
]```
There will be more than one error in the code. Output your CoT reasoning first, followed by only ONE json block in your response.'''

MULTI_RUBBER_DUCK_ZERO_COT_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query:
{{query}}


### Data Analysis Code:
{{code}}


You will be provided with a data analysis code. Your task is to:

1. Read the code carefully and identify all logic errors injected into the code. There will be two or more logic errors in the code.
2. For each logic error you identify:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error or where the incorrect behavior is observed.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback). Focus on the *type* of error and the *reason* if possible from the output.

First, think step-by-step through the code and identify each logic error.  Explain your reasoning process for each error clearly.

After presenting your CoT reasoning for all identified errors, output the answer in the following JSON format. Ensure you provide both the CoT reasoning and the JSON output in your response.

Output Format:

**Chain of Thought (CoT) Output:**
Your step-by-step reasoning process for error 1 here, 
Your step-by-step reasoning process for error 2 here
... (and so on for all identified errors)

**JSON Output:**
```json
[
    {
        "cause_line": "Specify the exact line of code causing error 1",
        "effect_line": "Specify the exact line of code where error 1 is triggered",
        "error_message": "Concise error message for error 1"
    },
    {
        "cause_line": "Specify the exact line of code causing error 2",
        "effect_line": "Specify the exact line of code where error 2 is triggered",
        "error_message": "Concise error message for error 2"
    },
    ... (and so on for all identified errors)
]```
There will be more than one error in the code. Output your CoT reasoning first, followed by only ONE json block in your response.
'''