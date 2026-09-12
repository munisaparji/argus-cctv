# Build completion and research acceptance

The local software delivery is runnable. Completion of a research study requires evidence that software alone cannot generate. The table distinguishes implementation from the brief's research acceptance criteria.

| Phase | Delivered | Acceptance still dependent on external work |
| --- | --- | --- |
| 0 Foundation | Package, setup scripts, Makefile, lint, types, tests and CI | CI must execute after a repository push |
| 1 Sample and schema | Eight synthetic clips, typed records and seven-stage CPU run | None for the local sample |
| 2 Data | Resumable checksum fetchers, manual instructions and parquet index validation | Real licensed datasets, trusted hashes and normalized indexes |
| 3 Detector | Four-layer transformer, MIL objective, training, TensorBoard and frame evaluator | Full UCF training and measured held-out AUC; no 84% claim |
| 4 Evidence | Pixel sample detector, DETR adapter, geometric tracker and keyframes | Model download and visual review on twenty real clips |
| 5 Language | Qwen grammar-constrained batch adapter, cache validation and notebook | Free-GPU execution and at least 250 real VLM outputs |
| 6 SIRB | Studio, independent sessions, sampling, codebook and export | Human annotation, timing study, locked independent study routing |
| 7 Critic | Conservative object/count/window rules and adversarial tests | Real-language validity study with independent labels |
| 8 Severity and policy | Constrained ordinal fitter, factor tracing and 12-action validator | Human calibration and held-out kappa, rho and MAE |
| 9 Console | React screens, API, static demo, WebSockets and audit | Production authentication, full accessibility certification |
| 10 Evaluation and release | Scripted metrics, figures, ablation aggregation and local package | Real benchmark runs, model ablations, public hosting and DOI |
| 11 Academic | Technical guide, review deck, poster, LaTeX source, DOI metadata and viva bank | Replace pending research tables only after real evaluation |

## Deliberate implementation differences

The sample detector is a labelled motion baseline, not a trained model. The real detector is binary; a 13-class prediction head is not implemented. M3 uses DETR and a simple IoU tracker, not ByteTrack or BoT-SORT. Seven severity factors remain unavailable automatically because no independent event/context verifier exists. The critic accepts a narrow sentence grammar to avoid overclaiming general entailment. This reduces language coverage.

The frontend uses React, Vite, TypeScript, Lucide and custom CSS. It does not depend on the brief's optional animation, component, chart or state libraries. Incident lists are not virtualized. The studio uses typed numeric span entry and blank factor ratings rather than an unvalidated model-prefill workflow. Double-annotation assignments are generated in a file; access isolation and routing are procedural, not enforced as an authenticated multi-user system.

The offline console disables writes. Small-screen presentation stacks content; the intended editing environment is desktop. The API supports local research use and does not provide multi-tenant authentication or network exposure hardening. A Docker recipe and Gradio fallback are supplied, with their runtime verification stated in the test report.

`make eval` recomputes sample metrics and incorporates existing research artifacts. It does not re-run large experiments from scratch in one command. The 20-slide review deck and manuscript describe the actual implementation and mark research findings pending. DOI metadata verification is not equivalent to full-text critical review of all fifteen papers. No publication, code-hosting push, Zenodo submission or cloud GPU job has occurred.

