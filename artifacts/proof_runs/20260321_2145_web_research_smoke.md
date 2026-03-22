# OH_SHOP Automated web_research Smoke Test

- Captured at: 2026-03-21 16:40:22 CDT
- Repo root: /home/dev/OH_SHOP
- Command: python3 scripts/agent_house.py smoke-test-web-research
- Title: OH_SHOP web_research smoke 20260321_164022
- Start task id: bb4ca5f185c64981be546787b32a7f62
- Start task status: READY
- App conversation id: 7504a68cd57b45c3b336a8e88f75590f
- Sandbox id: oh-agent-server-5IsCAMBFogyZJW0wUo1m9F
- Agent server URL: http://host.docker.internal:34183
- Conversation URL: http://localhost:34183/api/conversations/7504a68cd57b45c3b336a8e88f75590f
- Final execution status: finished
- Outcome classification: model-behavior failure
- Detail: conversation finished after the tool observation but no final assistant reply was captured

## Prompt

```text
Use the web_research tool to find the current temperature in Burbank, IL. Cite the source you used and say explicitly that you used web_research.
```

## Assistant Reply

```text
(no assistant reply captured)
```

## Tool Observation

```text
[Tool 'sse_11412ea9_web_research' executed.]
{
  "answer": "Weather fallback results for: current temperature Burbank IL\nwttr.in reports current conditions for Burbank IL; temperature 70F / 21C; feels like 70F / 21C; Partly cloudy; humidity 36%; observed 2026-03-21 04:16 PM.\nSearch engines returned no usable search results, so a direct weather source fallback was used.\nSources:\n- https://wttr.in/Burbank%20IL?format=j1",
  "sources": [
    "https://wttr.in/Burbank%20IL?format=j1"
  ],
  "quotes": [
    "wttr.in reports current conditions for Burbank IL; temperature 70F / 21C; feels like 70F / 21C; Partly cloudy; humidity 36%; observed 2026-03-21 04:16 PM."
  ],
  "artifacts": [],
  "trace": {
    "searched": [],
    "visited": [
      "https://wttr.in/Burbank%20IL?format=j1"
    ],
    "downloads": [],
    "fallback": "wttr.in_weather"
  }
}
```
