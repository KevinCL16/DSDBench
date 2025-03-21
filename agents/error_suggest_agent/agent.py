import io
import json
import os
import re
import shutil
import pandas as pd
from tqdm import tqdm

from agents.generic_agent import GenericAgent
from agents.openai_chatComplete import completion_with_backoff
from agents.utils import fill_in_placeholders, get_error_message, is_run_code_success, run_code
from agents.utils import print_filesys_struture
from agents.error_inject_agent.prompt import ERROR_TYPE_PROMPT
from agents.utils import change_directory


def get_code2(response, file_name):
    all_python_code_blocks_pattern = re.compile(r'```\s*([\s\S]+?)\s*```', re.MULTILINE)
    all_code_blocks = all_python_code_blocks_pattern.findall(response)
    all_code_blocks_combined = '\n'.join(all_code_blocks)
    if all_code_blocks_combined == '':

        response_lines = response.split('\n')
        code_lines = []
        code_start = False
        for line in response_lines:
            if line.find('import') == 0 or code_start:
                code_lines.append(line)
                code_start = True
            if code_start and line.find(file_name)!=-1 and line.find('(') !=-1 and line.find(')')!=-1 and line.find('(') < line.find(file_name)< line.find(')'): #要有文件名，同时要有函数调用

                return '\n'.join(code_lines)
    return all_code_blocks_combined


def get_code(response):

    all_python_code_blocks_pattern = re.compile(r'```python\s*([\s\S]+?)\s*```', re.MULTILINE)
    all_code_blocks = all_python_code_blocks_pattern.findall(response)
    all_code_blocks_combined = '\n'.join(all_code_blocks)
    return all_code_blocks_combined


def clean_json_string(json_str):
    # Locate the injected_code value
    start_index = json_str.find('"error_code": "') + len('"error_code": "')
    end_index = json_str.find('",', start_index)

    # Extract the code part and replace newlines and quotes
    code_part = json_str[start_index:end_index]
    cleaned_code_part = code_part.replace('\n', '\\n').replace('"', '\"')

    # Replace the original code part in the json_str with the cleaned code part
    cleaned_json_str = json_str[:start_index] + cleaned_code_part + json_str[end_index:]

    return cleaned_json_str


def extract_csv_info_as_string(file_path):
    # Load the CSV file
    df = pd.read_csv(file_path)

    # Use StringIO to capture df.info() output
    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()

    # Create a string with the CSV information
    csv_info_str = f"""
CSV File Information:
----------------------
Shape: {df.shape[0]} rows, {df.shape[1]} columns

Columns: {', '.join(df.columns)}

Data Types and Non-null Values:
{info_str}

Sample Data (First 5 Rows):
{df.head().to_string(index=False)}
"""

    # Statistical Summary(Numeric Columns):
    # {df.describe().to_string()}

    return csv_info_str


