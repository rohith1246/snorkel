import os
import re
import zipfile
import tempfile
import shutil
import pathlib
import ast
try:
    import tomllib
except ImportError:
    import tomli as tomllib

CANONICAL_BASE_IMAGES = [
    "public.ecr.aws/docker/library/python:3.13-slim-bookworm",
    "public.ecr.aws/docker/library/python:3.11-slim-bookworm",
    "public.ecr.aws/docker/library/node:22-bookworm-slim",
    "public.ecr.aws/docker/library/golang:1.24-bookworm",
    "public.ecr.aws/docker/library/rust:1.85-slim",
    "public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy",
    "public.ecr.aws/docker/library/gcc:13-bookworm",
    "public.ecr.aws/docker/library/ruby:3.3-slim-bookworm",
    "public.ecr.aws/docker/library/maven:3.9.9-eclipse-temurin-21",
    "public.ecr.aws/docker/library/debian:bookworm-slim",
    "public.ecr.aws/docker/library/ubuntu:24.04"
]

class SnorkelTaskValidator:
    def __init__(self, zip_path):
        self.zip_path = zip_path
        self.temp_dir = tempfile.mkdtemp(prefix="snorkel_audit_")
        self.results = {
            "task_name": "unknown",
            "score": 100,
            "passed_checks": 0,
            "failed_checks": 0,
            "warning_checks": 0,
            "checks": [],
            "file_tree": [],
            "summary": ""
        }

    def cleanup(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def add_check(self, check_id, name, category, status, message, details=None, suggestion=None):
        if status == 'PASS':
            self.results["passed_checks"] += 1
        elif status == 'FAIL':
            self.results["failed_checks"] += 1
            self.results["score"] -= 15
        elif status == 'WARN':
            self.results["warning_checks"] += 1
            self.results["score"] -= 5

        self.results["checks"].append({
            "id": check_id,
            "name": name,
            "category": category,
            "status": status,
            "message": message,
            "details": details or "",
            "suggestion": suggestion or ""
        })

    def run_audit(self):
        try:
            # 1. Unpack ZIP & Check Clean Layout
            with zipfile.ZipFile(self.zip_path, 'r') as z:
                z.extractall(self.temp_dir)
                namelist = z.namelist()

            # Check for illegal directories in ZIP (jobs/, output/, __pycache__)
            illegal_dirs = [n for n in namelist if n.startswith(('jobs/', 'output/', 'tests/__pycache__/')) or '/__pycache__/' in n]
            if illegal_dirs:
                self.add_check(
                    "ZIP_CLEANLINESS", "ZIP Artifact Isolation & Cleanliness", "Packaging", "FAIL",
                    f"ZIP archive contains temporary runtime/cache directories: {set([n.split('/')[0] for n in illegal_dirs])}",
                    details="ZIP archives must NOT contain jobs/, output/, or __pycache__/ folders.",
                    suggestion="Purge jobs/, output/, and __pycache__/ before creating final ZIP archive."
                )
            else:
                self.add_check("ZIP_CLEANLINESS", "ZIP Artifact Isolation & Cleanliness", "Packaging", "PASS", "ZIP archive is clean and free of runtime/cache directories.")

            # Determine task root
            top_level_dirs = {name.split('/')[0] for name in namelist if '/' in name}
            has_root_files = any('/' not in name for name in namelist if name)
            
            if not has_root_files and len(top_level_dirs) == 1:
                nested_folder = list(top_level_dirs)[0]
                self.task_root = os.path.join(self.temp_dir, nested_folder)
                self.add_check(
                    "ZIP_STRUCTURE", "ZIP Package File Nesting", "Packaging", "WARN",
                    f"Task files are nested inside a subfolder '{nested_folder}' in the ZIP archive.",
                    details="Per Snorkel Platform rules, select individual files inside your task folder when compressing, rather than compressing the containing parent folder.",
                    suggestion="Compress files directly from inside your task folder (Select All -> Compress)."
                )
            else:
                self.task_root = self.temp_dir
                self.add_check(
                    "ZIP_STRUCTURE", "ZIP Package File Nesting", "Packaging", "PASS",
                    "Task files are correctly packaged directly at the root of the ZIP archive."
                )

            self._build_file_tree()

            # 2. Audit task.toml
            task_toml_data = self._audit_task_toml()

            number_of_milestones = 0
            if task_toml_data and "metadata" in task_toml_data:
                number_of_milestones = task_toml_data["metadata"].get("number_of_milestones", 0)

            is_milestone = number_of_milestones >= 2

            # 3. Audit File Architecture & Humanized instruction.md Prompt Styling
            self._audit_file_architecture(is_milestone, number_of_milestones)
            self._audit_instruction_styling()

            # 4. Audit Dockerfile & Environment
            self._audit_dockerfile()

            # 5. Audit Solution & Tests (Strict CTRF plugin, docstrings, & Oracle execution alignment)
            self._audit_solution_and_tests(is_milestone, number_of_milestones)

            # Final Score Normalization
            self.results["score"] = max(0, min(100, self.results["score"]))
            
            if self.results["failed_checks"] == 0 and self.results["warning_checks"] == 0:
                self.results["summary"] = "Task is 100% compliant with Snorkel Platform & STB Harbor standards!"
            elif self.results["failed_checks"] == 0:
                self.results["summary"] = f"Task passed with {self.results['warning_checks']} minor warnings."
            else:
                self.results["summary"] = f"Task has {self.results['failed_checks']} critical errors and {self.results['warning_checks']} warnings."

            return self.results
        finally:
            self.cleanup()

    def _build_file_tree(self):
        file_tree = []
        for root, dirs, files in os.walk(self.task_root):
            rel_root = os.path.relpath(root, self.task_root)
            for f in files:
                rel_path = f if rel_root == "." else os.path.join(rel_root, f)
                file_tree.append(rel_path.replace("\\", "/"))
        self.results["file_tree"] = sorted(file_tree)

    def _audit_task_toml(self):
        task_toml_path = os.path.join(self.task_root, "task.toml")
        if not os.path.exists(task_toml_path):
            self.add_check(
                "TASK_TOML_EXISTS", "task.toml Configuration File", "Metadata", "FAIL",
                "Missing required task.toml configuration file at task root.",
                suggestion="Create a task.toml file adhering to Snorkel schema v2.0."
            )
            return None

        try:
            with open(task_toml_path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            self.add_check(
                "TASK_TOML_PARSING", "task.toml Syntax & Schema", "Metadata", "FAIL",
                f"Failed to parse task.toml: {str(e)}",
                suggestion="Ensure task.toml contains valid TOML syntax."
            )
            return None

        version = data.get("version")
        if version == "2.0":
            self.add_check("SCHEMA_VERSION", "Top-level Schema Version", "Metadata", "PASS", "Schema version is set to '2.0'.")
        else:
            self.add_check("SCHEMA_VERSION", "Top-level Schema Version", "Metadata", "FAIL",
                           f"Invalid schema version '{version}'. Must be '2.0'.",
                           suggestion="Set `version = \"2.0\"` at the top level of task.toml.")

        self.results["task_name"] = data.get("name", os.path.basename(self.task_root))

        meta = data.get("metadata", {})
        required_meta_keys = ["author_name", "author_email", "difficulty", "category", "subcategories", "codebase_size", "languages", "tags"]
        missing_keys = [k for k in required_meta_keys if k not in meta]
        
        if not missing_keys:
            self.add_check("METADATA_SECTION", "[metadata] Section Compliance", "Metadata", "PASS", "All required [metadata] fields are present.")
        else:
            self.add_check("METADATA_SECTION", "[metadata] Section Compliance", "Metadata", "FAIL",
                           f"Missing metadata fields: {', '.join(missing_keys)}",
                           suggestion=f"Add missing fields to [metadata]: {missing_keys}")

        # Check difficulty enum validity
        difficulty_val = str(meta.get("difficulty", "")).strip().lower()
        valid_difficulties = ["easy", "medium", "hard"]
        if difficulty_val in valid_difficulties:
            self.add_check("DIFFICULTY_ENUM_VALID", "Task Difficulty Value Compliance", "Metadata", "PASS", f"Difficulty is valid ('{difficulty_val}').")
        else:
            self.add_check(
                "DIFFICULTY_ENUM_VALID", "Task Difficulty Value Compliance", "Metadata", "FAIL",
                f"Invalid difficulty '{meta.get('difficulty')}'. Allowed schema v2.0 values are: {valid_difficulties}.",
                details="Per Snorkel schema v2.0, difficulty must be exactly one of 'easy', 'medium', or 'hard'. Custom strings like 'excellent' break STB Harbor evaluation.",
                suggestion="Change metadata difficulty in task.toml to 'easy', 'medium', or 'hard'."
            )

        for sec in ["verifier", "agent", "environment"]:
            if sec in data:
                self.add_check(f"SECTION_{sec.upper()}", f"[{sec}] Configuration Section", "Metadata", "PASS", f"[{sec}] section present.")
            else:
                self.add_check(f"SECTION_{sec.upper()}", f"[{sec}] Configuration Section", "Metadata", "FAIL",
                               f"Missing [{sec}] section in task.toml.",
                               suggestion=f"Define the [{sec}] section in task.toml.")

        env_sec = data.get("environment", {})
        if "allow_internet" in env_sec:
            if env_sec["allow_internet"] is True:
                self.add_check("ALLOW_INTERNET", "Internet Access Setting", "Metadata", "WARN",
                               "allow_internet is set to true. Ensure task genuinely requires internet access.",
                               suggestion="Keep allow_internet = false unless retrieving live web info or large un-bundled models.")
            else:
                self.add_check("ALLOW_INTERNET", "Internet Access Setting", "Metadata", "PASS", "allow_internet is set to false (offline compliant).")

        return data

    def _audit_file_architecture(self, is_milestone, number_of_milestones):
        if is_milestone:
            self.add_check("MILESTONE_TASK", "Milestone Task Layout Detected", "Architecture", "PASS",
                           f"Task has {number_of_milestones} milestones. Validating steps/milestone_N structure.")
            
            root_prohibited = ["instruction.md", "tests", "solution"]
            found_prohibited = [p for p in root_prohibited if os.path.exists(os.path.join(self.task_root, p))]
            if found_prohibited:
                self.add_check(
                    "MILESTONE_ROOT_FILES", "Milestone Prohibited Root Files", "Architecture", "FAIL",
                    f"Milestone task contains root-level items: {', '.join(found_prohibited)}.",
                    suggestion="Remove root instruction.md, tests/, and solution/. Milestone files belong under steps/milestone_N/."
                )
            else:
                self.add_check("MILESTONE_ROOT_FILES", "Milestone Prohibited Root Files", "Architecture", "PASS",
                               "No prohibited root-level instruction or test files found.")

            for i in range(1, number_of_milestones + 1):
                m_dir = os.path.join(self.task_root, "steps", f"milestone_{i}")
                if not os.path.exists(m_dir):
                    self.add_check(
                        f"MILESTONE_{i}_DIR", f"Milestone {i} Directory", "Architecture", "FAIL",
                        f"Missing required milestone directory: steps/milestone_{i}/",
                        suggestion=f"Create directory `steps/milestone_{i}/` containing instruction.md, solution/, tests/."
                    )
                else:
                    req_m_files = ["instruction.md", "solution/solve.sh", f"solution/solve{i}.sh", "tests/test.sh", f"tests/test_m{i}.py"]
                    missing_m = [f for f in req_m_files if not os.path.exists(os.path.join(m_dir, f))]
                    if missing_m:
                        self.add_check(
                            f"MILESTONE_{i}_FILES", f"Milestone {i} File Suite", "Architecture", "FAIL",
                            f"Milestone {i} missing files: {', '.join(missing_m)}",
                            suggestion=f"Add missing milestone files: {missing_m}"
                        )
                    else:
                        self.add_check(f"MILESTONE_{i}_FILES", f"Milestone {i} File Suite", "Architecture", "PASS", f"Milestone {i} contains all required files.")
        else:
            req_root_files = {
                "instruction.md": "Task Instructions File",
                "environment/Dockerfile": "Environment Dockerfile",
                "solution/solve.sh": "Oracle Solution Script",
                "tests/test.sh": "Verifier Test Runner",
                "tests/test_outputs.py": "Pytest Assertion Suite"
            }
            for rel_path, desc in req_root_files.items():
                full_p = os.path.join(self.task_root, rel_path)
                if os.path.exists(full_p):
                    self.add_check(f"FILE_{rel_path.replace('/', '_')}", desc, "Architecture", "PASS", f"Found required file `{rel_path}`.")
                else:
                    self.add_check(f"FILE_{rel_path.replace('/', '_')}", desc, "Architecture", "FAIL", f"Missing required file `{rel_path}`.",
                                   suggestion=f"Create `{rel_path}` according to task component specifications.")

    def _audit_instruction_styling(self):
        inst_path = os.path.join(self.task_root, "instruction.md")
        if not os.path.exists(inst_path):
            return

        with open(inst_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        # Check for headings (#, ##, ###)
        has_headings = bool(re.search(r'^\s*#{1,6}\s+', content, re.MULTILINE))
        # Check for bullet lists (- item, * item, 1. item)
        has_bullets = bool(re.search(r'^\s*[-*]\s+|\^\s*\d+\.\s+', content, re.MULTILINE))
        # Check for tables (|---|)
        has_tables = "|" in content and "---" in content

        # STRICT PROMPT STYLING RULE: Accept 1 to 5 paragraphs of clean, humanized, conversational prose!
        if has_headings or has_bullets or has_tables or len(paragraphs) < 1 or len(paragraphs) > 5:
            violations = []
            if has_headings: violations.append("contains Markdown Headings (#, ##)")
            if has_bullets: violations.append("contains Bullet Lists (- or 1.)")
            if has_tables: violations.append("contains Markdown Tables (|---)")
            if len(paragraphs) < 1 or len(paragraphs) > 5: violations.append(f"has {len(paragraphs)} paragraphs (must be 1–5 paragraphs)")

            self.add_check(
                "INSTRUCTION_STYLING", "instruction.md Humanized Prose Styling", "Documentation", "FAIL",
                f"instruction.md violates prompt styling guidelines: {', '.join(violations)}.",
                details="Per Snorkel prompt guidelines, instruction.md must be 1–5 paragraphs of clean, humanized, conversational prose without headings, tables, or bullet lists.",
                suggestion="Rewrite instruction.md into 1–5 paragraphs of clean, humanized conversational text without headings, bullets, or tables."
            )
        else:
            self.add_check(
                "INSTRUCTION_STYLING", "instruction.md Humanized Prose Styling", "Documentation", "PASS",
                f"instruction.md is formatted in clean, humanized conversational prose ({len(paragraphs)} paragraph(s), no headings/tables/bullets)."
            )

    def _audit_dockerfile(self):
        dockerfile_path = os.path.join(self.task_root, "environment", "Dockerfile")
        if not os.path.exists(dockerfile_path):
            return

        with open(dockerfile_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        lines = content.splitlines()

        from_lines = [l for l in lines if l.strip().startswith("FROM")]
        unpinned_from = [fl for fl in from_lines if "@sha256:" not in fl]

        if unpinned_from:
            self.add_check(
                "DOCKER_PINNED_IMAGES", "Dockerfile Base Image Digest Pinning", "Docker", "FAIL",
                f"Unpinned base image FROM lines: {', '.join(unpinned_from)}",
                details="Every FROM line in environment/Dockerfile must be digest-pinned using @sha256:<digest>.",
                suggestion="Add @sha256:<digest> to every FROM image statement."
            )
        else:
            self.add_check("DOCKER_PINNED_IMAGES", "Dockerfile Base Image Digest Pinning", "Docker", "PASS", "All FROM lines use @sha256:<digest> digest pinning.")

        final_from = from_lines[-1] if from_lines else ""
        is_canonical = any(canon in final_from for canon in CANONICAL_BASE_IMAGES)
        has_justification_comment = any(line.strip().startswith("# Base Image Justification:") or line.strip().startswith("# Justification:") for line in lines)
        
        if is_canonical:
            self.add_check("DOCKER_SANCTIONED_BASE", "Sanctioned Canonical Base Image", "Docker", "PASS", "Final runtime image uses a canonical Terminal-Bench base image.")
        elif has_justification_comment:
            self.add_check("DOCKER_SANCTIONED_BASE", "Sanctioned Canonical Base Image", "Docker", "PASS", "Non-canonical base image includes written justification comment.")
        else:
            self.add_check(
                "DOCKER_SANCTIONED_BASE", "Sanctioned Canonical Base Image", "Docker", "FAIL",
                f"Non-canonical base image `{final_from}` without written justification comment.",
                suggestion="Use a canonical Terminal-Bench base image or add a '# Base Image Justification:' comment above the FROM line."
            )

        has_tmux = "tmux" in content
        has_asciinema = "asciinema" in content
        if has_tmux and has_asciinema:
            self.add_check("DOCKER_AGENT_TOOLS", "Agent Harness Tools (tmux & asciinema)", "Docker", "PASS", "tmux and asciinema are installed in Dockerfile.")
        else:
            missing_tools = []
            if not has_tmux: missing_tools.append("tmux")
            if not has_asciinema: missing_tools.append("asciinema")
            self.add_check(
                "DOCKER_AGENT_TOOLS", "Agent Harness Tools (tmux & asciinema)", "Docker", "FAIL",
                f"Dockerfile is missing required agent tools: {', '.join(missing_tools)}.",
                details="Missing tmux or asciinema will cause agent runs to fail silently with no verifier output.",
                suggestion=f"Install {missing_tools} in environment/Dockerfile via apt-get."
            )

        if re.search(r'COPY\s+.*\bsolution\b', content) or re.search(r'COPY\s+.*\btests\b', content):
            self.add_check(
                "SOL_TESTS_IN_IMAGE", "Solution/Tests Isolation in Dockerfile", "Docker", "FAIL",
                "Dockerfile explicitly copies solution/ or tests/ directory into the image.",
                suggestion="Remove any COPY statements referencing solution/ or tests/ from environment/Dockerfile."
            )
        else:
            self.add_check("SOL_TESTS_IN_IMAGE", "Solution/Tests Isolation in Dockerfile", "Docker", "PASS", "No solution or test files are copied into the Docker runtime image.")

        env_dir = os.path.join(self.task_root, "environment")
        total_size_mb = 0
        large_files = []
        for root, _, files in os.walk(env_dir):
            for f in files:
                fp = os.path.join(root, f)
                sz_mb = os.path.getsize(fp) / (1024 * 1024)
                total_size_mb += sz_mb
                if sz_mb > 50:
                    large_files.append((f, round(sz_mb, 1)))

        if total_size_mb > 100 or large_files:
            self.add_check(
                "DOCKER_CONTEXT_SIZE", "Build Context & File Size Limits", "Docker", "FAIL",
                f"environment/ total size is {round(total_size_mb, 1)} MiB (max 100 MiB). Large files over 50 MiB: {large_files}",
                suggestion="Keep environment/ under 100 MiB total and all files under 50 MiB."
            )
        else:
            self.add_check("DOCKER_CONTEXT_SIZE", "Build Context & File Size Limits", "Docker", "PASS", f"environment/ size ({round(total_size_mb, 1)} MiB) is within limits.")

        dockerignore_path = os.path.join(self.task_root, "environment", ".dockerignore")
        if os.path.exists(dockerignore_path):
            self.add_check("DOCKERIGNORE_CHECK", ".dockerignore File Presence", "Docker", "PASS", ".dockerignore file exists in environment/.")
        else:
            self.add_check("DOCKERIGNORE_CHECK", ".dockerignore File Presence", "Docker", "WARN", "Missing .dockerignore file in environment/.",
                           suggestion="Create environment/.dockerignore ignoring .git, solution/, tests/, node_modules, etc.")

    def _audit_solution_and_tests(self, is_milestone, number_of_milestones):
        test_req_path = os.path.join(self.task_root, "tests", "requirements.txt")
        if os.path.exists(test_req_path):
            self.add_check("TEST_DEPS_SEPARATION", "Test-Only Dependencies Separation", "Testing", "PASS", "Separate tests/requirements.txt present for verifier dependencies.")
        else:
            self.add_check("TEST_DEPS_SEPARATION", "Test-Only Dependencies Separation", "Testing", "WARN",
                           "Missing tests/requirements.txt.",
                           suggestion="Store test dependencies (pytest, pytest-json-ctrf) in tests/requirements.txt.")

        dockerfile_path = os.path.join(self.task_root, "environment", "Dockerfile")
        dockerfile_content = ""
        if os.path.exists(dockerfile_path):
            with open(dockerfile_path, "r", encoding="utf-8", errors="ignore") as f:
                dockerfile_content = f.read()

        test_sh_path = os.path.join(self.task_root, "tests", "test.sh")
        if os.path.exists(test_sh_path):
            with open(test_sh_path, "r", encoding="utf-8", errors="ignore") as f:
                t_content = f.read()

            # NEW DEEP CHECK 1: Ensure tests/test.sh explicitly runs solution/solve.sh BEFORE running pytest!
            runs_solution = any(kw in t_content for kw in ["solve.sh", "solve.py", "solution/solve", "reconciler.py"])
            if not runs_solution:
                self.add_check(
                    "ORACLE_SOLUTION_EXECUTION", "Verifier Reference Solution Invocation", "Testing", "FAIL",
                    "tests/test.sh does NOT execute the reference solution (solution/solve.sh) before running pytest assertions.",
                    details="Running pytest without first executing solution/solve.sh will cause the verifier to find missing output files or unhandled code states, resulting in a 0.000 Oracle score.",
                    suggestion="Add `bash solution/solve.sh` (or `bash /app/solution/solve.sh`) before pytest execution in tests/test.sh."
                )
            else:
                self.add_check(
                    "ORACLE_SOLUTION_EXECUTION", "Verifier Reference Solution Invocation", "Testing", "PASS",
                    "tests/test.sh explicitly executes the reference solution before running pytest assertions."
                )

            if "pip install" in t_content or "apt-get" in t_content:
                self.add_check(
                    "TEST_SH_OFFLINE", "Offline Test Execution Policy", "Testing", "FAIL",
                    "tests/test.sh attempts network downloads (pip install / apt-get) at runtime.",
                    details="All verifier test dependencies must be pre-baked into the Docker image during build.",
                    suggestion="Remove pip install / network commands from tests/test.sh and install dependencies in Dockerfile."
                )
            else:
                self.add_check("TEST_SH_OFFLINE", "Offline Test Execution Policy", "Testing", "PASS", "tests/test.sh executes offline without runtime package installation.")

            if "--ctrf" in t_content:
                # Check if pytest-json-ctrf is installed in Dockerfile or tests/requirements.txt
                has_ctrf_installed = "pytest-json-ctrf" in dockerfile_content or (os.path.exists(test_req_path) and "pytest-json-ctrf" in open(test_req_path).read())
                if not has_ctrf_installed:
                    self.add_check(
                        "TEST_CTRF_INSTALLED", "pytest-json-ctrf Package Installation", "Testing", "FAIL",
                        "tests/test.sh uses --ctrf flag but pytest-json-ctrf is missing from environment/Dockerfile.",
                        details="Using --ctrf without pytest-json-ctrf causes pytest to fail with 'unrecognized arguments: --ctrf' resulting in 0.000 reward.",
                        suggestion="Add `pytest-json-ctrf==0.3.5` to pip install command in environment/Dockerfile."
                    )
                else:
                    self.add_check("TEST_CTRF_INSTALLED", "pytest-json-ctrf Package Installation", "Testing", "PASS", "pytest-json-ctrf package is pre-baked in environment/Dockerfile.")

            if "--ctrf" in t_content and "/logs/verifier/reward.txt" in t_content:
                self.add_check("TEST_SH_CTRF", "Verifier CTRF Reporting & Reward Output", "Testing", "PASS", "test.sh generates CTRF JSON log and writes /logs/verifier/reward.txt.")
            else:
                self.add_check("TEST_SH_CTRF", "Verifier CTRF Reporting & Reward Output", "Testing", "WARN",
                               "tests/test.sh should use `--ctrf /logs/verifier/ctrf.json` and write `1` or `0` to `/logs/verifier/reward.txt`.",
                               suggestion="Update test.sh to execute pytest with CTRF reporting and write reward score.")

            # Check if set -e is active before pytest without set +e
            lines_test = [l.strip() for l in t_content.splitlines()]
            pytest_idx = -1
            set_e_before_pytest = False
            set_plus_e_before_pytest = False

            for i, line in enumerate(lines_test):
                if "pytest" in line:
                    pytest_idx = i
                    break

            if pytest_idx != -1:
                prev_lines = lines_test[:pytest_idx]
                for pl in prev_lines:
                    if pl.startswith("set -e") or "set -euo pipefail" in pl or "set -e" in pl:
                        set_e_before_pytest = True
                    if "set +e" in pl:
                        set_plus_e_before_pytest = True

            if set_e_before_pytest and not set_plus_e_before_pytest:
                self.add_check(
                    "TEST_SH_REWARD_RELIABILITY", "Verifier Reward File Writing Reliability", "Testing", "FAIL",
                    "tests/test.sh uses `set -e` before `pytest` without disabling it via `set +e`.",
                    details="When `set -e` is active during pytest execution, if pytest returns a non-zero exit code (test failure), bash exits immediately before writing `/logs/verifier/reward.txt`, causing Harbor to throw `RewardFileNotFoundError`.",
                    suggestion="Add `set +e` right before `pytest` in tests/test.sh, capture `$?`, and write reward score before exiting."
                )
            else:
                self.add_check("TEST_SH_REWARD_RELIABILITY", "Verifier Reward File Writing Reliability", "Testing", "PASS", "test.sh safely handles pytest exit codes without suppressing reward file creation.")

        # NEW DEEP CHECK 2: Parse Python AST in solution/ files for syntax errors
        sol_dir = os.path.join(self.task_root, "solution")
        py_code_to_check = ""
        if os.path.exists(sol_dir):
            for root, _, files in os.walk(sol_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    if f.endswith(".py"):
                        with open(fp, "r", encoding="utf-8", errors="ignore") as pf:
                            py_code_to_check += "\n" + pf.read()
                    elif f.endswith(".sh"):
                        with open(fp, "r", encoding="utf-8", errors="ignore") as sf:
                            sh_text = sf.read()
                            m = re.search(r"python3?\s+-\s+<<\s*['\"]?PYEOF['\"]?\n(.*?)PYEOF", sh_text, re.DOTALL)
                            if m:
                                py_code_to_check += "\n" + m.group(1)

        if py_code_to_check.strip():
            try:
                ast.parse(py_code_to_check)
                self.add_check("ORACLE_PYTHON_SYNTAX", "Oracle Python Solution Syntax Validation", "Solution", "PASS", "Oracle solution Python code has valid syntax without syntax errors.")
            except SyntaxError as se:
                self.add_check(
                    "ORACLE_PYTHON_SYNTAX", "Oracle Python Solution Syntax Validation", "Solution", "FAIL",
                    f"Oracle solution Python code contains a SyntaxError: {se.msg} (line {se.lineno}).",
                    details="Syntax errors in solve.py or solve.sh cause the Oracle solution to fail with exit code 1 during STB Harbor evaluation.",
                    suggestion="Fix the syntax error in solution/solve.py or solution/solve.sh (e.g. unescaped string literal or quotes)."
                )

        # Audit test_outputs.py docstrings & output file matching
        test_py_path = os.path.join(self.task_root, "tests", "test_outputs.py")
        if os.path.exists(test_py_path):
            with open(test_py_path, "r", encoding="utf-8", errors="ignore") as f:
                py_content = f.read()

            test_funcs = re.findall(r'def (test_\w+)\s*\(', py_content)
            missing_docstrings = []
            for func in test_funcs:
                func_match = re.search(r'def ' + func + r'\s*\([^)]*\):(?:\s*\n)+([ \t]*["\']{3})', py_content)
                if not func_match:
                    missing_docstrings.append(func)

            if missing_docstrings:
                self.add_check(
                    "TEST_DOCSTRINGS", "Pytest Function Docstrings", "Testing", "FAIL",
                    f"Test functions in test_outputs.py missing docstrings: {', '.join(missing_docstrings)}.",
                    details="Per Snorkel quality guidelines, every test function in test_outputs.py must include a clear and descriptive docstring.",
                    suggestion=f"Add descriptive docstrings (\"\"\"...\"\"\") to test functions: {missing_docstrings}"
                )
            else:
                self.add_check(
                    "TEST_DOCSTRINGS", "Pytest Function Docstrings", "Testing", "PASS",
                    f"All {len(test_funcs)} test functions in test_outputs.py have clear and descriptive docstrings."
                )

            # NEW DEEP CHECK 3: Check matching output file paths between test_outputs.py and solution directory
            expected_json_files = set(re.findall(r'[\'"](/app/[^\'"]+\.json)[\'"]', py_content) + re.findall(r'[\'"]([a-zA-Z0-9_\-]+\.json)[\'"]', py_content))
            solution_text = py_code_to_check
            if os.path.exists(sol_dir):
                for root, _, files in os.walk(sol_dir):
                    for f in files:
                        fp = os.path.join(root, f)
                        with open(fp, "r", encoding="utf-8", errors="ignore") as sf:
                            solution_text += "\n" + sf.read()

            mismatched_outputs = []
            for ef in expected_json_files:
                fname = os.path.basename(ef)
                if fname not in solution_text and fname not in ["ctrf.json", "reward.txt"]:
                    mismatched_outputs.append(fname)

            if mismatched_outputs:
                self.add_check(
                    "ORACLE_FILE_PATH_ALIGNMENT", "Verifier Output Path Alignment", "Solution", "FAIL",
                    f"Output JSON file(s) expected by test_outputs.py not written by solution: {mismatched_outputs}.",
                    details="If test_outputs.py asserts an output file (e.g. resolution_plan.json) but solution/solve.sh writes a different filename (e.g. resolved_pipeline.json), Oracle evaluation will fail with score 0.000.",
                    suggestion=f"Ensure solution/solve.sh writes to the exact output file paths asserted in tests/test_outputs.py: {mismatched_outputs}"
                )
            else:
                self.add_check(
                    "ORACLE_FILE_PATH_ALIGNMENT", "Verifier Output Path Alignment", "Solution", "PASS",
                    "Output file paths asserted by tests/test_outputs.py match the solution implementation."
                )

        solve_sh_path = os.path.join(self.task_root, "solution", "solve.sh")
        if os.path.exists(solve_sh_path):
            with open(solve_sh_path, "r", encoding="utf-8", errors="ignore") as f:
                s_content = f.read()

            if "set -e" in s_content or "set -euo pipefail" in s_content:
                self.add_check("SOLVE_SH_DETERMINISM", "Oracle Solution Determinism", "Solution", "PASS", "solve.sh includes strict error handling (`set -e` or `set -euo pipefail`).")
            else:
                self.add_check("SOLVE_SH_DETERMINISM", "Oracle Solution Determinism", "Solution", "WARN", "solve.sh should include `set -euo pipefail` for fail-fast execution.",
                               suggestion="Add `set -euo pipefail` to the top of solution/solve.sh.")
