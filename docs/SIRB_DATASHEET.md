# SIRB datasheet

## Motivation and current status

SIRB is a proposed annotation benchmark for severity, typed evidence spans and bounded response labels. Target size is 250 clips, with 150 as the brief's reduced scope. This delivery supplies software and a codebook. It does not supply a completed human study or a public DOI.

## Composition and collection

Sample across incident categories, expected severity and normal scenes from approved source datasets. Retain source-video identifiers and clip timestamps. Prevent overlapping windows or duplicate source videos from crossing train, validation and test. Dataset owners retain footage rights. The release exports annotations without footage.

## Annotation process

Two independent annotators double-label 20% of the sample. They enter normalized factors, overall score, recommended actions, typed evidence spans and notes. The studio starts with blank factors to avoid silently converting model predictions into ground truth. A third session adjudicates large disagreements after independent labels are complete.

## Intended use and limits

Evaluate research agreement and explainable factor contributions. Do not use these annotations as an operational risk standard or as labels about a person's character, intent or identity. Severity can depend on omitted context, camera position and annotation norms. Report missingness, agreement and sampling bias.

## Distribution and maintenance

Proposed licence is CC BY 4.0 for independently authored annotations, subject to source terms. No DOI is claimed until a repository assigns one. Maintain versioned manifests, change history and a takedown channel managed by the project team. Retention, ethics review and public release decisions remain with the institution and dataset owners.

