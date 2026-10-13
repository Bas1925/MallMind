# Try MallMind in 90 seconds

This is a working simulation, not a live mall. All places, paths, floor changes and distances belong to synthetic NOVA Mall. You can evaluate the idea entirely in a browser; no physical mall, GPS sensor or account is needed.

Start the stack using [Quick start](../README.md#quick-start), then open http://localhost:3000. The default configuration does not need an API key or an embedding-model download.

| Time | Try this | What it demonstrates |
| --- | --- | --- |
| 0–15 s | Search for Nike in Stores & dining and open its details. | Search, real brand asset, accessible dialog, synthetic store metadata. |
| 15–30 s | Choose Take me here. | A real API-calculated path from Main Entrance, distance and instructions. |
| 30–50 s | Change the destination to Apple, select Wheelchair, then switch to Level 1. | Accessibility-aware routing via elevators and floor-local map segments. |
| 50–75 s | In Plan, start at Main Entrance and add Nike, Zara, Apple, ATM — Ground and Super-Pharm. Optimize the trip. | Exact ordering for this small trip and a concrete distance comparison. |
| 75–90 s | Open Ask and enter `خذني إلى Nike`. | Database-grounded Arabic route response, without pretending it is live GPS or a verified hosted model. |

For the documented 13.6% benchmark, use the Walking profile and add the five stops in the order above. Results and timing can change with other inputs; do not present this example as a universal improvement.

## Optional engineering demonstration

Open the search maze in Route. Compare Fewest steps (BFS) with First hallway (DFS), then use Play the search. Explain that BFS minimizes edge count in this unweighted comparison, DFS does not promise a shortest path, and A* minimizes the selected nonnegative route cost with its heuristic assumptions.

## Record the actual app

The recording script drives a fresh browser session against your running API; it does not mock routes or change database records. It produces a silent walkthrough. User speed and network latency affect the duration.

From `frontend/` on Windows with Edge installed:

```powershell
npx playwright install ffmpeg
$env:PW_CHANNEL = 'msedge'
npm run demo:record
```

Alternatively install Playwright Chromium and omit `PW_CHANNEL`. Output is `.validation/mallmind-demo.webm` at the repository root. It stays out of Git, together with temporary recording files. Review it before uploading to the repository's README or a video host, then add the actual video URL; no placeholder link is presented as a published recording.

The walkthrough works as a portfolio demonstration even without public hosting. A hosted demo is convenient, not proof that the fictional mall is real.
