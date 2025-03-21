import pandas as pd
from tqdm import tqdm
import json
import os
import shutil
import subprocess
import sys
from agents.utils import change_directory
from datetime import datetime
from abc import ABC, abstractmethod
import ast
import copy  # 在文件顶部添加这个导入


# Output Handler Classes
class OutputHandler(ABC):
    @abstractmethod
    def handle(self, method_output, agent_name, method_name, individual_workspace, args):
        pass


class CodeOutputHandler(OutputHandler):
    def handle(self, method_output, agent_name, method_name, individual_workspace, args):
        log, code = method_output
        file_name = f'code_{agent_name}_{method_name}.py'
        with open(os.path.join(individual_workspace, file_name), 'w', encoding='utf-8') as f:
            f.write(code)
        return log, code, file_name


class AnalysisOutputHandler(OutputHandler):
    def handle(self, method_output, agent_name, model_type, individual_workspace, args):
        log, analysis_result = method_output
        file_name = f'analysis_{agent_name}_{model_type}.txt'
        model_dependent_directory = os.path.join(individual_workspace, model_type.replace(":", "_"))
        os.makedirs(model_dependent_directory, exist_ok=True)
        return log, str(analysis_result), file_name


class MaxDebugRetriesExceeded(Exception):
    """当达到最大调试重试次数时抛出的异常"""
    pass


