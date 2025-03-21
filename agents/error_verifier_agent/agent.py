import json
import os
import re
import shutil
import traceback

from tenacity import RetryError
from tqdm import tqdm
from agents.generic_agent import GenericAgent
from agents.openai_chatComplete import completion_with_backoff
from agents.utils import fill_in_placeholders, get_error_message, is_run_code_success, run_code
from agents.utils import print_filesys_struture
from agents.utils import change_directory


def extract_traceback(error_str):
    """
    从错误信息字符串中提取 'Traceback (most recent call last):' 及其之后的报错信息。
    """
    pattern = r"Traceback \(most recent call last\):.*"
    match = re.search(pattern, error_str, re.DOTALL)
    if match:
        return match.group(0).split('\n')[-2]
    else:
        return None


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


def get_code(response):
    all_python_code_blocks_pattern = re.compile(r'```python\s*([\s\S]+?)\s*```', re.MULTILINE)
    all_code_blocks = all_python_code_blocks_pattern.findall(response)
    all_code_blocks_combined = '\n'.join(all_code_blocks)
    return all_code_blocks_combined


def _format_verification_result(result, code):
    """格式化验证结果为标准格式"""
    try:
        # 尝试从结果中提取 JSON 部分
        start_index = result.find('{')
        end_index = result.rfind('}')
        if start_index == -1 or end_index == -1:
            raise ValueError("No valid JSON found in the result")

        json_str = result[start_index:end_index + 1]
        result_dict = json.loads(json_str)

        # 构建标准格式的结果
        formatted_result = {
            "result": {
                "has_errors": result_dict.get("is_error", "false").lower() == "true",
                "errors": []
            }
        }

        # 处理每个错误说明
        for error in result_dict.get("error_explanation", []):
            error_detail = {
                "error_type": error.get("error_type", "Unknown"),
                "error_message": error.get("explanation", ''),
                "expected_outcome": error.get("expected_outcome", ''),
                "suggestions": error.get("suggestions", '')
            }
            formatted_result['result']['errors'].append(error_detail)

        # 如果没有错误信息但标记为有错误，添加默认信息
        if formatted_result['result']['has_errors'] and not formatted_result['result']['errors']:
            formatted_result['result']['errors'].append({
                "error_type": "Unknown",
                "error_message": "Unspecified error detected",
                "expected_outcome": '',
                "suggestions": "Please review and correct the code"
            })

        return formatted_result

    except Exception as e:
        # 如果解析失败，返回错误格式的结果
        return {
            'result': {
                'has_errors': True,
                'error_type': 'ParseError',
                'error_message': f'Failed to parse verification result: {str(e)}',
                'suggestions': 'Please check the code and verification output format',
                'original_result': result
            }
        }


