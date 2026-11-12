---
title: "GAS & Combat"
summary: "Combat built on Unreal's Gameplay Ability System, and the systems that shape every hit: weapon equip, a shop with skill trees, ability levelling and consumables."
order: 2
tags: ["GAS", "Gameplay Effects", "Attributes", "Anim Notifies", "Gameplay Tags"]
glance:
  - "TODO: e.g. Every action is a Gameplay Ability, so it gets prediction and replication for free"
  - "TODO: e.g. Animation notifies open hit windows; socket traces find targets"
  - "TODO: e.g. Damage is data-driven via Modifier Magnitude Calculations"
keyFiles:
  - { path: "GAS/ChrisGameplayAbility.cpp", note: "Base ability class" }
  - { path: "GAS/ChrisAbilitySystemComponent.cpp", note: "Custom ASC" }
  - { path: "GAS/ChrisAttributeSet.cpp", note: "Core attributes" }
  - { path: "GAS/GA_Combo.cpp", note: "Melee combo ability" }
  - { path: "GAS/GA_Shoot.cpp", note: "Ranged ability" }
  - { path: "GAS/MMC_BaseAttackDamage.cpp", note: "Damage calculation" }
  - { path: "Animations/AN_SendTargetGroup.cpp", note: "Hit window \u2192 targets" }
  - { path: "Inventory/InventoryComponent.cpp", note: "Shop items & consumables" }
status: draft
---

## Foundations

### GAS foundations

<figure class="diagram">
  <a href="../../diagrams/gas-foundations.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/gas-foundations.svg" alt="GAS foundations in ten numbered steps: the constructor creates the ability system on every machine, the server sets it up and gives abilities on possession, and the owning client wires up its copy and turns key presses into abilities. The table below lists every function." /></a>
  <figcaption>Every machine builds the ability system, only the server fills it, and the owning client presses it.</figcaption>
</figure>

#### What it does

Every character in the game, heroes and skeleton minions alike, carries Unreal's Gameplay Ability System. It holds the character's attributes (health, mana, attack damage, armour), the effects acting on it, its gameplay tags and the abilities it can use. When a hero spawns, the server gives it base stats for that hero and its abilities: light attacks ready to use, heavy abilities waiting to be learnt, and passives like death that never need a key. Pressing an ability key finds the matching ability and tries to activate it, with the server deciding whether it really happens.

#### Step by step

The numbers match the diagram.

| # | Step | Calls, in order | Runs on |
|---|---|---|---|
| 1 | Character built | Constructor → `CreateDefaultSubobject` for the ASC and [`UChrisAttributeSet`](code:UChrisAttributeSet); player characters also make [`UCHeroAttributeSet`](code:UCHeroAttributeSet) | Every machine |
| 2 | Possessed | Player: [`OnPossess`](code:AChrisPlayerController::OnPossess) → [`ServerSideInit`](code:AChrisCharacter::ServerSideInit). Minion: [`PossessedBy`](code:AChrisCharacter::PossessedBy) → `ServerSideInit` | Server |
| 3 | Wire it up | `InitAbilityActorInfo(this, this)`, then the ASC's own [`ServerSideInit`](code:UChrisAbilitySystemComponent::ServerSideInit) | Server |
| 4 | Base stats | [`InitializeBaseAttributes`](code:UChrisAbilitySystemComponent::InitializeBaseAttributes) finds this class's row in the base stats data table | Server |
| 5 | Initial effects | [`ApplyInitialEffects`](code:UChrisAbilitySystemComponent::ApplyInitialEffects) | Server |
| 6 | Give abilities | [`GiveInitialAbilities`](code:UChrisAbilitySystemComponent::GiveInitialAbilities): heavy at level 0, light at level 1, passives with no input | Server |
| 7 | Possession arrives | [`AcknowledgePossession`](code:AChrisPlayerController::AcknowledgePossession) → [`ClientSideInit`](code:AChrisCharacter::ClientSideInit) | Owning client |
| 8 | Wire it up | `InitAbilityActorInfo(this, this)` on the client's copy | Owning client |
| 9 | Press a key | Enhanced Input → [`HandleAbilityInput`](code:AChrisPlayerCharacter::HandleAbilityInput) with that key's `EChrisAbilityInputID` | Owning client |
| 10 | Find the ability | `AbilityLocalInputPressed(InputID)` activates the ability given with that input ID | Owning client, confirmed by the server |

