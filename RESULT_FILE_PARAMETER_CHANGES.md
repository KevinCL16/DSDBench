# Result File Parameter Changes

## 概述
为DSDBench的单bug评估系统添加了自定义结果文件路径参数支持，并实现了基于配置信息的自动文件名生成功能。

## 修改的文件

### 1. `run_single_bug_eval.py`
- 添加了 `--result-file` 命令行参数
- 实现了 `generate_result_filename()` 函数，根据配置自动生成文件名
- 默认值: 基于配置自动生成 (格式: `eval_{model_name}_{eval_type}_{id_info}_rubber_duck_case_study_on_bench_v3.jsonl`)
- 将参数传递给 `workflow_generic.py` 和 `compute_single_eval_results.py`

### 2. `workflow_generic.py`
- 添加了 `--result-file` 命令行参数
- 实现了 `generate_result_filename_from_config()` 函数
- 默认值: 基于配置自动生成 (如果不提供参数)
- 将结果文件路径传递给workflow配置中的agent参数

### 3. `compute_single_eval_results.py`
- 重构为使用 `main()` 函数
- 添加了 `--result-file` 命令行参数
- 实现了 `generate_result_filename_from_config()` 函数
- 默认值: 基于配置自动生成
- 添加了文件存在性检查

### 4. `agents/error_verifier_agent/agent.py`
- 修改 `rubber_duck_eval` 方法签名，添加 `result_file` 参数
- 支持自定义结果文件路径
- 自动创建目录（如果不存在）

### 5. `config/single_bug_eval_agent_config.py`
- 在workflow配置中添加了 `result_file` 参数

## 自动文件名生成功能

### 文件名格式
```
eval_{model_name}_{eval_type}_{id_info}_rubber_duck_case_study_on_bench_v3.jsonl
```

### 组件说明
- `model_name`: 从配置中提取的模型名称 (如: `openai_gpt-oss-120b`)
- `eval_type`: 评估类型 (如: `single_bug`)
- `id_info`: 数据ID信息
  - 单个ID: `id_2`
  - 多个ID: `ids_1_2_3`
  - 数据范围: `range_1_10` (当使用data_range时)
  - 所有ID: `all_ids`

### 示例文件名
```
# data_ids = [2]
eval_openai_gpt-oss-120b_single_bug_id_2.jsonl

# data_ids = [1, 2, 3]
eval_openai_gpt-oss-120b_single_bug_ids_1_2_3.jsonl

# data_range = [1, 10]
eval_openai_gpt-oss-120b_single_bug_range_1_10.jsonl

# 无data_ids或data_range
eval_openai_gpt-oss-120b_single_bug_all_ids.jsonl
```

## 使用方法

### 基本用法 (使用自动生成的文件名)
```bash
python run_single_bug_eval.py
```

### 自定义结果文件路径
```bash
python run_single_bug_eval.py --result-file /path/to/your/custom/result.jsonl
```

### 直接运行workflow (使用自动文件名)
```bash
python workflow_generic.py --config config/single_bug_eval_agent_config.py
```

### 直接运行计算脚本
```bash
cd workspace/benchmark_evaluation
python compute_single_eval_results.py --result-file /path/to/your/result.jsonl
```

## 参数传递流程

1. `run_single_bug_eval.py` 接收 `--result-file` 参数
2. 传递给 `workflow_generic.py` 的 `--result-file` 参数
3. `workflow_generic.py` 将参数注入到workflow配置中
4. `ErrorVerifierAgent.rubber_duck_eval` 使用自定义路径保存结果
5. `compute_single_eval_results.py` 使用相同路径读取结果进行计算

## 新功能特性

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

## 测试
- 所有修改的Python文件都通过了语法检查
- 参数传递机制已验证
- 自动文件名生成功能已验证
- 文件名格式和组件提取功能已验证
