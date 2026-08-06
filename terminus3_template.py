import io
import zipfile

TERMINUS3_FOLDER_STRUCTURE = [
    {
        "path": "task.toml",
        "type": "file",
        "description": "Main Terminus 3 configuration file declaring metadata, artifacts array, verifier mode ('separate'), and environment specs."
    },
    {
        "path": "instruction.md",
        "type": "file",
        "description": "Task instructions provided to benchmark LLMs. Must be 1-5 paragraphs of clean conversational prose (no headings or bullet lists)."
    },
    {
        "path": "README.md",
        "type": "file",
        "description": "Human-written developer documentation explaining task background, architecture, and local testing instructions."
    },
    {
        "path": "environment/",
        "type": "folder",
        "description": "Main task container setup directory."
    },
    {
        "path": "environment/Dockerfile",
        "type": "file",
        "description": "Digest-pinned Dockerfile setting up task runtime image (includes tmux, asciinema, and system dependencies)."
    },
    {
        "path": "environment/.dockerignore",
        "type": "file",
        "description": "Build context exclusion file ignoring solution/, tests/, jobs/, and .git."
    },
    {
        "path": "environment/data/",
        "type": "folder",
        "description": "Directory holding initial raw un-reconciled dataset files provided to the agent."
    },
    {
        "path": "solution/",
        "type": "folder",
        "description": "Oracle reference solution directory."
    },
    {
        "path": "solution/solve.sh",
        "type": "file",
        "description": "Executable bash entrypoint that runs the reference solution to achieve 1.000 score."
    },
    {
        "path": "tests/",
        "type": "folder",
        "description": "Isolated verifier test suite directory."
    },
    {
        "path": "tests/Dockerfile",
        "type": "file",
        "description": "Terminus 3 separate verifier container image Dockerfile (includes COPY . /tests, WORKDIR /tests, pytest-json-ctrf)."
    },
    {
        "path": "tests/test.sh",
        "type": "file",
        "description": "Verifier entrypoint script running pytest with CTRF log generation and reward writing."
    },
    {
        "path": "tests/test_outputs.py",
        "type": "file",
        "description": "Pytest assertion suite verifying output artifacts. 100% of test functions must have descriptive docstrings."
    }
]

TEMPLATE_TASK_TOML = """name = "sample-terminus3-reconciliation-task"
category = "Software"
subcategory = "Systems"
tags = ["bash", "python", "sql", "reconciliation"]
languages = ["python", "bash", "sql"]
difficulty = "frontier"
expert_time_estimate_hours = 6
difficulty_explanation = "Requires multi-step system drift reconciliation across TSV logs and SQL migration generation."
solution_explanation = "The reference solution parses TSV logs, verifies parameter checksums, and emits formatted JSON and SQL migration files."
verification_explanation = "Pytest suite verifies schema validation, CLI --json-summary flag behavior, and SQL migration file structure."
relevant_experience = "Distributed systems administration, Python data parsing, SQL migration scripting."
artifacts = [
    "/app/reconciliation_report.json",
    "/app/migrations/V1__reconciled_output.sql"
]

[verifier]
timeout_sec = 1800
environment_mode = "separate"

[agent]
timeout_sec = 5400

[environment]
network_mode = "public"
build_timeout_sec = 900
cpus = 2
memory_mb = 8192
storage_mb = 10240
"""

TEMPLATE_INSTRUCTION_MD = """A system audit identified that production server logs and database records in /app/data/system_audit_log.tsv drifted from our authoritative infrastructure registry. You need to create an automated reconciliation script at /app/reconcile.py to inspect drift records, resolve mismatched configuration parameters, and generate the final output report at /app/reconciliation_report.json.

Your reconciliation tool at /app/reconcile.py must evaluate parameter discrepancies across registry records, returning exit code 0 for clean runs and exit code 1 for uncalibrated errors. When passed the --json-summary CLI flag, it must output a JSON summary containing overall findings before exiting. Finally, audit the registry and write the database migration file to /app/migrations/V1__reconciled_output.sql formatted with normalized parameter values and inline SHA256 integrity hashes.
"""

TEMPLATE_README_MD = """# Terminus 3 Starter Task Template

## Overview & Task Context

This starter template demonstrates the official **Terminus 3** task structure for Snorkel AI benchmark authoring. In Terminus 3, tasks run in isolated Docker containers with a separate verifier container mode (`environment_mode = "separate"`).

## System Architecture & File Components

1. **`task.toml`**: Configures task metadata, Terminus 3 difficulty tier (`frontier`), artifact paths array, and separate verifier environment mode.
2. **`instruction.md`**: Human-written conversational prose prompt provided to benchmark LLMs.
3. **`environment/Dockerfile`**: Digest-pinned Docker image with `tmux` and `asciinema` pre-installed.
4. **`solution/solve.sh`**: Executable Oracle reference solution script that achieves 1.000 reward score.
5. **`tests/Dockerfile`**: Verifier image Dockerfile containing `COPY . /tests`, `WORKDIR /tests`, and `pytest-json-ctrf`.
6. **`tests/test_outputs.py`**: Pytest assertions with 100% descriptive docstrings on all test functions.

## Local Testing Instructions

Test your task locally using the `stb` CLI tool:

```bash
# 1. Start interactive container environment
stb harbor tasks start-env -p . -i

# 2. Run Oracle Reference Solution (Expectation: 1.000 / PASS)
stb harbor run -a oracle -p .

# 3. Run Benchmark LLM Evaluation
stb harbor run -m @openai/gpt-5.5 -p . -k 5
stb harbor run -m @anthropic/claude-opus-4-8 -p . -k 5
```
"""

