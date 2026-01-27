# AI Log Analyzer

An AI-powered tool for analyzing Android Board Support Package (BSP) logs. It ingests Logcat, Bugreports, ANR traces, and Kernel logs to provide automated Root Cause Analysis (RCA) using advanced LLMs (OpenAI GPT-4o / Cambrian).

## Features

- **Multi-Format Support**: Accepts `.zip` bugreports, or individual `.txt`, `.log`, `.trace` files.
- **Smart Parsing**: Automatically extracts `bugreport`, `logcat`, and `ANR` traces from zip archives.
- **Dual LLM Support**:
  - **OpenAI**: Supports standard models (GPT-4o, GPT-3.5) with `OPENAI_API_KEY`.
  - **Cambrian**: Supports internal Pegatron Cambrian LLM Gateway (Llama 3.3 70B) for secure, on-premise analysis.
- **Visual Reports**: Generates professional PDF and HTML reports with "Executive Summary", "Technical Deep Dive", and "Recommendations".
- **Dockerized**: specific support for `linux/amd64` and `linux/arm64` architectures.

---

## 🚀 Deployment Guide (Docker)

This is the recommended way to deploy the application on any server (Ubuntu 20.04+, macOS, Windows).

### 1. Prerequisites
- Docker Installed ([Get Docker](https://docs.docker.com/get-docker/))

### 2. Pull the Image
The image is hosted on Docker Hub and supports both x86_64 and ARM64 platforms.

```bash
docker pull seen0516/log-analyzer:latest
```

### 3. Run the Container

You need to provide your API Key via environment variables.

**Option A: Run with inline API Key (Quickest)**

```bash
docker run -d \
  -p 8000:8000 \
  --name log-analyzer \
  --restart always \
  -e OPENAI_API_KEY="sk-proj-..." \
  seen0516/log-analyzer:latest
```

**Option B: Run with .env file (Recommended)**

1. Create a `.env` file:
   ```bash
   echo "OPENAI_API_KEY=sk-proj-..." > .env
   ```
2. Run the container:
   ```bash
   docker run -d \
     -p 8000:8000 \
     --name log-analyzer \
     --restart always \
     --env-file .env \
     seen0516/log-analyzer:latest
   ```

### 4. Access the UI
Open your browser and navigate to:
[http://localhost:8000](http://localhost:8000) (or your server IP)

---

## 🛠 Local Development

If you want to run the code locally without Docker:

### Prerequisites
- Python 3.10+
- Google Chrome (for PDF report generation)

### Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/seen0722/log-analyzer.git
   cd log-analyzer
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Server**
   ```bash
   uvicorn main:app --reload
   ```

---

## 🔑 API Key Management

The UI supports inputting keys directly, but you can configure defaults:

- **OpenAI**: Set `OPENAI_API_KEY` in `.env` or Docker env.
- **Cambrian**: Set `CAMBRIAN_TOKEN` in `.env` or Docker env. Alternatively, select "Cambrian" in the UI and input your Token.
