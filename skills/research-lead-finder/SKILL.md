---
name: research-lead-finder
description: Find grounded, non-redundant research leads for a goal
version: 0.1.0
metadata:
  hermes:
    category: research
    tags: [research, arxiv, leads, novelty-floor, grounding]
    config:
      - key: research_lead_finder.arxiv_categories
        description: "arXiv categories to search, space-separated"
        prompt: "arXiv categories (e.g. cs.NE cs.AI q-bio.PE nlin.AO)"
      - key: research_lead_finder.keywords
        description: "Keywords intersected with the categories"
        prompt: "Comma-separated keywords (leave blank for none)"
      - key: research_lead_finder.lookback_days
        description: "How many days back to pull candidate papers"
        prompt: "Lookback window in days (e.g. 7)"
      - key: research_lead_finder.archive_path
        description: "Path to the JSONL lead archive (env vars allowed)"
        prompt: "Archive path (e.g. $HERMES_HOME/data/research-leads.jsonl)"
---

# Research lead finder

## When to Use

Use this when asked to find research leads for the configured goal, or on the
scheduled daily run. A lead is a specific, checkable connection or tension between
retrieved papers that bears on the goal. It is not a summary, a topic, or a single
paper of interest.

## Procedure

1. Read `references/goal.md`. It defines the goal and the relevance floor (what passes,
   what fails). Hold it in mind for the whole run; it is the pass/fail gate, not a
   ranking target.

2. Retrieve candidates. Use the `arxiv` skill to fetch papers matching the configured
   categories and keywords within the configured lookback window. Do not write a new
   fetcher; the `arxiv` skill is the retrieval path.

3. Read the existing archive at the configured archive path (JSONL, one lead per line).
   Note the claims already emitted. You will not re-emit a lead whose claim matches one
   already there; record_lead.py enforces this by id, but knowing the prior leads also
   keeps you from generating near-duplicates.

4. Goal floor. Discard every candidate that fails the floor in `references/goal.md`.
   Relevance is the floor. Expect to discard most candidates here; that is correct.

5. Generate leads by combinatorial joins. Pair or triple the surviving candidates and,
   for each genuine connection, state a specific claim: what connects or tensions these
   papers, and why it bears on the goal. One lead per real join. Do not pad the run with
   weak joins to hit a count.

6. Grounding check. For each candidate lead, verify every connection against the actual
   abstract text of the cited papers. Attach the verbatim supporting quote and the arXiv
   id for each source. If support is only partial or you are inferring beyond the text,
   set `support_type` to `partial` or `inferred` and say so in the grounding note. Never
   assert support you cannot point to with a quote. For the strongest leads, note in the
   grounding note that full-text verification is warranted; do not fabricate it.

7. Record each surviving lead. Fill the contract in `references/lead-schema.json`
   completely, then run:

       python3 scripts/record_lead.py --lead <lead.json> --archive <configured archive path>

   It validates the lead against the contract and appends it (computing the id and
   timestamp for you, skipping duplicates). If it exits non-zero, the lead is incomplete:
   fix it or drop it. Do not emit a lead that fails the validator.

8. Emit the run's new leads. For each: the claim, the join rationale, the grounded
   sources with their quotes, and the honest novelty and grounding notes. If nothing
   cleared the floor and grounding, say so plainly. A run with zero leads is valid.

## Pitfalls

- Relevance is a floor, not a ranking. Passing the floor does not make a lead good. A
  grounded, surprising, checkable join does.
- Grounding must be point-to-able. "The abstract supports this" without a verbatim quote
  is not grounding. A plausible-sounding connection with no textual support is the main
  failure mode, and the contract will reject it for missing the quote.
- A novelty claim can only honestly say "not found in current archive / searched set."
  Never write "unexplored" or "novel to the field" — the search set is small and the
  validator cannot catch this dishonesty, so it is on you.
- Do not emit a lead to fill the run. Zero good leads is a valid outcome.
- A join that only says two papers share an area is not a lead. State a specific
  connection or tension that could be checked.

## Verification

- Every emitted lead passed record_lead.py (exit 0).
- Every source resolves to a paper retrieved this run and carries a verbatim quote.
- No emitted lead duplicates an id already in the archive.
- The run produced either grounded leads or an explicit "nothing cleared the floor"
  result, with no padded or ungrounded leads.
