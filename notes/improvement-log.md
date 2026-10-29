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

## 4. Guard against spawning the menu widget twice

- **System:** Gameplay Framework
- **Found:** 2026-10-27
- **Status:** Planned (one line)

**Now:** `AMenuPlayerController::SpawnWidget` runs from `OnRep_PlayerState`, which fires every time the Player State reference changes, not just the first time.

**Problem:** If it fires again (e.g. a reconnect), a second menu widget is created on top of the first.

**Plan:** Return early at the top of `SpawnWidget` if `IsValid(MenuWidget)`.

**Benefit:** Duplicate menus become impossible, whatever order replication arrives in.

## 5. Report "loaded" only when background loading has finished

- **System:** Gameplay Framework (match loop)
- **Found:** 2026-10-28
- **Status:** Planned

**Now:** Each client sends `Server_ReportLoaded` one frame after `AChrisPlayerController::BeginPlay`. That proves the map has loaded and the controller has started, not that textures, hero meshes, grooms and shaders have finished streaming. The 15-second minimum hold covers the gap.

**Plan:** Send the report once async loading has finished (e.g. wait until `IsAsyncLoading()` is false), combined with the planned async preload of hero soft assets.

**Benefit:** "Loaded" means loaded; the minimum hold becomes purely a design choice (time to read the hint).

## 6. Make the fallback team predictable

- **System:** Gameplay Framework (teams)
- **Found:** 2026-10-29
- **Status:** Planned (confirm with a UE_LOG of the team first)

**Now:** `AChrisGameMode::GetTeamIDForPlayer` falls back to `static int PlayerCount; return PlayerCount++ % 2;` when no hero was picked (solo PIE, practice mode). The function runs twice per player, and the `static` counter never resets, so it carries over between PIE sessions and practice runs.

**Problem:** A solo player's team can differ from one session to the next, and the first call claims a start spot for the wrong team.

**Plan:** Return a fixed team for the no-lobby case (e.g. team 0), or derive it from the player's index in the current match; never from a counter that outlives the match.

**Benefit:** Solo and practice behave the same every time; one less source of "it worked last time" bugs.

## Noted for later

- **Countdown input lock is client-side only:** `Client_OnCountdownStart` calls `DisableInput` on the client. The server should also refuse actions during the countdown. (Networking page)
- **RPC validation accepts everything:** every `_Validate` in `ALobbyPlayerController` returns `true`. Reject impossible values (e.g. slot ID beyond the max, null hero on select) so tampered clients are kicked; keep normal rule checks (slot occupied) in `_Implementation`. (Networking page)
- **Stale entries in `LoadedPlayers`:** if a player who already reported loaded leaves during the hold, their entry still counts in `LoadedPlayers.Num()`, so the hold could finish while someone else is still loading. Count only valid entries. (Match loop)
- **Two definitions of a kill:** the round tiebreak (`ReportKill`) counts hero kills on anything, minions included; the leaderboard (`AddHeroKill`) counts heroes killing heroes only. Confirm this is intended and document it. (Rounds & scoring)
