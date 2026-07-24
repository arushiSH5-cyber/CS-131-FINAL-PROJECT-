# Environment Setup (DGX Spark)

How to reproduce the working environment on this machine. Both partners run the
same steps so we share one setup.

## Machine (measured)

| Resource | Value |
|----------|-------|
| System | NVIDIA **DGX Spark** — GB10 Grace-Blackwell |
| CPU | 20 ARM cores (10× Cortex-X925 + 10× Cortex-A725), **arch = arm64** |
| Memory | **121 GB unified** (CPU+GPU share one pool — no separate VRAM) |
| GPU | 1× NVIDIA GB10, CUDA 13.0 — **shared machine**, others use it |
| Storage | 3.7 TB NVMe, ~2.8 TB free on `/` |
| Account | `ishigaki-cs6`, **no sudo**; groups: `video`, `render`, `docker` |

Notes that affect this project:
- **arm64** → install aarch64 builds, not x86.
- **No sudo** → user-space installs only (`pip`, conda, Docker, `--user`).
- **121 GB RAM** → making pandas OOM (Phase 2) needs either a huge file or a
  memory cap. Use the `ulimit`/Docker recipe in `2_breaking/`.
- **GPU is shared and not needed** for this project (Spark runs on Dataproc).

## 1. Python environment

A venv lives at `~/final_project/.venv` (arm64, Python 3.12). Packages pinned in
`requirements.txt`.

Recreate from scratch:
```bash
cd ~/final_project
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt
```

Activate it in a shell:
```bash
source ~/final_project/.venv/bin/activate    # then `deactivate` to exit
```

Installed: pandas, pyarrow, numpy, matplotlib, seaborn, jupyterlab, ipykernel,
ijson (streaming JSON), tqdm, requests.

## 2. JupyterLab (browser notebook IDE)

A kernel named **"CS131 (venv)"** is already registered. Launch the server:
```bash
source ~/final_project/.venv/bin/activate
jupyter lab --no-browser --ip=127.0.0.1 --port=8888
```
It prints a URL with a token. Two ways to open it:
- **On the DGX desktop:** paste the URL into the machine's browser.
- **From your laptop:** SSH-forward the port, then open the URL locally:
  ```bash
  ssh -N -L 8888:127.0.0.1:8888 ishigaki-cs6@<dgx-host>
  ```

## 3. VSCode

`code` is not installed on the server, and there's no sudo. Two good options:
- **Recommended — VSCode Remote-SSH from your laptop:** install the "Remote -
  SSH" extension in your local VSCode, connect to `ishigaki-cs6@<dgx-host>`,
  open `~/final_project`. The VSCode server auto-installs into your home dir; no
  admin needed. Pick the "CS131 (venv)" kernel for notebooks.
- **Alternative — code-server (VSCode in a browser):** run it via Docker (see
  below) if you can't use Remote-SSH.

## 4. Docker

You're in the `docker` group, so Docker works without sudo. The **`nvidia`
runtime is available** (GPU containers possible, though unused here).

Verified: `docker run --rm hello-world` → works.

Handy patterns:
```bash
# JupyterLab in a container (alternative to the venv), project mounted:
docker run --rm -p 8888:8888 -v ~/final_project:/home/jovyan/work \
  quay.io/jupyter/scipy-notebook:latest

# code-server (browser VSCode) on port 8080:
docker run --rm -p 8080:8080 -v ~/final_project:/home/coder/project \
  codercom/code-server:latest

# GPU-enabled container (only if ever needed):
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:13.0-base-ubuntu24.04 nvidia-smi
```
> Images must be arm64/multiarch. Be a good citizen — this box is shared.

## 5. Google Cloud SDK (Phase 3, later)

`gcloud`/`gsutil` are not installed yet. When we reach Phase 3:
```bash
# user-space install, no sudo:
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

## Data location

Raw data lives under `~/final_project/data/` which is **git-ignored** — never
committed. Multi-GB files stay here (or in GCS for Phase 3), never in the repo.
