# Render Deployment Guide

**Project**: Snorkel AI Benchmark Task Auditor Agent  
**Author**: Rohith Vuppula  

This guide provides step-by-step instructions for deploying the **Snorkel AI Benchmark Task Auditor Agent** web application to **[Render](https://render.com)**.

---

## 🚀 Step-by-Step Deployment Instructions

### Step 1: Push Code to GitHub / GitLab
1. Initialize Git repository (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Snorkel AI Task Auditor by Rohith Vuppula"
   ```
2. Push your repository to GitHub or GitLab:
   ```bash
   git remote add origin https://github.com/rohith1246/snorkel.git
   git branch -M main
   git push -u origin main
   ```

---

### Step 2: Deploy on Render
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** → Select **Web Service**.
3. Connect your GitHub repository (`rohith1246/snorkel`).
4. Fill in the deployment details:
   - **Name**: `snorkel-task-auditor`
   - **Environment**: `Python 3`
   - **Region**: Choose closest to you (e.g. `Oregon` or `Frankfurt`)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

---

### Step 3: Add Environment Variables
Under the **Environment Variables** section in Render, add the following keys:

| Environment Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API Key (from console.groq.com) |
| `PYTHON_VERSION` | `3.11.0` |
| `NEON_DATABASE_URL` | *(Optional)* Neon PostgreSQL Database URL |

---

### Step 4: Complete Deployment
1. Click **Create Web Service**.
2. Render will automatically build your app and deploy it.
3. Once the build finishes, your live URL will be active (e.g. `https://snorkel-task-auditor.onrender.com`).
