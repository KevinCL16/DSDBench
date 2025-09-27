# 🚀 DSDBench 环境配置指南

## 📋 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

#### 方法A：使用 .env 文件（推荐）

1. **复制环境变量模板**：
   ```bash
   cp env.example .env
   ```

2. **编辑 `.env` 文件**，填入你的API密钥：
   ```
   OPENROUTER_API_KEY=sk-or-v1-你的真实密钥
   ```

3. **验证配置**：
   ```python
   from agents.config.openai import API_KEY
   print(f"API Key loaded: {API_KEY[:10]}..." if API_KEY else "No API key found")
   ```

#### 方法B：直接设置环境变量

**Windows (PowerShell)**：
```powershell
$env:OPENROUTER_API_KEY="sk-or-v1-你的真实密钥"
```

**Windows (CMD)**：
```cmd
set OPENROUTER_API_KEY=sk-or-v1-你的真实密钥
```

**Linux/Mac**：
```bash
export OPENROUTER_API_KEY="sk-or-v1-你的真实密钥"
```

### 3. 运行测试

```bash
# 运行单bug评估
python run_single_bug_eval.py

# 运行多bug评估  
python run_multi_bug_eval.py
```

## 🔒 安全提醒

- ✅ `.env` 文件已被 `.gitignore` 忽略，不会提交到Git
- ✅ 使用环境变量存储敏感信息
- ❌ 不要在代码中硬编码API密钥
- ❌ 不要将包含密钥的文件提交到Git

## 🛠️ 故障排除

### 问题1：找不到API密钥
```
错误：API Key loaded: 
解决：检查 .env 文件是否存在且包含正确的 OPENROUTER_API_KEY
```

### 问题2：导入错误
```
错误：ModuleNotFoundError: No module named 'dotenv'
解决：pip install python-dotenv
```

### 问题3：API调用失败
```
错误：401 Unauthorized
解决：检查API密钥是否正确，是否有足够的配额
```

## 📁 文件结构

```
DSDBench/
├── .env                    # 你的API密钥（不提交到Git）
├── env.example            # 环境变量模板
├── .gitignore             # Git忽略文件
├── requirements.txt       # Python依赖
└── agents/config/openai.py # API配置
```

## 🔄 更新API密钥

如果需要更换API密钥：

1. **编辑 `.env` 文件**：
   ```
   OPENROUTER_API_KEY=新的密钥
   ```

2. **重启程序**（环境变量在程序启动时加载）

3. **验证新密钥**：
   ```python
   from agents.config.openai import API_KEY
   print("API Key updated successfully")
   ```
