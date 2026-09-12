# ARGUS 1.0 local delivery

The release archive contains the complete authored source, built operator console, eight synthetic sample clips, typed fixtures, setup scripts, tests, research tools, academic sources and final review materials. It excludes virtual environments, node_modules, local databases, independent annotations, third-party footage, model weights and temporary training checkpoints.

Download the ZIP and walkthrough video from the [GitHub v1.0.0 release](https://github.com/munisaparji/argus-cctv/releases/tag/v1.0.0). The source repository includes the smaller review documents directly. The release and repository require access to the private `munisaparji/argus-cctv` repository.

## Review materials

- `deliverables/ARGUS_Project_Guide.pdf`: 20-page explanation of setup, architecture, API, data formats, workflows, annotation, results, ethics, licences, completion status, literature and viva questions.
- `deliverables/ARGUS_Project_Guide.md`: editable text source of the guide's technical sections.
- `deliverables/ARGUS_Review_Deck.pptx`: 20 editable slides, speaker notes and an embedded chart workbook.
- `deliverables/ARGUS_Poster.pdf`: printable A4 project overview.
- `deliverables/ARGUS_Demo_Walkthrough.webm`: approximately three minutes of recorded console interaction with explanatory captions. The recording has no audio and uses synthetic data only.
- `docs/DEMO_SCRIPT.md`: a longer five-minute live demonstration script, including operator decisions and annotation.
- `docs/paper`: IEEE-style manuscript and bibliography sources. Real study findings remain pending.

## What was verified

All 26 backend tests passed. Ruff, strict schema/module type checks and the production console build passed. Seven browser screens produced zero automated WCAG 2 A/AA violations and zero JavaScript page errors; playback and WebSocket execution passed. One synthetic training epoch exercised checkpoint creation and reloading.

All 20 guide pages, the poster and all 20 slide renders were visually checked. The presentation finalizer checked package structure, layout, fonts and the chart workbook, and reimported the exact final PPTX. Native Microsoft PowerPoint rendering was not tested.

A separate extraction regenerated the eight-clip sample, imported the extracted source, served the built console and video, and recorded an isolated decision and audit entry. This used the dependencies already installed on the Windows machine, so it does not establish a fresh dependency install or another operating system. Read `artifacts/release-check.json` and `docs/TEST_REPORT.md` for scope.

## Rebuilding and checksums

The source release script is `scripts/release/build_release.py`. It creates a ZIP with a manifest and per-file SHA256 checksums. The adjacent `.sha256` file checks the outer archive. The relocation check is `scripts/release/check_release.py`.

The PDF builder uses ReportLab. The original PPTX builder uses the Codex bundled Artifact Tool and requires `ARGUS_ARTIFACT_RUNTIME` and `ARGUS_PRESENTATION_SKILL`; the resulting PowerPoint remains directly editable without those tools. The capture scripts use installed Chrome and Playwright. For recording, install the free encoder with `npx playwright install ffmpeg` and run `node record-demo.mjs` from `apps/console` while the API is running. A custom `PLAYWRIGHT_BROWSERS_PATH` must match both commands if used.

If the Windows recorder adds uniform gray padding to initial frames, `python scripts/release/normalize_recording.py` crops that padding and preserves the recorded content at the output dimensions. The shipped recording has this correction applied.

## External research prerequisites

Real benchmark datasets, model-weight downloads, full training, VLM batches, independent human ratings and calibrated held-out evaluations have not been completed. The optional Docker and Gradio runtimes have not been exercised here. GitHub delivery does not deploy the application, publish a dataset or register a DOI. This release is runnable local research software with explicit experimental limitations.
