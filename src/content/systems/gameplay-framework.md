---
title: "Gameplay Framework"
summary: "How the game is architected: who owns what across menu, lobby and arena, and how a match flows from login to results."
order: 1
tags: ["C++", "GameMode", "GameState", "PlayerController", "PlayerState", "Match flow", "Flag capture"]
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

#### What it does

Champions Arena runs on a dedicated server. Each class in Unreal's gameplay framework has one job, and exists only on the machines that need it:

| Class | Job | Exists on | Lives for |
|---|---|---|---|
| `ChrisGameInstance` | Login, sessions, travel | Every machine, its own copy (never synced) | The whole time the game is running |
| `LobbyGameMode` / `ChrisGameMode` | The rules: decides what happens | Server only | One map |
| `ChrisGameState` | Shared match info: selections, kills, match stats | Server + every client | One map |
| `ChrisPlayerState` | One player's name, team slot and hero | Server + every client | One map (copied across on travel) |
| `LobbyPlayerController` / `ChrisPlayerController` | One player's link to the server | Server + that player's PC only | One map |
| Widgets | Lobby, HUD, shop, match stats | That player's PC only | While on screen |

#### How it works

Every player action follows the same path. Readying up in the lobby, for example:

1. The lobby widget on your PC calls a `Server_` RPC on your `LobbyPlayerController`.
2. The server's copy of your controller passes the request to the Game State, which checks you have a team slot and marks you ready.
3. The selection array is replicated, so every client receives it. `OnRep_PlayerSelectionArray` fires a delegate, and each lobby widget redraws, so your friend sees your green bar.

Going the other way, the server uses `Client_` RPCs on each controller for one-off events such as the round countdown and result banners.

#### Why I designed it this way



- **Separate lobby and arena maps, each with its own Game Mode** – they are never used at the same time, so loading both would waste memory, and one Game Mode handling both would fill up with "if lobby / else if arena" checks. Each map also gets its own controller and UI. The trade-off is a load between them, which is why the arena holds a loading screen until every player has arrived.
- **Requests go through the player's own controller** – only the server can change replicated data for everyone, and a client can only send RPCs through actors it owns. Widgets exist only on one PC, so they ask the controller, and the controller asks the server.
- **Seamless travel from lobby to arena** – players stay connected, so their Player States, with their team and hero, can be copied into the arena with `CopyProperties`. A hard travel would disconnect everyone, and the lobby refuses new joins once team selection is over, so players could not get back in.

### Per-map game modes & controllers

<figure class="diagram">
  <img src="../../diagrams/framework-per-map.svg" alt="Three rows, one per map. MainMenuLevel uses MainMenuGameMode, which uses MainMenuPlayerController_BP, which spawns the main menu UI. LobbyLevel uses LobbyGameMode, LobbyPlayerController_BP and the lobby UI. Lvl_ThirdPerson uses ChrisGameMode_BP, ChrisPlayerController and the hero and HUD." />
  <figcaption>Each map picks its rules, its controller and its UI.</figcaption>
</figure>

#### What it does

Each of the three maps runs with its own Game Mode and its own Player Controller, so the menu, the lobby and the arena only ever load the rules, input and UI they need.

#### How it works

The wiring is a chain set up in the editor:

1. Each map's **World Settings → GameMode Override** picks a Game Mode Blueprint. Maps without an override fall back to the project default, `ChrisGameMode_BP`.
2. Each Game Mode Blueprint sets a **Player Controller Class**, for example the lobby uses `LobbyPlayerController_BP`.
3. Each controller spawns its own UI. The menu controllers pick which widget to create through a `MenuWidgetClass` property set in their Blueprint.

<figure class="diagram">
  <img src="../../diagrams/framework-controllers.svg" alt="Inheritance tree. APlayerController is the parent of AMenuPlayerController and AChrisPlayerController. AMenuPlayerController is the parent of AMainMenuPlayerController and ALobbyPlayerController." />
  <figcaption>The two menu controllers share one base class; the arena controller does not.</figcaption>
</figure>

The main menu and lobby controllers both inherit from `AMenuPlayerController`, which shows the cursor, creates the menu widget, gives it keyboard and controller focus, and switches input to UI only. Each child then adds its own part: the main menu starts its music, and the lobby adds the RPCs for picking a slot, readying up, choosing a hero and locking in.

**When the widget is created** depends on the situation:

