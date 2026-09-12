# Research workflows

## Data acquisition

Run `python -m argus.cli data`. Each dataset either downloads with a trusted expected SHA256 or prints precise manual instructions. Official pages and mutable download links live in `configs/data_sources.yaml`. A locally computed checksum records bytes; without a trusted expected checksum it is labelled RECORDED_NOT_AUTHENTICATED. Gated archives are not downloaded by bypassing consent. Use `docs/DATA_FORMATS.md` to prepare the unified index.

## Detector training and held out evaluation

Install optional research dependencies with `pip install -e '.[research]'`. Prefer pre-released I3D or CLIP features and set input dimensions from actual arrays. Do not mix feature families in one checkpoint. Split by source video, with no adjacent source windows in different splits. The training script rejects duplicate clip IDs across splits, but the dataset creator must provide original-video group IDs and check semantic duplicates.

```sh
python scripts/train/detector.py --index data/index/ucf_crime.parquet --epochs 30 --device auto
python scripts/eval/detector.py --index data/index/ucf_crime.parquet --checkpoint artifacts/checkpoints/detector.pt --device cpu
python scripts/eval/crossdataset.py --index data/index/xdviolence.parquet --checkpoint artifacts/checkpoints/detector.pt --device cpu
```

Test evaluation requires real per-frame labels, correct source FPS and explicit snippet duration. Train/validation identifiers stored in the checkpoint cannot reappear in evaluation. XD-Violence is never a training source. UCF AUC and XD AP are separate results. Published PEL4VAD 86.76% is a literature reference, not an ARGUS measurement or equivalent compute protocol.

## Evidence and offline language generation

Extract features using `scripts/features.py`. Build evidence using `build_evidence` from M3 and a manifest of clip IDs plus evidence JSON paths. The research batch notebook explains packaging the repository, selected licensed clips and evidence for a free GPU notebook. Run `python scripts/batch_vlm.py --manifest data/cache/vlm_manifest.json`. Use `--fallback-3b` only after accepting that checkpoint's distinct research licence. `--device cpu --no-quantize` is supported but can require substantial memory and time. Four-bit GPU operation is optional and does not guarantee a specific VRAM footprint.

The batch job saves after every clip and uses a signature over model ID, configuration, evidence and keyframe pixels. Completed valid matching caches are skipped. Use separate output directories for 3B/7B and with/without-evidence ablations. A free GPU quota is not guaranteed and must be checked in the user's account. No cloud session has been launched or billed by this delivery.

## Run a real local clip

```sh
python scripts/run_clip.py data/raw/local/example.mp4 --claims data/cache/vlm/example.json --checkpoint artifacts/checkpoints/detector.pt --severity-model artifacts/checkpoints/severity.json --device cpu --blur-faces
```

The clip stays inside the project. Real source playback in the console requires a supported browser codec and explicitly registered media; do not expose an arbitrary filesystem directory. Optional privacy rendering blurs the whole derived keyframe because a face detector cannot guarantee recall. It leaves raw input untouched.

## SIRB sampling and independent annotation

Run `scripts/data/sample_sirb.py --index data/index/ucf_crime.parquet`. The default selects up to 250 clips, with a deterministic category/expected-severity round robin and 20% overlap. The assignment file is the routing manifest. Assign different annotator names. The default studio is a local collaboration tool, not an authenticated study platform; independent operators must avoid the adjudication view until both ratings are locked. Source-video grouping, demographics, diversity and licence checks need human review.

Join independent ratings by clip ID, export paired score arrays, and run `scripts/eval/interannotator.py`. Fit severity using pipeline factor vectors, not human factor entries, with `scripts/train/severity.py`. Evaluate predictions and human scores on untouched test clips using `scripts/eval/severity.py`. Eight rows are a software minimum, not an adequate sample-size recommendation. Report distributions, uncertainty and annotator disagreement before making conclusions.

## Evaluation artifacts and release

Each research evaluator writes `artifacts/research/*.json`. `python -m argus.cli eval` recomputes sample verification and policy checks, imports existing research outputs and regenerates the console metrics and RESULTS.md. It does not implicitly launch expensive training or research inference. Re-run the individual research commands when inputs or checkpoints change. The status document records this difference from the brief's single-command ideal.

`scripts/data/export_sirb.py` exports completed real-source annotations only and excludes sample practice labels. `reconstruct_sirb.py` maps annotation clip IDs to locally available source records. The package contains no original source video. Licensing and publication approval remain prerequisites for Zenodo submission. This delivery does not publish a DOI or upload private material.

