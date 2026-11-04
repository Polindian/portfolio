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
  - { path: "Framework/Flag.cpp", note: "Capture zones, rates and progress" }
  - { path: "Widgets/FlagCaptureGaugeWidget.cpp", note: "Zone gauges on the HUD" }
  - { path: "Widgets/FlagProgressWidget.cpp", note: "Tug-of-war bar in a zone" }
  - { path: "Character/ChrisCharacter.cpp", note: "Base character" }
status: draft
---

## Features

### Class architecture

<figure class="diagram">
  <a href="../../diagrams/framework-classes.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/framework-classes.svg" alt="Diagram showing which framework classes exist on the dedicated server and on each player's PC, with replication arrows from the server's Game State and Player States to the clients, and RPC arrows between each player's controller and its server copy." /></a>
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
2. The server's copy of your controller passes the request to the Game State ([`RequestPlayerReadyChange`](code:AChrisGameState::RequestPlayerReadyChange)), which checks you have a team slot and marks you ready.
3. The selection array is replicated, so every client receives it. [`OnRep_PlayerSelectionArray`](code:AChrisGameState::OnRep_PlayerSelectionArray) fires a delegate, and each lobby widget redraws, so your friend sees your green bar.

Going the other way, the server uses `Client_` RPCs on each controller for one-off events such as the round countdown and result banners.

#### Why I designed it this way



- **Separate lobby and arena maps, each with its own Game Mode** – they are never used at the same time, so loading both would waste memory, and one Game Mode handling both would fill up with "if lobby / else if arena" checks. Each map also gets its own controller and UI. The trade-off is a load between them, which is why the arena holds a loading screen until every player has arrived.
- **Requests go through the player's own controller** – only the server can change replicated data for everyone, and a client can only send RPCs through actors it owns. Widgets exist only on one PC, so they ask the controller, and the controller asks the server.
- **Seamless travel from lobby to arena** – players stay connected, so their Player States, with their team and hero, can be copied into the arena with [`CopyProperties`](code:AChrisPlayerState::CopyProperties). A hard travel would disconnect everyone, and the lobby refuses new joins once team selection is over, so players could not get back in.

### Per-map game modes & controllers

<figure class="diagram">
  <a href="../../diagrams/framework-per-map.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/framework-per-map.svg" alt="Three rows, one per map. MainMenuLevel uses MainMenuGameMode, which uses MainMenuPlayerController_BP, which spawns the main menu UI. LobbyLevel uses LobbyGameMode, LobbyPlayerController_BP and the lobby UI. Lvl_ThirdPerson uses ChrisGameMode_BP, ChrisPlayerController and the hero and HUD." /></a>
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
  <a href="../../diagrams/framework-controllers.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/framework-controllers.svg" alt="Inheritance tree. APlayerController is the parent of AMenuPlayerController and AChrisPlayerController. AMenuPlayerController is the parent of AMainMenuPlayerController and ALobbyPlayerController." /></a>
  <figcaption>The two menu controllers share one base class; the arena controller does not.</figcaption>
</figure>

The main menu and lobby controllers both inherit from [`AMenuPlayerController`](code:AMenuPlayerController), which shows the cursor, creates the menu widget ([`SpawnWidget`](code:AMenuPlayerController::SpawnWidget)), gives it keyboard and controller focus, and switches input to UI only. Each child then adds its own part: the main menu starts its music, and the lobby adds the RPCs for picking a slot, readying up, choosing a hero and locking in.

**When the widget is created** depends on the situation:

- **Main menu (not connected)** – in [`BeginPlay`](code:AMenuPlayerController::BeginPlay). With no server, this machine has authority and is the local player, so it is safe to build the UI straight away.
- **Lobby (connected to the dedicated server)** – in [`OnRep_PlayerState`](code:AMenuPlayerController::OnRep_PlayerState). On a client, the controller arrives first and the Player State a moment later, and the lobby UI needs the Player State to know who you are.
- **On the server** – never. The server's copy of each controller is not a local player, and the server has no screen.

#### Why I designed it this way

- **A shared menu base class** – the main menu and lobby need identical cursor, focus and widget handling, so it is written once. A fix to the menu setup fixes both screens.
- **The arena controller is separate** – it is not a kind of menu controller. It needs game-only input, the HUD, team IDs and the round RPCs, and inheriting the menu behaviour would give it a menu widget and UI-only input it would have to undo.
- **Wiring in Blueprints, logic in C++** – the C++ classes hold the behaviour, while the Blueprint children choose which widget and controller to use. Swapping a widget never needs a recompile.

### The match loop

<figure class="diagram">
  <a href="../../diagrams/framework-match-phases.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/framework-match-phases.svg" alt="Match phases in ten numbered steps, each with the function that runs it: PostLogin while waiting for players, StartLoadingHold, then a loop of StartRoundIntro, StartCountdown, StartRound, EndRound, StartTransitionToShop, StartShopPhase and StartTransitionToArena, back to the round intro. From EndRound, a team with two round wins goes to EndMatch." /></a>
  <figcaption>Every phase of a match. The gold loop repeats until a team has won two rounds.</figcaption>
</figure>

#### What it does

[`AChrisGameMode`](code:AChrisGameMode) runs the whole match as a **state machine**: one `EMatchPhase` value at a time, from players arriving, through a loading hold, into a loop of round intro, countdown, fight, result and shop, until one team has won two rounds.