- **Main menu (not connected):** in `BeginPlay`. With no server, this machine has authority and is the local player, so it is safe to build the UI straight away.
- **Lobby (connected to the dedicated server):** in `OnRep_PlayerState`. On a client, the controller arrives first and the Player State a moment later, and the lobby UI needs the Player State to know who you are.
- **On the server:** never. The server's copy of each controller is not a local player, and the server has no screen.

#### Why I designed it this way

- **A shared menu base class** – the main menu and lobby need identical cursor, focus and widget handling, so it is written once. A fix to the menu setup fixes both screens.
- **The arena controller is separate** – it is not a kind of menu controller. It needs game-only input, the HUD, team IDs and the round RPCs, and inheriting the menu behaviour would give it a menu widget and UI-only input it would have to undo.
- **Wiring in Blueprints, logic in C++** – the C++ classes hold the behaviour, while the Blueprint children choose which widget and controller to use. Swapping a widget never needs a recompile.

### The match loop

<figure class="diagram">
  <img src="../../diagrams/framework-match-phases.svg" alt="Match phases. Waiting for players, then the loading hold, then a loop: round intro, countdown, in round, round end, transition to shop, shop, transition to arena, and back to round intro. From round end, a team with two round wins goes to match over." />
  <figcaption>Every phase of a match. The gold loop repeats until a team has won two rounds.</figcaption>
</figure>

#### What it does

`AChrisGameMode` runs the whole match as a **state machine**: one `EMatchPhase` value at a time, from players arriving, through a loading hold, into a loop of round intro, countdown, fight, result and shop, until one team has won two rounds.

#### How it works

**Getting everyone in.** Once enough players have joined, the server starts a loading hold. Each player's controller shows the loading screen, waits one frame so it is actually on screen, then tells the server it is ready with `Server_ReportLoaded`. The server keeps the ready players in a set, and ends the hold when everyone has reported and at least 15 seconds have passed, or after 25 seconds whatever happens.

**Moving between phases.** Each phase ends in one of two ways:

- **A timer** – the round's five minutes, the shop's 60 seconds, the fades.
- **A game event** – a team capturing a majority of the flags, or every player pressing Continue in the shop.

Either way, the next phase is started by one function, and players are told with `Client_` RPCs: banners, the countdown, camera fades and the shop UI.

**Keeping it from breaking.** Events can arrive at awkward moments, so every transition is protected:

- **Phase guards** – anything triggered from outside the timer chain checks the phase first. A flag captured during the shop, or a Continue vote after the shop has closed, is ignored.
- **One timer handle for "what comes next"** – setting a new timer on it replaces the old one, so only one next phase can ever be pending.
- **Cancel the timer when an event wins** – when flags end a round early, or everyone votes Continue, the pending timer is cleared before moving on, so it cannot fire again later.
- **Run once** – the loading hold can finish from two routes, so a flag makes sure it only finishes once.
- **Sets** – loaded players and Continue votes are stored in sets, so nobody counts twice.

Because Unreal runs gameplay on one thread, two of these events never truly happen at once: whichever runs first cancels the other's timer, and the phase guard rejects anything that arrives late.

#### Why I designed it this way

- **Timers and events instead of checking every frame** – the Game Mode does nothing between transitions instead of asking "is the round over yet?" 60 times a second. Each phase only says what ends it and what comes next.
- **A minimum loading hold** – everyone usually loads in a couple of seconds, but 15 seconds gives players time to read the hint and a breather between choosing heroes and fighting. The 25-second timeout means one slow PC cannot hold the whole match hostage.
- **Checking for the match winner before the shop** – the last round goes straight to the result instead of into a shop nobody needs.

### Rounds, teams & scoring

#### What it does

Players pick a team by clicking a slot in the lobby. That choice is carried into the arena, turned into team 0 or team 1, and used by everything that cares about sides. Teams then fight over three flags for up to five minutes a round, and the server decides each round's winner, pays out souls and keeps score until one team has won two rounds.

#### How it works: from lobby slot to arena team

<figure class="diagram">
  <img src="../../diagrams/framework-team-journey.svg" alt="Team journey in three stages. Lobby: click a slot, request it with a Server RPC, the Game State array updates, every lobby redraws, and your Player State keeps a copy. Travel: seamless travel and CopyProperties carry the copy to a new Player State. Arena: the slot becomes team 0 or 1, is set on the controller, picks a start spot, is copied to the hero, and replicates so every PC colours health bars." />
  <figcaption>A team is just a slot number until the arena turns it into team 0 or team 1.</figcaption>
</figure>

