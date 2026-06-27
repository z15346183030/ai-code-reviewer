# 🔍 AI Code Reviewer

一个基于 AI 的代码审查 CLI 工具。输入代码文件，自动输出结构化的代码审查报告，涵盖代码质量、潜在 Bug、性能问题和改进建议。

## ✨ 特性

- **多维度审查** — 代码风格、Bug 检测、性能优化、安全风险
- **结构化输出** — 按严重程度分级（🔴 严重 / 🟡 警告 / 🔵 建议）
- **多语言支持** — Python / JavaScript / TypeScript / Java / Go
- **OpenAI 兼容** — 支持 OpenAI / Kimi / Claude 等任意兼容接口

## 🚀 快速开始

```bash
pip install openai rich

# 配置 API Key
export OPENAI_API_KEY="sk-xxx"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选

# 审查单个文件
python reviewer.py main.py

# 审查整个目录
python reviewer.py ./src --ext .py .js

# 指定模型
python reviewer.py main.py --model gpt-4o
```

## 📊 输出示例

```
🔍 AI Code Review — main.py

🔴 严重 (1)
  L12: 使用了 eval()，存在代码注入风险
     建议: 使用 ast.literal_eval() 替代

🟡 警告 (2)
  L25: 函数 process_data 超过 50 行，建议拆分
  L38: 变量名 'd' 含义不清晰，建议使用描述性命名

🔵 建议 (3)
  L5: 未使用的 import 'os'
  L15: 可以使用列表推导式替代 for 循环
  L42: 建议添加类型注解

📊 总结: 1 严重 | 2 警告 | 3 建议
```

## 🏗️ 项目结构

```
ai-code-reviewer/
├── README.md
├── reviewer.py        # 主程序
└── .gitignore
```

## License

MIT
