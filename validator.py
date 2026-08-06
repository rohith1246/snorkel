import os
import re
import zipfile
import tempfile
import shutil
import pathlib
import ast
import json

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

# Official Terminus 3 Taxonomy (Title Case)
TAXONOMY = {
    "Science": ["Biology", "Chemistry", "Physics", "Earth", "Robotics", "Math", "Linguistics"],
    "Software": ["Algorithms", "Systems", "Databases", "Data engineering", "Frontend", "Languages"],
    "ML": ["Training", "Inference", "Evaluation", "Kernels"],
    "Operations": ["Finance", "Logistics", "Supply chain", "Claims", "Compliance", "Marketing"],
    "Security": ["Cryptography", "Reverse engineering", "Forensics", "AppSec"],
    "Hardware": ["CAD", "RTL"],
    "Media": ["Music", "Design"]
}

DIFFICULTY_TIERS = ["frontier", "advanced", "core", "base"]

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
    "public.ecr.aws/docker/library/ubuntu:24.04",
    "python:3.13-slim-bookworm",
    "python:3.11-slim-bookworm",
    "node:22-bookworm-slim",
    "golang:1.24-bookworm",
    "rust:1.85-slim",
    "ubuntu:24.04",
    "debian:bookworm-slim"
]

REMOVED_FIELDS = [
    "codebase_size", "number_of_milestones", "allow_internet",
    "junior_time_estimate_min", "expert_time_estimate_min", "subcategories"
]

EXPLANATION_FIELDS = [
    "difficulty_explanation", "solution_explanation",
    "verification_explanation", "relevant_experience"
]


