# Viva preparation

1. What is the contribution? Evidence consistency checks, interpretable severity calibration tooling and a validated action vocabulary in one auditable record. The human study and performance claims remain pending.
2. Is this a trained model demonstration? The default sample uses a motion baseline and authored claims. The repository also contains a trainable transformer and ordinal fitter. Show their tests and training code; never label sample fixtures as learned results.
3. Show a hallucination being caught. Open the counter scene, expand the rejected knife claim and show its reason. Compare raw output with the ledger.
4. Does no detection prove no knife? No. It means the claim lacks support from the selected detector. A detector miss can reject a true claim.
5. Why is the critic independent? It receives structured claims and separately generated evidence, not the VLM prompt. It cannot invent new claims.
6. How do you prevent an entity-list trick? Scan sentence text as well as metadata. Only narrow, checkable presence/count wording can be verified. Other semantics are downgraded.
7. What happens to intent? It is inference. It contributes no automatic severity points.
8. How are counts computed? By simultaneous detections in the claim interval. Track fragmentation is not counted as new people over the whole video.
9. Why LayerNorm? It avoids batch statistics varying with normal/anomalous composition of MIL bags.
10. What does weak supervision mean? Training sees video-level binary labels, not frame labels. Frame ground truth is reserved for evaluation.
11. Is each snippet a second? No. Sixteen frames at 25 fps is 0.64 seconds. Pre-released features must declare their own temporal spacing.
12. How are pretrained and trained components separated? CLIP, DETR and Qwen remain frozen. The temporal model and severity weights are fitted. The default demo uses no downloaded weights.
13. Why are several severity factors unavailable? The current independent evidence does not justify them. Missingness is explicit and low scores can be misleading.
14. Can a rejected knife raise severity? No. A test verifies that adding the rejected claim changes neither weights nor factor values nor the score.
15. How is the score calibrated? A constrained cumulative logistic objective with fixed ordered thresholds and a score-error term fits nonnegative weights on training human ratings. Evaluate on held-out source videos.
16. What are the severity metrics? Banded Cohen kappa, raw-score Spearman correlation and MAE. Undefined metrics are null. For independent annotators, interval Krippendorff alpha is also computed.
17. Why no 72 HIGH golden result? That number in the brief was illustrative. It cannot become a measured acceptance target without human-fitted weights and real evidence.
18. What does the policy validator guarantee? Membership in twelve permitted tokens. It does not guarantee the semantic appropriateness of any token.
19. Does confirm call the police? No. It stores the recommendation and operator review in SQLite. There is no dispatch implementation.
20. Is the audit immutable? Application writes are append-only and chained. A database administrator can still replace files or drop triggers.
21. How does 7B run locally? It does not run in the default laptop demo. An optional offline free-GPU job produces JSON once. CPU consumers reuse it.
22. Is the smaller Qwen model Apache licensed? The 3B checkpoint has a separate Qwen Research licence. Check the exact model licence.
23. How do you measure cross-dataset performance? Train on UCF, hold out XD and report XD AP using aligned frame labels. Do not train on the held-out dataset.
24. What is the greatest unfinished dependency? Independent SIRB annotations and real-source experiment runs, followed by robust event-level verification.
25. What would a deployment require? Authentication, institution-approved data governance, operational validation, protected storage and a separate human response procedure. This delivery is local academic software.