#### Step by step

The numbers match the diagram. Every phase is started by one function, and ends with a timer or event that calls the next one.

| # | Phase | Started by | Ends when → calls next |
|---|---|---|---|
| 1 | WaitingForPlayers | The default phase | Each join runs [`PostLogin`](code:AChrisGameMode::PostLogin); once everyone is in → `StartLoadingHold` |
| 2 | Loading hold | [`StartLoadingHold`](code:AChrisGameMode::StartLoadingHold) | Each PC's [`Server_ReportLoaded`](code:AChrisPlayerController::Server_ReportLoaded_Implementation) → [`ReportPlayerLoaded`](code:AChrisGameMode::ReportPlayerLoaded) → [`TryFinishLoadingHold`](code:AChrisGameMode::TryFinishLoadingHold); the 15 s timer also tries, the 25 s timer forces it → [`FinishLoadingHold`](code:AChrisGameMode::FinishLoadingHold) → timer → `StartRoundIntro` |
| 3 | RoundIntro | [`StartRoundIntro`](code:AChrisGameMode::StartRoundIntro) | Banner timer → `StartCountdown` |
| 4 | Countdown | [`StartCountdown`](code:AChrisGameMode::StartCountdown) | [`CountdownTick`](code:AChrisGameMode::CountdownTick) every second; at zero → `StartRound` |
| 5 | InRound | [`StartRound`](code:AChrisGameMode::StartRound) | Round timer → `EndRound`, or a capture → [`OnFlagCapturedCallback`](code:AChrisGameMode::OnFlagCapturedCallback) clears the timer → `EndRound` |
| 6 | RoundEnd | [`EndRound`](code:AChrisGameMode::EndRound) | [`AwardRoundEndSouls`](code:AChrisGameMode::AwardRoundEndSouls) scores the round; two wins → `EndMatch`, otherwise timer → `StartTransitionToShop` |
| 7 | TransitionToShop | [`StartTransitionToShop`](code:AChrisGameMode::StartTransitionToShop) | Fade out → [`OnTransitionToShopMidpoint`](code:AChrisGameMode::OnTransitionToShopMidpoint) clears AI and resets players → [`OnTransitionToShopFadeIn`](code:AChrisGameMode::OnTransitionToShopFadeIn) → `StartShopPhase` |
| 8 | ShopPhase | [`StartShopPhase`](code:AChrisGameMode::StartShopPhase) | 60 s timer, or every PC's [`Server_VoteContinue`](code:AChrisPlayerController::Server_VoteContinue_Implementation) → [`OnPlayerVoteContinue`](code:AChrisGameMode::OnPlayerVoteContinue) clears the timer → `StartTransitionToArena` |
| 9 | TransitionToArena | [`StartTransitionToArena`](code:AChrisGameMode::StartTransitionToArena) | Fade out → [`OnTransitionToArenaMidpoint`](code:AChrisGameMode::OnTransitionToArenaMidpoint) resets the flags → [`OnTransitionToArenaFadeIn`](code:AChrisGameMode::OnTransitionToArenaFadeIn) → back to step 3 |
| 10 | MatchOver | [`EndMatch`](code:AChrisGameMode::EndMatch) | Timer → [`ShowMatchResultBanner`](code:AChrisGameMode::ShowMatchResultBanner) → timer → [`ShowMatchStats`](code:AChrisGameMode::ShowMatchStats) |

#### How it works

**Getting everyone in** – once enough players have joined, the server starts a loading hold ([`StartLoadingHold`](code:AChrisGameMode::StartLoadingHold)). Each player's controller shows the loading screen ([`BeginPlay`](code:AChrisPlayerController::BeginPlay)), waits one frame so it is actually on screen, then tells the server it is ready with [`Server_ReportLoaded`](code:AChrisPlayerController::Server_ReportLoaded_Implementation). The server keeps the ready players in a set ([`ReportPlayerLoaded`](code:AChrisGameMode::ReportPlayerLoaded)), and ends the hold ([`TryFinishLoadingHold`](code:AChrisGameMode::TryFinishLoadingHold)) when everyone has reported and at least 15 seconds have passed, or after 25 seconds whatever happens.

**Moving between phases** – each phase ends in one of two ways:

- **A timer** – the round's five minutes, the shop's 60 seconds, the fades.
- **A game event** – a team capturing a majority of the flags, or every player pressing Continue in the shop.

Either way, the next phase is started by one function, and players are told with `Client_` RPCs: banners, the countdown, camera fades and the shop UI.

**Keeping it from breaking** – events can arrive at awkward moments, so every transition is protected:

- **Phase guards** – anything triggered from outside the timer chain checks the phase first. A flag captured during the shop ([`OnFlagCapturedCallback`](code:AChrisGameMode::OnFlagCapturedCallback)), or a Continue vote after the shop has closed ([`OnPlayerVoteContinue`](code:AChrisGameMode::OnPlayerVoteContinue)), is ignored.
- **One timer handle for "what comes next"** – setting a new timer on it replaces the old one, so only one next phase can ever be pending.
- **Cancel the timer when an event wins** – when flags end a round early, or everyone votes Continue, the pending timer is cleared before moving on, so it cannot fire again later.
- **Run once** – the loading hold can finish from two routes, so a flag makes sure it only finishes once ([`FinishLoadingHold`](code:AChrisGameMode::FinishLoadingHold)).
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
  <a href="../../diagrams/framework-team-journey.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/framework-team-journey.svg" alt="Team journey in thirteen numbered steps across the lobby, travel and the arena. The table below lists every function." /></a>
  <figcaption>A team is just a slot number until the arena turns it into team 0 or team 1.</figcaption>