class ErrorVerifierAgent(GenericAgent):
    def __init__(self, workspace, **kwargs):
        super().__init__(workspace, **kwargs)
        self.chat_history = []
        self.query = kwargs.get('query', '')
        self.data_information = kwargs.get('data_information', None)

    def generate(self, user_prompt, model_type, code, backend='OpenRouter'):
        workspace_structure = print_filesys_struture(self.workspace)

        information = {
            'workspace_structure': workspace_structure,
            'code': code,
            'query': user_prompt,
        }

        messages = []
        messages.append({"role": "system", "content": fill_in_placeholders(self.prompts['system'], information)})
        messages.append({"role": "user", "content": fill_in_placeholders(self.prompts['user'], information)})

        self.chat_history = self.chat_history + messages
        return completion_with_backoff(messages, model_type, backend)

    def run(self, queries, model_type, code):
        log = []
        verifier_results = []
        query = queries

        concepts = query['concepts']
        error_code_directory = os.path.join(self.workspace, 'error_code_dir/')
        jsonl_file_path = os.path.join(error_code_directory, 'logical_error_data.jsonl')
        error_code_content = []

        # Read from the jsonl file
        with open(jsonl_file_path, 'r') as jsonl_file:
            file_content = jsonl_file.read()

        # Split the content by assuming each JSON object ends with '}\n'
        json_objects = file_content.strip().split('\n}\n')

        for obj_str in json_objects:
            # Ensure each object has proper JSON format by adding the closing brace back
            # obj_str = obj_str + '}'
            result_dict = json.loads(obj_str)

            # Loop through each concept in the JSON object and extract error codes
            for concept, entries in result_dict.items():
                for entry in entries:
                    error_code_each = entry.get('error_code', '')
                    error_code_content.append(error_code_each)

        '''for concept in concepts:
            for i in range(3):
                error_code_list.append(os.path.join(error_code_directory, f"logical_error_{concept}_{i}_injected.py"))

        for idx, error_code_dir in enumerate(error_code_list):
            with open(error_code_dir, 'r') as file:
                error_code_each = file.read()
                error_code_content.append(error_code_each)'''

        for error_code_each in tqdm(error_code_content):
            information = {
                'code': error_code_each,
            }

            messages = []
            messages.append({"role": "system", "content": ''})
            messages.append({"role": "user", "content": fill_in_placeholders(self.prompts['error'], information)})

            error_erase_result = completion_with_backoff(messages, model_type)
            error_erase_code = get_code(error_erase_result)

            # 记录日志
            log.append(f"\n------------------------------------- Processing Query -------------------------------------")
            log.append(f"Question ID: {query['id']}")
            log.append(f"Question: {query['question']}")
            log.append(f"Constraints: {query['constraints']}")
            log.append(f"Data File: {query['file_name']}")
            log.append(f"Expected Format: {query['format']}")
            log.append(f"Ground Truth: {query['answers']}")
            log.append(f"\n\nError Erased Code:\n\n {error_erase_code}\n")

            prompt = f"""Question ID: {query['id']}
    Question: {query['question']}

    Constraints: {query['constraints']}

    Data File Name: {query['file_name']}

    Format: {query['format']}

    Correct answer: {query['answers']}
                    """

            log.append("\n...............Verifying code...............")
            result = self.generate(prompt, model_type=model_type, code=error_erase_code)

            # 解析验证结果并格式化
            verification_result = _format_verification_result(result, error_erase_code)
            verifier_results.append(verification_result)

            # 记录验证结果
            log.append(f"\nVerifier Result:\n{json.dumps(verification_result, indent=2)}\n")

        # 将结果写入文件
        with open(os.path.join(error_code_directory, 'logical_error_verification.jsonl'), 'w') as jsonl_file:
            for result in verifier_results:
                jsonl_file.write(json.dumps(result) + '\n')

        log_string = "\n".join(log)
        return log_string, verifier_results

    def run_with_other_agent(self, queries, model_type, from_prev_agent, individual_workspace):
        log = []
        # verifier_results = []
        query = queries

        concepts = query['concepts']
        error_code_directory = os.path.join(self.workspace, 'error_code_dir/')
        jsonl_file_path = os.path.join(error_code_directory, 'logical_error_data.jsonl')
        error_code_content = []

        if isinstance(from_prev_agent, dict):
            error_erase_code = from_prev_agent['result']
        elif isinstance(from_prev_agent, tuple):
            error_erase_code = from_prev_agent[1]
        else:
            raise TypeError("Unsupported information type between agents")

        '''information = {
            'code': error_code_each,
        }

        messages = []
        messages.append({"role": "system", "content": ''})
        messages.append({"role": "user", "content": fill_in_placeholders(self.prompts['error'], information)})

        error_erase_result = completion_with_backoff(messages, model_type)
        error_erase_code = get_code(error_erase_result)'''

        # 记录日志
        log.append(f"\n------------------------------------- Processing Query -------------------------------------")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")
        log.append(f"Constraints: {query['constraints']}")
        log.append(f"Data File: {query['file_name']}")
        log.append(f"Expected Format: {query['format']}")
        log.append(f"Ground Truth: {query['answers']}")
        log.append(f"\n\nError Erased Code:\n\n {error_erase_code}\n")

        prompt = f"""Question ID: {query['id']}
    Question: {query['question']}

    Constraints: {query['constraints']}

    Data File Name: {query['file_name']}

    Format: {query['format']}

    Correct answer: {query['answers']}
                    """

        log.append("\n...............Verifying code...............")
        result = self.generate(prompt, model_type=model_type, code=error_erase_code)

        # 解析验证结果并格式化
        verification_result = _format_verification_result(result, error_erase_code)
        # verifier_results.append(verification_result)

        # 记录验证结果
        log.append(f"\nVerifier Result:\n{json.dumps(verification_result, indent=2)}\n")

        # 将结果写入文件
        # with open(os.path.join(error_code_directory, 'logical_error_verification.jsonl'), 'w') as jsonl_file:
        #     for result in verifier_results:
        #         jsonl_file.write(json.dumps(result) + '\n')

        log_string = "\n".join(log)
        return log_string, verification_result

    def eval(self, queries, model_type, eval_folder):
        log = []
        query = queries

        error_hidden_code = query['error_hidden_code']
        ground_truth_dict = {
            "error_type": query['error_type'],
            "explanation": query['explanation'],
            "expected_outcome": query['expected_outcome']
        }

        # 记录日志
        log.append(f"\n------------------------------------- Processing Query -------------------------------------")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")
        log.append(f"Constraints: {query['constraints']}")
        log.append(f"Data File: {query['file_name']}")
        log.append(f"Expected Format: {query['format']}")
        log.append(f"Ground Truth: {query['answers']}")
        log.append(f"\n\nError Hidden Code:\n\n {error_hidden_code}\n")

        prompt = f"""Question ID: {query['id']}
    Question: {query['question']}

    Constraints: {query['constraints']}

    Data File Name: {query['file_name']}

    Format: {query['format']}

    Correct answer: {query['answers']}
                    """

        log.append("\n...............Verifying code...............")
        print(f"\n...............Verifying query {query['id']}...............")
        result = self.generate(prompt, model_type=model_type, code=error_hidden_code)

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

        information = {
            'ground_truth': ground_truth_dict,
            'eval_dict': result_dict
        }

        messages = []
        messages.append({"role": "system", "content": ''})
        messages.append({"role": "user", "content": fill_in_placeholders(self.prompts['eval'], information)})

        print(f"\n...............Evaluating query {query['id']}...............")
        eval_result = completion_with_backoff(messages, 'gpt-4o')

        eval_result_dict = {
            'id': query['id'],
            'eval_result': eval_result
        }

        result_dict['eval_result'] = eval_result

        # 记录验证结果
        log.append(f"\nVerifier Result:\n{json.dumps(result_dict, indent=2)}\n")

        # 将结果写入文件
        with open(os.path.join(eval_folder, f'{model_type.replace("Qwen/","")}_method_eval_result.jsonl'), 'a') as jsonl_file:
            jsonl_file.write(json.dumps(eval_result_dict) + '\n')

        log_string = "\n".join(log)
        return log_string, result_dict

    def rubber_duck_eval(self, queries, model_type, eval_folder, individual_workspace):
        log = []
        query = queries

        error_versions = query['error_versions']
        if not error_versions:
            raise ValueError("No error versions found in the query.")

        # 记录日志
        log.append(f"\n------------------------------------- Processing Query -------------------------------------")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")
        # log.append(f"Constraints: {query['constraints']}")
        # log.append(f"Data File: {query['file_name']}")
        # log.append(f"Expected Format: {query['format']}")
         #log.append(f"Ground Truth: {query['answers']}")

        prompt = f"""Question ID: {query['id']}
    Question: {query['question']}
                    """

        MAX_RETRIES = 5
        eval_results = []
        print(f"\n**********Verifying ID: {query['id']}**********")
        try:
            for idx, error_version in enumerate(error_versions):
                retries = 0  # 重试计数器
                success = False  # 标记是否成功处理

                while retries < MAX_RETRIES and not success:
                    try:
                        log.append(
                            f"\n--- Processing Error Version {idx + 1}/{len(error_versions)} (Attempt {retries + 1}) ---")

                        modified_code = error_version['modified_code']
                        error_message = extract_traceback(error_version['execution_output'])
                        if error_message is not None:
                            ground_truth = {
                                "cause_error_line": error_version["cause_error_line"],
                                "effect_error_line": error_version["effect_error_line"],
                                "execution_output": error_message
                            }
                            # Log error version details
                            log.append(f"\nModified Code:\n{modified_code}")
                            log.append(f"Ground Truth: {json.dumps(ground_truth, indent=2)}")

                            log.append("\n...............Verifying code with LLM...............")
                            print(
                                f"\n...............Verifying error version {idx + 1}/{len(error_versions)} (Attempt {retries + 1})...............")

                            result = self.generate(prompt, model_type=model_type, code=modified_code, backend='THU')

                            # Locate the first curly brace to the last one for extracting the JSON object
                            start_index = result.rfind('{')
                            end_index = result.rfind('}')

                            if start_index == -1 or end_index == -1:
                                raise ValueError("No valid JSON found in the LLM response.")

                            # Extract and parse JSON
                            json_str = result[start_index:end_index + 1]
                            # cleaned_json_str = clean_json_string(json_str)
                            llm_output = json.loads(json_str)

                            information = {
                                'ground_truth': ground_truth,
                                'eval_dict': llm_output
                            }

                            messages = []
                            messages.append({"role": "system", "content": ''})
                            messages.append(
                                {"role": "user", "content": fill_in_placeholders(self.prompts['eval'], information)})

                            print(
                                f"\n...............Evaluating error version {idx + 1}/{len(error_versions)} (Attempt {retries + 1})...............")
                            eval_completion = completion_with_backoff(messages, 'gpt-4o', backend='THU')

                            start_index = eval_completion.rfind('{')
                            end_index = eval_completion.rfind('}')
                            json_str = eval_completion[start_index:end_index + 1]
                            eval_result = json.loads(json_str)
                            eval_results.append(eval_result)

                            # Log comparison result
                            log.append(f"LLM Output: {json.dumps(result, indent=2)}")
                            print(f"LLM Output: {json.dumps(result, indent=2)}")
                            log.append(f"JSON Output: {json.dumps(llm_output, indent=2)}")
                            log.append(f"Eval Result: {eval_result}")

                            # 如果成功处理，设置 success 为 True
                            success = True

                        else:
                            break  # 如果没有错误信息，跳过该 error_version

                    except (ValueError, json.JSONDecodeError, KeyError, TypeError, RetryError) as e:
                        retries += 1
                        log.append(f"Error encountered in Attempt {retries}: {str(e)}")
                        print(f"Error in Attempt {retries}: {str(e)}")
                        # traceback.print_exc()

                # 如果重试次数用尽仍未成功
                if not success:
                    log.append(f"Failed to process Error Version {idx + 1} after {MAX_RETRIES} attempts.")
                    print(f"Failed to process Error Version {idx + 1} after {MAX_RETRIES} attempts.")


        except (ValueError, json.JSONDecodeError, KeyError) as e:
            print(f"Exception occurred: {str(e)}")

        finally:
            # Save all results to a file
            with open(os.path.join(eval_folder, f'eval_{model_type.replace("deepseek/", "").replace(":", "_")}_rubber_duck_case_study_on_bench_v3.jsonl'), 'a') as jsonl_file:
                eval_result_dict = {
                    'id': query['id'],
                    'eval_result': eval_results
                }
                jsonl_file.write(json.dumps(eval_result_dict) + '\n')

        log_string = "\n".join(log)
        return log_string, eval_results

    def multi_rubber_duck_eval(self, queries, model_type, eval_folder, individual_workspace):
        log = []
        query = queries

        log.append(f"\n------------------------------------- Processing Query -------------------------------------")
        log.append(f"Question ID: {query['id']}")
        log.append(f"Question: {query['question']}")

        prompt = f"""Question ID: {query['id']}
            Question: {query['question']}
                            """

        MAX_RETRIES = 5
        eval_results = []  # Will store list of lists of single-error eval results
        print(f"\n**********Verifying ID: {query['id']}**********")
        try:
            retries = 0
            success = False
            error_message = []
            while retries < MAX_RETRIES and not success:
                try:
                    log.append(
                        f"\n--- Processing Error {query['id']} (Attempt {retries + 1}) ---")

                    modified_code = query['modified_code']
                    for exec_o in query['execution_outputs']:
                        error_message.append(extract_traceback(exec_o))
                    if error_message is not None:
                        ground_truth_info = []
                        for cause_e_l, effect_e_l, error_m in zip(query["cause_error_lines"], query["effect_error_lines"], error_message):
                            ground_truth_info.append({  # Store ground truth lists
                                "cause_error_line": cause_e_l,
                                "effect_error_line": effect_e_l,
                                "error_message": error_m
                            })

                        log.append(f"\nModified Code:\n{modified_code}")
                        log.append(f"Ground Truth Lists: {json.dumps(ground_truth_info, indent=2)}")

                        log.append("\n...............Verifying code with LLM...............")
                        print(
                            f"\n...............Verifying error {query['id']} (Attempt {retries + 1})...............")

                        result = self.generate(prompt, model_type=model_type, code=modified_code, backend='THU')

                        # start_index = result.rfind('[')  # Expecting JSON list now for multi-bug detection
                        # end_index = result.rfind(']')

                        match = re.search(r"\[\s*\{.*?\}\s*\]", result, re.DOTALL)

                        if match:
                            json_list_str = match.group(0)
                        else:
                            json_list_str = None

                        # if start_index == -1 or end_index == -1:
                            # raise ValueError("No valid JSON List found in the LLM response (Error Detection).")

                        llm_output_errors = json.loads(json_list_str)

                        # json_list_str = result[start_index:end_index + 1]
                        # cleaned_json_list_str = clean_json_string(json_list_str)
                        # llm_output_errors = json.loads(json_list_str)  # Now LLM output is expected to be a list of errors

                        log.append(f"LLM Output (Error Detection): {json.dumps(llm_output_errors, indent=2)}")

                        single_error_eval_results = []  # List to store eval results for each detected error
                        for llm_error_index, llm_error in enumerate(
                                llm_output_errors):  # Loop through each detected error
                            information_single_error = {
                                'ground_truth': ground_truth_info,
                                'llm_output_error': llm_error  # Pass the single LLM detected error
                            }

                            messages = []
                            messages.append({"role": "system", "content": ''})
                            messages.append(
                                {"role": "user", "content": fill_in_placeholders(self.prompts['eval'],
                                                                                 information_single_error)})  # Use single-error eval prompt

                            print(
                                f"\n...............Evaluating detected error {llm_error_index + 1}/{len(llm_output_errors)} of error version {query['id']} (Attempt {retries + 1})...............")
                            eval_result_str = completion_with_backoff(messages,
                                                                      'gpt-4o', backend='THU')  # Get single-error eval result

                            start_index = eval_result_str.rfind('{')
                            end_index = eval_result_str.rfind('}')
                            json_str = eval_result_str[start_index:end_index + 1]
                            single_error_eval_result = json.loads(json_str)  # Parse single-error eval JSON
                            single_error_eval_results.append(single_error_eval_result)  # Append single-error result

                            log.append(
                                f"  Error {llm_error_index + 1} Eval Result: {json.dumps(single_error_eval_result, indent=2)}")

                        eval_results.append(
                            single_error_eval_results)  # Append list of single-error results for this error_version
                        success = True

                    else:
                        break

                except (ValueError, json.JSONDecodeError, KeyError) as e:
                    retries += 1
                    log.append(f"Error encountered in Attempt {retries}: {str(e)}")
                    print(f"Error in Attempt {retries}: {str(e)}")

            if not success:
                log.append(f"Failed to process Error Version {query['id']} after {MAX_RETRIES} attempts.")
                print(f"Failed to process Error Version {query['id']} after {MAX_RETRIES} attempts.")


        except (ValueError, json.JSONDecodeError, KeyError) as e:
            print(f"Exception occurred: {str(e)}")

        finally:
            with open(
                    os.path.join(eval_folder, f'eval_{model_type.replace("Qwen/", "").replace(":", "_")}_multi_rubber_duck_CoT_on_multi_bench_v2.jsonl'),
                    'a') as jsonl_file:
                eval_result_dict = {
                    'id': query['id'],
                    'eval_result': eval_results  # Now contains list of lists of single-error evaluations
                }
                jsonl_file.write(json.dumps(eval_result_dict) + '\n')

        log_string = "\n".join(log)
        return log_string, eval_results
