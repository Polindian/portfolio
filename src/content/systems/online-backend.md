---
title: "Online Backend"
summary: "Steam login through EOS, sessions matched by GUID, a Python coordinator that launches servers and stores stats, and deployment with Docker on AWS."
order: 4
tags: ["EOS", "Steam", "Flask", "SQLite", "Docker", "AWS EC2"]
glance:
  - "TODO: e.g. One GUID ties a lobby, its EOS session and its dedicated server together"
  - "TODO: e.g. The coordinator spins up a server container per match"
  - "TODO: e.g. Servers post results at match end; leaderboard reads from SQLite"
keyFiles:
  - { path: "Framework/ChrisGameInstance.cpp", note: "Login, session create/join" }
  - { path: "Network/ChrisNetStatics.cpp", note: "Shared network helpers" }
  - { path: "Network/ChrisGameSession.cpp", note: "Server-side player registration" }
  - { path: "Data/MatchStatsTypes.h", note: "Match result data" }
  - { path: "Data/LeaderboardTypes.h", note: "Leaderboard row data" }
  - { path: "ServerDeploy/coordinator/coordinator/coordinator.py", note: "Flask coordinator" }
  - { path: "ServerDeploy/docker-compose.yaml", note: "Deployment setup" }
status: draft
---

## Features

### Login: Steam → EOS

<div class="placeholder">GIF / screenshot: Login: Steam → EOS</div>

#### What it does

TODO: EOSPlus + EOS Connect flow and the translator-delegate pattern in the GameInstance.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Creating & finding sessions

<div class="placeholder">GIF / screenshot: Creating & finding sessions</div>

#### What it does

TODO: HTTP request to the coordinator, polling, EOS search by GUID.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### The coordinator service

<div class="placeholder">GIF / screenshot: The coordinator service</div>

#### What it does

TODO: what the Flask app does, its endpoints and secrets.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Server lifecycle

<div class="placeholder">GIF / screenshot: Server lifecycle</div>

#### What it does

TODO: registration, player tracking in AChrisGameSession, no-players timeout.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Match stats & leaderboard

<div class="placeholder">GIF / screenshot: Match stats & leaderboard</div>

#### What it does

TODO: data structs, who posts results, leaver rules, sorting.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

### Deployment

<div class="placeholder">GIF / screenshot: Deployment</div>

#### What it does

TODO: Linux server build, Docker Compose, EC2, versioned images.

#### How it works

TODO

#### Why I designed it this way

TODO: alternatives considered and trade-offs.

## How it connects

- UI Architecture — session search & leaderboard widgets
- Gameplay Framework — match end → stats
- Networking — dedicated servers

## Built to extend

#### Easy to add today

TODO: what this system makes easy to add, and which part of the design makes it easy.

#### Would need work first

TODO: honest limits, and what would need changing to remove them.

## Challenges & bugs

**Symptom → cause → fix → lesson** – TODO: TODO: e.g. EOS P2P sockets failing to bind without login and the fallback to the menu map.

## Optimisations

TODO: before/after, with numbers where possible.

## What I'd do differently

TODO: honest self-critique and planned refactors.