</figure>

**Step by step** – the numbers match the diagram.

| # | Step | Calls, in order | Runs on |
|---|---|---|---|
| 1 | Click a slot | Lobby widget [`SlotSelected`](code:ULobbyWidget::SlotSelected) | The PC |
| 2 | Request the slot | Lobby controller `Server_RequestSlotSelectionChange` (a Server RPC) | Sent by the PC |
| 3 | Game State array | [`Server_RequestSlotSelectionChange`](code:ALobbyPlayerController::Server_RequestSlotSelectionChange_Implementation) → Game State [`RequestPlayerSelectionChange`](code:AChrisGameState::RequestPlayerSelectionChange) moves or adds the record | Server |
| 4 | Every lobby redraws | Array replicates → [`OnRep_PlayerSelectionArray`](code:AChrisGameState::OnRep_PlayerSelectionArray) → lobby widgets | Every PC |
| 5 | Player State copy | `OnPlayerSelectionUpdated` → [`PlayerSelectionUpdated`](code:AChrisPlayerState::PlayerSelectionUpdated) copies its own record | Server and every PC |
| 6 | Seamless travel | Game State [`StartMatch`](code:AChrisGameState::StartMatch) → Game Instance [`StartMatch`](code:UChrisGameInstance::StartMatch) | Server |
| 7 | Carry the record | Old Player State [`CopyProperties`](code:AChrisPlayerState::CopyProperties) → new Player State | Server |
| 8 | Slot becomes a team | [`HandleSeamlessTravelPlayer`](code:AChrisGameMode::HandleSeamlessTravelPlayer) → [`GetTeamIDForPlayer`](code:AChrisGameMode::GetTeamIDForPlayer) → [`GetTeamIdBasedOnSlot`](code:AChrisPlayerState::GetTeamIdBasedOnSlot) | Server |
| 9 | Controller team | Controller [`SetGenericTeamId`](code:AChrisPlayerController::SetGenericTeamId) | Server |
| 10 | Team start spot | [`FindNextStartSpotForTeam`](code:AChrisGameMode::FindNextStartSpotForTeam) | Server |
| 11 | Hero gets the team | Controller [`OnPossess`](code:AChrisPlayerController::OnPossess) → hero [`SetGenericTeamId`](code:AChrisCharacter::SetGenericTeamId) | Server |
| 12 | Health bars coloured | Team replicates → [`OnRep_TeamID`](code:AChrisCharacter::OnRep_TeamID) → [`ConfigureTeamColor`](code:UOverheadStatsGauge::ConfigureTeamColor) | Every PC |
| 13 | Everything else asks | Cast to `IGenericTeamAgentInterface` → [`GetGenericTeamId`](code:AChrisCharacter::GetGenericTeamId) | Wherever it is needed |

**In the lobby** – each player's choice is an [`FPlayerSelection`](code:FPlayerSelection) record: their slot (0–9), name, ready state, hero and lock-in. The lobby shows ten slots ([`ClearAndPopulateTeamSelectionSlots`](code:ULobbyWidget::ClearAndPopulateTeamSelectionSlots)), 0–4 in the red column and 5–9 in the blue. Clicking one ([`SlotSelected`](code:ULobbyWidget::SlotSelected)) sends [`Server_RequestSlotSelectionChange`](code:ALobbyPlayerController::Server_RequestSlotSelectionChange_Implementation) through the player's `LobbyPlayerController`. On the server, the Game State ([`RequestPlayerSelectionChange`](code:AChrisGameState::RequestPlayerSelectionChange)) refuses the request if the slot is taken, otherwise it moves the player's record to the new slot, or adds one on their first pick. Switching is blocked while the player is readied up.

The records live in the Game State's replicated `PlayerSelectionArray`, so every client receives the change and [`OnRep_PlayerSelectionArray`](code:AChrisGameState::OnRep_PlayerSelectionArray) redraws every lobby. Each Player State also listens for changes and keeps a copy of its own record ([`PlayerSelectionUpdated`](code:AChrisPlayerState::PlayerSelectionUpdated)).

**Travelling to the arena** – the Game State is destroyed when the server changes map; the Player State is not. That is why each Player State keeps its own copy. During seamless travel, [`CopyProperties`](code:AChrisPlayerState::CopyProperties) hands the record to the player's new Player State in the arena.

**Turning the slot into a team** – when a player arrives ([`HandleSeamlessTravelPlayer`](code:AChrisGameMode::HandleSeamlessTravelPlayer)), the arena Game Mode reads their new Player State ([`GetTeamIDForPlayer`](code:AChrisGameMode::GetTeamIDForPlayer)) and turns the slot into a team with one rule ([`GetTeamIdBasedOnSlot`](code:AChrisPlayerState::GetTeamIdBasedOnSlot)), the same rule the lobby used to build its columns:

