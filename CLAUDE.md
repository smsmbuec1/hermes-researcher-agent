# CLAUDE.md

Operating rules for Claude Code in this repo. Durable constraints only; status and work
plans live in work packages, not here.

## What this is

Hermes skills (Nous Research, MIT) for goal-seeded research. One skill today,
`research-lead-finder`: retrieves arXiv candidates for a goal, generates
combinatorial-join leads, grounds them against abstracts, appends them to a JSONL archive
against a strict schema. It is the floor of a larger truth-search system; the v1 upgrade
(falsification, pairwise tournament, behavior descriptor, meta-review) is unbuilt.
Deploy, profile, and cron: see README.

## Layout and the one hard rule

    skills/<name>/SKILL.md        runtime agent instructions ONLY
    skills/<name>/references/      contract + docs the agent reads at runtime
    skills/<name>/scripts/         deterministic helpers (pure stdlib preferred)

SKILL.md is runtime instructions and nothing else — no setup, install, or cron (those go
in README). Fixed section order: When to Use / Procedure / Pitfalls / Verification.
Frontmatter: name, description (<=60 chars), version, metadata.hermes.{category, tags,
config}. Bump `version:` on any change to a skill.

## Commands

    # validate a lead against the contract (no deps, no network)
    python3 skills/research-lead-finder/scripts/record_lead.py --lead <file|-> --validate-only
    # validate and append
    python3 skills/research-lead-finder/scripts/record_lead.py --lead <file> --archive <path>

record_lead.py reads references/lead-schema.json: the schema is the single source of
truth, the validator follows it. Re-run it against a good and a bad lead before committing
schema or validator changes. End-to-end runs need a live profile (`researcher chat -q
"..."`, see README).

## Conventions (owner's standing rules)

- Reuse before rebuild: existing solution first (bundled Hermes skills, libraries, repo
  code); if building custom, name the specific capability gap.
- No post-hoc justification: do not dress up reasoning found after a decision as the
  original rationale; label later evidence as such and say if it is load-bearing.
- Stress-test claims: does the example prove the mechanism; would the obvious follow-up
  break it. No uncritical synthesis.
- Outcome over process: define "done" and how to verify it first; a spec must let someone
  with zero context judge completion.
- Tight over long. Plain text, no emojis — anywhere.

## Hermes specifics — verify, do not assert

Hermes moves fast; model memory of it is stale and has been wrong here. Verify CLI flags,
frontmatter, paths, and tap behavior against hermes-agent.nousresearch.com, not memory.
Two settled facts: the lead archive is a JSONL file, not Hermes memory (memory is for
small durable facts); multi-file skills install via tap or git checkout, and `hermes
skills tap add` is github.com-only (#14290) — on internal git, place by hand.

## Invariants — deliberate limits, do not fake them

- Grounding is half-enforced: the schema requires a verbatim quote per source and rejects
  a lead without one; record_lead.py does not check the quote is actually in the abstract.
  Do not make it claim otherwise. Honest fix (v1): pass abstracts in, assert substring.
- Free-text honesty cannot be enforced structurally: the validator accepts a dishonest
  novelty_note; the SKILL.md pitfalls forbid it and it rests on the agent. Do not fake
  enforcement.
- This generates and grounds; it does not disconfirm. If you build the v1 falsifier,
  "argue both sides" is the failure mode — balanced prose, not disconfirmation.

## Do not

- Put setup in a SKILL.md, or store leads in Hermes memory.
- Commit data (*.jsonl) or secrets (config.yaml, .env, auth.json) — .gitignore covers it.
- Build coevolution speculatively; it is gated by an ablation that decides if it earns its
  cost.
- Pad output. Nothing valid? Say so.