class AgentEnvironment:
    def __init__(self, workspace, config):
        self.workspace = workspace
        self.config = config
        self.agents = {}
        self.data_store = {}
        self.instructions = None
        self.data_folder = config.get('data_folder', './InfiAgent_data/da-dev-tables')
        self.log_file = os.path.join(workspace, 'agent_workflow.log')
        self.output_handlers = {
            'code': CodeOutputHandler(),
            'analysis': AnalysisOutputHandler(),
        }
        self.cleared_log_files = set()  # 新增：用于跟踪已清除的日志文件

    # Agent Management
    def add_agent(self, agent_name, agent_class, **kwargs):
        self.agents[agent_name] = agent_class(self.workspace, **kwargs)

    # Data Processing Methods
    def process_instruction_file(self, input_file, data_ids=None, data_range=None):
        with open(input_file, 'r', encoding='utf-8') as f:
            instructions = [json.loads(line) for line in f]

        if data_ids:
            instructions = [inst for inst in instructions if inst['id'] in data_ids]
        elif data_range:
            start, end = data_range
            instructions = [inst for inst in instructions if start <= inst['id'] <= end]

        self.instructions = instructions

    def copy_data_files(self):
        workspace_list = []
        for instruction in self.instructions:
            d_id = instruction['id']
            individual_directory = os.path.join(self.workspace, f'example {d_id}')
            os.makedirs(individual_directory, exist_ok=True)
            workspace_list.append(individual_directory)

            if file_name := instruction.get('file_name'):
                src = os.path.join(self.data_folder, file_name)
                dst = os.path.join(individual_directory, file_name)
                if os.path.exists(src):
                    shutil.copy(src, dst)
                else:
                    print(f"Warning: File {file_name} not found in data folder.")

        return workspace_list

    # Execution and Logging Methods
    def execute_code(self, file_name, individual_workspace):
        with change_directory(individual_workspace):
            if not os.path.exists(file_name):
                return f"Error: File {file_name} not found in workspace."
            try:
                result = subprocess.run([sys.executable, file_name], capture_output=True, text=True)
                return result.stdout + result.stderr
            except Exception as e:
                return f"Error executing {file_name}: {str(e)}"

    def log_action(self, action, agent_name, model_type, code, log, individual_workspace):
        model_type = model_type.replace("Qwen/", "").replace("deepseek/", "").replace("google/", "").replace(":", "_")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"""
{'=' * 80}
TIMESTAMP: {timestamp}
ACTION: {action.upper()}
AGENT: {agent_name}
MODEL TYPE: {model_type}
WORKSPACE: {individual_workspace}
{'=' * 80}

LOG OUTPUT:
{log}

{'=' * 80}
"""
        model_dependent_directory = os.path.join(individual_workspace, model_type)
        os.makedirs(model_dependent_directory, exist_ok=True)
        individual_log_file = os.path.join(model_dependent_directory, f'{agent_name}_{model_type}_log.txt')

        # 如果是该文件的第一次写入，先清除内容
        if individual_log_file not in self.cleared_log_files:
            with open(individual_log_file, 'w') as f:
                pass  # 清空文件
            self.cleared_log_files.add(individual_log_file)

        # 追加写入新的日志
        with open(individual_log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        return log_entry

    def is_execution_successful(self, log):
        error_indicators = ['Traceback (most recent call last):', 'Incorrect Answer:', 'Error:']
        return not any(indicator in log for indicator in error_indicators)

    # Step Execution Methods
    def _execute_step(self, step, config_args):
        """执行单个工作流步骤"""
        agent_args = step.get('args', {})

        agent_name = step['agent']
        method_name = step['method']
        output_type = step.get('output_type', 'code')
        
        workspace_list = self._handle_input(step)
        self._handle_data_flow(config_args, agent_args)
        
        step_results = self._execute_agent_method(
            agent_name, method_name, agent_args,
            workspace_list, output_type, step.get('input', {})
        )
        
        if 'output' in step:
            self.data_store[step['output']] = step_results
            
        return step_results, agent_name, method_name

    def _handle_input(self, step):
        """处理步骤的输入数据"""
        if 'input' in step:
            input_file = step['input'].get('data')
            if False:
                self.process_instruction_file(
                    input_file, 
                    step.get('data_ids'), 
                    step.get('data_range')
                )
        return self.current_workspace  # Return current workspace as a single-item list

    def _handle_data_flow(self, config_args, agent_args):
        """处理数据流参数"""
        for arg_name, arg_value in config_args.items():
            if isinstance(arg_value, dict) and 'from' in arg_value:
                agent_args[arg_name] = self.data_store[arg_value['from']]

    def _execute_agent_method(self, agent_name, method_name, args, workspace_list, output_type, input_):
        """执行agent方法并处理结果"""
        agent = self.agents[agent_name]
        method = getattr(agent, method_name)
        
        result = self._process_single_instruction(
            agent, method, args, input_, self.current_instruction,
            self.current_workspace, output_type, agent_name
        )
        
        return result

    def _process_single_instruction(self, agent, method, args, input_, instruction, individual_workspace, output_type, agent_name):
        """处理单个指令"""
        self._prepare_instruction_args(args, input_, instruction, individual_workspace)
        
        try:
            method_output = method(**args, individual_workspace=individual_workspace)
        except Exception as e:
            print(f"错误：{e}")
            return None

        return self._handle_method_output(
            method_output, output_type, agent_name, 
            individual_workspace, args
        )

    def _prepare_instruction_args(self, args, input_, instruction, individual_workspace):
        """准备指令参数"""
        for input_name, input_value in input_.items():
            if isinstance(input_value, str) and input_name == 'code':
                file_path = os.path.join(individual_workspace, input_value)
                if os.path.isfile(file_path):
                    with open(file_path, 'r') as file:
                        args[input_name] = file.read()
        
        args['queries'] = instruction

    def _handle_method_output(self, method_output, output_type, agent_name, individual_workspace, args):
        """处理方法输出"""
        handler = self.output_handlers.get(output_type)
        if not handler:
            print(f"No handler found for output type: {output_type}")
            return None

        model_type = args['model_type'].replace('deepseek-ai/', '')
        log, result, file_name = handler.handle(
            method_output, agent_name, model_type,
            individual_workspace, args
        )

        return self._process_output_result(
            output_type, agent_name, model_type,
            result, log, file_name, individual_workspace, args
        )

    def _process_output_result(self, output_type, agent_name, model_type, result, log, file_name, individual_workspace, args):
        """处理输出结果"""
        full_log = self._handle_execution_and_logging(
            output_type, agent_name, model_type,
            result, log, file_name, individual_workspace
        )
        
        if output_type == 'code':
            result = self._handle_code_execution(
                agent_name, model_type, result, file_name,
                individual_workspace, args, full_log
            )
            
        return {'log': full_log, 'result': result}

    def _handle_execution_and_logging(self, output_type, agent_name, model_type, result, log, file_name, individual_workspace):
        """处理执行和日志记录"""
        full_log = self.log_action("Generate", agent_name, model_type, result, log, individual_workspace)
        
        if output_type == 'code':
            execution_output = self.execute_code(file_name, individual_workspace)
            full_log += self.log_action(
                "Execute", agent_name, model_type,
                result, execution_output, individual_workspace
            )
            
        return full_log

    def _handle_code_execution(self, agent_name, model_type, result, file_name, individual_workspace, args, full_log):
        """处理代码执行"""
        execution_output = self.execute_code(file_name, individual_workspace)
        if not self.is_execution_successful(execution_output):
            retry_time = 0
            while not self.is_execution_successful(execution_output) and retry_time < 1:
                try:
                    result = self._debug_code(
                        agent_name, model_type, result,
                        file_name, individual_workspace,
                        args, execution_output
                    )
                except NotImplementedError as e:
                    print(f"debug method missing: {e}")

                execution_output = self.execute_code(file_name, individual_workspace)

                print(f"Self-debugging, current retry time: {retry_time}")
                debug_log = "\n\n*********Debugged Code**********\n\n" + result +"\n\n****************Execution Output***************\n\n" + execution_output + "\n"

                # Log each debug attempt
                self.log_action(
                    f"Debug Attempt {retry_time + 1}",
                    agent_name,
                    model_type,
                    result,
                    debug_log,
                    individual_workspace
                )
                retry_time += 1
                
            if retry_time >= 10:
                error_msg = f"Maximum debug retries (10) exceeded for instruction {self.current_instruction['id']}"
                self.log_action(
                    "Debug Failed",
                    agent_name,
                    model_type,
                    result,
                    error_msg,
                    individual_workspace
                )
                raise MaxDebugRetriesExceeded(error_msg)
                
        return result

    def _debug_code(self, agent_name, model_type, code, file_name, individual_workspace, args, error_output):
        """调试代码"""
        method_name = args.get('method_name', 'run')  # 获取方法名
        debug_method = getattr(self.agents[agent_name], f"debug_{method_name}", None)
        if not debug_method:
            print(f"No debug method found for {agent_name}")
            raise NotImplementedError

        debug_args = args.copy()
        debug_args.update({
            'error_message': error_output,
            'buggy_code': code
        })

        try:
            debug_log, debug_code = debug_method(**debug_args)
            if debug_code:
                with open(os.path.join(individual_workspace, file_name), 'w') as f:
                    f.write(debug_code)
                return debug_code
        except Exception as e:
            print(f"Debug failed: {e}")
        
        return code

    # Main Workflow Methods
    def _find_input_step(self, workflow):
        """递归查找包含input的步骤"""
        for step in workflow:
            if 'input' in step:
                return step
            elif step.get('type') == 'loop' and 'steps' in step:
                input_step = self._find_input_step(step['steps'])
                if input_step:
                    return input_step
        return None

    def run_workflow(self, workflow):
        """执行工作流"""
        all_results = []
        
        # Find input step recursively
        input_step = self._find_input_step(workflow)
        if not input_step:
            raise ValueError("No input step found in workflow")
            
        # Process instruction file
        input_file = input_step['input'].get('data')
        if not input_file:
            raise ValueError("No input file specified in workflow")
            
        self.process_instruction_file(
            input_file,
            input_step.get('data_ids'),
            input_step.get('data_range')
        )

        workflow_aux = copy.deepcopy(workflow)
        
        # Now process each instruction
        for instruction in tqdm(self.instructions):
            try:
                results = {}
                # Create individual workspace for this instruction
                individual_workspace = os.path.join(self.workspace, f'example {instruction["id"]}')
                os.makedirs(individual_workspace, exist_ok=True)
                
                # Copy data file if needed
                if file_name := instruction.get('file_name'):
                    src = os.path.join(self.data_folder, file_name)
                    dst = os.path.join(individual_workspace, file_name)
                    if os.path.exists(src):
                        shutil.copy(src, dst)
                    else:
                        print(f"Warning: File {file_name} not found in data folder.")
                
                # Store current instruction and workspace
                self.current_instruction = instruction
                self.current_workspace = individual_workspace

                # Execute each step for this instruction
                for step, step_aux in zip(workflow, workflow_aux):
                    if step.get('type') == 'loop':
                        results.update(self._handle_loop_step(step, step_aux))
                    else:
                        config_args = step_aux.get('args')
                        step_results, agent_name, method_name = self._execute_step(step, config_args)
                        results[f"{agent_name}_{method_name}"] = step_results
                
                all_results.append(results)
                
            except MaxDebugRetriesExceeded as e:
                print(f"Aborting instruction {instruction['id']}: {str(e)}")
                continue  # Skip to next instruction
            
        return all_results

    def _handle_loop_step(self, step, step_aux):
        """处理循环步骤"""
        loop_results = {}
        loop_condition = True
        max_iterations = 5
        iteration = 0
        step_aux_steps = copy.deepcopy(step_aux['steps'])
        
        while loop_condition and iteration < max_iterations:
            print(f"\n=== Starting iteration {iteration + 1} ===")
            
            for substep, substep_aux in zip(step['steps'], step_aux_steps):
                if iteration == 0:
                    # 首次迭代
                    config_args = substep_aux.get('args')
                    step_results, agent_name, method_name = self._execute_step(substep, config_args)
                elif substep['agent'] != 'data_annotate_agent':
                    # 非 data_annotate_agent 时正常执行
                    config_args = substep_aux.get('args')
                    step_results, agent_name, method_name = self._execute_step(substep, config_args)
                else:
                    # data_annotate_agent 的后续迭代使用 debug 方法
                    step_results, agent_name, method_name = self._execute_debug_step(
                        substep,
                        self.data_store.get('verification_result', [])
                    )
                
                result_key = f"{agent_name}_{method_name}"
                loop_results[result_key] = step_results
                self.data_store[substep['output']] = step_results
            
            # 检查循环条件
            verifier_result = self.data_store.get('verification_result', [])
            result_data = verifier_result.get('result')
            if isinstance(result_data, str):
                result_data = ast.literal_eval(result_data)
            loop_condition = result_data.get("result").get('has_errors', True)

            # TODO: NOT APPLICABLE TO ALL AGENT WORKFLOWS
            if not loop_condition:
                self._save_correct_code("easy_medium_da-dev-q-code-a.jsonl")
            # TODO: NOT APPLICABLE TO ALL AGENT WORKFLOWS

            print(f"Iteration {iteration + 1}: {'Errors found' if loop_condition else 'No errors found'}")
            iteration += 1
            
        if iteration >= max_iterations:
            print(f"Warning: Maximum loop iterations ({max_iterations}) reached without resolving all errors")
        
        return loop_results

    def _execute_debug_step(self, step, verification_result):
        """执行 debug 步骤"""
        agent = self.agents[step['agent']]
        debug_method = getattr(agent, step['debug_method'])
        agent_args = step.get('args', {})

        agent_name = step['agent']
        method_name = step['method']
        output_type = step.get('output_type', 'code')

        
        # 从验证结果中提取错误信息
        error_info = self._extract_error_info(verification_result)
        
        # 获取之前生成的代码
        previous_result = self.data_store.get('data_analysis_result')

        if isinstance(previous_result, tuple):
            previous_code = previous_result[1]
        elif isinstance(previous_result, dict):
            previous_code = previous_result['result']
        else:
            raise TypeError("Unsupported information type between agents")
        
        # 准备 debug 方法的参数
        debug_args = {
            **step['args'],
            'error_message': error_info,
            'buggy_code': previous_code
        }
        
        # 执行 debug 方法
        method_output = debug_method(**debug_args)

        results = self._handle_method_output(
            method_output, output_type, agent_name,
            self.current_workspace, agent_args
        )

        self.log_action(
            "Verifier Debug",
            step['agent'],
            step['args']['model_type'].replace('deepseek-ai/', ''),
            str(results['result']),
            results['log'],
            self.current_workspace
        )
        
        return results, step['agent'], step['debug_method']

    def _extract_error_info(self, verification_result):
        """从验证结果中提取错误信息"""
        error_info = []

        result = verification_result.get('result')
        # Convert result_data to a dictionary if it's a string
        if isinstance(result, str):
            result = ast.literal_eval(result)

        if isinstance(result, dict):
            result_details = result.get('result', {})
            if result_details.get('has_errors'):
                # Loop over each error in the 'errors' list
                for error in result_details.get('errors', []):
                    error_info.append({
                        'error_type': error.get('error_type', ''),
                        'error_message': error.get('error_message', ''),
                        'suggestions': error.get('suggestions', '')
                    })

        else:
            raise TypeError("verification result couldn't be transformed into dict")
        
        return '\n'.join([
            f"Error Type: {err['error_type']}\n"
            f"Error Message: {err['error_message']}\n"
            f"Suggestions: {err['suggestions']}\n"
            for err in error_info
        ])

    def _save_correct_code(self, file_name):
        """保存正确的代码到jsonl文件"""
        # 获取当前的分析代码
        analysis_result = self.data_store.get('data_analysis_result')
        if isinstance(analysis_result, tuple):
            correct_code = analysis_result[1]
        elif isinstance(analysis_result, dict):
            correct_code = analysis_result.get('result', '')
        else:
            print("Warning: Could not extract correct code from analysis result")
            return

        # 更新当前instruction的内容
        instruction_with_code = self.current_instruction.copy()
        instruction_with_code['correct_analysis_code'] = correct_code

        # 创建输出目录（如果不存在）
        output_dir = os.path.join(self.workspace, 'correct_codes')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, file_name)

        # 追加写入jsonl文件
        with open(output_file, 'a', encoding='utf-8') as f:
            json.dump(instruction_with_code, f, ensure_ascii=False)
            f.write('\n')
