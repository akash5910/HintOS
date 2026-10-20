# Run HintOS on another computer

This guide is for transferring and running the complete HintOS project on a different computer. HintOS runs the web app, the chat model, and OS note search locally. Once the required files are present, it does not need internet access.

## Option A: Set up the new computer while it has internet

1. Copy the whole HintOS project folder to the new computer. Keep its directory structure intact. Include the application files and folders: `app.py`, `tutor.py`, `llm/`, `rag/`, `knowledge/`, `static/`, `problems/`, `requirements.txt`, `prepare_model.py`, `setup_local_ai` and `run_hintos` scripts, and the README files.
2. Install Python 3.12 on the new computer. Do not copy `.venv`, `.venv312`, or another computer's Python environment; environments contain machine-specific paths and native packages.
3. Open a terminal in the copied project folder and create a fresh environment, then install the packages.

   **Windows PowerShell:**

   ```powershell
   py -3.12 -m venv .venv312
   .\.venv312\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
   .\.venv312\Scripts\python.exe prepare_model.py
   .\setup_local_ai.ps1
   .\run_hintos.ps1
   ```

   **macOS/Linux:** Install the native Ollama app for that operating system, then run:

   ```sh
   python3.12 -m venv .venv
   .venv/bin/python -m pip install --no-cache-dir -r requirements.txt
   .venv/bin/python prepare_model.py
   bash setup_local_ai.sh
   bash run_hintos.sh
   ```

4. Open `http://127.0.0.1:8000` on the new computer. The status should say **Local OS tutor is ready**.

The setup scripts download the configured Ollama chat model and the BGE note-search model into the project. Allow several gigabytes for the chat model. HintOS keeps its Ollama model store in the project folder instead of the default per-user model directory.

## Option B: Prepare a complete offline copy

Do these steps on a computer with internet before transferring the project. Prepare assets for the same operating system, CPU architecture, and Python version as the offline target; native Python wheels and Ollama executables are platform-specific.

1. On the preparing computer, install Python 3.12 and Ollama, then run the online setup steps above. This creates `models/bge-small-en-v1.5/` and downloads the chat model into `ollama/`.
2. Download Python packages for offline installation:

   **Windows:**

   ```powershell
   .\prepare_offline.ps1
   ```

   **macOS/Linux:**

   ```sh
   python3.12 prepare_model.py
   python3.12 -m pip download --no-cache-dir --only-binary=:all: --dest offline_wheels -r requirements.txt
   ```

   `offline_wheels/` is for the matching OS, CPU architecture, and Python version. If pip cannot find a compatible wheel for a dependency, complete the dependency installation on the target while it is online or prepare that dependency for the target platform separately.
3. Copy the project source plus `knowledge/`, `models/bge-small-en-v1.5/`, `ollama/`, and `offline_wheels/` to the target. Keep the folder layout. Do not copy `.venv*` folders or `.cache/`.
4. On the offline target, install Python 3.12 and create a new environment using the copied wheel cache.

   **Windows PowerShell:**

   ```powershell
   py -3.12 -m venv .venv312
   .\.venv312\Scripts\python.exe -m pip install --no-index --find-links offline_wheels -r requirements.txt
   .\run_hintos.ps1
   ```

   The project `ollama/` folder must contain a Windows-compatible `ollama.exe`. If it does not, install Ollama on the target before disconnecting it. The model files must be in `ollama/Models/models/` (or `ollama/models/`).

   **macOS/Linux:**

   ```sh
   python3.12 -m venv .venv
   .venv/bin/python -m pip install --no-index --find-links offline_wheels -r requirements.txt
   bash run_hintos.sh
   ```

   Install the target operating system's native Ollama app before taking it offline; the Linux/macOS launcher uses the native `ollama` command from `PATH`. Copy the model store into `ollama/models/`.

5. Open `http://127.0.0.1:8000`. If the local model is reported missing, verify the model name and the project-local `ollama` model-store path.

## Moving between different operating systems

The source code and course notes can move between operating systems. Do not reuse `.venv*`, `offline_wheels/`, or an Ollama executable from a different operating system or CPU architecture. Install native Python 3.12 and Ollama on the target, recreate the Python environment there, and use model files prepared for that Ollama installation. A Windows `ollama.exe` only runs on compatible Windows systems.

## What travels with the project

- `knowledge/`: OS notes used by the tutor.
- `models/bge-small-en-v1.5/`: local note-search model.
- `ollama/`: local chat model store and, on Windows, possibly the Ollama executable.
- `offline_wheels/`: optional Python packages for one specific target platform.
- `hintos.db`: optional chat history. It is created on first run and is ignored by Git; copy it separately only if the history should move too.

See [README.md](README.md) for troubleshooting, model selection, and local-network access.