```cpp
return PlayerSelection.GetPlayerSlot() < UChrisNetStatics::GetPlayerCountPerTeam() ? FGenericTeamId{ 0 } : FGenericTeamId{ 1 };
```

The team is set on the player's controller, used to claim one of that team's start spots ([`FindNextStartSpotForTeam`](code:AChrisGameMode::FindNextStartSpotForTeam)), and copied onto the hero when the controller possesses it ([`OnPossess`](code:AChrisPlayerController::OnPossess)).

**Showing it to everyone** – other players' PCs never have your controller, and minions have no controller at all, so the team is replicated on the character itself. When it arrives, [`OnRep_TeamID`](code:AChrisCharacter::OnRep_TeamID) compares the character's team with the viewing player's own team ([`ConfigureTeamColor`](code:UOverheadStatsGauge::ConfigureTeamColor)), and colours the health bar green for an ally or red for an enemy. Flags, kills, AI and souls all ask a character or controller for its team through Unreal's `IGenericTeamAgentInterface`, casting to it and checking the result before using it.

#### How it works: ending and scoring a round

<figure class="diagram">
  <a href="../../diagrams/framework-round-scoring.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/framework-round-scoring.svg" alt="Round scoring in six numbered steps: the round ends and calls EndRound, DetermineRoundWinner checks five rules in order, AwardRoundEndSouls adds the round win and pays souls, EndRound checks for two wins, then EndMatch or StartTransitionToShop." /></a>
  <figcaption>How a round ends, who wins it, and what happens next.</figcaption>
</figure>

**Step by step** – the numbers match the diagram. All of it runs on the server.

| # | Step | Calls, in order |
|---|---|---|
| 1 | The round ends | A capture → [`OnFlagCapturedCallback`](code:AChrisGameMode::OnFlagCapturedCallback) recounts the flags and, on a majority or all flags taken, clears the timer; or the round timer from [`StartRound`](code:AChrisGameMode::StartRound) fires. Either way → [`EndRound`](code:AChrisGameMode::EndRound) |
| 2 | Pick the winner | `EndRound` → [`AwardRoundEndSouls`](code:AChrisGameMode::AwardRoundEndSouls) → [`DetermineRoundWinner`](code:AChrisGameMode::DetermineRoundWinner), using kills counted during the round by [`ReportKill`](code:AChrisGameMode::ReportKill) |
| 3 | Add a round win | Back in `AwardRoundEndSouls`, the winning team's round wins go up by one |
| 4 | Pay souls | Still in `AwardRoundEndSouls`, every player's soul attribute is increased |
| 5 | Check for two wins | Back in `EndRound` |
| 6 | Match over, or shop | Two wins → [`EndMatch`](code:AChrisGameMode::EndMatch); otherwise timer → [`StartTransitionToShop`](code:AChrisGameMode::StartTransitionToShop) |

**Ending a round** – every flag capture triggers a recount of all flags ([`OnFlagCapturedCallback`](code:AChrisGameMode::OnFlagCapturedCallback)). A round ends early as soon as one team holds a majority (2 of 3), because captured flags cannot be retaken, so the result can no longer change. If every flag is taken without a majority, which only happens with an even number of flags, the round also ends. Otherwise the five-minute timer ends it.

**Picking the winner** – [`DetermineRoundWinner`](code:AChrisGameMode::DetermineRoundWinner) walks down a ladder and stops at the first rule that separates the teams: flags captured, then territory on the remaining flag, then total territory if nobody captured anything, then kills this round ([`ReportKill`](code:AChrisGameMode::ReportKill)). If everything is equal, the round is replayed.

**Scoring** – [`AwardRoundEndSouls`](code:AChrisGameMode::AwardRoundEndSouls) asks for the winner, gives that team a round win, then pays souls to every player. Back in [`EndRound`](code:AChrisGameMode::EndRound), the first team to two wins ends the match ([`EndMatch`](code:AChrisGameMode::EndMatch)); otherwise everyone goes to the shop.

#### Why I designed it this way

- **The slot is the team** – one number decides both the lobby column and the arena team, so the two can never disagree.
- **A copy on the Player State** – the lobby only needs the Game State's array, but the Game State does not survive travel. The slot only ever flows one way, from the array to the Player State, so the two cannot disagree about teams.
- **Team on the character, not just the controller** – other players' PCs never have your controller, and minions have none at all, so every character carries its own team.
- **Recount the flags instead of keeping a tally** – the flags themselves are the single source of truth. A separate running score could drift out of sync after a missed event or a reset between rounds; a recount is always right and costs almost nothing with three flags.
- **End the round on a majority** – once a team holds two of three flags it cannot be caught, so playing out the timer would just be waiting.
- **A tiebreak ladder instead of draws** – rounds almost always produce a winner, and kills only matter when the objective is genuinely level. Kills reset every round so an early lead cannot decide a later tie.
- **Losers earn more souls** – the losing team gets 100 and the winners 50, so falling behind buys a bigger upgrade in the shop and matches stay close. A rare draw pays both teams 100, so the replayed round plays differently.

### Flag capture

