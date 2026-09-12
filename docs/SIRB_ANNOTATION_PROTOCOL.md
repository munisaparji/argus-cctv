# SIRB annotation protocol

Use this codebook with the Annotation Studio. A short review should take about three minutes as a design aim; no annotator timing study has yet measured that target.

## Review procedure

1. Select your own annotator name. Do not inspect other ratings before completing the independent pass.
2. Watch the clip once at normal speed, then replay only the uncertain interval. Mark start/end seconds and a concise evidence label.
3. Enter the thirteen normalized factor values. Unknown means zero plus a note stating unknown, not a claim of absence. The current form does not model a separate human missingness flag, so retain the note when exporting.
4. Rate overall severity from 0 to 100. LOW is 0 to below 25, MEDIUM 25 to below 50, HIGH 50 to below 75, CRITICAL 75 to 100. Choose the lower band when context does not justify a higher band, and explain uncertainty.
5. Select only actions supported by the context. These are annotation labels, never a dispatch instruction. Save and complete the review.
6. For disagreements of at least one band, use a third independent annotator, then review side-by-side evidence and retain both original ratings. Do not erase disagreements.

## Decision tree

Is the event visible? If no, describe uncertainty and avoid speculative factors. If yes, identify the evidence span and count only simultaneous people. Is any factor based on identity, motive or an unsupported event? If yes, leave it unknown. Is there enough source context for response selection? If no, choose review-oriented labels. Complete the overall rating after factor entry, then inspect it for consistency.

## Factor definitions

### Weapon Present

Documented visible weapon presence. Scale: 0 absent or unknown, 1 independently supported.

Positive example: A clearly visible weapon independently supported by detections or human evidence.

Counterexample: An inference that a concealed object must be a knife.

### People Involved

Simultaneous involved people. Scale: min(count / 10, 1).

Positive example: Two people in the same relevant frame give 0.2.

Counterexample: Counting one person twice because a track ID changed.

### Physical Contact

Physical interaction. Scale: 0 no support, 1 clearly documented interaction.

Positive example: A visible push or strike with an evidence span.

Counterexample: Two boxes merely overlapping in image coordinates.

### Crowd Density

People count proxy. Scale: min(count / 20, 1).

Positive example: Ten visible people give 0.5.

Counterexample: Interpreting this as measured people per square metre.

### Incident Duration

Supported event duration. Scale: min(seconds / 60, 1).

Positive example: A 30-second supported interval gives 0.5.

Counterexample: Including unrelated time before the event.

### Time Of Day

Documented night context. Scale: 0 day or unknown, 1 documented night.

Positive example: A reliable timestamp or explicit source context establishes night.

Counterexample: Assuming every dark frame was recorded at night.

### Property Damage

Visible damage. Scale: 0 unsupported, 1 directly documented damage.

Positive example: A visible before/after change with a typed span.

Counterexample: An object detector reporting a window, with no damage evidence.

### Vulnerable Person

Explicit contextual vulnerability. Scale: 0 unknown, 1 explicit contextual support.

Positive example: A source-provided non-biometric context documented in the note.

Counterexample: Guessing age, disability, health or identity from appearance.

### Role Asymmetry

Documented role asymmetry. Scale: 0 unsupported, 1 independently documented.

Positive example: An independent evidence annotation describes unequal roles.

Counterexample: Assigning victim or aggressor from clothing or appearance.

### Escalation

Increasing event intensity. Scale: 0 no support, 1 clearly documented increase.

Positive example: Two supported spans show an increase in the event.

Counterexample: Treating camera motion as increasing aggression.

### Restricted Area

Configured restricted zone. Scale: 0 unknown, 1 configured and supported.

Positive example: A provided zone policy identifies the location as restricted.

Counterexample: Inferring trespass from a fence alone.

### Vehicle Involvement

Visible vehicle in the event. Scale: 0 unsupported, 1 supported vehicle presence.

Positive example: A detected car is referenced by a supported observation.

Counterexample: Assuming a distant static car caused the event.

### Detection Confidence

Supporting detection reliability. Scale: 0 to 1; software quality proxy, not intrinsic severity.

Positive example: Mean confidence of detections referenced by verified claims.

Counterexample: Using the VLM's self-confidence as detector reliability.

## Study controls

The sampling manifest assigns 20% overlap. Use separate annotator sessions. The local studio does not enforce authentication or blinded access, so study administrators must control access procedurally. Synthetic practice annotations cannot be exported as real SIRB labels. Report agreement before adjudication. Record skipped clips, factor missingness, source quality and reasons for exclusions. Do not infer that a small synthetic fit establishes validity.

No model suggestions are silently accepted. The current blank-form workflow has no model-prefill acceptance rate to report. If label assistance is added, record accepted unchanged versus edited suggestions explicitly and evaluate bias.