#### How it works

**On the character, not the Player State** – [`AChrisCharacter`](code:AChrisCharacter) creates its [`UChrisAbilitySystemComponent`](code:UChrisAbilitySystemComponent) and combat attribute set in its constructor, and implements `IAbilitySystemInterface` so any GAS code can find them ([`GetAbilitySystemComponent`](code:AChrisCharacter::GetAbilitySystemComponent)). Heroes are never destroyed when they die: they respawn in place, so cooldowns, effects and levels stay on the same ASC. Minions use the same class, and AI controllers have no Player State, so the character is the one place both can share.

**Set up on both sides** – the server and the owning client each have their own copy of the character and its ASC, so each calls `InitAbilityActorInfo` to tell its copy who owns it and which body it drives. Only the server then fills it in: base stats from a data table row matched by class, the initial effects, and every ability. Granting abilities is server-only and replicates down. Minions are set up from `PossessedBy`, because their AI controller exists only on the server and no client ever acknowledges possessing them.

**Abilities as data** – each hero's Blueprint lists its abilities in two maps of input ID to ability class: heavy `Abilities` and light `BasicAbilities`. The shared [`UPA_GenericAbilitySystem`](code:UPA_GenericAbilitySystem) data asset holds what every hero has in common: the passive abilities, the initial effects and the base stats table. `GiveAbility` takes a level and an input ID. Heavy abilities start at level 0, which the tutorial calls "not learnt": they can't be cast until an upgrade point buys level 1. Passives get input ID −1, because they are triggered by tags and events, never by a key.

**From key to ability** – the player character maps each Enhanced Input action to an `EChrisAbilityInputID` ([`SetupPlayerInputComponent`](code:AChrisPlayerCharacter::SetupPlayerInputComponent)). Pressing it calls `AbilityLocalInputPressed` with that ID, and the ASC activates the ability that was given with the same ID. Light attacks also send a gameplay event, locally and to the server, which the combo ability listens for to chain the next hit.

#### Why I designed it this way

- **The ASC on the character** – the common reason to put it on the Player State is that the pawn is destroyed on death and a fresh one would lose its cooldowns and buffs. My heroes respawn without being destroyed, and minions need the same system with no Player State, so the character is simpler and fits both.
- **A second attribute set only for heroes** – XP, level, souls, upgrade points and growth rates only matter to players. Every skeleton carrying and replicating them would be waste, so they live in `UCHeroAttributeSet`, created only by `AChrisPlayerCharacter`.
- **Stats in a data table, abilities in Blueprint maps** – balancing a hero means editing a row or a map, not C++. A new hero needs a table row and its two ability maps.
- **Input IDs instead of one function per key** – one handler serves every ability. Rebinding a key or swapping an ability is an editor change.

### Attributes, XP & levelling

<figure class="diagram">
  <a href="../../diagrams/gas-levelling.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/gas-levelling.svg" alt="Levelling in numbered steps: XP from kills and flag zones changes the Experience attribute, the server works out the level and upgrade points, stats grow with level, and the owning client spends points on heavy abilities through a server RPC. The table below lists every function." /></a>
  <figcaption>XP only ever changes on the server. Everything a player sees, and every upgrade they ask for, goes through it.</figcaption>
</figure>

#### What it does

Every character has combat attributes: health, mana, attack damage, armour, speed, plus the values the shop's skills and upgrades switch on. Heroes also have a second set for progression: experience, level (1 to 10), souls and upgrade points. Kills and standing in a flag zone earn XP. Each new level raises the hero's stats by that hero's own growth rates and gives upgrade points, which are spent on the four heavy abilities: 1 point to learn one, then 2, 3 and 4 points for levels 2, 3 and 4.

#### Step by step

The numbers match the diagram.

