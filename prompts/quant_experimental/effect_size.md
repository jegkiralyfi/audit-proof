You are auditing a quantitative experimental social-science paper for explicit effect-size reporting.

Your task is narrow: decide whether the excerpt reports an effect-size metric or a clearly equivalent magnitude-of-effect statistic.

Strong PASS signals (direct evidence):
- Cohen's d / Cohen d
- Hedges' g / Hedges g
- eta squared / partial eta squared / η² / partial η²
- omega squared / ω²
- odds ratio / OR
- relative risk / risk ratio
- standardized beta when clearly reported as a magnitude statistic
- wording such as "effect size" followed by a value or named metric

WARNING-level signals:
- the excerpt discusses magnitude, practical significance, or meaningful effect without an explicit statistic
- the excerpt implies that effect sizes exist elsewhere (for example "see supplementary table") but does not show one
- a statistic is reported that might be magnitude-related but is not clearly labeled enough to count as an effect-size report

FAIL signals:
- no explicit effect-size metric or equivalent magnitude statistic is present

Important exclusions:
- do NOT treat p-values alone as effect sizes
- do NOT treat confidence intervals alone as effect sizes
- do NOT treat mean differences, coefficients, or significance statements as effect-size reporting unless clearly presented as such

Return:
- PASS only if an explicit effect-size metric or equivalent magnitude statistic is reported
- WARNING if the excerpt suggests magnitude reporting but does not show a concrete effect-size statistic
- FAIL if there is no meaningful effect-size signal

Be conservative.
Quote exact evidence.
