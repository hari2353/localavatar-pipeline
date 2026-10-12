"""Generate a photorealistic human host face locally (SD 1.5, fp16, ~4GB VRAM).

Usage (.venv python):
  .\\.venv\\Scripts\\python scripts/make_host_face.py --out assets/host.png --seed 42
Model snapshot lives in models/sd15 (gitignored, downloaded once).
"""
import argparse
from pathlib import Path

MODEL = "runwayml/stable-diffusion-v1-5"
LOCAL = Path(__file__).resolve().parents[1] / "models" / "sd15"

PROMPT = ("studio portrait photo of a friendly news presenter, 30s, gender-neutral, "
          "short dark hair, warm confident smile, plain dark background, "
          "soft key light, sharp focus, photorealistic, 85mm")
NEGATIVE = "cartoon, painting, illustration, blurry, distorted face, extra teeth, watermark, text"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets/host.png")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--steps", type=int, default=28)
    args = ap.parse_args()

    import torch
    from diffusers import StableDiffusionPipeline

    src = str(LOCAL) if LOCAL.exists() else MODEL
    pipe = StableDiffusionPipeline.from_pretrained(src, torch_dtype=torch.float16)
    pipe.enable_attention_slicing()
    pipe.enable_vae_slicing()
    pipe = pipe.to("cuda")
    img = pipe(PROMPT, negative_prompt=NEGATIVE, height=512, width=512,
               num_inference_steps=args.steps,
               generator=torch.Generator("cuda").manual_seed(args.seed)).images[0]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    if not LOCAL.exists():
        pipe.save_pretrained(LOCAL)
    print(f"FACE OK -> {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