| # | Step | Calls, in order | Runs on |
|---|---|---|---|
| A | Subscribe | ASC [constructor](code:UChrisAbilitySystemComponent::UChrisAbilitySystemComponent) puts `ExperienceUpdated` on Experience's value-change delegate | Every machine |
| B | Starting values | [`InitializeBaseAttributes`](code:UChrisAbilitySystemComponent::InitializeBaseAttributes): growth rates from the data table, max level from the XP curve, level 1, then one `ExperienceUpdated` call to set the gauge's first target | Server |
| 1a | XP from a kill | [`UGAP_Dead::ActivateAbility`](code:UGAP_Dead::ActivateAbility) applies a reward effect carrying XP and souls (set-by-caller values) | Server |
| 1b | XP from a flag zone | [`AFlag::Tick`](code:AFlag::Tick) → `ApplyModToAttribute`, +50 XP every 8 seconds | Server |
| 2 | Experience changes | The delegate from A calls [`ExperienceUpdated`](code:UChrisAbilitySystemComponent::ExperienceUpdated) with the new total XP | Server |
| 3 | Work out the level | Same function: walk the XP curve to the first threshold above the total, add the levels gained to upgrade points, save level, previous and next XP | Server |
| 4 | Stats grow | [`MMC_LevelBased`](code:UMMC_LevelBased::CalculateBaseMagnitude_Implementation) recalculates `(Level − 1) × GrowthRate` because it watches Level live | Server |
| 5 | Shown on the HUD | Level, XP and points replicate → the XP gauge and upgrade buttons update | Owning client |
| 5b | Press upgrade | [`UpgradeAbilityWithInputID`](code:AChrisCharacter::UpgradeAbilityWithInputID) → `Server_UpgradeAbilityWithID` (a Server RPC on the ASC) | Sent by the owning client |
| 6 | Pay and upgrade | [`Server_UpgradeAbilityWithID`](code:UChrisAbilitySystemComponent::Server_UpgradeAbilityWithID_Implementation): find the ability by input ID, refuse if level 4 ([`IsAbilityAtMaxLevel`](code:UChrisAbilitySystemStatics::IsAbilityAtMaxLevel)) or unaffordable, pay `Level + 1` points, raise the level, `MarkAbilitySpecDirty` | Server |
| 7 | Upgrade arrives | [`Client_AbilitySpecLevelUpdated`](code:UChrisAbilitySystemComponent::Client_AbilitySpecLevelUpdated_Implementation): set the level now, broadcast to the UI, play the upgrade sound | Owning client |

#### How it works

**Two attribute sets** – [`UChrisAttributeSet`](code:UChrisAttributeSet) is on every character and holds the combat values. [`UCHeroAttributeSet`](code:UCHeroAttributeSet) is only created by the player character and holds intelligence, strength, the growth rates, experience, level, souls and upgrade points. Health and mana are clamped between 0 and their maximum in [`PreAttributeChange`](code:UChrisAttributeSet::PreAttributeChange), which edits the incoming value before it is applied.

**XP is a running total** – the XP curve in the shared data asset stores the total XP needed to reach each level. `ExperienceUpdated` walks it until it finds the first threshold the hero hasn't reached: everything below is a level gained, that threshold is the next target. It saves the previous and next thresholds too, so the HUD can show progress within the level. It only runs on the server, because the same delegate also fires on clients when the replicated XP arrives.

**Stats grow without being told** – a Gameplay Effect applied at setup uses `MMC_LevelBased`, which captures the hero's Level and returns `(Level − 1) × GrowthRate`. Level 1 adds nothing, because the base stats already apply. Each hero's growth rates come from its data table row, which is how Christos gains more intelligence per level than Yuri.

**Spending points** – the client can only ask. The server checks the points from its own copy, charges the level being bought, raises the ability's level and marks it dirty so it replicates. A Client RPC follows so the owning player hears the upgrade sound and sees the notch straight away, instead of waiting for replication. Heavy abilities start at level 0, so the first purchase is what makes them castable.

#### Why I designed it this way

- **Levels from a curve, not from code** – the thresholds are a curve asset, so rebalancing how fast players level is an editor change. Max level is simply the number of keys.
- **Event-driven, not polled** – nothing checks XP every frame. The delegate calls `ExperienceUpdated` only when XP actually changes, from any source.
- **The server owns progression** – XP, level and points are only ever written on the server, and an upgrade is a request the server checks. A modified client can't give itself points.
- **Rising costs** – charging the level being bought makes level 4 cost four times as much as learning the ability, so players choose between maxing one heavy ability or spreading points across all four.

## Systems that change a hero

Each of these is a system in its own right, and each one switches on conditions that decide what a hit does later. Every section ends with where it plugs into the hit.

### Weapon equip