<figure class="diagram">
  <a href="../../diagrams/framework-flag-capture.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/framework-flag-capture.svg" alt="Flag capture in nine numbered steps: six on the server every frame, then three on each player PC. The table below lists every function." /></a>
  <figcaption>The server decides everything about a flag; each player's PC only shows it.</figcaption>
</figure>

#### What it does

Each of the three flags is a capture zone. Heroes and minions standing in it push it towards their team, heroes three times as hard as minions. A contested zone drains the other team's progress before it can build your own, and once a flag reaches 100% it is captured for the rest of the round. Every player sees all three zones' progress on their HUD, and a tug-of-war bar shows who is pushing harder in the zone they are standing in.

#### Step by step

The numbers match the diagram.

| # | Step | Calls, in order | Runs on |
|---|---|---|---|
| 1 | Who is in the zone | Sphere overlap → [`OnInfluencerEnter`](code:AFlag::OnInfluencerEnter) / [`OnInfluencerExit`](code:AFlag::OnInfluencerExit) | Server |
| 2 | Team rates | [`Tick`](code:AFlag::Tick) → [`RecalculateCaptureRates`](code:AFlag::RecalculateCaptureRates) → [`GetActorCaptureWeight`](code:AFlag::GetActorCaptureWeight) for each character | Server, every frame |
| 3 | Capture progress | Rest of `Tick`: net rate × `DeltaTime`, drain, flip, clamp | Server, every frame |
| 4 | Captured at 100% | `Tick` → `OnFlagCaptured.Broadcast` and [`PlayTeamCaptureBanner`](code:AFlag::PlayTeamCaptureBanner) → [`PlayBannerSlam`](code:AFlag::PlayBannerSlam) | Server |
| 5 | Zone rewards | `Tick` → Game State [`AddCaptureTime`](code:AChrisGameState::AddCaptureTime) and XP for each hero every 8 seconds | Server, every frame |
| 6 | Majority check | Game Mode [`OnFlagCapturedCallback`](code:AChrisGameMode::OnFlagCapturedCallback) (see Rounds, teams & scoring) | Server |
| 7 | Zone gauges | [`UFlagCaptureGaugeWidget::NativeTick`](code:UFlagCaptureGaugeWidget::NativeTick) reads the replicated percent and owner | Every PC, every frame |
| 8 | Tug-of-war bar | [`UFlagProgressWidget::NativeTick`](code:UFlagProgressWidget::NativeTick) → [`FindLocalPlayerFlag`](code:UFlagProgressWidget::FindLocalPlayerFlag) | Every PC, every frame |
| 9 | Banner | `BannerState` replicates → [`OnRep_BannerState`](code:AFlag::OnRep_BannerState) → [`ApplyBannerState`](code:AFlag::ApplyBannerState) | Every PC |

Around all of this, the Game Mode switches every flag on and subscribes to step 4 in [`StartRound`](code:AChrisGameMode::StartRound) ([`SetCaptureEnabled`](code:AFlag::SetCaptureEnabled)), and resets them between rounds in [`OnTransitionToArenaMidpoint`](code:AChrisGameMode::OnTransitionToArenaMidpoint) ([`ResetCapture`](code:AFlag::ResetCapture)).

#### How it works

**Who is in the zone** – the flag is a sphere that only reacts to pawns, so projectiles and props never trigger it. Enter and exit events ([`OnInfluencerEnter`](code:AFlag::OnInfluencerEnter), [`OnInfluencerExit`](code:AFlag::OnInfluencerExit)) keep two sets: every character that can say which team it is on, and the heroes on their own for rewards.

**How hard each team pushes** – every frame of a round, the server adds up each team's weight in the zone ([`RecalculateCaptureRates`](code:AFlag::RecalculateCaptureRates)). A hero counts 3 plus any Dominion upgrade, a minion counts 1 ([`GetActorCaptureWeight`](code:AFlag::GetActorCaptureWeight)). Dead characters are skipped while their bodies still overlap the zone, and anything destroyed without an exit event is removed.

**Moving the percentage** – the flag's [`Tick`](code:AFlag::Tick) runs only on the server, and only while capture is enabled for the round. It takes the difference between the two teams' rates and moves the percentage by that much per second, using `DeltaTime` so capture speed follows real time rather than the server's frame rate. A lone hero captures a neutral flag in about 33 seconds. If the other team owns some progress, it drains first; when it crosses zero, ownership flips and the leftover carries over. A perfectly balanced zone does not move. At 100% the flag is captured, tells the Game Mode through its `OnFlagCaptured` event, and slams its banner in the team's colour ([`PlayBannerSlam`](code:AFlag::PlayBannerSlam)).

**Rewards** – while a flag is uncaptured, every living hero in the zone earns 50 XP for each 8 seconds spent in any zone, and capture time for the match stats. The timer lives on the hero, so time spent on different zones adds up.

**What every player sees** – the flag replicates its percentage, owner, team rates, captured state and banner, and is always relevant, so every player gets updates for every zone however far away they are. The zone gauges ([`UFlagCaptureGaugeWidget::NativeTick`](code:UFlagCaptureGaugeWidget::NativeTick)) smooth the percentage between network updates so the fill glides instead of jumping. The tug-of-war bar ([`UFlagProgressWidget::NativeTick`](code:UFlagProgressWidget::NativeTick)) shows the share of red against blue weight, and appears when the player's own PC finds them inside a zone ([`FindLocalPlayerFlag`](code:UFlagProgressWidget::FindLocalPlayerFlag)). The banner plays from [`OnRep_BannerState`](code:AFlag::OnRep_BannerState) on clients, and is applied directly on the server, where an OnRep never fires.