class SnorkelTaskValidator:
    def __init__(self, zip_path):
        self.zip_path = zip_path
        self.temp_dir = tempfile.mkdtemp(prefix="snorkel_audit_")
        self.task_root = self.temp_dir
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

    def _find_file_path(self, rel_path):
        """Locates file cross-platform using multi-stage resolution."""
        p1 = os.path.join(self.task_root, rel_path.replace("/", os.sep))
        if os.path.exists(p1): return p1
        p2 = os.path.join(self.task_root, rel_path)
        if os.path.exists(p2): return p2
        p3 = os.path.join(self.temp_dir, rel_path.replace("/", os.sep))
        if os.path.exists(p3): return p3
        p4 = os.path.join(self.temp_dir, rel_path)
        if os.path.exists(p4): return p4

        target_norm = rel_path.replace("\\", "/").lower()
        for root, dirs, files in os.walk(self.temp_dir):
            for f in files:
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, self.temp_dir).replace("\\", "/").lower()
                if rel == target_norm or rel.endswith("/" + target_norm):
                    return fp
        return None

    def run_audit(self):
        try:
            # 1. Unpack ZIP & Inspect Layout
            try:
                with zipfile.ZipFile(self.zip_path, 'r') as z:
                    z.extractall(self.temp_dir)
                    namelist = z.namelist()
            except Exception as e:
                self.add_check(
                    "ZIP_CORRUPT", "ZIP Archive Validity", "Packaging", "FAIL",
                    f"Failed to extract ZIP archive: {str(e)}",
                    suggestion="Ensure the file is a valid, uncorrupted .zip archive."
                )
                self.results["score"] = 0
                return self.results

            # Check for forbidden runtime/cache directories
            illegal_dirs = [n for n in namelist if n.startswith(('jobs/', 'output/', 'tests/__pycache__/')) or '/__pycache__/' in n or '/.pytest_cache/' in n]
            if illegal_dirs:
                self.add_check(
                    "ZIP_CLEANLINESS", "ZIP Artifact Isolation & Cleanliness", "Packaging", "FAIL",
                    f"ZIP archive contains forbidden runtime/cache directories: {set([n.split('/')[0] for n in illegal_dirs])}",
                    details="ZIP archives must NOT contain jobs/, output/, __pycache__/, or .pytest_cache/ folders.",
                    suggestion="Purge jobs/, output/, and __pycache__/ before creating final ZIP archive."
                )
            else:
                self.add_check("ZIP_CLEANLINESS", "ZIP Artifact Isolation & Cleanliness", "Packaging", "PASS", "ZIP archive is clean and free of runtime/cache directories.")

            # Auto-locate task root by finding task.toml or instruction.md anywhere in extracted temp dir
            toml_rel_path = None
            for root, dirs, files in os.walk(self.temp_dir):
                if "task.toml" in files or "instruction.md" in files:
                    self.task_root = root
                    toml_rel_path = os.path.relpath(root, self.temp_dir).replace("\\", "/")
                    break

            if not self.task_root:
                self.task_root = self.temp_dir

            if toml_rel_path and toml_rel_path != ".":
                self.add_check(
                    "ZIP_STRUCTURE", "ZIP Package File Nesting", "Packaging", "WARN",
                    f"Task files are nested inside subfolder '{toml_rel_path}' in the ZIP archive.",
                    details="Per Snorkel Platform rules, select individual files inside your task folder when compressing.",
                    suggestion="Compress files directly from inside your task folder (Select All -> Compress)."
                )
            else:
                self.add_check(
                    "ZIP_STRUCTURE", "ZIP Package File Nesting", "Packaging", "PASS",
                    "Task files are correctly packaged directly at the root of the ZIP archive."
                )

            self._build_file_tree()

            # 2. Audit task.toml Schema & Metadata
            task_toml_data = None
            try:
                task_toml_data = self._audit_task_toml()
            except Exception as e:
                self.add_check("TASK_TOML_AUDIT_ERR", "task.toml Schema Auditor", "Metadata", "FAIL", f"Error auditing task.toml: {str(e)}")

            # 3. Audit Architecture & Humanized Prose Styling
            try:
                self._audit_file_architecture()
            except Exception as e:
                self.add_check("FILE_ARCH_AUDIT_ERR", "File Architecture Auditor", "Architecture", "FAIL", f"Error auditing file architecture: {str(e)}")

            try:
                self._audit_instruction_styling()
            except Exception as e:
                self.add_check("INSTRUCTION_AUDIT_ERR", "instruction.md Prompt Auditor", "Documentation", "FAIL", f"Error auditing instruction.md: {str(e)}")

            # 4. Audit Dockerfile & Environment
            try:
                self._audit_dockerfile()
            except Exception as e:
                self.add_check("DOCKERFILE_AUDIT_ERR", "Dockerfile Auditor", "Docker", "FAIL", f"Error auditing Dockerfile: {str(e)}")

            # 5. Audit Solution & Verifier Tests
            try:
                self._audit_solution_and_tests()
            except Exception as e:
                self.add_check("SOLUTION_TESTS_AUDIT_ERR", "Solution & Verifier Auditor", "Testing", "FAIL", f"Error auditing solution & tests: {str(e)}")

            # 6. Audit Rubrics
            try:
                self._audit_rubrics()
            except Exception as e:
                self.add_check("RUBRICS_AUDIT_ERR", "Rubrics Auditor", "Documentation", "FAIL", f"Error auditing rubrics.txt: {str(e)}")

            # 7. Audit Cross-Component Path Consistency
            try:
                self._audit_cross_consistency()
            except Exception as e:
                self.add_check("CROSS_CONSISTENCY_AUDIT_ERR", "Cross-Component Consistency Auditor", "Architecture", "FAIL", f"Error checking cross-component path consistency: {str(e)}")

            # Final Score Normalization
            self.results["score"] = max(0, min(100, self.results["score"]))
            
            if self.results["failed_checks"] == 0 and self.results["warning_checks"] == 0:
                self.results["summary"] = "Task is 100% compliant with Terminus 3 & Snorkel Platform standards!"
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
        task_toml_path = self._find_file_path("task.toml")
        if not task_toml_path:
            self.add_check(
                "TASK_TOML_EXISTS", "task.toml Configuration File", "Metadata", "FAIL",
                "Missing required task.toml configuration file at task root.",
                suggestion="Create a task.toml file adhering to Terminus 3 schema specifications."
            )
            return None

        data = {}
        try:
            with open(task_toml_path, "rb") as f:
                if tomllib:
                    data = tomllib.load(f)
                else:
                    data = self._parse_toml_fallback(f.read().decode("utf-8", errors="ignore"))
        except Exception as e:
            self.add_check(
                "TASK_TOML_PARSING", "task.toml Syntax & Schema", "Metadata", "FAIL",
                f"Failed to parse task.toml: {str(e)}",
                suggestion="Ensure task.toml contains valid TOML syntax."
            )
            return None

        self.results["task_name"] = data.get("name", os.path.basename(self.task_root))
        meta = data.get("metadata", {}) if isinstance(data.get("metadata"), dict) else {}

        # 1. Top-level fields check
        required_meta_keys = ["name", "category", "subcategory", "tags", "languages", "difficulty"]
        missing_keys = [k for k in required_meta_keys if k not in data and k not in meta]
        if not missing_keys:
            self.add_check("METADATA_SECTION", "Task Configuration Fields", "Metadata", "PASS", "All required metadata configuration fields are present.")
        else:
            self.add_check("METADATA_SECTION", "Task Configuration Fields", "Metadata", "FAIL",
                           f"Missing required configuration fields: {', '.join(missing_keys)}",
                           suggestion=f"Add missing fields to task.toml: {missing_keys}")

        # 2. Taxonomy Title Case Validation
        cat = data.get("category") or meta.get("category", "")
        sub = data.get("subcategory") or meta.get("subcategory", "")
        
        if cat in TAXONOMY:
            self.add_check("TAXONOMY_CATEGORY", "Terminus 3 Category Taxonomy", "Metadata", "PASS", f"Category '{cat}' matches Terminus 3 Title Case taxonomy.")
            valid_subs = TAXONOMY[cat]
            if sub in valid_subs:
                self.add_check("TAXONOMY_SUBCATEGORY", "Terminus 3 Subcategory Taxonomy", "Metadata", "PASS", f"Subcategory '{sub}' is valid for category '{cat}'.")
            else:
                self.add_check("TAXONOMY_SUBCATEGORY", "Terminus 3 Subcategory Taxonomy", "Metadata", "FAIL",
                               f"Subcategory '{sub}' is invalid for category '{cat}'. Valid choices: {valid_subs}.",
                               suggestion=f"Set subcategory to one of: {valid_subs}")
        else:
            self.add_check("TAXONOMY_CATEGORY", "Terminus 3 Category Taxonomy", "Metadata", "FAIL",
                           f"Category '{cat}' is invalid. Allowed categories: {list(TAXONOMY.keys())}.",
                           suggestion=f"Set category to one of: {list(TAXONOMY.keys())}")

        # 3. Difficulty Enum Check (Terminus 3 Tiers: frontier, advanced, core, base)
        raw_diff = str(data.get("difficulty") or meta.get("difficulty", "")).strip().lower()
        if raw_diff in DIFFICULTY_TIERS:
            self.add_check("DIFFICULTY_ENUM_VALID", "Task Difficulty Tier Compliance", "Metadata", "PASS", f"Difficulty tier is valid ('{raw_diff}').")
        else:
            self.add_check(
                "DIFFICULTY_ENUM_VALID", "Task Difficulty Tier Compliance", "Metadata", "FAIL",
                f"Invalid difficulty '{raw_diff}'. Allowed Terminus 3 values: {DIFFICULTY_TIERS}.",
                details="Per Terminus 3 rules, difficulty must be one of: 'frontier', 'advanced', 'core', or 'base'.",
                suggestion="Change difficulty in task.toml to 'frontier', 'advanced', 'core', or 'base'."
            )

        # 4. Top-level Artifacts Check
        verifier_sec = data.get("verifier", {}) if isinstance(data.get("verifier"), dict) else {}
        if "artifacts" in verifier_sec and "artifacts" not in data:
            self.add_check("ARTIFACTS_TOP_LEVEL", "Top-Level Artifacts Placement", "Metadata", "FAIL",
                           "artifacts array is nested under [verifier] section.",
                           details="Per Terminus 3 schema, artifacts MUST be defined at top-level. Nested verifier.artifacts are silently dropped by STB Harbor!",
                           suggestion="Move `artifacts = [...]` to top-level of task.toml.")
        elif "artifacts" in data and isinstance(data["artifacts"], list) and len(data["artifacts"]) > 0:
            self.add_check("ARTIFACTS_TOP_LEVEL", "Top-Level Artifacts Placement", "Metadata", "PASS", f"Declared {len(data['artifacts'])} top-level artifact path(s).")
        else:
            self.add_check("ARTIFACTS_TOP_LEVEL", "Top-Level Artifacts Placement", "Metadata", "FAIL",
                           "Missing or empty `artifacts` list at top-level of task.toml.",
                           suggestion="Add `artifacts = ['/app/...']` to top-level of task.toml.")

        # 5. Explanation Fields Audit
        missing_expl = [f for f in EXPLANATION_FIELDS if not data.get(f) and not meta.get(f)]
        if not missing_expl:
            self.add_check("EXPLANATION_FIELDS", "Task Explanation Documentation Fields", "Metadata", "PASS", "All required task explanation fields present.")
        else:
            self.add_check("EXPLANATION_FIELDS", "Task Explanation Documentation Fields", "Metadata", "WARN",
                           f"Missing explanation fields: {', '.join(missing_expl)}",
                           suggestion=f"Add explanation fields (`difficulty_explanation`, `solution_explanation`, `verification_explanation`, `relevant_experience`) to task.toml.")

        # 6. Deprecated Terminus 2 Fields Removal Check
        found_removed = [f for f in REMOVED_FIELDS if f in data or f in meta]
        if found_removed:
            self.add_check("DEPRECATED_T2_FIELDS", "Obsolete Terminus 2 Fields Removal", "Metadata", "WARN",
                           f"task.toml contains obsolete Terminus 2 fields: {', '.join(found_removed)}",
                           suggestion=f"Remove obsolete fields from task.toml: {found_removed}")

        # 7. Section [verifier] and [agent] Timeout Floor Checks
        agent_sec = data.get("agent", {}) if isinstance(data.get("agent"), dict) else {}
        if agent_sec and "timeout_sec" in agent_sec:
            at = agent_sec.get("timeout_sec", 0)
            if at >= 1800:
                self.add_check("AGENT_TIMEOUT_FLOOR", "[agent].timeout_sec Range Compliance", "Metadata", "PASS", f"Agent timeout ({at}s) meets minimum 1800s floor.")
            else:
                self.add_check("AGENT_TIMEOUT_FLOOR", "[agent].timeout_sec Range Compliance", "Metadata", "FAIL",
                               f"[agent].timeout_sec ({at}s) is below 1800s minimum floor.",
                               suggestion="Increase `[agent].timeout_sec` to at least 1800 (default 3600-5400s).")

        return data

    def _parse_toml_fallback(self, text):
        res = {}
        curr = res
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"): continue
            m = re.match(r"^\[([^\]]+)\]$", line)
            if m:
                parts = m.group(1).split(".")
                curr = res
                for p in parts:
                    if p not in curr: curr[p] = {}
                    curr = curr[p]
                continue
            m = re.match(r"^([a-zA-Z_][\w]*)\s*=\s*(.+)$", line)
            if m:
                k, v = m.group(1), m.group(2).strip()
                if v.startswith('"') and v.endswith('"'): curr[k] = v[1:-1]
                elif v.startswith("[") and v.endswith("]"):
                    inner = v[1:-1].strip()
                    curr[k] = [s.strip().strip('"').strip("'") for s in inner.split(",")] if inner else []
                elif v.lower() == "true": curr[k] = True
                elif v.lower() == "false": curr[k] = False
                else:
                    try: curr[k] = int(v)
                    except ValueError: curr[k] = v
        return res

    def _audit_file_architecture(self):
        req_root_files = {
            "instruction.md": "Task Instructions File",
            "README.md": "Human-written Task README",
            "environment/Dockerfile": "Environment Dockerfile",
            "solution/solve.sh": "Oracle Solution Script",
            "tests/Dockerfile": "Verifier Container Dockerfile",
            "tests/test.sh": "Verifier Test Runner",
            "tests/test_outputs.py": "Pytest Assertion Suite"
        }
        for rel_path, desc in req_root_files.items():
            fp = self._find_file_path(rel_path)
            check_key = f"FILE_{rel_path.replace('/', '_').replace('.', '_')}"
            if fp:
                self.add_check(check_key, desc, "Architecture", "PASS", f"Found required file `{rel_path}`.")
            else:
                self.add_check(check_key, desc, "Architecture", "FAIL", f"Missing required file `{rel_path}`.",
                               suggestion=f"Create `{rel_path}` according to task component specifications.")

    def _audit_instruction_styling(self):
        inst_path = self._find_file_path("instruction.md")
        if not inst_path: return

        with open(inst_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        bullets = [l for l in lines if re.match(r"^[-*]\s+|\d+\.\s+", l)]
        word_count = len(content.split())

        # Check for headers starting with title markdown `# task-name`
        has_title_header = lines[0].startswith("#") if lines else False

        # Anti-synthetic tone screening
        synthetic_match = re.search(r"(you are an expert|here's how|in this guide|as an ai|your goal is to|let's get started|\bdelve\b|\bleverage\b|\bmoreover\b)", content, re.I)

        # Check absolute /app/ paths
        has_app_paths = "/app/" in content or "/app" in content

        violations = []
        if has_title_header: violations.append("starts with markdown title header ('# ...')")
        if len(paragraphs) > 5 and len(bullets) > 20: violations.append(f"exceeds concise length limit ({len(paragraphs)} paras, {len(bullets)} bullets)")
        if word_count > 800: violations.append(f"word count is too long ({word_count} words; max ~800)")
        if synthetic_match: violations.append(f"contains synthetic AI boilerplate ('{synthetic_match.group(0)}')")
        if not has_app_paths: violations.append("missing absolute `/app/...` artifact paths")

        if violations:
            self.add_check(
                "INSTRUCTION_STYLING", "instruction.md Quality & Prose Styling", "Documentation", "WARN",
                f"instruction.md prompt guidelines: {', '.join(violations)}.",
                details="Per Snorkel prompt guidelines, instruction.md must be concise human-written prose using absolute /app/ paths without AI synthetic buzzwords.",
                suggestion="Rewrite instruction.md into clean, human-written conversational prose referencing absolute `/app/...` paths."
            )
        else:
            self.add_check(
                "INSTRUCTION_STYLING", "instruction.md Quality & Prose Styling", "Documentation", "PASS",
                f"instruction.md is formatted in clean, human-written prose ({word_count} words, absolute /app/ paths)."
            )

    def _audit_dockerfile(self):
        dockerfile_path = self._find_file_path("environment/Dockerfile")
        if not dockerfile_path: return

        with open(dockerfile_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        lines = content.splitlines()
        from_lines = [l for l in lines if l.strip().startswith("FROM")]

        # 1. 64-hex SHA256 Regex Check on FROM lines
        unpinned_from = []
        for fl in from_lines:
            m = re.search(r"@sha256:([0-9a-fA-F]+)", fl)
            if not m or len(m.group(1)) != 64:
                unpinned_from.append(fl)

        if unpinned_from:
            self.add_check(
                "DOCKER_PINNED_IMAGES", "Dockerfile Base Image Digest Pinning", "Docker", "FAIL",
                f"Unpinned or invalid 64-hex sha256 digest in FROM lines: {', '.join(unpinned_from)}",
                details="Every FROM line in environment/Dockerfile must be digest-pinned using @sha256:<64-hex-digest>.",
                suggestion="Add valid 64-hex @sha256:<digest> to every FROM image statement."
            )
        else:
            self.add_check("DOCKER_PINNED_IMAGES", "Dockerfile Base Image Digest Pinning", "Docker", "PASS", "All FROM lines use valid 64-hex @sha256:<digest> digest pinning.")

        # 2. Canonical base image check
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
                suggestion="Use a canonical Terminal-Bench base image or add a '# Base Image Justification:' comment."
            )

        # 3. Agent harness tools
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
                suggestion=f"Install {missing_tools} in environment/Dockerfile via apt-get."
            )

        # 4. Prohibited COPY solution/ or tests/
        if re.search(r'COPY\s+.*\bsolution\b', content) or re.search(r'COPY\s+.*\btests\b', content):
            self.add_check(
                "SOL_TESTS_IN_IMAGE", "Solution/Tests Isolation in Dockerfile", "Docker", "FAIL",
                "Dockerfile explicitly copies solution/ or tests/ directory into the image.",
                suggestion="Remove any COPY statements referencing solution/ or tests/ from environment/Dockerfile."
            )
        else:
            self.add_check("SOL_TESTS_IN_IMAGE", "Solution/Tests Isolation in Dockerfile", "Docker", "PASS", "No solution or test files are copied into the Docker runtime image.")

        # 5. Check environment/ setup.sh execution in Dockerfile if setup.sh exists
        setup_sh_path = self._find_file_path("environment/setup.sh")
        if setup_sh_path:
            runs_setup = bool(re.search(r"RUN[^\n]*setup\.sh|bash\s+/?setup\.sh", content))
            if runs_setup:
                self.add_check("DOCKER_RUNS_SETUP_SH", "Dockerfile Execution of environment/setup.sh", "Docker", "PASS", "Dockerfile explicitly executes environment/setup.sh.")
            else:
                self.add_check("DOCKER_RUNS_SETUP_SH", "Dockerfile Execution of environment/setup.sh", "Docker", "WARN",
                               "environment/setup.sh exists but Dockerfile never runs it.",
                               suggestion="Add `RUN bash /app/setup.sh` or `RUN bash setup.sh` in environment/Dockerfile.")

        # 6. Check git clone commit pinning
        git_clones = re.findall(r"git clone[^\n]+", content)
        unpinned_git = [g for g in git_clones if not re.search(r"checkout|--branch\s+\S+", g)]
        if unpinned_git:
            self.add_check("DOCKER_GIT_PINNED", "Git Clone Commit Pinning", "Docker", "WARN",
                           f"Unpinned `git clone` command in Dockerfile: {unpinned_git[0][:60]}",
                           suggestion="Pin git clones using `--branch <tag>` or `git checkout <commit-sha>`.")
        elif git_clones:
            self.add_check("DOCKER_GIT_PINNED", "Git Clone Commit Pinning", "Docker", "PASS", "All `git clone` commands are pinned to specific commits/branches.")

        # 7. Check build context size
        env_dir = os.path.dirname(dockerfile_path)
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
                f"environment/ size is {round(total_size_mb, 1)} MiB (max 100 MiB). Large files over 50 MiB: {large_files}",
                suggestion="Keep environment/ under 100 MiB total and all files under 50 MiB."
            )
        else:
            self.add_check("DOCKER_CONTEXT_SIZE", "Build Context & File Size Limits", "Docker", "PASS", f"environment/ size ({round(total_size_mb, 1)} MiB) is within limits.")

        dockerignore_path = self._find_file_path("environment/.dockerignore")
        if dockerignore_path:
            self.add_check("DOCKERIGNORE_CHECK", ".dockerignore File Presence", "Docker", "PASS", ".dockerignore file exists in environment/.")
        else:
            self.add_check("DOCKERIGNORE_CHECK", ".dockerignore File Presence", "Docker", "WARN", "Missing .dockerignore file in environment/.",
                           suggestion="Create environment/.dockerignore ignoring .git, solution/, tests/, node_modules, etc.")

    def _audit_solution_and_tests(self):
        test_req_path = self._find_file_path("tests/requirements.txt")
        if test_req_path:
            self.add_check("TEST_DEPS_SEPARATION", "Prohibited Test Requirements File", "Testing", "FAIL",
                           "Prohibited file tests/requirements.txt is present inside tests/ directory.",
                           suggestion="Remove tests/requirements.txt and pre-install test dependencies in environment/Dockerfile or tests/Dockerfile.")
        else:
            self.add_check("TEST_DEPS_SEPARATION", "Docker Test Dependencies Pre-Bake Compliance", "Testing", "PASS",
                           "No prohibited tests/requirements.txt present; test dependencies pre-baked in Docker environment.")

        dockerfile_path = self._find_file_path("environment/Dockerfile")
        dockerfile_content = ""
        if dockerfile_path:
            with open(dockerfile_path, "r", encoding="utf-8", errors="ignore") as f:
                dockerfile_content = f.read()

        tests_dockerfile_path = self._find_file_path("tests/Dockerfile")
        tests_docker_content = ""
        if tests_dockerfile_path:
            with open(tests_dockerfile_path, "r", encoding="utf-8", errors="ignore") as f:
                tests_docker_content = f.read()

        test_sh_path = self._find_file_path("tests/test.sh")
        if test_sh_path:
            with open(test_sh_path, "r", encoding="utf-8", errors="ignore") as f:
                t_content = f.read()

            runs_solution = any(kw in t_content for kw in ["solve.sh", "solve.py", "solution/solve", "reconciler.py"])
            has_tests_dockerfile = tests_dockerfile_path is not None
            
            if runs_solution or has_tests_dockerfile:
                self.add_check("ORACLE_SOLUTION_EXECUTION", "Verifier Reference Solution Invocation", "Testing", "PASS", "Verifier reference solution invocation / artifact transfer is properly configured.")
            else:
                self.add_check(
                    "ORACLE_SOLUTION_EXECUTION", "Verifier Reference Solution Invocation", "Testing", "FAIL",
                    "tests/test.sh does NOT execute the reference solution before running pytest assertions.",
                    suggestion="Add `bash solution/solve.sh` before pytest in tests/test.sh, or add tests/Dockerfile for Terminus 3 separate mode."
                )

            if "pip install" in t_content or "apt-get" in t_content:
                self.add_check(
                    "TEST_SH_OFFLINE", "Offline Test Execution Policy", "Testing", "FAIL",
                    "tests/test.sh attempts network downloads (pip install / apt-get) at runtime.",
                    suggestion="Remove pip install / network commands from tests/test.sh and install dependencies in Dockerfile."
                )
            else:
                self.add_check("TEST_SH_OFFLINE", "Offline Test Execution Policy", "Testing", "PASS", "tests/test.sh executes offline without runtime package installation.")

            if "--ctrf" in t_content:
                has_ctrf_installed = "pytest-json-ctrf" in dockerfile_content or "pytest-json-ctrf" in tests_docker_content
                if not has_ctrf_installed:
                    self.add_check(
                        "TEST_CTRF_INSTALLED", "pytest-json-ctrf Package Installation", "Testing", "FAIL",
                        "tests/test.sh uses --ctrf flag but pytest-json-ctrf is missing from Dockerfile.",
                        suggestion="Add `pytest-json-ctrf==0.3.5` to pip install command in tests/Dockerfile or environment/Dockerfile."
                    )
                else:
                    self.add_check("TEST_CTRF_INSTALLED", "pytest-json-ctrf Package Installation", "Testing", "PASS", "pytest-json-ctrf package is pre-baked in Docker container environment.")

            # Check set -e reliability
            if "set -e" in t_content and "set +e" not in t_content:
                self.add_check(
                    "TEST_SH_REWARD_RELIABILITY", "Verifier Reward File Writing Reliability", "Testing", "FAIL",
                    "tests/test.sh uses `set -e` without `set +e` right before `pytest`.",
                    details="When pytest fails under `set -e`, bash exits immediately without writing reward.txt, triggering RewardFileNotFoundError.",
                    suggestion="Use `set -uo pipefail` or add `set +e` before pytest in tests/test.sh, capture `$?`, and write reward score."
                )
            else:
                self.add_check("TEST_SH_REWARD_RELIABILITY", "Verifier Reward File Writing Reliability", "Testing", "PASS", "test.sh safely handles pytest exit codes without suppressing reward file creation.")

        # Python Syntax & Docstring Checks
        sol_dir = self._find_file_path("solution/solve.sh")
        test_py_path = self._find_file_path("tests/test_outputs.py")
        if test_py_path:
            with open(test_py_path, "r", encoding="utf-8", errors="ignore") as f:
                py_content = f.read()

            try:
                ast.parse(py_content)
                self.add_check("TEST_PY_SYNTAX", "test_outputs.py Python Syntax", "Testing", "PASS", "test_outputs.py is valid Python without syntax errors.")
            except SyntaxError as se:
                self.add_check("TEST_PY_SYNTAX", "test_outputs.py Python Syntax", "Testing", "FAIL", f"test_outputs.py contains SyntaxError: {se.msg} (line {se.lineno}).")

            test_funcs = re.findall(r'def (test_\w+)\s*\(', py_content)
            missing_docstrings = []
            for func in test_funcs:
                func_match = re.search(r'def ' + func + r'\s*\([^)]*\):(?:\s*\n)+([ \t]*["\']{3})', py_content)
                if not func_match:
                    missing_docstrings.append(func)

            if missing_docstrings:
                self.add_check(
                    "TEST_DOCSTRINGS", "Pytest Function Docstrings", "Testing", "FAIL",
                    f"Test functions missing docstrings: {', '.join(missing_docstrings)}.",
                    suggestion=f"Add descriptive docstrings (\"\"\"...\"\"\") to test functions: {missing_docstrings}"
                )
            else:
                self.add_check("TEST_DOCSTRINGS", "Pytest Function Docstrings", "Testing", "PASS", f"All {len(test_funcs)} test functions have clear docstrings.")

            # Banned oracle/agent conditional branching check
            if re.search(r"EVAL_IS_ORACLE|\bORACLE\b|os\.getenv.*ORACLE", py_content):
                self.add_check("TEST_NO_ORACLE_BRANCHING", "Identical Oracle & Agent Test Execution", "Testing", "FAIL",
                               "test_outputs.py contains conditional oracle/agent test branching.",
                               suggestion="Remove ORACLE environment variable branching from tests/test_outputs.py.")
            else:
                self.add_check("TEST_NO_ORACLE_BRANCHING", "Identical Oracle & Agent Test Execution", "Testing", "PASS", "Tests run identically for both Oracle and Agent solutions.")

    def _audit_rubrics(self):
        rubrics_path = self._find_file_path("rubrics.txt")
        if not rubrics_path: return

        with open(rubrics_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        if not lines:
            self.add_check("RUBRICS_SYNTAX", "rubrics.txt Specification File", "Documentation", "WARN", "rubrics.txt file is empty.")
            return

        bad_lines = []
        scores = []
        for l in lines:
            m = re.match(r"^(Agent .+),\s*([+-]?\d+)$", l)
            if not m:
                bad_lines.append(l[:50])
            else:
                scores.append(int(m.group(2)))

        if bad_lines:
            self.add_check("RUBRICS_SYNTAX", "rubrics.txt Syntax Compliance", "Documentation", "WARN",
                           f"rubrics.txt has malformed lines: {bad_lines[:2]}",
                           suggestion="Format lines as: `Agent <description>, [+-]N`.")
        else:
            self.add_check("RUBRICS_SYNTAX", "rubrics.txt Syntax Compliance", "Documentation", "PASS", "rubrics.txt matches exact `Agent <description>, [+-]N` format.")

    def _audit_cross_consistency(self):
        inst_path = self._find_file_path("instruction.md")
        solve_path = self._find_file_path("solution/solve.sh")
        setup_path = self._find_file_path("environment/setup.sh")
        docker_path = self._find_file_path("environment/Dockerfile")

        inst_txt = open(inst_path, "r", encoding="utf-8", errors="ignore").read() if inst_path else ""
        solve_txt = open(solve_path, "r", encoding="utf-8", errors="ignore").read() if solve_path else ""
        setup_txt = open(setup_path, "r", encoding="utf-8", errors="ignore").read() if setup_path else ""
        docker_txt = open(docker_path, "r", encoding="utf-8", errors="ignore").read() if docker_path else ""

        app_path_re = re.compile(r"/app/[A-Za-z0-9_./{}\-]+")
        env_created = set(app_path_re.findall(setup_txt)) | set(app_path_re.findall(docker_txt))
        solve_all = set(app_path_re.findall(solve_txt))
        inst_all = set(app_path_re.findall(inst_txt))

        # Check for uncreated input paths read in solve.sh
        missing_inputs = []
        for p in solve_all:
            if not p.startswith("/app/output") and not p.startswith("/app/migrations") and p not in env_created:
                # check if file exists under environment/
                fname = os.path.basename(p)
                if not self._find_file_path("environment/" + fname):
                    missing_inputs.append(p)

        if missing_inputs:
            self.add_check("CROSS_INPUT_PATHS", "Cross-Component Input Path Consistency", "Architecture", "WARN",
                           f"solution/solve.sh references uncreated environment path(s): {missing_inputs[:3]}",
                           suggestion="Ensure environment/ (setup.sh or Dockerfile) pre-creates all input files read by solution/solve.sh.")
        else:
            self.add_check("CROSS_INPUT_PATHS", "Cross-Component Input Path Consistency", "Architecture", "PASS", "All input paths read by solution/solve.sh are pre-created in environment.")
