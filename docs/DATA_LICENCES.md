# Dataset provenance and access

| Dataset | Purpose | Access and release position |
| --- | --- | --- |
| UCF Crime | WHEN | Official research benchmark. Follow the official access process and source terms. No raw footage is bundled or assumed redistributable. |
| UCA | WHAT TO SAY | Annotation downloads linked by the official Surveillance Video Understanding repository. Underlying footage retains its own rights. |
| XD Violence | GENERALISE | Official site links dataset and features. Held out for evaluation. Do not infer unrestricted redistribution from public download links. |
| SIRB | HOW SERIOUS AND DO WHAT | Proposed project annotation set. No human-labelled release or DOI currently exists in this delivery. |
| ARGUS sample | Software smoke test | Original generated shapes and scene videos, CC0-1.0. Authored claims and example records are explicitly synthetic. |

All URLs are centralized in configs/data_sources.yaml. Files without an independently trusted expected digest receive a recorded checksum only. Public access, research use and redistribution are different permissions.

The source brief reports that NWPU Campus restricts derivative dataset release and UBnormal uses CC BY-NC-ND. Neither dataset is downloaded or used. Re-check their current authoritative terms before citing these exclusions as a legal conclusion; this project does not rely on them. Annotation-only packaging does not by itself override a source restriction on derivatives.

Use original source IDs and timestamps when reconstructing SIRB. Do not include contacts, names, biometric identifiers or precise identity descriptions in public annotations. Preserve research split membership and release only the fields necessary for reproduction.