**Each round** – the Game Mode enables every flag and subscribes to its capture event when the round starts ([`StartRound`](code:AChrisGameMode::StartRound)), unsubscribes when it ends so captures are never counted twice in later rounds, and resets every flag during the black screen before the next one ([`ResetCapture`](code:AFlag::ResetCapture)).

#### Why I designed it this way

- **Track membership by events, recompute rates every frame** – players die, respawn, get destroyed and buy upgrades while standing still, and none of that fires an exit event. Recounting a handful of characters on three flags costs almost nothing and is always right, where adding and subtracting on events would go wrong the first time one was missed.
- **Heroes count three times as much as minions** – minions help hold ground, but a hero arriving should matter. Dominion lets players invest in becoming even stronger on objectives.
- **Drain before you gain** – a team has to undo the enemy's progress before building its own, so a flag that is nearly lost can still be saved, and flips are earned.
- **Rewards in contested zones too** – holding a contested zone is the hardest thing a player can do, even when the bar is not moving, so it pays the same XP as walking onto an empty one.
- **Zone time carries across flags** – the XP timer is on the hero, not the flag, so players are rewarded for moving between objectives rather than camping one.
- **The server decides, the PC only shows** – ownership, progress and rewards are all decided on the server. The client only works out whether to show the bar, which is safe because it changes nothing in the match.
- **Poll the values for the HUD** – the gauges animate every frame anyway, so reading the replicated values while they do is simpler and cannot miss a change.

### Characters & hero data

<figure class="diagram">
  <a href="../../diagrams/framework-hero-data.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/framework-hero-data.svg" alt="Hero data in twelve numbered steps, from registering heroes in the lobby to initialising the spawned hero in the arena. The table below lists the same steps with every function." /></a>
  <figcaption>A hero is data until the arena: the lobby only needs to show it, and only the server ever spawns it.</figcaption>
</figure>

#### What it does

Every hero is a data asset: its name, icon, tooltip card, how it poses on the hero-select screen, and which character Blueprint to spawn. The lobby lists whatever hero assets exist, players pick one (two players can pick the same hero), and anyone who has not picked when the timer runs out gets a random hero. In the arena each player spawns as the hero they picked. Heroes and AI minions share one character base class, so health, abilities, teams, stuns, death and respawn work the same for both.

#### Step by step

The numbers match the diagram. Each arrow is one function calling, or leading to, the next.

| # | Step | Calls, in order | Runs on |
|---|---|---|---|
| 1 | Register heroes | Asset Manager scans the hero folder → [`GetPrimaryAssetId`](code:UPA_CharacterDefinition::GetPrimaryAssetId) on each asset | Every machine, at startup |
| 2 | Load the definitions | Lobby widget [`NativeConstruct`](code:ULobbyWidget::NativeConstruct) → asset manager [`LoadCharacterDefinitions`](code:UCAssetManager::LoadCharacterDefinitions) | Each PC |
| 3 | Show the tiles | Callback [`CharacterDefinitionsLoaded`](code:ULobbyWidget::CharacterDefinitionsLoaded) → [`GetLoadedCharacterDefinitions`](code:UCAssetManager::GetLoadedCharacterDefinitions) → tile view `SetListItems` | Each PC |
| 4 | Preload the assets | [`PreloadHeroAssets`](code:ULobbyWidget::PreloadHeroAssets) → [`GetPreloadAssetPaths`](code:UPA_CharacterDefinition::GetPreloadAssetPaths) for each hero → one `RequestAsyncLoad` | Each PC |
| 5 | Hover a hero | [`HeroEntryHovered`](code:ULobbyWidget::HeroEntryHovered) → [`ShowHeroTooltip`](code:ULobbyWidget::ShowHeroTooltip) → [`LoadToolTip`](code:UPA_CharacterDefinition::LoadToolTip) | Each PC |
| 6 | Click a hero | [`HeroEntryClicked`](code:ULobbyWidget::HeroEntryClicked) → Player State `Server_SetSelectedCharacterDefinition` (a Server RPC) | Sent by the PC |
| 7 | Server records it | [`Server_SetSelectedCharacterDefinition`](code:AChrisPlayerState::Server_SetSelectedCharacterDefinition_Implementation) → Game State [`SetCharacterSelected`](code:AChrisGameState::SetCharacterSelected) → selection array replicates → [`OnRep_PlayerSelectionArray`](code:AChrisGameState::OnRep_PlayerSelectionArray) updates every PC's team slots | Server, then every PC |
| 8 | Start the match | Game State [`StartMatch`](code:AChrisGameState::StartMatch) → [`AssignRandomCharactersToEmptySlots`](code:AChrisGameState::AssignRandomCharactersToEmptySlots) → Game Instance [`StartMatch`](code:UChrisGameInstance::StartMatch) travels to the arena | Server |
| 9 | Keep the pick | Old Player State [`CopyProperties`](code:AChrisPlayerState::CopyProperties) → new Player State | Server |
| 10 | Choose the class | Game Mode [`GetDefaultPawnClassForController`](code:AChrisGameMode::GetDefaultPawnClassForController_Implementation) → Player State [`GetSelectedPawnClass`](code:AChrisPlayerState::GetSelectedPawnClass) → [`LoadCharacterClass`](code:UPA_CharacterDefinition::LoadCharacterClass) | Server |
| 11 | Spawn the hero | [`SpawnDefaultPawnFor`](code:AChrisGameMode::SpawnDefaultPawnFor_Implementation) → [`GetTeamIDForPlayer`](code:AChrisGameMode::GetTeamIDForPlayer) and [`FindNextStartSpotForTeam`](code:AChrisGameMode::FindNextStartSpotForTeam) | Server |
| 12 | Initialise | Controller [`OnPossess`](code:AChrisPlayerController::OnPossess) → hero [`ServerSideInit`](code:AChrisCharacter::ServerSideInit); then on the owning client [`AcknowledgePossession`](code:AChrisPlayerController::AcknowledgePossession) → [`ClientSideInit`](code:AChrisCharacter::ClientSideInit) | Server, then owning client |

