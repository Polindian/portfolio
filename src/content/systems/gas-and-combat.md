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

### Attributes & levelling

<div class="placeholder">Diagram: Attributes & levelling</div>

#### What it does

TODO

#### Step by step

TODO

#### How it works

TODO

#### Why I designed it this way

TODO

## Systems that change a hero

Each of these is a system in its own right, and each one switches on conditions that decide what a hit does later. Every section ends with where it plugs into the hit.

### Weapon equip

<div class="placeholder">Diagram: Weapon equip</div>

#### What it does

TODO

#### Step by step

TODO

#### How it works

TODO

#### Why I designed it this way

TODO

### Shop & inventory

<div class="placeholder">Diagram: Shop & inventory</div>

#### What it does

TODO

#### Step by step

TODO

#### How it works

TODO

#### Why I designed it this way

TODO

### Skill trees

<div class="placeholder">Diagram: Skill trees</div>

#### What it does

TODO

#### Step by step

TODO

#### How it works

TODO

#### Why I designed it this way

TODO

### Ability levelling & upgrades

<div class="placeholder">Diagram: Ability levelling & upgrades</div>

#### What it does

TODO

#### Step by step

TODO

#### How it works

TODO

#### Why I designed it this way

TODO

### Consumables

<div class="placeholder">Diagram: Consumables</div>

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

### Melee combos

<div class="placeholder">Diagram: Melee combos</div>

#### What it does

TODO

#### Step by step

TODO

#### How it works

TODO

#### Why I designed it this way

TODO

### Hit detection

<div class="placeholder">Diagram: Hit detection</div>

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

**Symptom → cause → fix → lesson** – TODO: UGA_Shoot fired multiple shots per press until input was debounced; the death effect needed Infinite duration for the respawn flow.

## Optimisations

TODO: before/after, with numbers where possible.

## What I'd do differently

TODO
