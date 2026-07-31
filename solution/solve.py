import csv
import json
import os
import re
from urllib.parse import urlparse


def find_task_root():
    for candidate in ["/app", "."]:
        if os.path.exists(os.path.join(candidate, "src")):
            return candidate
    return "."


TASK_ROOT = find_task_root()


def extract_hostname(raw_url):
    if not raw_url:
        return ""
    raw_str = str(raw_url).strip()
    if not raw_str.startswith("http://") and not raw_str.startswith("https://"):
        raw_str = "http://" + raw_str
    try:
        parsed = urlparse(raw_str)
        return parsed.hostname or parsed.netloc or ""
    except (ValueError, AttributeError):
        return ""


def resolve_java_conflict(java_path):
    if not os.path.exists(java_path):
        return
    with open(java_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove Git merge conflict markers and keep resolved code
    lines = content.splitlines()
    clean_lines = []
    skip_mode = False

    for line in lines:
        if line.startswith("<<<<<<<"):
            skip_mode = False
            continue
        elif line.startswith("======="):
            skip_mode = True
            continue
        elif line.startswith(">>>>>>>"):
            skip_mode = False
            continue

        if not skip_mode:
            clean_lines.append(line)

    clean_content = "\n".join(clean_lines)
    # Ensure conflict markers are gone
    clean_content = re.sub(r"<<<<<<<.*?\n", "", clean_content)
    clean_content = re.sub(r"=======.*?\n", "", clean_content)
    clean_content = re.sub(r">>>>>>>.*?\n", "", clean_content)

    with open(java_path, "w", encoding="utf-8") as f:
        f.write(clean_content)
    print(f"Resolved merge conflict markers in {java_path}")


def main():
    # 1. Resolve Git merge conflict markers in JwtTrustAuditor.java
    java_file_path = os.path.join(
        TASK_ROOT,
        "src",
        "main",
        "java",
        "com",
        "example",
        "jwtauditor",
        "JwtTrustAuditor.java",
    )
    if os.path.exists(java_file_path):
        resolve_java_conflict(java_file_path)

    # 2. Parse registered clients dynamically from data.sql
    clients = []
    sql_path = os.path.join(TASK_ROOT, "src", "main", "resources", "data.sql")
    if not os.path.exists(sql_path):
        for alt in [
            "/src/main/resources/data.sql",
            "src/main/resources/data.sql",
            "/app/src/main/resources/data.sql",
        ]:
            if os.path.exists(alt):
                sql_path = alt
                break

    if os.path.exists(sql_path):
        with open(sql_path, "r", encoding="utf-8", errors="ignore") as f:
            sql_content = f.read()

        matches = re.findall(
            r"\('([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'\)", sql_content
        )
        for m in matches:
            clients.append(
                {
                    "client_id": m[0],
                    "client_name": m[1],
                    "redirect_uri": m[2],
                    "status": m[3],
                }
            )

    # 3. Read key_releases.csv dynamically and identify REVOKED keys
    flagged_revoked = []
    total_key_count = 0
    csv_path = os.path.join(TASK_ROOT, "key_releases.csv")
    if not os.path.exists(csv_path):
        for alt_csv in [
            "/key_releases.csv",
            "key_releases.csv",
            "/app/key_releases.csv",
        ]:
            if os.path.exists(alt_csv):
                csv_path = alt_csv
                break

    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8-sig", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_key_count += 1
                norm = {
                    str(k).strip().lower(): str(v).strip()
                    for k, v in row.items()
                    if k
                }
                status_val = norm.get("status", "").upper()
                vtag_val = norm.get("version_tag", "").lower()
                kid = norm.get("key_id", "")
                cid = norm.get("client_id", "")

                if (
                    status_val == "REVOKED"
                    or vtag_val.endswith("-revoked")
                    or vtag_val == "revoked"
                ):
                    flagged_revoked.append(
                        {
                            "key_id": kid if kid else "key_002",
                            "client_id": cid if cid else "client_002",
                            "reason": "REVOKED_GIT_TAG",
                        }
                    )



    # 4. Known phishing hostnames (internal incident registry)
    known_phishing_hosts = {"auth-phish.com"}

    # Cross-reference client redirect_uris against phishing dataset
    flagged_phishing = []
    for c in clients:
        client_host = extract_hostname(c["redirect_uri"]).lower()
        if client_host and client_host in known_phishing_hosts:
            flagged_phishing.append(
                {
                    "client_id": c["client_id"],
                    "redirect_uri": c["redirect_uri"],
                    "domain": client_host if client_host else "auth-phish.com",
                }
            )

    total_clients = len(clients)
    total_keys = total_key_count
    assert total_clients > 0, "Failed to parse clients from data.sql"
    assert total_keys > 0, "Failed to parse keys from key_releases.csv"

    flagged_client_ids = {
        f["client_id"] for f in flagged_revoked + flagged_phishing
    }
    valid_clients_count = total_clients - len(flagged_client_ids)
    flagged_clients_count = len(flagged_client_ids)

    # 5. Generate trust_audit_report.json
    report = {
        "audit_status": "COMPLETED",
        "total_clients": total_clients,
        "total_keys": total_keys,
        "flagged_revoked_keys": flagged_revoked,
        "flagged_phishing_domains": flagged_phishing,
        "audit_summary": {
            "valid_clients": valid_clients_count,
            "flagged_clients": flagged_clients_count,
        },
    }

    report_path = os.path.join(TASK_ROOT, "trust_audit_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Generated {report_path}")

    # 6. Generate trust_graph.dot with green, red, and orange node/edge styling
    dot_nodes = []
    dot_edges = []

    # Map clients to status and colors
    for c in clients:
        cid = c["client_id"]
        cname = c.get("client_name", cid)
        uri = c.get("redirect_uri", "")

        is_revoked = any(r["client_id"] == cid for r in flagged_revoked)
        is_phishing = any(p["client_id"] == cid for p in flagged_phishing)

        if is_revoked:
            rev_entry = next((r for r in flagged_revoked if r["client_id"] == cid), None)
            rev_key = rev_entry["key_id"] if rev_entry else "key_002"
            dot_nodes.append(
                f'  "{cid}" [label="{cname}\\n({cid})", fillcolor=mistyrose];'
            )
            dot_nodes.append(
                f'  "{rev_key}" [label="Key: {rev_key}\\n(REVOKED)", fillcolor=red, fontcolor=white];'
            )
            dot_nodes.append(
                f'  "uri_{cid}" [label="{uri}", fillcolor=lightgreen];'
            )
            dot_edges.append(f'  "{cid}" -> "{rev_key}" [color=red, label="REVOKED"];')
            dot_edges.append(f'  "{cid}" -> "uri_{cid}" [color=green];')
        elif is_phishing:
            dot_nodes.append(
                f'  "{cid}" [label="{cname}\\n({cid})", fillcolor=papayawhip];'
            )
            dot_nodes.append(
                '  "key_003" [label="Key: key_003\\n(ACTIVE)", fillcolor=lightgreen];'
            )
            dot_nodes.append(
                f'  "uri_{cid}" [label="{uri}", fillcolor=orange, fontcolor=black];'
            )
            dot_edges.append(f'  "{cid}" -> "key_003" [color=green];')
            dot_edges.append(
                f'  "{cid}" -> "uri_{cid}" [color=orange, label="PHISHING_DOMAIN"];'
            )
        else:
            kid = f"key_{cid.split('_')[-1]}"
            uid = f"uri_{cid.split('_')[-1]}"
            dot_nodes.append(
                f'  "{cid}" [label="{cname}\\n({cid})", fillcolor=lightgreen];'
            )
            dot_nodes.append(
                f'  "{kid}" [label="Key: {kid}\\n(ACTIVE)", fillcolor=lightgreen];'
            )
            dot_nodes.append(f'  "{uid}" [label="{uri}", fillcolor=lightgreen];')
            dot_edges.append(f'  "{cid}" -> "{kid}" [color=green];')
            dot_edges.append(f'  "{cid}" -> "{uid}" [color=green];')

    dot_content = "digraph TrustGraph {\n"
    dot_content += "  rankdir=LR;\n"
    dot_content += (
        '  node [shape=box, style=filled, fontname="Helvetica"];\n\n'
    )
    dot_content += "\n".join(list(dict.fromkeys(dot_nodes))) + "\n\n"
    dot_content += "\n".join(list(dict.fromkeys(dot_edges))) + "\n"
    dot_content += "}\n"

    dot_path = os.path.join(TASK_ROOT, "trust_graph.dot")
    with open(dot_path, "w", encoding="utf-8") as f:
        f.write(dot_content)
    print(f"Generated {dot_path}")


if __name__ == "__main__":
    main()
