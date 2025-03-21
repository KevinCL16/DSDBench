import json
import re
import os
import argparse
from tqdm import tqdm
from agents.utils import run_code


def extract_traceback(error_str):
    """
    Extract 'Traceback (most recent call last):' and subsequent error information from an error string.
    """
    pattern = r"Traceback \(most recent call last\):.*"
    match = re.search(pattern, error_str, re.DOTALL)
    if match:
        return match.group(0)
    else:
        return None


def extract_filepath_and_filename(traceback_string):
    """
    Extracts the file path and filename (ending with 'error_{i}_monitored.py')
    from a Python traceback string. Extracts only the first occurrence.

    Args:
        traceback_string: The traceback string.

    Returns:
        A tuple containing:
            - directory_path (str): The directory path of the file, or None if not found.
            - filename (str): The filename (ending with 'error_{i}_monitored.py'), or None if not found.
    """
    lines = traceback_string.splitlines()
    for line in lines:
        match = re.search(r'^\s*File\s+"?([A-Za-z]:[\\/].*error_\d+_monitored\.py)"?', line)
        if match:
            full_filepath = match.group(1)
            directory_path, filename = os.path.split(full_filepath)
            return directory_path, filename, full_filepath  # Return both and exit
    return None, None  # Return None for both if no matching path is found


def extract_error_lines(execution_output):
    """
    Extract error lines marked with '!!!' from execution output.
    Avoid extracting duplicate error lines for the same error.
    """
    error_lines = []
    lines = execution_output.splitlines()
    skip_next = False  # Flag to skip duplicate '!!!' markers

    for i, line in enumerate(lines):
        if "!!!" in line:  # Three exclamation marks as markers
            if skip_next:  # Skip current '!!!' if flag is True
                continue
            # Search upward for the code line
            for j in range(i - 1, -1, -1):
                if "|" in lines[j]:  # Find line with code
                    error_code_line = lines[j].split("|", 1)[1].strip()  # Extract code content
                    if error_code_line not in error_lines:  # Avoid duplicates
                        error_lines.append(error_code_line)
                    break
            skip_next = True  # Set flag to True to skip subsequent '!!!'
        else:
            skip_next = False  # Reset flag if current line has no '!!!'

    return error_lines