#### How it works

**One base class for every character** – [`AChrisCharacter`](code:AChrisCharacter) owns the Ability System Component and attributes, the team ID (through `IGenericTeamAgentInterface`, so anything can ask which side a character is on), stun, death and respawn, and the overhead health bar. [`AChrisPlayerCharacter`](code:AChrisPlayerCharacter) adds the camera and input, and the skeleton minion adds AI. Each hero is a Blueprint child of the player character, with its mesh and abilities set in the editor.

**Heroes as data** – [`UPA_CharacterDefinition`](code:UPA_CharacterDefinition) is a primary data asset. Every field that points at something large is a soft pointer: a path that is only loaded when asked for, so knowing about a hero costs almost nothing. The project's Asset Manager settings register a "Character Definition" type and the folder it lives in, and [`GetPrimaryAssetId`](code:UPA_CharacterDefinition::GetPrimaryAssetId) gives each asset an ID of that type plus its name. The game can then ask for every hero by type, with no hand-kept list to forget to update.

**Building the hero list** – when the lobby widget is created it asks the custom asset manager to load every Character Definition in the background ([`LoadCharacterDefinitions`](code:UCAssetManager::LoadCharacterDefinitions)). When that finishes, [`CharacterDefinitionsLoaded`](code:ULobbyWidget::CharacterDefinitionsLoaded) gets the loaded heroes ([`GetLoadedCharacterDefinitions`](code:UCAssetManager::GetLoadedCharacterDefinitions)) and hands them to the tile view, which makes one tile per hero.

**Preloading so hovering is instant** – straight after, [`PreloadHeroAssets`](code:ULobbyWidget::PreloadHeroAssets) asks every hero for the paths of everything it shows ([`GetPreloadAssetPaths`](code:UPA_CharacterDefinition::GetPreloadAssetPaths), which skips empty fields) and loads them all in one background batch. The widget keeps the handle that batch returns; while it holds it, the assets stay in memory instead of being garbage collected. Hovering and previewing still call `LoadSynchronous` ([`LoadToolTip`](code:UPA_CharacterDefinition::LoadToolTip)), but it now finds the asset already loaded and returns immediately.

**Picking** – clicking a tile ([`HeroEntryClicked`](code:ULobbyWidget::HeroEntryClicked)) is rejected on the spot if the player is locked in or clicks the hero they already have. Otherwise it sends a server RPC ([`Server_SetSelectedCharacterDefinition`](code:AChrisPlayerState::Server_SetSelectedCharacterDefinition_Implementation)), and the Game State records the hero in that player's replicated selection ([`SetCharacterSelected`](code:AChrisGameState::SetCharacterSelected)), so every player's team slots show it. When the hero-select timer runs out, [`AssignRandomCharactersToEmptySlots`](code:AChrisGameState::AssignRandomCharactersToEmptySlots) fills in anyone without a hero.

**Spawning in the arena** – seamless travel creates a new Player State on the arena map, and [`CopyProperties`](code:AChrisPlayerState::CopyProperties) carries the selection across. The arena Game Mode overrides [`GetDefaultPawnClassForController`](code:AChrisGameMode::GetDefaultPawnClassForController_Implementation) to spawn the class from that selection ([`GetSelectedPawnClass`](code:AChrisPlayerState::GetSelectedPawnClass)), with a backup pawn if there is none. The dedicated server never ran the lobby widget, so this is where the hero class is really loaded from disk, during the loading screen when nobody is playing yet. [`SpawnDefaultPawnFor`](code:AChrisGameMode::SpawnDefaultPawnFor_Implementation) then gives the player their team and a start spot. Once possessed, the hero sets up its abilities on the server ([`OnPossess`](code:AChrisPlayerController::OnPossess)) and on the owning client ([`AcknowledgePossession`](code:AChrisPlayerController::AcknowledgePossession)).

#### Why I designed it this way

