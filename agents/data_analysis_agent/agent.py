import os
import re
import json

from tenacity import RetryError
from tqdm import tqdm

from agents.generic_agent import GenericAgent
from agents.openai_chatComplete import completion_with_backoff
from agents.utils import fill_in_placeholders, get_error_message, is_run_code_success, run_code
from agents.utils import print_filesys_struture
from agents.utils import change_directory


def parse_output_string(output_str):
    """
    Parses the output string format and extracts key-value pairs.

    Args:
        output_str: The output string in the format "@key[value]\n@key[value]...".

    Returns:
        A dictionary where keys are the extracted keys and values are the extracted values.
    """
    output_dict = {}
    lines = output_str.strip().split('\n')
    for line in lines:
        match = re.match(r'@(\w+)\[([\d.]+)\]', line)
        if match:
            key = match.group(1)
            value = match.group(2)
            output_dict[key] = value
    return output_dict


def parse_ground_truth_list(ground_truth_list):
    """
    Parses the ground truth list format and extracts key-value pairs.

    Args:
        ground_truth_list: The ground truth list of lists in the format [["key", "value"], ["key", "value"], ...].

    Returns:
        A dictionary where keys are the extracted keys and values are the extracted values.
    """
    gt_dict = {}
    for item in ground_truth_list:
        if len(item) == 2:
            key = item[0]
            value = item[1]
            gt_dict[key] = value
    return gt_dict


def calculate_accuracy(output_str, ground_truth_list, tolerance=1e-6):
    """
    Calculates the accuracy between the output string and the ground truth list.

    Args:
        output_str: The output string.
        ground_truth_list: The ground truth list of lists.
        tolerance: The tolerance for comparing float values (default 1e-6).

    Returns:
        The accuracy as a float between 0 and 1.
    """
    output_dict = parse_output_string(output_str)
    gt_dict = parse_ground_truth_list(ground_truth_list)

    correct_matches = 0
    total_pairs = len(gt_dict)

    if total_pairs == 0:
        return 1.0 if len(output_dict) == 0 else 0.0 # Handle empty GT case

    for key, gt_value in gt_dict.items():
        if key in output_dict:
            output_value = output_dict[key]
            try:
                gt_value_float = float(gt_value)
                output_value_float = float(output_value)
                if abs(gt_value_float - output_value_float) <= tolerance: # Compare as floats with tolerance
                    correct_matches += 1
            except ValueError:
                if gt_value == output_value: # If not float, compare as strings
                    correct_matches += 1

    accuracy = correct_matches / total_pairs if total_pairs > 0 else 0.0
    return accuracy


