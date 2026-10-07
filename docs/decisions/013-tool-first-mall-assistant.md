# 013 — The assistant calls tools; the model only phrases

**Status:** Accepted
**Date:** 2026-10-06
**Deciders:** Basel

## Context

"Where is Nike?" and "How do I get to Nike?" look like language problems. The first is a lookup. The second is A*, which already exists and is tested against Dijkstra. A model that "knows" malls will invent Gucci, a floor, and a distance.

## Options considered

### Option A — Stuff the catalog into the prompt
- Pros: one call.
- Cons: every new store changes the prompt, the model can still ignore it, and routes are not in the catalog.

### Option B — Let the model choose tools
- Pros: flexible.
- Cons: tool choice becomes a thing to evaluate, and a bad choice can skip the router.

### Option C — Code chooses the tool. The model may phrase a location fact. Routes stay on the template.
- Pros: intent is a small parser (search, nearest, route, "where did I start?"). `calculate_route` is `NavigationService`. Empty retrieval never calls the model. A phrased answer that names a mall store we did not retrieve is rejected and the template is kept. Provider down: template.
- Cons: the parser will miss phrasings a model would catch. We would rather miss a phrasing than invent a store.

## Decision

Option C.

Tools, all backed by existing services: `search_locations`, `get_location`, `calculate_route`. The prompt lives in `app/assistant/prompts/system_v1.txt`. The HTTP response carries `actions` (`highlight_location`, `show_route`, `change_floor`) so the map does not parse English.

## Why

A unit test feeds the model "The walk is 1 meter via a secret corridor." The answer still says 102 m, because that number comes from the route tool and the model is not called for routes. A unit test feeds "Nike is next to Gucci on Floor 9." The answer is rejected and the template says Ground Floor. "Where is Gucci?" in English, Arabic, and Hebrew returns no sources and does not call the model.

Live chat-model verification is pending. `LLM_API_KEY` is unset. Provider failure was tested by pointing the HTTP client at `127.0.0.1:9` (connection refused → `LlmError`) and by a raising fake. The assistant still answers from the database.

## Trade-offs

We will not answer a question the parser does not recognize, even if a model could. Opening hours are not in the database, so they are not answered. Hallucinations are reduced, not impossible: the grounding check is a name list plus English Capitalized words, not a proof.

## What would change this later

A phrasing the parser keeps missing in real use, after we have a transcript. Not before.
