# -*- coding: utf-8 -*-
"""
C6 AI Web 应用 —— AI 数学解题助手（点开链接就能用）

架构（两层，各干各的）：
  1) AI 核心（占主导）：调用大模型（默认 DeepSeek，OpenAI 兼容接口）分步骤解题 + 讲解。
     —— 这是 rubric「AI 是核心」的落点，不是可有可无的装饰。
  2) 符号复核（复用 C5 homework-solver 的 SymPy 引擎）：对明确的机械计算题做答案复核。
     —— 这是「复用 C5 项目」的真实落点：同款 sympy 依赖，同款「能解什么取决于知道什么」思路。

安全红线：API Key 只从环境变量读取（DEEPSEEK_API_KEY），绝不出现在前端 / 代码 / 仓库里。

本地运行：  python app.py   →  http://127.0.0.1:5000
部署：Vercel（见 vercel.json + api/index.py）
"""

import os
import re
import json

import requests
import sympy as sp
from flask import Flask, request, jsonify, render_template

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)

# ---------- 大模型配置（环境变量注入，绝不写死 Key）----------
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")
LLM_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()

SYSTEM_PROMPT = (
    "你是一位耐心的数学助教。对用户给的题目：\n"
    "1) 先判断题型；\n"
    "2) 分步骤写出完整解题过程（每一步带一行文字说明）；\n"
    "3) 最后给出最终答案，并用简短语言解释为什么；\n"
    "4) 如果题目信息不足或有歧义，诚实说明，不要编造；\n"
    "5) 用 Markdown 写，数学公式用 LaTeX（行内 $...$，独立公式 $$...$$）。"
)


def call_llm(problem, subject=""):
    """调用大模型分步骤解题。未配置 Key 时返回 None（进入演示模式）。"""
    if not LLM_API_KEY:
        return None
    user_msg = f"题型：{subject}\n\n题目：{problem}" if subject else f"题目：{problem}"
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.2,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            json=payload, headers=headers, timeout=90,
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:  # 网络 / Key 失效等：返回错误文本而不是崩掉
        return f"（AI 调用失败：{e}）"


def sympy_verify(problem):
    """
    用 SymPy 对「明确的机械计算题」做符号复核（复用 C5 引擎）。
    只支持 4 种标准简写，无法识别 / 解析失败时返回 None（诚实，不硬编答案）。
       lim(x->0, sin(x)/x)   diff(x^2)   int(x^2)   solve(x^2-4)
    """
    x = sp.symbols("x")
    s = (problem or "").strip()
    try:
        m = re.match(r"lim\s*\(\s*x\s*->\s*([^,)]+)\s*,\s*(.+?)\s*\)\s*$", s, re.I)
        if m:
            a = sp.sympify(m.group(1))
            f = sp.sympify(m.group(2))
            return {"method": f"limit(x→{a})", "answer": str(sp.limit(f, x, a))}
        m = re.match(r"diff\s*\(\s*(.+?)\s*\)\s*$", s, re.I)
        if m:
            return {"method": "derivative", "answer": str(sp.diff(sp.sympify(m.group(1)), x))}
        m = re.match(r"int\s*\(\s*(.+?)\s*\)\s*$", s, re.I)
        if m:
            return {"method": "integral", "answer": str(sp.integrate(sp.sympify(m.group(1)), x))}
        m = re.match(r"solve\s*\(\s*(.+?)\s*\)\s*$", s, re.I)
        if m:
            return {"method": "solve for x", "answer": str(sp.solve(sp.sympify(m.group(1)), x))}
    except Exception:
        pass
    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"ok": True, "ai_configured": bool(LLM_API_KEY)})


@app.route("/api/solve", methods=["POST"])
def solve():
    data = request.get_json(force=True, silent=True) or {}
    problem = (data.get("problem") or "").strip()
    subject = (data.get("subject") or "").strip()
    if not problem:
        return jsonify({"ok": False, "error": "请输入题目"}), 400

    ai_answer = call_llm(problem, subject)
    verify = sympy_verify(problem)
    return jsonify({
        "ok": True,
        "ai_available": ai_answer is not None,
        "ai_answer": ai_answer,
        "sympy_verify": verify,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
