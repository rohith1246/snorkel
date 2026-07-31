import os
import json
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

def load_env_key():
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key
    # Try reading local .env file dynamically if available
    for env_path in [r"D:\rohithbuilds\.env", ".env"]:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("GROQ_API_KEY="):
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                pass
    return ""

class GroqTaskAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or load_env_key()

    def analyze_audit_results(self, audit_data, file_contents=None):
        """
        Sends the audit failure report to Groq AI LLM (Llama 3.3 70B) to generate actionable explanations
        and code patch recommendations.
        """
        if not self.api_key:
            return self._heuristic_fallback(audit_data)

        system_prompt = (
            "You are an expert AI Benchmark Engineer for Snorkel AI Platform and STB Harbor. "
            "Your task is to analyze audit failure reports of benchmark tasks, explain root causes, "
            "and provide exact, copy-pasteable code fixes for Dockerfile, task.toml, solution/solve.sh, "
            "instruction.md, and tests/test_outputs.py to achieve 100% compliance."
        )

        user_content = f"""
Audit Summary:
Task Name: {audit_data.get('task_name')}
Compliance Score: {audit_data.get('score')}/100
Passed Checks: {audit_data.get('passed_checks')}
Failed Checks: {audit_data.get('failed_checks')}
Warning Checks: {audit_data.get('warning_checks')}

Failed & Warning Audit Findings:
{json.dumps([c for c in audit_data.get('checks', []) if c['status'] != 'PASS'], indent=2)}

File Contexts Available:
{json.dumps(file_contents or {}, indent=2)}

Please provide a structured response with:
1. Executive Summary & Root Cause Analysis
2. Detailed Step-by-Step Fix Instructions
3. Copy-Paste Code Patches for failed files
"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.2,
            "max_tokens": 2048
        }

        try:
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                ai_text = result["choices"][0]["message"]["content"]
                return {
                    "status": "SUCCESS",
                    "source": "Groq AI (Llama 3.3 70B)",
                    "analysis": ai_text
                }
            else:
                return {
                    "status": "ERROR",
                    "source": "Groq API Call Failed",
                    "error_message": f"Groq API returned HTTP {resp.status_code}: {resp.text}",
                    "analysis": self._heuristic_fallback(audit_data)["analysis"]
                }
        except Exception as e:
            return {
                "status": "ERROR",
                "source": "Groq Connection Exception",
                "error_message": str(e),
                "analysis": self._heuristic_fallback(audit_data)["analysis"]
            }

    def _heuristic_fallback(self, audit_data):
        failed = [c for c in audit_data.get('checks', []) if c['status'] == 'FAIL']
        warns = [c for c in audit_data.get('checks', []) if c['status'] == 'WARN']

        analysis_lines = [
            "### 🤖 Snorkel Task Auditor - Rule Engine Recommendations",
            "",
            "#### Action Items:"
        ]

        for check in failed:
            analysis_lines.append(f"❌ **[{check['id']}] {check['name']}**")
            analysis_lines.append(f"- **Issue**: {check['message']}")
            if check.get('suggestion'):
                analysis_lines.append(f"- **Fix**: `{check['suggestion']}`")
            analysis_lines.append("")

        for check in warns:
            analysis_lines.append(f"⚠️ **[{check['id']}] {check['name']}**")
            analysis_lines.append(f"- **Issue**: {check['message']}")
            if check.get('suggestion'):
                analysis_lines.append(f"- **Fix**: `{check['suggestion']}`")
            analysis_lines.append("")

        return {
            "status": "SUCCESS",
            "source": "Rule Engine Heuristic Fallback",
            "analysis": "\n".join(analysis_lines)
        }
