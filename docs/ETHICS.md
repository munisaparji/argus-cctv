# Ethics and operating limits

ARGUS is an offline academic research tool. The bundled videos depict computer-generated shapes. They contain no real people, private footage or identity information. Real footage must have an appropriate research basis and licence, and must remain local unless separate permission permits transfer. Use the smallest clip set necessary for the study and record its provenance.

The system performs no face recognition, biometric identification or cross-camera re-identification. Track IDs are temporary geometric associations inside a clip. No face crops or face embeddings are saved. Optional privacy rendering blurs whole derived keyframes; the operator must inspect shared outputs because raw source footage remains unchanged.

Language can misdescribe an event. DETR can miss small objects or detect false positives. Tracking can fragment identities. Verification measures consistency with symbolic evidence, not truth. Missing support for a knife does not prove no knife was present. No unverified inference is used as an automatic severity factor.

Unknown context must not become an invented measurement. Time of day, vulnerability, motive, victim/aggressor roles, escalation and restricted-area status require explicit context or separately validated evidence. The default implementation leaves unavailable factors at zero and records their missingness. This can depress scores; low severity never means safe.

All automatic runs stop at AWAITING_HUMAN_CONFIRMATION. The action vocabulary contains recommendations only. Confirm/dismiss updates a local audit record. No code contacts police, medical responders, guards or external messaging services. Vocabulary validity alone does not establish action appropriateness. Human operators must use the event context and applicable institutional procedures.

The local console has no production identity provider or access control. Annotator names are session identifiers, not authenticated identities. Independent annotation depends on study procedure. A local database owner can alter files or disable triggers; the chained audit is not a tamper-proof external ledger. Do not deploy public write endpoints without a separate security design.

The SIRB protocol should minimize annotator exposure to distressing scenes, allow breaks and withdrawal, exclude gratuitous material, and document disagreements rather than force false certainty. Proposed benchmark releases contain annotations and source IDs only, never redistributed source footage. Confirm that derivative annotation publication itself is allowed by each source licence.

