"""Build the printable guide, poster, codebook, literature review and academic sources."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    CondPageBreak,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "deliverables"
OUT.mkdir(exist_ok=True)

FACTORS = [
    (
        "weapon_present",
        "Documented visible weapon presence",
        "A clearly visible weapon independently supported by detections or human evidence.",
        "An inference that a concealed object must be a knife.",
        "0 absent or unknown, 1 independently supported",
    ),
    (
        "people_involved",
        "Simultaneous involved people",
        "Two people in the same relevant frame give 0.2.",
        "Counting one person twice because a track ID changed.",
        "min(count / 10, 1)",
    ),
    (
        "physical_contact",
        "Physical interaction",
        "A visible push or strike with an evidence span.",
        "Two boxes merely overlapping in image coordinates.",
        "0 no support, 1 clearly documented interaction",
    ),
    (
        "crowd_density",
        "People count proxy",
        "Ten visible people give 0.5.",
        "Interpreting this as measured people per square metre.",
        "min(count / 20, 1)",
    ),
    (
        "incident_duration",
        "Supported event duration",
        "A 30-second supported interval gives 0.5.",
        "Including unrelated time before the event.",
        "min(seconds / 60, 1)",
    ),
    (
        "time_of_day",
        "Documented night context",
        "A reliable timestamp or explicit source context establishes night.",
        "Assuming every dark frame was recorded at night.",
        "0 day or unknown, 1 documented night",
    ),
    (
        "property_damage",
        "Visible damage",
        "A visible before/after change with a typed span.",
        "An object detector reporting a window, with no damage evidence.",
        "0 unsupported, 1 directly documented damage",
    ),
    (
        "vulnerable_person",
        "Explicit contextual vulnerability",
        "A source-provided non-biometric context documented in the note.",
        "Guessing age, disability, health or identity from appearance.",
        "0 unknown, 1 explicit contextual support",
    ),
    (
        "role_asymmetry",
        "Documented role asymmetry",
        "An independent evidence annotation describes unequal roles.",
        "Assigning victim or aggressor from clothing or appearance.",
        "0 unsupported, 1 independently documented",
    ),
    (
        "escalation",
        "Increasing event intensity",
        "Two supported spans show an increase in the event.",
        "Treating camera motion as increasing aggression.",
        "0 no support, 1 clearly documented increase",
    ),
    (
        "restricted_area",
        "Configured restricted zone",
        "A provided zone policy identifies the location as restricted.",
        "Inferring trespass from a fence alone.",
        "0 unknown, 1 configured and supported",
    ),
    (
        "vehicle_involvement",
        "Visible vehicle in the event",
        "A detected car is referenced by a supported observation.",
        "Assuming a distant static car caused the event.",
        "0 unsupported, 1 supported vehicle presence",
    ),
    (
        "detection_confidence",
        "Supporting detection reliability",
        "Mean confidence of detections referenced by verified claims.",
        "Using the VLM's self-confidence as detector reliability.",
        "0 to 1; software quality proxy, not intrinsic severity",
    ),
]


def write_supporting_docs():
    lines = [
        "# SIRB annotation protocol",
        "",
        "Use this codebook with the Annotation Studio. A short review should take about three minutes as a design aim; no annotator timing study has yet measured that target.",
        "",
        "## Review procedure",
        "",
        "1. Select your own annotator name. Do not inspect other ratings before completing the independent pass.",
        "2. Watch the clip once at normal speed, then replay only the uncertain interval. Mark start/end seconds and a concise evidence label.",
        "3. Enter the thirteen normalized factor values. Unknown means zero plus a note stating unknown, not a claim of absence. The current form does not model a separate human missingness flag, so retain the note when exporting.",
        "4. Rate overall severity from 0 to 100. LOW is 0 to below 25, MEDIUM 25 to below 50, HIGH 50 to below 75, CRITICAL 75 to 100. Choose the lower band when context does not justify a higher band, and explain uncertainty.",
        "5. Select only actions supported by the context. These are annotation labels, never a dispatch instruction. Save and complete the review.",
        "6. For disagreements of at least one band, use a third independent annotator, then review side-by-side evidence and retain both original ratings. Do not erase disagreements.",
        "",
        "## Decision tree",
        "",
        "Is the event visible? If no, describe uncertainty and avoid speculative factors. If yes, identify the evidence span and count only simultaneous people. Is any factor based on identity, motive or an unsupported event? If yes, leave it unknown. Is there enough source context for response selection? If no, choose review-oriented labels. Complete the overall rating after factor entry, then inspect it for consistency.",
        "",
        "## Factor definitions",
        "",
    ]
    for name, definition, positive, negative, scale in FACTORS:
        lines += [
            f"### {name.replace('_', ' ').title()}",
            "",
            definition + ". Scale: " + scale + ".",
            "",
            "Positive example: " + positive,
            "",
            "Counterexample: " + negative,
            "",
        ]
    lines += [
        "## Study controls",
        "",
        "The sampling manifest assigns 20% overlap. Use separate annotator sessions. The local studio does not enforce authentication or blinded access, so study administrators must control access procedurally. Synthetic practice annotations cannot be exported as real SIRB labels. Report agreement before adjudication. Record skipped clips, factor missingness, source quality and reasons for exclusions. Do not infer that a small synthetic fit establishes validity.",
        "",
        "No model suggestions are silently accepted. The current blank-form workflow has no model-prefill acceptance rate to report. If label assistance is added, record accepted unchanged versus edited suggestions explicitly and evaluate bias.",
    ]
    (ROOT / "docs/SIRB_ANNOTATION_PROTOCOL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    literature = json.loads((ROOT / "docs/literature/verified.json").read_text())
    review = [
        "# Literature review",
        "",
        "Fifteen IEEE journal references have resolved Crossref DOI metadata. The discussion below connects their stated topics to this implementation. Metadata verification does not establish reproduction of paper results, and abstracts do not replace full-text methodological review.",
        "",
    ]
    summaries = [
        "Conceptual foundation for surveillance video-language understanding. It motivates evaluating language on surveillance rather than assuming general-purpose multimodal performance transfers. ARGUS adds a conservative evidence-consistency interface; it does not claim the video-language task as novel.",
        "A reproducible weakly supervised detection comparator with an official code repository and released feature links. The published 86.76% UCF-Crime AUC is a reference from that repository. ARGUS must use matched feature, split and frame-alignment conventions before making a numerical comparison.",
        "A direct precedent for graded video violence ratings. It prevents treating graded severity itself as new. ARGUS's intended comparison concerns interpretable factors and agreement with independently collected ratings, which remain pending.",
        "A tracking baseline and useful reference for association quality. ARGUS currently uses simple geometric IoU association, so it does not inherit StrongSORT accuracy or occlusion handling. Persistent IDs in this implementation are local track labels.",
        "A normalization-focused weak-supervision reference. It motivates examining how bag composition interacts with feature statistics. ARGUS selects LayerNorm as an implementation choice, but this does not reproduce the paper's method or establish a performance improvement.",
        "A snippet-attention reference for prioritizing anomalous temporal segments. ARGUS includes a learnable attention pooling branch and tests its training path. A controlled ablation is still needed to establish its benefit.",
    ]
    for i, row in enumerate(literature):
        topic = (
            "This paper extends the comparison set for "
            + (
                "multimodal or language-guided detection"
                if re.search("language|text|audio|multimodal|vocabulary", row["title"], re.I)
                else "weakly supervised temporal and feature modeling"
            )
            + ". Its contribution should be compared on matched datasets and splits. ARGUS does not reproduce or claim its published performance. Full-text protocol details should be reviewed before adopting a numerical baseline."
        )
        review += [
            f"## {i + 1} {row['title']}",
            "",
            f"{', '.join(row['authors'])}. {row['journal']}, {row['year']}. DOI: {row['doi']}. {row['url']}",
            "",
            summaries[i] if i < len(summaries) else topic,
            "",
        ]
    (ROOT / "docs/LITERATURE_REVIEW.md").write_text("\n".join(review), encoding="utf-8")
    (ROOT / "docs/index.md").write_text((ROOT / "README.md").read_text(encoding="utf-8"), encoding="utf-8")
    for name in ["ucf_crime", "uca", "xdviolence", "sirb"]:
        (ROOT / f"scripts/data/fetch_{name}.py").write_text(
            f'from argus.data.fetch import fetch_all\n\nif __name__ == "__main__":\n    import argparse\n\n    parser = argparse.ArgumentParser()\n    parser.add_argument("--resume", action="store_true")\n    args = parser.parse_args()\n    fetch_all("{name}", resume=args.resume)\n',
            encoding="utf-8",
        )
    return literature


def notebooks():
    folder = ROOT / "notebooks"
    folder.mkdir(exist_ok=True)

    def notebook(name, cells):
        data = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
            "cells": [
                {
                    "cell_type": kind,
                    "metadata": {},
                    "source": text.splitlines(True),
                    **({"outputs": [], "execution_count": None} if kind == "code" else {}),
                }
                for kind, text in cells
            ],
        }
        (folder / name).write_text(json.dumps(data, indent=2), encoding="utf-8")

    notebook(
        "01_kaggle_batch_vlm.ipynb",
        [
            (
                "markdown",
                "# ARGUS offline VLM batch\nUpload an approved copy of this repository and only the selected licensed research clips/evidence. Enable a free GPU only if available. This notebook does not promise free GPU capacity. No paid API is used. Confirm the model licence, especially when selecting the 3B fallback.\n",
            ),
            (
                "code",
                'from pathlib import Path\nimport os, subprocess, sys\nroot = Path(os.environ.get("ARGUS_ROOT", "/kaggle/working/argus"))\nassert (root / "pyproject.toml").exists(), "Place the project at ARGUS_ROOT first"\nos.chdir(root)\n',
            ),
            (
                "code",
                'subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".[research,cloud]"], check=True)\n',
            ),
            (
                "code",
                'import torch\nprint("CUDA available:", torch.cuda.is_available())\nif torch.cuda.is_available():\n    print(torch.cuda.get_device_name(0))\n',
            ),
            (
                "code",
                'manifest = root / "data/cache/vlm_manifest.json"\nassert manifest.exists(), "Prepare clip_id and evidence_path entries first"\nsubprocess.run([sys.executable, "scripts/batch_vlm.py", "--manifest", str(manifest), "--device", "auto"], check=True)\n',
            ),
            (
                "markdown",
                "Each successful clip writes validated JSON and a cache signature. Restart the same command to resume. Download data/cache/vlm before the notebook session expires. A failed clip raises with its error; inspect that input before resuming. For the research-licensed 3B variant, add --fallback-3b and use a separate output directory.\n",
            ),
        ],
    )
    notebook(
        "02_results_figures.ipynb",
        [
            (
                "markdown",
                "# ARGUS measured artifacts\nThis notebook regenerates sample metrics and loads existing research artifacts. Missing research runs remain PENDING.\n",
            ),
            ("code", "from argus.eval.suite import evaluate\nresults = evaluate()\nresults\n"),
            (
                "code",
                'from IPython.display import Image, display\nfrom argus.config import ROOT\ndisplay(Image(filename=str(ROOT / "artifacts/figures/sample_verification.png")))\n',
            ),
        ],
    )


def manuscript(literature):
    paper = ROOT / "docs/paper"
    paper.mkdir(exist_ok=True)

    def tex(s):
        return s.replace("&", r"\&").replace("_", r"\_").replace("%", r"\%").replace("#", r"\#")

    bibliography = []
    for i, row in enumerate(literature):
        bibliography.append(
            "@article{ref"
            + str(i + 1)
            + ",\n title={"
            + row["title"]
            + "},\n author={"
            + " and ".join(row["authors"])
            + "},\n journal={"
            + row["journal"]
            + "},\n year={"
            + str(row["year"])
            + "},\n doi={"
            + row["doi"]
            + "}\n}"
        )
    (paper / "references.bib").write_text("\n\n".join(bibliography), encoding="utf-8")
    metrics = json.loads((ROOT / "artifacts/metrics.json").read_text())["sample"]
    table = "\\begin{tabular}{lr}\n\\hline\nSynthetic software check & Measured value \\\\\n\\hline\n"
    for name, value in [
        ("Scenes", metrics["incidents"]),
        ("Authored claims", metrics["claims"]),
        ("Rejected claims", metrics["rejected_claims"]),
        ("Policy violations", metrics["constraint_violations"]),
        ("Invalid actions stripped", metrics["adversarial_stripped"]),
    ]:
        table += tex(name) + " & " + str(value) + " \\\\\n"
    table += "\\hline\n\\end{tabular}\n"
    (ROOT / "artifacts/tables/sample_results.tex").write_text(table, encoding="utf-8")
    body = r"""\documentclass[journal]{IEEEtran}
