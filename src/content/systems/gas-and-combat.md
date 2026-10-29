---
title: "GAS & Combat"
summary: "Combat built on Unreal's Gameplay Ability System: combos, light and heavy attacks, projectiles, area damage, upgrades and consumables."
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

## Features

### Ability architecture

<div class="placeholder">GIF / screenshot: Ability architecture</div>

#### What it does

TODO: base ChrisGameplayAbility, custom ASC, input binding and default abilities per hero (PA_GenericAbilitySystem).

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Attributes & levelling

<div class="placeholder">GIF / screenshot: Attributes & levelling</div>

#### What it does

TODO: ChrisAttributeSet / CHeroAttributeSet and level scaling via MMC_LevelBased.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Melee combos

<div class="placeholder">GIF / screenshot: Melee combos</div>

#### What it does

TODO: GA_Combo and the light/heavy attacks (Swipe, Thrust, Stab).

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Animation-driven hit detection

<div class="placeholder">GIF / screenshot: Animation-driven hit detection</div>

#### What it does

TODO: anim notifies (AN_SendTargetGroup, AN_SendGameplayEvent) and socket traces that apply damage.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Damage calculation

<div class="placeholder">GIF / screenshot: Damage calculation</div>

#### What it does

TODO: the MMCs for base/light/heavy damage and the BlindBomb execution calculation.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Projectiles & area abilities

<div class="placeholder">GIF / screenshot: Projectiles & area abilities</div>

#### What it does

TODO: GA_Shoot + ProjectileActor, TargetActor_Around, GA_BlindBomb.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Death & knockback

<div class="placeholder">GIF / screenshot: Death & knockback</div>

#### What it does

TODO: passive abilities GAP_Dead and GAP_Launched.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Upgrades, skill tree & souls

<div class="placeholder">GIF / screenshot: Upgrades, skill tree & souls</div>

#### What it does

TODO: earning souls, spending upgrade points, ability upgrades.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Shop, inventory & consumables

<div class="placeholder">GIF / screenshot: Shop, inventory & consumables</div>

#### What it does

TODO: PA_ShopItem, InventoryComponent, using items in the arena.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Weapon equip

<div class="placeholder">GIF / screenshot: Weapon equip</div>

#### What it does

TODO: GA_EquipToggle and SwordEquipComponent.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

## How it connects

- Networking — GAS prediction and replication modes
- Gameplay Framework — ASC lives on the character/player state
- Audio — gameplay tags trigger sounds

## Challenges & bugs

**Symptom → cause → fix → lesson** – TODO: UGA_Shoot fired multiple shots per press until input was debounced; the death effect needed Infinite duration for the respawn flow.

## Optimisations

TODO: before/after, with numbers where possible.

## What I'd do differently

TODO: honest self-critique and planned refactors.