- **Data assets instead of a class per hero** – a new hero is a data asset and a Blueprint, with no C++ and no list to edit. Designers can add or rebalance heroes without a programmer.
- **Soft pointers everywhere** – hard pointers would load every hero's meshes, grooms and textures the moment the hero list loaded, even on the server and even for heroes nobody picks. Soft pointers let me choose when each cost is paid.
- **Load early, in the background** – the lobby has a natural quiet moment while players pick slots, so that is when the hero assets load. By the time anyone hovers a hero there is nothing left to wait for.
- **The pick is data, the spawn is the server's** – the lobby only stores which definition a player chose. Only the arena server turns it into a character, so a client can never spawn something itself.
- **One base class for heroes and minions** – the Game Mode, flags, combat and AI all deal with `AChrisCharacter` and its team interface, so they treat a minion and a hero the same way unless they choose not to.

## How it connects

- GAS & Combat — characters own the Ability System Component
- Networking — what replicates and who has authority
- Online Backend — GameInstance holds login/session state

## Built to extend

How the framework copes with the changes a team would most likely ask for, and where it would need work first.

#### Easy to add today

- **A new hero** – no framework code changes. Heroes are `PA_CharacterDefinition` data assets that the asset manager finds and loads by type, the hero-select screen lists whatever it finds, and [`GetDefaultPawnClassForController`](code:AChrisGameMode::GetDefaultPawnClassForController_Implementation) spawns whichever one the player picked.
- **New match rules** – round length, shop length, countdown, rounds to win, soul rewards, player count and the loading hold are all `EditDefaultsOnly` properties on [`AChrisGameMode`](code:AChrisGameMode). Designers tune them in `ChrisGameMode_BP` without a recompile, which is exactly how five-minute rounds were set.
- **A new kind of unit on objectives** – a siege unit worth 2, or a hero ability that boosts capture, is one case in [`GetActorCaptureWeight`](code:AFlag::GetActorCaptureWeight); the rest of the flag does not change.
- **More or fewer flags** – the round recounts every flag in the level and works out the majority from the total ([`OnFlagCapturedCallback`](code:AChrisGameMode::OnFlagCapturedCallback)), so a map with five flags needs no code changes, and even numbers are already handled.
- **A new map or game mode** – each map picks its own Game Mode and controller in World Settings. A new mode is a new Game Mode class and Blueprint; nothing else has to know about it.
- **A new menu screen** – a new controller can inherit from [`AMenuPlayerController`](code:AMenuPlayerController) and gets the cursor, focus and widget setup for free; it only names its widget in the Blueprint.
- **A new match phase** – add a value to `EMatchPhase`, a function that starts it, and a timer on the shared phase handle. The phase guards and single "what comes next" timer keep the new phase as safe as the existing ones.

#### Would need work first

- **More than two teams** – two teams are built into the types: `EFlagOwnership` has `TeamOne` and `TeamTwo`, kills are counted in `TeamOneKills` and `TeamTwoKills`, and a slot becomes team 0 or 1. Supporting three teams would mean storing scores in a map keyed by team ID instead of a pair of variables, and the slot rule would divide slots by team size instead of halving them.
- **Team size** – [`GetPlayerCountPerTeam`](code:UChrisNetStatics::GetPlayerCountPerTeam) drives the lobby slots, the session size and the team rule from one place, which is good, but it returns a hard-coded `5`. It should come from config so it can change per mode without a recompile.
- **Bigger teams in the arena** – each player currently claims two start spots (see What I'd do differently), so larger teams need that fixed before they will spawn reliably.

## Challenges & bugs

### Hero tooltips froze the lobby on first hover

- **Symptom** – the first time a player hovered a hero, the lobby hitched before the tooltip card appeared. Picking a hero for the first time did the same before the preview model showed.
- **Cause** – the tooltip and preview use `LoadSynchronous`. The textures and meshes were not in memory yet, so each call read them from disk on the game thread, and the whole game waited for it.
- **Fix** – the lobby now preloads every hero's display assets in one background batch as soon as the hero list arrives, and keeps the handle so they stay loaded ([commit](https://github.com/Polindian/AnimationTesting/commit/3346368)). The `LoadSynchronous` calls did not change: they now find everything already loaded and return immediately.
- **Lesson** – `LoadSynchronous` is only slow when the asset is not loaded yet. Soft pointers decide when you pay for loading, so pay early and in the background, at a moment the player is busy with something else.

**Symptom → cause → fix → lesson** – TODO: Lobby animations froze because LobbyGameMode inherited from AGameMode instead of AGameModeBase (the world stayed in WaitingToStart).

## Optimisations

### The hero list was rebuilt once per hero

`CharacterDefinitionsLoaded` used to call `SetListItems` inside the loop over heroes, so the tile view replaced and refreshed its whole list once for each hero instead of once in total. Moving the call out of the loop sets the list once, however many heroes the roster grows to.

TODO: more before/after, with numbers where possible.

## What I'd do differently

### Match phase lives in the Game Mode, not the Game State

The current match phase is stored in [`AChrisGameMode`](code:AChrisGameMode), which only exists on the server. Every phase change, and every second of the countdown ([`CountdownTick`](code:AChrisGameMode::CountdownTick)), is pushed to each player with a `Client_` RPC on their Player Controller.

That works, but RPCs are one-off messages: a player who reconnects mid-round never learns which phase the match is in. It also sends a message every second to every player.

**The fix** – replicate the phase and the time it ends (`PhaseEndServerTime`) on `AChrisGameState`. Each client works out the remaining time locally from the server clock, so there is one update per phase instead of one per second, and late joiners see the right state immediately.
