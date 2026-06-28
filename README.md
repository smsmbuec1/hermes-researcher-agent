# hermes-research-skills

Hermes skills for goal-seeded research. One skill so far: `research-lead-finder`, which
finds grounded, non-redundant research leads for a configured goal and writes them to a
JSONL archive. This is a tap-compatible repo, so it works both as a Hermes tap and as a
plain git checkout you place by hand.

This README is the operator doc. The SKILL.md inside each skill holds runtime agent
instructions only.

## Layout

    hermes-research-skills/
      skills/
        research-lead-finder/
          SKILL.md                 runtime instructions
          references/
            goal.md                the goal + relevance floor — EDIT THIS FIRST
            lead-schema.json       the auditable output contract
          scripts/
            record_lead.py         validate-and-append spine (pure stdlib)
      README.md
      LICENSE
      .gitignore

## Two separate things, do not conflate them

GitHub gives you two distinct things here, and they are independent:

1. Version control / source of truth. Non-negotiable for something you will iterate on.
   Develop in this repo, commit, push. This has nothing to do with Hermes.
2. How the skill reaches the running profile. Two options below.

### Deploy A — git checkout, placed by hand (recommended for now)

Lowest risk for a solo operator on one VPS: the destination profile is explicit, there is
no trust prompt, and it works with any git host — including an internal Liebherr GitLab,
which the tap path does not (see caveat below).

    git clone <you>/hermes-research-skills.git
    cp -r hermes-research-skills/skills/research-lead-finder \
      /root/.hermes/profiles/researcher/skills/research/research-lead-finder

Update later with `git pull` and re-copy. To skip the copy step you can symlink the skill
folder into the profile, or point an external skill directory at the checkout's `skills/`
path (Hermes documents external skill directories) — but I have not verified that skill
discovery follows symlinks or the exact external-directory syntax, so test with
`researcher skills list` and fall back to copy if the skill does not appear.

### Deploy B — Hermes tap (when you want managed updates or sharing)

The right mechanism once you want `hermes skills update` to pull new versions, install the
same skill across machines or profiles, or share it. It handles multi-file skills natively
(the `references/` + `scripts/` layout is fine).

    # add the repo as a skill source, then install just this skill
    hermes skills tap add <you>/hermes-research-skills
    hermes skills install <you>/hermes-research-skills/skills/research-lead-finder

    # or install the one skill directly without subscribing to the tap
    hermes skills install <you>/hermes-research-skills/skills/research-lead-finder

    # updates
    hermes skills check
    hermes skills update

First install from your own tap shows a third-party security-scan warning (new taps get
community trust by default); accept it once. A private repo needs GITHUB_TOKEN set. Bump
the `version:` field in SKILL.md on each change so `skills update` detects it.

One uncertainty that is itself a reason to prefer Deploy A right now: I have not confirmed
whether a tap install lands in the active profile's skills directory or the global
`~/.hermes/skills/`. With Deploy A the destination is whatever path you copy to, so there
is no ambiguity.

### Caveat — taps are github.com-only

`hermes skills tap add` resolves repos only through the GitHub Contents API, i.e.
github.com `owner/repo`. A self-hosted or SSH git remote (e.g. an internal GitLab) is
accepted by `tap add` but then `search`, `inspect`, and `install` resolve nothing from it
(NousResearch/hermes-agent issue #14290, open as of April 2026). If this skill ever moves
to internal git, use Deploy A; the tap path will silently fail.

## Profile

This runs as its own profile (call it `researcher`), separate from the `alife` digest. The
isolation is the point: distinct memory and learning loop, distinct delivery, distinct
default toolset, no leakage either way. Create it fresh — do not clone the digest's memory
(`--clone-all`); the researcher starts empty. Commands below shown as `researcher ...` mean
the profile-scoped invocation, the same way you invoke `alife`.

Three things genuinely differ for a fresh profile:

- The bundled `arxiv` skill must be reachable inside it: `researcher skills list | grep
  arxiv`. Whether bundled skills propagate to a new profile or must be made available in
  it is the thing to check — the digest profile has it, a new one may not. No arxiv, no
  retrieval.
- The default toolset must include terminal/code execution (the skill runs
  record_lead.py, and cron inherits the profile's default toolset with no per-job
  override). A fresh profile will not carry whatever you tuned on `alife`; set it
  explicitly on `researcher`.
- Telegram delivery routes to the researcher profile's own gateway and bot, which a fresh
  profile does not have until you onboard one (the hosted manager-bot flow, on mobile).

## Config

Set in the researcher profile's own config.yaml (Hermes prompts on first load; values
stored under skills.config):

- research_lead_finder.arxiv_categories — e.g. `cs.NE cs.AI q-bio.PE nlin.AO`
- research_lead_finder.keywords — comma-separated, or blank
- research_lead_finder.lookback_days — e.g. `7`
- research_lead_finder.archive_path — e.g. `$HERMES_HOME/data/research-leads.jsonl`
  (record_lead.py expands env vars and ~)

View with `researcher config show | grep '^skills\.config'`.

Editing the goal is separate and primary: open `references/goal.md` and replace the
example with your real goal and floor before the first run.

## First run and verification

    researcher chat -q "Run the research-lead-finder skill for today's goal."

Then verify (each checkable with no prior context):

1. The archive file exists at the configured path, one JSON object per line.
2. A line validates: `python3 .../scripts/record_lead.py --lead <(echo '<line>')
   --validate-only` prints PASS.
3. Each lead's sources carry a verbatim supporting_quote and an arXiv id from this run.
4. Re-running does not duplicate leads (record_lead.py skips by id).
5. A run that finds nothing says so rather than padding.

## Scheduling

    researcher cron create "0 8 * * 1-5" --name research-leads \
      --skill research-lead-finder --deliver telegram

`--deliver telegram` routes to the researcher profile's own gateway/bot (onboard it
first). Cron inherits the profile's default toolset, so the code-execution precondition
must already be set.

## Data and secrets

The skill folder carries no secrets — it declares config keys, whose values live in the
profile's config.yaml, not here. The lead archive lives under `$HERMES_HOME/data/`,
outside this repo, so it is never committed. `.gitignore` also blocks `*.jsonl`,
`config.yaml`, `.env`, and `auth.json` as belt-and-suspenders. The repo is safe to make
public; if you make it private, the tap path needs GITHUB_TOKEN.

## Deliberately out of scope (v1, not built here)

- Falsification engine, pairwise tournament, behavior descriptor, meta-review loop.
- The QD novelty ranker. MVP novelty is only "not found in the searched set."
- Whether the falsification axis should become coevolutionary — gated by the separate
  coevolution ablation, which decides it empirically before any build.

## Honest flags

- Grounding is load-bearing and only half-enforced. The contract forces a verbatim quote
  per source and rejects a lead without one, but record_lead.py does not check the quote
  actually appears in the abstract. That semantic check is the v1 grounding module; first
  hardening is to pass abstracts into record_lead.py and assert each quote is a substring.
- Free-text honesty (the novelty_note especially) cannot be enforced structurally. The
  validator accepts "novel to the field"; the SKILL.md pitfalls forbid it, but it rests on
  the agent.
- This is a lead-finder, not yet a truth-search system. It generates and grounds; it does
  not disconfirm. Disconfirmation is the v1 upgrade and the hard field-wide gap.
