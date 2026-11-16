# AI 数学解题助手（homework-solver-web）

> 把 C5 的 `homework-solver` 包装成「点开链接就能用」的 AI Web 应用：输入一道题，AI 分步骤讲解，符号引擎复核答案。

## 一句话说明

一个网页：输入数学题 → 大模型（默认 DeepSeek）分步骤讲解 → SymPy 符号引擎复核答案。

## 它解决什么问题

C5 的 `homework-solver` 是命令行工具（要克隆、装环境、跑脚本），对「不会代码的人」不友好。本应用把它变成浏览器里 30 秒能上手的网页——不用装任何东西，打开链接就能用。

## 安装步骤（本地运行）

```bash
git clone https://github.com/junyisong01-glitch/homework-solver-web.git
cd homework-solver-web
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env      # 编辑 .env 填入 DEEPSEEK_API_KEY
.venv/bin/python app.py
# 浏览器打开 http://127.0.0.1:5000
```

不填 API Key 也能跑：进入「演示模式」，符号复核照常工作，只差 AI 分步讲解。

## 使用示例

| 输入 | 输出 |
|------|------|
| `lim(x->0, sin(x)/x)` | AI 讲解极限过程 + 符号复核 `1` |
| `diff(x^2)` | 符号复核 `2*x` |
| `int(x^2)` | 符号复核 `x**3/3` |
| `solve(x^2-4)` | 符号复核 `[-2, 2]` |
| 「求 x² 的导数并解释为什么」 | AI 分步讲解（自然语言题目） |

## 项目结构

```
├── app.py              ← Flask 应用（AI 核心 + 符号复核）
├── api/index.py        ← Vercel Serverless 入口
├── templates/index.html← 前端页面（手机可用）
├── requirements.txt    ← flask / requests / sympy
├── vercel.json         ← Vercel 部署配置
├── .env.example        ← API Key 模板（.env 不提交）
├── AI_LOG.md           ← AI 协作日志
├── ATTRIBUTION.md      ← 素材来源与署名
└── LICENSE             ← MIT
```

## 架构说明

- **AI 核心**：调用大模型分步骤解题讲解（默认 DeepSeek，OpenAI 兼容接口，可换）。
- **符号复核**：复用 C5 `homework-solver` 的 SymPy 引擎，对 4 种机械计算题（极限/求导/积分/解方程）做答案复核。
- **安全红线**：API Key 只走服务端环境变量，绝不出现在前端、代码或仓库里。

## 许可

MIT License。SymPy 为开源符号计算库（BSD 许可），详见 ATTRIBUTION.md。
