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

<div class="placeholder">Diagram: GAS foundations</div>

#### What it does

TODO

#### Step by step

TODO

#### How it works

TODO

#### Why I designed it this way

TODO

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
