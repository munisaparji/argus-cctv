# Software and model licences

Project-authored code is MIT. Project-authored synthetic footage and sprites are CC0-1.0. Proposed independently authored SIRB annotation releases use CC BY 4.0 only after checking underlying source terms. No third-party model weights or benchmark video are distributed in this project package.

| Component | Licence or status | Source |
| --- | --- | --- |
| CLIP implementation and released model | MIT | https://github.com/openai/CLIP |
| DETR and selected checkpoint | Apache 2.0 | https://huggingface.co/facebook/detr-resnet-50 |
| Qwen2.5 VL 7B Instruct | Apache 2.0 | https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct |
| Qwen2.5 VL 3B Instruct | Qwen Research licence, distinct from 7B | https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct/blob/main/LICENSE |
| PyTorch | BSD style | https://github.com/pytorch/pytorch/blob/main/LICENSE |
| Transformers | Apache 2.0 | https://github.com/huggingface/transformers |
| FastAPI, React, Vite | MIT | Their package licence files |
| OpenCV | Apache 2.0 distribution includes third-party components | Installed wheel licence files |
| Geometric IoU tracker | Project-authored MIT | src/argus/modules/m3_evidence.py |

Licence review date: 11 September 2026. Model cards and licence files are authoritative. A smaller model is not automatically covered by the larger model's licence. Ultralytics is not installed or used here; the selected DETR adapter avoids introducing an AGPL dependency. Actual downloaded checkpoint revisions and model metadata should be recorded with research outputs. The current cache signature includes model ID, not a fully pinned weights revision; pin revisions before final reproducibility experiments.

