import json

import gradio as gr

from argus.config import ROOT

records = json.loads((ROOT / "data/sample/incidents.json").read_text())


def inspect(clip):
    record = next(r for r in records if r["source"]["clip_id"] == clip)
    return str(ROOT / record["source"]["video_path"]), record


with gr.Blocks(title="ARGUS offline sample") as app:
    gr.Markdown(
        "# ARGUS offline sample\nSynthetic footage and authored claims. Research calibration remains pending. No automated dispatch."
    )
    choice = gr.Dropdown(
        [r["source"]["clip_id"] for r in records], label="Clip", value=records[0]["source"]["clip_id"]
    )
    video = gr.Video(label="Synthetic clip")
    record = gr.JSON(label="Auditable incident record")
    choice.change(inspect, choice, [video, record])
    app.load(inspect, choice, [video, record])

if __name__ == "__main__":
    app.launch(server_name="127.0.0.1", share=False)
