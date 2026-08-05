---
name: red-team-gate
description: Run one bounded red-team pass on a product or technical specification immediately before implementation. Use when the user has a proposed or settled spec, architecture, implementation plan, or major design decision and asks to red-team it, challenge it, find fatal flaws, decide whether it is ready to build, or avoid analysis paralysis. Separate credible blockers from accepted debt and end with a clear start-or-revise gate.
---

# Red Team Gate

Turn pre-build doubt into a decision. Protect the core outcome without reopening every settled choice.

## Boundaries

- Run one pass. Do not red-team the red-team.
- Review only; do not edit the spec or code unless the user separately asks.
- Do not expand scope, optimize for hypothetical scale, or reject a choice merely because alternatives exist.
- Treat the user's settled requirements and constraints as the contract. Mark contradictions; do not silently replace them.
- Use qualitative likelihood backed by evidence. Do not invent precise probabilities.
- If a prior gate record exists and its inputs have not materially changed, keep its verdict and stop.

## 1. Establish the Decision Contract

Extract, without turning this into a new discovery exercise:

- the decision being gated;
- the core outcome and acceptance criteria;
- hard constraints and already-settled choices;
- relevant evidence, assumptions, and unknowns;
- irreversible or expensive commitments.

If the specification maps to an existing product or repository, inspect the relevant implementation and dependencies before judging fit. Keep verified facts, inferences, and unknowns distinct.

Classify the decision:

- **Two-way door:** cheap to change after learning. Scan only for core-requirement failure, data loss, security, legal/compliance, or an implementation dead end.
- **One-way door:** expensive or unsafe to reverse. Also inspect migration, external dependency, authority, lock-in, and recovery assumptions at the irreversible boundary.

## 2. Admit Only Credible Blockers

A concern is a blocker only when all are true:

1. It has a concrete trigger in the intended usage, not just an imaginable edge case.
2. It can cause data loss, a security or compliance failure, inability to meet a core acceptance criterion, an unrecoverable commitment, or a genuine implementation dead end.
3. A causal chain or evidence supports it.
4. Fixing or deciding it now is materially cheaper or safer than learning during the first implementation slice.

If any condition fails, classify it as a known issue only when it deserves an explicit revisit trigger; otherwise omit it. Never manufacture blockers to fill a quota.

Report at most three blockers. For each, state:

- failure and trigger;
- supporting fact, inference, or unresolved unknown;
- impact and qualitative likelihood;
- smallest change that removes the blocker;
- one check that proves it is resolved.

## 3. Stop and Decide

Return exactly one verdict:

- **Build now:** no credible blocker remains. Imperfection and known issues do not prevent the first vertical slice.
- **Revise, then build:** one or more credible blockers remain. Require only the minimal changes and checks listed; do not reopen the whole specification.

Then record at most three known issues. Each must include a concrete revisit trigger such as measured usage, a failed check, a new requirement, or an approaching irreversible commitment. Do not turn speculative concerns into a backlog.

End with the smallest implementation slice and its verification. After the verdict, stop analysis and move to implementation if the user has authorized it.

Write the report in the user's language. Translate headings and verdict labels without changing the two verdict meanings.

## Output

```markdown
## Red Team Gate: Build now | Revise, then build

**Decision:** ...
**Door type:** Two-way | One-way
**Basis:** Verified facts / key inferences / unresolved unknowns

### Blockers (0–3)
- **Problem:** ...
  - Trigger and consequence: ...
  - Basis and likelihood: ...
  - Minimum fix: ...
  - Resolution check: ...

### Accepted known issues (0–3)
- ...; reopen only when ...

### Start now
- Smallest implementation slice: ...
- Verification: ...

**Reopen when:** constraints or core requirements change, a resolution check fails, or new evidence directly related to the risks above appears. Otherwise, do not red-team again.
```

Omit empty subsections except `Blockers`, which must explicitly say `None` when the verdict is `Build now`.
