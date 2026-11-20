---
title: "GAS & Combat"
summary: "Combat built on Unreal's Gameplay Ability System, and the systems that shape every hit: weapon equip, a shop with skill trees, ability levelling and consumables."
order: 2
tags: ["GAS", "Gameplay Effects", "Attributes", "Anim Notifies", "Gameplay Tags"]
glance:
  - "Every attack is a Gameplay Ability, so it gets prediction and replication for free"
  - "Montage notifies open combo windows and sweep the sword's sockets; only the server turns hits into damage"
  - "Damage is worked out in two stages: an MMC for stats against Armour, then the attribute set for every skill"
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

### The shop: buying an item

<figure class="diagram">
  <a href="../../diagrams/gas-shop-buying.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/gas-shop-buying.svg" alt="Buying a shop item in numbered steps: the shelf is loaded from item assets, a click is checked on the player's PC, the server checks the phase and souls again, pays, and either applies a permanent effect or puts a consumable in the inventory, then tells the player it succeeded or failed. The table below lists every function." /></a>
  <figcaption>The player's PC answers instantly; the server is the one that actually sells.</figcaption>
</figure>

#### What it does

Between rounds the shop opens for 60 seconds. Players spend the souls they earned on 21 items: 12 skills in four trees, 4 premium ability upgrades, and 5 potions. Skills and upgrades are bought once and last the whole match. Potions go into a five-slot inventory to be used in the arena. The shop refuses anything the player can't afford, already owns, or has bought too many of, and closes the moment the phase ends.

#### Step by step

The numbers match the diagram.

| # | Step | Calls, in order | Runs on |
|---|---|---|---|
| 1 | Items on the shelf | [`LoadShopItems`](code:UCAssetManager::LoadShopItems) loads every [`UPA_ShopItem`](code:UPA_ShopItem) by asset type → [`ShopItemLoadFinished`](code:UShopWidget::ShopItemLoadFinished) fills the shop | Owning client |
| 2 | Click an item | [`OnItemPurchaseRequested`](code:UShopWidget::OnItemPurchaseRequested): refuse if the shop is closing → [`TryPurchase`](code:UInventoryComponent::TryPurchase): refuse if owned, out of stock or unaffordable ([`GetSoul`](code:UInventoryComponent::GetSoul)) | Owning client |
| 3 | Ask the server | `TryPurchase` marks the item owned locally, then sends `Server_Purchase` | Owning client → server |
| 4 | Check again | [`Server_Purchase`](code:UInventoryComponent::Server_Purchase_Implementation): still the shop phase (`IsInShopPhase`)? enough souls? If not → `Client_PurchaseFailed` | Server |
| 5a | Permanent item | Pay with `ApplyModToAttribute` on Soul → apply `EquippedEffect` to self, or `GiveAbility` for a `GrantedAbility` → `Client_SkillPurchased` | Server |
| 5b | Consumable | Slot free and stock left? → [`GrantItem`](code:UInventoryComponent::GrantItem) → pay → count the purchase (see Inventory & consumables) | Server |
| 6 | Confirmed | [`Client_SkillPurchased`](code:UInventoryComponent::Client_SkillPurchased_Implementation) → `OnSkillPurchased` → the widget relocks the trees ([`OnSkillPurchasedCallback`](code:UShopWidget::OnSkillPurchasedCallback)) and plays the unlock sound | Owning client |
| 6b | Refused | [`Client_PurchaseFailed`](code:UInventoryComponent::Client_PurchaseFailed_Implementation) un-marks the item → `OnPurchaseFailed` → reject sound | Owning client |

#### How it works

**One asset class for every item** – [`UPA_ShopItem`](code:UPA_ShopItem) is a primary data asset with an icon, tooltip, price and stock settings, and three optional payloads: an `EquippedEffect` (a Gameplay Effect applied once and kept for the match), a `ConsumedEffect` (applied when the item is used), or a `GrantedAbility` (an ability given on purchase and activated when the item is used). Each item sets exactly one. Skills and upgrades use the equipped effect, potions the consumed effect, and Nightflare a granted ability, which finds every enemy around the player and blinds them. The Asset Manager registers a "ShopItem" type, so the shop finds every item by type, like the hero definitions.

**Two rounds of checks** – the widget and `TryPurchase` check everything the client can know: the shop isn't closing, the item isn't owned, stock is left, souls are enough. A failure plays the reject sound and sends nothing. `Server_Purchase` then repeats the checks that matter, the phase and the souls, because the client's values could be stale or dishonest. Only the server pays, by subtracting the price from the Soul attribute, and only the server applies effects or grants abilities.

**Permanent or consumable** – the single branch in `Server_Purchase` is `bIsConsumable`. Permanent items never touch the inventory: the effect is applied to the hero's ASC and the item is remembered in `PurchasedItems`, so it can't be bought twice. Consumables go through `GrantItem` into the inventory grid instead.

**Answering the client** – the server replies with a Client RPC either way. `Client_SkillPurchased` confirms the purchase, and the widget's callback unlocks the next tier. `Client_PurchaseFailed` removes the optimistic local mark, so the item can be tried again, and plays the reject sound.

#### Why I designed it this way

- **Items as data** – a new potion or skill is one asset and one Gameplay Effect, no C++. The shop screen and purchase code never change.
- **Optimistic marking on the client** – marking an item owned before the server answers stops rapid double-clicks sending two purchases, without waiting a round trip. The failure RPC undoes it if the server disagrees.
- **The server owns souls** – souls are an attribute only the server modifies, and the purchase is a request. A client can't give itself items or skip the bill.
- **Same reject for every failure** – one sound for closed, unaffordable, owned or out of stock keeps the shop quick to read in the 60 seconds players have. Showing the reason is a UI improvement I'd add.

### Skill trees & ability upgrades

<figure class="diagram">
  <a href="../../diagrams/gas-skill-trees.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/gas-skill-trees.svg" alt="The four skill trees, Assassin, Gambler, Tank and Magician, three tiers each costing 20 to 50 souls, each tier locked until the one above is owned, with the attribute each skill sets. Below them the four ability upgrades at 50 souls each." /></a>
  <figcaption>Every skill is a switch on the hero's attribute set. The shop flips it; combat reads it.</figcaption>
</figure>

#### What it does

Twelve skills sit in four trees of three tiers: Assassin (stealth and attack power), Gambler (chance), Tank (health and heavy damage) and Magician (support and objectives). A tier can't be bought until the one above it is owned, and each skill costs between 20 and 50 souls, rising through the tree, so finishing a tree means committing to it. Four premium ability upgrades at 50 souls each give one heavy ability a unique twist: Bonebreaker for Smash, Shockwave for Stun, Scorched for Thrust and Deadeye for Shoot. All sixteen are bought once and last the match.

#### Step by step

