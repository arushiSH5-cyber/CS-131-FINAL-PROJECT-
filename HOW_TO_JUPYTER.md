# How to Open JupyterLab on the DGX

Machine: `spark-833c` (IP `130.65.111.89`), user `ishigaki-cs6`.
The DGX has a GNOME desktop with a browser, so the simplest path is Option A.

---

## Option A — sitting at the DGX (its own screen + browser)

1. Open a **Terminal** on the DGX desktop.
2. Activate the project environment:
   ```bash
   source ~/final_project/.venv/bin/activate
   ```
3. Go to the project and launch JupyterLab:
   ```bash
   cd ~/final_project
   jupyter lab
   ```
4. A browser tab opens automatically at `http://localhost:8888/lab`.
   (If it doesn't, copy the `http://127.0.0.1:8888/lab?token=...` line the
   terminal printed and paste it into the DGX's browser.)
5. In JupyterLab, open `4_analysis/explore_gharchive.ipynb` and, top-right,
   select the kernel **"CS131 (venv)"**.
6. To stop the server: go back to the terminal and press **Ctrl-C**, then `y`.

---

## Option B — from your laptop over SSH (port forwarding)

Use this if you're not physically at the DGX.

1. **On the DGX** (SSH in first: `ssh ishigaki-cs6@130.65.111.89`), start a
   headless server:
   ```bash
   source ~/final_project/.venv/bin/activate
   cd ~/final_project
   jupyter lab --no-browser --ip=127.0.0.1 --port=8888
   ```
   Leave this terminal running. Copy the printed
   `http://127.0.0.1:8888/lab?token=...` URL.

2. **On your laptop** (a second terminal) forward the port:
   ```bash
   ssh -N -L 8888:127.0.0.1:8888 ishigaki-cs6@130.65.111.89
   ```
   Leave this running too.

3. **On your laptop**, paste the `http://127.0.0.1:8888/lab?token=...` URL into
   your browser. You're now using the DGX's Jupyter through the tunnel.

---

## Troubleshooting

- **`jupyter: command not found`** → you forgot step 2 (`source ...venv/bin/activate`).
- **`Address already in use` (port 8888)** → someone else is using it (shared
  box). Pick another port, e.g. `--port=8890`, and match it in the `ssh -L
  8890:127.0.0.1:8890 ...` command.
- **Lost the token URL** → run `jupyter server list` on the DGX to reprint it.
- **Kernel "CS131 (venv)" missing** → re-register it:
  ```bash
  ~/final_project/.venv/bin/python -m ipykernel install --user \
    --name cs131 --display-name "CS131 (venv)"
  ```