\usepackage{graphicx}
\usepackage{url}
\title{ARGUS: Evidence Consistency Verification and Interpretable Severity Tooling for Offline CCTV Review}
\author{Munis Aparji V S, Mithin Sagar S, and Janit B\\Guide: Dr. Premanand V\\School of Computer Science and Engineering, Vellore Institute of Technology}
\begin{document}
\maketitle
\begin{abstract}
ARGUS is an implemented offline research pipeline that combines temporal detection interfaces, symbolic evidence, structured language claims, conservative verification, interpretable severity factors, and a validated recommendation vocabulary. The delivered demonstration uses eight synthetic scenes and authored language fixtures. It exercises the full operator workflow without downloaded model weights. Research adapters provide a trainable temporal transformer and a constrained ordinal severity fitter. Benchmark detection performance, human severity calibration, independent annotation agreement, and real vision-language-model ablations remain pending. The paper distinguishes executed software checks from future empirical claims.
\end{abstract}
\section{Domain and Problem Statement}
An anomaly score alone does not explain an incident. A fluent description may add objects, interactions or intent that the evidence cannot establish. ARGUS records each handoff and exposes rejected and downgraded claims. It excludes biometric identification, cross-camera re-identification, live-stream inference and automated dispatch. The automatic terminal state is awaiting human confirmation.
\section{Literature Review}
Surveillance video-language understanding supplies the conceptual task family \cite{ref1}. Prompt-enhanced weak supervision supplies a reproducible detector comparator \cite{ref2}. Graded violence assessment already exists \cite{ref3}; tracking quality is also established prior work \cite{ref4}. Normalization and snippet attention inform design choices \cite{ref5,ref6}. The broader comparison set covers graph learning, temporal constraints, feature tuning, instance models, confidence-aware prototypes, multimodal text guidance, reconstruction and open-vocabulary detection \cite{ref7,ref8,ref9,ref10,ref11,ref12,ref13,ref14,ref15}. DOI metadata has been resolved through Crossref. ARGUS does not claim these established methods as novel, reproduce every comparator, or equate metadata review with a full experimental replication.
\section{Design of Proposed Methodology}
One versioned IncidentRecord carries source provenance and seven stage outputs. M1 resamples at 25 fps and aggregates 16-frame snippets. M2 is a four-layer temporal transformer trained with binary video-level Multiple Instance Learning, LayerNorm, attention pooling and an erasing regularizer. It does not infer thirteen semantic categories from binary labels. M3 independently extracts detections and clip-local geometric tracks. M4 consumes or generates strict structured claims. M5 sees claims and evidence but not the generation prompt. Object and count checks are time-local, and unsupported action or intent assertions become inference. A narrow sentence grammar limits what can be verified.
\section{Module Description and System Design}
M6 aggregates nonnegative contributions from thirteen factors. Only independently supported observations contribute. Context and event factors without an independent verifier remain unavailable. A constrained cumulative logistic objective and score-error term fit weights from independent training ratings. Fixed ordered cut points map scores to four bands. M7 selects from twelve permitted tokens and counts invalid proposals before stripping. The operator console includes video overlays, a visible claim ledger, source-factor links, structured traces, annotation and audit screens. SQLite transactions bind decisions to append-only chained audit records. Local session names are not authenticated identities.
\section{Executed Checks}
The following values come from the sample evaluation artifact. They are synthetic software checks, not UCF-Crime or XD-Violence results and not measured human agreement.
\begin{table}[h]\centering\caption{Executed synthetic checks}\input{../../artifacts/tables/sample_results.tex}\end{table}
\begin{figure}[h]\centering\includegraphics[width=\linewidth]{../../artifacts/figures/sample_verification.pdf}\caption{Claim rejection in authored synthetic fixtures.}\end{figure}
\section{Evaluation Plan and Limitations}
Frame-level UCF AUC requires independent test labels and correct temporal feature alignment. XD-Violence remains held out and uses AP. UCA supports temporal overlap evaluation. SIRB requires independent ratings, 20 percent overlap, pre-adjudication agreement and a source-grouped held-out split. VLM ablations compare 7B and 3B, evidence conditioning and critic use on identical clips. No target number is reported as a measured result. Detector errors can reject true claims or support false ones. The symbolic critic is not a complete semantic verifier. Unavailable factors can lower scores. Vocabulary membership does not establish response appropriateness. The package is local academic software, not a validated security product.
\bibliographystyle{IEEEtran}
\bibliography{references}
\end{document}
"""
    (paper / "main.tex").write_text(body, encoding="utf-8")
    (paper / "README.md").write_text(
        "# Manuscript source\n\nFrom this directory, run `latexmk -pdf main.tex` with a TeX installation containing IEEEtran. Figures and tables are loaded from artifacts. The source has not been compiled in this environment. Replace PENDING study statements only after running the real evaluations.\n",
        encoding="utf-8",
    )


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="GuideTitle",
        fontName="Helvetica-Bold",
        fontSize=28,
        leading=33,
        textColor=colors.black,
        spaceAfter=15,
    )
)
styles.add(
    ParagraphStyle(
        name="GuideH1",
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=23,
        textColor=colors.black,
        spaceBefore=16,
        spaceAfter=10,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        name="GuideH2",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.black,
        spaceBefore=13,
        spaceAfter=6,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        name="GuideBody",
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#283445"),
        spaceAfter=8,
    )
)
styles.add(
    ParagraphStyle(
        name="GuideSmall",
        fontName="Helvetica",
        fontSize=8.3,
        leading=12,
        textColor=colors.HexColor("#3d4a5b"),
        spaceAfter=5,
    )
)
styles.add(
    ParagraphStyle(
        name="GuideCode",
        fontName="Courier",
        fontSize=7.7,
        leading=11,
        textColor=colors.HexColor("#1b3b4e"),
        spaceAfter=5,
    )
)


def clean(text):
    text = (
        text.replace("≥", ">=")
        .replace("κ", "kappa")
        .replace("ρ", "rho")
        .replace("α", "alpha")
        .replace("→", " to ")
        .replace("–", "-")
        .replace("—", "-")
        .replace("·", " / ")
    )
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    text = html.escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    return text


def para(text, style="GuideBody"):
    return Paragraph(clean(text), styles[style])


def markdown_story(text):
    story = []
    code = False
    table = []

    def flush_table():
        if not table:
            return
        rows = [
            [para(cell.strip(), "GuideSmall") for cell in row.strip("|").split("|")]
            for row in table
            if not re.fullmatch(r"[\s|:-]+", row)
        ]
        cols = len(rows[0])
        widths = [(A4[0] - 104) / cols] * cols
        if cols == 3:
            widths = [83, 184, A4[0] - 104 - 267]
        tbl = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7edf3")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9d9d9")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.extend([tbl, Spacer(1, 10)])
        table.clear()

    for line in text.splitlines():
        if line.startswith("```"):
            flush_table()
            code = not code
            continue
        if line.startswith("|") and not code:
            table.append(line)
            continue
        flush_table()
        if not line.strip():
            continue
        if code:
            for start in range(0, len(line), 99):
                story.append(para(line[start : start + 99], "GuideCode"))
        elif line.startswith("# "):
            story.append(para(line[2:], "GuideH1"))
        elif line.startswith("## "):
            story.append(para(line[3:], "GuideH2"))
        elif line.startswith("### "):
            story.append(para(line[4:], "GuideH2"))
        else:
            story.append(para(line))
    flush_table()
    return story


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#667487"))
    canvas.drawString(52, 30, "ARGUS project guide / September 2026")
    canvas.drawRightString(A4[0] - 52, 30, str(doc.page))
    canvas.restoreState()


def guide():
    story = [
        para("ARGUS project guide", "GuideTitle"),
        para("Software architecture and research operation", "GuideH2"),
        para(
            "This guide explains the delivered ARGUS project, how to run its offline CCTV demonstration, how its evidence checks work, and how to carry out the remaining research study. The local software and synthetic demonstration are implemented. Real-dataset performance, human severity calibration, independent SIRB agreement and cloud VLM experiments remain pending."
        ),
        Spacer(1, 10),
        para("Munis Aparji V S, Mithin Sagar S and Janit B"),
        para("Guide Dr Premanand V"),
        para("BCSE497J / School of Computer Science and Engineering / Vellore Institute of Technology"),
        Spacer(1, 12),
        para("Start here", "GuideH2"),
        para(
            "On the prepared Windows machine, open PowerShell in the project folder and run start.ps1. Open http://127.0.0.1:8000. For a new machine, run setup.ps1 first. The PDF is a companion to the editable Markdown documentation and source code, not evidence that unrun research targets have been achieved."
        ),
        para("Delivery map", "GuideH2"),
        para(
            "src/argus contains the pipeline and API. apps/console contains the React application. data/sample contains original synthetic clips and authored fixtures. scripts contains training, evaluation, data and release tools. artifacts contains measured outputs. docs contains operational and academic sources. deliverables contains the review deck and printable materials."
        ),
        para("Research boundary", "GuideH2"),
        para(
            "The bundled sample uses no real people, no downloaded neural weights and no paid API. Detector and model errors remain possible in research mode. An operator must review every recommendation. Confirm records a decision and never dispatches a service."
        ),
    ]
    sections = [
        "SETUP",
        "ARCHITECTURE",
        "API_REFERENCE",
        "DATA_FORMATS",
        "RESEARCH_WORKFLOWS",
        "SIRB_ANNOTATION_PROTOCOL",
        "RESULTS",
        "TEST_REPORT",
        "ETHICS",
        "LICENCES",
        "DATA_LICENCES",
        "COMPLETION_STATUS",
        "LITERATURE_REVIEW",
        "VIVA_PREP",
    ]
    full = ["# ARGUS project guide", ""]
    for name in sections:
        text = (ROOT / f"docs/{name}.md").read_text(encoding="utf-8")
        full.append(text)
        if name == "ARCHITECTURE":
            text = re.sub(
                r"```mermaid.*?```",
                "The data flow is video, features, detection, evidence, language, critic, severity, policy, and human review.",
                text,
                flags=re.S,
            )
        story.append(PageBreak() if name == sections[0] else CondPageBreak(170))
        story.extend(markdown_story(text))
    (OUT / "ARGUS_Project_Guide.md").write_text("\n\n".join(full), encoding="utf-8")
    SimpleDocTemplate(
        str(OUT / "ARGUS_Project_Guide.pdf"),
        pagesize=A4,
        rightMargin=52,
        leftMargin=52,
        topMargin=46,
        bottomMargin=49,
        title="ARGUS project guide",
        author="ARGUS project team",
    ).build(story, onFirstPage=footer, onLaterPages=footer)


def poster():
    sample = json.loads((ROOT / "artifacts/metrics.json").read_text())["sample"]
    story = [
        para("ARGUS CCTV evidence verification", "GuideTitle"),
        para("Offline research pipeline with human review", "GuideH2"),
        para("Munis Aparji V S / Mithin Sagar S / Janit B / Guide Dr Premanand V"),
        para("Problem and approach", "GuideH1"),
        para(
            "A generated description can claim objects or intent that the video evidence does not support. ARGUS keeps the claim, its evidence references and the verification decision in an auditable ledger. It downgrades uncheckable semantics and computes severity only from supported observations."
        ),
        para("Seven module pipeline", "GuideH2"),
        para(
            "Feature cache → Temporal detector → Object and track evidence → Structured language → Independent critic → Thirteen severity factors → Validated policy → Human review"
        ),
        para("The visible rejection", "GuideH2"),
        para(
            "Authored claim: A person is holding a knife. The synthetic evidence contains people and a bag, with no supporting knife detection. The critic marks the claim REJECTED. This means missing support, not proof of absence."
        ),
        para("Executed sample checks", "GuideH2"),
        para(
            f"{sample['incidents']} synthetic scenes / {sample['claims']} authored claims / {sample['rejected_claims']} unsupported claims rejected / {sample['constraint_violations']} normal-run vocabulary violations / {sample['adversarial_stripped']} of {sample['adversarial_injected']} injected invalid actions stripped."
        ),
        para("Research status", "GuideH2"),
        para(
            "Real UCF AUC, XD AP, human severity agreement, independent annotation agreement and Qwen ablations are PENDING. Reference severity weights are uncalibrated. No target or illustration is presented as an experimental result."
        ),
        para("Boundaries", "GuideH2"),
        para(
            "Offline clips only. No face recognition or identity inference. No cross-camera re-identification. No dispatch or external messaging. The system recommends and a human acts."
        ),
        para("BCSE497J / SCOPE / Vellore Institute of Technology", "GuideSmall"),
    ]
    SimpleDocTemplate(
        str(OUT / "ARGUS_Poster.pdf"),
        pagesize=A4,
        rightMargin=46,
        leftMargin=46,
        topMargin=42,
        bottomMargin=36,
        title="ARGUS research poster",
    ).build(story)


if __name__ == "__main__":
    literature = write_supporting_docs()
    notebooks()
    manuscript(literature)
    guide()
    poster()
    print("Built project guide, poster, manuscript sources, codebook and notebooks")
