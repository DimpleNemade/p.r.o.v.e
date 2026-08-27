# AI governance boundary

## V0.1 position: no AI

P.R.O.V.E makes **no external AI calls** and contains no model integration. All core
workflows function and are reproducible without any model. This is a deliberate baseline
(equivalent to level "A0" in the programme's AI progression).

## Prohibited, now and later

- Changing original evidence or silently altering normalized records.
- Autonomous evidential conclusions, attribution, guilt/innocence assessment, or report
  sign-off.
- Presenting model output as observed fact, or hiding uncertainty and missing context.
- Sending case material to an external provider without an approved legal, security,
  privacy, residency, and contract decision.
- Letting instructions embedded in evidence control tools or reveal other cases.

## Conditions for any future assistance

If assistance is ever added, each material claim it makes must **cite a retrievable case
source**; its output must be a labelled, provenance-linked **suggestion** that an
examiner explicitly accepts or rejects; and the model, prompt, and retrieval
configuration must be versioned and recorded with the run. A machine suggestion can
never become an approved finding unchanged.

The data model already separates `suggestion` from `approved`
(`TimelineEvent.interpretation_status`, `Finding.examiner_status`) so this boundary is
enforceable when the time comes.

Related: [01 Product constitution](01-product-constitution.md) ·
[06 Provenance & chain of custody](06-provenance-and-chain-of-custody.md).
