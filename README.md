# Agent Skills

Small, opinionated [Agent Skills](https://agentskills.io/) extracted from real solo-builder workflows.

## Included skills

| Skill | Purpose | Status |
| --- | --- | --- |
| [`red-team-gate`](skills/red-team-gate/) | Run one bounded challenge immediately before implementation, then decide whether to build or revise. | Experimental |

## Why `red-team-gate`

Many review workflows keep generating concerns after the important decision is already clear. `red-team-gate` admits only credible blockers, consolidates them by root cause, scales review depth to the actual risk, separates accepted debt from blockers, and ends with a concrete implementation slice.

It is intentionally not a security penetration-testing skill or a multi-agent review pipeline.

## Install

Clone this repository, then copy the skill directory into your agent's skills folder:

```bash
git clone https://github.com/crustmyo/agent-skills.git

# Codex
cp -R agent-skills/skills/red-team-gate ~/.codex/skills/

# Claude Code
cp -R agent-skills/skills/red-team-gate ~/.claude/skills/
```

Then ask your agent to red-team a settled specification, architecture, implementation plan, or major design decision before implementation.

## Validation boundary

- The skill follows the `SKILL.md` directory format and has no scripts, dependencies, network access, or bundled private context.
- Routing regression cases cover intended triggers, explicit exclusions, and near-neighbor workflows in [`evals/trigger_cases.json`](skills/red-team-gate/evals/trigger_cases.json).
- Structural validation does not prove review accuracy. Treat this release as experimental until it has been forward-tested on several real specifications.

## License

[MIT](LICENSE)
