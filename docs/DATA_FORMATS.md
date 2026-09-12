# Data formats

## Unified dataset index

Place `index.csv` beside each manually obtained dataset and run its fetcher. Required columns are `clip_id,source_dataset,split,label,category,duration_s,fps,path_video,path_features,has_captions,has_sirb_labels`. Splits are train, val, test or demo. Labels are binary 0 or 1. Paths are relative to the project root. Features are finite float32 arrays with shape [snippets, dimension], loaded with pickle disabled. Optional `expected_severity` supports stratification. The index writer preserves extra evaluation columns.

Frame evaluation additionally requires `path_frame_labels` pointing to a binary NumPy vector with one entry per source frame, and `snippet_s` giving the feature interval in seconds. Do not substitute video-level labels. CLIP extraction here uses 16 frames at 25 fps, so snippet_s is 0.64. Pre-released I3D arrays may have different spacing or crop axes; convert them explicitly and record the transformation.

## Pair evaluation files

Localisation accepts a JSON array of `{clip_id, predicted: [start,end], truth: [start,end]}`. Severity and inter-annotator evaluation accept `{clip_id, a, b}` rows; severity requires `split: "test"`. Values `a` and `b` are score pairs in 0–100. Undefined correlation or agreement for constant labels returns null rather than a fabricated zero.

Severity fitting accepts `{clip_id, split, score, pipeline_factors, sample}` records. `pipeline_factors` must provide all thirteen factor names in the configured order with values between 0 and 1. `sample: true` forces the fitted model to say SYNTHETIC FIT ONLY. Train and test must be disjoint. The intended source of pipeline factors is `m6_severity.factors[].raw` joined to independent human ratings.

## VLM manifest

A JSON array with `clip_id` and `evidence_path` entries drives the offline batch. Each evidence path points to an Evidence schema JSON containing local keyframe paths. Model cache files contain only `claims`. Every claim requires `claim_id`, `text`, `type`, `entities`, `time_span_s`, `self_confidence` and an optional structured predicate/count map. Consult the generated OpenAPI schema rather than retyping interfaces.

## Ablations

`scripts/eval/ablations.py` expects rows with `variant, clip_id, n_claims, n_rejected`. Required variants are 7b_evidence_critic, 7b_no_evidence_critic, 3b_evidence_critic and 7b_evidence_no_critic. The same clip IDs must appear exactly once per variant. For the no-critic variant, use independently scored unsupported claims; simply setting rejection count to zero would conceal errors. Current tooling aggregates counts; it does not manufacture missing variant runs.

