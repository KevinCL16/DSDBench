INITIAL_SYSTEM_PROMPT = '''You will receive three components:  
1. **Original Query**: A user query that contain specific **concepts** related to data analysis.  
2. **Correct Data Analysis Code**: A working code snippet designed to analyze the data according to the original query.  
3. **CSV Information**: Details about the structure, content, and sample data from the CSV file being analyzed.

Your task is to:
1. **Identify potential data analysis error types** for each concept mentioned in the **original query**, considering the code and CSV information provided. Give at least **three error types** that are commonly associated with each mentioned concept and **have a real possibility of occuring** within the query and data analysis code.

2. **Explain** why these errors could occur, based on the characteristics of the data (e.g., missing values, incorrect data types, or structural inconsistencies) and how the code addresses or overlooks these issues.

3. **Describe the impact** of each error on the expected outcome, including performance, accuracy, or interpretability.


Return your output in the following **JSON format**:

```json
{
  "concept": {
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  "concept": {
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  
  ......

}
'''

INITIAL_USER_PROMPT = '''### Original Query:
{{query}}


### Correct Data Analysis Code:
{{code}}


### CSV Information
{{csv_info}}

### Concepts
{{concepts}}



### Expected Output:
The expected output format is given below:
```json
{
  "concept_1": [{
    "error_code": "Print the entire code with injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  {
    "error_code": "Print the entire code with injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  {
    "error_code": "Print the entire code with injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  }],
  "concept_2": [{
    "error_code": "Print the entire code with injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  {
    "error_code": "Print the entire code with injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  {
    "error_code": "Print the entire code with injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  }
  ],

  ......

}
```
'''

ERROR_PROMPT = '''There are some errors in the code you gave:
{{error_message}}
please correct the errors.
Then give the complete code and don't omit anything even though you have given it in the above code.'''

LOGICAL_SYSTEM_PROMPT = '''You will receive three components:  
1. **Original Query**: A user query that contain specific requirements related to data analysis.  
2. **Correct Data Analysis Code**: A working code snippet designed to analyze the data according to the original query.  
3. **CSV Information**: Details about the structure, content, and sample data from the CSV file being analyzed.

Your task is to:
1. Inject hard-to-detect logical errors at the **line level** into the provided code, considering both the code and the accompanying CSV data info.
The line-level errors should include misuses of multiple elements in an entire line of code, replacing the original line of code with a totally different one that seems alright but indeed out of place. Ensure these new errors are both original and **creative**, yet realistic enough to be mistakes that a data analyst might plausibly make. Avoid tampering the code at parameter-level, such as changing values passed to a method or pass a value to a wrong parameter an so on. Avoid overly obvious errors. DO NOT put any cues in the actual code that the error is present, you can only use comments to point out your injected errors. Print the entire code.

2. **Explain** how the injected errors lead to issues in data analysis.

3. **Describe the impact** of each error on the expected outcome, including performance, accuracy, or interpretability.


Return your output in the following **JSON format**:

```json
{
    "error_code": "Print the entire code with injected error",
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
}
```
'''

LOGICAL_USER_PROMPT = '''### Original Query:
{{query}}


### Correct Data Analysis Code:
{{code}}


### CSV Information
{{csv_info}}


### Expected Output:
The expected output format is given below:
```json
{
    "error_code": "Print the entire code with injected error",
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
}
```
'''

ERROR_ERASE_PROMPT = '''You are given the following incorrect data analysis code.

### Incorrect Data Analysis Code:
{{code}}

There some places in the code where errors are explicitly stated.

Your task is to only remove the explicit description of the errors in the code (mainly in comments), but leave the error code unaltered.
'''

LIBRARY_SYSTEM_PROMPT = '''You will receive three components:  
1. **Original Query**: A user query that contains specific requirements related to data analysis.  
2. **Correct Data Analysis Code**: A working code snippet designed to analyze the data according to the original query.  
3. **CSV Information**: Details about the structure, content, and sample data from the CSV file being analyzed.

Your task is to:
1. **Identify sklearn and pandas code**: Analyze the provided code and extract all lines where sklearn or pandas libraries are used. Organize these lines in a structured format.

2. **Inject errors that will cause runtime interruptions**: For EACH AND EVERY identified sklearn and pandas lines, inject errors with the following guidelines:
   - **Error Type**: Inject errors that lead to runtime interruptions, such as syntax errors, attribute errors, type errors, or value errors.
   - **Plausibility**: The modified lines should still appear logical and plausible at first glance but contain mistakes that will cause the code to fail during execution.
   - **Contextual alignment**: Ensure the errors take into account the structure and content of the CSV file to create mistakes that are realistic and aligned with potential data issues.
   - **Impact downstream processes**: Errors should trigger runtime interruptions, effectively halting the program before it completes execution.

3. **Explain each error**: For every injected error:
   - Describe **why this is an error** and the conditions under which it would fail.
   - Provide details on the likely runtime error (e.g., `KeyError`, `ValueError`, `AttributeError`, etc.).

4. **Output the structured results**:
   - Provide the **original sklearn and pandas code** in a structured list.
   - Include the **complete modified code with runtime-interrupting errors injected**.
   - Clearly explain each injected error in a concise and structured format.

Return your output in the following **JSON format**:

```json
{
    "original_sklearn_pandas_code": [
        "Original sklearn or pandas code line",
        ...
    ],
    "errors": [
        {
            "code": "Modified whole code file with the injected error",
            "error_type": "Specify the type of runtime-interrupting error (e.g., KeyError, ValueError, etc.)",
            "explanation": "Describe why this is an error and the conditions under which it will cause a runtime interruption"
        },
        ...
    ]
}
```
'''

LIBRARY_USER_PROMPT = '''### Original Query:
{{query}}


### Correct Data Analysis Code:
{{code}}


### CSV Information
{{csv_info}}


### Expected Output:
The expected output format is given below:
```json
{
    "original_sklearn_pandas_code": [
        "Original sklearn or pandas code line",
        ...
    ],
    "errors": [
        {
            "code": "Modified complete code with the injected error",
            "error_type": "Specify the type of runtime-interrupting error (e.g., KeyError, ValueError, etc.)",
            "explanation": "Describe why this is an error and the conditions under which it will cause a runtime interruption"
        },
        ...
    ]
}
```
'''