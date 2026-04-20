# External Calibration Note — Skeleton

## Working title
External Calibration Note: Retrospective Citation Uptake

## 1. Purpose
This document is **not** part of certificate issuance, does **not** affect issuance, and is **not** a validity input.
Its purpose is only to test whether the certification signal is meaningfully aligned with later external scholarly uptake.

## 2. Separation principle
The Audit-Proof certificate is generated strictly from standards-bound audit checks.
External outcomes such as citation uptake are analyzed only afterward, as retrospective calibration variables.

## 3. Research question
If we take a set of papers from year **Y**, run the Audit-Proof certification protocol on them, and then measure their external citation uptake by **Y + 5**, does the certification signal show a meaningful association with later scholarly uptake?

## 4. Hypotheses
- **H1.** Papers with stronger certification outcomes show higher later citation uptake.
- **H2.** Papers with more warnings or failed checks show lower later citation uptake.
- **H3.** A composite certification score is positively associated with later external uptake.

## 5. Scope
- Certification type: `quant_experimental`
- Cohort year: **Y**
- Outcome horizon: **Y + 5**
- Sample size: **X papers**
- Inclusion criteria: papers within the declared certification type only

## 6. Certification variables
For each paper:
- issuance status
- warning count
- failed check count
- check-level results
- certification profile
- optional composite audit score

## 7. External outcome variables
Primary:
- article-level normalized citation percentile at **Y + 5**

Secondary:
- raw citation count at **Y + 5**

Optional context:
- publication venue metadata
- publication lag
- correction / retraction signals

## 8. Data sources
- internal certification outputs from Audit-Proof
- external article-level citation metadata from a public scholarly metadata source
- optional preprint / article relation metadata for matching

## 9. Analysis plan
- descriptive summary of certification outcomes
- descriptive summary of later citation uptake
- Spearman correlation between certification score and later citation uptake
- grouped comparison by issuance status
- optional simple regression with citation uptake as outcome

## 10. Interpretation rule
External citation uptake is **not** treated as a truth signal.
It is used only as a retrospective calibration variable for the PoC.

## 11. Limitations
- citation uptake is field- and time-dependent
- not all valuable work is highly cited
- external uptake may reflect attention, not correctness
- this analysis cannot validate truth, only external alignment

## 12. Outputs
- one short narrative memo
- one table of certification outcomes vs later uptake
- one figure
- one appendix with methodology and variable definitions

## 13. Required disclaimer
This note is a retrospective external calibration exercise.
It is not part of certificate issuance and must not be interpreted as a truth-validation layer.
