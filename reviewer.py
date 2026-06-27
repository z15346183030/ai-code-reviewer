#!/usr/bin/env python3
"""AI Code Reviewer — 基于 AI 的代码审查 CLI 工具。"""

import argparse
import json
import os
import sys
from pathlib import Path

from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

REVIEW_PROMPT = """你是一个资深代码审查专家。请审查以下代码，返回 JSON 格式的审查结果。

代码文件: {filename}
编程语言: {language}

```{language}
{code}
```

请返回以下 JSON 格式（不要包含其他文字）:
{{
  "issues": [
    {{
      "severity": "critical|warning|info",
      "line": 行号(数字),
      "message": "问题描述",
      "suggestion": "改进建议"
    }}
  ],
  "summary": "一句话总结代码质量"
}}

审查维度:
1. 🔴 严重 (critical): 安全漏洞、逻辑错误、资源泄漏
2. 🟡 警告 (warning): 代码风格问题、潜在 Bug、性能问题
3. 🔵 建议 (info): 最佳实践、可读性改进、命名优化

只报告真正有价值的问题，不要吹毛求疵。"""


LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".rb": "ruby",
    ".php": "php",
}


def detect_language(filepath: str) -> str:
    """根据文件扩展名检测语言。"""
    ext = Path(filepath).suffix.lower()
    return LANG_MAP.get(ext, "text")


def review_code(client: OpenAI, model: str, code: str, filename: str, language: str) -> dict:
    """调用 AI 模型审查代码。"""
    prompt = REVIEW_PROMPT.format(filename=filename, language=language, code=code)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是代码审查专家，只返回 JSON 格式的结果。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=2048,
    )

    content = response.choices[0].message.content.strip()

    # 提取 JSON
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    return json.loads(content)


def print_review(filename: str, result: dict):
    """格式化打印审查结果。"""
    console.print()
    console.print(Panel(f"[bold cyan]🔍 AI Code Review[/] — {filename}", style="cyan"))

    issues = result.get("issues", [])
    if not issues:
        console.print("[green]✅ 未发现问题，代码质量良好！[/]")
        return

    # 按严重程度分组
    severity_config = {
        "critical": {"icon": "🔴", "label": "严重", "style": "bold red"},
        "warning": {"icon": "🟡", "label": "警告", "style": "yellow"},
        "info": {"icon": "🔵", "label": "建议", "style": "blue"},
    }

    counts = {"critical": 0, "warning": 0, "info": 0}

    for severity in ["critical", "warning", "info"]:
        group = [i for i in issues if i.get("severity") == severity]
        if not group:
            continue

        config = severity_config[severity]
        counts[severity] = len(group)

        console.print(f"\n{config['icon']} {config['label']} ({len(group)})")
        for issue in group:
            line = issue.get("line", "?")
            msg = issue.get("message", "")
            suggestion = issue.get("suggestion", "")
            console.print(f"  L{line}: {msg}", style=config["style"])
            if suggestion:
                console.print(f"     建议: {suggestion}", style="dim")

    # 总结
    summary = result.get("summary", "")
    console.print(f"\n📊 [bold]总结[/]: {counts['critical']} 严重 | {counts['warning']} 警告 | {counts['info']} 建议")
    if summary:
        console.print(f"💬 {summary}")
    console.print()


def collect_files(path: str, extensions: list[str]) -> list[str]:
    """收集待审查的文件列表。"""
    target = Path(path)
    if target.is_file():
        return [str(target)]

    files = []
    for ext in extensions:
        files.extend(str(f) for f in target.rglob(f"*{ext}"))
    return sorted(files)


def main():
    parser = argparse.ArgumentParser(description="AI Code Reviewer — AI 代码审查工具")
    parser.add_argument("path", help="要审查的文件或目录")
    parser.add_argument("--model", default="gpt-4o", help="模型名称 (默认: gpt-4o)")
    parser.add_argument("--ext", nargs="+", default=[".py", ".js", ".ts"], help="文件扩展名过滤")
    parser.add_argument("--output", default=None, help="输出 JSON 报告到文件")
    args = parser.parse_args()

    # 初始化客户端
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not api_key:
        console.print("[red]错误: 请设置 OPENAI_API_KEY 环境变量[/]")
        sys.exit(1)

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)

    # 收集文件
    files = collect_files(args.path, args.ext)
    if not files:
        console.print(f"[red]未找到匹配的文件: {args.path}[/]")
        sys.exit(1)

    console.print(f"[cyan]📂 找到 {len(files)} 个文件待审查[/]\n")

    all_results = []

    for filepath in files:
        language = detect_language(filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code = f.read()
        except Exception as e:
            console.print(f"[red]读取失败 {filepath}: {e}[/]")
            continue

        console.print(f"[dim]审查中: {filepath}...[/]")
        try:
            result = review_code(client, args.model, code, filepath, language)
            print_review(filepath, result)
            all_results.append({"file": filepath, "result": result})
        except json.JSONDecodeError:
            console.print(f"[yellow]⚠️ {filepath}: AI 返回格式异常，跳过[/]")
        except Exception as e:
            console.print(f"[red]❌ {filepath}: {e}[/]")

    # 输出 JSON 报告
    if args.output and all_results:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        console.print(f"[green]📄 报告已保存: {args.output}[/]")


if __name__ == "__main__":
    main()
