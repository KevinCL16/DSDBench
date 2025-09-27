# 🔒 安全配置说明

## API密钥配置

**重要：** 请勿在代码中硬编码任何API密钥！

### 配置步骤：

1. **复制环境变量模板文件：**
   ```bash
   cp env.example .env
   ```

2. **编辑 `.env` 文件，填入你的真实API密钥：**
   ```
   OPENROUTER_API_KEY=你的真实密钥
   ```

3. **确保 `.env` 文件已被 `.gitignore` 忽略，不会提交到Git**

### 支持的API密钥：

- `OPENROUTER_API_KEY`: OpenRouter API密钥
- `OPENAI_API_KEY`: OpenAI API密钥（如果需要）
- `ANTHROPIC_API_KEY`: Anthropic API密钥（如果需要）

### 安全提醒：

- ✅ 使用环境变量存储敏感信息
- ✅ 将 `.env` 文件添加到 `.gitignore`
- ❌ 不要在代码中硬编码密钥
- ❌ 不要将包含密钥的文件提交到Git
- ❌ 不要在公开仓库中暴露API密钥

如果发现密钥泄露，请立即：
1. 在对应平台撤销/重新生成密钥
2. 检查密钥使用情况
3. 更新所有使用该密钥的地方