**In the lobby.** Each player's choice is an `FPlayerSelection` record: their slot (0–9), name, ready state, hero and lock-in. The lobby shows ten slots, 0–4 in the red column and 5–9 in the blue. Clicking one sends `Server_RequestSlotSelectionChange` through the player's `LobbyPlayerController`. On the server, the Game State refuses the request if the slot is taken, otherwise it moves the player's record to the new slot, or adds one on their first pick. Switching is blocked while the player is readied up.

The records live in the Game State's replicated `PlayerSelectionArray`, so every client receives the change and `OnRep_PlayerSelectionArray` redraws every lobby. Each Player State also listens for changes and keeps a copy of its own record.

**Travelling to the arena.** The Game State is destroyed when the server changes map; the Player State is not. That is why each Player State keeps its own copy. During seamless travel, `CopyProperties` hands the record to the player's new Player State in the arena.

**Turning the slot into a team.** When a player arrives, the arena Game Mode reads their new Player State and turns the slot into a team with one rule, the same rule the lobby used to build its columns:

```cpp
return PlayerSelection.GetPlayerSlot() < UChrisNetStatics::GetPlayerCountPerTeam() ? FGenericTeamId{ 0 } : FGenericTeamId{ 1 };
```

The team is set on the player's controller, used to claim one of that team's start spots, and copied onto the hero when the controller possesses it.

**Showing it to everyone.** Other players' PCs never have your controller, and minions have no controller at all, so the team is replicated on the character itself. When it arrives, `OnRep_TeamID` compares the character's team with the viewing player's own team, and colours the health bar green for an ally or red for an enemy. Flags, kills, AI and souls all ask a character or controller for its team through Unreal's `IGenericTeamAgentInterface`, casting to it and checking the result before using it.

#### How it works: ending and scoring a round

<figure class="diagram">
  <img src="../../diagrams/framework-round-scoring.svg" alt="A round ends on a flag majority, every flag being taken, or the five-minute timer. DetermineRoundWinner then checks five rules in order: flags captured, territory on the remaining flag, total territory, kills this round, otherwise replay. The server pays souls, adds a round win, and either ends the match at two wins or moves to the shop." />
  <figcaption>How a round ends, who wins it, and what happens next.</figcaption>
</figure>

**Ending a round.** Every flag capture triggers a recount of all flags. A round ends early as soon as one team holds a majority (2 of 3), because captured flags cannot be retaken, so the result can no longer change. If every flag is taken without a majority, which only happens with an even number of flags, the round also ends. Otherwise the five-minute timer ends it.

**Picking the winner.** `DetermineRoundWinner` walks down a ladder and stops at the first rule that separates the teams: flags captured, then territory on the remaining flag, then total territory if nobody captured anything, then kills this round. If everything is equal, the round is replayed.

**Scoring.** Souls are paid to every player at the end of each round, then the winning team gets a round win. The first team to two wins ends the match; otherwise everyone goes to the shop.

#### Why I designed it this way

- **The slot is the team** – one number decides both the lobby column and the arena team, so the two can never disagree.
- **A copy on the Player State** – the lobby only needs the Game State's array, but the Game State does not survive travel. The copy only ever flows one way, from the array to the Player State, so the two cannot drift apart.
- **Team on the character, not just the controller** – other players' PCs never have your controller, and minions have none at all, so every character carries its own team.
- **Recount the flags instead of keeping a tally** – the flags themselves are the single source of truth. A separate running score could drift out of sync after a missed event or a reset between rounds; a recount is always right and costs almost nothing with three flags.
- **End the round on a majority** – once a team holds two of three flags it cannot be caught, so playing out the timer would just be waiting.
- **A tiebreak ladder instead of draws** – rounds almost always produce a winner, and kills only matter when the objective is genuinely level. Kills reset every round so an early lead cannot decide a later tie.
- **Losers earn more souls** – the losing team gets 100 and the winners 50, so falling behind buys a bigger upgrade in the shop and matches stay close. A rare draw pays both teams 100, so the replayed round plays differently.

### Flag capture

<div class="placeholder">GIF / screenshot: Flag capture</div>

#### What it does

TODO: capture zones, hero and minion weighting, capture progress, replication and the on-screen gauges.

#### How it works

TODO

#### Why I designed it this way

TODO

### Characters & hero data

<div class="placeholder">GIF / screenshot: Characters & hero data</div>

#### What it does

TODO: ChrisCharacter / ChrisPlayerCharacter and data-driven heroes via PA_CharacterDefinition.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

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
