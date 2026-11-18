# Agent Skills

Small, opinionated [Agent Skills](https://agentskills.io/) extracted from real solo-builder workflows.

## Included skills

| Skill | Purpose | Status |
| --- | --- | --- |
| [`red-team-gate`](skills/red-team-gate/) | Run one bounded challenge immediately before implementation, then decide whether to build or revise. | Experimental |
| [`page-task-check`](skills/page-task-check/) | Check whether a user can complete a page task and whether the result survives reload. | Experimental |
| [`optical-align`](skills/optical-align/) | Diagnose off-center icons and uneven visual weight with foreground measurements and before-and-after comparisons. | Experimental |

## Why `red-team-gate`

Many review workflows keep generating concerns after the important decision is already clear. `red-team-gate` admits only credible blockers, consolidates them by root cause, scales review depth to the actual risk, separates accepted debt from blockers, and ends with a concrete implementation slice.

It is intentionally not a security penetration-testing skill or a multi-agent review pipeline.

## Why `page-task-check`

An order can move to a new column and show **Saved** even when the save request fails. `page-task-check` follows one user task from the starting state through the action and reload, then reports the evidence for each result. Use it for page changes involving field comparisons, status transitions, or finding the same item again after navigation. The skill instructions are in Chinese. [Worked example](skills/page-task-check/examples/order-status.md)

## Install

Clone this repository, set `skill` to the directory you want, and use the block for your agent.

```bash
git clone https://github.com/suicuLsi/agent-skills.git
cd agent-skills
skill=page-task-check
```

**Codex**

```bash
mkdir -p ~/.codex/skills
cp -R "skills/$skill" ~/.codex/skills/
```

**Claude Code**

```bash
mkdir -p ~/.claude/skills
cp -R "skills/$skill" ~/.claude/skills/
```

Start a new session and ask your agent to use `page-task-check` to verify a page task. Include the expected result and any evidence you already have. For `red-team-gate`, ask it to challenge a settled specification or implementation plan before you start building.

For `optical-align`, ask your agent to check a mark that looks off-center in a control. The analyzer also runs directly from the command line with Python and Pillow. [Setup and before-and-after example](skills/optical-align/README.md)

## Validation boundary

- `red-team-gate` and `page-task-check` ship without runtime dependencies. Live page checks depend on the tools and environment provided by the host.
- `red-team-gate` includes [routing regression cases](skills/red-team-gate/evals/trigger_cases.json). `page-task-check` includes a [fictional walkthrough](skills/page-task-check/examples/order-status.md) that you can give to your agent alongside the skill.
- `optical-align` includes an offline analyzer, a repeatable sample, and unit tests. Its measurements describe the visible foreground. Check the actual control to decide whether a change improves alignment.

## License

[MIT](LICENSE)
