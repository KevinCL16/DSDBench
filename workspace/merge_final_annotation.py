import json
import pandas as pd

# 定义输入的jsonl文件路径模式（比如当前目录下的所有.jsonl文件）
input_files = [r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\sklearn_pandas_errors\c_a_e_claude-3-5-sonnet-20240620_matplotbench_monitored_errors_v2_with_use_agg.jsonl", r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\sklearn_pandas_errors\c_a_e_llama-3.1-8b-instant_matplotbench_monitored_errors_with_use_agg.jsonl", r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\InfiAgent\sklearn_pandas_errors\c_a_e_gpt-4o_dabench_hard_monitored_errors_with_use_agg.jsonl", r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\InfiAgent\sklearn_pandas_errors\c_a_e_llama-3.1-8b-instant_dabench_hard_monitored_errors.jsonl", r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\InfiAgent\sklearn_pandas_errors\final_format_claude_inject_dseval_annotation.jsonl", r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\DSEval\sklearn_pandas_errors\c_a_e_llama-3.1-8b-instant_dseval_monitored_errors.jsonl"]

input_file = r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\benchmark_evaluation\bench_final_annotation_with_multi_errors_v2.jsonl"
output_file = r"D:\ComputerScience\CODES\MatPlotAgent-main\workspace\benchmark_evaluation\bench_annotation_for_multi_error_generation.jsonl"


def count_errors(files):
    """
    统计多个jsonl文件中所有error_versions的总数。
    """
    total_errors = 0
    total_queries = 0
    error_number_count = {}

    with open(files, "r") as f:
        for line in f:
            data = json.loads(line)
            error_versions = data.get("error_versions", [])
            total_errors += len(error_versions)
            total_queries += 1
            # total_errors += 1
            entry_id = data.get("id")

            error_number_count[f"entry_{entry_id}"] = len(data.get("cause_error_lines"))

    error_number_df = pd.DataFrame(list(error_number_count.items()), columns=["Query ID", "Error Count"])
    error_number_df = error_number_df.sort_values(by="Error Count", ascending=False)  # 可以按代码行数排序，方便查看
    print("\n多错误统计表格：")
    print(error_number_df.to_string(index=False))

    return total_errors, total_queries, error_number_df


def load_jsonl_files(files):
    """
    读取多个jsonl文件，合并数据到一个列表中。
    """
    all_data = []
    for file in files:
        with open(file, "r", encoding='utf-8') as f:
            all_data.extend(json.loads(line) for line in f)
    return all_data

def merge_data(data_list):
    """
    根据question字段合并数据，合并error_versions，并重新生成新的id。
    只保留error_versions中的modified_code, execution_output, effect_error_line, cause_error_line字段。
    """
    merged_dict = {}

    for entry in data_list:
        question = entry.get("question")
        error_versions = entry.get("error_versions", [])

        # 只保留每个error_version中的指定字段
        '''filtered_error_versions = [
            {
                "modified_code": version.get("modified_code"),
                "execution_output": version.get("execution_output"),
                "effect_error_line": version.get("effect_error_line"),
                "cause_error_line": version.get("cause_error_line")
            }
            for version in error_versions
        ]'''

        filtered_error_versions = [
            {
                "modified_code": version.get("modified_code"),
                "original_line": version.get("original_line", ""),
                "modified_line": version.get("modified_line", ""),
                "execution_output": version.get("execution_output"),
                "effect_error_line": version.get("effect_error_line"),
                "cause_error_line": version.get("cause_error_line")
            }
            for version in error_versions
        ]

        if filtered_error_versions[0].get("original_line") == "" or filtered_error_versions[0].get("modified_line") == "":
            print("没有original_line或modified_line")
            continue

        if question in merged_dict:
            # 如果question已存在，合并过滤后的error_versions
            merged_dict[question]["error_versions"].extend(filtered_error_versions)
        else:
            # 如果question不存在，创建新的记录
            merged_dict[question] = {
                "id": None,  # 重新生成ID
                "question": question,
                "error_versions": filtered_error_versions
            }

    # 重新分配连续的ID
    for new_id, (question, merged_entry) in enumerate(merged_dict.items(), start=1):
        merged_entry["id"] = new_id

    return list(merged_dict.values())

def save_to_jsonl(data, output_path):
    """
    将合并后的数据保存到新的jsonl文件。
    """
    with open(output_path, "w") as f:
        for entry in data:
            f.write(json.dumps(entry) + "\n")


def count_errors_main():
    # 统计错误数量
    total_errors, total_queries, error_number_df = count_errors(input_file)
    print("\n多错误分布统计量:")
    print(error_number_df['Error Count'].describe())
    print(f"共有 {total_errors} 个错误版本（error_versions）"
          f"共有 {total_queries} 个Query")


def merge_annotation_files():
    # 1. 加载所有jsonl文件
    all_data = load_jsonl_files(input_files)
    # 2. 根据question合并数据
    merged_data = merge_data(all_data)
    # 3. 保存合并后的数据到新的jsonl文件
    save_to_jsonl(merged_data, output_file)
    print(f"合并完成！结果已保存到 {output_file}")


# 运行脚本
if __name__ == "__main__":
    count_errors_main()
