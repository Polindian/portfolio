---
title: "Gameplay Framework"
summary: "How the game is architected: who owns what across menu, lobby and arena, and how a match flows from login to results."
order: 1
tags: ["C++", "GameMode", "GameState", "PlayerController", "PlayerState", "Match flow"]
glance:
  - "TODO: e.g. Separate GameMode / PlayerController pairs per map (menu, lobby, arena)"
  - "TODO: e.g. Server-only GameMode drives rounds; GameState replicates match state to everyone"
  - "TODO: e.g. GameInstance persists login and session data across map travel"
keyFiles:
  - { path: "Framework/ChrisGameInstance.cpp", note: "Persists login & sessions across travel" }
  - { path: "Framework/ChrisGameMode.cpp", note: "Server-only rules: rounds, teams, match end" }
  - { path: "Framework/ChrisGameState.cpp", note: "Replicated match state" }
  - { path: "Framework/LobbyGameMode.cpp", note: "Lobby & hero selection rules" }
  - { path: "Player/ChrisPlayerController.cpp", note: "Per-player input & UI ownership" }
  - { path: "Player/ChrisPlayerState.cpp", note: "Per-player replicated stats" }
  - { path: "Character/ChrisCharacter.cpp", note: "Base character" }
status: draft
---

## Features

### Class architecture

<div class="placeholder">GIF / screenshot: Class architecture</div>

**What it does.** TODO: which classes exist, where they live (server, client or both) and why.

**How it works.** TODO

**Why I designed it this way.** TODO: alternatives considered and trade-offs.

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

TODO: honest self-critique and planned refactors.
