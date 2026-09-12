from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch
from lmformatenforcer import JsonSchemaParser
from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn
from PIL import Image
from transformers import AutoProcessor, BitsAndBytesConfig, Qwen2_5_VLForConditionalGeneration

from argus.config import ROOT, device_name, digest, read_config, write_json
from argus.modules.m4_reasoning import generate_validated, load_claims
from argus.schema import Evidence, VLMOutput


def main() -> None:
    parser = argparse.ArgumentParser(description="Resumable offline Qwen VLM batch job")
    parser.add_argument("--manifest", type=Path, required=True, help="JSON list of clip_id and evidence_path")
    parser.add_argument("--output", type=Path, default=Path("data/cache/vlm"))
    parser.add_argument("--device", default="auto")
    parser.add_argument("--fallback-3b", action="store_true")
    parser.add_argument("--without-evidence", action="store_true")
    parser.add_argument("--no-quantize", action="store_true")
    args = parser.parse_args()
    cfg = read_config("model/vlm.yaml")
    device = device_name(args.device)
    model_id = cfg["fallback_model_id"] if args.fallback_3b else cfg["model_id"]
    quantized = device == "cuda" and not args.no_quantize
    kwargs = {"device_map": "auto"} if quantized else {"torch_dtype": torch.float32}
    if quantized:
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16
        )
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(model_id, **kwargs).eval()
    if not quantized:
        model.to(device)
    processor = AutoProcessor.from_pretrained(
        model_id, min_pixels=256 * 28 * 28, max_pixels=cfg["max_pixels"]
    )
    prefix = build_transformers_prefix_allowed_tokens_fn(
        processor.tokenizer, JsonSchemaParser(VLMOutput.model_json_schema())
    )
    for row in json.loads(args.manifest.read_text()):
        evidence = Evidence.model_validate_json((ROOT / row["evidence_path"]).read_text())
        images = [
            Image.open(ROOT / k.path).convert("RGB") for k in evidence.keyframes[: cfg["max_keyframes"]]
        ]
        if not images:
            raise ValueError(f"No keyframes for {row['clip_id']}")
        signature = digest(
            {
                "model": model_id,
                "config": cfg,
                "without_evidence": args.without_evidence,
                "evidence": evidence.model_dump(),
                "images": [hashlib.sha256(image.tobytes()).hexdigest() for image in images],
            }
        )
        output = args.output / f"{row['clip_id']}.json"
        metadata = output.with_suffix(".meta.json")
        if (
            output.exists()
            and metadata.exists()
            and json.loads(metadata.read_text()).get("signature") == signature
        ):
            load_claims(output)
            print(f"CACHE HIT {row['clip_id']}")
            continue
        prompt = (
            "Describe only observable content using the JSON schema. Never rate severity or recommend actions. Entity presence claims should use 'A bag is visible.' or '2 people are visible in the scene.' All actions, intent and uncertain facts must be INFERENCE or UNCERTAINTY. Use clip-relative seconds.\n"
            + json.dumps(VLMOutput.model_json_schema())
        )
        if not args.without_evidence:
            prompt += "\nDetector evidence (fallible): " + evidence.model_dump_json()

        def generate(text: str, images: list[Image.Image] = images) -> str:
            content = [{"type": "image", "image": image} for image in images] + [
                {"type": "text", "text": text}
            ]
            messages = [{"role": "user", "content": content}]
            formatted = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = processor(text=[formatted], images=images, return_tensors="pt", padding=True).to(
                model.device
            )
            with torch.inference_mode():
                tokens = model.generate(
                    **inputs,
                    max_new_tokens=cfg["max_new_tokens"],
                    do_sample=False,
                    prefix_allowed_tokens_fn=prefix,
                )
            return str(
                processor.batch_decode(tokens[:, inputs.input_ids.shape[1] :], skip_special_tokens=True)[0]
            )

        claims = generate_validated(generate, prompt)
        write_json(output, claims.model_dump(mode="json"))
        write_json(
            metadata,
            {
                "signature": signature,
                "model": model_id,
                "quantized": quantized,
                "evidence_conditioned": not args.without_evidence,
            },
        )
        print(f"CACHED {row['clip_id']}")


if __name__ == "__main__":
    main()