def compare_error_and_modified_line(jsonl_file_path, output_file_path):
    """
    遍历 JSONL 文件，检查 execution_output 中的报错行是否和 modified_line 一致。
    """
    with open(jsonl_file_path, "r", encoding="utf-8") as file:
        entries = []
        consistent_count = 0
        inconsistent_count = 0
        for line in file:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"JSON 解码错误: {e}")
                continue

            error_versions = entry.get("error_versions", [])
            for error_version in error_versions:
                execution_output = error_version.get("execution_output", "")
                modified_line = error_version.get("modified_line", "")

                # 提取 execution_output 中的报错行代码
                error_line_list = extract_error_lines(execution_output)
                error_line = error_line_list[-1]

                # 将 cause_error_line 和 effect_error_line 添加到 error_version 中
                error_version["effect_error_line"] = error_line
                error_version["cause_error_line"] = modified_line

                if error_line:
                    # 比较报错行与 modified_code
                    if error_line.strip() == modified_line.strip():
                        print("报错行和修改行一致")
                        consistent_count += 1
                    else:
                        print("报错行和修改行不一致")
                        print(f"报错行代码: {error_line}")
                        print(f"修改代码: {modified_line}")
                        inconsistent_count += 1
                else:
                    print("未找到报错行代码")

            # 修改后的 entry 保留在原位置
            entries.append(entry)

        print(f"\n报错行和修改行一致有：{consistent_count} 条\n报错行和修改行不一致有：{inconsistent_count} 条")

        # 将修改后的数据写回到新的 JSONL 文件
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            for entry in entries:
                output_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def find_cause_and_effect_error_lines_for_weak_analysis(jsonl_file_path, output_file_path):
    """
    遍历 JSONL 文件，检查 execution_output 中的报错行，并在每个 error_version 中新增 cause_error_line 和 effect_error_line。
    """
    with open(jsonl_file_path, "r", encoding="utf-8") as file:
        entries = []
        count = 0
        consistent_count = 0
        inconsistent_count = 0

        for line in file:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"JSON 解码错误: {e}")
                continue

            error_versions = entry.get("error_versions", [])
            for error_version in error_versions:
                execution_output = error_version.get("execution_output", "")

                # 提取 execution_output 中的报错行代码
                error_line_list = extract_error_lines(execution_output)

                if len(error_line_list) >= 2:
                    effect_error_line = error_line_list[-1]
                    cause_error_line = error_line_list[-2]

                    # 将 cause_error_line 和 effect_error_line 添加到 error_version 中
                    error_version["effect_error_line"] = effect_error_line
                    error_version["cause_error_line"] = cause_error_line

                    # 比较报错行与修改行
                    if effect_error_line.strip() == cause_error_line.strip():
                        print("报错行和修改行一致")
                        consistent_count += 1
                    else:
                        print("报错行和修改行不一致")
                        print(f"报错行代码: {effect_error_line}")
                        print(f"修改代码: {cause_error_line}")
                        inconsistent_count += 1
                else:
                    effect_error_line = error_line_list[-1]
                    cause_error_line = error_line_list[-1]

                    # 将 cause_error_line 和 effect_error_line 添加到 error_version 中
                    error_version["effect_error_line"] = effect_error_line
                    error_version["cause_error_line"] = cause_error_line
                    print("仅有一行报错代码，同行报错")
                    consistent_count += 1

            # 修改后的 entry 保留在原位置
            entries.append(entry)

    # 输出统计结果
    print(f"\n报错行和修改行一致有：{consistent_count} 条\n报错行和修改行不一致有：{inconsistent_count} 条")

    # 将修改后的数据写回到新的 JSONL 文件
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        for entry in entries:
            output_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def find_error_message_error_type(jsonl_file_path):
    """
    遍历 JSONL 文件，检查 execution_output 中的报错行是否和 modified_line 一致。
    """
    error_type_count = {}  # 用于记录错误类型的统计
    code_length_count = {}  # 用于记录代码长度的统计
    question_length_count = {}
    multi_hop_count, no_hop_count = 0, 0

    with open(jsonl_file_path, "r", encoding="utf-8") as file:
        for entry_id, line in enumerate(file):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"JSON 解码错误: {e}")
                continue

            query = entry.get('question', "")
            question_words = query.strip().split(' ')
            question_word_count = len(question_words)
            question_length_count[f"entry_{entry_id}"] = question_word_count

            if entry_id in [1,2,3,4,5,51,52,53,54,55,100,101,102,103,104,151,152,153,154,155]:
                print(f"ID: {entry_id}\n\nModified Code:\n{modified_code}\n\n")

            error_versions = entry.get("error_versions", [])
            for error_id, error_version in enumerate(error_versions):
                modified_code = error_version.get("modified_code", "")
                execution_output = error_version.get("execution_output", "")
                error_message = extract_traceback(execution_output)
                cause_error_line = error_version.get("cause_error_line", "")
                effect_error_line = error_version.get("effect_error_line", "")

                if entry_id in [1, 2, 3, 4, 5, 51, 52, 53, 54, 55, 100, 101, 102, 103, 104, 151, 152, 153, 154, 155]:
                    print(f"Error ID: {error_id}\nCause Line: {cause_error_line}\nEffect Line: {effect_error_line}\nError Message: {error_message}\n")

                # 确保 error_message 是字符串
                if not isinstance(error_message, str):
                    error_message = ""

                # 使用正则表达式匹配错误类型
                pattern = r"(?<=\n)(\w+Error):"
                match = re.search(pattern, error_message)

                if match:
                    error_type = match.group(1)  # 提取错误类型
                    error_type_count[error_type] = error_type_count.get(error_type, 0) + 1
                else:
                    # print(f"id: {entry_id}, error_id: {error_id}\nError Traceback: {error_message}\n\n")
                    error_type_count["Other"] = error_type_count.get("Other", 0) + 1

                # 统计 modified_code 的代码行数
                code_lines = modified_code.strip().splitlines()  # 使用 strip() 去除首尾空白行，然后 splitlines() 分割行
                line_count = len(code_lines)
                if line_count < 10:
                    # print("有点短\n" + modified_code + '\n')
                    continue
                code_length_count[f"entry_{entry_id}_error_{error_id}"] = line_count  # 使用 entry_id 和 error_id 作为键

                if cause_error_line != effect_error_line:
                    multi_hop_count += 1
                else:
                    no_hop_count += 1

    # 将错误类型统计结果转换为 DataFrame
    error_df = pd.DataFrame(list(error_type_count.items()), columns=["Error Type", "Count"])
    error_df = error_df.sort_values(by="Count", ascending=False)  # 按错误出现次数降序排序

    # 输出错误类型统计表格
    print("\n错误类型统计表格：")
    print(error_df.to_string(index=False))

    # 将代码长度统计结果转换为 DataFrame，便于后续分析
    code_length_df = pd.DataFrame(list(code_length_count.items()), columns=["Code Snippet ID", "Line Count"])
    code_length_df = code_length_df.sort_values(by="Line Count", ascending=False)  # 可以按代码行数排序，方便查看

    # 输出代码长度统计表格 (可选，如果需要直接查看)
    print("\n代码长度统计表格：")
    print(code_length_df.to_string(index=False))

    # 将问题长度统计结果转换为 DataFrame，便于后续分析
    question_length_df = pd.DataFrame(list(question_length_count.items()), columns=["Query ID", "Word Count"])
    question_length_df = question_length_df.sort_values(by="Word Count", ascending=False)  # 可以按代码行数排序，方便查看

    # 输出问题长度统计表格 (可选，如果需要直接查看)
    print("\n问题长度统计表格：")
    print(question_length_df.to_string(index=False))

    print(f"\nMulti Hop cause and effect pair number: {multi_hop_count}\nNo Hop cause and effect number: {no_hop_count}")

    return error_df, code_length_df, question_length_df