class ErrorSuggestAgent(GenericAgent):
    def __init__(self, workspace, **kwargs):
        super().__init__(workspace, **kwargs)
        self.chat_history = []
        self.query = kwargs.get('query', '')
        self.data_information = kwargs.get('data_information', None)

    def raw_generate(self, user_prompt, model_type):
        messages = [{"role": "system", "content": ''}, {"role": "user", "content": user_prompt}]

        self.chat_history = self.chat_history + messages
        return completion_with_backoff(messages, model_type)

    def generate(self, user_prompt, model_type, code, csv_info, concepts):

        workspace_structure = print_filesys_struture(self.workspace)
        
        information = {
            'workspace_structure': workspace_structure,
            'code': code,
            'query': user_prompt,
            'csv_info': csv_info,
            'concepts': concepts
        }


        messages = []
        messages.append({"role": "system", "content": fill_in_placeholders(self.prompts['system'], information)})
        messages.append({"role": "user", "content": fill_in_placeholders(self.prompts['user'], information)})



        self.chat_history = self.chat_history + messages
        return completion_with_backoff(messages, model_type)

    def run(self, queries, model_type, code):
        log = []
        suggest_results = []
        file_name = queries['file_name']
        error_code_directory = os.path.join(self.workspace, 'error_code_dir')
        os.makedirs(error_code_directory, exist_ok=True)

        src = os.path.join(self.workspace, file_name)
        dst = os.path.join(error_code_directory, file_name)
        shutil.copy(src, dst)

        # Load the CSV file
        csv_info = extract_csv_info_as_string(src)

        query = queries
        print(f"\n------------------------ Processing Query {query['id']} ------------------------")
        log.append(f"\n------------------------ Processing Query {query['id']} ------------------------")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")
        log.append(f"Constraints: {query['constraints']}")
        log.append(f"Concepts: {query['concepts']}")
        log.append(f"Data File: {query['file_name']}")
        log.append(f"Expected Format: {query['format']}")
        log.append(f"Ground Truth: {query['answers']}")

        prompt = f"""Question ID: {query['id']}
    Question: {query['question']}
                    
    Constraints: {query['constraints']}
    
    Data File Name: {query['file_name']}
                    
    Format: {query['format']}
    
    Correct answer: {query['answers']}
    
    **Concepts: {query['concepts']}**
                    """

        concepts = query['concepts']
        log.append("\n\n...Generating error types...\n\n")
        result = self.generate(prompt, model_type=model_type, code=code, csv_info=csv_info, concepts=concepts)

        '''try:
            # Locate the first curly brace to the last one for extracting the JSON object
            start_index = result.find('{')
            end_index = result.rfind('}')

            if start_index == -1 or end_index == -1:
                raise ValueError("No valid JSON found in the input string.")

            # Extract the JSON substring
            json_str = result[start_index:end_index + 1]
            cleaned_json_str = clean_json_string(json_str)

            # Convert the extracted JSON string to a Python dictionary
            result_dict = json.loads(cleaned_json_str)

        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {e}")'''

        try:
            # Locate the first curly brace to the last one for extracting the JSON object
            start_index = result.find('{')
            end_index = result.rfind('}')

            if start_index == -1 or end_index == -1:
                raise ValueError("No valid JSON found in the input string.")

            # Extract the JSON substring and clean it if necessary
            json_str = result[start_index:end_index + 1]
            cleaned_json_str = clean_json_string(json_str)

            # Convert the extracted JSON string to a Python dictionary
            result_dict = json.loads(cleaned_json_str)

            # Write the entire dictionary as a single line to a jsonl file
            with open(os.path.join(error_code_directory, 'logical_error_data.jsonl'), 'w') as jsonl_file:
                jsonl_file.write(json.dumps(result_dict, indent=4) + '\n')

            # Loop through each concept in the dictionary and extract details
            for concept, entries in result_dict.items():
                print(f"Concept: {concept}")
                for idx, entry in enumerate(entries):
                    injected_code = entry.get('error_code', '')
                    error_type = entry.get('error_type', '')
                    error_explanation = entry.get('explanation', '')
                    expected_outcome = entry.get('expected_outcome', '')

                    file_name = f'logical_error_{concept}_{idx}_injected.py'
                    with open(os.path.join(error_code_directory, file_name), 'w') as f:
                        f.write(injected_code)
                    error_code_result = run_code(error_code_directory, file_name)

                    # Use the extracted variables as needed
                    log.append(f"\nInjected Code {concept} {idx}:\n{injected_code}\n")
                    log.append(f"\nError Type {concept} {idx}:\n{error_type}\n")
                    log.append(f"\nError Explanation {concept} {idx}: {error_explanation}\n")
                    log.append(f"\nExpected Outcome {concept} {idx}: {expected_outcome}\n")
                    log.append(f"\nError injected code execution result: {error_code_result}\n")
                    log.append(f"\n***************************************************************************************\n")

        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {e}")

        '''# Extract and store the expected result
        injected_code = result_dict.get('error_code', '')
        error_explanation = result_dict.get('explanation', '')
        expected_outcome = result_dict.get('expected_outcome', '')'''

        # Wrap the extracted information
        suggest_results.append({
            'suggest_result': result
        })

        # log.append(f"Generated code for Query {index}:")
        # log.append(injected_code)
        # log.append("\n" + "-"*50)

        # Join the log list into a single string

        log_string = "\n".join(log)
        return log_string, suggest_results

    def run_logical(self, queries, model_type, data_folder):
        log = []
        suggest_results = []
        file_name = queries['file_name']
        error_code_directory = os.path.join(self.workspace, 'error_code')
        os.makedirs(error_code_directory, exist_ok=True)

        src = os.path.join(data_folder, file_name)

        # Load the CSV file
        csv_info = extract_csv_info_as_string(src)
        code = queries["correct_analysis_code"]

        query = queries
        print(f"\n------------------------ Processing Query {query['id']} ------------------------")
        log.append(f"\n------------------------ Processing Query {query['id']} ------------------------")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")
        log.append(f"Constraints: {query['constraints']}")
        log.append(f"Concepts: {query['concepts']}")
        log.append(f"Data File: {query['file_name']}")
        log.append(f"Expected Format: {query['format']}")
        log.append(f"Ground Truth: {query['answers']}")

        prompt = f"""Question ID: {query['id']}
    Question: {query['question']}

    Constraints: {query['constraints']}

    Data File Name: {query['file_name']}

    Format: {query['format']}

    Correct answer: {query['answers']}

    **Concepts: {query['concepts']}**
                    """

        concepts = query['concepts']
        log.append("\n\n...Generating error types...\n\n")
        result = self.generate(prompt, model_type=model_type, code=code, csv_info=csv_info, concepts=concepts)

        try:
            # Locate the first curly brace to the last one for extracting the JSON object
            start_index = result.find('{')
            end_index = result.rfind('}')

            if start_index == -1 or end_index == -1:
                raise ValueError("No valid JSON found in the input string.")

            # Extract the JSON substring and clean it if necessary
            json_str = result[start_index:end_index + 1]
            cleaned_json_str = clean_json_string(json_str)

            # Convert the extracted JSON string to a Python dictionary
            result_dict = json.loads(cleaned_json_str)

            injected_code = result_dict['error_code']

            information = {
                'code': injected_code,
            }

            messages = []
            messages.append({"role": "system", "content": ''})
            messages.append({"role": "user", "content": fill_in_placeholders(self.prompts['error'], information)})

            error_hidden_result = completion_with_backoff(messages, model_type)
            error_hidden_code = get_code(error_hidden_result)

            error_type = result_dict['error_type']
            error_explanation = result_dict['explanation']
            # expected_outcome = result_dict['expected_outcome']

            result_dict['error_hidden_code'] = error_hidden_code
            query.update(result_dict)

            # Write the entire dictionary as a single line to a jsonl file
            with open(os.path.join(error_code_directory, 'hard_library_wrong.jsonl'), 'a') as jsonl_file:
                jsonl_file.write(json.dumps(query) + '\n')

            # Use the extracted variables as needed
            log.append(f"\nInjected Code:\n{injected_code}\n")
            log.append(f"\nError Erased Code:\n{error_hidden_code}\n")
            log.append(f"\nError Type:\n{error_type}\n")
            log.append(f"\nError Explanation: {error_explanation}\n")
            # log.append(f"\nExpected Outcome: {expected_outcome}\n")

            log.append(f"\n***************************************************************************************\n")

        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {e}")

        log_string = "\n".join(log)
        return log_string, error_hidden_code

    def run_library(self, queries, model_type, data_folder):
        log = []
        file_name = queries['file_name']
        error_code_directory = os.path.join(self.workspace, 'error_code')
        os.makedirs(error_code_directory, exist_ok=True)

        src = os.path.join(data_folder, file_name)
        csv_info = extract_csv_info_as_string(src)
        code = queries["correct_analysis_code"]

        # Log basic information
        query = queries
        print(f"\n------------------------ Processing Query {query['id']} ------------------------")
        log.append(f"\n------------------------ Processing Query {query['id']} ------------------------")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")
        log.append(f"Data File: {query['file_name']}")

        prompt = f"""Question ID: {query['id']}
    Question: {query['question']}
    Data File Name: {query['file_name']}
    Format: {query['format']}
    """

        # Generate library usage analysis and error injection
        result = self.generate(prompt, model_type=model_type, code=code, csv_info=csv_info, concepts='')

        try:
            # Parse JSON response
            start_index = result.find('{')
            end_index = result.rfind('}')
            if start_index == -1 or end_index == -1:
                raise ValueError("No valid JSON found in the input string.")
            
            json_str = result[start_index:end_index + 1]
            result_dict = json.loads(json_str)
            
            # Process each error case
            for error_case in result_dict.get('errors', []):
                injected_code = error_case.get('code', '')
                error_type = error_case.get('error_type', '')
                error_explanation = error_case.get('explanation', '')

                # Remove error comments from code
                information = {'code': injected_code}
                messages = [
                    {"role": "system", "content": ''},
                    {"role": "user", "content": fill_in_placeholders(self.prompts['error'], information)}
                ]
                clean_code_result = completion_with_backoff(messages, model_type)
                clean_code = get_code(clean_code_result)
                
                # Update error case with cleaned code
                error_case['clean_code'] = clean_code
                
                # Log the results
                log.append(f"\nOriginal sklearn/pandas code:\n{', '.join(result_dict.get('original_sklearn_pandas_code', []))}\n")
                log.append(f"\nInjected Code:\n{injected_code}\n")
                log.append(f"\nCleaned Code:\n{clean_code}\n")
                log.append(f"\nError Type:\n{error_type}\n")
                log.append(f"\nError Explanation: {error_explanation}\n")
                log.append(f"\n{'*' * 80}\n")

            # Save results to JSONL file
            queries.update(result_dict)
            with open(os.path.join(error_code_directory, 'gpt-4o_dabench_hard_library_errors.jsonl'), 'a') as jsonl_file:
                jsonl_file.write(json.dumps(queries) + '\n')

        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {e}")

        log_string = "\n".join(log)
        return log_string, result_dict

    def run_snoop(self, queries, model_type, data_folder, individual_workspace):
        log = []
        error_code_directory = os.path.join(self.workspace, 'sklearn_pandas_errors')
        individual_error_code_directory = os.path.join(individual_workspace, 'error_code_dir')
        os.makedirs(error_code_directory, exist_ok=True)
        os.makedirs(individual_error_code_directory, exist_ok=True)

        # Extract file name and source path
        '''file_name = queries['file_name']
        src = os.path.join(individual_workspace, file_name)
        dst = os.path.join(individual_error_code_directory, file_name)
        shutil.copy(src, dst)'''

        # Process each error version in the error_versions list
        for i, error_case in enumerate(queries.get('error_versions', [])):
            clean_code = error_case.get('modified_code', '')
            if not clean_code:
                continue

            # Split the code into imports and main body
            code_lines = clean_code.split('\n')
            import_lines = []
            body_lines = []

            for line in code_lines:
                if line.strip().startswith(('import ', 'from ')):
                    import_lines.append(line)
                else:
                    body_lines.append(line)

            # Create the monitored version of the code
            monitored_code = '\n'.join([
                *import_lines,
                'import snoop',
                '',
                '@snoop',
                'def main():',
                *['    ' + line for line in body_lines if line.strip()],
                '',
                'if __name__ == "__main__":',
                '    main()'
            ])

            '''for line in code_lines:
                if line.strip().startswith(('import ', 'from ')):
                    import_lines.append(line)
                else:
                    body_lines.append(line)

            # Add snoop import
            import_lines.append('import snoop')

            # Add @snoop decorator to all functions
            decorated_body = []
            for line in body_lines:
                stripped_line = line.strip()
                if stripped_line.startswith('def '):  # Detect function definitions
                    decorated_body.append('@snoop')  # Add @snoop before the function
                decorated_body.append(line)  # Append the original line

            # Combine imports and body
            monitored_code = '\n'.join([
                *import_lines,
                '',
                *decorated_body,
            ])'''

            # Save the monitored code to a file
            error_file = f'error_{i}_monitored.py'
            error_file_path = os.path.join(individual_error_code_directory, error_file)
            with open(error_file_path, 'w') as f:
                f.write(monitored_code)

            # Capture the execution output
            try:
                # Run the code and capture output
                output = run_code(individual_error_code_directory, error_file)
                    
                # Update the error case with execution results
                error_case['execution_output'] = output
                error_case['monitored_code'] = monitored_code
                    
                log.append(f"\nExecuting error case {i}:")
                log.append(f"Error type: {error_case.get('error_type', 'Unknown')}")
                log.append(f"Execution output:\n{output}\n")
                log.append("-" * 80)

            except Exception as e:
                error_msg = f"Error executing {error_file}: {str(e)}"
                error_case['execution_output'] = error_msg
                log.append(f"\nError in case {i}: {error_msg}")

        # Save the updated queries with execution results
        output_file = os.path.join(error_code_directory, f'{model_type}_matplotbench_monitored_errors_with_use_agg.jsonl')
        with open(output_file, 'a') as f:
            f.write(json.dumps(queries) + '\n')

        log_string = "\n".join(log)
        return log_string, queries

    def process_sklearn_pandas_code(self, queries, model_type, data_folder, individual_workspace):
        log = []
        # Step 1: Identify sklearn and pandas code
        """identify_sk_pd_prompt = f### Original Query:
{queries['question']}

### Correct Data Analysis Code:
{queries['correct_analysis_code']}

### CSV Information
{extract_csv_info_as_string(os.path.join(data_folder, queries['file_name']))}

### Task:
Identify and extract all lines of code that use sklearn, pandas libraries for actual data processing or analysis.
Rules:
1. Skip import statements
2. Only include lines that actively use pandas/sklearn functionality (e.g., data loading, model training, predictions)
3. Include the complete line of code, not just the method calls
4. Focus on core functionality like:
   - Data loading and manipulation (pd.read_csv, DataFrame operations)
   - Model creation and training (model.fit)
   - Predictions and evaluations (model.predict, metrics)
   - Data transformations (train_test_split, imputation)

### Expected Output:
The expected output format is given below:
```json
{
    "original_sklearn_pandas_code": [
        {
            "line": "Complete line of code using sklearn/pandas",
            "purpose": "Brief description of what this line does",
            "library": "sklearn or pandas"
        },
        ...
    ]
}
```
"""

        identify_prompt = f"""### Original Query:
        {queries['question']}

### Correct Data Analysis Code:
{queries['correct_analysis_code']}



### Task:  
Identify and extract all lines of code that use **numpy**, **scipy**, and **matplotlib** libraries for actual data processing, analysis, or visualization.  

### Rules:  
1. Skip import statements.  
2. Only include lines that actively use **numpy**, **scipy**, or **matplotlib** functionality (e.g., array manipulations, statistical operations, plotting).  
3. Include the **complete line of code**, not just the method calls.  
4. Focus on core functionality like:  
   - **Numpy**: Array creation, manipulation, and mathematical computations (e.g., `np.array`, `np.mean`, `np.dot`).  
   - **Scipy**: Statistical or mathematical operations, optimization, and integration (e.g., `scipy.stats`, `scipy.optimize`).  
   - **Matplotlib**: Data visualization (e.g., `plt.plot`, `plt.scatter`, `plt.imshow`).  

### Expected Output:  
The expected output format is given below:  
```json
{{
    "original_package_code": [
        {{
            "line": "Complete line of code using numpy/scipy/matplotlib",
            "purpose": "Brief description of what this line does",
            "library": "numpy, scipy, or matplotlib"
        }},
        ...
    ]
}}
```
"""

        identify_dseval_prompt = f"""### Original Query:
        {queries['question']}

### Correct Data Analysis Code:
{queries['correct_analysis_code']}


### Task:
Identify and extract all lines of code that use numpy, scipy, and sklearn libraries for actual data processing or analysis.  
Rules:  
1. Skip import statements.  
2. Only include lines that actively use numpy, scipy, or sklearn functionality (e.g., array manipulations, statistical operations, model training, predictions).  
3. Include the complete line of code, not just the method calls.  
4. Focus on core functionality like:  
   - Array creation and manipulation (e.g., `np.array`, `np.mean`, `np.dot`).  
   - Statistical or mathematical computations (e.g., `scipy.stats`, `scipy.optimize`).  
   - Model creation and training (e.g., `model.fit`, `model.predict`).  
   - Data transformations (e.g., `train_test_split`, feature scaling, imputation).  

### Expected Output:
The expected output format is given below:
```json
{{
    "original_package_code": [
        {{
            "line": "Complete line of code using numpy/scipy/sklearn",
            "purpose": "Brief description of what this line does",
            "library": "numpy, scipy, or sklearn"
        }},
        ...
    ]
}}
```
"""

        # Call LLM to identify sklearn and pandas code
        print(f"**********Running example {queries['id']}**********")
        result = self.raw_generate(identify_prompt, model_type=model_type)
        start_index = result.find('{')
        end_index = result.rfind('}')
        if start_index == -1 or end_index == -1:
            raise ValueError("No valid JSON found in the input string.")
        
        json_str = result[start_index:end_index + 1]
        result_dict = json.loads(json_str)
        original_code_lines = result_dict.get('original_package_code', [])

        # Step 2: Inject errors for each identified line
        errors = []
        original_code = queries['correct_analysis_code']
        
        for code_info in tqdm(original_code_lines):
            code_line = code_info['line']
            error_injection_prompt = f"""### Original Query:
{queries['question']}

### Original Complete Code:
{original_code}

### Target Line to Modify:
{code_line}

### Task:
Create a version of the complete code where you inject a subtle logical error by modifying the target line.
The error should:
1. Not be immediately obvious
2. Appear plausible at first glance
3. Cause incorrect results or runtime issues
4. Be related to the sklearn/pandas usage in the target line

### Expected Output:
The expected output format is given below:
```json
{{
    "modified_code": "The **complete** version of the code with the injected error. Ensure the output contains the entire modified code, not just the changed line.",
    "original_line": "The original line that was modified",
    "modified_line": "The new version of the line with the error",
    "error_type": "Type of error (e.g., LogicalError, RuntimeError)",
    "explanation": "Detailed explanation of the error and its impact"
}}
```
"""
            # Call LLM to inject error
            error_result = self.raw_generate(error_injection_prompt, model_type=model_type)
            error_start_index = error_result.find('{')
            error_end_index = error_result.rfind('}')
            if error_start_index == -1 or error_end_index == -1:
                continue
            
            try:
                error_json_str = error_result[error_start_index:error_end_index + 1]
                error_dict = json.loads(error_json_str)
                errors.append(error_dict)
                
                log.append(f"\nProcessing original line: {code_line}")
                log.append(f"\nModified erroneous line: {error_dict.get('modified_line')}")
                log.append(f"Error type: {error_dict.get('error_type', 'Unknown')}")
                log.append(f"Explanation: {error_dict.get('explanation', '')}")
                log.append("-" * 80)
                
            except json.JSONDecodeError as e:
                log.append(f"Error processing line {code_line}: {str(e)}")
                continue

        # Step 3: Structure the output
        structured_output = {
            "original_code": original_code,
            "package_usage": original_code_lines,
            "error_versions": errors
        }

        # Save the structured output to a file
        output_dir = os.path.join(self.workspace, 'sklearn_pandas_errors')
        os.makedirs(output_dir, exist_ok=True)

        queries.update(structured_output)
        with open(os.path.join(output_dir, f'{model_type}_dseval_library_errors_v2.jsonl'), 'a', encoding='utf-8') as jsonl_file:
            jsonl_file.write(json.dumps(queries) + '\n')

        log_file = os.path.join(os.path.join(individual_workspace, model_type), f'processing_log_{queries["id"]}.txt')
        os.makedirs(os.path.join(individual_workspace, model_type), exist_ok=True)
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log))

        return structured_output, '\n'.join(log)