<figure class="diagram">
  <a href="../../diagrams/gas-weapon-equip.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/gas-weapon-equip.svg" alt="Weapon equip in numbered steps: the equip ability decides the direction and plays a replicated montage, anim notifies on every machine fly the swords through Throw, Hover and Snap, and the final state sets the tag that decides which attacks can be used. Between rounds a replicated counter resets every player's swords. The table below lists every function." /></a>
  <figcaption>Only the animation crosses the network. Every machine flies its own swords, and one tag tells the attacks what's allowed.</figcaption>
</figure>

#### What it does

Every hero carries two swords on their back. Pressing equip throws them over the shoulders, holds them in the air for a moment, then snaps them into the hands; pressing it again sends them back to the sheaths. With swords out a hero can use their light combos, Stab and Thrust. With swords away they can Shoot instead. While the swords are in the air, no attack can start. Every player sees the same flight, and every round starts with swords sheathed.

#### Step by step

The numbers match the diagram.

| # | Step | Calls, in order | Runs on |
|---|---|---|---|
| 1 | Press equip | Input ID → ASC activates [`GA_EquipToggle`](code:UGA_EquipToggle::ActivateAbility); blocked while aiming | Server and owning client |
| 2 | Decide which way | `K2_CommitAbility` → `FindComponentByClass<USwordEquipComponent>` → [`BeginEquip`](code:USwordEquipComponent::BeginEquip) or [`BeginUnequip`](code:USwordEquipComponent::BeginUnequip); a press mid-flight is ignored | Server and owning client |
| 3 | Play the montage | `PlayMontageAndWait`; the ability ends when the montage completes, blends out, is interrupted or is cancelled | Server and owning client, replicated to everyone |
| 4 | Anim notify fires | [`UAN_SwordPhase::Notify`](code:UAN_SwordPhase::Notify) → [`ExecutePhaseAction`](code:USwordEquipComponent::ExecutePhaseAction)`(DetachAndThrow)`; other players' machines work out the direction from the current state | Every machine |
| 5 | Throw, Hover, Snap | [`DetachSwordsToMeshRoot`](code:USwordEquipComponent::DetachSwordsToMeshRoot) → [`StartPhase`](code:USwordEquipComponent::StartPhase) → [`TickComponent`](code:USwordEquipComponent::TickComponent) moves the swords ([`UpdateSwordTransforms`](code:USwordEquipComponent::UpdateSwordTransforms)) → [`AdvanceToNextPhase`](code:USwordEquipComponent::AdvanceToNextPhase) | Every machine |
| 6 | Swords arrive | [`FinalizeEquip`](code:USwordEquipComponent::FinalizeEquip) or [`FinalizeUnequip`](code:USwordEquipComponent::FinalizeUnequip) → [`AttachSwordsToSockets`](code:USwordEquipComponent::AttachSwordsToSockets) → [`UpdateEquippedTag`](code:USwordEquipComponent::UpdateEquippedTag) | Every machine |
| 7 | Reset, server | [`ResetAllPlayerSwords`](code:AChrisGameMode::ResetAllPlayerSwords) → [`ServerResetToUnequipped`](code:USwordEquipComponent::ServerResetToUnequipped): `++ResetCount`, then reset its own copy | Server |
| 8 | Reset, clients | `ResetCount` replicates → [`OnRep_ResetCount`](code:USwordEquipComponent::OnRep_ResetCount) → [`ResetToUnequipped`](code:USwordEquipComponent::ResetToUnequipped) | Every client |

#### How it works

**An ability and a component** – [`UGA_EquipToggle`](code:UGA_EquipToggle::ActivateAbility) is a Gameplay Ability, so it gets GAS's cooldown, blocking tags and replicated montages for free. It only decides the direction and plays the right montage. [`USwordEquipComponent`](code:USwordEquipComponent) owns everything about the swords: where they are, the flight, the glow and the tag.

**The animation drives the timing** – anim notifies placed on the montage call `ExecutePhaseAction` with one of three commands: start the throw, jump to the snap, or attach now. The last two keep the swords locked to the animation even if the flight durations in the editor don't quite match it. Because GAS replicates the montage, the notifies fire on every machine, and each one flies its own copy of the swords. On other players' machines `BeginEquip` was never called, so the throw command works out the direction from where the swords currently are.