| # | Step | Calls, in order | Runs on |
|---|---|---|---|
| 1 | Lock state | [`UpdateSkillLockStates`](code:UShopWidget::UpdateSkillLockStates): for each tree, tier 1 is open; tier n is locked unless tier n−1 is owned. [`UpdateAbilityUpgradeStates`](code:UShopWidget::UpdateAbilityUpgradeStates): never locked, only owned or not | Owning client |
| 2 | Purchase | The buying flow above; the server applies the item's `EquippedEffect` to the hero | Server |
| 3 | The effect sets an attribute | An infinite Gameplay Effect adds to one [`UChrisAttributeSet`](code:UChrisAttributeSet) attribute, e.g. `LoadedDiceActive = 1`, `HeavyAttackBuffDamage = 0.2` | Server, replicated |
| 4 | Relock | `Client_SkillPurchased` → [`OnSkillPurchasedCallback`](code:UShopWidget::OnSkillPurchasedCallback) → [`FindSkillIndices`](code:UShopWidget::FindSkillIndices) finds the tree and tier → the branch fills with the tree's colour and the next tier unlocks | Owning client |
| 5 | Combat reads it | Attack damage: [`MMC_LightAttackBuffDamage`](code:UMMC_LightAttackBuffDamage::CalculateBaseMagnitude_Implementation) and [`MMC_HeavyAttackBuffDamage`](code:UMMC_HeavyAttackBuffDamage::CalculateBaseMagnitude_Implementation). After a hit: [`PostGameplayEffectExecute`](code:UChrisAttributeSet::PostGameplayEffectExecute). Flags: [`GetActorCaptureWeight`](code:AFlag::GetActorCaptureWeight). Kills: `GAP_Dead` | Server |

#### How it works

**A skill is an attribute** – no C++ knows that Loaded Dice exists. Its asset points at a Gameplay Effect with infinite duration and one modifier, `LoadedDiceActive +1`. Buying it applies that effect to the hero's ASC and it stays there for the match. The combat code only ever asks the attribute set: is `LoadedDiceActive` above zero? What is `HeavyAttackBuffDamage`? The table below is the whole contract between the shop and combat.

| Skill | Attribute it sets | Read by |
|---|---|---|
| Bladed Edge, Juggernaut | `LightAttackBuffDamage`, `HeavyAttackBuffDamage` | The buff MMCs, while the damage is calculated |
| Fleetfoot, Iron Clad | `MoveSpeed`, `MaxHealth` | Movement and the health clamp |
| Double Down, Loaded Dice, Stealth Strike | `DoubleDownChance`, `LoadedDiceActive`, `StealthStrikeActive` | `PostGameplayEffectExecute`, attacker's side |
| Bulwark, Stasis Ward, Arcane Aegis | `DamageReduction`, `StasisWardReduction`, `HeavyDamageReduction` | `PostGameplayEffectExecute`, target's side |
| Stacked Odds | `StackedOddsChance` | `GAP_Dead`, when rewards are paid |
| Dominion | `DominionBonus` | `AFlag::GetActorCaptureWeight`, every frame in a zone |
| Bonebreaker, Shockwave, Scorched, Deadeye | `SmashDamageBonus`, `StunSweepRadius`, `ScorchedActive`, `DeadeyeActive` | The heavy abilities and the damage pipeline |

**The lock rule lives in the widget** – the shop keeps each tree as an ordered list of tiers. After every purchase it walks each list: tier 1 is always open, and each later tier is locked unless the previous one is owned. The upgrades have no prerequisite, so their widgets only switch between owned and available. The server does not currently check the order; that's on the improvement list.

**Cost per hit is negligible** – every hit reads a dozen attributes and runs a few branches. That's nanoseconds against a 16 ms frame, far below the sweep, montage and replication the same hit already pays for.

#### Why I designed it this way

- **Trees force a build** – with roughly 100 souls a round, finishing one tree means skipping the others. Higher prices further down each tree and the lock rule turn twelve skills into four playstyles.
- **Attributes instead of code** – adding a skill is a data asset, a Gameplay Effect and one attribute. Balancing it is editing a number in the effect. The shop and combat never change.
- **Switches, not handlers** – one damage function checks every switch in a fixed order. Scattering each skill into its own handler would hide that order, which matters: Stealth Strike applies before reductions, and burn damage skips every bonus.
- **Upgrades as premium flat purchases** – the four ability upgrades change how an ability feels rather than a number, so they sit outside the trees at one price.

### Inventory & consumables

<figure class="diagram">
  <a href="../../diagrams/gas-inventory.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/gas-inventory.svg" alt="Inventory in six jobs. Buying: the player's PC clicks, the server makes the item with a new handle, and the player's PC copies it under the same handle while its widget picks a slot. Both machines keep a map of handle to item. Using: a key press finds the handle in that slot and sends it to the server, the server uses the item, and the player's PC removes it or updates the stack." /></a>
  <figcaption>Six jobs, two copies of the inventory, and one handle number that both machines agree on.</figcaption>
</figure>

#### What it does

Potions bought in the shop go into a five-slot inventory. Buying the same potion again stacks it, up to three, and each potion can only be bought three times a match. In the arena a number key uses the potion in that slot: it applies its buff, the stack goes down by one, and an empty stack disappears. Nightflare works the same way from the player's side, but instead of a buff it sets off the blind bomb it granted when it was bought, blinding every enemy around the player.

#### Step by step

Six jobs, numbered as in the diagram. The first function in each row carries the job; the rest are helpers it calls.

| # | Job | Functions | Runs on |
|---|---|---|---|
| 1 | Click | [`TryPurchase`](code:UInventoryComponent::TryPurchase): souls, already owned, three bought this match → `Server_Purchase` | Owning client |
| 2 | Make it | [`GrantItem`](code:UInventoryComponent::GrantItem): a stack of this potion with room ([`GetAvailableStackForItem`](code:UInventoryComponent::GetAvailableStackForItem)) gets +1 ([`AddStackCount`](code:UInventoryItem::AddStackCount)); otherwise a new handle (`CreateHandle`), a new [`UInventoryItem`](code:UInventoryItem) ([`InitItem`](code:UInventoryItem::InitItem)) and `InventoryMap.Add`. Then pay and [`AddConsumablePurchase`](code:UInventoryComponent::AddConsumablePurchase) | Server |
| 3 | Show it | [`Client_ItemAdded`](code:UInventoryComponent::Client_ItemAdded_Implementation): the client makes its own copy under the same handle → `OnItemAdded` → the inventory widget picks the first free slot → [`ItemSlotChanged`](code:UInventoryComponent::ItemSlotChanged) | Owning client |
| 4 | Press a key | [`TryActivateItemInSlot`](code:UInventoryComponent::TryActivateItemInSlot): find the item in that slot → `Server_ActivateItem(handle)` | Owning client |
| 5 | Use it | [`Server_ActivateItem`](code:UInventoryComponent::Server_ActivateItem_Implementation): [`GetInventoryItemByHandle`](code:UInventoryComponent::GetInventoryItemByHandle) → [`IsOnCooldown`](code:UInventoryItem::IsOnCooldown)? → [`TryActivateGrantedAbility`](code:UInventoryItem::TryActivateGrantedAbility) → [`ConsumeItem`](code:UInventoryComponent::ConsumeItem): [`ApplyConsumeEffect`](code:UInventoryItem::ApplyConsumeEffect), [`ReduceStackCount`](code:UInventoryItem::ReduceStackCount) | Server |
| 6 | Remove it | Stack empty → `InventoryMap.Remove` → [`Client_ItemRemoved`](code:UInventoryComponent::Client_ItemRemoved_Implementation); stack left → `Client_ItemStackCountChanged` | Server, then owning client |