def find_meaningless_annotation_and_remedy(jsonl_file_path):
    """
    遍历 JSONL 文件，检查 execution_output 中的报错行是否和 modified_line 一致。
    """
    error_type_count = {}  # 用于记录错误类型的统计

    with open(jsonl_file_path, "r", encoding="utf-8") as file:
        inconsistent_count, consistent_count = 0, 0
        for entry_id, line in tqdm(enumerate(file)):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"JSON 解码错误: {e}")
                continue

            error_versions = entry.get("error_versions", [])
            for error_id, error_version in enumerate(error_versions):
                cause_line = error_version.get("cause_error_line", "")
                modified_code = error_version.get("modified_code", "")
                execution_output = error_version.get("execution_output", "")
                error_message = extract_traceback(execution_output)

                if cause_line == "main()":
                    # print(f"id: {entry_id}, error_id: {error_id}\nError Message:\n {error_message}\nCause Line: {error_version['cause_error_line']}\nEffect Line: {error_version['effect_error_line']}\n")
                    code_lines = modified_code.splitlines()
                    import_lines = []
                    body_lines = []

                    for line in code_lines:
                        if line.strip().startswith(('import ', 'from ')):
                            import_lines.append(line)
                        else:
                            body_lines.append(line)

                    # Add snoop import
                    import_lines.append('import snoop')

                    decorated_body = []
                    for line in body_lines:
                        stripped_line = line.strip()
                        indentation = line[:len(line) - len(line.lstrip())]  # Capture indentation

                        if stripped_line.startswith('def '):
                            decorated_body.append(
                                indentation + '@snoop')  # Add @snoop with the same indentation as 'def'
                            decorated_body.append(line)  # Append the original 'def' line
                        else:
                            decorated_body.append(line)  # Append other lines as is

                    # Combine imports and body
                    monitored_code = '\n'.join([
                        *import_lines,
                        '',
                        *decorated_body,
                    ])

                    extracted_directory, error_file, extracted_filepath = extract_filepath_and_filename(error_message)
                    with open(extracted_filepath, 'w') as f:
                        f.write(monitored_code)

                    # Run the code and capture output
                    new_exec_output = run_code(extracted_directory, error_file)

                    # Update the error case with execution results
                    error_version['execution_output'] = new_exec_output
                    # error_version['monitored_code'] = monitored_code
                    new_error_message = extract_traceback(new_exec_output)

                    # 提取 execution_output 中的报错行代码
                    error_line_list = extract_error_lines(new_exec_output)

                    if len(error_line_list) >= 2:
                        effect_error_line = error_line_list[-1]
                        cause_error_line = error_line_list[-2]

                        # 将 cause_error_line 和 effect_error_line 添加到 error_version 中
                        error_version["effect_error_line"] = effect_error_line
                        error_version["cause_error_line"] = cause_error_line

                        # 比较报错行与修改行
                        if effect_error_line.strip() == cause_error_line.strip():
                            # print("报错行和修改行一致")
                            consistent_count += 1
                        else:
                            # print("报错行和修改行不一致")
                            # print(f"报错行代码: {effect_error_line}")
                            # print(f"修改代码: {cause_error_line}")
                            inconsistent_count += 1
                    else:
                        effect_error_line = error_line_list[-1]
                        cause_error_line = error_line_list[-1]

                        # 将 cause_error_line 和 effect_error_line 添加到 error_version 中
                        error_version["effect_error_line"] = effect_error_line
                        error_version["cause_error_line"] = cause_error_line
                        # print("仅有一行报错代码，同行报错")
                        consistent_count += 1

                    # print(f"\nAfter remedy:\nid: {entry_id}, error_id: {error_id}\nError Message:\n {new_error_message}\nCause Line: {error_version['cause_error_line']}\nEffect Line: {error_version['effect_error_line']}\n")

            # Save the updated queries with execution results
            output_file = r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\benchmark_evaluation\bench_final_annotation_v4.jsonl"
            with open(output_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')


def find_cause_and_effect_lines(jsonl_file_path, output_file_path):
    """
    Analyze error versions in the JSONL file to identify cause and effect error lines.
    """
    with open(jsonl_file_path, "r", encoding="utf-8") as file:
        entries = []
        multi_hop_count = 0
        single_hop_count = 0

        for line in tqdm(file, desc="Processing entries"):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                continue

            error_versions = entry.get("error_versions", [])
            for error_version in error_versions:
                execution_output = error_version.get("execution_output", "")

                # Extract error lines from execution output
                error_line_list = extract_error_lines(execution_output)

                if len(error_line_list) >= 2:
                    # Multi-hop error: at least two error lines
                    effect_error_line = error_line_list[-1]  # Last error line is the effect
                    cause_error_line = error_line_list[-2]   # Second-to-last is the cause
                    
                    # Add cause and effect lines to the error version
                    error_version["effect_error_line"] = effect_error_line
                    error_version["cause_error_line"] = cause_error_line
                    
                    if effect_error_line.strip() != cause_error_line.strip():
                        multi_hop_count += 1
                    else:
                        single_hop_count += 1
                        
                elif len(error_line_list) == 1:
                    # Single-hop error: only one error line
                    effect_error_line = error_line_list[0]
                    
                    # For single-hop, both cause and effect are the same line
                    error_version["effect_error_line"] = effect_error_line
                    error_version["cause_error_line"] = effect_error_line
                    single_hop_count += 1

            # Keep the modified entry
            entries.append(entry)

    # Print statistics
    print(f"\nMulti-hop errors: {multi_hop_count}")
    print(f"Single-hop errors: {single_hop_count}")
    print(f"Total errors: {multi_hop_count + single_hop_count}")

    # Write modified data to the new JSONL file
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        for entry in entries:
            output_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    print(f"Processed data saved to: {output_file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Find multi-hop errors in data')
    parser.add_argument('--input', default='workspace/sklearn_pandas_errors/filtered_errors.jsonl',
                       help='Path to input JSONL file')
    parser.add_argument('--output', default='workspace/benchmark_evaluation/annotated_errors.jsonl',
                       help='Path to output annotated JSONL file')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Find cause and effect error lines
    find_cause_and_effect_lines(args.input, args.output)

# 测试函数，传入包含 JSONL 数据的文件路径
jsonl_file_path = r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\benchmark_evaluation\bench_final_annotation_v4.jsonl"  # 替换为您的 JSONL 文件路径
jsonl_output_path = r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\sklearn_pandas_errors\c_a_e_llama-3.1-8b-instant_matplotbench_monitored_errors_with_use_agg.jsonl"

error_df, code_length_df, question_length_df = find_error_message_error_type(jsonl_file_path)

# 你可以在这里对 code_length_df 进行进一步的统计分析，例如：
print("\n代码长度统计量:")
print(code_length_df['Line Count'].describe())

# 你可以在这里对 code_length_df 进行进一步的统计分析，例如：
print("\n问题长度统计量:")
print(question_length_df['Word Count'].describe())

# 例如，绘制代码长度分布直方图 (需要 matplotlib)
'''import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('tkagg')

plt.hist(question_length_df['Word Count'], bins=50) # 可以调整 bins 参数
plt.title('Question Length Distribution')
plt.xlabel('Word Count')
plt.ylabel('Frequency')
plt.show()'''