import os
import tempfile
import zipfile
import json
from flask import Flask, render_template, request, jsonify, Response
from validator import SnorkelTaskValidator
from groq_agent import GroqTaskAgent
from db import TaskAuditDB

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max upload limit

db = TaskAuditDB()

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

if __name__ == '__main__':
    print("Starting Snorkel AI Benchmark Auditor Web Application on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
