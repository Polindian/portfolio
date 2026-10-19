---
title: "UI Architecture"
summary: "A page-and-overlay menu system with keyboard/controller focus navigation, reusable C++ widgets and a live server browser."
order: 5
tags: ["UMG", "C++ widgets", "Focus navigation", "Data-driven lists"]
glance:
  - "TODO: e.g. One widget switcher drives every menu page"
  - "TODO: e.g. Reusable MenuButtonWidget with live Designer preview"
  - "TODO: e.g. Server browser builds entries from session search results"
keyFiles:
  - { path: "Widgets/MainMenuWidget.cpp", note: "Menu page system" }
  - { path: "Widgets/MenuButtonWidget.cpp", note: "Reusable button" }
  - { path: "Widgets/SessionSearchBarWidget.cpp", note: "Server search" }
  - { path: "Widgets/SessionEntryWidget.cpp", note: "Server browser entry" }
  - { path: "Widgets/LeaderboardWidget.cpp", note: "Leaderboard overlay" }
  - { path: "Player/MenuPlayerController.cpp", note: "Spawns the menu widget" }
status: draft
---

## Features

### Page & overlay system

<div class="placeholder">GIF / screenshot: Page & overlay system</div>

**What it does.** TODO: widget switcher pages, fade transitions, overlays that hold focus.

**How it works.** TODO

**Why I designed it this way.** TODO: alternatives considered and trade-offs.

### Reusable widgets

<div class="placeholder">GIF / screenshot: Reusable widgets</div>

**What it does.** TODO: MenuButtonWidget, BackHintWidget and why C++ base classes.

**How it works.** TODO

**Why I designed it this way.** TODO: alternatives considered and trade-offs.

### Keyboard & controller navigation

<div class="placeholder">GIF / screenshot: Keyboard & controller navigation</div>

**What it does.** TODO: focus paths, default buttons, back input.

**How it works.** TODO

**Why I designed it this way.** TODO: alternatives considered and trade-offs.

### Session search & server browser

<div class="placeholder">GIF / screenshot: Session search & server browser</div>

**What it does.** TODO: SessionSearchBarWidget → results → SessionEntryWidget population.

**How it works.** TODO

**Why I designed it this way.** TODO: alternatives considered and trade-offs.

### Leaderboard overlay

<div class="placeholder">GIF / screenshot: Leaderboard overlay</div>

**What it does.** TODO: sorting, paging, animations.

**How it works.** TODO

**Why I designed it this way.** TODO: alternatives considered and trade-offs.

## How it connects

- Online Backend — session search & leaderboard data
- Gameplay Framework — menu player controllers

## Challenges & bugs

**Symptom → cause → fix → lesson.** TODO: TODO: e.g. BindToAnimationFinished stacking callbacks, or SetActiveWidget failing silently.

## Optimisations

TODO: before/after, with numbers where possible.

## What I'd do differently

TODO: honest self-critique and planned refactors.