class DataAnalysisAgent(GenericAgent):
    def __init__(self, workspace, **kwargs):
        super().__init__(workspace, **kwargs)
        self.chat_history = []
        self.query = kwargs.get('query', '')
        self.data_information = kwargs.get('data_information', None)

    def generate(self, user_prompt, model_type, file_name, backend='THU'):

        workspace_structure = print_filesys_struture(self.workspace)
        
        information = {
            'workspace_structure': workspace_structure,
            'file_name': file_name,
            'query': user_prompt
        }


        messages = []
        messages.append({"role": "system", "content": fill_in_placeholders(self.prompts['system'], information)})
        messages.append({"role": "user", "content": fill_in_placeholders(self.prompts['user'], information)})

        self.chat_history = self.chat_history + messages
        return completion_with_backoff(self.chat_history, model_type, backend=backend)
        # return completion_with_backoff(messages, model_type)

    def generate_rubber_duck(self, user_prompt, model_type, code, backend='THU'):
        workspace_structure = print_filesys_struture(self.workspace)

        information = {
            'workspace_structure': workspace_structure,
            'code': code,
            'query': user_prompt,
        }

        messages = []
        messages.append({"role": "system", "content": fill_in_placeholders(self.prompts['debug_system'], information)})
        messages.append({"role": "user", "content": fill_in_placeholders(self.prompts['debug_user'], information)})

        # self.chat_history = self.chat_history + messages
        return completion_with_backoff(messages, model_type, backend)

    def get_code(self, response):

        all_python_code_blocks_pattern = re.compile(r'```python\s*([\s\S]+?)\s*```', re.MULTILINE)


        all_code_blocks = all_python_code_blocks_pattern.findall(response)
        all_code_blocks_combined = '\n'.join(all_code_blocks)
        return all_code_blocks_combined

    def get_code2(self, response,file_name):

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

    def run(self, queries, model_type, file_name, individual_workspace):
        log = []
        code = []
        
        if queries:
            for index, query in enumerate([queries], 1):
                log.append(f"\n--- Processing Query {index} ---")
                log.append(f"Question ID: {query['id']}")
                log.append(f"Question: {query['question']}")
                log.append(f"Constraints: {query['constraints']}")
                log.append(f"Data File: {query['file_name']}")
                log.append(f"Expected Format: {query['format']}")
                log.append(f"Ground Truth: {query['answers']}")

                prompt = f"""Question ID: {query['id']}
Question: {query['question']}
                
Constraints: {query['constraints']}

Data File Name: {query['file_name']}
                
Format: {query['format']}

Correct answer: {query['answers']}. Make sure your analysis results are identical with the annotated ground truth.
                """

                log.append("\nGenerating code...")
                result = self.generate(prompt, model_type=model_type, file_name=file_name)
                generated_code = self.get_code(result)
                code.append(generated_code)
                
                log.append(f"Generated code for Query {index}:")
                log.append(generated_code)
                log.append("\n" + "-"*50)
        else:
            log.append("Processing single query...")
            log.append(f"Query: {self.query}")
            
            result = self.generate(self.query, model_type=model_type, file_name=file_name)
            generated_code = self.get_code(result)
            code = generated_code
            
            log.append("\nGenerated code:")
            log.append(generated_code)

        '''structured_output = {
            "weak_code_analysis": code
        }
        queries.update(structured_output)

        # Save the structured output to a file
        output_dir = os.path.join(self.workspace, 'sklearn_pandas_errors')
        os.makedirs(output_dir, exist_ok=True)

        with open(os.path.join(output_dir, f'{model_type}_weak_direct_analysis.jsonl'), 'a') as jsonl_file:
            jsonl_file.write(json.dumps(queries) + '\n')'''

        # Join the log list into a single string
        log_string = "\n".join(log)
        return log_string, ''.join(code)

    def debug_run(self, queries, model_type, file_name, error_message, buggy_code):
        log = []
        
        log.append("=== Debug Run Initiated ===")
        log.append(f"Model Type: {model_type}")
        log.append(f"File Name: {file_name}")
        
        log.append("\n--- Previous Error Information ---")
        log.append("Error Message:")
        log.append(error_message)
        
        # log.append("\nBuggy Code:")
        # log.append(buggy_code)
        
        if queries:
            debug_prompt = f"""The previous code generated for the data analysis task resulted in errors. 
            Here's the error information:
            
            {error_message}
            
            Here's the previous code that needs to be fixed:
            
            {buggy_code}
            
            
            Please review the error information and generate corrected code that:
            1. Fixes all identified errors
            2. Maintains the original functionality
            3. Follows the output format requirements
            4. Ensures results match the ground truth
            """
        else:
            debug_prompt = f"""The previous code generated for the data analysis task resulted in errors. 
            Here's the error information:
            
            {error_message}
            
            Here's the previous code that needs to be fixed:
            
            {buggy_code}
            
            Please review the error information and generate corrected code.
            """

        '''Question
        ID: {queries['id']}
        Question: {queries['question']}
        Constraints: {queries['constraints']}
        Data
        File: {queries['file_name']}
        Expected
        Format: {queries['format']}
        Ground
        Truth: {queries['answers']}'''

        log.append("\n--- Generating Corrected Code ---")
        result = self.generate(debug_prompt, model_type=model_type, file_name=file_name)
        corrected_code = self.get_code(result)
        
        log.append("Corrected code generated:")
        log.append(corrected_code)
        
        log.append("\n=== Debug Run Completed ===")

        return '\n'.join(log), corrected_code

    def weak_direct_analysis(self, queries, model_type, file_name, individual_workspace):
        log = []
        structured_output = {"error_versions": []}

        query = queries

        log.append(f"\n--- Processing Query {query['id']} ---")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")
        # log.append(f"Constraints: {query['constraints']}")
        # log.append(f"Data File: {query['file_name']}")
        # log.append(f"Expected Format: {query['format']}")
        # log.append(f"Ground Truth: {query['answers']}")

        # prompt_dabench = f"""Question ID: {query['id']}