#### How it works

**Handles** – every inventory item gets an [`FInventoryItemHandle`](code:FInventoryItemHandle): a number from a counter that only goes up, so it never repeats. The inventory is a `TMap` from handle to item, which finds an item straight from its handle. The handle defines equality and a hash so it can be a map key.

**Two copies, one set of handles** – the inventory isn't replicated. The server keeps its own map, and the owning client keeps another, kept in step by Client RPCs that name items by handle: added, stack changed, removed. Only the server creates handles, so both maps always use the same numbers.

**Slots live on the client** – which slot an item sits in is decided by the inventory widget, which only exists on the player's machine. The server never knows slots. So pressing a key turns a slot into a handle on the client, and the handle is what crosses the network: the one name for an item that both machines share.

**Three limits** – a stack holds three; the grid holds five stacks; and each potion can be bought three times a match, so using one doesn't let you buy another. With five potion types and stacking, the grid can't fill up today; the capacity check is there for when more consumables are added.

**One use path for every consumable** – using an item is the same server function whether it holds a potion or Nightflare. The item asset decides what happens: a granted ability is activated, a consumed effect is applied. Nightflare's ability is granted when the item is created, so pressing its slot only has to activate it.

#### Why I designed it this way

- **Handles instead of pointers or slots** – a pointer is a memory address that means nothing on another machine, and the server doesn't know slots. A small number created by the server works on both.
- **Only the client knows slots** – slot order is presentation. Keeping it out of the server keeps the server's job to rules: does the item exist, is it on cooldown, use it.
- **Pay after granting** – `GrantItem` runs before the souls are taken, so a purchase that can't be placed never costs anything.
- **The item decides, not the inventory** – a new kind of consumable is a new asset with an effect or an ability; the inventory code doesn't change.


## The hit

### The life of a hit

<figure class="diagram">
  <a href="../../diagrams/gas-life-of-a-hit.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/gas-life-of-a-hit.svg" alt="The life of a hit in five stages, each condition coloured by the section that controls it. 1 Can I attack: weapon equipped tag, cost and cooldown, not stunned, combo window. 2 Where does it hit: melee socket sweep, projectiles and radius sweeps, hostile targets only, each hit once. 3 How hard: damage effect and MMC reading Attack Damage, stats and ability level, skill tree buffs, a damage effect per combo section. 4 How much is taken: Armour, Loaded Dice, Health clamped. 5 What happens next: knockback and death abilities, souls and XP for the killer." /></a>
  <figcaption>Every hit answers five questions, and each answer belongs to a different system.</figcaption>
</figure>

A hit isn't one system. Before any damage happens, several earlier systems have already had a say: the swords have to be out (Weapon equip), the ability has to be off cooldown (GAS foundations), and the hero can't be stunned. After it lands, the attacker's stats, level and skills decide how hard it is, the target's Armour decides how much is taken, and a kill pays out souls and XP that feed straight back into the shop and levelling.

The sections below follow a hit in order:

