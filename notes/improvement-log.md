# Improvement log

Changes found while studying the Champions Arena code. Each one becomes a refactor branch off `develop` and a "What I'd do differently" / "Optimisations" entry on the site.

## Open to-dos (keep this list current)

**Editor checks still to do (combat & GAS page):**
- 14: switch the hero generic data asset's Death Effect to the Infinite one, then test that respawn takes death montage − 0.8 s + 8 s (see "Two death effects").
- 15: `RespawnDelay` (8) and `DeathMontageFinishTimeShift` (−0.8) are on the hero Blueprint's Class Defaults → Death category (they're `EditDefaultsOnly` on `AChrisCharacter`); confirm nothing overrides them.
- Test the fall-back kill bug: smash an enemy hero, then kill them while they're knocked down. Do you get XP, souls and the kill? (see "Killing a knocked-down hero")
- Send the Blood Serum screenshot (it didn't attach) and the potion shared cooldown.
- 16: potions share the 10 s cooldown.
- 17: in-game test: get stunned while aiming Shoot and mid-combo (does the aim stick?).
- 18: roll capsule height.
- Burn total: watch Health to confirm 40 or 44 per burn.
- Server bone test (see the "server bone updates" entry below), then fix.

**Code changes (Christopher writes them, branch off `develop`):**
- `IncomingDamage` meta attribute rewrite, with Armour applied once on the target (fixes the killing-blow bug, heavies and skeletons ignoring Armour). Good PR story.
- Additive bonus bucket; Blood Serum `!bIsDot`; MMC merge (one light MMC, Double Down on tagged combo hits); GA_Combo merged into Stab; Mode A dead code removed; Thrust onto `PushTarget`; `stats.stun` on Thrust; renames (Scorched effects, `StabDamageEffect`, `RightStabMontage`); projectiles stop on walls; skip dead allies in reward sharing; Fleetfoot balance; mesh tick option.
- Planned feature: combo-hit stun (0.5–0.75 s) and small push (e.g. 400, 0, 100) after checking `GAP_Launched`.

**Learning and website:**
- Combined mock: gameplay framework + combat & GAS (score 0–10 each, review at the end).
- Concise comments for the hard parts of each feature (file, function, line), added on a branch off `develop`.
- Remaining tabs, each with a ~10-question quiz: Networking, AI, UI, Audio, Online backend. Then a final mixed mock.
- After the code changes: update "What I'd do differently" entries that become "Challenges & bugs" stories, and add profiling numbers to Optimisations.

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

## 7. Make StartMatch run once

- **System:** Gameplay Framework (lobby)
- **Found:** 2026-10-29
- **Status:** Planned (do together with improvement 2, when lobby rules move to `ALobbyGameMode`)

**Now:** `AChrisGameState::StartMatch` is called from two routes: the last `RequestPlayerLockIn`, and the hero-selection timer reaching zero (which force-locks everyone). Nothing records that the match has already started.

**Problem:** If the timer starts the match and a lock-in request already in flight arrives just after, `CanStartMatch()` is still true, so `StartMatch` runs again and calls `ServerTravel` a second time mid-travel.

**Plan:** Add a `bMatchStarting` flag set on the first call; return early on any later call, and ignore lock-in requests once it is set. Same pattern as `bLoadingHoldFinished`.

**Benefit:** Travel to the arena is triggered exactly once, whatever order requests arrive in.

## 8. Banner state as an enum, chosen by team

- **System:** Flag capture
- **Found:** 2026-11-03
- **Status:** Planned

**Now:** `AFlag::BannerState` is a replicated number: 0 hidden, 1 neutral, 2 team one, 3 team two. `PlayBannerSlam` decides which by comparing the colour it was given against `TeamOneBannerColor` / `TeamTwoBannerColor`.

**Problem:** Magic numbers are hard to read and easy to get wrong, and matching on colour breaks if a team's colour is changed in the Blueprint.

**Plan:** Replace the number with `enum class EBannerState : uint8 { Hidden, Neutral, TeamOne, TeamTwo }`. Pass the team (or `EFlagOwnership`) into the banner functions and look the colour up from it.

**Benefit:** Readable, compiler-checked states; colours can change freely; a step towards supporting more than two teams.

## Noted for later

- **Countdown input lock is client-side only:** `Client_OnCountdownStart` calls `DisableInput` on the client. The server should also refuse actions during the countdown. (Networking page)
- **RPC validation accepts everything:** every `_Validate` in `ALobbyPlayerController` returns `true`. Reject impossible values (e.g. slot ID beyond the max, null hero on select) so tampered clients are kicked; keep normal rule checks (slot occupied) in `_Implementation`. (Networking page)
- **Stale entries in `LoadedPlayers`:** if a player who already reported loaded leaves during the hold, their entry still counts in `LoadedPlayers.Num()`, so the hold could finish while someone else is still loading. Count only valid entries. (Match loop)
- **Two definitions of a kill:** the round tiebreak (`ReportKill`) counts hero kills on anything, minions included; the leaderboard (`AddHeroKill`) counts heroes killing heroes only. Confirm this is intended and document it. (Rounds & scoring)
- **No feedback when teams are uneven:** if everyone readies up with unequal teams, `CanStartHeroSelection` just returns false and nothing happens. Show a message such as "Teams must be even to start" to every player. (UI page)
- **Unused flag delegate:** `AFlag::OnTeamInfluenceUpdated` is broadcast (only when rates change) but nothing binds to it; the gauges and AI read the replicated values directly. Remove it: the gauges animate every frame anyway, so polling the replicated values is the right fit. (Flag capture)
- **Zone edge mismatch:** the server counts a hero as soon as their capsule overlaps the sphere, but `UFlagProgressWidget::FindLocalPlayerFlag` only shows the bar when the character's centre is inside the radius, so at the very edge you can be capturing with no bar. Add the capsule radius to the widget's check. (Flag capture)
- **Random heroes on a dedicated server may only pick from heroes someone chose:** `AssignRandomCharactersToEmptySlots` uses `GetLoadedCharacterDefinitions`, which only returns definitions already in memory. The server never runs the lobby widget, so it may only have the heroes players picked loaded (and none if nobody picked). Confirm with a UE_LOG of `AllDefinitions.Num()` on the packaged server; fix by calling `LoadCharacterDefinitions` on the server when the lobby starts. (Characters & hero data)
- **Unused hero-pick RPC:** `ALobbyPlayerController::Server_RequestCharacterSelected` is never called; the lobby uses `AChrisPlayerState::Server_SetSelectedCharacterDefinition`. Remove one so there is a single route, ideally through the controller like the other lobby requests. (Characters & hero data)
- **Two copies of the pick can drift:** `Server_SetSelectedCharacterDefinition` writes the Player State's own copy before the Game State checks lock-in, so a pick that arrives after a forced lock-in changes the Player State (which decides the spawn) but not the Game State (which the lobby shows). Let the Game State decide and have the Player State copy only from it. (Characters & hero data)
- **Redundant deselect before select:** `AChrisPlayerState::Server_SetSelectedCharacterDefinition` calls `SetCharacterDeselected` and then `SetCharacterSelected`, but selecting already overwrites the row, so the first call only fires an extra `OnPlayerSelectionUpdated`. It is the only caller of `SetCharacterDeselected`. Remove the call (keep the function only if a "clear pick" action is added). (Characters & hero data)
- **`EndRound` has no guard of its own:** it sets `RoundEnd` without checking the phase first, so it relies on every caller (the timer, `OnFlagCapturedCallback`) to protect it. Add `if (CurrentPhase != EMatchPhase::InRound) return;` at the top, like the other phase functions. (Match loop)
- **Ready-up lock is client-side only:** `ULobbyWidget::SlotSelected` refuses to switch slots while `bIsReady`, but `AChrisGameState::RequestPlayerSelectionChange` only checks authority and whether the slot is taken. A modified client could switch while readied up. Check the player's ready state on the server too. (Rounds, teams & scoring / Networking page)
- **Base stats fall back to the last table row:** `UChrisAbilitySystemComponent::InitializeBaseAttributes` reuses `BaseStats` inside the loop, so if no row matches the character's class, `BaseStats` is still the last row checked and that row's stats are applied. Set it back to `nullptr` when a row doesn't match (or keep the match in a separate variable), and log a warning. (GAS foundations)
- **Upgrade points don't match the design:** `ExperienceUpdated` gives one point per level gained (`NewLevel - CurrentLevel`), but the tutorial and design say reaching level N gives N points. With one per level, levels 1 to 10 give 9 points in total, which isn't enough to fully upgrade even one heavy ability (1 + 2 + 3 + 4 = 10). Fix: add every level number passed (e.g. loop from `CurrentLevel + 1` to `NewLevel` and add each). With the fix, levels 2 to 10 give 54 points, and all four heavy abilities (40 points) can be maxed by level 9. (Attributes, XP & levelling)
- **Two paths reset the swords:** `ServerResetToUnequipped` (replicated `ResetCount`) already resets every client, and `AChrisPlayerController::Client_OnReturnToArena` also calls `ResetToUnequipped` on the owning client. Harmless, but one job has two routes; keep the replicated one. (Weapon equip)
- **Skill tier order is only enforced in the widget:** `UShopWidget::UpdateSkillLockStates` greys out tier 2 until tier 1 is owned, but `UInventoryComponent::Server_Purchase` has no tree-order check, so a modified client could buy tier 3 first. Add the prerequisite to the item asset (or a tier index) and check it on the server. (Shop)
- **No reason on a failed purchase:** every failure plays one reject sound; `Client_PurchaseFailed` could carry a reason enum so the shop can show "not enough souls" or "shop closed". (Shop / UI)
- **Potion rules (design decided):** after ANY consumable is used (all five, including Elixir of Life and Nightflare), no consumable can be used for 10 seconds, and none while another potion's buff is still active. Today `UInventoryItem::IsOnCooldown` is per item and returns 0 for items without a granted ability, so neither rule exists. Plan: `GE_ConsumableCooldown` (10 s, grants `Cooldown.Consumable`) applied after every use; every potion's `ConsumedEffect` grants `Consumable.Active` while it lasts; `Server_ActivateItem` refuses if the hero has either tag; the HUD reads the cooldown effect's remaining time. Reason: stops players chaining different potions to become near-invincible. (Inventory)
- **A failed ability activation still consumes the item:** `Server_ActivateItem` calls `TryActivateGrantedAbility` and then `ConsumeItem` regardless of the result, so a Nightflare thrown while stunned is lost. Only consume when the ability activated (or when there is no ability). (Inventory)
- **The skill-tree layout is written out three times:** `UShopWidget::UpdateSkillLockStates`, `FindSkillIndices` and `RestoreShopState` each build the same `TArray<TArray<UItemWidget*>> Categories`. Build it once (a member filled in `NativeConstruct`) so adding or moving a skill only changes one place. (Skill trees)
- **`OnSkillPurchased` is bound twice:** `UShopWidget::NativeConstruct` calls `OnSkillPurchased.AddUObject(this, &UShopWidget::OnSkillPurchasedCallback)` on two identical lines, so every skill purchase runs the callback twice: two branch-fill animations on the same branch, two lock refreshes and two shimmers. Delete one line. (Skill trees)
- **Server tree-order check (design):** add `TObjectPtr<const UPA_ShopItem> RequiredItem` to `UPA_ShopItem` (tier 2 points at tier 1, set in the editor), and in `Server_Purchase` refuse when `RequiredItem` is set and not in `PurchasedItems`. The widget's `Categories` array can't be used because widgets don't exist on a dedicated server. (Skill trees)
- **Merge GA_Combo into Stab:** `UGA_Combo` hard-codes its buttons (`HandleComboCommitLeftSlashEvent` / `HandleComboCommitRightSlashEvent` plus `bStartsWithRightHand`), while `UStabAbility` does the same job from data (`ComboInputMap`, `ComboDamageMap`). Move the dual slash onto Stab Blueprints (one per starting hand) and delete GA_Combo. Remember GA_Combo's constructor adds the basic-attack ability tag and blocks other basic attacks; set those on the new Blueprints or the slash could overlap other attacks. (Melee combos)
- **GA_Combo doesn't clear `NextComboName` on activation:** `UStabAbility::ActivateAbility` sets `NextComboName = NAME_None`, but `UGA_Combo::ActivateAbility` doesn't, so a combo interrupted while the window was open could carry the old section name into the next swing. Add the reset (goes away anyway if GA_Combo is merged into Stab). (Melee combos)
- **Rename `RightStabMontage`:** `UStabAbility` now plays every kind of attack, so call it something like `AttackMontage`. Add a property redirect in `DefaultEngine.ini` (`+PropertyRedirects=(OldName="StabAbility.RightStabMontage",NewName="StabAbility.AttackMontage")`) so the montages already set in the Blueprints aren't wiped. (Melee combos)
- **Empty `Swipe` class:** `Swipe.cpp` / `Swipe.h` contain nothing. Delete them. (Melee combos)
- **Debug log in `HandleComboCommit`:** the `UE_LOG` at the top runs on every combo button press and repeats the map lookups. Remove it or put it behind a verbose log category. (Melee combos)
- **Editor check: server bone updates for hit detection:** `AN_SendTargetGroup` reads `GetSocketLocation` on the server, but a dedicated server renders nothing, so with the wrong setting it may not refresh bone positions and the sweep would use stale sword positions. Checked 2026-11-25: hero and skeleton Blueprints use **Always Tick Pose** (the `ACharacter` default). That ticks the animation, so notifies still fire, but it only refreshes bone positions when the mesh is rendered, and a dedicated server never renders. So the server's sockets are probably stale (the reference pose, moved along with the actor), and sweeps start from the wrong sword position.
  - **Test first:** in `AN_SendTargetGroup`, log `GetSocketLocation` on the server and on the attacking client for the same swing (or draw a debug sphere on each). If the server's position doesn't follow the swing, it's confirmed.
  - **Fix:** set the mesh to **Always Tick Pose and Refresh Bones** on the hero and skeleton Blueprints (or in the constructors). Other server-side socket users benefit too: Thrust's detection actor attached to `target_ThrustCneter`, and the projectile spawn socket.
  - **Cost and optimisation:** the server now computes bone positions every frame for every character. Fine for an arena this size; if profiling shows it, switch to refreshing bones only while an attack is playing, or use Animation Update Rate Optimisation.
  - If confirmed, it's a strong Challenges / Optimisations story for the site. (Melee hit detection / Networking)
- **One-frame sweeps can miss fast swings:** each `AN_SendTargetGroup` checks the blade's position on a single frame only, so an enemy the blade passed through between frames isn't counted. Upgrade: an anim notify state that sweeps every tick from last tick's socket positions to this tick's, keeping one hit list for the whole window. (Melee hit detection)
- **Light attacks do a wasted sweep:** `UStabAbility::HandleComboDamageEvent` calls `GetHitResultFromSweepLocationTargetData` (one extra sphere sweep per hit) before checking the mode, but only Mode A (smash/stun) uses the results; Mode B (light attacks) throws them away. Move the call inside the `bUseAoESweepResults` branch. (Melee / Optimisations)
- **To verify (area section): Mode A airborne check looks reversed:** the comment says "Skip airborne targets", and `StartCombo` skips targets that are falling, but Mode A in `HandleComboDamageEvent` does `if (TargetCharacter && !IsFalling()) continue;`, which skips grounded targets and only damages airborne ones. Design confirmed: smash and stun should ignore airborne players so they can be dodged by jumping, so if Mode A runs for any smash/stun hit, flip it to `if (TargetCharacter && TargetCharacter->GetCharacterMovement()->IsFalling()) continue;`. Test a smash combo's later hits on a grounded enemy. (Ranged & area)
- **Zero push still fires a launch (confirmed in the editor: the right stab's combo02 push is 0, 0, 0):** in `UStabAbility::HandleComboDamageEvent` (Mode A and Mode B), `PushTarget` is called on every hit even when the section's `PushVelocity` is zero, so the target's `UGAP_Launched` activates (commits, then `LaunchCharacter` with zero velocity) for nothing; if that ability has a cooldown, a real knockback straight after could be blocked. Add the same `IsNearlyZero()` check `StartCombo` uses. Check the `ComboDamageMap` push values on the light attacks. (Melee / Knockback)
- **Projectiles fly through walls:** `AProjectileActor`'s collision sphere ignores every channel except Pawn, so the `SetActorLocation` sweep never stops on geometry. Block `ECC_WorldStatic` (and `WorldDynamic` if needed), and on a blocking hit spawn the impact VFX and destroy the projectile with no damage. (Ranged & area)
- **Delete `UBlindBombExecution`:** Nightflare uses its `GrantedAbility` (`UGA_BlindBomb`), so the execution calculation is a leftover copy of the same overlap logic, with a hard-coded asset path. (Ranged & area)
- **Planned feature: blind affects AI too:** confirmed 2026-11-25 that `GE_Nightflare_Blind` (3 s, one stack, refreshes) has no components, so it grants no tag and is cues only (`GameplayCue.blinded`, `.sound.blinded`, `.vfx.blinded`). Give it a granted tag (e.g. `stats.blinded`), and have the skeletons' behaviour tree or perception drop their target while they have it, so Nightflare works against AI as well as players. (Ranged & area / AI)
- **Projectile lingers on clients after hitting:** clients run `NotifyActorBeginOverlap` too and play the impact VFX, but `Destroy()` does nothing on a client for a server-spawned replicated actor, so the projectile keeps flying until the server's destroy arrives. Call `SetActorHiddenInGame(true)` (and disable collision) locally on overlap so the hit looks instant. (Ranged & area)
- **Unused projectile code:** in `AProjectileActor`, the `HitResult` built in `NotifyActorBeginOverlap` is never used, `SendLocalGameplayCue` is never called, and `Target` is stored but never read. Remove them or use the cue for impact sparks. (Ranged & area)
- **`ATargetActor_Around::GetLifetimeReplicatedProps` doesn't call `Super`:** the actor's own replicated properties (owner, attachment, movement) aren't registered, and `TargetDetectionRadius` has an `OnRep` but is never registered either. It works today only because every machine configures its own sphere. Call `Super::GetLifetimeReplicatedProps` and register the radius, or delete the unused `OnRep`. (Ranged & area)
- **Thrust pushes differently from melee:** `UThrust::TargetReceived` calls `LaunchCharacter` directly, while melee sends `PushTarget` (the target's launched ability). Use one path so knockback rules (and any future hit reactions or stagger) apply to every attack. (Ranged & area / Knockback)
- **Mode A in `UStabAbility::HandleComboDamageEvent` is probably dead code:** smash and stun only send `ability.stab.right` (they can't be comboed), so they never reach `HandleComboDamageEvent`, and light attacks always take Mode B. Confirm in the smash/stun montages, then delete Mode A, `bUseAoESweepResults` and the radius lookup there. That also removes the reversed airborne check and the wasted sweep logged earlier. (Ranged & area)
- **Commented-out impact cue in `UStabAbility::StartCombo`:** the `ImpactCueTag` block is commented out, so the `ImpactCueTag` setting does nothing. Bring it back or delete both. (Ranged & area)
- **Rename `StabDamageEffect`:** `UStabAbility` runs light attacks, heavy attacks, smash and stun, so the name no longer fits. It's the damage effect for the first hit, so `InitialHitDamageEffect` pairs with the existing `InitialHitPushVelocity`. Add a property redirect in `DefaultEngine.ini`, same as the `RightStabMontage` rename, so the Blueprints keep their values. (Melee / Ranged & area)
- **Bug: reductions can't save you from a killing blow, but leave you alive-looking:** damage effects modify `Health` directly, so GAS applies the base damage first and `UChrisAbilitySystemComponent::HealthUpdated` fires straight away. If that takes Health to 0, the death effect and the dead event go out before `PostGameplayEffectExecute` runs the stage-2 reductions, which then heal some Health back onto a hero who is already dying. The damage credit is also wrong on overkill, because `HealthBeforeEffect` is worked out after the clamp. Fix with a meta attribute: add an unreplicated `IncomingDamage` attribute, point every damage effect at it instead of `Health`, and in `PostGameplayEffectExecute` read it, apply every bonus and reduction to that one number, then `SetHealth` once and clamp. Health changes once, so death is decided on the final value. (Damage pipeline / Death)
- **Armour doesn't reduce heavy damage:** `MMC_HeavyAttackBuffDamage` only returns `1 + HeavyAttackBuffDamage`, and the damage comes from the curve value in the effect's Coefficient, so smash, stun, thrust and shoot ignore the target's Armour. Capture the target's `Armour` in the heavy MMC and return `(1 + bonus) * (1 - Armour / (Armour + 100))`. (Damage pipeline)
- **Double Down isn't tied to combos:** its roll lives in `MMC_BaseAttackDamage`, so it applies to whichever effects use that MMC, and never to effects using `MMC_LightAttackBuffDamage`. The skill says "combos". Tag only the follow-up combo hit effects, the `ComboDamageMap` effects reached after the combo flash (not the first hit's `StabDamageEffect`), with e.g. `damage.type.combo`, and roll Double Down in `PostGameplayEffectExecute` when the effect has that tag, the same way Bonebreaker and Deadeye check theirs. (Damage pipeline)
- **Two near-identical damage MMCs (confirmed in the editor: first hits use the light MMC with a Coefficient, e.g. 1.2 on the right stab; follow-up combo hits use the base MMC, so Bladed Edge never reaches a combo hit):** `MMC_BaseAttackDamage` and `MMC_LightAttackBuffDamage` share the same captures and formula; base only adds the Double Down roll. Once Double Down moves to stage 2, delete the base MMC and point every light damage effect at the light MMC. Check first whether the skeletons' attack effects use the base MMC; if they do, point them at the light MMC too. (Damage pipeline)
- **Reminder: hero tooltip typo:** Christopher put a typo in one of the hero tooltips on purpose. Remind him to fix it during the improvements batch. (Characters & hero data)
- **Blood Serum boosts burn ticks:** step 2.5 in `UChrisAttributeSet::PostGameplayEffectExecute` (Consumable Damage Bonus) has no `!bIsDot` check, so a hero with Blood Serum active makes their Scorched burn ticks hit 20% harder. Add `&& !bIsDot` like Loaded Dice, Stealth Strike and Deadeye. (Damage pipeline)
- **Decide how stage-2 bonuses stack:** bonuses in `PostGameplayEffectExecute` multiply (each is a percentage of the damage including earlier bonuses), so they compound: Loaded Dice × Stealth Strike × Blood Serum × Deadeye = ×6.55 on a third shot. Reductions also multiply, which keeps them below 100%. **Decided: add the bonuses in one bucket.** Collect every stage-2 bonus into one `TotalBonus` (Loaded Dice +0.3, Stealth Strike +0.4, Blood Serum +0.2, Bonebreaker +0.5, Deadeye +2.0) and apply `Damage *= (1 + TotalBonus)` once; reductions keep multiplying so they never reach 100%. The MMC-stage bonuses (Bladed Edge, Juggernaut, Double Down) stay a separate bucket. Worst case drops from ×6.55 to ×3.9. Do it during the `IncomingDamage` rewrite. Still to consider after playtesting: Deadeye ×3 → ×2, and a per-hit cap (e.g. 40% of max Health) as a no-one-shot safety net. (Damage pipeline / balance)
- **Balance: buff the Gambler skills:** on average Double Down (20% chance of +30% on combo hits ≈ +6%) and Loaded Dice (every 4th hit, 30% chance of +30% ≈ +2%) fall well behind Bladed Edge's guaranteed +10%. Planned: Double Down to a 50% chance (≈ +15% on follow-up combo hits, about +10% across light hits), and Loaded Dice to a 60% chance with a +50% bonus on the 4th hit (≈ +7.5% per hit, on every hit type). Change the chance in Double Down's effect (`DoubleDownChance`) and the `0.3f` chance and `0.3f` bonus in the Loaded Dice block (both move into the additive bonus bucket). (Skill trees / balance)
- **Planned feature: Loaded Dice and Deadeye counters on the HUD:** `LoadedDiceHitCounter` and `DeadeyeHitCounter` already replicate, so the HUD only needs a small widget bound with `GetGameplayAttributeValueChangeDelegate` on the local ASC: 4 pips for Loaded Dice (3rd pip glows, flash on a proc), shown only when `LoadedDiceActive > 0`, and a 1/3 to 3/3 tracker for Deadeye. Lets players plan the 4th hit onto a smash or a third shot. Both counters could switch to `COND_OwnerOnly`, since only the owner needs them. (Skill trees / UI)
- **Dead allies can share kill rewards:** `UGAP_Dead::GetFriendlyAlliesNearKiller` keeps any friendly hero inside `AllyShareRadius`, with no check for the dead tag, so a teammate lying dead near the killer still takes a share of the souls and XP (and shrinks everyone else's). Skip allies with `GetDeadStatsTag()`. (Death & rewards)
- **`PushTarget` carries the velocity in `ImpactNormal`:** it builds a fake hit result and stores the push velocity in `ImpactNormal`, which `UGAP_Launched` reads back. It works, but the field means something else. A small custom target data struct (or the event's own payload) would say what it is. (Knockback)
- **Ragdoll is never switched on:** `AChrisCharacter::SetRagdollEnabled(true)` is never called (death uses the montage and the dissolve), so only the "off" half runs, on respawn. Delete the ragdoll path or use it. (Death)
- **To test: getting stunned mid-ability:** nothing cancels a running ability when the stun tag lands (`ActivationBlockedTags` only stops new ones starting). Abilities that play their montage through `PlayMontageAndWait` end when the stun montage interrupts it (if they share a slot), but `GA_Shoot` plays its aim montage with `PlayAnimMontage` and has no task waiting on it, and input is off while stunned, so letting go of aim during a stun may never arrive: the hero could come out of the stun still aiming. Test it; if so, cancel abilities in `StunTagUpdated` / `FallBackTagUpdated` on the server (excluding the passives), or give the stun effect a "cancel abilities with tags" setting. (Stun)
- **Thrust can be activated while stunned:** the Thrust Blueprint's Activation Blocked Tags list only `stats.attacking`; the Blueprint's list replaced the C++ default that adds `stats.stun`. The right stab Blueprint lists `stats.stun` explicitly. Input is off while stunned, so players can't press it, but add `stats.stun` to Thrust. The other heavy attacks already list it. (Ranged & area / Stun)
- **Thrust's attach socket name is misspelled in both places:** `target_ThrustCneter` on the Blueprint and the skeleton, so it works. Optional: rename both together. (Ranged & area)
- **Scorched's effects are named the wrong way round:** `GE_Scorched_Equipped` is the burn itself (Has Duration, −4 Health, `GameplayCue.vfx.burning`, stacks once per target and refreshes), while `GE_ScorchedActive` is the shop's infinite flag (`ScorchedActive` = 1). Rename the burn to something like `GE_Scorched_Burn`. Confirmed: Period 0.5 s, Duration 5 s, so 10 ticks of 4 = 40, or 44 if "Execute Periodic Effect On Application" is ticked (an extra tick the moment it lands). Check the total with a log or by watching Health. Ticks skip Armour but Bulwark and the other reductions reduce each one. Confirmed: its asset tags include `damage.type.dot`, so the bonus exclusions work (except Blood Serum, logged above). (Ranged & area / Damage pipeline)
- **Editor values found:** right stab move speed 100, sweep radius 35; Thrust detection radius 100 (C++ default 150), push speed 5000, cost and cooldown effects set; smash damage −85 at level 1 (`CT_Smash`), Thrust −50 (`CT_Thrust`); smash and Thrust damage effects apply fall-back effects; the right stab's first hit applies a 0.5 s stun (`GE_StabStun`); Bulwark = `DamageReduction` +0.1 (10% off every hit, any source); Fleetfoot = `MoveSpeed` Multiply (Additive) 1.05 (+5%); Iron Clad = `MaxHealth` +100 (Add Base), and `RescaleHealth` keeps the health percentage. All three Infinite. (Reference)
- **Fleetfoot may be too small to feel:** +5% move speed is hard for players to notice (most notice around 10%). Playtest and consider 1.08–1.10. (Balance)
- **Armour does nothing against skeletons:** the skeleton's combo damage effect (`GE_ComboDamage_Skeleton`) is a fixed −8 Scalable Float, with no MMC, so a hero's Armour (and the skeleton's own Attack Damage) never affect it. It also means no damage effect uses `MMC_BaseAttackDamage` except the light combo hits, so the MMC merge is safe. Decided: Armour should reduce every hit, not just heroes'. (Bulwark and the other reductions already apply to skeletons, since step 3 of `PostGameplayEffectExecute` has no source check.)
  - **Quick fix (small C++):** a tiny MMC, e.g. `MMC_ArmourOnly`, that captures only the target's Armour and returns `1 − Armour / (Armour + 100)`. In `GE_ComboDamage_Skeleton`, switch to Custom Calculation Class with Coefficient −8, so the final value is −8 × the armour multiplier. Works for any future fixed-damage source (traps, hazards) without giving skeletons an AttackDamage attribute.
  - **Proper fix (with the IncomingDamage rewrite):** apply Armour once, on the target's side, in `PostGameplayEffectExecute` for every incoming hit, and take it out of the MMCs. Then every damage source gets Armour automatically, which also fixes heavies ignoring Armour. Decide whether burn ticks skip it (they can check `damage.type.dot`).
  (Damage pipeline / AI)
- **Planned feature: reward landing a combo:** give the follow-up combo hits a short stun and a small push, so the attacker gets an opening. Editor only: add a stun effect under the combo damage effects' Additional Effects (like `GE_StabStun` on first hits) and set each `ComboDamageMap` entry's `PushVelocity`. Guard against stun-lock: start around 0.5–0.75 s rather than 1 s, and consider a short stun-immunity window after a stun ends, since teammates can chain stuns. Push values are local to the attacker (X forward, Y right, Z up) and are a launch velocity, so 30 barely moves anyone; try something like (400, 0, 100). Checked: `UGAP_Launched` is a plain C++ passive with no cooldown or cost, and it doesn't block on stun, so combo pushes will always go through. If chains get silly, adding a short cooldown to it is the one-place fix. (Melee / Balance)
- **Smash camera shake starts from the world origin:** in the smash impact anim notify Blueprint, `Play World Camera Shake`'s Epicenter pin isn't connected, so it's (0, 0, 0). Players are shaken by how close they are to the middle of the map, not to the smash. Fix: wire the `target_JumpSmashEnd` socket location (already used for the VFX) into Epicenter. Check the stun notify too. (Ranged & area / VFX)
- **Smash VFX scaling could live in Niagara:** the notify sets nine Niagara variables, each with its own multiplier (2.5, 100, 125, 75, 7, 5…). Optional: pass one `Scale` user parameter and do the multipliers inside the Niagara system, so the artist side owns the ratios and the Blueprint shrinks to one call. The 260 fallback radius is also hard-coded here; read it from the same base value as the curve. (VFX / Optimisation)
- **Editor values found (2):** `GE_StunRadius` is Instant, Override `StunSweepRadius` from `CT_SkillStun` → Radius (320 at level 1); the smash notify falls back to 260 if the attribute isn't found. (Reference)
- **Two death effects:** there's an Infinite death effect and a 10 s Has Duration one, both granting `stats.dead`. Respawn is driven by a timer (`DeathMontageFinished` → `RespawnDelay`, 8 s by default → `RespawnImmediately` removes the effect), so death must be Infinite. The 10 s one looks like a leftover from the course's design, where the effect's duration *was* the respawn timer. If it's still assigned anywhere, that character has two respawn triggers racing each other (the effect expiring, and the timer). Checked 2026-11-25: the **hero** data asset (`PA_GenericHeroAbilitySystem`) uses the 10 s `GE_Death`, and the skeleton one uses the Infinite one. So for heroes the two triggers really do race: the timer fires at death montage − 0.8 s + 8 s, the effect expires at 10 s, and whichever comes first respawns the hero. Deaths look fine because both paths end in the same `Respawn`. But `RespawnDelay` can only make respawns *shorter* than 10 s, never longer, and `CancelDeathTimers` can't stop the effect expiring. Fix: put the Infinite death effect on the hero data asset too, test, then delete the 10 s one if nothing else references it. (Death & respawn)
- **Editor values found (3):** stun effect `StunDuration` from `CT_SkillStun` (4 s at level 1), Grant Tags, no stacking (two stuns overlap rather than refresh); stun ability: Attack Move Speed 250, no push, `GE_VFX_stun` for the VFX, blocked by `stats.attacking` and `stats.stun`; fall back effects grant `stats.fallback`, fixed 3.5 s (smash) and 3 s (Thrust), not levelled; smash push (800, 0, 300). (Reference)
- **Killing a knocked-down hero gives no rewards (bug, found in code 2026-11-25):** `UChrisGameplayAbility`'s constructor blocks every ability on `stats.stun` **and** `stats.fallback`. `UGAP_Dead` removes only the stun tag (`ActivationBlockedTags.RemoveTag(GetStunStatsTag())`), and its Blueprint shows `stats.fallback` still blocking. So if a hero dies while knocked down by smash or Thrust, the reward ability can't activate: the killer gets no XP or souls, and `AddDeath` / `AddHeroKill` never run, so the scoreboard's K/D is wrong too. Being finished off while on the ground is a very common way to die. Test it, then fix with one line in the constructor: `ActivationBlockedTags.RemoveTag(UChrisAbilitySystemStatics::GetFallBackStatsTag());` (and clear it from the Blueprint). Good Challenges story: "a reward ability inherited a block from its parent class". (Death & rewards)
- **Launch is blocked during fall back:** `UGAP_Launched` also only removes the stun tag, so a hero who's already knocked down can't be launched again. Probably good (no juggling a downed player), but make it a deliberate decision and note it. (Knockback)
- **Unused reward settings:** `ExperienceRewardPerExperience` (0.05) and `SoulRewardPerExperience` (20) on `UGAP_Dead` aren't read anywhere; they're from the course, where rewards scaled with the victim's experience. Delete them, or use them for a catch-up rule (killing a higher-level hero pays more). (Death & rewards)
- **Expected Player Count is 1 for real matches:** in the Game Mode Blueprint it's 1, and in C++ it's only set in `InitGame` for practice. `PostLogin` starts the match when the player count reaches it, and the Continue vote passes at it, so a real match starts as soon as the first player loads in and one vote continues. Check whether the server gets the real count from the lobby; if not, pass it as a URL option (like `practice`) or read it from the session. (Gameplay framework / Online backend)
- **Editor values found (4):** `GAP_Dead_BP`: skeleton kill 100 XP / 5 souls, hero kill 300 XP / 30 souls, ally share radius 400, `GE_KillReward`. Game Mode: best of 3 (Rounds to Win 2), round 300 s, shop 60 s, countdown 10 s, round end wait 12 s, death cleanup delay 2 s; winner 50 souls, loser 100 (a deliberate catch-up rule?). (Reference)
