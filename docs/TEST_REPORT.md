# Executed validation report

The checks below ran locally on Windows using Python 3.12 and Node.js 22. They establish software behavior in this environment. They do not establish research accuracy, real-scene safety or portability to every machine.

| Check | Result and scope |
| --- | --- |
| Backend tests | 26 passed, including critic adversarial cases, golden response policy, audit transactions, API validation, independent annotations and model gradient flow |
| Static Python checks | Ruff and strict mypy on the schema and seven modules passed |
| Frontend compilation | TypeScript checking and Vite production build passed |
| Browser workflow | Seven screens checked, sample playback succeeded, WebSocket pipeline reached completion |
| Browser accessibility | Zero automated WCAG 2 A/AA violations detected on the seven checked screens; this is not a full accessibility certification |
| Synthetic pipeline | Eight clips, 15 authored claims, two unsupported claims rejected, zero ordinary policy violations |
| Adversarial policy | Four of four unknown action tokens stripped; two valid tokens retained |
| Training smoke check | One epoch with four synthetic training bags and two validation bags; saved checkpoint reloaded and predicted eight finite snippet scores on held-out synthetic features |
| Literature metadata | Fifteen DOI records resolved through Crossref; no claim of full-text experimental replication |

The training smoke model contains 4,937,922 parameters with its 16-dimensional test input. Its temporary checkpoint is not a research model and is excluded from the release. The structured report is `artifacts/training-smoke.json`.

Browser output is recorded in `artifacts/screenshots/browser-report.json`. Pipeline metrics and actual machine-dependent timings are recorded in `artifacts/metrics.json`. The sample's observed rejection rate is evidence consistency for authored fixtures, not human-adjudicated hallucination accuracy.

## Reproduce the checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src scripts tests apps/gradio_fallback
.\.venv\Scripts\python.exe -m mypy src/argus/schema src/argus/modules --follow-imports=silent
.\.venv\Scripts\python.exe scripts/release/smoke_training.py
```

Training smoke checks require the optional `research` dependencies. For browser checks, keep the API running, install the console dependencies, then run `node browser-check.mjs` from `apps/console`. The script uses installed Google Chrome. The sample tests require the included fixture records; `python -m argus.cli demo` regenerates them.

## Checks not executed

Full CLIP, DETR and Qwen weight downloads and real dataset inference have not run. Neither GPU training nor free-cloud notebook execution has occurred. Human annotation, calibrated severity, real benchmark AUC/AP, and 7B/3B ablations remain pending. Docker and the optional Gradio UI have not been launched here. The IEEE manuscript source has not been compiled with a TeX installation. CI is supplied but has not run on a remote repository.

The Python tests emitted upstream FastAPI/Starlette dependency deprecation warnings. There were no test failures. Dependency versions used on this machine are captured separately from the portable project dependency ranges.