| Stage | Question | Section |
|---|---|---|
| 1–2 | Can I swing, and what did the sword touch? | [Melee combos & hit detection](#melee-combos--hit-detection) |
| 1–2 | The same for projectiles and area attacks | Ranged & area abilities |
| 3–4 | How much damage, after buffs and Armour? | The damage pipeline |
| 5 | Knockback, stun, death, souls and XP | Death, stun, knockback & rewards |

### Melee combos & hit detection

<figure class="diagram">
  <a href="../../diagrams/gas-melee.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/gas-melee.svg" alt="A melee combo in seven numbered steps. On the attacker's PC and the server: a key press starts the ability, which commits, slows the hero and plays the montage. On every machine the montage's AN_SendTargetGroup notify sweeps between sword sockets, skips the attacker, anyone already hit and anyone not hostile, plays local sparks and sends the hits in a gameplay event, even with no hits. On the server, StartCombo handles the first hit and starts the combo listeners; the combo window notify sets the next section when the right button is pressed in time; later hits arrive on ability.combo.damage. Every hit applies a damage effect with a spec and a context holding the hit. The table below lists every function." /></a>
  <figcaption>The montage decides when, the sword decides what was hit, and only the server decides that it counts.</figcaption>
</figure>

#### What it does

Every sword attack is a Gameplay Ability that plays an animation montage. Pressing the right button inside a short window chains the next swing, up to three in a row. The sword itself finds what it hit: at the moment of impact, a notify in the montage sweeps spheres between sockets placed along the blade, so a hit lands exactly where the player sees the sword. Teammates and the attacker are ignored, each enemy is hit once per swing, hit sparks play on every screen, and only the server turns the hits into damage.

Two ability classes do this. [`UStabAbility`](code:UStabAbility::ActivateAbility) runs most attacks, light and heavy, with its buttons and damage set per montage section in the Blueprint. [`UGA_Combo`](code:UGA_Combo::ActivateAbility) runs the three-part dual slash.

#### Step by step

The numbers match the diagram.

| # | Step | Calls, in order | Runs on |
|---|---|---|---|
| 1 | Press attack | [`HandleAbilityInput`](code:AChrisPlayerCharacter::HandleAbilityInput) → `AbilityLocalInputPressed(InputID)` starts the ability given with that button → `SendGameplayEventToActor` (input-pressed tag) locally, plus `Server_SendGameplayEventToSelf` so the server's copy hears the press too | Owning client → server |
| 2 | Start the swing | [`ActivateAbility`](code:UStabAbility::ActivateAbility): `K2_CommitAbility` (cost, cooldown) → walk speed 50 and the `SpeedOverride` loose tag → `PlayMontageAndWait` → `WaitGameplayEvent` listeners | Owning client (predicted) and server |
| 3 | Sweep the sword | [`AN_SendTargetGroup::Notify`](code:UAN_SendTargetGroup::Notify): `SphereTraceMultiForObjects` between each pair of sockets → skip the attacker, anyone already hit, anyone not Hostile → [`SendLocalGameplayCue`](code:UAN_SendTargetGroup::SendLocalGameplayCue) → `SendGameplayEventToActor` with the hits | Every machine |
| 4 | First hit | [`StartCombo`](code:UStabAbility::StartCombo) on `ability.stab.right`: push if set → `ApplyGameplayEffectToHitResultActor` for each hit → start the combo listeners | Server (damage), owning client and server (listeners) |
| 5 | Combo window | [`AN_SendGameplayEvent::Notify`](code:UAN_SendGameplayEvent::Notify) sends `ability.combo.change.<section>` → [`HandleComboChangeEvent`](code:UStabAbility::HandleComboChangeEvent) sets `NextComboName` (`.end` clears it) → press → [`HandleComboCommit`](code:UStabAbility::HandleComboCommit): window open and right button? → `Montage_SetNextSection` → the next section plays and step 3 repeats | Owning client (predicted) and server |
| 6 | Later hits | `ability.combo.damage` → [`HandleComboDamageEvent`](code:UStabAbility::HandleComboDamageEvent) (or [`DoDamage`](code:UGA_Combo::DoDamage) in GA_Combo) → this section's damage effect and push → [`PushTarget`](code:UChrisGameplayAbility::PushTarget) + apply | Server |
| 7 | Apply | [`ApplyGameplayEffectToHitResultActor`](code:UChrisGameplayAbility::ApplyGameplayEffectToHitResultActor): `MakeOutgoingGameplayEffectSpec` → `MakeEffectContext` + `AddHitResult` → `SetContext` → `ApplyGameplayEffectSpecToTarget` | Server |

#### How it works

**One ability, one montage** – each attack's montage holds every swing of its combo as named sections (combo01, combo02, combo03). `PlayMontageAndWait` starts at the first, and its four endings (completed, blended out, interrupted, cancelled) all end the ability, so an attack can never be left running. While it plays, the hero walks at 50. A loose `SpeedOverride` tag stops the anim instance from resetting the speed every frame. It isn't replicated because only the server and the attacker's PC move the hero; everyone else just receives the position.

**The montage talks to the ability through gameplay events** – a notify placed on the montage timeline sends a tagged gameplay event to its owner, and the ability waits for that tag with `WaitGameplayEvent`. Button presses use the same mechanism, so presses, combo windows and hits all reach the ability the same way. The combo tag carries the section name: [`HandleComboChangeEvent`](code:UStabAbility::HandleComboChangeEvent) splits `ability.combo.change.combo02` at the dots and keeps `combo02`. The listener is set up without requiring an exact match, so it hears every child tag, and [`GetNotifyName_Implementation`](code:UAN_SendGameplayEvent::GetNotifyName_Implementation) labels each notify on the timeline with that last word.

**The combo window** – `NextComboName` holds the section to jump to while the window is open and `NAME_None` while it's closed, so presses too early or too late do nothing. `ComboInputMap` says which button continues from each section, and the ability listens once per distinct button (a `TSet` removes duplicates, otherwise one press would be handled twice). `Montage_SetNextSection` doesn't cut the current swing short: it queues the next section to play when this one ends. The attacker's PC runs this straight away, and the server runs it too because the press was also sent as a Server RPC in step 1.

**The sword finds the hit** – every attack animation has sockets along the blade (three for light attacks). [`AN_SendTargetGroup`](code:UAN_SendTargetGroup::Notify) slides a sphere (radius 35, or an attribute for smash and stun) from each socket to the next, on the frame it fires, so it covers a capsule along the blade wherever the sword is at that moment, including any turning since the swing began. It only looks for characters, ignores the attacker, keeps only targets whose team is Hostile, and records each actor it accepts in a `TSet`, so an enemy touched by two sweeps (they overlap at the middle socket) is hit once. The roll into double slash has two notifies, one per sword, so an enemy caught by both blades takes two hits.

**A miss still sends the event** – the hits are sent once, after the sweeps, whether or not anything was hit. That matters for the first swing: Stab only sets up its combo listeners in `StartCombo`, which runs on the first hit event. If the event only came on a hit, swinging at thin air would leave the combo with nobody listening, and the player couldn't press on into the second swing.

**Every machine sweeps, only the server damages** – notifies fire wherever the montage plays, and the montage is replicated, so every machine runs the sweep. Each one plays the hit sparks itself as a local gameplay cue, which costs nothing on the network. Only the server's copy of the ability listens for the hit events (`K2_HasAuthority`), so a client's sweep can never cause damage.

**Damage per section** – each section of a Stab montage has its own entry in `ComboDamageMap`: a damage effect and a push. A finisher can hit harder and launch further than the first swing without any new code. GA_Combo's `DamageEffectMap` does the same, with a default effect for sections it doesn't list.

**Spec and context** – the damage effect is the rule, made in the editor. [`ApplyGameplayEffectToHitResultActor`](code:UChrisGameplayAbility::ApplyGameplayEffectToHitResultActor) fills in a spec (the effect at this ability's level), attaches a context (who caused it, with which ability, and where it hit) and applies it to the target. The context is what lets the target's attribute set know who hit it, which Loaded Dice and Stealth rely on.

**Links to other sections**

- **Weapon equip** – every attack requires the `stats.weapon.equipped` tag, so nothing here runs with the swords away.
- **GAS foundations** – step 1 depends on abilities given with input IDs, and `K2_CommitAbility` uses the cooldowns set up there. Every ability is blocked while the hero has the stun tag.
- **Attributes & levelling** – the ability's level goes into the spec, so damage effects can scale with upgrades.
- **The damage pipeline** – what the damage effect does once it reaches the target: Attack Damage, Armour and skill buffs.
- **Ranged & area abilities** – smash and stun reuse Stab and this sweep, with the radius read from an attribute.
- **Death, stun, knockback & rewards** – [`PushTarget`](code:UChrisGameplayAbility::PushTarget) sends the target a launch event that its own launched ability carries out.

#### Why I designed it this way

- **The sword decides the hit** – sockets on the blade follow the animation exactly, so hits match what players see, and a new attack needs sockets rather than hand-made hitboxes.
- **Timing lives in the montage, rules live in C++** – the combo window and the moment of impact are notifies placed on the timeline, so I can retime an attack in the editor without touching code, and the section names travel inside the tags.
- **One way to talk to abilities** – presses, combo windows and hits are all gameplay events, so an ability only needs `WaitGameplayEvent` to react to any of them.
- **Trust the server, not the client, but don't make the client wait** – the attacker's PC plays the swing and the next section straight away (prediction), the server decides what the hits do, and sparks are local because they're only cosmetic.
- **Combos as data** – in Stab, a new combo is montage sections plus map entries in the Blueprint. GA_Combo is the older hard-coded version, and I'd move the dual slash onto Stab.

### Ranged & area abilities

<figure class="diagram">
  <a href="../../diagrams/gas-ranged.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/gas-ranged.svg" alt="Four ranged and area abilities side by side, each with four numbered steps coloured by the machine that runs them. Shoot: hold aim activates without paying, RT makes the server spawn a projectile carrying the hit spec, every machine moves it and the server applies the spec on overlap, and the third shot pays mana and starts the cooldown. Thrust: commit and wait for the start event, a speed effect from the server plus forward input on the attacker's PC, a detection sphere on a socket, and the server launches, damages and burns each enemy. Smash and stun: a radius effect at the ability level sets the radius attribute, the hit notify sweeps with it, the impact slows the caster and starts the VFX effect, and the server skips airborne targets before pushing and applying the effect. Nightflare: using the item activates the granted ability, which overlaps a 240 radius sphere, filters targets and applies the blind effect. Below, an in-match upgrade raises the ability level, which every spec reads for radius, damage, stun length, VFX length, thrust speed and shoot cooldown. Links: the shop, levelling and melee feed in; the AI, the damage pipeline and knockback read from it." /></a>
  <figcaption>Four abilities, four ways of finding targets, and one ability level that scales them all.</figcaption>
</figure>

#### What it does

Every hero has the same four heavy abilities alongside their sword combos. **Shoot** raises the hero's arm to aim and fires a volley of three projectiles. **Thrust** dashes the hero across the arena, launching and damaging every enemy in the way. **Smash** and **stun** slam the sword into the ground, hitting every grounded enemy in a circle (stun also stops them using abilities for a while), and players can jump to dodge them. Premium upgrades from the shop make these four stronger (Scorched adds a burn to Thrust, Deadeye changes Shoot's projectile), and **Nightflare**, a consumable from the shop, blinds every enemy close to the player when it's used.

All four abilities grow as they're upgraded during the match: a bigger radius, more damage, a longer stun, faster dashes, shorter cooldowns. Each one also obeys the same rules as melee: only Hostile characters are hit, each target once, and only the server decides what a hit does.

#### Step by step

The numbers match the diagram.

| Ability | # | Step | Calls, in order | Runs on |
|---|---|---|---|---|
| Shoot | 1 | Hold aim | [`ActivateAbility`](code:UGA_Shoot::ActivateAbility): swords must be away, GAS checks the mana cost can be paid, aim montage, listeners for release and RT. No commit yet | Owning client (predicted) and server |
| | 2 | Press RT | [`ShootProjectile`](code:UGA_Shoot::ShootProjectile): on cooldown? less than 0.15 s since the last shot? → shoot montage → server `SpawnActor` at the `ProjectileSpawn` socket → [`AProjectileActor::ShootProjectile`](code:AProjectileActor::ShootProjectile) with speed, range, team and the hit spec | Owning client and server; spawn on the server |
| | 3 | Fly and hit | [`Tick`](code:AProjectileActor::Tick) moves it on every machine → [`NotifyActorBeginOverlap`](code:AProjectileActor::NotifyActorBeginOverlap): Hostile with an ASC? → server `ApplyGameplayEffectSpecToSelf` on the target → impact VFX → `Destroy` | Every machine; damage on the server |
| | 4 | Third shot | `CommitAbilityCost` → `CommitAbilityCooldown` (forced) → `AbilityCommittedCallbacks.Broadcast` for the cooldown gauge | Owning client (predicted) and server |
| Thrust | 1 | Start | [`ActivateAbility`](code:UThrust::ActivateAbility): `K2_CommitAbility` → `PlayMontageAndWait` → wait for `ability.heavyattack2.start` | Owning client (predicted) and server |
| | 2 | Dash | [`StartThrust`](code:UThrust::StartThrust): server applies `ThrustEffect` (speed) → owning client starts [`PushForward`](code:UThrust::PushForward), adding forward input every frame | Server (speed), owning client (input) |
| | 3 | Detect | `WaitTargetData` → `BeginSpawningActor` → [`ConfigureDetection`](code:ATargetActor_Around::ConfigureDetection) → `FinishSpawningActor` → attach to `TargetThrustCenter` → [`ActorInDetectionRange`](code:ATargetActor_Around::ActorInDetectionRange) for each new Hostile enemy | Owning client and server; targets reported by the server |
| | 4 | Hit | [`TargetReceived`](code:UThrust::TargetReceived): `LaunchCharacter` away from the hero → `DamageEffect` → `BurnEffect` if Scorched is owned. [`EndAbility`](code:UThrust::EndAbility) removes the speed and stops the input | Server |
| Smash & stun | 1 | Set the radius | [`ActivateAbility`](code:UStabAbility::ActivateAbility): `RadiusSweepEffect` at the ability level → `SmashSweepRadius` / `StunSweepRadius` | Owning client (predicted) and server |
| | 2 | Impact sweep | [`AN_SendTargetGroup::Notify`](code:UAN_SendTargetGroup::Notify) sweeps with the radius attribute → `ability.stab.right` with the hits | Every machine |
| | 3 | Impact | [`StartCombo`](code:UStabAbility::StartCombo): walk speed 15 → caster sound → `VFXDurationEffect` | Owning client and server; effect on the server |
| | 4 | Damage | Skip anyone falling → `PushTarget` → `ApplyGameplayEffectToHitResultActor` with `StabDamageEffect` | Server |
| Nightflare | 1 | Use the item | [`Server_ActivateItem`](code:UInventoryComponent::Server_ActivateItem_Implementation) activates the granted ability → [`ActivateAbility`](code:UGA_BlindBomb::ActivateAbility): `K2_CommitAbility` | Server |
| | 2 | Overlap | `OverlapMultiByObjectType`: a sphere of radius 240 at the player | Server |
| | 3 | Filter | Skip the player, anyone already blinded, anyone not Hostile | Server |
| | 4 | Blind | `ApplyGameplayEffectSpecToTarget` with one blind spec for every target → the blind cue plays on each target's screen | Server; cue on each target's PC |

#### How it works

**Four ways to find a target, one set of rules** – melee sweeps the sword's sockets. These abilities find targets four other ways: a flying projectile, a sphere carried with the hero, a bigger sweep at the impact point, and an instant overlap around the player. However the targets are found, the same filters follow: never the attacker, each target once (a `TSet` of actors already hit), and only characters whose team is Hostile.

**Shoot: pay late, check early** – most abilities pay their mana and start their cooldown the moment they activate. Shoot activates when the player starts aiming, but [`CheckCooldown`](code:UGA_Shoot::CheckCooldown) is overridden to always pass, so the arm can always be raised. The cooldown is checked per shot instead. The mana is paid on the third shot, together with the cooldown, so a player who keeps their last shot keeps their volley, but the cooldown doesn't start until it's fired. That doesn't let a player with no mana fire for free: before any ability activates, GAS checks its cost can be paid at its current level, so a volley the player can't afford can't even be aimed. The shot count lives on the ability (one instance per hero), so it survives letting go of aim, and [`ResetShootState`](code:UGA_Shoot::ResetShootState) clears it at every round reset, along with the Deadeye counter. Because the cooldown starts late, the ability announces its own commit (`AbilityCommittedCallbacks.Broadcast`) so the HUD's cooldown gauge still starts.

**The projectile is flown by every machine** – only the server spawns it (otherwise there'd be one per machine), and it's a replicated actor, so it appears for everyone. It replicates only its direction, speed and team, not its position every frame: each machine starts it at the same socket and moves it with the same maths each frame (position + direction × speed × frame time), which keeps players in agreement for very little bandwidth. Its direction comes from where the shooter is looking (`GetActorEyesViewPoint`), so it flies towards the crosshair rather than the way the body faces. Its range is a timer (distance ÷ speed), and the hit spec, made by the ability at its level, travels inside it. On impact the target applies that spec to itself, which keeps the shooter in the effect's context.

**Thrust holds the stick instead of setting the speed** – when a player moves, their PC moves them straight away and sends the server a record of the input. The server replays that input to check the result, and if its answer is different it sends a correction that snaps the player back (rubber-banding). [`PushForward`](code:UThrust::PushForward) adds forward input every frame on the attacker's PC, exactly like holding the stick forward, so the input goes into that record and the server reaches the same position. Setting the hero's velocity directly on their PC would never reach the server's replay, so the server would correct the dash away. The speed itself comes from `ThrustEffect`, a gameplay effect the server applies to the hero, so both machines agree on how fast "forward" is.

**A target actor that travels with the hero** – Thrust finds enemies with [`ATargetActor_Around`](code:ATargetActor_Around::ActorInDetectionRange), my child of GAS's target actor class: an actor whose only job is finding targets and reporting them to an ability. The ability task `WaitTargetData` creates it and calls [`TargetReceived`](code:UThrust::TargetReceived) whenever it reports. It's created in two steps: `BeginSpawningActor` makes it without switching it on, [`ConfigureDetection`](code:ATargetActor_Around::ConfigureDetection) sets its radius, team and hit cue, and only then does `FinishSpawningActor` switch it on. Switched on any earlier, it could detect someone before it knew its size or team. It's then attached to a socket on the hero's mesh, so it dashes with them, and it's removed automatically when the ability ends. Only the server's copy reports targets, and every copy plays the hit sparks locally.

**Pushing away from the hero** – the push direction is the target's position minus the hero's position, which gives an arrow pointing from the hero to the target. With the hero at (0, 0) and the target at (3, 4), that's (3, 4). `GetSafeNormal` shrinks it to length 1 while keeping its direction, (0.6, 0.8), so a target further away isn't launched harder, and multiplying by the push speed gives the launch. Melee and smash push through `PushTarget`, which asks the target's own launched ability to do it, so the push follows the same GAS rules as every other ability. Thrust currently calls `LaunchCharacter` directly, which skips those rules; I'd move it onto `PushTarget` so every attack knocks back the same way, and future hit reactions apply to all of them.

**Smash and stun are the same code with different effects** – both are Stab Blueprints with the area settings filled in. The only difference is the gameplay effect plugged into their damage setting: smash's takes health, and stun's also gives the target the stun tag for a duration. Every ability lists that tag as blocking, so a stunned hero can't use any ability until the effect ends. Stun isn't code at all; it's an effect asset.

**The radius is an attribute** – on activation, the ability applies `RadiusSweepEffect` to the hero, which sets `SmashSweepRadius` or `StunSweepRadius` from a curve table at the ability's level. The hit notify on the impact reads that attribute instead of its default 35. The attribute replicates to every player because every machine runs the notify (for the hit sparks), so every machine needs the same radius. My skeleton AI reads the same attribute in [`CheckForAoEDanger`](code:UBTService_CheckCombatMode::CheckForAoEDanger): when a player starts a heavy attack, skeletons inside that radius run out of it, and those just outside stop advancing.

**Jumping dodges the ground** – before any push or damage, the server skips every target whose movement is falling, so a player in the air at the moment of impact isn't hit. The check comes before the push on purpose: pushing first would launch players who had dodged. On impact the caster also slows to 15 (planted by the swing), hears a 2D sound only they get, and gains `VFXDurationEffect`, a duration-only effect whose gameplay cue is the looping stun VFX. A cue attached to an effect starts when the effect is applied and stops when it ends, and it replicates with the effect, so everyone sees the VFX for exactly as long as it lasts.

**One level, every number** – abilities are upgraded during the match with upgrade points from levelling ([`Server_UpgradeAbilityWithID`](code:UChrisAbilitySystemComponent::Server_UpgradeAbilityWithID_Implementation)). Every effect these abilities apply is made with the ability's current level, and every number in those effects is a curve-table value read at that level: the smash radius, the damage, the stun's length, the VFX's length, Thrust's speed and Shoot's cooldown. Upgrading an ability changes one number, and the next use reads the next row of every table. Balancing a level means editing a curve table, not code.

**Nightflare: an overlap, not a sweep** – a sweep moves a shape from one point to another. An overlap asks what is inside a shape right now. Nightflare is instant, so [`UGA_BlindBomb`](code:UGA_BlindBomb::ActivateAbility) overlaps a sphere of radius 240 at the player, on the server, and ends straight away. It makes the blind spec once and applies the same spec to every Hostile character inside, which is cheaper than one per target and fine because they all get the same blind. It uses level 1 on purpose: it's a shop item, so it never levels up. The blind effect replicates to each target, and its cue darkens that player's own screen until it ends.

**Links to other sections**

- **The shop** – Nightflare is a shop item with a granted ability, and Scorched (Thrust's burn) and Deadeye (Shoot's different projectile and hit effect) are premium upgrades that switch on a flag attribute these abilities read.
- **Attributes & levelling** – upgrade points from levelling raise ability levels, which every effect here reads.
- **Melee combos & hit detection** – smash and stun are Stab abilities using the same hit notify, the same first-hit function and the same apply helper.
- **The damage pipeline** – every damage effect these abilities apply.
- **Death, stun, knockback & rewards** – the stun tag, `PushTarget` and the launched ability.
- **AI** – skeletons read the smash and stun radius to get out of the way.

#### Why I designed it this way

- **Pay late, check early** – a player can keep their last shot without losing the volley, but can never start a volley they can't pay for.
- **Every machine flies the projectile** – replicating three values once is far cheaper than streaming a position every frame, and only the server's overlap decides the damage.
- **Move with input, not velocity** – the dash goes through the same predicted movement as walking, so it never rubber-bands.
- **Effects as data** – stun, burn, blind and Deadeye are effect assets, not code. Changing what an ability does, or how long it lasts, happens in the editor.
- **One number to scale everything** – every effect reads the ability level from a curve table, so balancing is spreadsheet work.
- **Counterplay** – jumping dodges smash and stun, and the AI reads the same radius players can see, so the same rule teaches both.

### The damage pipeline

<figure class="diagram">
  <a href="../../diagrams/gas-damage.svg" target="_blank" rel="noopener" title="Open full size"><img src="../../diagrams/gas-damage.svg" alt="The damage pipeline in seven numbered steps. Stage one, worked out before Health changes: 1, the ability makes the spec with its level and a context saying who, which ability and where; 2, an MMC captures the attacker's and target's attributes and works out the base: light attacks use Attack Damage times the light bonus times the armour factor, heavy attacks use a curve value at the ability level times the heavy bonus, and the base MMC adds a Double Down roll. Armour blocks Armour over Armour plus 100. 3, GAS adds the negative number to Health, PreAttributeChange clamps it, and HealthUpdated fires; at zero it starts death before stage two has run. Stage two, in PostGameplayEffectExecute on the target: 4, undo damage after the round, ignore heals, note burn ticks and find the attacker from the context; 5, attacker bonuses Loaded Dice, Stealth Strike, Blood Serum, Bonebreaker and Deadeye multiply on top; 6, the target's reductions Arcane Aegis, Stasis Ward, Bulwark and Warden's Phial multiply into one heal-back; 7, clamp Health, cache the health percentage for rescaling, and credit the attacker's damage dealt. Links: melee and ranged hits, skill and shop attributes and levelling feed in; death, match stats, health bars and rescaling read from it." /></a>
  <figcaption>Two stages: an MMC works out the base before Health changes, then the target's attribute set adds the bonuses and reductions.</figcaption>
</figure>

#### What it does

Every hit, from a sword, a projectile, a dash or a smash, ends here. The attacker's Attack Damage and skills meet the target's Armour and defences, and one number comes off the target's Health. Light attacks grow with the attacker's stats; heavy abilities grow with the ability's level. Armour gives diminishing returns, so no hero becomes unkillable. Bonuses from skills and potions, and reductions from the target's own skills and potions, all multiply, so stacking them is strong but never overpowered. The attacker is credited with the damage they really dealt, for the end-of-match stats.

#### Step by step

The numbers match the diagram. Everything here runs on the server; Health then replicates to every player.

| # | Step | Calls, in order | Where |
|---|---|---|---|
| 1 | Make the spec | [`ApplyGameplayEffectToHitResultActor`](code:UChrisGameplayAbility::ApplyGameplayEffectToHitResultActor): `MakeOutgoingGameplayEffectSpec` (effect + ability level) → `MakeEffectContext` + `AddHitResult` → `ApplyGameplayEffectSpecToTarget` | The attacker's ability |
| 2 | Base damage | The effect's modifier asks its MMC. Constructor: capture definitions (Attack Damage from the Source, Armour from the Target) → [`MMC_LightAttackBuffDamage`](code:UMMC_LightAttackBuffDamage::CalculateBaseMagnitude_Implementation), [`MMC_HeavyAttackBuffDamage`](code:UMMC_HeavyAttackBuffDamage::CalculateBaseMagnitude_Implementation) or [`MMC_BaseAttackDamage`](code:UMMC_BaseAttackDamage::CalculateBaseMagnitude_Implementation): `GetCapturedAttributeMagnitude` → formula → negative number × the effect's Coefficient | The MMC |
| 3 | Health changes | GAS adds the magnitude to Health → [`PreAttributeChange`](code:UChrisAttributeSet::PreAttributeChange) clamps it → [`HealthUpdated`](code:UChrisAbilitySystemComponent::HealthUpdated) fires (at 0: death effect and dead event) | The target's attribute set and ASC |
| 4 | Who and what | [`PostGameplayEffectExecute`](code:UChrisAttributeSet::PostGameplayEffectExecute): round over and immune → undo → damage only → burn tick? (`damage.type.dot`) → `GetContext().GetEffectCauser()` → the attacker's ASC | The target's attribute set |
| 5 | Bonuses | Loaded Dice → Stealth Strike → Blood Serum → Bonebreaker → Deadeye: each reads the attacker's attributes, `SetHealth` takes the extra, and the running magnitude grows | The target's attribute set |
| 6 | Reductions | Arcane Aegis → Stasis Ward → Bulwark → Warden's Phial: multiplied into one value → one heal-back with `SetHealth` | The target's attribute set |
| 7 | Clamp, remember, credit | `SetHealth(Clamp(...))` → `SetCachedHealthPercent` → [`AddDamageDealt`](code:AChrisGameState::AddDamageDealt) on the Game State | The target's attribute set |
| – | Max Health changes later | [`MaxHealthUpdated`](code:AChrisCharacter::MaxHealthUpdated) → [`RescaleHealth`](code:UChrisAttributeSet::RescaleHealth): MaxHealth × the cached percentage | The character |

#### How it works

**An MMC works out one number** – a Modifier Magnitude Calculation is a small class a gameplay effect asks "how big is this?" when it's applied. In its constructor, each MMC writes capture definitions: which attribute it needs and from which side, the **Source** (the attacker) or the **Target** (the one being hit). It adds them to `RelevantAttributesToCapture` so GAS gathers those values from both ability system components when the effect lands. In `CalculateBaseMagnitude_Implementation` it reads them with `GetCapturedAttributeMagnitude`, works out the damage and returns it as a **negative** number, because the effect adds it to Health.

**Light attacks scale with stats** – [`MMC_LightAttackBuffDamage`](code:UMMC_LightAttackBuffDamage::CalculateBaseMagnitude_Implementation) returns Attack Damage × (1 + the light bonus) × (1 − Armour ÷ (Armour + 100)). The light bonus is an attribute on the attacker: 0 normally, 0.1 with Bladed Edge. The skill doesn't need a tag check, because only effects built with this MMC read it.

**Heavy abilities scale with their level** – a modifier using an MMC has a **Coefficient** box, and the final number is Coefficient × what the MMC returns. My heavy damage effects put their damage in the Coefficient, as a curve-table value read at the ability's level, and [`MMC_HeavyAttackBuffDamage`](code:UMMC_HeavyAttackBuffDamage::CalculateBaseMagnitude_Implementation) returns only the multiplier, 1 + the heavy bonus (1.2 with Juggernaut). So the two kinds of bonus come from different places: the **Coefficient** belongs to the effect and changes with the ability's level, while the **light and heavy bonuses** belong to the attacker and change when a skill is bought.

**Armour gives diminishing returns** – Armour ÷ (Armour + 100) is the share blocked: 50 Armour blocks 33%, 100 blocks 50%, 200 blocks 67%. Every point helps a little less than the one before, and the result can never reach 100%.

**Double Down** – the 20% chance of ×1.3 is rolled inside [`MMC_BaseAttackDamage`](code:UMMC_BaseAttackDamage::CalculateBaseMagnitude_Implementation). It's safe to roll random numbers there because damage effects are only applied on the server, so one machine rolls and everyone gets the result.

**Stats grow without touching the pipeline** – [`MMC_LevelBased`](code:UMMC_LevelBased::CalculateBaseMagnitude_Implementation) isn't part of a hit. It belongs to an infinite effect applied once at setup, which captures the hero's Level live, so GAS recalculates it whenever Level changes. The growth lands in Attack Damage, Armour and the rest, and every hit just reads their current values.

**Stage two runs on the target, after Health has changed** – GAS calls [`PostGameplayEffectExecute`](code:UChrisAttributeSet::PostGameplayEffectExecute) on the target's attribute set after an instant effect changes one of its attributes. It receives a record of what happened: which attribute, by how much (`EvaluatedData.Magnitude`), and the spec that did it. The spec's context says who caused it (`GetEffectCauser`), which gives the attacker's ability system component, so the bonuses can read the **attacker's** skills while the reductions read the **target's own**.

**Damage types are tags I check myself** – my damage effects carry asset tags: `damage.type.heavy`, `.smash`, `.projectile` and `.dot`. GAS has its own way to make a modifier depend on tags, but I read these in C++ instead (`Def->InheritableGameplayEffectTags`), which lets each skill decide exactly which hits it affects: Bonebreaker only boosts smash, Deadeye only projectiles, Arcane Aegis only reduces heavy damage. DoT means damage over time: Scorched's burn ticks from Thrust, the only DoT in the game. Burn ticks skip the bonuses, so one Thrust can't roll Loaded Dice or Stealth Strike on every tick.

**Bonuses multiply** – each bonus is a percentage of the damage **including** the bonuses before it. The running total is `Magnitude`, which is negative, so making the damage bigger means subtracting: −33 − 9.9 = −42.9. `Abs` gives the size without the sign whenever a percentage is needed. Loaded Dice and Stealth Strike together give 1.3 × 1.4 = ×1.82, more than the +70% that adding them would give, so stacked bonuses grow faster than their parts, and the order of the bonuses doesn't change the result. Loaded Dice's and Deadeye's hit counters are attributes on the attacker, so they count that player's hits across every enemy.

**Reductions multiply into one heal-back** – the target's reductions are multiplied into a single value starting at 1: two 20% reductions give 0.8 × 0.8 = 0.64, so 36% off, never stacking to 100%. The damage the target is spared is then given back in one `SetHealth`.

**Keeping the percentage when max Health changes** – after every hit, `CachedHealthPercent` saves Health ÷ MaxHealth. When MaxHealth changes (a level-up, or Iron Clad's +100 at the start of a round), [`MaxHealthUpdated`](code:AChrisCharacter::MaxHealthUpdated) calls [`RescaleHealth`](code:UChrisAttributeSet::RescaleHealth), which sets Health to the new maximum × the saved percentage. A hero on 50 of 100 who levels up to 120 max goes to 60, still half health, instead of the bar dropping to 42%. The percentage has to be saved beforehand, because once MaxHealth has changed, Health ÷ MaxHealth gives the new, wrong percentage. A dead hero (0%) is never rescaled back to life.

**Credit for the real damage** – the difference between Health before and after the hit, after every bonus, reduction and clamp, is added to the attacker's `DamageInflicted` in the Game State's match stats, unless they hurt themselves.

**Links to other sections**

- **Melee combos & hit detection, Ranged & area abilities** – every hit reaches step 1 through `ApplyGameplayEffectToHitResultActor`, a projectile's spec or a target-data apply, always with the ability's level.
- **Skill trees & ability upgrades, the shop** – Bladed Edge, Juggernaut, Double Down, Loaded Dice, Stealth Strike, Bonebreaker, Deadeye and the defensive skills are all flag or bonus attributes read here. Blood Serum and Warden's Phial are potion effects.
- **Attributes, XP & levelling** – Attack Damage, Armour and MaxHealth grow with level through `MMC_LevelBased`, and `PreAttributeChange` is the clamp described there.
- **Death, stun, knockback & rewards** – `HealthUpdated` starts death when Health reaches 0. Stasis Ward reads the stun tag.
- **The gameplay framework** – the Game State keeps the match stats `AddDamageDealt` writes to.

#### Why I designed it this way

- **Two stages** – the MMC handles the maths every hit shares (stats against Armour), and the attribute set handles the conditional rules (who owns which skill, which way the attacker faces, which kind of hit). Each rule lives in one place.
- **Skills as attributes** – buying a skill sets an attribute through an effect, and the pipeline reads it. No hit has to ask the shop what a player owns.
- **Multiplying reductions** – each reduction takes a share of what's left, so stacking them always helps but can never reach 100%, and no hero becomes immune.
- **Diminishing returns on Armour** – Armour always helps, never makes a hero immune, and a single formula works at every level.
- **Data for the numbers** – damage per ability level lives in curve tables, so balancing is spreadsheet work, not code.

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

- **Sweep every frame, not on one frame** – each hit notify checks where the blade is on a single frame, so a very fast swing can pass an enemy between frames. An anim notify state that sweeps every tick, from last tick's socket positions to this tick's, with one hit list for the whole window, would catch everything the blade passes through.
- **Stop projectiles on walls** – projectiles only collide with characters, so they fly through walls. They should stop on level geometry, play their impact effect and do no damage.
- **One push path** – Thrust launches targets directly while every other attack uses `PushTarget`. Moving Thrust onto `PushTarget` means knockback rules, and any future hit reactions, apply to every attack.
- **Change Health once per hit** – damage effects change Health directly, so death is judged the moment the base damage lands, before bonuses and reductions run. A hero on 35 Health with a 20% reduction, hit for 40, should survive on 3 (40 × 0.8 = 32); instead Health hits 0, death starts, and the reduction then heals 8 back onto a dying hero. An unreplicated `IncomingDamage` meta attribute fixes it: damage effects write to it instead of Health, every bonus and reduction is applied to that one number, and Health changes once, so death is judged on the final value and the damage credit is exact, even on overkill.
- **Armour against heavy abilities** – heavy damage is the curve value × the heavy bonus, so it ignores Armour. Capturing Armour in the heavy MMC makes every attack respect it.
- **Double Down on combo hits only** – its roll lives in the base MMC, so it follows whichever effects use that MMC, while the skill promises combo hits. Tagging the follow-up combo effects and rolling it in stage two would tie it to the hits it describes, and let the base MMC go.
- **Add bonuses inside one bucket** – stage-two bonuses multiply, so they grow faster than their parts: Loaded Dice, Stealth Strike, Blood Serum and Deadeye together reach ×6.6 on a third shot, while reductions shrink towards a limit. Adding the bonuses (×1 + 0.3 + 0.4 + 0.2 + 2 = ×3.9) or capping the total would keep stacked damage in check, while reductions keep multiplying.
- **One combo class** – `UGA_Combo` hard-codes its buttons, while `UStabAbility` reads them from data. I'd move the dual slash onto Stab and delete GA_Combo.
