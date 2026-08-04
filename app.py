import os
import tempfile
import zipfile
import json
from flask import Flask, render_template, request, jsonify, Response, send_file
import io
from validator import SnorkelTaskValidator
from groq_agent import GroqTaskAgent
from db import TaskAuditDB
from task_ideas_catalog import get_100_task_ideas
from terminus3_template import TERMINUS3_FOLDER_STRUCTURE, generate_terminus3_starter_zip_bytes

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max upload limit

db = TaskAuditDB()
ALL_TASK_IDEAS = get_100_task_ideas()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return Response(status=204)

@app.route('/api/audit', methods=['POST'])
def audit_task_zip():
    if 'task_zip' not in request.files:
        return jsonify({"status": "ERROR", "message": "No task_zip file uploaded."}), 400

    file = request.files['task_zip']
    if file.filename == '':
        return jsonify({"status": "ERROR", "message": "No selected file."}), 400

    if not file.filename.endswith('.zip'):
        return jsonify({"status": "ERROR", "message": "Invalid file type. Must be a .zip archive."}), 400

    groq_api_key = request.form.get('groq_api_key', '').strip()

    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    try:
        file.save(temp_zip.name)
        temp_zip.close()

        # Run Validator Engine
        validator = SnorkelTaskValidator(temp_zip.name)
        audit_results = validator.run_audit()

        # Extract file contents for AI analysis
        file_contents = {}
        with zipfile.ZipFile(temp_zip.name, 'r') as z:
            for name in z.namelist():
                if name.endswith(('Dockerfile', 'task.toml', 'test.sh', 'test_outputs.py', 'solve.sh', 'instruction.md')):
                    try:
                        content = z.read(name).decode('utf-8', errors='ignore')
                        file_contents[os.path.basename(name)] = content[:2000]
                    except Exception:
                        pass

        # Run Groq AI Analysis
        agent = GroqTaskAgent(api_key=groq_api_key)
        ai_response = agent.analyze_audit_results(audit_results, file_contents=file_contents)

        audit_results["ai_analysis"] = ai_response

        # Save to DB
        audit_id = db.save_audit(audit_results)
        audit_results["db_audit_id"] = audit_id

        return jsonify({
            "status": "SUCCESS",
            "data": audit_results
        })

    except Exception as e:
        return jsonify({"status": "ERROR", "message": f"Audit execution error: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_zip.name):
            os.remove(temp_zip.name)

@app.route('/api/history', methods=['GET'])
def get_audit_history():
    history = db.get_recent_audits(limit=10)
    return jsonify({"status": "SUCCESS", "history": history})

@app.route('/api/task-ideas', methods=['GET'])
def get_task_ideas():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 5))
    category = request.args.get('category', 'all').strip().lower()
    search = request.args.get('search', '').strip().lower()
    show_claimed = request.args.get('show_claimed', 'false').lower() == 'true'

    claimed_map = db.get_claimed_tasks_dict()

    enriched_ideas = []
    for task in ALL_TASK_IDEAS:
        t_copy = dict(task)
        if t_copy["name"] in claimed_map:
            t_copy["is_claimed"] = True
            t_copy["claimed_by"] = claimed_map[t_copy["name"]]["claimed_by"]
            t_copy["claimed_at"] = claimed_map[t_copy["name"]]["claimed_at"]
        else:
            t_copy["is_claimed"] = False
            t_copy["claimed_by"] = None
            t_copy["claimed_at"] = None
        enriched_ideas.append(t_copy)

    # Exclude/Hide claimed tasks unless show_claimed is True
    if not show_claimed:
        enriched_ideas = [t for t in enriched_ideas if not t["is_claimed"]]

    if category != 'all':
        enriched_ideas = [t for t in enriched_ideas if t['category'].lower() == category]

    if search:
        enriched_ideas = [t for t in enriched_ideas if search in t['name'].lower() or search in t['problem_statement'].lower() or search in t['hardening_mechanism'].lower()]

    total_tasks = len(enriched_ideas)
    total_pages = (total_tasks + per_page - 1) // per_page if total_tasks > 0 else 1
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_tasks = enriched_ideas[start_idx:end_idx]

    return jsonify({
        "status": "SUCCESS",
        "total_tasks": total_tasks,
        "total_pages": total_pages,
        "current_page": page,
        "per_page": per_page,
        "show_claimed": show_claimed,
        "built_by": "Rohith Vuppula",
        "tasks": paginated_tasks
    })

