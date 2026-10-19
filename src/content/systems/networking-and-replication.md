---
title: "Networking & Replication"
summary: "Server-authoritative multiplayer on dedicated servers: what replicates, who owns what, and how I measured and reduced network cost."
order: 3
tags: ["Dedicated server", "Replication", "RPCs", "Prediction", "Unreal Insights"]
glance:
  - "TODO: e.g. The server is the authority for damage, rounds and stats"
  - "TODO: e.g. Clients predict abilities through GAS"
  - "TODO: e.g. Measured bandwidth with Networking Insights and cut X%"
keyFiles:
  - { path: "Framework/ChrisGameState.cpp", note: "Replicated match state" }
  - { path: "Player/ChrisPlayerState.cpp", note: "Replicated player data" }
  - { path: "Player/ChrisPlayerController.cpp", note: "Client/server RPCs" }
  - { path: "GAS/ChrisAbilitySystemComponent.cpp", note: "Ability replication" }
status: draft
---

## Features

### Authority model

<div class="placeholder">GIF / screenshot: Authority model</div>

**What it does.** TODO: what the server decides vs what clients predict.

**How it works.** TODO

**Why I designed it this way.** TODO: alternatives considered and trade-offs.

### Replicated properties vs RPCs

<div class="placeholder">GIF / screenshot: Replicated properties vs RPCs</div>

**What it does.** TODO: examples from the game and when I chose each.

**How it works.** TODO

**Why I designed it this way.** TODO: alternatives considered and trade-offs.

### Ownership & relevancy

<div class="placeholder">GIF / screenshot: Ownership & relevancy</div>

**What it does.** TODO: who owns which actors and why it matters for RPCs.

**How it works.** TODO

**Why I designed it this way.** TODO: alternatives considered and trade-offs.

### GAS over the network

<div class="placeholder">GIF / screenshot: GAS over the network</div>

**What it does.** TODO: replication mode and prediction for abilities and effects.

**How it works.** TODO

**Why I designed it this way.** TODO: alternatives considered and trade-offs.

### Testing setup

<div class="placeholder">GIF / screenshot: Testing setup</div>

**What it does.** TODO: dedicated server + multiple clients locally, Dev Auth Tool, launch scripts, network emulation.

**How it works.** TODO

**Why I designed it this way.** TODO: alternatives considered and trade-offs.

## How it connects

- GAS & Combat
- Gameplay Framework
- Online Backend — server lifecycle

## Challenges & bugs

**Symptom → cause → fix → lesson.** TODO: TODO: pick a replication bug — symptom, cause, fix, lesson.

## Optimisations

TODO: before/after, with numbers where possible.

## What I'd do differently

TODO: honest self-critique and planned refactors.
