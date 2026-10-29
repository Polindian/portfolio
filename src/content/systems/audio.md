---
title: "Audio"
summary: "Original music plus a sound system that decides who hears each sound over the network, and whether it plays in 2D or 3D."
order: 7
tags: ["Audio subsystem", "Gameplay Tags", "Anim Notifies", "Original music"]
glance:
  - "TODO: e.g. One routing rule per sound: owner only, team, or everyone"
  - "TODO: e.g. Sounds are looked up by gameplay tag, not hard-coded assets"
  - "TODO: e.g. All music composed by me"
keyFiles:
  - { path: "Audio/ChrisAudioSubsystem.cpp", note: "Central audio subsystem" }
  - { path: "Audio/ChrisSoundLibrary.cpp", note: "Tag \u2192 sound lookup" }
  - { path: "Audio/AnimNotify_ChrisSound.cpp", note: "Sounds from animations" }
  - { path: "Audio/ChrisGameUserSettings.cpp", note: "Volume settings" }
status: draft
---

## Features

### Original music

<div class="placeholder">GIF / screenshot: Original music</div>

#### What it does

TODO: what you composed, tools and how it is used in game.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Sound routing over the network

<div class="placeholder">GIF / screenshot: Sound routing over the network</div>

#### What it does

TODO: who hears it, 2D vs 3D, and why.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Tag-driven sound library

<div class="placeholder">GIF / screenshot: Tag-driven sound library</div>

#### What it does

TODO: ChrisSoundLibrary and ChrisGameplayTags.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Animation-timed sounds

<div class="placeholder">GIF / screenshot: Animation-timed sounds</div>

#### What it does

TODO: AnimNotify_ChrisSound and ChrisSoundCueNotify.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Settings & volume

<div class="placeholder">GIF / screenshot: Settings & volume</div>

#### What it does

TODO: ChrisGameUserSettings and volume sliders.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

## How it connects

- GAS & Combat — abilities trigger sounds
- Networking — routing depends on ownership

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