@app.route('/api/claim-task', methods=['POST'])
def claim_task():
    data = request.get_json() or {}
    task_name = data.get("task_name", "").strip()
    claimed_by = data.get("claimed_by", "Friend").strip() or "Friend"

    if not task_name:
        return jsonify({"status": "ERROR", "message": "Missing task_name parameter."}), 400

    success, msg = db.claim_task(task_name, claimed_by)
    if not success:
        return jsonify({"status": "ERROR", "message": msg}), 400

    return jsonify({
        "status": "SUCCESS",
        "message": msg,
        "task_name": task_name,
        "claimed_by": claimed_by
    })

@app.route('/api/unclaim-task', methods=['POST'])
def unclaim_task():
    data = request.get_json() or {}
    task_name = data.get("task_name", "").strip()

    if not task_name:
        return jsonify({"status": "ERROR", "message": "Missing task_name parameter."}), 400

    db.unclaim_task(task_name)
    return jsonify({
        "status": "SUCCESS",
        "message": f"Task '{task_name}' has been unclaimed and restored to available task pool.",
        "task_name": task_name
    })

@app.route('/api/configure-neon-db', methods=['POST'])
def configure_neon_db():
    data = request.get_json() or {}
    neon_url = data.get("neon_url", "").strip()
    
    if not neon_url:
        return jsonify({"status": "ERROR", "message": "Missing neon_url parameter."}), 400

    cfg_path = os.path.join(os.path.dirname(__file__), "neon_config.json")
    try:
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump({"NEON_DATABASE_URL": neon_url}, f, indent=2)
        
        # Re-initialize DB connection
        global db
        db = TaskAuditDB()
        
        db_type = "Neon PostgreSQL Database" if not db.use_sqlite else "SQLite (Fallback)"
        return jsonify({
            "status": "SUCCESS",
            "message": f"Successfully configured Neon Database URL! Current Storage: {db_type}.",
            "db_type": db_type,
            "use_sqlite": db.use_sqlite
        })
    except Exception as e:
        return jsonify({"status": "ERROR", "message": f"Failed to save Neon DB config: {str(e)}"}), 500

@app.route('/api/terminus3-structure', methods=['GET'])
def get_terminus3_structure():
    return jsonify({
        "status": "SUCCESS",
        "title": "Snorkel Terminal-Bench 3 (Terminus 3) Official Task Layout",
        "structure": TERMINUS3_FOLDER_STRUCTURE
    })

@app.route('/api/download-terminus3-starter', methods=['GET'])
def download_terminus3_starter():
    zip_bytes = generate_terminus3_starter_zip_bytes()
    return send_file(
        io.BytesIO(zip_bytes),
        mimetype='application/zip',
        as_attachment=True,
        download_name='terminus3_task_starter_template.zip'
    )

@app.route('/api/download-demo-task/<task_slug>', methods=['GET'])
def download_demo_task(task_slug):
    valid_tasks = {
        "reconcile-ocean-acoustics-registry": [
            r"D:\snorkel terminal bench 3\reconcile-ocean-acoustics-registry.zip",
            r"D:\snorkeltasksubmitted\reconcile-ocean-acoustics-registry.zip",
            r"C:\Users\rohit\Downloads\reconcile-ocean-acoustics-registry.zip"
        ],
        "inference-fleet-reconciliation": [
            r"D:\snorkeltasksubmitted\inference-fleet-reconciliation.zip",
            r"C:\Users\rohit\Downloads\inference-fleet-reconciliation.zip"
        ],
        "training-pipeline-dependency-resolver": [
            r"D:\snorkeltasksubmitted\training-pipeline-dependency-resolver.zip"
        ],
        "jwt-trust-auditor-task": [
            r"D:\snorkeltasksubmitted\jwt-trust-auditor-task.zip"
        ]
    }

    paths = valid_tasks.get(task_slug, [])
    found_path = None
    for p in paths:
        if os.path.exists(p):
            found_path = p
            break

    if not found_path:
        return jsonify({"status": "ERROR", "message": f"Demo task package '{task_slug}' not found on server."}), 404

    return send_file(
        found_path,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"{task_slug}.zip"
    )

if __name__ == '__main__':
    print("Starting Snorkel AI Benchmark Auditor Web Application on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
