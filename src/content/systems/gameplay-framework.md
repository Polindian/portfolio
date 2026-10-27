---
title: "Gameplay Framework"
summary: "How the game is architected: who owns what across menu, lobby and arena, and how a match flows from login to results."
order: 1
tags: ["C++", "GameMode", "GameState", "PlayerController", "PlayerState", "Match flow"]
glance:
  - "Each map (menu, lobby, arena) has its own Game Mode and Player Controller"
  - "The Game Mode decides on the server; the Game State shares the result with every player"
  - "Every player action is a Server RPC through their own controller, and reaches everyone else by replication"
keyFiles:
  - { path: "Framework/ChrisGameInstance.cpp", note: "Persists login & sessions across travel" }
  - { path: "Framework/ChrisGameMode.cpp", note: "Server-only rules: rounds, teams, match end" }
  - { path: "Framework/ChrisGameState.cpp", note: "Replicated match state" }
  - { path: "Framework/LobbyGameMode.cpp", note: "Lobby rules: seamless travel, refusing late joins" }
  - { path: "Player/LobbyPlayerController.cpp", note: "Lobby requests: slot, ready, hero, lock-in" }
  - { path: "Player/ChrisPlayerController.cpp", note: "Per-player input & UI ownership" }
  - { path: "Player/ChrisPlayerState.cpp", note: "Per-player replicated stats" }
  - { path: "Character/ChrisCharacter.cpp", note: "Base character" }
status: draft
---

## Features

### Class architecture

<figure class="diagram">
  <img src="../../diagrams/framework-classes.svg" alt="Diagram showing which framework classes exist on the dedicated server and on each player's PC, with replication arrows from the server's Game State and Player States to the clients, and RPC arrows between each player's controller and its server copy." />
  <figcaption>Which classes exist on which machine, and how they talk to each other.</figcaption>
</figure>

**What it does.** Champions Arena runs on a dedicated server. Each class in Unreal's gameplay framework has one job, and exists only on the machines that need it:

| Class | Job | Exists on | Lives for |
|---|---|---|---|
| `ChrisGameInstance` | Login, sessions, travel | Every machine, its own copy (never synced) | The whole time the game is running |
| `LobbyGameMode` / `ChrisGameMode` | The rules: decides what happens | Server only | One map |
| `ChrisGameState` | Shared match info: selections, kills, match stats | Server + every client | One map |
| `ChrisPlayerState` | One player's name, team slot and hero | Server + every client | One map (copied across on travel) |
| `LobbyPlayerController` / `ChrisPlayerController` | One player's link to the server | Server + that player's PC only | One map |
| Widgets | Lobby, HUD, shop, match stats | That player's PC only | While on screen |

**How it works.** Every player action follows the same path. Readying up in the lobby, for example:

1. The lobby widget on your PC calls a `Server_` RPC on your `LobbyPlayerController`.
2. The server's copy of your controller passes the request to the Game State, which checks you have a team slot and marks you ready.
3. The selection array is replicated, so every client receives it. `OnRep_PlayerSelectionArray` fires a delegate, and each lobby widget redraws, so your friend sees your green bar.

Going the other way, the server uses `Client_` RPCs on each controller for one-off events such as the round countdown and result banners.

**Why I designed it this way.**

- **Separate lobby and arena maps, each with its own Game Mode.** They are never used at the same time, so loading both would waste memory, and one Game Mode handling both would fill up with "if lobby / else if arena" checks. Each map also gets its own controller and UI. The trade-off is a load between them, which is why the arena holds a loading screen until every player has arrived.
- **Requests go through the player's own controller.** Only the server can change replicated data for everyone, and a client can only send RPCs through actors it owns. Widgets exist only on one PC, so they ask the controller, and the controller asks the server.
- **Seamless travel from lobby to arena.** Players stay connected, so their Player States, with their team and hero, can be copied into the arena with `CopyProperties`. A hard travel would disconnect everyone, and the lobby refuses new joins once team selection is over, so players could not get back in.

### Per-map game modes & controllers

<div class="placeholder">GIF / screenshot: Per-map game modes & controllers</div>

**What it does.** TODO: MainMenu, Lobby and Arena each have their own GameMode/PlayerController pair, and the AMenuPlayerController base.

**How it works.** TODO

**Why I designed it this way.** TODO: alternatives considered and trade-offs.

### The match loop

<div class="placeholder">GIF / screenshot: The match loop</div>

**What it does.** TODO: trace one player: login → lobby → hero select → arena rounds → match end → stats.

**How it works.** TODO

**Why I designed it this way.** TODO: alternatives considered and trade-offs.

### Rounds, teams & flag capture

<div class="placeholder">GIF / screenshot: Rounds, teams & flag capture</div>

**What it does.** TODO: how ChrisGameMode runs rounds and win conditions, and what ChrisGameState replicates.

**How it works.** TODO

**Why I designed it this way.** TODO: alternatives considered and trade-offs.

### Characters & hero data

<div class="placeholder">GIF / screenshot: Characters & hero data</div>

**What it does.** TODO: ChrisCharacter / ChrisPlayerCharacter and data-driven heroes via PA_CharacterDefinition.

**How it works.** TODO

**Why I designed it this way.** TODO: alternatives considered and trade-offs.

## How it connects

- GAS & Combat — characters own the Ability System Component
- Networking — what replicates and who has authority
- Online Backend — GameInstance holds login/session state

## Challenges & bugs

**Symptom → cause → fix → lesson.** TODO: Lobby animations froze because LobbyGameMode inherited from AGameMode instead of AGameModeBase (the world stayed in WaitingToStart).

## Optimisations

TODO: before/after, with numbers where possible.

## What I'd do differently

### Match phase lives in the Game Mode, not the Game State

The current match phase is stored in `AChrisGameMode`, which only exists on the server. Every phase change, and every second of the countdown, is pushed to each player with a `Client_` RPC on their Player Controller.

That works, but RPCs are one-off messages: a player who reconnects mid-round never learns which phase the match is in. It also sends a message every second to every player.

**The fix:** replicate the phase and the time it ends (`PhaseEndServerTime`) on `AChrisGameState`. Each client works out the remaining time locally from the server clock, so there is one update per phase instead of one per second, and late joiners see the right state immediately.
