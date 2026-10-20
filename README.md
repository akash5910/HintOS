# HintOS

HintOS is an Operating Systems tutor that runs on your computer. It uses a local language model for conversation, BGE and FAISS to find relevant class notes, and Python checks for Banker’s Algorithm answers. The local model can explain concepts, follow earlier turns, guide a solution, and check student work without sending questions to a cloud service.

For a clean transfer checklist, see [RUN_ON_ANOTHER_MACHINE.md](RUN_ON_ANOTHER_MACHINE.md). It covers online setup and preparing an offline copy for another computer.

## First-time setup on Windows

The code uses Python 3.12. The project also needs Ollama and the local chat model. Do this setup while the computer has internet access; after both models are downloaded, HintOS can run without internet.

1. Keep the Ollama executable in the project's `ollama/` folder, or install [Ollama for your operating system](https://ollama.com/download). The HintOS scripts start their own local service; you do not need to keep the Ollama app open.
2. Open PowerShell in this folder. Download the [Qwen 3.5 model](https://ollama.com/library/qwen3.5) for the tutor (about 2.7 GB):

   ```powershell
   .\setup_local_ai.ps1
   ```

   HintOS starts a project-specific, local-only Ollama service on `127.0.0.1:11435` and stores the model inside this project: `ollama/Models/models` on Windows, or `ollama/models` on macOS/Linux. This keeps the large model files out of Ollama's default `C:\Users\<you>\.ollama\models` folder. Ollama may still keep small settings or key files in your user profile. Keep the project on a drive with enough free space.

   The default is `qwen3.5:2b`, which is a current, compact model suitable for computers with limited memory. On a computer with more memory, use the stronger `qwen3.5:4b` model by setting `$env:HINTOS_LOCAL_MODEL="qwen3.5:4b"` before running the setup script. The 4B download is about 3.4 GB.

3. Create the Python environment and install the app packages if you have not done so:

   ```powershell
   py -3.12 -m venv .venv312
   .\.venv312\Scripts\Activate.ps1
   python -m pip install --no-cache-dir -r requirements.txt
   python prepare_model.py
   ```

   `prepare_model.py` downloads BGE, the separate model used to search the OS notes. Keep the created `models/bge-small-en-v1.5` folder.

4. Start HintOS:

   ```powershell
   .\run_hintos.ps1
   ```

5. Open http://127.0.0.1:8000. The status under the title should say **Local OS tutor is ready**.

## Running offline

After first-time setup, the Qwen model is stored in the project-local `ollama` folder, BGE in `models/bge-small-en-v1.5`, and Python packages in the environment. Run `run_hintos.ps1` on Windows or `./run_hintos.sh` on macOS/Linux. The launcher starts a project-specific Ollama service, preloads Qwen into memory, sets offline flags, and disables Ollama cloud features. The initial model warm-up can take several seconds; keeping the model loaded for 30 minutes makes subsequent replies faster. No cloud AI service is used.

If the launcher cannot start Ollama, install the native Ollama executable or restore the project's `ollama/` folder. If the status says the model is missing, reconnect to the internet and run `setup_local_ai.ps1` (or `bash setup_local_ai.sh`) once; it downloads the model into the project folder.

For a computer that will never have internet access, prepare it before disconnecting: install Python, create the environment, install the packages, run `python prepare_model.py`, and run `setup_local_ai.ps1` (or `bash setup_local_ai.sh`). These scripts place the Qwen model in the project's own `ollama` folder.

## Moving HintOS to another computer

HintOS uses project-relative paths, so the source folder does not depend on this computer's `C:` or `D:` paths. A code-only copy is not a complete offline install: the Python packages, BGE search model, Qwen model, and a native Ollama executable are required. Do not copy a virtual environment between computers or operating systems; create a new one on each target computer.

The `.gitignore` excludes generated model files and the Ollama bundle to keep them out of source control. When making an offline transfer zip, deliberately include `models/bge-small-en-v1.5/`, `ollama/`, and (if needed) `offline_wheels/`.

For a target computer that has internet during setup:

1. Copy the HintOS source folder, `knowledge/`, `models/bge-small-en-v1.5/`, and the project `ollama/` folder to it. The model assets can be several gigabytes. For Windows-to-Windows transfer, the `ollama/` folder can include the Windows Ollama executable and its model store. On another operating system, install that OS's native Ollama executable and copy the model store into `ollama/models/`.
2. Install Python 3.12. If the copied `ollama/` folder does not include a compatible executable, install Ollama for that computer's operating system.
3. Create a fresh Python environment and install `requirements.txt`. If BGE was not copied, run `python prepare_model.py` while online.
4. If the Qwen model was not copied, run `setup_local_ai.ps1` (or `bash setup_local_ai.sh`) while online. This pulls it into the project-local model store.
5. Run the matching HintOS launcher. It starts Ollama on the project's private local port and uses only the model store under the project folder.

For a computer that must be set up without internet, first finish the normal online setup on a computer with the **same operating system, CPU type, and Python version** as the target. That makes the Python environment available to download BGE and Qwen. Then:

1. Install Python 3.12 and run `prepare_offline.ps1` on Windows or `bash prepare_offline.sh` on macOS/Linux. This saves pip packages in `offline_wheels/` for that platform. Wheel files are platform-specific; one wheel folder is not guaranteed to work on Windows, macOS, and Linux.
2. Run `python prepare_model.py` to create `models/bge-small-en-v1.5`.
3. Run `setup_local_ai.ps1` to download the selected chat model into the project's `ollama` folder. The Windows project can use the included Windows Ollama executable; other operating systems need their native Ollama executable.
4. Copy the entire HintOS folder, including `knowledge/`, `models/bge-small-en-v1.5/`, `offline_wheels/`, and `ollama/`, to the target. Keep the folder structure intact. Do not copy `.venv` folders. The Windows `ollama/` executable can only be reused on another compatible Windows computer; install native Ollama on a different operating system.
5. On Windows, create a new environment and install from the wheel cache:

   ```powershell
   py -3.12 -m venv .venv312
   .\.venv312\Scripts\python.exe -m pip install --no-cache-dir --no-index --find-links offline_wheels -r requirements.txt
   ```

   On macOS/Linux, use the matching OS-specific wheel cache:

   ```sh
   python3.12 -m venv .venv
   .venv/bin/python -m pip install --no-cache-dir --no-index --find-links offline_wheels -r requirements.txt
   ```

6. Run the matching HintOS launcher and open `http://127.0.0.1:8000`. The launcher reads the model from the copied project-local `ollama` folder and does not use the default C: user model store.

The local OS notes and SQLite history travel with the project if copied. The ignored `hintos.db` file is created separately on a new copy, so old attempt history is not included unless you copy that file yourself. A phone or another computer can use the tutor through a browser on the same local network, but the host computer must stay on and run HintOS.

On macOS or Linux, use that operating system's Ollama and Python packages (do not copy a Windows virtual environment), then run:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --no-cache-dir -r requirements.txt
python prepare_model.py
bash setup_local_ai.sh
bash run_hintos.sh
```

Phone/tablet browsers can connect to a computer running HintOS on the same local network, but the tutor model itself runs on the host computer.

## How the tutor answers

- The local chat model reads the current message, earlier turns, and relevant retrieved OS notes.
- Basic concept questions get a direct explanation. For problem-solving exercises, HintOS starts with one small hint, checks submitted work, and progresses through Recall, Identify, Diagnose, Direct, and Scaffold. After five unsuccessful work attempts it shows a worked solution; students can also request one at any time. Clarification questions do not count as failed attempts, and a clearly confirmed correct answer resets the attempt count.
- Banker’s Algorithm Need matrices and safe sequences are checked by Python code, not guessed by the language model.
- The SQLite database keeps recent attempts and the active numeric problem across app restarts.
- `knowledge/` has summaries for the seven syllabus modules. Add `.txt`, `.md`, `.pdf`, or `.pptx` notes there and restart HintOS to index them.
- If Ollama is unavailable, the app reports the local model problem instead of pretending to generate a tutoring answer. Full conversational tutoring needs the local model to be installed and running.

## Configure the model

The default local model is `qwen3.5:2b`. To use the stronger 4B model on a computer with more memory, set this before setup and each time you start the app:

```powershell
$env:HINTOS_LOCAL_MODEL="qwen3.5:4b"
```

The launcher binds HintOS to `127.0.0.1` by default. To let another device on your local network use it, set `HINTOS_BIND_HOST=0.0.0.0` before launching, then open the host computer's local IP address on port 8000 from that device. Ollama stays bound to `127.0.0.1` and is never exposed to the network.

See `TEST_CASES.md` for OS tutoring and numerical examples.

## Main files

- `app.py` serves the page, chat, model status, history, and Banker checker.
- `tutor.py` keeps chat context and verifies Banker’s Algorithm answers.
- `llm/client.py` talks to the local Ollama model and builds the OS tutor prompt.
- `rag/retriever.py` parses course files, chunks them, and searches with BGE and FAISS.
- `knowledge/` contains course notes and module summaries.
- `setup_local_ai.ps1` downloads the default Ollama model.
- `run_hintos.ps1` starts the app in offline mode.
