# Multi Bug Evaluation Changes

## 概述
成功将single bug评估的成功经验复刻到multi bug评估系统，实现了相同的自动文件名生成和参数传递功能。

## 修改的文件

### 1. `run_multi_bug_eval.py`
- 添加了 `--result-file` 命令行参数
- 实现了 `generate_result_filename()` 函数，根据配置自动生成文件名
- 默认值: 基于配置自动生成 (格式: `eval_{model_name}_{eval_type}_{id_info}.jsonl`)
- 将参数传递给 `workflow_generic.py` 和 `compute_multi_eval_results.py`

### 2. `compute_multi_eval_results.py`
- 重构为使用 `main()` 函数
- 添加了 `--result-file` 命令行参数
- 实现了 `generate_result_filename_from_config()` 函数
- 默认值: 基于配置自动生成
- 添加了文件存在性检查和路径处理
- 修复了ground_truth文件路径

### 3. `config/multi_bug_eval_agent_config.py`
- 在workflow配置中添加了 `result_file` 参数

## 自动文件名生成功能

### 文件名格式
```
eval_{model_name}_{eval_type}_{id_info}.jsonl
```

### 组件说明
- `model_name`: 从配置中提取的模型名称 (如: `Qwen_Qwen2.5-72B-Instruct`)
- `eval_type`: 评估类型 (如: `multi_bug`)
- `id_info`: 数据ID信息
  - 单个ID: `id_4`
  - 多个ID: `ids_4_9_10_109_110_208_309`
  - 数据范围: `range_1_10` (当使用data_range时)
  - 所有ID: `all_ids`

### 示例文件名
```
# data_ids = [4, 9, 10, 109, 110, 208, 309]
eval_Qwen_Qwen2.5-72B-Instruct_multi_bug_ids_4_9_10_109_110_208_309.jsonl

# data_range = [1, 10]
eval_Qwen_Qwen2.5-72B-Instruct_multi_bug_range_1_10.jsonl
```

## 使用方法

### 基本用法 (使用自动生成的文件名)
```bash
python run_multi_bug_eval.py
```

### 自定义结果文件路径
```bash
python run_multi_bug_eval.py --result-file custom_multi_bug_result.jsonl
```

### 直接运行计算脚本
```bash
cd workspace/benchmark_evaluation
python compute_multi_eval_results.py --result-file /path/to/your/result.jsonl
```

## 测试结果

### 1. 文件名生成测试
```bash
# 测试run_multi_bug_eval.py
python run_multi_bug_eval.py --help
# 输出: eval_Qwen_Qwen2.5-72B-Instruct_multi_bug_ids_4_9_10_109_110_208_309.jsonl

# 测试compute_multi_eval_results.py
cd workspace/benchmark_evaluation
python compute_multi_eval_results.py --help
# 输出: eval_Qwen_Qwen2.5-72B-Instruct_multi_bug_ids_4_9_10_109_110_208_309.jsonl
```

### 2. 功能验证测试
```bash
# 测试文件名生成
python -c "from run_multi_bug_eval import generate_result_filename; print('Generated filename:', generate_result_filename('config/multi_bug_eval_agent_config.py'))"
# 输出: eval_Qwen_Qwen2.5-72B-Instruct_multi_bug_ids_4_9_10_109_110_208_309.jsonl

# 测试计算脚本
python compute_multi_eval_results.py --result-file eval_openai_gpt-oss-120b_single_bug_id_2.jsonl
# 成功运行并计算评估结果
```

## 功能特性

### 自动文件名生成
- ✅ 根据配置信息自动生成描述性文件名
- ✅ 包含模型名称、评估类型、数据ID等关键信息
- ✅ 支持单个ID、多个ID和数据范围的情况
- ✅ 自动处理路径分隔符和特殊字符
- ✅ 支持data_range配置 (如: [1, 10] 表示样本1到10)

### 智能默认值
- ✅ 如果不提供 `--result-file` 参数，自动使用生成的文件名
- ✅ 保持向后兼容，仍支持手动指定文件路径
- ✅ 所有脚本都支持自动文件名生成

### 文件名优先级
1. **data_range** (最高优先级) - 当配置中有data_range时使用
2. **data_ids** - 当配置中有data_ids时使用
3. **all_ids** (后备选项) - 当既没有data_range也没有data_ids时使用

## 向后兼容性
- 所有修改都保持向后兼容
- 如果不提供 `--result-file` 参数，系统使用自动生成的文件名
- 现有的工作流程不受影响
- 仍支持手动指定自定义文件路径

## 成功复刻的功能
- ✅ 自动文件名生成
- ✅ 路径处理
- ✅ 相对路径处理
- ✅ 路径重复修复
- ✅ 参数传递
- ✅ 错误处理
- ✅ 向后兼容

现在multi bug评估系统具有与single bug评估系统完全相同的功能和特性！
