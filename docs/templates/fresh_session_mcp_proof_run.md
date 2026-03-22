# OH_SHOP Fresh-Session MCP Proof Run

Use this template only after:

- LM Studio is running on the host
- the canonical Docker stack is up
- repo-controlled verification has been run
- external MCP registration has been entered manually in OpenHands
- a brand-new OpenHands session has been opened

Do not mark this template complete just because `/health`, `/ready`, or `scripts/verify.sh` were green.

## Run Metadata

- Date:
- Time:
- Time zone:
- Operator:
- Repo path: `/home/dev/OH_SHOP`
- Working snapshot identifier:
  - Optional. Use a local note, backup folder name, or other manual identifier.
- LM Studio model used:
- LM Studio reachable on host before test? `yes` / `no`
- Docker stack up before test? `yes` / `no`
- Repo-controlled verify command run:
  - `./scripts/verify.sh`
- Repo-controlled verify result:
  - `pass` / `fail`
- Optional proof-context capture file:
  - Example: `python3 scripts/agent_house.py capture-proof-context --output artifacts/proof_runs/<name>.md`
- Optional automated fresh-session smoke test:
  - Example: `python3 scripts/agent_house.py smoke-test-web-research --output artifacts/proof_runs/<name>.md`
  - Allow several minutes. A healthy run can produce the tool observation before the final assistant reply.

## Manual MCP Registration Entered

- OpenHands MCP Server Type:
  - `SSE`
- OpenHands MCP URL entered:
  - `http://host.docker.internal:3010/sse`
- Any deviation from the expected values:

## Fresh Session Used

- Confirmed this was a brand-new OpenHands session? `yes` / `no`
- Session identifier or UI label:

## Proof Prompt Used

- Exact prompt/task entered:

Recommended diagnostic prompt:

```text
Use the web_research tool to find the current temperature in Burbank, IL. Cite the source you used and say explicitly that you used web_research.
```

This prompt does not guarantee success. It only gives the run a standard diagnostic shape.

## Observed Tool Availability

- Did `web_research` appear available to the agent? `yes` / `no` / `unclear`
- What made that clear:

## Outcome Classification

Choose one:

- `success`
- `integration failure`
- `provider/dependency failure`
- `model-behavior failure`

## Outcome Details

- Exact observed result:
- If failure, brief reason:
- If failure, which boundary failed first:
  - registration
  - integration
  - provider/dependency
  - model behavior
  - unclear

## Artifact / Log Locations

- Saved proof-context capture:
- Saved automated smoke test artifact:
- Relevant terminal output:
- Relevant screenshots:
- Relevant LM Studio logs:
- Relevant Docker logs:

## Brief Notes

- Anything unusual about the run:
- Follow-up action suggested:
