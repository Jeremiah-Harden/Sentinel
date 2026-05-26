# Agentive Workflows — Project Context

This project uses the **WAT framework** (Workflows, Agents, Tools).

## Architecture

| Layer | Location | Purpose |
|-------|----------|---------|
| Workflows | `workflows/` | Markdown SOPs — objective, inputs, tools, outputs, edge cases |
| Agent | Claude | Reads workflows, sequences tool calls, handles failures, asks when unclear |
| Tools | `tools/` | Python scripts for deterministic execution (API calls, transforms, file ops) |

## How I Operate

1. **Check tools/ first** before building anything new.
2. **Follow the workflow** — read the relevant `.md`, resolve inputs, execute tools in order.
3. **Don't touch workflows without asking** unless explicitly told to. They are living instructions.
4. **Learn from failures** — fix the tool, verify it works, then update the workflow.
5. **Deliverables go to cloud** (Google Sheets, Slides, etc). `.tmp/` is disposable scratch space.

## Self-Improvement Loop

Failure → fix tool → verify → update workflow → move on.

## File Structure

```
.tmp/           # Temporary / intermediate files. Regenerated as needed. Gitignored.
tools/          # Python scripts (deterministic execution)
workflows/      # Markdown SOPs
.env            # API keys — never stored anywhere else
credentials.json, token.json  # Google OAuth (gitignored)
```

## Key Principle

Probabilistic AI (Claude) handles reasoning and orchestration. Deterministic scripts handle execution. Keep them separate.
