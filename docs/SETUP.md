# Setup and operation

Use Python 3.12 and Node.js 22. CPU execution is sufficient for the included sample. Keep the project in a writable local directory. All paths in application records are relative to the project root. `ARGUS_ROOT` can override the inferred root when installing elsewhere.

## Windows commands

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
cd apps\console
npm.cmd ci
cd ..\..
.\.venv\Scripts\python.exe -m argus.cli schema
cd apps\console
npm.cmd run types
cd ..\..
.\.venv\Scripts\python.exe -m argus.cli demo
cd apps\console
npm.cmd run build
cd ..\..
.\.venv\Scripts\python.exe -m argus.cli serve
```

Open http://127.0.0.1:8000. The OpenAPI documentation is at http://127.0.0.1:8000/docs. The server binds to loopback by default. A development frontend can run separately with `npm run dev`, proxying `/api` and WebSockets to port 8000.

## First review

Open the counter scene. Expand the rejected knife claim. Its reason records the missing supporting detection. Use the comparison checkbox to inspect the authored raw output, then return to the verified ledger. Select a severity factor to highlight its supporting claims. The reference weights are uncalibrated; low scores are not safety assurances. Enter an operator name and confirm, or enter a note and dismiss. Open Audit trail to see the decision.

## Starting and stopping

`start.ps1` regenerates sample outputs and starts the server. Existing decisions remain in SQLite. Repeated pipeline runs create distinct incident records. Ctrl+C stops the server. Never delete `data/argus.sqlite` if its audit or annotation data must be retained. Back up the database using SQLite backup tooling or with the server stopped.

## Offline fallback

The built `apps/console/dist` contains JavaScript, CSS, synthetic clips and JSON. Serve it using `python -m http.server 8080 --directory apps/console/dist`, then open `http://127.0.0.1:8080/?demo=1`. Direct `file://` opening is not supported because the console loads JSON using fetch. The Gradio fallback requires `pip install -e '.[gradio]'` and `python apps/gradio_fallback/app.py`.

## Troubleshooting

If the screen says Disconnected, check the API terminal and `/api/health`. Build the frontend before starting the API because static mounting is configured at startup. If source TypeScript changes, rebuild and restart. Browser-compatible synthetic previews are WebM; MP4 analysis files remain in the sample directory. For missing research weights or language caches, use the commands in Research workflows. CUDA is optional. Set `--device cpu` for research scripts on a machine without CUDA.

The Docker recipe is a packaging option and has not been run on this machine. It bootstraps the synthetic sample before binding port 7860. Map it to loopback with `docker run -p 127.0.0.1:7860:7860 argus`. Do not expose operator writes publicly without authentication, authorization, storage protection and deployment-specific origin configuration.