# Question: {query['question']}

# Constraints: {query['constraints']}

# Data File Name: {query['file_name']}

# Format: {query['format']}

# Correct answer: {query['answers']}. Make sure your analysis results are identical with the annotated ground truth.
#                 """

        prompt = f"""Here is the query:

{query['question']}


If the query requires data manipulation from a csv file, process the data from the csv file and complete the query in one piece of code.
"""

        for i in tqdm(range(5)):
            log.append("\nGenerating code...")
            print(f"\nweak llm generating turn No.{i}")
            result = self.generate(prompt, model_type=model_type, file_name=file_name)
            generated_code = self.get_code(result)

            log.append(f"Generated code for run No.{i}:")
            log.append(generated_code)
            log.append("\n" + "-" * 50)

            single_output = {
                "modified_code": generated_code
            }
            structured_output['error_versions'].append(single_output)

        queries.update(structured_output)

        # Save the structured output to a file
        output_dir = os.path.join(self.workspace, 'sklearn_pandas_errors')
        os.makedirs(output_dir, exist_ok=True)

        with open(os.path.join(output_dir, f'{model_type}_dseval_weak_direct_analysis.jsonl'), 'a') as jsonl_file:
            jsonl_file.write(json.dumps(queries) + '\n')
            print("Analysis saved.")

        # Join the log list into a single string
        log_string = "\n".join(log)
        return log_string, queries

    def direct_analysis_with_rubber_duck_debug(self, queries, model_type, file_name, individual_workspace):
        log = []
        self.chat_history = []
        structured_output = {"analysis_attempts": []}

        query = queries

        log.append(f"\n--- Processing Query {query['id']} ---")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")
        log.append(f"Constraints: {query['constraints']}")
        log.append(f"Data File: {query['file_name']}")
        log.append(f"Expected Format: {query['format']}")
        # log.append(f"Ground Truth: {query['answers']}")

        prompt_dabench = f"""Question ID: {query['id']}
# Question: {query['question']}

# Constraints: {query['constraints']}

# Data File Name: {query['file_name']}

# Format: {query['format']}
                 """


        log.append("\nGenerating code...")
        print("\ngenerating first analysis code")

        result = self.generate(prompt_dabench, model_type=model_type, file_name=file_name)
        generated_code = self.get_code(result)

        log.append(generated_code)
        log.append("\n" + "-" * 50)

        retries = 0
        MAX_RETRIES = 5
        success = False

        while retries < MAX_RETRIES and not success:
            try:
                log.append(
                    f"\n--- Processing LLM code (Attempt {retries + 1}) ---")

                modified_code = generated_code
                log.append("\n...............Verifying code with LLM...............")
                print(
                    f"\n...............Verifying generated code (Attempt {retries + 1})...............")

                result = self.generate_rubber_duck(prompt_dabench, model_type=model_type, code=modified_code, backend='THU')

                # Locate the first curly brace to the last one for extracting the JSON object
                start_index = result.rfind('{')
                end_index = result.rfind('}')

                if start_index == -1 or end_index == -1:
                    raise ValueError("No valid JSON found in the LLM response.")

                # Extract and parse JSON
                json_str = result[start_index:end_index + 1]
                # cleaned_json_str = clean_json_string(json_str)
                rubber_duck_debug_info = json.loads(json_str)

                debug_info_without_cause = {key: value for key, value in rubber_duck_debug_info.items() if key not in ['cause_line']}
                debug_info_without_effect = {key: value for key, value in rubber_duck_debug_info.items() if key not in ['effect_line']}
                debug_info_without_message = {key: value for key, value in rubber_duck_debug_info.items() if key not in ['error_message']}


                success = True

            except (ValueError, json.JSONDecodeError, KeyError, TypeError, RetryError) as e:
                retries += 1
                rubber_duck_debug_info = None
                log.append(f"Error encountered in Attempt {retries}: {str(e)}")
                print(f"Error in Attempt {retries}: {str(e)}")

        iter_count = 1
        for i in range(iter_count):
            prompt_refine = f'''After retrospecting the code you just generated, an LLM debugger has provided the following debugging information for your reference: {rubber_duck_debug_info}. This information tells you the cause line of potential error, the effect line where the Python interpreter would throw the error, as well as error message. Improve and refine your previous code to better accomplish the question.'''
            prompt_no_cause = f'''After retrospecting the code you just generated, an LLM debugger has provided the following debugging information for your reference: {debug_info_without_cause}. This information tells you the cause line of potential error, the effect line where the Python interpreter would throw the error, as well as error message. Improve and refine your previous code to better accomplish the question.'''
            prompt_no_effect = f'''After retrospecting the code you just generated, an LLM debugger has provided the following debugging information for your reference: {debug_info_without_effect}. This information tells you the cause line of potential error, the effect line where the Python interpreter would throw the error, as well as error message. Improve and refine your previous code to better accomplish the question.'''
            prompt_no_message = f'''After retrospecting the code you just generated, an LLM debugger has provided the following debugging information for your reference: {debug_info_without_message}. This information tells you the cause line of potential error, the effect line where the Python interpreter would throw the error, as well as error message. Improve and refine your previous code to better accomplish the question.'''

            print("\ngenerating refined code")

            # result = self.generate(prompt_refine, model_type=model_type, file_name=file_name)

            print("\ngenerating refined code no cause")
            result_no_cause = self.generate(prompt_no_cause, model_type=model_type, file_name=file_name)
            print("\ngenerating refined code no effect")
            result_no_effect = self.generate(prompt_no_effect, model_type=model_type, file_name=file_name)
            print("\ngenerating refined code no message")
            result_no_message = self.generate(prompt_no_message, model_type=model_type, file_name=file_name)

            # refined_code = self.get_code(result)

            refined_code_no_cause = self.get_code(result_no_cause)
            refined_code_no_effect = self.get_code(result_no_effect)
            refined_code_no_message = self.get_code(result_no_message)

            if i == iter_count - 1:
                continue
            else:
                log.append("\n...............Verifying code with LLM...............")
                print(
                    f"\n...............Iteratively Verifying generated code (Attempt {i})...............")

                result = self.generate_rubber_duck(prompt_dabench, model_type=model_type, code=refined_code, backend='THU')

                # Locate the first curly brace to the last one for extracting the JSON object
                start_index = result.rfind('{')
                end_index = result.rfind('}')

                if start_index == -1 or end_index == -1:
                    raise ValueError("No valid JSON found in the LLM response.")

                # Extract and parse JSON
                json_str = result[start_index:end_index + 1]
                # cleaned_json_str = clean_json_string(json_str)
                rubber_duck_debug_info = json.loads(json_str)

                debug_info_without_cause = {key: value for key, value in rubber_duck_debug_info.items() if
                                            key not in ['cause_line']}
                debug_info_without_effect = {key: value for key, value in rubber_duck_debug_info.items() if
                                             key not in ['effect_line']}
                debug_info_without_message = {key: value for key, value in rubber_duck_debug_info.items() if
                                              key not in ['error_message']}


        # refined_code = "import matplotlib\nmatplotlib.use('agg')\n" + refined_code.replace("plt.show()", "")

        refined_code_no_cause = "import matplotlib\nmatplotlib.use('agg')\n" + refined_code_no_cause.replace("plt.show()", "")
        refined_code_no_effect = "import matplotlib\nmatplotlib.use('agg')\n" + refined_code_no_effect.replace("plt.show()", "")
        refined_code_no_message = "import matplotlib\nmatplotlib.use('agg')\n" + refined_code_no_message.replace("plt.show()", "")

        # generated_code = "import matplotlib\nmatplotlib.use('agg')\n" + generated_code.replace("plt.show()", "")

        '''code_file = f'analysis_attempt.py'
        error_file_path = os.path.join(individual_workspace, code_file)
        with open(error_file_path, 'w',encoding='utf-8') as f:
            # f.write(generated_code)
            f.write(refined_code)'''

        code_file_no_cause = f'analysis_attempt_no_cause.py'
        error_file_path = os.path.join(individual_workspace, code_file_no_cause)
        with open(error_file_path, 'w', encoding='utf-8') as f:
            # f.write(generated_code)
            f.write(refined_code_no_cause)

        code_file_no_effect = f'analysis_attempt_no_effect.py'
        error_file_path = os.path.join(individual_workspace, code_file_no_effect)
        with open(error_file_path, 'w', encoding='utf-8') as f:
            # f.write(generated_code)
            f.write(refined_code_no_effect)

        code_file_no_message = f'analysis_attempt_no_message.py'
        error_file_path = os.path.join(individual_workspace, code_file_no_message)
        with open(error_file_path, 'w', encoding='utf-8') as f:
            # f.write(generated_code)
            f.write(refined_code_no_message)

        # Capture the execution output
        try:
            # Run the code and capture output
            # output = run_code(individual_workspace, code_file)

            output_no_cause = run_code(individual_workspace, code_file_no_cause)
            output_no_effect = run_code(individual_workspace, code_file_no_effect)
            output_no_message = run_code(individual_workspace, code_file_no_message)

        except Exception as e:
            output = None
            '''output_no_cause = None
            output_no_effect = None
            output_no_message = None'''

            error_msg = f"Error executing {code_file_no_cause}: {str(e)}"
            log.append(f"\nError: {error_msg}")
            error_msg = f"Error executing {code_file_no_effect}: {str(e)}"
            log.append(f"\nError: {error_msg}")
            error_msg = f"Error executing {code_file_no_message}: {str(e)}"
            log.append(f"\nError: {error_msg}")

        # print(output)
        ground_truth = query['answers']

        # accuracy_score = calculate_accuracy(output, ground_truth)
        # print(f"\n*******************Accuracy: {accuracy_score}*******************")

        accuracy_score_no_cause = calculate_accuracy(output_no_cause, ground_truth)
        print(f"\n*******************Accuracy No Cause: {accuracy_score_no_cause}*******************")
        accuracy_score_no_effect = calculate_accuracy(output_no_effect, ground_truth)
        print(f"\n*******************Accuracy No Effect: {accuracy_score_no_effect}*******************")
        accuracy_score_no_message = calculate_accuracy(output_no_message, ground_truth)
        print(f"\n*******************Accuracy No Message: {accuracy_score_no_message}*******************")

        single_output = {
            "task_code": [refined_code_no_cause, refined_code_no_effect, refined_code_no_message],
            # "task_code": generated_code,
            # "task_code": refined_code,
            "task_result": [output_no_cause, output_no_effect, output_no_message],
            # "task_result": output,
            # "accuracy": accuracy_score,
            "accuracy_no_cause": accuracy_score_no_cause,
            "accuracy_no_effect": accuracy_score_no_effect,
            "accuracy_no_message": accuracy_score_no_message
        }
        structured_output['analysis_attempts'].append(single_output)

        queries.update(structured_output)

        # Save the structured output to a file
        output_dir = os.path.join(self.workspace, 'dabench_quantitative_experiment')
        os.makedirs(output_dir, exist_ok=True)

        with open(os.path.join(output_dir, f'{model_type.replace("Qwen/", "")}_dabench_quantitative_experiment_ablation_2.jsonl'), 'a') as jsonl_file:
            jsonl_file.write(json.dumps(queries) + '\n')

        # Join the log list into a single string
        log_string = "\n".join(log)
        return log_string, queries