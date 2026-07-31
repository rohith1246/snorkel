import json
import os
import subprocess

import pytest


def find_task_root():
    for candidate in ["/app", "."]:
        if os.path.exists(os.path.join(candidate, "src")):
            return candidate
    return "."


TASK_ROOT = find_task_root()


def test_rebase_conflict_resolved():
    """Verify that Git merge conflict markers have been removed from JwtTrustAuditor.java."""
    java_file = os.path.join(
        TASK_ROOT,
        "src",
        "main",
        "java",
        "com",
        "example",
        "jwtauditor",
        "JwtTrustAuditor.java",
    )
    assert os.path.exists(
        java_file
    ), f"JwtTrustAuditor.java not found at {java_file}"

    with open(java_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert (
        "<<<<<<<" not in content
    ), "Git merge conflict marker '<<<<<<<' still present in JwtTrustAuditor.java"
    assert (
        "=======" not in content
    ), "Git merge conflict marker '=======' still present in JwtTrustAuditor.java"
    assert (
        ">>>>>>>" not in content
    ), "Git merge conflict marker '>>>>>>>' still present in JwtTrustAuditor.java"


def test_java_compilation():
    """Verify that JwtTrustAuditor.java compiles cleanly."""
    import shutil
    if not shutil.which("javac"):
        pytest.skip("javac not available")

    java_file = os.path.join(
        TASK_ROOT,
        "src",
        "main",
        "java",
        "com",
        "example",
        "jwtauditor",
        "JwtTrustAuditor.java",
    )
    assert os.path.exists(java_file), f"JwtTrustAuditor.java not found at {java_file}"

    src_dir = os.path.join(TASK_ROOT, "src", "main", "java")
    res = subprocess.run(
        ["javac", "-sourcepath", src_dir, java_file],
        capture_output=True,
        text=True,
        check=False,
    )
    assert (
        res.returncode == 0
    ), f"JwtTrustAuditor.java compilation failed: {res.stderr}"


def test_audit_json_report():
    """Verify complete schema, fields, exact summary counts, and anti-decoy assertions for trust_audit_report.json."""
    report_file = os.path.join(TASK_ROOT, "trust_audit_report.json")
    assert os.path.exists(
        report_file
    ), f"trust_audit_report.json not found at {report_file}"

    with open(report_file, "r", encoding="utf-8") as f:
        report = json.load(f)

    # 1. Top level status & dynamic counts (9 clients, 9 keys)
    assert report.get("audit_status") == "COMPLETED"
    assert report.get("total_clients") == 9
    assert report.get("total_keys") == 9

    # 2. Audit Summary exact counts validation (6 valid clients, 3 flagged clients)
    summary = report.get("audit_summary")
    assert summary is not None, "Missing audit_summary field in report"
    assert "valid_clients" in summary, "Missing valid_clients in audit_summary"
    assert "flagged_clients" in summary, "Missing flagged_clients in audit_summary"
    assert summary.get("valid_clients") == 6, f"Expected valid_clients=6, got {summary.get('valid_clients')}"
    assert summary.get("flagged_clients") == 3, f"Expected flagged_clients=3, got {summary.get('flagged_clients')}"
    assert (
        summary["valid_clients"] + summary["flagged_clients"] == 9
    ), "Audit summary counts do not sum to total_clients"

    # 3. Flagged Revoked Keys schema & decoy assertions
    revoked_keys = report.get("flagged_revoked_keys", [])
    assert len(revoked_keys) > 0, "No revoked keys flagged in report"
    
    # key_002 flagged for status=REVOKED
    k2 = next((k for k in revoked_keys if k.get("key_id") == "key_002"), None)
    assert k2 is not None, "key_002 not found in flagged_revoked_keys"
    assert k2.get("client_id") == "client_002"
    assert k2.get("reason") == "REVOKED_GIT_TAG"

    # key_006 flagged for version_tag suffix '-revoked' (with status=RELEASED)
    k6 = next((k for k in revoked_keys if k.get("key_id") == "key_006"), None)
    assert k6 is not None, "key_006 (tag-suffix revoked) not found in flagged_revoked_keys"
    assert k6.get("client_id") == "client_006"

    # Anti-Decoy Assertions for Revoked Keys:
    # key_005 decoy (version_tag 'v1.3.0-unrevoked-notice') must NOT be flagged
    assert not any(
        k.get("key_id") == "key_005" for k in revoked_keys
    ), "Decoy key_005 ('unrevoked-notice') was wrongly flagged by naive substring check"

    # key_008 decoy (version_tag 'v1.0.5-revoked-status-clear') must NOT be flagged
    assert not any(
        k.get("key_id") == "key_008" for k in revoked_keys
    ), "Decoy key_008 ('revoked-status-clear') was wrongly flagged by naive substring check"

    # 4. Flagged Phishing Domains schema & decoy assertions
    phishing = report.get("flagged_phishing_domains", [])
    assert len(phishing) > 0, "No phishing domains flagged in report"
    c3 = next((p for p in phishing if p.get("client_id") == "client_003"), None)
    assert c3 is not None, "client_003 not found in flagged_phishing_domains"
    assert "redirect_uri" in c3 and "auth-phish.com" in c3["redirect_uri"]
    assert c3.get("domain") == "auth-phish.com"

    # Anti-Decoy Assertions for Phishing Domains:
    # client_005 decoy ('auth-phish.com.trusted-proxy.net') must NOT be flagged
    assert not any(
        p.get("client_id") == "client_005" for p in phishing
    ), "Decoy client_005 ('auth-phish.com.trusted-proxy.net') was wrongly flagged"

    # client_007 decoy ('anti-phishing-defense.org') must NOT be flagged
    assert not any(
        p.get("client_id") == "client_007" for p in phishing
    ), "Decoy client_007 ('anti-phishing-defense.org') was wrongly flagged by naive 'phish' substring check"

    # client_009 decoy ('auth-phish.com.security-gateway.com') must NOT be flagged
    assert not any(
        p.get("client_id") == "client_009" for p in phishing
    ), "Decoy client_009 ('auth-phish.com.security-gateway.com') was wrongly flagged by naive subdomain check"


def test_graphviz_dot_file():
    """Verify contents, green/red/orange color styling, and Graphviz DOT structure."""
    dot_file = os.path.join(TASK_ROOT, "trust_graph.dot")
    assert os.path.exists(dot_file), f"trust_graph.dot not found at {dot_file}"

    with open(dot_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "digraph" in content, "Invalid Graphviz DOT file (missing 'digraph')"
    assert "key_002" in content
    assert "green" in content or "lightgreen" in content, "Missing green color styling for valid components"
    assert "red" in content, "Missing red color styling for revoked key"
    assert (
        "orange" in content
    ), "Missing orange color styling for phishing domain"
    assert "auth-phish.com" in content


def test_dot_graphviz_compilation():
    """Verify that trust_graph.dot is valid syntax using graphviz dot binary."""
    import shutil
    if not shutil.which("dot"):
        pytest.skip("dot not available")

    dot_file = os.path.join(TASK_ROOT, "trust_graph.dot")
    assert os.path.exists(dot_file), f"trust_graph.dot not found at {dot_file}"

    res = subprocess.run(
        ["dot", "-Tsvg", dot_file, "-o", "/dev/null"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert (
        res.returncode == 0
    ), f"Graphviz dot syntax check failed: {res.stderr}"
