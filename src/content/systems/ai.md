---
title: "AI"
summary: "Behaviour-tree enemies that pick goals, take tactical positions and fight using the same ability system as players."
order: 6
tags: ["Behaviour Trees", "BT Services", "BT Tasks", "GAS"]
glance:
  - "TODO: e.g. AI uses the same abilities as players by sending input to the ASC"
  - "TODO: e.g. Services update goals and combat mode each tick interval"
  - "TODO: e.g. Barracks spawn and manage skeleton waves"
keyFiles:
  - { path: "AI/ChrisAIController.cpp", note: "AI controller" }
  - { path: "AI/BTService_UpdateGoal.cpp", note: "Goal selection" }
  - { path: "AI/BTService_TacticalPosition.cpp", note: "Positioning" }
  - { path: "AI/BTTask_SendInputToAbilitySystem.cpp", note: "AI \u2192 abilities" }
  - { path: "AI/SkeletonBarrack.cpp", note: "Spawner" }
status: draft
---

## Features

### Behaviour tree overview

<div class="placeholder">GIF / screenshot: Behaviour tree overview</div>

#### What it does

TODO: the tree, blackboard keys and the main loop.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Services: goals, combat mode, tactical position

<div class="placeholder">GIF / screenshot: Services: goals, combat mode, tactical position</div>

#### What it does

TODO: what each BTService decides and how often.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### AI using GAS

<div class="placeholder">GIF / screenshot: AI using GAS</div>

#### What it does

TODO: BTTask_SendInputToAbilitySystem.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Spawning

<div class="placeholder">GIF / screenshot: Spawning</div>

#### What it does

TODO: SkeletonBarrack and SkeletonAI.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

## How it connects

- GAS & Combat
- Gameplay Framework

## Built to extend

#### Easy to add today

TODO: what this system makes easy to add, and which part of the design makes it easy.

#### Would need work first

TODO: honest limits, and what would need changing to remove them.

## Challenges & bugs

**Symptom → cause → fix → lesson** – TODO: TODO

## Optimisations

TODO: before/after, with numbers where possible.

## What I'd do differently

TODO: honest self-critique and planned refactors.