TEMPLATE_DOCKERFILE_ENV = """FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

WORKDIR /app

# Install required agent harness tools and system utilities
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        asciinema \\
        ca-certificates \\
        git \\
        tmux \\
    && rm -rf /var/lib/apt/lists/*

COPY data/ /app/data/
"""

TEMPLATE_DOCKERIGNORE = """.git
.gitignore
jobs/
logs/
output/
__pycache__/
.pytest_cache/
solution/
tests/
"""

TEMPLATE_DATA_TSV = """record_id	server_name	config_param	raw_value	status
101	srv-auth-01	max_connections	500	ACTIVE
102	srv-pay-02	connection_timeout	30	ACTIVE
103	srv-db-03	cache_size_mb	2048	ACTIVE
"""

TEMPLATE_SOLVE_SH = """#!/bin/bash
set -euo pipefail

mkdir -p /app/migrations

python3 - << 'PYEOF'
import json
import hashlib
import os

os.makedirs("/app/migrations", exist_ok=True)

# 1. Generate /app/reconciliation_report.json
report = {
    "status": "COMPLETED",
    "total_records": 3,
    "reconciled_records": 3,
    "audit_summary": {
        "valid_servers": 3,
        "flagged_servers": 0
    }
}

with open("/app/reconciliation_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

# 2. Generate /app/migrations/V1__reconciled_output.sql
sql_statements = [
    "UPDATE sys_config SET max_connections = 500 WHERE server_name = 'srv-auth-01';",
    "UPDATE sys_config SET connection_timeout = 30 WHERE server_name = 'srv-pay-02';",
    "UPDATE sys_config SET cache_size_mb = 2048 WHERE server_name = 'srv-db-03';"
]

output_lines = []
for stmt in sql_statements:
    csum = hashlib.sha256(stmt.encode("utf-8")).hexdigest()
    output_lines.append(f"{stmt} -- SHA256:{csum}")

with open("/app/migrations/V1__reconciled_output.sql", "w", encoding="utf-8") as f:
    f.write("\\n".join(output_lines) + "\\n")

print("Oracle solution executed successfully!")
PYEOF
"""

TEMPLATE_TESTS_DOCKERFILE = """FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        ca-certificates \\
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

# Pre-create parent directories for artifacts declared in task.toml
RUN mkdir -p /app/migrations /app

COPY . /tests
WORKDIR /tests
"""

TEMPLATE_TEST_SH = """#!/bin/bash
set -uo pipefail

mkdir -p /logs/verifier

python3 -m pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
rc=$?

if [ "$rc" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
"""

TEMPLATE_TEST_OUTPUTS_PY = """\"\"\"Tests for Terminus 3 Starter Reconciliation Task.\"\"\"
import json
import hashlib
from pathlib import Path
import pytest


def test_reconciliation_report_exists_and_valid():
    \"\"\"Verify that /app/reconciliation_report.json exists and contains COMPLETED audit status.\"\"\"
    report_path = Path("/app/reconciliation_report.json")
    assert report_path.exists(), "Reconciliation report /app/reconciliation_report.json does not exist"
    
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data.get("status") == "COMPLETED", "Report status must be COMPLETED"
    assert data.get("total_records") == 3, "Expected 3 total records"
    assert data.get("reconciled_records") == 3, "Expected 3 reconciled records"


def test_sql_migration_integrity_and_hashes():
    \"\"\"Verify that /app/migrations/V1__reconciled_output.sql exists with valid inline SHA256 hashes.\"\"\"
    sql_path = Path("/app/migrations/V1__reconciled_output.sql")
    assert sql_path.exists(), "SQL migration file /app/migrations/V1__reconciled_output.sql does not exist"
    
    lines = sql_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3, f"Expected 3 SQL UPDATE statements, got {len(lines)}"
    
    for idx, line in enumerate(lines):
        assert "-- SHA256:" in line, f"Line {idx+1} missing inline SHA256 hash comment"
        stmt_part, csum_part = line.split(" -- SHA256:")
        expected_hash = hashlib.sha256(stmt_part.encode("utf-8")).hexdigest()
        assert csum_part == expected_hash, f"Line {idx+1} SHA256 checksum mismatch"
"""

def generate_terminus3_starter_zip_bytes():
    """Build in-memory ZIP archive of clean Terminus 3 starter task template."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr("task.toml", TEMPLATE_TASK_TOML)
        z.writestr("instruction.md", TEMPLATE_INSTRUCTION_MD)
        z.writestr("README.md", TEMPLATE_README_MD)
        z.writestr("environment/Dockerfile", TEMPLATE_DOCKERFILE_ENV)
        z.writestr("environment/.dockerignore", TEMPLATE_DOCKERIGNORE)
        z.writestr("environment/data/system_audit_log.tsv", TEMPLATE_DATA_TSV)
        z.writestr("solution/solve.sh", TEMPLATE_SOLVE_SH)
        z.writestr("tests/Dockerfile", TEMPLATE_TESTS_DOCKERFILE)
        z.writestr("tests/test.sh", TEMPLATE_TEST_SH)
        z.writestr("tests/test_outputs.py", TEMPLATE_TEST_OUTPUTS_PY)
    buffer.seek(0)
    return buffer.getvalue()
