# Improvement log

Changes found while studying the Champions Arena code. Each one becomes a refactor branch off `develop` and a "What I'd do differently" / "Optimisations" entry on the site.

## 1. Move match phase and timers into the Game State

- **System:** Gameplay Framework (also Networking)
- **Found:** 2026-10-20
- **Status:** Planned

**Now:** `CurrentPhase` lives in `AChrisGameMode` (server only). Each phase change and every countdown second is pushed to clients with `Client_` RPCs on `AChrisPlayerController`.

**Problem:** RPCs are one-off messages. A player who reconnects mid-round never receives the current phase or time. One RPC per second per player is also more network traffic than needed.

**Plan:** Replicate `CurrentPhase` and `PhaseEndServerTime` in `AChrisGameState`. Clients compute the remaining time locally using `GetServerWorldTimeSeconds()`, and react to phase changes in `OnRep_MatchPhase`.

**Benefit:** One update per phase instead of per second; late joiners and reconnects see the correct state; smooth timers.

## Noted for later

- **Countdown input lock is client-side only:** `Client_OnCountdownStart` calls `DisableInput` on the client. The server should also refuse actions during the countdown. (Networking page)