**Two state machines** – `ESwordEquipState` says where the swords are: unequipped, equipping, equipped or unequipping. `ESwordFlyPhase` runs only during the two transitions: Throw to an apex over the shoulder (easing out), Hover there, then Snap into the hands or sheaths (easing in). Each phase records a start and end transform, and the tick moves both swords by `Alpha += DeltaTime / Duration`, lerping position and slerping rotation. In flight the swords are attached to the character's root rather than a bone, so they follow the character but not the arms. Ticking is only switched on during the flight.

**Tags as the contract** – when the swords land, `UpdateEquippedTag` adds `stats.weapon.equipped` or `stats.weapon.unequipped`, and removes both while they're in the air. The attack abilities never ask the component anything: melee abilities require the equipped tag, and Shoot requires unequipped and is blocked by equipped. The tags are loose and not replicated, which works because every machine sets them itself at the end of its own flight.

**Resetting between rounds** – a function only runs on the machine that calls it, so the Game Mode can't sheath everyone's swords directly. Instead the server increments a replicated `ResetCount`. Each client sees the number change and resets its own swords in `OnRep_ResetCount`. The server resets its copy straight away, because `OnRep` never fires on the server.

#### Why I designed it this way

- **Replicate the animation, not the swords** – sending the swords' positions every frame would cost bandwidth for something purely visual. One replicated montage gives every machine the same flight for free.
- **The tag decouples equip from combat** – adding a new attack only needs the right required tag. The equip system doesn't know which attacks exist, and the attacks don't know how equipping works.
- **The component is reusable** – the lobby's hero preview uses a display version of the same flight, and the anim notify drives whichever one the character has.
- **A counter, not a bool, for the reset** – `OnRep` only fires when a value changes. A bool set to true would stay true after the first round, so the second reset would never arrive. A counter changes every time.

### The shop: skills, ability upgrades & consumables

<div class="placeholder">Diagram: buying an item, the three item kinds, and what each one changes</div>

#### What it does

TODO

#### Step by step

TODO

#### How it works

TODO

#### Why I designed it this way

TODO

## The hit

### The life of a hit

<div class="placeholder">Diagram: the five stages of a hit, with every condition coloured by the system that controls it</div>

TODO: can I attack → where does it hit → how hard → how much is taken → what happens next.

### Melee combos & hit detection

<div class="placeholder">Diagram: a combo from key press to anim notify sweep to gameplay event</div>

#### What it does

TODO

#### Step by step

TODO

#### How it works

TODO

#### Why I designed it this way

TODO

### Ranged & area abilities

<div class="placeholder">Diagram: Ranged & area abilities</div>

#### What it does

TODO

#### Step by step

TODO

#### How it works

TODO

#### Why I designed it this way

TODO

### The damage pipeline

<div class="placeholder">Diagram: The damage pipeline</div>

#### What it does

TODO

#### Step by step

TODO

#### How it works

TODO

#### Why I designed it this way

TODO

### Death, stun, knockback & rewards

<div class="placeholder">Diagram: Death, stun, knockback & rewards</div>

#### What it does

TODO

#### Step by step

TODO

#### How it works

TODO

#### Why I designed it this way

TODO

## How it connects

- Gameplay Framework — the ASC lives on the character; souls come from the Game Mode; flags read Dominion
- Networking — what runs on the server, what is predicted, what replicates
- UI — ability gauges, the shop widget, the skill tree
- AI — minions use the same ASC and attribute set, and press abilities through a behaviour tree task
- Audio — cooldown and low-health sounds driven by tags

## Built to extend

#### Easy to add today

TODO

#### Would need work first

TODO

## Challenges & bugs

### Heroes started with a free upgrade point

- **Symptom** – every hero spawned with one upgrade point they hadn't earned.
- **Cause** – Level started at 0. The first `ExperienceUpdated` call worked out level 1 and counted the jump from 0 to 1 as a level gained.
- **Fix** – `InitializeBaseAttributes` sets Level to 1 before the first call, so the starting level is never counted as progress.
- **Lesson** – when something is calculated as a difference (new minus old), the starting "old" value matters as much as the formula.

**Symptom → cause → fix → lesson** – TODO: UGA_Shoot fired multiple shots per press until input was debounced; the death effect needed Infinite duration for the respawn flow.

## Optimisations

TODO: before/after, with numbers where possible.

## What I'd do differently

TODO
