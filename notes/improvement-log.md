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

## 2. Move lobby decisions from the Game State to the Lobby Game Mode

- **System:** Gameplay Framework
- **Found:** 2026-10-20
- **Status:** Planned

**Now:** `AChrisGameState` holds lobby rules (`StartMatch`, `AbortMatch`, the hero-selection timer, `AssignRandomCharactersToEmptySlots`), guarded with `HasAuthority()`. `ALobbyGameMode` only handles seamless travel and `PreLogin`.

**Problem:** The Game State exists on every client, so decision-making code has to protect itself from running there. It blurs "Game Mode decides, Game State shares".

**Also move (they contain decisions):** `RequestPlayerSelectionChange`, `SetCharacterSelected`, `SetCharacterDeselected`, `RequestPlayerLockIn`, `RequestPlayerReadyChange`.

**Plan:** Move the actions, validation and the timer to `ALobbyGameMode`. Keep the replicated selection data and read-only queries (`CanStartMatch`, `HasValidTeamsForMatch`, `IsSlotOccupied`) in the Game State, plus rule-free write helpers the Game Mode calls after validating. Client requests go Server RPC (Player State / Controller) -> `GetAuthGameMode<ALobbyGameMode>()` -> Game State.

**Benefit:** Clear ownership, no authority guards needed for lobby rules, and a thinner Game State.

## 3. Start spots are claimed twice per player

- **System:** Gameplay Framework
- **Found:** 2026-10-20
- **Status:** Planned (confirm with a UE_LOG in `FindNextStartSpotForTeam` first)

**Now:** `FindNextStartSpotForTeam` marks a Player Start as "Taken" each time it runs. It runs in `HandleSeamlessTravelPlayer` (or `SpawnPlayerController` for fresh joins) and again in `SpawnDefaultPawnFor`. The second call overwrites `PC->StartSpot`, so the first spot is wasted.

**Problem:** Each player uses two Player Starts. With bigger teams (e.g. 4v4), later players can get `nullptr` and spawn in the wrong place or fail to spawn. The team-ID + start-spot block is also copy-pasted in three functions.

**Plan:** Move "set team ID + claim start spot" into one helper. In `SpawnDefaultPawnFor`, reuse `NewPlayer->StartSpot` if it is already valid; only claim a new spot if not.

**Benefit:** One spot per player, no duplicated code, safe for larger teams.

## Noted for later

- **Countdown input lock is client-side only:** `Client_OnCountdownStart` calls `DisableInput` on the client. The server should also refuse actions during the countdown. (Networking page)
