---
doc_id: 86e7f98271e5db6a
source: fandom
game: onmyoji
url: https://onmyoji.fandom.com/wiki/Adjustments
title: "Untitled"
language: zh
word_count: 167140
quality_score: 0.5
crawl_ts: 2026-09-21T09:01:50.145082+00:00
---
This a complitation of implemented adjustments for onmyoji/shikigami skills and soul effects. All the dates listed are sorted by when they were implemented on GL server. If no date for GL server is available, then the next latest date for when they were inplemented on TW/JP or CN servers will be listed instead.

The following adjustments occurred on May 26th, 2026 for CN servers.

- **River Water** Skill Adjustment:
  - Adjusted to: Summons a rushing stream to strike the enemy, dealing damage equal to 80% of ATK to the target and dispels 1 buff. When an ally takes a single instance of enemy damage exceeding 30% of their max HP, the damage source receives 3 stacks of Grudge.
- **Ride Wave** Skill Adjustments:
  - Adjusted to: After an enemy turn ends, gains 1 stack of Focus. If she does not have Spiritfish Shield, gains a Spiritfish Shield equal to 80% of ATK.
  - Upper Hand: Gains 4 stacks of Focus.
  - Spiritfish Shield: [Buff, Mark] Absorbs a certain amount of damage and cannot be dispelled.
- **Goldfish's Embrace** Skill Adjustments:
  - Adjusted to: Unique effect. Applies 3 stacks of Grudge to an enemy target and activates Fishtail Cluster for 1 turn. Upon activation, raises all allies' Move Bar by 10% and gains 1 stack of Surge. During the duration, when an enemy gains a single-target Move Bar boost or single-target acceleration effect, gains 1 stack of Surge. After an ally turn ends, if she is still able to act, heals them for 50% of ATK and triggers Surge.
  - Surge: Max 3 stacks. Each stack deals 50% of ATK as Indirect Damage to 1 random enemy, prioritizing different enemies. Each trigger increases the damage factor by 3%, up to a maximum of 80%.
  - **Lv. 2** : Surge deals 150% damage to targets with Grudge
  - **Lv. 3** : During Fishtail Cluster, non-critical damage taken by allies is reduced by 30%, and by an extra 30% for herself
- **Grudge** Effect Adjustment:
  - Adjusted to: [Debuff, Mark] Max 3 stacks. During Fishtail Cluster, Surge prioritizes the bearer, dealing damage equal to 100% of Seawatch Kingyo's ATK and consuming 1 stack of Grudge.
- Reminder
  - When Seawatch Kingyo appears as a monster, these balance adjustments do not affect her skills.

- **Feathering** Skill Adjustments
- Adjusted to: Unique effect. At the start of battle and after her turn ends, gains 1 stack of Feathers. At the start of her turn, if Feathers has reached 5 stacks, consumes all stacks and enters Display Stance for 3 turns, then gains 1 stack of Feathers when the duration ends.
  - **Lv. 4** : When gaining Feathers, dispels 1 debuff from all allies
  - **Lv. 5** : While in Display Stance, every 1% of Effect HIT she has increases her ATK by 1%
- **Feathers** Effect Adjustment:
  - Adjusted to: [Buff, Mark] Max 5 stacks. Each stack increases her Effect HIT by 15%, and at max stacks, increases her SPD by 50%.
- **Alluring Realm** Skill Adjustments:
  - Adjusted to: Unique effect. Creates a Plume Field for 2 turns and gains 1 stack of Feathers. Enemies inside the Plume Field have their Effect RES reduced by 30% and deal 30% less single-target damage. While in Display Stance, this skill is replaced with Jaku Dance, and its level scales with Alluring Realm.
  - **Lv. 2** : On cast, there is a 40% base chance to inflict disarm on all enemies for 1 turn
  - **Lv. 3** : When the non-summoned entity ally with the lowest HP in the Realm takes damage, there is a 40% base chance to inflict Disarm on the damage source for 1 turn
  - **Lv. 4** : Reduces damage she takes in the Plume Field by 30%
  - **Lv. 5** : Upper Hand: Creates a Plume Field for 2 turns
- **Jaku Dance** Skill Adjustment:
- Adjusted to: Attacks all enemies 4 times, each hit dealing damage equal to 45% of ATK; then follows with 2 additional slashes, each dealing damage equal to 45% of ATK. Each attack has a 100% base chance to inflict Disarm for 2 turns. After entering Display Stance, the first cast doubles the number of attacks.
- Reminder
  - When Kujaku-Myoo appears as a monster, these balance adjustments do not affect her.

- Base Stat Adjustment
  - Initial Crit DMG is adjusted from 130% to 150%.
- **Mountain Hiking** Skill Adjustment:
  - Adjusted to: Unique effect. Creates Mountain Realm for 3 turns. While the Realm lasts, allies gain Rock Pattern: Cloud Robe on the first action of their first turn; afterward, if an ally uses the same skill as in the previous turn, they gain Rock Pattern: Cloud Robe; otherwise, they gain Rock Pattern: Mountain Hue after their turn ends.
  - **Lv. 2** : In Mountain Realm, Crit DMG taken by allies is reduced by 25%
  - **Lv. 3** : In Mountain Realm, non-critical damage dealt by allies is increased by 25%
- Other Fixes
  - Fixed an issue where under certain circumstances, the effect of Mountain Hiking interacted abnormally with Rift in Time.

- **Descending Judgment** Skill Adjustments:
  - Adjusted to: Attacks the target enemy 2 times with chains, each hit dealing damage equal to 50% of ATK, and has a 100% chance to inflict Bone Locks for 2 turns. If the enemy already has Bone Locks, the chance is reduced to 30%. When an enemy gains a single-target Move Bar boost or Haste effect, Kidomaru casts Descending Judgment on them. Before the turn starts, this effect and the extra Descending Judgment triggered by Bone Locks can be cast up to 5 times in total. If the enemy already has Bone Locks, it will not trigger again.
  - **Lv. 5** skill upgrade description optimized to: Attacking a Bone Locks target grants 1 stack of Rage after the turn ends
- **Bone Locks** Effect Adjustment:
  - Adjusted to: Cannot receive Move Bar-altering or Haste effects. After Kidomaru attacks a Bone Lock targets, he deals damage equal to 60% of ATK to other targets with Bone Locks. When an ally uses a normal attack on a Bone Locks target, Kidomaru performs a co-op attack.
- **Stealth** Effect Adjustment:
  - Adjusted to: Kidomaru's special state. Enemy skills prioritize targets other than Kidomaru for 3 turns. While in Stealth, damage taken by Kidomaru is reduced by 20%, and his attacks deal an extra 33% of ATK as True Damage. Stealth is removed after Kidomaru attacks during his turn.
- Description Optimization for **Asura Bone Locks**  - The description for Asura Bone Locks is optimized to: Kidomaru attacks the target enemy 3 times, each hit dealing damage equal to 70% of ATK and inflicting Bone Locks for 2 turns, then enters Stealth and gains 1 stack of Rage after the turn ends. If already in Stealth, he cannot gain Stealth again.
- Reminder
  - When Kidomaru appears as a monster, these balance adjustments do not affect him.

- **Snow Weaver** Skill Adjustment:
  - Adjusted to: When attacking or dealing conduction damage, has a 25% base chance to inflict Freeze for 1 turn. When attacking a Freeze target again, it becomes Deep Freeze and also inflicts Ice Mark on the enemy for 2 turns. Damage dealt to enemies under Freeze-type effects is increased to 300%. When inflicting Freeze-type effects on an enemy, gains an undispellable shield that absorbs damage equal to 150% of Yuki's starting ATK for 2 turns. Gains Frostwoven Shelter at the start of battle and at the end of each turn.
- New **Ice Mark** Effect:
  - Ice Mark: Reduces starting SPD by 40%.
- **Frostwoven Shelter** Effect Adjustment:
  - Adjusted to: Blocks 1 instance of Suppress, Seal, Freeze-type effects, or Banish. When attacking, if the enemy has Shelter, loses Frostwoven Shelter and removes the enemy's Shelter.
- **Moonlit Snow Slash** Skill Adjustments:
  - Adjusted to: Uses the famed blade Snow Chaser to attack the target enemy 3 times, each hit dealing 140% of ATK as damage, and increases Effect HIT by 200% until the end of the turn. After inflicting a Freeze-type effect, restores 1 orb.
  - **Lv. 2** : Damage increases to 145%
  - **Lv. 3** :Damage increases to 150%
  - **Lv. 4** :Damage increases to 155%
  - **Lv. 5** :Damage increases to 160%
- Issue Fixes
  - Fixed an issue where the damage increase description in Snow Weaver against Freeze-type effects was incorrect, so it now matches the actual effect.
  - Fixed an issue where the actual Effect HIT increase from Moonlit Snow Slash was lower than intended, so it now matches the description.
- Reminder
- 8When Yuki appears as a monster, these balance adjustments do not affect him.

- **Demonic Slash Skill** Effect Adjustment:
  - Draws one random blade from Higekiri, Tomokiri, and Shishinoko to slash the target enemy, dealing damage equal to 80% of ATK, and activates its corresponding effect.
    - Higekiri: Gains a 20% chance to co-op for 1 turn.
    - Tomokiri: Damage taken is reduced by 50%, removed after triggering 3 times.
    - Shishinoko: After the Onmyoji defeats a non-summoned entity target, uses a normal attack on the enemy with the lowest HP percentage, then removes this effect.
- Draws one random blade from Higekiri, Tomokiri, and Shishinoko to slash the target enemy, dealing damage equal to 80% of ATK, and activates its corresponding effect.
- **Demonic Blade: Rajomon** Skill Adjustment:
  - **Lv. 2** : Gains the effect of 1 random blade at the start of battle
  - **Lv. 3** : Gains the effects of 2 random blades at the start of battle
  - **Lv. 4** : Gains the effects of all 3 blades at the start of battle
  - **Lv. 5** : Each activated blade effect increases ATK by 15%
- **Shadow Slash** Skill Adjustment:
  - Draws Higekiri, Tomokiri, and Shishinoko all at once and attacks the target enemy 3 times, each hit dealing damage equal to 80% of ATK while activating all three blade effects.
- Reminder
  - When Onikiri appears as a monster, these balance adjustments do not affect his skills.

The following adjustments occurred on February 11th, 2026 for CN servers.

- **Fox Fire** Skill Adjustments:
  - Adjusted to: Concentrates fox fire to attack 1 enemy, dealing damage equal to 353% of ATK.
- Upgrade effects adjusted to:
  - **Lv. 2** level up effects changed to: Damage increased to 362%.
  - **Lv. 3** level up effects changed to: Damage increased to 371%.
  - **Lv. 4** level up effects changed to: Damage increased to 380%.
  - **Lv. 5** level up effects changed to: Damage increased to 389%.
- **The Falling** Skill Adjustments:
  - Adjusted to: Channels all of his power, dealing damage to all enemies equal to 176% of his ATK.
- Upgrade effects adjusted to:
  - **Lv. 2** level up effects changed to: Damage increased to 182%.
  - **Lv. 3** level up effects changed to: Damage increased to 188%.
  - **Lv. 4** level up effects changed to:  Damage increased to 195%.
  - **Lv. 5** level up effects changed to: If Fox Fire or The Falling KO's an enemy, immediately casts another skill without cost, with damage decreasing by 20% each time.
- Reminder:
  - When Tamamonomae appears as a monster, his skills won't be affected by these balance adjustments.



- **Maple Dance** Skill Adjustments:
  - Adjusted to: Dances freely, summoning maple leaves to gain 2 stacks of Into the Woods. During its duration, all allies gain Leaf Buffer.
- **Into the Woods** Effect Adjustments:
  - Adjusted to: Max 2 stacks. Reduces by 1 stack after casting Leaf Blade during turn. Increases Indirect Damage taken by 20%, and reduces non-Indirect Damage taken by 20%.
- **Leaf Buffer** Effect Adjustments:
  - Adjusted to: When the unit takes damage, inflicts a stack of Burnt Leaf on the attacker. Triggers up to once each turn.
- Other improvements
  - Improved some of Heartseeker Momiji's skill descriptions, while the original skill effects remain unchanged.
  - Fixed an issue where Burnt Leaf could be improperly resisted in certain situations.
- Reminder
  - When Heartseeker Momiji appears as a monster, her skills won't be affected by these balance adjustments.

- **Blazing Tails** Skill Adjustments:
  - Adjusted the orb cost from 4 to 3.
  - Skill effect has been adjusted to: Launches 12 random attacks on enemies, dealing damage equal to 80% of his ATK with each strike. Damage is reduced by 20% for each subsequent attack on the same target.
- Reminder
  - When Blazing Tamamonomae appears as a monster, his skills won't be affected by these balance adjustments.

The following adjustment occurred on December 16th, 2025 for CN servers.

**Rewind Time** Skill Effect Adjustments:

- Effect before Evolution adjusted to: Exclusive effect. Postpones 40% of her damage taken to the start of her next turn (the postponed damage won't be lethal).
  - Active skill: When cast on an enemy target, has a 100% base chance of locking them in the Crack in Time for 1 turn. When cast on an ally, takes them into the Rift in Time; if the target is herself, gains 1 stack of Time Radiance and cooldown for 1 turn; if the target is another ally, grants them 2 stacks of Time Radiance.
- Effect after Evolution adjusted to: Exclusive effect. Postpones 40% of her damage taken to the start of her next turn (the postponed damage won't be lethal).
  - Active skill: When cast on an enemy target, lockes them in the Crack in Time for 1 turn. When cast on an ally, takes them into the Rift in Time; if the target is herself, gains 1 stack of Time Radiance and cooldown for 1 turn; if the target is another ally, grants them 2 stacks of Time Radiance.
- **Lv.3** Effect Adjusted to: Crack in Time duration increased to 2 turns.
- **Lv.5** Effect Adjusted to: Upper Hand: grants 1 stack of Time Radiance to the allied shikigami with the highest initial ATK.

**New Time Radiance** Skill Effect added:

- Time Radiance: [Buff, Mark] Up to 2 stacks. A maximum of 1 instance of this effect can exist on the ally field. After Himiko casts Timely Sunlight, consumes 1 stack of Time Radiance to make the bearer enter the Rift in Time. Before the bearer's turn begins, consumes 1 stack of Time Radiance to convert this turn and take them into the Rift in Time.

**Timely Sunlight** Skill Effect Adjustments:

- **Lv.5** Effect Adjusted to: Damage ignores Soul effects.

The following adjustments occurred on December 9th, 2025 for CN servers.

- Base Stat Adjustments:
  - Base SPD increased from 90 to 98.
- **Hillcry: Blast** Skill Effect Adjustments:
  - Skill effect adjusted to: Wields the Jade Blade of Yasakani and unleashes a wave of energy at 1 enemy, dealing damage equal to 100% of his ATK.
  - When **Unlimited Blade Prison** is active, changes Hillcry: Blast to Hillcry: Slash and increases the next 3 Double Team trigger chances to 100%.
- **Hillcry: Slash** Skill Effect Adjustments:
  - Skill effect adjusted to: Advanced secret of the Jade Blade of Yasakani. Unleashes a crashing wave of energy at 1 enemy, dealing damage equal to 100% of his ATK. The damage doesn't trigger the target's Soul effects or passive effects. Gains a 50% chance of Double Team.
  - 100% of damage dealt by Hillcry: Slash will be added to the next damage dealt by Rockfall from Unlimited Blade Prison (to a max of 600% of Otakemaru's ATK).
- **Force of Earth** Skill Effect Adjustments:
  - Skill effect adjusted to: At the start of battle, summons the Force of Earth to protect self.
    - Force of Earth: Reduces damage taken by 20%.
  - **Lv.2** Force of Earth reduces damage taken by 25%.
  - **Lv.3** Force of Earth reduces damage taken by 30%.
  - **Lv.4** Force of Earth reduces damage taken by 35%.
  - **Lv.5** Force of Earth reduces damage taken by 40%.
- Skill effect adjusted to: At the start of battle, summons the Force of Earth to protect self.
- **Unlimited Blade Prison** Skill Effect Adjustments:
  - Orb cost reduced from 4 to 3.
    - Skill effect adjusted to: Uses Unlimited Blade Prison to banish 1 enemy, gaining 30% of the target's initial ATK and DEF (the gained stats cannot exceed 50% of Otakemaru's own initial ATK and DEF) until the end of Otakemaru's next turn, and conjures a torrent of Wave of Rock to attack all enemies, dealing damage equal to 285% of his ATK.
    - When the Blade Prison closes, the floating rock falls to attack the banished enemy, dealing damage equal to 358% of his ATK. The damage cannot be shared, does not trigger the target's Soul effects and Passive skills, raises the Move Bar of Otakemaru by 40%, and removes the extra stats gained.
      - When Unlimited Blade Prison is active, the skill cannot be cast.
  - **Lv.2** Wave of Rock damage increased to 299%.
  - **Lv.3** Wave of Rock damage increased to 312%.
  - **Lv.4** effect adjusted to: When Blade Prison closes, Move Bar raise effect increased to 70%.
- Orb cost reduced from 4 to 3.
- **Reminder**  - When Otakemaru appears as a monster, his skills won't be affected by these balance adjustments.

- **Devour** Effect Adjustments:
  - Skill effect adjusted to: Unable to act, cannot be targeted, Move Bar position locked, passive skills and equipped Soul effects disabled, immune to damage, healing, buffs, and debuffs.
  - Fixed an issue where Devour's base chance wasn't affected by Effect HIT, making it consistent with the original description.

- **Water Circuit** Skill Effect Adjustments:
  - Skill effect adjusted to: When an allied non-summoned entity other than self has their HP first drop below 70%, if no allied target on the field has HP Connection, that target and Shouzu immediately gain HP Connection for 1 turn. This effect can only trigger once per battle.
    - Active skill: Grants HP Connection to all allied non-summoned entities, causing them to heal by 5% of Shouzu's max HP after taking action, lasting 1 turn.
    - Damage shared is regarded as Transferred Damage.
- Skill effect adjusted to: When an allied non-summoned entity other than self has their HP first drop below 70%, if no allied target on the field has HP Connection, that target and Shouzu immediately gain HP Connection for 1 turn. This effect can only trigger once per battle.
- **Reminder**  - When Shouzu appears as a monster, her skills won't be affected by these balance adjustments.

- Base Stat Adjustments:
  - Base SPD increased from 93 to 104.
- **Purifying Rain** Skill Effect Adjustments:
  - Skill effect adjusted to: At the start of the turn, removes all controlling effects on self and dispels all debuffs. Gains 40 SPD for 1 turn when affected by debuffs or controlling effects (triggers at most once before own turn starts).
- **Sky Tears** Skill Effect Adjustments:
  - Skill effect adjusted to: Select an allied target to remove all controlling effects they bear, and dispels all debuffs or controlling effects from all allies (up to four per allied shikigami).
  - Dispels 1 buff from each enemy and has a 100% base chance to inflict Shackle of Tears on them, lasting for 2 turns.
    - Lv.2 effect adjusted to:
      - Increases the selected allied target's Effect RES by 80% for 1 turn.
  - Lv.2 effect adjusted to:
- **Reminder**  - When Ame Onna appears as a monster, her skills won't be affected by these balance adjustments.

The following adjustments occurred on September 3rd, 2025 for CN servers.

- **Great Responsibility** Skill Effect Adjustment:
  - Original effect adjusted to: Recovers the HP of 1 non-summoned ally entity by 14% of max HP with a 50% chance of transferring the 4-piece set effect of his Souls to the ally (up to 1 effect can be transferred, total damage boost from all Souls maxed out at 140%). Lasts for 1 turn. Using the skill on the ally who received his Souls via transfer won't trigger the Soul-transferring effect again, and dispels or removes all controlling effects on them instead. If the target is not under control effects, grants them a new turn and removes the Soul-transferring effect at the end of that turn.
- Balance Adjustment Compensation:
  - For this adjustment to Returner Ebisu, we will provide the following compensation:
  - For each G5 Returner Ebisu owned, you get one G5 Shikigami Exchange Amulet; for each G6 Returner Ebisu owned, you get one G6 Shikigami Exchange Amulet.
  - For each Returner Ebisu with upgraded skills, regardless of grade, you get Skill Darumas based on the number of skill upgrades, with a maximum of 3 Skill Darumas.

- **Dream Binder** Skill Effect Adjustment:
  - Original effect adjusted to: Unique effect. The echoes of the incense from a distant memory drift out from the divine censer to create a Scented Realm that lasts for 3 turns. While the Scented Realm is active, at the end of each other non-summoned ally entity's turn, Jinkougyou gains 1 Devout Mind stack. Jinkougyou has a 40% chance of applying Soul Binder when attacking enemies. Additionally, for every 1% the enemy's DEF is lower than Jinkougyou's, his damage dealt increases by 1%.
    - **Lv. 2** effect adjusted to: Each time Bodhicitta is cast, the Scented Realm duration is extended by 1 turn.
- Original effect adjusted to: Unique effect. The echoes of the incense from a distant memory drift out from the divine censer to create a Scented Realm that lasts for 3 turns. While the Scented Realm is active, at the end of each other non-summoned ally entity's turn, Jinkougyou gains 1 Devout Mind stack. Jinkougyou has a 40% chance of applying Soul Binder when attacking enemies. Additionally, for every 1% the enemy's DEF is lower than Jinkougyou's, his damage dealt increases by 1%.
- **Soul Binder** Effect Adjustment:
  - Effect adjusted to: Each time it is gained, permanently reduces the carrier's base DEF by 5%, stacking up to 5 times. At 3 stacks, consumes all current stacks to inflict Distracted and deal 231% indirect damage to an enemy.
- **Distracted** Effect Adjustment:
  - Effect adjusted to: When the Move Bar of the unit with this mark reaches the bottom of the turn order, removes this mark to skip their turn.

- **Soul Rage** Skill Effect Adjustments:
  - Changed to an active effect.
  - Skill cooldown modified to 2 turns.
  - When attacked by non-transferred damage, there is a 12% chance to cast Extra Slice without consuming resources. Upon casting, gains Revenant, lasting for 2 turns.
    - Added the **Revenant** effect: When taking fatal damage, survives with 1 HP and immediately gains a shield equal to 135% of ATK for 2 turns.
  - Added the 
  - **Lv. 2** level up effects changed to: Trigger chance increased to 16%.
  - **Lv. 3** level up effects changed to: Trigger chance increased to 20%.
  - **Lv. 4** level up effects changed to: For every 30% decrease in HP, the trigger chance increases by an additional 3%.
  - **Lv. 5** level up effects changed to: Upper Hand: Casts Soul Rage.

The following adjustments occurred on July 30th, 2025 for CN servers.

- **Clearsky Rainbow** Skill Adjustments:
  - **Lv. 4** upgrade: When Sungraced Hiyoribou or the allied non-summon unit with the highest starting ATK takes damage, consumes up to 60% of starting ATK worth of rainbow energy to block an equal amount of damage.
  - Adjusted **Lv. 5 upgrade** : When Sungraced Hiyoribou takes damage, the amount of rainbow energy consumed to block damage increases to 90% of starting ATK.
- **Sunny Radiance** Skill Adjustments:
  - **New effect** :
    - Dispels dark clouds to let the rainbow shine. Grants Lightning Doll to another ally. Sustainable for 1 turn. And stores rainbow energy equal to 600% of her starting ATK. For every 600% starting ATK worth of rainbow energy stored, gains 1 Sunshine Doll (max 3 before the next turn).
    - Added effect for Sunshine Doll: Max 3 stacks. At the start of each turn (for both sides), removes Freeze effects from 1 non-summoned ally and consumes 1 stack.
    - Adjusted **Lv. 4** upgrade: After the ally with Lightning Doll deals or take damage, heals 3 non-summoned ally entities with the lowest proportion of HP by 120% of her starting ATK (max 4 times before her next turn).
    - Adjusted **Lv.5 upgrade** : Upper Hand: Automatically casts Sunny Radiance on the ally with the highest starting ATK at the start of battle.
- Optimizations and Fixes:
  - Improved some skill descriptions without changing their effects.
  - Fixed an issue where Rest in Ice could not be dispelled.
  - Fixed an issue where Sunny Radiance sometimes failed to trigger healing.

- **Illusory Moonfall** Skill Adjustments:
  - Adjusted **Lv.4 upgrade** : Transfer chance increases to 70%. For every 30% of Illusory Moon's max HP, the chance increases by an additional 10%.
- Adjusted 
- **Lost Star** Skill Adjustments:
  - New effect: Max 5 stacks. After a unit attacks another unit with Lost Star, detonates it, removing 1 stack, dealing damage equal to 55% of Tsukuyomi's ATK, and restoring 5% of the Illusory Moon's max HP, without triggering the enemy's Soul effects. Damage is increased to 85% instead when attacking monsters. Can be triggered up to once. When Tsukuyomi attacks an enemy with Lost Star stacks, detonates it at the end of his action and removes 3 stacks.
- Fixes:
  - Fixed an issue where the Illusory Moon would behave abnormally in certain cases.

- **Dark Predation** Skill Adjustments
  - New effect: Exclusive effect. At the end of the turn, gains 1 stack of Dark Predation. When an ally's Move Bar is lowered, heals the ally with the lowest HP percentage for 12% of Tagitsuhime's max HP.
  - New effect: Stacks up to 5 times. Each stack increases healing by 10%. At 5 stacks, reduces the orb cost of using Shark Surge by 3.
- **Shark Surge** Skill Adjustments
  - New effect: Raises the sails and rides the waves, boosting a designated ally's Move Bar by 20%. Launches a 2-strike attack on all enemies, dealing damage equal to 70% of ATK on each strike. 12% chance to freeze them for 1 turn.
- Bug Fixes
  - Fixed an issue where Spell: Protect couldn't block damage from Shark Surge.
  - Fixed an issue where Dark Predation would trigger incorrectly in some situations.

The following adjustments occurred on May 21th, 2025 for CN servers.

- **Wings of Steel** Skill Adjustments:
  - **Lv. 5** level up effects changed to: After Shelter blocks a control effect, casts Blade Storm at no cost.
- **Blade Storm** Skill Adjustments:
  - Summons a hurricane to form a massive vortex of feather blades, attacking all enemies 4 times, dealing damage equal to 65% of Ootengu's ATK. For each enemy hit, gains 1 stack of Heroic Posture and increases Ootengu's Move Bar by 5% (max 6 triggers per attack).
  - **Lv.2** level up effects changed to: Damage increased to 67%
  - **Lv.3** level up effects changed to: Damage increased to 69%
  - **Lv.4** level up effects changed to: Damage increased to 71%
  - **Lv.5** level up effects changed to: Damage increased to 75%

- **Co-Op** Skill Adjustments:
  - New **Co-Op** effect: When Ubume joins battle and wins, EXP rewards are increased by 9%.
- New 
- Base Stat Adjustments:
  - Base Crit adjusted to: 50%
  - Base Crit DMG adjusted to: 120%

The following adjustments occurred on April 23nd, 2025 for CN servers.

- **Lantern Support** Skill Adjustments:
  - Exclusive Effect. At the start of other ally shikigami's turn, has a 10% chance to gain **Lantern Support** until the end of their turn. If**Lantern Support** is obtained when casting skills, every 1 orb left will increase the skill's damage by 5%.
  - **Lv. 2** level up effects changed to: Trigger chance increased to 12%.
  - **Lv. 3** level up effects changed to: Trigger chance increased to 14%.
  - **Lv.4** level up effects changed to: Trigger chance increased to 16%.
  - **Lv.5** level up effects changed to: Trigger chance increased to 40%, but chance is reduced by 3% for every orb owned.
- Exclusive Effect. At the start of other ally shikigami's turn, has a 10% chance to gain 
- **Lantern Drain** Skill Adjustments:
  - Deals damage equal to 158% of her ATK to all enemies and has 30% chance of draining 1 orb from each attacked enemy. After she attacks, for every additional orb allies have over enemies, she deals an additional true damage equal to 5% of target's max HP. (Does not apply to monsters)
  - **Lv. 2** level up effects changed to: Damage increases to 165%.
  - **Lv. 3** level up effects changed to: Damage increases to 172%.
  - **Lv.4** level up effects changed to: Damage increases to 180%.
  - **Lv 5.** level up effects changed to: Damage increases to 190%. Grants the allied shikigami with highest ATK a**Lantern Support** .
- Reminder:
  - Aoandon's skills won't be affected by the balance update if she's a monster.

- **Empowering Flow** Skill Adjustments:
  - **Exclusive Effect.** Deals 20% additional damage when he launches a critical hit. Gains**Empowering Flow** at start of battle.
  - Reduces DEF by 20%. When he deals damage, ignores 120 enemy DEF. After accumulating damage that equals to 50% of max HP, casts ***Swallow** at an enemy target with no cost.
  - **Lv. 2** level up effects changed to: Trigger condition is reduced to 40% of max HP.
  - **Lv. 3** level up effects changed to: Trigger condition is reduced to 30% of max HP.
  - **Lv. 4** level up effects changed to: Gains addition 20% HP steal when landing a critical hit.
  - **Lv. 5** level up effects changed to: When affected by Move Bar-lowering effects, instead increases Move Bar by 30% (max 2 times before own turn starts)
- **Swallow** Skill Adjustments:
  - Conjures a school of fish with dark energy to attack an enemy target twice. The first hit deals damage equal to 53% ATK with 100% base chance to inflict **Isolation** for 2 turns. The second hit deals damage equal to 211% ATK. Gains**Reign** for 2 turns after using the skill.
  - **Isolation** : Only 1 enemy target can be isolated at most. Cannot be selected by other allies. Damage taken cannot be shared or transferred by other effects.
  - **Reign** : When using**Swallow** , additionally performs 2 follow-up attacks on the 2 enemies with the lowest HP, each dealing damage equal to 100% ATK
- Conjures a school of fish with dark energy to attack an enemy target twice. The first hit deals damage equal to 53% ATK with 100% base chance to inflict 
- Reminder:
  - Arakawa no Aruji won't be affected by the balance update if he's a monster.

- **Sword Slice** Skill Adjustments:
  - Attacks an enemy target, dealing damage equal to 300% of DEF. When used outside of the turn, damage increases by 200%.
  - **Lv. 2** level up effects changed to: Damage increases to 340%
  - **Lv. 3** level up effects changed to: Damage increases to 380%
  - **Lv. 4** level up effects changed to: Damage increases to 420%
  - **Lv. 5** level up effects changed to: When used during the turn, 30% base chance to inflict Taunt on the target
- **Sturdy Armor** Skill Adjustments:
  - **Unique effect.** For every 20% decrease in HP, increases DEF by 8%. If unable to act, gains**Hardened** and 100 SPD, lasting 2 turns.
  - **Hardened** : DEF increases by 100%, cannot land critical hits, immune to Move Bar changes.
  - **Lv. 2** level up effects changed to: DEF boost increases to 12%
  - **Lv. 3** level up effects changed to: When hit by an enemy normal attack for the first time each turn, launches a counter-attack at the source of the damage.
  - **Lv. 4** level up effects changed to: DEF boost effect is shared with all allies
  - **Lv. 5** level up effects changed to: When an ally is hit by an enemy normal attack, Samurai X takes 65% of the damage (does not trigger own Soul effects during this period)
- **Unbreakable** Skill Adjustments:
  - Normal attack damage taken reduced by 30%.
  - Use to gain **Hardened** , with a 50% base chance to Taunt all enemies, lasting 1 turn.
  - **Lv. 2** level up effects changed to: DEF boost from Hardened increases to 110%
  - **Lv. 3** level up effects changed to: DEF boost from Hardened increases to 120%
  - **Lv. 4** level up effects changed to: DEF boost from Hardened increases to 130%
  - **Lv. 5** level up effects changed to: DEF boost from Hardened increases to 150%
  - Base Attributes Adjustment: Base DEF increased from 415 to 481.
- Reminder:
  - Heiyou's skills won't be affected by the balance update if he's a monster.

The following adjustments occurred on May 22nd, 2024 for CN servers.

- **Inferno Gate** Skill Adjustments: The skill now costs 3 orbs to use.

- **Feather Blade Wind** Skill Adjustments:
  - **Lv. 4** level-up effects changed to: Increases damage to 50%.
  - **Lv. 5** level-up effects changed to: Effective effect. Each non-summoned enemy entity KO'd increases the starting strikes by 2, up to 4 strikes.

- **Fox Bell Skill** Adjustments:
  - Ringing her blessing bell, sends out one of her foxes to attack 1 enemy, dealing damage equal to 80% of her ATK, and has a 50% base chance of inflicting one of the effects among Silence, Seal, Suppress, and Grounded lasting 1 turn on them.
  - **Grounded** : Move Bar-changing effects are invalidated.
- **Sunlit Fox Realm** Skill Adjustments:
  - **Lv. 4** level-up effects changed to: Increases dispelling chance to 100%.

- **Disarm** Effect Adjustments:
  - Prevents using normal attacks. Prevents the effects of Souls equipped on shikigami. Reduces the enemy's normal attack damage by 20% for 1 turn when it's dispelled.

The following adjustments occurred on November 8th, 2023 for CN servers.

- **Scorching Fire Skill** Effect Adjustments:
  - Adjusted **Lv. 3** level-up effects to: If Suzuhikohime has**Holy Fire** , at the end of a non-summoned ally entity's turn, recovers her HP by 8% (changed from 6%) of her max HP.
  - Adjusted **Lv. 5** level-up effects to: When she becomes an**Undying Flame** (changed from having Holy Fire), creates a shield that cannot be dispelled and lasts 2 turns, absorbing damage equal to 120% of her ATK.
- Adjusted 
- **Undying Flame** Skill Effect Adjustments:
  - Added to the effect: While she's in this state, increases other allies' Crit RES and DEF by 40%. When another non-summoned entity is KO'd, immediately recovers Suzuhikohime's HP by 50% of her max HP.
- **Fire Rite** Skill Effect Adjustments:
  - Added to the effect: If **Fire Rite** manages to KO a non-summoned enemy entity, immediately recovers her HP to full. The effects can be triggered up to once per turn.
- Added to the effect: If 

The following adjustments occurred on August 9th, 2023 for CN servers.

- Adjusted the Skill Effects of **Wind Amulet: Shield** :
  - **Wind Amulet: Shield** is now an exclusive effect.
  - (Added) Each ally with a shield grants Azurestorm Ichimokuren 5% damage reduction, up to 30%.
    - Adjusted the **LV. 2** level-up effect: Increases the**Wind Shield** 's shield capacity to 217%. (previously: 198%)
    - Adjusted the **LV. 3** level-up effect: Increases the proportion of HP required to trigger**Wind Amulet: Shield** to 40% and reduces the cooldown to 2 turns.
    - Adjusted the **LV. 4** level-up effect: When another ally gains a shield, Azurestorm Ichimokuren creates a**Wind Shield** to protect himself, absorbing damage equal to 50% of the shield capacity of the ally's shield.
    - Adjusted the **LV. 5** level-up effect: For each 1% of excess Crit Azurestorm Ichimokuren has for his starting Crit, the**Wind Shield** grants 2% damage reduction (max 40%) and increases his Crit DMG by 2%.
  - Adjusted the 
- Adjusted the Skill Effects of **Wind Halted: Dragonfall** :
  - Removed the **Dragon Fury** and**Isolation** effects.
  - (Added) Using the skill no longer consumes **Wind Shield** .
  - (Added) Damage dealt is reduced by 20% for each subsequent strike on the same enemy.
    - Adjusted the **LV. 4** level-up effect: Using the skill also recovers the HP of the allies with the**Wind Shield** by 35% of their**Wind Shield** 's remaining shield capacity.
    - ※Adjusted the **LV. 5** level-up effect: After using the skill, if the shield capacity of an ally's**Wind Shield** is below 72% of its starting capacity, resets it to 72% of its starting capacity.
  - Adjusted the 
- Removed the 
- **Wind Shield** Adjustments:
  - **Wind Shield** 's max shield capacity is equal to 600% of Azurestorm Ichimokuren's starting ATK. (previously: 200% of his max HP)
  - Each **Wind Shield** increases the shield creator's SPD by 15. (previously: 30)
- Kind Reminder:
  - Improved how Azurestorm Ichimokuren uses his skills in auto mode.
  - Azurestorm Ichimokuren's skills won't be affected by the balance update if he's a monster.

The following adjustments occurred on July 5th, 2023 for CN servers.

- **Lock Soul** Skill Effect Adjustments
  - **Added effect** : If he doesn't have**Web of Souls** while using the skill, raises his Move Bar by 40%.
  - Adjusted the **Lv. 3** level-up effect: Increases**Delirious** ' base chance of forcing a normal attack to 80% (instead of the original 75%.)
- **Lost in Demon City** Skill Effect Adjustments
  - Added effect: If he has **Web of Souls** , the damage is inflicted onto all enemies.
- Added effect: If he has 
- Basic Stat Adjustments:
  - Increased Shura Kidomaru's base **SPD** from 110 to 114.
- Increased Shura Kidomaru's base 

- **Healing Fragrance** Skill Effect Adjustments:
  - While healing, additional heals the HP of other allies by 30% of the healing amount. Allies healed by Momo deals 30% more damage for 1 turn.
  - **Active skill** : Heals the HP of 1 ally by 20% of her max HP.
- Kind Reminder: Momo's skills won't be affected by the balance update if she's a monster.

The following adjustments occurred on May 24, 2023 for CN servers.

- **Infernal Hand** Improved:
  - Effective Exclusively.
  - Summons his hand from hell with a demonic power to attack 1 enemy, dealing damage equal to 263% of his ATK. Gains him 3 **Demonic Arm** stacks. Whenever another non-summoned ally entity uses a Skill on a single enemy, consumes 1**Demonic Arm** stack to inflict damage equal to 171% of his ATK on the enemy. After using the skill, each**Fury Fire** stack he has recovers your orbs by 1.
    - Changed the **Lv. 2** level-up effect: Increases the damage to 276% and**Demonic Arm** 's damage to 176%.
    - Changed the **Lv. 3** level-up effect: Increases the damage to 289% and**Demonic Arm** 's damage to 181%.
    - Changed the **Lv. 4** level-up effect: Increases the damage to 302% and**Demonic Arm** 's damage to 186%.
    - Changed the **LV. 5** level-up effect: Increases the damage to 315% and**Demonic Arm** 's damage to 191%.
  - Changed the 
- Kind Reminder: Ibaraki Doji's skills won't be affected by the balance update if he's a monster.

- **Blade Storm** Improved:
  - Commands a storm to rain blades onto all enemies to inflict 4 continuous strikes, dealing damage equal to 37% of his ATK on each strike. At the start of his turn, if an enemy is not inflicted with **Feather Blade** , inflicts**Feather Blade** lasting 2 turns on them on the last strike.
    - **Feather Blade** Improved:
    - When the inflicted target is attacked by **Blade Storm** , also inflicts damage equal to 18% of his ATK, granting 1**Heroic Posture** stack to himself and removing the**Feather Blade** . If the enemy is unable to take actions, increases the damage 60% and raises his Move Bar by 5% (triggers up to 6 times for each attack.)
- Commands a storm to rain blades onto all enemies to inflict 4 continuous strikes, dealing damage equal to 37% of his ATK on each strike. At the start of his turn, if an enemy is not inflicted with 
- Increased **Base SPD** to**114**
- Kind Reminder: Ootengu's skills won't be affected by the balance update if he's a monster.

- **Ice Buffer** Improved:
  - Effective exclusively.
  - At the end of her turn, creates an **Ice Shield** (sustainable for 1 turn) to protect herself and 2 allies with the highest Crit DMG, absorbing damage equal to 6% of her max HP. When a unit with**Ice Shield** deals damage to a unit with Freeze or Deep Freeze, increases their ATK by 40% of their starting ATK.
    - Changed the **Lv. 2** : Increases the damage absorbed by the**Ice Shield** to 9%.
    - Changed the **LV. 4** : Increases the damage absorbed by the**Ice Shield** to 12%.
  - Changed the 
- **Blizzard** Improved:
  - Summons a blizzard to attack all enemies 3 times, dealing damage equal to 30% of her ATK each time, with an 8% base chance of inflicting Freeze lasting 1 turn on them. Increases the overall chance by 10% for enemies with Slow. Increases the base chance to 25% against monsters. Attacking units with Freeze again has a 30% chance of converting it to Deep Freeze. If the target is a monster, Deep Freeze will instead become Freeze for 2 turns.
- Kind Reminder: Yuki Onna's skills won't be affected by the balance update if she's a monster.

The following adjustments occurred on May 17th, 2023 for CN servers.

- **Void Dreamland** :
  - Changed the **Lv. 5** level-up effect to: When**Watchful Eye** is inflicted on the same target, causes their passive skills to fail until the end of Void Menreiki's next turn. This cannot be dispelled.
  - **Watchful Eye** :
    - It's now a General Mark that lasts 3 turns.
- Changed the 
- **Void Dreamland** :
  - Adjusted how the skill is used in Auto mode. Now she prioritizes the enemy with the highest HP.

The following adjustments occurred on April 5th, 2023 for CN servers.

- **Void Dreamland** Effect Improvements:
  - Changed **Lv. 5** level-up effect to: When**Watchful Eye** is inflicted on the same target, it will causes their passive skills to fail until the end of Void Menreiki's next turn.
- Changed 

- **Command** Skill Adjustment:
  - **Exclusive effect** adjusted: During battle, each time Briskey gains 1 MP, raises the Move Bar of Valiant Yamakaze by 1%. When a controlling effect on Valiant Yamakaze is dispelled or naturally expires, if he's not under any controlling effects, raises his Move Bar by 30%. Then Briskey consumes all MP (limited to 60) to raise Valiant Yamakaze's Move Bar by 1% for each MP consumed. When Valiant Yamakaze deals damage, amplifies the damage by 0.5% for each 1% of the HP the enemy has lost.
    - Changed **Lv. 4** level-up effect to: For all allies, each time they take critical damage, raises Valiant Yamakaze's Move Bar by 10%. (triggers only up to once for each attack.)
    - Changed **Lv. 5** level-up effect to: At the start of battle, Briskey gains 20 MP.
  - Changed 
  - **Briskey's Hunting Eyes** Skill Adjustment:
    - Briskey gazes at 1 enemy, reducing their ATK, SPD, and DEF by 35% for 2 turns. Each Briskey can only gazes at up to 1 enemy.
  - **Briskey's Blow Off** Skill Adjustment
    - Consumes ~~80~~ 60 MP after using it.
  - Consumes 

Compensation:

- The following was issued as compensation for the update on Valiant Yamakaze.
  - For each grade 5 Valiant Yamakaze owned, a Grade 5 Shikigami Exchange Amulet will be issued in compensation.
  - For each grade 6 Valiant Yamakaze owned, a Grade 6 Shikigami Exchange Amulet will be issued in compensation.
  - For each Valiant Yamakaze owned who had his skill levelled up, regardless of his grade, a Skill Daruma will be issued in compensation for each skill levelled up, up to a maximum of 3 Skill Daruma.

- **Glittering Shield** Effect Improvements:
  - **Exclusive effect** adjusted:
    - Before an ally takes an action When an ally takes an action, creates a shield that lasts 2 turns for the ally. This shield can absorb damage equal to 8% of Hako Shoujo's max HP. Also, it grants a **random buff** lasting 2 turns. When she's attacked, has a 100% base chance of inflicting 1**random debuff** lasting 1 turn on the attacker.
  - Before an ally takes an action When an ally takes an action, creates a shield that lasts 2 turns for the ally. This shield can absorb damage equal to 8% of Hako Shoujo's max HP. Also, it grants a 
- **Retrace** Effect Improvements:
  - Uses her box to preserve the current HP of all allies. Effective after in 2 Sustainable turns. When it's effective, if the HP of the ally drops below 30% of the preserved amount, recovers their HP to 30%.
  - Effective immediately when a preserved ally would be KO'd from taking damage, granting them immunity to the damage.

- **Protection** Effect Improved:
  - The Protection skill has been changed from a **passive** skill to a**special** skill that costs**1 orb** .
  - The previous passive effect of the skill has been kept.
  - A new active skill effect has been added:
    - Grants **Best Friend** to 1 ally. Sustainable for 1 turn. When an ally with**Best Friend** is KO'd, removes all controlling effects on Inugami, raises his Move Bar by 30%, and changes the skill to**Best Friend's Rage** . Also, creates a shield to protect himself, absorbing damage equal to 100% of his ATK, and a shield for each of his other allies, absorbing damage equal to 30% of his ATK. Both last 1 turn.
  - Grants 
- The Protection skill has been changed from a 
- New Skill **Best Friend's Rage** :
  - This unlocks when Inugami's **Best Friend** is KO'd to replace**Protection** .
  - Increases Inugami's base ATK by 210% and grants **Protection Mark** to all allies. Whenever a**Protection Mark** triggers a counter attack, recovers his own HP by 15% of the damage dealt; if Inugami is unable to take actions, dispels 1 controlling effect or 1 debuff on him instead.
  - **Sword Flurry'** s damage dealt no longer reduces and its cost is reduced by 2 orbs. Before Inugami's next turn, each 1 new ally KO'd allows his next**Sword Flurry** to inflict 1 additional follow-up strike.
- This unlocks when Inugami's 

- **Will to Live** Effect Improvements:
  - Will to Live has been changed from a **passive** skill to a**special** skill that costs**2 orbs** .
  - The effects of the new skill are as follows:
    - Increases Effect RES by 20%.
    - **Active skill** : Deals damage to 1 enemy equal to 100% of his ATK with a 30% base chance of inflicting Daze lasting 1 turn on them. When an ally is KO'd, automatically uses the skill on the one who KO'd them with the base chance increased to 100%.
- Will to Live has been changed from a 
- **Resurrection** Effect Improvements:
  - Places a coffin where each ally has been KO'd.
  - A coffin is sacrificed on its next action, reviving the ally where it's placed and recovering their HP by 100% of their max HP.
  - A coffin inherits 10% and 100% of the HP and SPD of the ally where it's placed, respectively. Also, 30% of Kyonshi Ani's max HP is distributed evenly among all coffins as a bonus.
  - Whenever a coffin is KO'd, raises the Move Bar of all other coffins by 15%.

The following adjustments occurred on November 30th, 2022 for CN servers.

- Added an effect to **Deep-rooted Grudge** :
  - For each enemy with **Spreading Hatred** he attacks, immediately gains him 1**Hatred Mark** .
  - Adjusted the level-up effects:
    - **Lv. 4** : Increases the triggering chance to 100%.
- For each enemy with 
- Adjusted the effects of **Hatred Mark** :
  - Vengeful Hannya's special mechanic. Stacks up to 9 times. Each stack increases his own Effect RES by 10% and his own damage reduction by 5%. When stacked the maximum number of times, removes all controlling effects on him and raises his Move Bar by 35%. While **Sealing Field** is active, he cannot gain**Hatred Marks** .
- Vengeful Hannya's special mechanic. Stacks up to 9 times. Each stack increases his own Effect RES by 10% and his own damage reduction by 5%. When stacked the maximum number of times, removes all controlling effects on him and raises his Move Bar by 35%. While 
- Adjusted the effect of **Vengeful Demon** :
  - Reduces Crit by 30%.
- Added an icon display for the SP shikigami Vengeful Hannya's Demon Masks when his **Sealing Field** is active. Players can view the number of remaining Demon Masks through the icon.

- Adjusted the effects of **Shadow Cut** :
  - The enemy marked by **Shadow Cut** is locked on by the**Shadowy Double** , cannot be affected by Move Bar-changing effects, and can remove it by using normal attack on Onikiri Reforged or when Onikiri Reforged takes 5 normal attacks. If the enemy's**Shadow Cut** is not removed, at the end of Onikiri Reforged's turn, increases**Shadow Cut** Count by 3.**Shadow Cut** Count maxes out at 5.
- The enemy marked by 
- Adjusted the effects of **Blade of the Mind** :
  - Grants immunity to controlling effects. While he has this, the enemy with **Shadow Cut** cannot counter-attack him or receive Call to Arms against him. At the start of his turn, if the enemy's**Shadow Cut** is removed,**Blade of the Mind** is also removed.
- Grants immunity to controlling effects. While he has this, the enemy with 
- Adjusted the effects of **Endangered** :
  - Reduces healing received by 75%, slows SPD by 20, and reduces DEF by 20%. The next 3 damages from normal attacks or skills dealt to the enemy ignore shields, cannot be shared, and won't trigger the enemy's Soul effects or passive skills. Then, this mark is removed. **Endangered** can be inflicted to up to 1 enemy.
- Reduces healing received by 75%, slows SPD by 20, and reduces DEF by 20%. The next 3 damages from normal attacks or skills dealt to the enemy ignore shields, cannot be shared, and won't trigger the enemy's Soul effects or passive skills. Then, this mark is removed. 
- Adjusted the effects of **Unshaken Will** :
  - Permanently gains 20% damage reduction. At the end of an enemy's turn, raises his Move Bar by 10% until he enters **Blade of the Mind** state for the first time. When taking a normal attack, if he's not unable to take action, has a 60% chance of parrying the attack. When a parry is triggered, inflicts Silence lasting 1 turn on the attacker, grants him immunity to the damage, and raises his Move Bar by 10%.
  - **Active skill** : Enters the**Blade of the Mind** state, raises his Move Bar by 40%, and inflicts**Shadow Cut** on 1 enemy. Then casts**Shadowy Double** .
    - Adjusted the level-up effects:
      - **Lv. 3** : Increases the base chance of parrying to 80%.
      - **Lv. 5** : When taking lethal damage, uses**Unshaken Will** on the source of the damage, recovers his HP to 50% of his max HP, increases his Crit RES by 100% for 1 turn, and raises his Move Bar by 30%. Triggers only once each round.
  - Adjusted the level-up effects:
- Permanently gains 20% damage reduction. At the end of an enemy's turn, raises his Move Bar by 10% until he enters 
- Adjusted the effects of **Heavenly Blade: Evilslayer** :
  - Attacks 1 enemy, dealing damage equal to 276% of his ATK. If the enemy is not **Endangered** , inflicts**Endangered** on them.
    - Adjusted the level-up effects:
      - **Lv. 2** : Increases the damage to 289%.
      - **Lv. 3** : Increases the damage to 302%.
      - **Lv. 4** : When the enemy with**Shadow Cut** uses a skill, the**Shadowy Double** immediately uses**Heavenly Blade: Evilslayer** on them, dealing 30% less damage.
      - **Lv. 5** : If he's in the**Blade of the Mind** state,**Heavenly Blade: Evilslayer** costs 2 less orbs and raises his Move Bar by 40% after it's used.
  - Adjusted the level-up effects:
- Attacks 1 enemy, dealing damage equal to 276% of his ATK. If the enemy is not 

The following adjustments occurred on October 19th, 2022 for CN servers.

- Adjusted how the SSR shikigami Senhime uses her skills in auto mode: Now she prioritizes on using the **Tame the Tides** skill, then the**Thousand Tides** skill, and no longer uses**Tidal Dream** and**Tide of Eternity** in auto mode. This adjustment won't affect how she uses her skills in Showdown Bidding, Draft Duel, Royal Battle, Duel, Realm Raid, and Underworld Arena among other zones.

- Adjusted her base SPD to 118.
- Adjusted the **Spider Mark** skill to:
  - When she attacks, has a 60% base chance of inflicting **Spider Mark** on the target.
- When she attacks, has a 60% base chance of inflicting 
- Adjusted the **Spider Mark** effect to:
  - When using an orb skill, inflicts indirect damage equal to 100% of Jorogumo's ATK and reduces the SPD by 20 for 1 turn.
- Adjusted the **Arachnid Horde** skill to:
  - Deals damage to all enemies equal to 72% of her ATK with a 20% base chance of inflicting Daze lasting 1 turn on them. Increases the base chance by 1% for each 3 SPD difference if the enemy is slower than Jorogumo.
    - **Lv. 2** damage increases to 76%.
    - **Lv. 3** damage increases to 80%.
    - **Lv. 4** damage increases to 83%.
    - Adjusted the **Lv. 5** level up effects to: Inflicts**Arachnid Venom** on each enemy not Dazed this way, dealing indirect damage equal to 136% of her ATK at the end of their turn for 1 turn. Increases the damage by 1% for each 1 SPD difference if the enemy is faster than Jorogumo, up to a maximum of 50%.
- Deals damage to all enemies equal to 72% of her ATK with a 20% base chance of inflicting Daze lasting 1 turn on them. Increases the base chance by 1% for each 3 SPD difference if the enemy is slower than Jorogumo.

The following adjustments occurred on June 1st, 2022 for CN servers.

- Improved **Sky Tears** skill effects: Dispels 1 buff from each of the enemies with a 50% base chance of inflicting**Shackle of Tears** lasting 2 turns on them. Dispels 4 debuffs or controlling effects from each ally.

The following adjustments occurred on March 16th, 2022 for CN servers.

- Changed the SP shikigami Nightveil Higanbana's skill-casting logic in auto mode:
  - If her HP is over 40% of her max HP, she prioritizes using **Doom** over**Underworld** and**Fallen Flower** ; if her HP is below 40% of her max HP, she prioritizes using**Withering Blooms** . These changes won't affect her skill-casting logic when a certain Skill is locked.
- If her HP is over 40% of her max HP, she prioritizes using 

- Changed the **Ghostly Blade** skill effect to:
  - Whenever her damage lands a critical hit, permanently increases her Crit DMG by 5% (max 100% Crit DMG increased). If her Crit DMG reaches 350%, she enters the **Glorious Blade** state.
  - Added level-up effect:
    - **Lv. 2** : Increases the Crit DMG boost from critical hits to 6% and increases the Crit DMG boost limit to 120%.
    - **Lv. 3** : Increases the Crit DMG boost from critical hits to 7% and increases the Crit DMG boost limit to 140%.
    - **Lv. 4** : Increases the Crit DMG boost from critical hits to 8% and increases the Crit DMG boost limit to 160%.
    - **Lv. 5** : Increases the Crit DMG boost from critical hits to 10% and increases the Crit DMG boost limit to 200%.
  - Added the **Glorious Blade** effect: Attacks ignore 50% of target's DEF. Each time 8 orbs are used by allies, if she's not under controlling effects or Banished, she uses**Dazzling Cleave** on a random enemy free of orb cost, prioritizing on the target she last actively attacked with**Dazzling Cleave** . The damage multiplier of the attack is halved. The skill's orb count resets after it's triggered.
- Whenever her damage lands a critical hit, permanently increases her Crit DMG by 5% (max 100% Crit DMG increased). If her Crit DMG reaches 350%, she enters the 
- Improved the **Savage Combo** skill effect to:
  - Launches a 6-strike attack on 1 enemy, dealing damage equal to 50% of her ATK on each strike. If the enemy is KO'd before she finishes her 6 strikes, she changes her target to the enemy with the lowest HP. If she's in the **Glorious Blade** state, she gains**Dazzling Cleave** with its skill level equal to the skill level of**Savage Combo** .
- Launches a 6-strike attack on 1 enemy, dealing damage equal to 50% of her ATK on each strike. If the enemy is KO'd before she finishes her 6 strikes, she changes her target to the enemy with the lowest HP. If she's in the 
- Added the **Dazzling Cleave** skill: Launches a 6-strike attack on 1 enemy, dealing damage equal to 60% of her ATK on each strike.
  - **Lv. 2** : Increases damage to 65%.
  - **Lv. 3** : Increases damage to 70%.
  - **Lv. 4** : Increases damage to 75%.
  - **Lv. 5** : Increases damage to 80%.

The following adjustments occurred on January 26th, 2022 for CN servers.

- Improved the effect of **Focused** to: Seawatch Kingyo's special mechanism. Stacks up to 8 times. When the stacks are maxed out, all stacks are removed to remove all effects on her, inflicts**River's Binding** lasting 2 turns on all enemies, and activates a**Fishtail Embrace** that lasts 1 turn. If she already has a**Fishtail Embrace** , raises the Move Bar of all allies by 25% instead.
- Improved the effect of **River's Binding** to: When the unit receives a single-target Move Bar-raising effect, focuses spiritual fish to reverse the flow, reducing their SPD by 40% at the end of their turn.
- Improved the healing logic of **Fishtail Embrace** , allowing the skill to heal Seawatch Kingyo herself.

- Increased his initial SPD from 94 to 99.
- Improved the effect of his **Star Beam** skill to:
  - Releases a beam of starlight to strike 1 enemy, dealing damage equal to 100% of his ATK and inflicting a **Star Mark** .
  - Added the **Star Mark** effect: Max 5 stacks. When the stacks are maxed out, if Susabi is able to take action, consumes all stacks to use a**Scourge: Star** on the enemy free of orb cost.
- Releases a beam of starlight to strike 1 enemy, dealing damage equal to 100% of his ATK and inflicting a 
- Changed **Stellar Field** to an active skill which costs 2 orbs.
- Improved the effect of **Stellar Field** to:
  - At the start of his turn, has a 30% chance of forming an attack-assisting field lasting 1 turn. While the field is active, at the start of Susabi's turn, dispels 1 debuff or controlling effect on him; Susabi has a 50% chance of assisting an ally when the ally uses a normal attack.
  - **Active skill** : Forms an attack-assisting field or extends its duration by 1 turn and inflicts 3**Star Mark** stacks on 1 enemy.
  - Improved the level-up effect of **Stellar** Field to:
    - **Lv. 2** : Increases the chance of forming the field to 50%.
    - **Lv. 3** : Increases the chance of forming the field to 60%.
    - Improved the level-up effect of **Lv. 4** to: Chance of forming a field is 100% if 4 or more orbs are available.
    - Improved the level-up effect of **Lv. 5** to: While the field is active, using the skill additionally raises the Move Bar of all allies by 25%.
- Improved the effect of **Scourge: Star** to:
  - Summons comets to inflict 3 strikes on 1 enemy, dealing damage equal to 120% of his ATK for the first strike. Reduces his damage by 10% for each subsequent strike. If the enemy is not KO'd, inflicts a **Star Mark** on them.
  - Improved the level-up effects of **Scourge: Star** to:
    - **Lv. 2** : Increases damage to 135% and enhances**Scourge: Moon** .
    - **Lv. 3** : Increases damage to 150% and enhances**Scourge: Moon** .
    - **Lv. 4** : If the enemy is not KO'd, inflicts a**Star Mark** on them and enhances**Scourge: Moon.**
- Summons comets to inflict 3 strikes on 1 enemy, dealing damage equal to 120% of his ATK for the first strike. Reduces his damage by 10% for each subsequent strike. If the enemy is not KO'd, inflicts a 
- Improved the effect of **Scourge: Moon** to:
  - Uses up all orbs to summon comets which inflict equal number of attacks on 1 enemy, dealing damage equal to 120% of his ATK for the first attack. Reduces his damage by 20% for each subsequent attack.
  - Improved the level-up effects of **Scourge: Moon** to:
    - **Lv. 2** : Increases damage to 135%.
    - **Lv. 3** : Increases damage to 150%.
    - **Lv. 4** : Each**Star Mark** on the enemy reduces the orb cost by 1.

- Improve the effect of **Glittering Shield** to: When an ally takes an action, creates a Shield that lasts 1 turn for the ally, absorbing damage equal to 8% of Hako Shoujo's max HP. Also grants a random buff lasting 1 turn. When attacked, has a 100% base chance of inflicting a debuff lasting 1 turn on the attacker.

The following adjustments occurred on December 29th, 2021 for CN servers.

- Changed **Darkened** 's effect to:
  - Removes the **Watchful Eye** and all debuffs on herself, changing**Void Dreamland** to**Recurrence Strike** and recovering her HP by 100%. Also, her attacks ignore DEF by 200 and inflicts 15% HP Steal.
- Removes the 
- Changed **Watchful Eye** 's effect to:
  - Exclusive effective.
  - Reduces target's DEF by 20%. Removed after ignited, dealing indirect damage equal to 100% of the Rancor marked in the **Watchful Eye** (max 4,000% of the total starting ATK of all deployed allied shikigami). Ignited automatically after 2 turns.
- Changed **Two Faces** 's**Lv. 2** level-up effect to: When she's Darkened, each Void Mask increases the SPD of all allies by 5.
- Changed **Void Dreamland** 's**Lv. 4** level-up effect to: When taking damage, marks 30% of the damage taken as Rancor in the**Watchful Eye** .
- Changed **Void Dreamland** 's**Lv. 5** level-up effect to: When**Watchful Eye** is inflicted on the same target, there's a 100% base chance of causing their passive skills to fail until the end of Void Menreiki's next turn.

- The following was also issued as compensation to all players who have a Void Menreiki for this adjustment via in-game mail (Mail expires in 14 days.)
  - For each grade 6 Void Menreiki owned, a Grade 6 Shikigami Exchange Amulet will be issued in compensation.
  - For each grade 5 Void Menreiki owned, a Grade 5 Shikigami Exchange Amulet will be issued in compensation.
  - For each Void Menreiki owned who had their skill leveled up, regardless of their grade, a Skill Daruma will be issued in compensation for each skill leveled up, up to a maximum of 3 Skill Daruma.

- In multi-round battles where the SSR shikigami Takiyashahime is deployed, the cooldown for **Moon's Secrets** has now been removed.
- Improved the SSR shikigami Takiyashahime's **Moon's Secrets** by adjusting the skill switching in auto battles. If Takiyashahime is currently using**Ignis** and more than half of her enemies has less than 50% HP, the skill will automatically be switched to**Aer** and will be switched back to**Ignis** when the round ends. If there's only one enemy left, it will automatically be switched to single-target mode.
- Increased the DEF ignoring effect from **Shadowless Sun: Ignis** and**Sleepless Moon: Ignis** from 150 to 180.

- Changed **Feather Blade** 's effect to: When the inflicted target is attacked by**Blade Storm** , also inflicts damage equal to 18% of his ATK, granting 1**Heroic Posture** stack to himself and removing the**Feather Blade** .
- Changed **Blade Storm** 's effect to:
  - Commands a storm to rain blades onto all enemies to inflict 4 continuous attacks, dealing damage equal to 37% of his ATK on each attack. At the start of his turn, if an enemy is not inflicted with **Feather Blade** , inflicts**Feather Blade** lasting 2 turns on them.
  - Changed the **Lv. 2** level-up effect to: Increases the damage to 39% and**Feather Blade** 's damage to 19%.
  - Changed the **Lv. 3** level-up effect to: Increases the damage to 41% and**Feather Blade** 's damage to 20%.
  - Changed the **Lv. 4** level-up effect to: Increases the damage to 43% and**Feather Blade** 's damage to 21%.
  - Changed the **Lv. 5** level-up effect to: Increases the damage to 45% and**Feather Blade** 's damage to 22%.
- Commands a storm to rain blades onto all enemies to inflict 4 continuous attacks, dealing damage equal to 37% of his ATK on each attack. At the start of his turn, if an enemy is not inflicted with 
- Improvements made to Ootengu in this update do not affect the skill of Ootengu as a monster.

The following adjustments occurred on November 17th, 2021 for CN servers.

- Changed the skill description of the **Chin's Feathers** skill to: Shoots poisonous feathers at 1 enemy, dealing damage equal to 80% of her ATK and inflicting 2**Poisonous Feathers** stacks on them.
- Changed the effect description of **Poisonous Feathers** to: Inflicts the Poisoned effect for 2 turns, dealing indirect damage at the start of the turn, then removes 1 stack. Max 5 stacks.
- Changed the skill effect of the **Poison Erosion** skill to:
  - Changed the **Lv. 2** level-up effect to: Increases the damage to 193% and the indirect damage to 39%.
  - Changed the **Lv. 3** level-up effect to: Increases the damage to 210% and the indirect damage to 42%.
  - Changed the **Lv. 4** level-up effect to: When using the skill, immediately inflicts 3**Poisonous Feathers** stacks to the enemy.
  - Changed the **Lv. 5** level-up effect to: If the enemy is not KO'd, immediately uses**Poisonous Beauty** on them. Only 1**Poisonous Feathers** stack is inflicted from the**Poisonous Feathers** used this way.
- Changed the 

The following adjustments occurred on October 27rd, 2021 for CN servers.

- Adjusted the **Unflinching** effect to: Prevents revival effects from triggering on him. Prevents him from being revived. Prevents his spot from being taken. Reduces the damage taken by all allies by 10%. Each 300 starting ATK he has grants an additional 1% damage reduction, up to a total of 30% damage reduction. He continues to exist as a soul upon being KO'd. On his action turn, he harnesses sea waves to attack all enemies, dealing damage equal to 20% of the total starting ATK of allied shikigami. (The total ATK counted this way won't exceed 120% of his starting ATK. This is an exclusive effect and the damage doesn't trigger his Soul effects or the enemies'.)
- Adjusted the **River's Fury** skill effect to:
  - When he's KO'd, his body becomes **Unflinching** until the end of battle. (Effective exclusively) When an ally takes damage, if the damage is over 30% of their max HP, raises his own Move Bar by 50% and removes 1 controlling effect on himself. Triggers once each turn.
  - **Active skill** : Gains a**Sea Fury** stack. All allies gain the damage reduction effects of**Unflinching** . Sustainable for 1 turn.
- When he's KO'd, his body becomes 
- Adjusted **River's Fury** skill level-up effects:
  - **Lv. 2** : Increases the damage of sea waves to 22% of allied shikigami's starting ATK.
  - **Lv. 5** : The damage multiplier of each strike of sea waves is equal to 120% of the last one (the damage multiplier can be increased up to 5 times).

- The following was also issued as compensation to all players who had a Waverider Lord Arakawa for this adjustment via in-game mail (Mail expires in 14 days.)
  - For each grade 6 Waverider Lord Arakawa owned, a Grade 6 Shikigami Exchange Amulet will be issued in compensation.
  - For each grade 5 Waverider Lord Arakawa owned, a Grade 5 Shikigami Exchange Amulet will be issued in compensation.
  - For each Waverider Lord Arakawa owned who had their skill leveled up, regardless of their grade, a Skill Daruma will be issued in compensation for each skill leveled up, up to a maximum of 3 Skill Darumas.

The following adjustments occurred on September 22nd, 2021 for CN servers*.*

- **Wind Amulet: Protect** :
  - The skill's orb cost has been changed to 2 orbs and the skill's cooldown duration is now 1 turn.
  - Skill's effects changed: Grants **Wind's Protection** to 1 ally, absorbing damage equal to 16% of his max HP for 2 turns. When**Wind's Protection** disappears, it deals damage to all enemies equal to 12% of his max HP.
  - The shield effect has been changed to **Wind's Protection** : Absorbs an amount of damage and cannot be dispelled.
  - Skill's level-up effects changed:
    - **Lv. 2** : Increases the damage absorbed by Wind's Protection to 20%.
    - **Lv. 3** : When**Wind's Protection** disappears, it lowers the Move Bar of all enemies by 20%.
    - **Lv. 4** :**Upper Hand** : Effective exclusively. Uses the skill on the ally with the highest ATK free of orbs.
    - **Lv. 5** : When an ally is inflicted with a debuff or a controlling effect, if they have a**Wind's Protection** , lowers the Move Bar of all enemies by 5%. Triggers up to 3 times each turn.

- **Wind Shield** :
  - Skill's effects changed: Grants **Wind Aegis** to all allies, absorbing damage equal to 12% of his max HP and increasing their ATK and Effect RES by 10% and 15%, respectively for 2 turns.
  - The shield effect has been changed to **Wind Aegis** : Absorbs an amount of damage and cannot be dispelled.
  - Skill's level-up effects changed:
    - **Lv. 2** : Increases the damage absorbed by**Wind Aegis** to 15%.
    - **Lv. 3** : Increases the damage absorbed by**Wind Aegis** to 18%.
    - **Lv. 4** : Using the skill on allies with**Wind Aegis** grants them an additional 20% ATK Bonus and 30% Effect RES Bonus for 1 turn.
    - **Lv. 5** : Using the skill on allies with**Wind Aegis** additionally recovers their HP by 80% of the remaining HP of the shield.
- Skill's effects changed: Grants 

The following adjustments occurred on July 14th, 2021 for CN servers.

- Before evolution:
  - Adjusted the skill effects of **Possess** before Nyunai-suzume's evolution to:
    - Effective exclusively.
    - **Upper Hand** :**Possess** es the ally with the highest ATK. When the**possess** ed unit takes lethal damage, they cease to be**Possess** ed.
    - **Active skill** :**Possess** es another ally instead.
- Adjusted the skill effects of 

- After evolution:
  - Adjusted the skill effects of **Possess** after Nyunai-suzume's evolution to:
    - Effective exclusively.
    - **Upper Hand** :**Possess** es the ally with the highest ATK.
    - When the **possess** ed unit takes lethal damage, they cease to be**Possess** ed, negating the damage, deducting their current max HP to 1, and granting them an amount of**Decayed Blood** equal to the amount of max HP deducted (max 4,000% of Nyunai-suzume's starting DEF). Then, they can no longer gain**Decayed Blood** .
    - **Active skill** :**Possess** es another ally instead.
- Adjusted the skill effects of 

- The status effect of **Possess** have been adjusted to:
  - Nyunai-suzume's exclusive mechanic. Up to 1 unit can be possessed at a time.
  - Disappeared when the possessed unit cease to be possessed.
  - The possessed unit gains DEF equal to Nyunai-suzume's starting DEF (max 50% of the unit's starting DEF).
  - Nyunai-suzume gains ATK equal to the possessed unit's starting ATK (max 50% of his own starting ATK).

- The following compensation was sent to all players who had a Nyunai-suzume for this adjustment:
  - If you own a grade 6 Nyunai-suzume, you will be compensated with 1 G6 Exchange Amulet and 800 Talismans.
  - If you own a grade 5 Nyunai-suzume, you will be compensated with 1 G5 Exchange Amulet and 400 Talismans.
  - If you own multiple grade 6 Nyunai-suzume, for each one beyond the first, you will be compensated with an additional G6 Exchange Amulet.
  - If you own multiple grade 5 Nyunai-suzume, for each one beyond the first, you will be compensated with an additional G5 Exchange Amulet.
  - If you own a grade 6 Nyunai-suzume and a grade 5 Nyunai-suzume, you will receive Talisman compensation based on the one of a higher grade. Talisman won't be compensated again for the lower grade

The following adjustments occurred on May 26th, 2021 for CN servers.

- **Light Drain** has now been changed to a kind of mark that cannot be dispelled.
- The effects of **Unextinguished** now read:
  - She gains 1 stack for each orb she collects. Max 100 stacks. The stacks don't reset when she's revived after being KO'd. Each stack increases the ATK and DEF of all allies by 1%.
- **Lights On** now has additional effects:
  - For a unit with **Light Drain** , inflicting**Light Drain** on them again removes 2 orbs from them; Worldly Aoandon collects the removed orbs.
  - Whenever she collects 30 orbs, she immediately uses **Lantern of Death** free of orbs.
- For a unit with 

The following adjustments occurred on May 7th, 2021 for CN servers.

- **Moon's Boon** have now been improved:
  - Added new **Lv. 5** level up effect: Monsters cannot remove orbs from her and allies affected by**Moon's Blessings** . When using**Clear Moon** while you don't have enough orbs, you can still spend all the remaining orbs to use the skill. When this effect is triggered, a number of filled slots will be emptied from your Orb Bar equal to the difference. If you don't have enough filled slots on your Orb Bar, the effect won't trigger.
- Added new 

The following adjustments occurred on March 17th, 2021 for CN servers.

- Changed **Snow Weaver** 's skill effects to: When attacking or dealing transferred damage, has a 45% base chance of inflicting Freeze lasting 1 - 2 turns on the enemy. Breaks the ice around enemies with Freeze, Deep Freeze, or Frostbound, increasing his damage by 300% and dissipating Freeze from them.
- Changed **Frostwoven Shelter** 's skill effects to: Negates a Suppress, Seal, Freeze, Deep Freeze, Frostbound, or Banish effect once.

The following adjustments occurred on February 7th 2021 for CN servers.

- **Unflinching** effects improved: Prevents revival effects from triggering on him. Prevents him from revival. Prevents his spot from being taken. Reduces damage taken by all allies by 10%. Each 300 starting ATK he has granted an additional 1% damage reduction, up to 30% damage reduced. He continues to exist as a soul upon being KO'd. On his action turn, he harnesses sea waves to attack all enemies, dealing damage equal to 60% of his ATK. (The damage doesn't trigger the Soul effects or exclusive effects of either side.)
- **Sea Fury** skill effects improved:
  - When he's KO'd, his body becomes **Unflinching** until the end of battle.
  - **Effective exclusively** : When an ally takes damage, if the damage is over 30% of their max HP, he gains 1**Sea Fury** stack, raises his Move Bar by 50%, and removes 1 controlling effect on himself. Triggers once each turn.
  - **Active skill** : Grants him a**Sea Fury** stack. All allies gain the damage reduction effects of**Unflinching** . Sustainable for 1 turn.
- When he's KO'd, his body becomes 
- **River's Fury** level-up effects improved:
  - **Lv. 2** : Increases the damage of sea waves to 120%.
  - **Lv. 3** : Sea Fury effects won't disappear when he's KO'd.
  - **Lv. 4** : When he's KO'd, heals the HP of all allies by 125% of his HP.
  - **Lv. 5** : Each strike of sea waves deals damage equal to 120% of the last one (the damage can be increased up to 5 times).
  - Using River's Fury now costs no orbs.
- **Wavebreaker Slash** level-up effects improved:
  - **Lv. 2** : Increases damage to 315%.
  - **Lv. 3** : Target is regarded as being inflicted with Isolation.
  - **Lv. 4** : Increases damage to 335%.
  - **Lv. 5** : When he has 3 Sea Fury stacks, his DEF is reduced by 20% and his damage is increased by 40%. After using the skill, all allies gain the damage reduction effects of Unflinching. Sustainable for 1 turn.

- **Unshaken Will** skill effects improved:
  - Effective exclusively.
  - Gains 20% damage reduction indefinitely. When taking a normal attack, if he's not unable to take action, has a 30% chance of parrying the attack, which prevents him from taking damage and raises his Move Bar by 10%.
  - **Active skill** : Enters**Blade of the Mind** state and inflicts**Shadow Cut** on 1 enemy. Then casts**Shadowy Double** .
  - Level-up effects improved:
    - **Lv. 2** : Increases the indefinite damage reduction rate to 30%.
    - **Lv. 3** : Increases the base chance of parrying to 40%.
    - **Lv. 4** : Each parry triggered increases his damage by 20%. Stacks up to 5 times. (Before: Each parry triggered increases his damage by 30%. Stacks up to 3 times.)
    - **Lv. 5** : When taking lethal damage, recovers his HP to 30% of his max HP, and raises his Crit RES by 100% and his SPD by 100 for 1 turn. Triggers only once each round.
  - **Unshaken Will** 's skill cooldown has now been removed.
  - **Blade of the Mind** : Grants immunity to controlling effects.**Parry** chance is doubled. Inflicts Silence on the attacker for 1 turn when a parry is triggered. Counter-attack and Call to Arms won't be triggered for its duration. At the start of his turn, if the**Shadow Cut** on the enemy is removed,**Blade of the Mind** is also removed.
  - **Shadow Cut** : Locked on by the**Shadowy Double** . Visible to allies only. Can be removed when the enemy with**Shadow Cut** uses a normal attack on Onikiri Reforged or when Onikiri Reforged takes 5 normal attacks.
  - **Shadowy Double** : Inherits all the current stats of Onikiri Reforged. At the start of a turn, the double disappears if the**Shadow Cut** mark on the enemy is removed. Otherwise, the double launch the same attack as Onikiri Reforged when he attacks in his turn against the target with the**Shadow Cut** mark.
- **Heavenly Blade: Evilslayer** 's**Lv. 5** level-up effects improved:**Heavenly Blade: Evilslayer** costs 2 orbs less to use if he's under the**Blade of the Mind** state and raises his Move Bar by 40% after using the skill.

- **Ink Wind** skill improved: Moves like a feather and unsheathes her sword to attack 1 enemy, dealing damage equal to 100% of her ATK. After 3 normal attacks, the next normal attack will be replaced with Ink-shadow Slash, except it deals 30% less damage. At the start of the battle, she's regarded as having used 2 normal attacks.
  - **Lv. 5** level-up effects improved: Increases her damage to 125%. The damage will no longer be reduced by 30% for every 3 normal attacks used.
- **Ink Shadow** skill improved:
  - Effective exclusively.
  - At the start of her turn, gains 2 Feathery Tutelage stacks.
  - **Feathery Tutelage** effects improved: Guardian Ubume is guaranteed to assist an ally the first time they use a normal attack then consume a Feathery Tutelage stack. After assisting the ally, they gain a Feathery Caring stack.
  - **Feathery Caring** effects improved: Permanently increases ATK by 10%. Stacks up to 5 times.

- **Arrival of Death** skill effects improved: If no enemies have Bone Lock, the chance is increased to 100%.
- Addition to **Hidden** 's effects: Kidomaru takes 20% less damage when Hidden.

- **Double Team** skill effect improved: Has a 30% chance of Assisting. If her total ATK is the highest among non-summoned entity allies, she gains First Feathers.
  - **First Feathers** effects: Increases her damage and her chance of Assisting by 100% and 60%, respectively.
- **Hack and Slash** level-up effects improved:
  - **Lv. 5** : Increases her AoE damage to 41% and her slashing damage to 108%. If the HP of the enemy is below 60% or if they're the last standing enemy, increases her slashing damage to 200%.

- **Blade of Justice** effects improved: Dashes forward to stab 1 enemy, dealing damage equal to 80% of his ATK with a 30% chance of issuing a Call to Arms to the ally with the highest starting ATK.
  - Level-up effects improved:
    - **Lv. 3** : Increases the chance of issuing Call to Arms to 40%.
    - **Lv. 5** : Increases the chance of issuing Call to Arms to 50%.
  - When auto-battle is enabled, **Blade of Justice** will prioritize attacking the enemy with the highest proportion of HP.
- Level-up effects improved:
- **Purification Wings** effects improved: When an ally uses a normal attack, raises his own Move Bar by 5%. At the start of his turn, there's a 50% chance that 1 controlling effect on him is dispelled or removed.
  - Level-up effects improved:
    - **Lv. 3** : Increases the chance of triggering to 100%.
  - Added level-up effects:
    - **Lv. 5** : Additionally dispels or removes a controlling effect on a random ally.
- Level-up effects improved:
- **Deadly Flock** effects improved: Summons crows to attack every one of his enemies, starting with the enemy with the lowest proportion of HP, dealing damage equal to 119% of his ATK on each enemy with a 30% chance of issuing Call to Arms to the ally with the highest starting ATK. Damage is increased by 20% for each KO'd enemy to a maximum boost of 100%.
  - Level-up effects improved:
    - **Lv. 3** : Increases the chance of issuing Call to Arms to 40%.
    - **Lv. 5** : Increases the chance of issuing Call to Arms to 50%.
- Level-up effects improved:

- **Insurance Policy** skill effects improved: Winning a battle with Tesso deployed grants a 9% Coin bonus.
- **Gold Barrage** skill effects improved: Commands countless gold coins to fly at all enemies twice, dealing damage equal to 44% of his ATK each time, with a 100% base chance of inflicting a**Flaw** stack lasting 2 turns on them.
- **Flaw** effect improved: 40% Vulnerability.

- Improved the target-selecting logic of **Threads Connection** when auto-battle is enabled. After the update, the enemy with the highest HP will be selected as the target.
- **Needle and Threads** skill effects improved: Commands needle and thread to pierce through all enemies, dealing damage equal to 100% of her ATK. For each enemy attacked and connected by her needle and thread, 1 orb is refunded. Also inflicts landing damage equal to 100% of her ATK on the target enemy.
  - **Lv. 5** skill level-up effects improved: Increases damage to 125% and damage to connected enemies by 30%.

- **Shelter for Rain** skill effects improved: Effect RES boost is doubled on her.
- **Song of Reunion** effects improved after evolution: Revel Mark grants her immunity to controlling effects. When Ghoul House is sober, increases the Effect RES of Tenjo-kudari by 75%.

The following adjustments occurred on September 23rd, 2020 for CN servers.

- **Crimson Slash** level-up effects improved:
  - **Lv. 2** : When her attack KO's a non-summoned enemy entity, she gains Crimson Breath (buff, status), increasing her damage by 15% to a max of 90%.
  - **Lv. 4** : When her attack KO's an enemy, she gains a new turn. Using Crimson Slash in the new turn costs no orbs.
  - **Lv. 5** : In the new turn granted, Crimson Slash deals an additional 30%. This damage cannot be shared and doesn't trigger the Soul effects or passive skills of the target.

- **Mountain's Soul: Ultra** skill improvements:
  - Skill Orb Cost reduced from 3 orbs to 2.
  - The shield multiplier of **Obligated Duty** has been increased from 90% to 115%.
  - When the **Obligated Duty** shield fails, it is removed along with the status, and she no longer gains any layers of**Mountain's Might** .
  - The **Lv. 2** level-up effects have been changed to: After using the skill, the Move Bar of all allies is raised by 10%.
- The effects of **Crashing Barrage** have now been improved:
  - Combines the power of her two weapons and shoots out her Shadowchaser with her Nether Bow to launch a 5-strike attack on all enemies, dealing damage equal to 44% of her ATK with each strike. Her attack also inflicts a 10% HP Steal.
  - **Lv. 2** : Increases damage to 47%.
  - **Lv. 3** : Increases damage to 50%.
  - **Lv. 4** : Increases damage to 53%.
  - **Lv. 5** : Each Orb spent by any ally increases her ATK and DEF by 2%. Stacks up to 50 layers.

- Increased effects on **Dragon Jewel** skill:
  - Under her field, if you don't have enough orbs to use a skill, you can still spend all the remaining orbs to use the skill. Each time the effect is triggered, Kaguya sacrifices 5% of her current HP for each orb spent and her field's duration is reduced by 1 turn. Under her field, her **Dragon Jewel** costs 1 orb less.
- Under her field, if you don't have enough orbs to use a skill, you can still spend all the remaining orbs to use the skill. Each time the effect is triggered, Kaguya sacrifices 5% of her current HP for each orb spent and her field's duration is reduced by 1 turn. Under her field, her 

- The Slow effect inflicts by **Hillcry: Blast** and**Hillcry: Slash** can no longer be dispelled.

- **Nourishment** effects improved:
  - Using the skill when her Sunshine Doll is present stores sunshine energy equal to 25% of her max HP. When her Sunshine Doll is sacrificed, its revival cooldown is reduced by 1 turn.

- Added effects to **Blizzard** : When she inflicts Freeze on a target who already has Freeze, she has a 30% chance of converting Freeze into Deep Freeze.
- Deep Freeze effects: Cannot take actions. Reduces SPD by 20. The effect cannot be dispelled.

- Added level-up effects to **Seduction** at**Lv. 5** : If her current HP is equal to her max HP, she deals an additional 15% damage.

- Added effects to **Nine Lives** : When she's KO'd, inflicts**Cat Vengeance** to the source of the lethal damage.

- **Wind Amulet: Destroy** effects improved: The**Wind Shield** he creates could previously absorb damage equal to his normal attack damage. Now the shield absorbs damage equal to 60% of his ATK. If he has a**Wind Shield** , he creates a**Wind Shield** to protect his ally with the lowest proportion of HP who has no**Wind Shield** .
- **Wind Amulet: Shield** description improved: The descriptions regarding increasing the shield's damage absorbing limit and the Move Bar-raising effect applied to the shield creator when the**Wind Shield** fails have been moved to the description of**Wind Shield** .
- Effects added to **Wind Shield** : Each**Wind Shield** increases the shield creator's SPD by 30.
- **Wind Halted: Dragonfall** effects improved: A 100% base chance of inflicting Isolation when dealing damage to the target whose HP is lower than 80% (previously 50%).

- **Blazing Sky** effects improved: While the realm is active, allies gain a fixed 25 SPD boost.
  - **Lv. 3** level-up effects improved: While the realm is active, each orb increases damage by 2% and damage reduction by 2%.

- **Soul Plunder** effects improved: Enma gains**Ghost Rider** . Ghosts sacrifice themselves on their next action, dealing damage to all enemies. This doesn't trigger the Soul effects or passive skills of the enemy.
- **Ghost Rider** effects: If there's a ghost on the enemy's side, Enma gains 50% damage reduction. Otherwise, her damage is raised by 50%.

- **Roam** effects improved: Dispels or removes a controlling effect from the healed ally.
  - **Lv. 5** level-up effects description has been modified. It now reflects the actual effects.
    - **Lv. 5** : Also heals the HP of the ally with the lowest proportion of HP by 8% of Bukkuman's max HP and grants them Heavenly Scroll: Seamless.
- **Scroll of Everything Lv. 5** level-up effects description modified. It now reflects the actual effects.
  - **Lv. 5** : Also inflicts damage equal to 80% of Bukkuman's ATK to the enemy with the lowest proportion of HP and grants them**Heavenly Scroll: Heart Assault** .

- **Blessing Lv. 5** level-up effects improved: If**Carp Banner** is on the battlefield, raises the Move Bar of**Carp Banner** by 30%.
- **Carp Banner** effects improved: Increases**Carp Banner** 's SPD inherited from Ebisu from 100% to 140%.
  - **Lv. 3** level-up effects improved:**Carp Banner** inherits 60% of Ebisu's HP.
  - **Lv. 4** level-up effects improved: If**Carp Banner** is on the battlefield, increases the SPD of all allies by 20, and allies with HP lower than 30% of their max HP gain an additional 30 SPD.
  - **Lv. 5** level-up effects improved: When**Carp Banner** takes actions, you gain 1 orb.
  - Improved how **Carp Banner** dispels debuffs/controlling effects with its**Purifying Flutter** : effects that cannot be dispelled will now be ignored.

- **Punishment** effects improved: In the new turn granted by**Necrosis** , his**Punishment** skill will be substituted by**Soul Chaser** .
- New skill **Soul Chaser** added: Wields his scythe to launch a 2-strike follow-up attack on 1 enemy, dealing damage equal to 100% of his ATK on each strike. Increases his Crit by 50%. The skill's level is equal to the skill level of**Punishment** . (In the new turn granted, his**Soul Chaser** will first be used on an enemy with HP lower than 40%.)
- **Death Sentence** effects improved: Increases his Crit by 50% against enemies with HP higher than 40%.

- **Temper Tantrum** effects improved: When Kyonshi Imoto is KO'd and Tomato is on the battlefield, she will revive immediately. Each revival increases the CD of her next revival by 1 turn.
- **Dog Attack** effects improved: Summons Tomato with the ability to use**Rage** ; Tomato uses**Rage** immediately when summoned to attack the enemy with the lowest proportion of HP. Tomato inherits 60% of Kyonshi Imoto's HP, 50% of her ATK, and 100% of her SPD. If Tomato is on the battlefield, the skill is changed to**Watch This** .
  - **Lv. 5** level-up effects improved: Kyonshi Imoto's attack will issue a Call to Arms to Tomato.
  - **Rage** effects improved: Deals damage equal to 100% of its ATK.
  - New skill **Watch This** added: Grants Tomato a layer of**Grow Up** . Tomato then attacks first the targeted enemy and then the enemy with the lowest proportion of HP, dealing damage equal to 125% of its ATK on each attack.
  - New status **Grow Up** added: Increases ATK by 20%, Crit by 20%, and SPD by 10. This stats can be stacked up to 5 layers.

- Effects added to the **Growing Feathers** skill: When dealing damage, gains**Chasing the Wind** (increases SPD by 1) that stacks up to 80 layers. For each 40 layers of**Chasing the Wind** gained, the orb cost of**Feather Blade Wind** is reduced by 1 orb.
- When auto-battle is enabled, **Feather Blade Wind** will be prioritized on the enemy with the highest HP.

- Effects added to the **Lv. 5** effects of**Conch Blow** : When Daze disappears, gains**Jump-start** (increases Crit DMG by an additional 40%) for 1 turn.

- Effects added to **Clear Moon** : Gains Shelter at the start of battle and loses Shelter at the start of her turn.

- Adjustment made to the **Wind Blade** skill: Damage is reduced to 80%, 85%, 90%, 95%, and 100% for each level respectively.
- Improvements made to the **Ki Focus** skill: Can stack up to 10 layers.
  - Effects added: When Youko completes an attack, if the enemy has more than 50% HP, an additional follow-up attack is inflicted (this includes **Wind Blade** and**Blade Cyclone** ). Each attack can trigger up to 1 follow-up attack
- Effects added: When Youko completes an attack, if the enemy has more than 50% HP, an additional follow-up attack is inflicted (this includes 
- When auto-battle is enabled, Youko will prioritize attacking the enemy with the highest proportion of HP.

- **Flower Moon** before evolution:
  - Effective exclusively.
  - At the start of another ally's turn, grants them 1 Knot of a random type (4 in total). If the Knot they received is of the same type as the one granted to the last ally who performed an action (other than Enmusubi), a match is formed. You gain 1 orb immediately and Enmusubi gains a layer of **Fateful Bond** . If a match is not formed, Enmusubi gains a layer of**Frustration** .
- **Flower Moon** after evolution:
  - Effective exclusively.
  - At the start of another ally's turn, grants them 1 Knot of a random type (4 in total). If the Knot they received is of the same type as the one granted to the last ally who performed an action (other than Enmusubi), a match is formed. You gain 1 orb immediately and Enmusubi gains a layer of **Fateful Bond** . If a match is not formed, Enmusubi gains a layer of**Frustration** . When she gains 5 layers, a match between two allies is guarantee to be formed next time.
  - **Frustration** : When she gains 5 layers, consumes all layers to dispel or remove all controlling effects on her and lowers the Move Bar of all enemies by 25%. She loses 2 layers when a match is formed.
  - It now takes a shorter time for her to use Divine Power when it's triggered.

- Adjustment to **Hollowfication** :
  - Effect for **Hollowed** form changed to: After gaining 4 layers of**Reiatsu** , Ichigo will enter his**Hollowed** form.
  - Release condition for **2nd Stage Hollowed** changed to: Using**Tensa Zangetsu** or**Getsuga Tensho** 4 times releases Ichigo from his hollowed forms.
  - Unlock condition for **Final Getsuga Tensho** changed to: When Ichigo gains 1 layer of**Reiatsu** for the first time,**Final Getsuga Tensho** will be unlocked.
- Effect for 
- When auto-battle is enabled, Ichigo Kurosaki will prioritize using **Hollowfication** to enter his**2nd Stage Hollowed** form.

- Effects added to the **Dance of the Wind** skill:
  - If the target is inflicted with **Golden Feather** , she launches an additional attack for each layer of**Golden Feather** on her and her target. She can inflict up to 4 attacks in total.
- If the target is inflicted with 
- **Golden Feather** skill effects improvement:
  - At the start of her turn, she gains 1-3 layers of **Golden Feather** . When she takes damage, she transfers 1 layer onto the damage dealer (stackable up to 3 layers). When she's KO'd, each enemy with**Golden Feather** takes damage equal to 40% of her ATK for each layer of**Golden Feather** on them, consuming all layers.
  - **Golden Feather** status effects improved: When inflicted on an enemy, 1, 2, and 3 layers inflict 6%, 18%, and 36% Damage Down and Vulnerability respectively.
  - Level-up effects improved:
    - **Lv. 2** :**Golden Feather** 's Damage Down and Vulnerability effects increased to 7%, 21% and 42% respectively.
    - **Lv. 3** :**Golden Feather** 's Damage Down and Vulnerability effects increased to 8%, 24% and 48% respectively.
    - **Lv. 4** :**Golden Feather** 's Damage Down and Vulnerability effects increased to 9%, 27% and 54% respectively.
    - **Lv. 5** :**Golden Feather** 's Damage Down and Vulnerability effects increased to 10%, 30% and 60% respectively.
- At the start of her turn, she gains 1-3 layers of 
- **Feather Dance** skill effects improved:
  - She rises into the air and dives into the enemy's lineup to land an attack, dealing damage equal to 60% of her ATK. For each layer of **Golden Feather** she has, she inflicts additional damage equal to 36% of her ATK on them. On each enemy with**Golden Feather** , she inflicts additional damage equal to 40% of her ATK for each layer of**Golden Feather** on them, consuming all layers.
  - Level-up effects improved:
    - **Lv. 2** : Damage of the first attack increased to 63%.
    - **Lv. 3** : Damage of the first attack increased to 66%.
    - **Lv. 4** : Damage of the first attack increased to 69%.
    - **Lv. 5** : Damage of the first attack increased to 72%.
- She rises into the air and dives into the enemy's lineup to land an attack, dealing damage equal to 60% of her ATK. For each layer of 

- Effects added to the **Evil Light** skill: Dodomeki deals indirect damage equal to 211% of her ATK to them (this part remains unchanged), as well as additional indirect damage equal to 8% of their max HP (increased by 100% for each**Evil Light** the enemy team has, up to 600% of her ATK). After this,**Gaze** is removed from all enemies.

- Effects added to the **Lv. 5** effects of the**Graceful Agility** skill: If she gains 4 buffs from**Graceful Agility** , her**Dance of Hope** 's orb cost is reduced by 2.
- **Dance of Hope** skill effects improvement:
  - Dispels 3 debuffs or controlling effects on 1 ally, and restores their HP by 30% of her max HP. If there is excess HP after they are fully healed, a shield is created to protect the ally. The shield absorbs damage equal to 5% of her max HP and lasts 2 turns. After this, the ally gains **Butterfly Dance** for 3 turns.
  - Level-up effects improved:
    - **Lv. 2** : Healing is increased to 31% and**Butterfly Dance** 's healing effect to 9% each time.
    - **Lv. 3** : Healing is increased to 33% and**Butterfly Dance** 's healing effect to 10% each time.
    - **Lv. 4** : Healing is increased to 34% and**Butterfly Dance** 's healing effect to 11% each time.
    - **Lv. 5** : Healing is increased to 36% and**Butterfly Dance** 's healing effect to 12% each time.
  - **Butterfly Dance** status effect improved: it now increases SPD by 20 and heals HP by 8% of Chocho's max HP when damage is taken (can be triggered up to once each turn).
- Dispels 3 debuffs or controlling effects on 1 ally, and restores their HP by 30% of her max HP. If there is excess HP after they are fully healed, a shield is created to protect the ally. The shield absorbs damage equal to 5% of her max HP and lasts 2 turns. After this, the ally gains 

- Effects added to the **Unheard Counter** skill: When dealing with damage, gains**Drizzle** for 2 turns.
  - **Drizzle** : Increases Effect RES by 30% and SPD by 30.**Water Circuit** 's orb cost is reduced by 1.
- Effects added to the **HP Connection** status effect: When an ally takes critical damage if they don't have Isolation, they lose**HP Connection** to block the damage. Increases an ally's damage dealt by 20% if it's not on their turn.

- The skill effects of **Wind** have been modified as follows:
  - Charges at 1 enemy and launches a 2-strike attack, dealing damage equal to 76% of his ATK with each strike. The strikes are guaranteed to land critical hits if the HP of the target is below 35%.
  - No changes have been made to the skill level-up effect.
- The effect of the **Trapped Beast** status he gains via the skill**Violent** has been modified as follows:
  - Increases ATK by 10% and Effect RES by 50%.
  - No changes have been made to the skill level-up effects.

- The skill effects of **Wings of Steel** have been modified as follows:
  - When dealing damage, has a 50% chance of gaining **Heroic Posture** , stackable for up to 10 layers and lasting until the round ends.
  - The level-up effects have been changed to:
    - **Lv. 2** Effects:**Heroic Posture** stacks up to 30 layers.
    - **Lv. 3** Effects:**Heroic Posture** stacks up to 50 layers.
    - **Lv. 4** Effects:**Heroic Posture** stacks up to 80 layers.
    - **Lv. 5** Effects: When Shelter negates a controlling effect, his Move Bar is raised by 50%.
- When dealing damage, has a 50% chance of gaining 
- The effect of the **Heroic Posture** status has been modified as follows: Each layer increases damage by 1%.

- The effects of **Mirror's Protection** have been modified as follows: When the effect is triggered, the HP of the ally with the lowest proportion of HP is recovered by 240% of Ungaikyo's DEF.

- The following effects have been added to the skill **Lantern Support** (both before and after her evolution):
  - During an ally or an enemy's turn, if your orbs overflow, Aoandon gains a layer of **Candlelight** (mark). When she has 3 layers of**Candlelight** ,**Lantern Support** is triggered when your next ally takes action, consuming all layers of**Candlelight** . Can be triggered up to once each turn.
- During an ally or an enemy's turn, if your orbs overflow, Aoandon gains a layer of 

- The skill effects of the skill **Forbidden Masks** have been modified as follows:
  - When activated, instead of granting **Masks of Goodwill** to allies, it now releases 7 masks. The full effects of the updated skill (after her evolution) are as follows:
    - Recalls all 7 masks, raising the Move Bar of allies with **Mask of Goodwill** by 20% and inflicting 130% Indirect Damage to enemies with**Mask of Evil** (increases by 10% for each layer of**Mask of Evil** ). Then, releases 7 masks, first granting them to other allies as**Mask of Goodwill** , then inflicting the rest on enemies as**Mask of Evil** (first inflicted on enemies without**Mask of Evil** , then on enemies with lower proportion of HP).
    - **Upper Hand** : Exclusive effect. Releases her 7 masks. Menreiki cannot wear**Mask of Goodwill** .
  - Recalls all 7 masks, raising the Move Bar of allies with 
  - No changes have been made to the level-up effect.
- When activated, instead of granting 

- The following effects have been added to the skill **Sword Flurry** : Inflicts**Tailed** on the counter-attack target for 1 turn. If 2 or more enemies have**Tailed** ,**Sword Flurry** 's orb cost is reduced by 2.
  - **Tailed** : Reduces ATK by 35%.

- The skill effect of the skill **Warm Protection** has been modified as follows: The HP she needs to spend has been reduced from 30% to 25%.

- Her initial SPD has been increased to 108 and her SPD after evolution to 118.
- The skill effects of **Bowl Barrage** have been been modified as follows:
  - The skill costs 1 orb.
  - When an enemy uses a normal attack, her Move Bar is raised by 5%.
  - **Active skill** : Sends her bowl charging at 1 enemy, dealing damage equal to 130% of her ATK with a 50% base chance of inflicting Silence lasting 1 turn on them. Also, lowers their Move Bar by 40%.
  - No changes have been made to the level-up effect.
- The skill effects of **Silence Drop** have been modified as follows:
  - The skill costs 3 orbs and has a 2 turn cooldown.
  - Jumps into the air in her bowl and lands on all enemies, dealing damage equal to 130% of her ATK. Has a 60% base chance of inflicting Silence lasting 1 turn on them. Also lowers the Move Bar of units unaffected by Silence by 20%.
  - The level-up effects have been changed to:
    - **Lv. 2** : Increases damage to 137%.
    - **Lv. 3** : Increases damage to 144%.
    - **Lv. 4** : Increases damage to 151%.
    - **Lv. 5** : Increases damage to 158%.

- A **Lv. 4** effect has been added to the**Bunny Dance** skill: After she takes an action, the ally at the bottom of the turn order gains a 40% ATK increase from**Bunny Dance** .
- The **Lv. 5** effects of**Ring Toss** have been modified as follows: Increases damage to 285% (no changes have been made to the level-up effect so far). If she manages to inflict Morph on the target, she immediately uses**Bunny Dance** again without spending any orbs.

- Her evolution effect has been improved: The Effect RES increase granted has been raised from 25% to 40%.
- Improved the wording of the **Zen** skill's description and the skill's level-up effects (no changes have been made to the original effects). The modifications are as follows:
  - Meditates for 2 turns. While she meditates, if she's not unable to take action, each of her allies has a 40% chance of 1 debuff or controlling effect being dispelled (increases by 10% for each bead she has). Each one successfully dispelled restores their HP by 3% of Juzu's max HP and raises their Move Bar by 30% at the cost of 1 bead at the end of their turn. If the dispelling fails, their Effect RES is increased by 40% for 1 turn.
  - No changes have been made to the level-up effect.

- **Meditation** 's skill effects after the update:
  - At the end of her turn, if Hakuro is not in a recharging state, she enters a meditative state. While in the meditative state, her Crit DMG is increased by 20% until the end of her next turn. Also creates a shadow double that cannot be attacked. The shadow double has a 30% chance of preventing Hakuro from taking any damage.
- **Non-Self** 's skill effects after the update:
  - Channels all of her energy into an arrow, increasing the Crit of the attack by 30% before dealing damage equal to 237% of her ATK to 1 enemy. Also lowers their Move Bar by 20%, or by 50% instead if she's in a meditative state. If their Move Bar is lowered to zero, 1.5x the damage is dealt instead. She then enters a recharging state, reducing her SPD by 40%.
  - After-evolution skill effects after the update: If the enemy is KO'd, raises her Move Bar by 90%.

Designer's note:

*"We noticed that Hakuro, one of the most iconic single damage dealers from the early stage of the game, hasn't been performing that well in various scenarios in the current metagame. So we made some improvements to her skills for this update. We hope to improve the stability of Hakuro's chance of entering the meditative state, as well as her chances of survival once she enters the meditative state, to solve the problem of her lack of versatility as a pure damage dealer. We've also improved her Non-Self skill by adding a Move Bar-lowering effect and explosive damage in order to increase her power and attack tempo."*

- **Cocoon Burst** 's skill level-up effects after the update:
  - **Lv. 3** : After the explosion, inflicts another Poison of 1 grade higher, lasting 1 more turn.
  - **Lv. 5** : Increases Okikumushi's SPD by 10 for each enemy with Poison.
- **Caterpillar Venom** 's skill level-up effects after the update:
  - Also inflicts **Bug's Grudge** on the target she stared at, dealing indirect damage equal to 105% of her ATK, and copies the Poison effect on another enemy she caused to explode during the attack. Has a 100% base chance of inflicting this copy on the target she stared at, lasting 2 turns.
  - Effects of **Bug's Grudge** : Inflicts indirect damage at the end of the turn.
- Also inflicts 

*"When designing Okikumushi, we tried to make her a support shikigami who can help by inflicting Poison, and who focuses on inflicting Poison quickly on a single enemy to deal indirect damage, giving her a place among the damage dealers. There were problems with her passive skill Cocoon Burst when the skill caused a Poison explosion – the newly created Poison had a chance of being negated and its duration could be too short to take effect. These problems are solved with this update.*

*In addition, we improved her Caterpillar Venom skill after her evolution. The skill used to deal direct damage that was affected by all layers and grades of Poison. Now the skill inflicts indirect damage (at the target's turn end). This works better with her own ability to inflict Poison, and the indirect damage can effectively lower the target's HP."*

- **Flower Power** 's skill effects after the update:
  - When attacked, heals her HP by 15% of her ATK. Triggers only once for a single attack. If the source of the damage has a lower ATK than Kusa's, reduces the damage taken by Kusa by 30%.
- **Healing Light** 's skill effects after the update:
  - Effective exclusively.
  - Carries 2 **Blessed Seeds** at the start of the battle. Each**Blessed Seed** increases her own ATK by 60%.
  - **Active skill** : Grants a**Blessed Seed** to an ally before healing the HP of all allies by an amount equal to 87% of her ATK. Also grants them**Photosynthesis** lasting 2 turns, healing their HP by 22% of her ATK on each turn.
  - **Blessed Seed** 's skill effects: When Kusa has a**Blessed Seed** , each**Blessed Seed** increases Kusa's ATK by 60%. When Kusa receives healing, the HP of the ally with a**Seed** will be recovered by an equal amount.
  - The effects of **Photosynthesis** remains the same after the update.
- Kusa will prioritize using **Healing Light** when the player selects Skill for her in Auto mode.

*"Relating the ATK stat to the healing amount is an exclusive design choice for Kusa. We hope players can increase Kusa's ATK to improve her overall power through Blessed Seed, and come up with different Soul set configurations to ensure she is seen more in different scenarios."*

- **Sunlit Fox Realm** :
  - Now the effect works exclusively.
  - The Move Bar-raising effect now correctly works on the target appears "at the top of the turn order" instead of the next target who would take the next turn order.
  - The Move Bar-raising effect now correctly works on "another ally". A target will no longer receive multiple Move Bar-raising effects granted this way.
  - **Lv. 3** level-up effects improved:
    - Before: Increases dispelling chance to 80%.
    - After: Increases dispelling chance to 60%.
  - **Lv. 4** level-up effects improved.
    - Before: Increases debuffs to be dispelled to 2.
    - After: Increases dispelling chance to 80%.
- **Moonlit Fox Realm** :
  - The debuff that lasts 2 turns inflicted by Fox Bell when the enemy ends their turn will no longer be replaced by the debuff that lasts 1 turn inflicted by her normal attack.

- We will be issuing compensations to all players who have a Divine Miketsu for this improvement:
  - For each grade 6 Divine Miketsu owned, a Grade 6 Shikigami Exchange Amulet will be issued in compensation.
  - For each grade 5 Divine Miketsu owned, a Grade 5 Shikigami Exchange Amulet will be issued in compensation.
  - For each Divine Miketsu owned who had her skill leveled up, regardless of her grade, a Skill Daruma will be issued in compensation for each skill leveled up, up to a maximum of 3 Skill Daruma.
  - For example, if a player has a grade 6 Divine Miketsu (skill levels at 5/5/5) and a grade 5 Divine Miketsu (skill levels at 1/2/1), the total compensation for them will be one Grade 6 Shikigami Exchange Amulet, one Grade 5 Shikigami Exchange Amulet, and 4 Skill Daruma.
  - Compensation claiming time: After maintenance on Jul 10th to Aug 10th, 23:59, 2019
- In the meantime, we're setting the rules for compensation for SP shikigami:
  - For each grade 6 SP shikigami owned, a Grade 6 Shikigami Exchange Amulet will be issued in compensation.
  - For each grade 5 SP shikigami owned, a Grade 5 Shikigami Exchange Amulet will be issued in compensation.
  - For each SP shikigami owned who had their skill leveled up, regardless of their grade, a Skill Daruma will be issued in compensation for each skill leveled up, up to a maximum of 3 Skill Daruma.

- **Recovery** :
  - Now, when she has the **Dance of Recovery** status, she will no longer use the skill again.
- Now, when she has the 

- **Threads Connection** :
  - The needle and thread summoned that inherits HP from the target now has an HP limit equal to 300% of Kosodenote's max HP.

- **Cursed Eye** :
  - Now when she inflicts **Gaze** on monsters, the cost for the**Evil Light** skill that substituted their skills will not exceed their orb limit.
- Now when she inflicts 

- **Recovery** :
  - Skill effect balance, changing "if she's not inflicted with Morph" to "if she isn't unable to take action".
  - Dance of Recovery now lasts 1 turn instead of 4 turns.
  - Dance of Recovery now stacks up to 1 layer instead of 4 layers.
  - Increased the healing efficiency of **Dance of Recovery** to 10%/25% at**Lv. 3** to 40%/100% at**Lv. 3** .
  - **Lv. 2** effect now changed to**Dance of Recovery** also grants 50% Effect RES.
  - **Lv. 4** effect now changed to: Increases the duration of**Dance of Recovery** to 2 turns.
- **Sakura Blizzard** :
  - Heal Down effect can now be dispelled.
  - **Lv. 4** effect now changed to Increases Heal Down effect to 60%.
  - **Cherry Blossom** now lasts 1 turn instead of 2 turns.
  - Increased **Cherry Blossom** 's indirect damage dealt from 7%/11%/15% to 9%/14%/19%.
  - Changed **Cherry Blossom** 's indirect damage dealt limit from 325% of Sakura's ATK to 370% of her ATK.

- **Empowering Flow** :
  - Deals an extra 20% damage when landing a critical hit, but inflicts Empowering Flow (Reduces DEF by 20%. Whenever he deals damage, if the target has higher DEF, the damage dealt ignores 50% of the DEF difference.) lasting 1 turn on himself.
- **Swallow** :
  - Forms water into a shoal of fish that inflicts a 2-strike attack on 1 enemy, dealing damage equal to 53% of his ATK with a 100% base chance of inflicting Isolation lasting 2 turns on them on the first strike, and dealing damage equal to 211% of his ATK on the second strike. Damage taken cannot be shared by other effects, including Shouzu's skill Water Circuit and Soul Edge's effect, among others.
  - The first strike dispels 1-2 random buffs from the enemy. Each buff dispelled increases the damage of the second strike by 5%.
  - **Lv. 2** : Increases damage of the second strike to 226%.
  - **Lv. 3** : Increases damage of the second strike to 241%.
  - **Lv. 4** : Increases damage of the second strike to 256%.
  - **Lv. 5** : Increases damage of the second strike to 270%.
- Improvements made to Lord Arakawa in this update do not affect the skill effects of Lord Arakawa as a monster.

- Kaoru's skills have been extensively revamped with new mechanics added.
- **Interfering Throw** (originally**Stone Strike** )
  - Orb cost: Normal attack, costs no orbs
  - Viciously flings a stone at one enemy, dealing damage equal to 100% of her ATK.
  - Lv. 2: Increases damage to 105%.
  - Lv. 3: Increases damage to 110%.
  - Lv. 4: Increases damage to 115%.
  - Lv. 5: Additionally lowers the Move Bar of the target by 15% if the target has 4 or more buffs.
- **Vigilant Owl**  - Orb cost: Passive skill, costs no orbs
  - Effective exclusively.
  - At the beginning of each turn (either ally's or enemy's), a status change triggers, changing her status to either **Play** or**Alert** .
  - Kaoru usually stays in **Play** status. If 2 of her allies are under controlling effects, Kaoru's status will be changed to**Alert** .
  - **Play** status: Kaoru is usually in**Play** status.
  - **Alert** status: Increases SPD by 10 and Effect RES by 40%.
  - **Lv. 2** : When she's in**Alert** status, increases the Effect RES boost effect to 50%.
  - **Lv. 3** : When she's in**Alert** status, increases the Effect RES boost effect to 60%.
  - **Lv. 4** : When she's in**Alert** status, increases the SPD boost effect to 15.
  - **Lv. 5** : If she's in**Play** status, at the end of her turn, increases all damage dealt by allies by 10% until her status changes.
- **Warm Protection** :
  - Orb cost: 2 orbs
  - Spends 30% of her current HP to grant **Owl's Protection** to an ally. Sustainable for 1 turn. Dispels a debuff or controlling effect from each of her allies.
  - If Kaoru is in **Alert** status, allies under controlling effects gain**Owl's Dance** for 2 turns. Otherwise, gains 4 orbs.
  - **Owl's Protection** : When taking damage, absorbs and records all damage taken. When the mark fails, causes the ally to lose HP by 80% of the amount recorded.
  - **Owl's Dance** : Increases SPD by 50.
  - **Lv. 2** : When**Owl's Protection** fails, causes the ally to lose HP by 70% of the amount recorded.
  - **Lv. 3** : Reduces orbs required by 1.
  - **Lv. 4** : When**Owl's Protection** fails, causes the ally to lose HP by 60% of the amount recorded.
  - **Lv. 5** :**Upper Hand** : Grants**Owl's Protection** to the ally with the lowest HP. Sustainable for 1 turn.

- When **Tessaiga** evolved into**Black Tessaiga** , the accumulated status of**Force of Wind** will not be consumed anymore.

- After awakening **Barrier: Tenseiga** , if its effect of resisting deadly damage is triggered, Sesshomaru will gain a 30% HP Steal until the end of the turn.
- The **Fractured** mark added by**Meido Zangetsuha** and**Bakusaiga** will trigger an effect that decreases target's healing by 100% when the target's HP is less than 30%.

- Adjusted the indirect damage equal to 18% of target's current HP + 120% Yamakaza's ATK (max 150%) caused by the **Torn** effects inflicted by**Demonic Slash** after the target's turn to the indirect damage equal to 12% of target's current HP + 88% Yamakaza's ATK (max 320%). And the damage ignores target's DEF by 600.

- Adjusted the calculation order of Hiyoribou's Revive from reviving instantly to reviving after the skill takes effect. This was done to fix the fluctuation caused by calculating part of the revive amount.

- Increase the direct and subsequent damage caused by the skill **Death Penalty** of Hangan from 79% attack (max 95%) to 100% attack (max 125%)

- Skill 2 **Recovery** :
  - Orb cost: 3
  - Effective exclusively.
  - If she's not inflicted with Morph, at the end of an ally's action, restores their HP by 6% of her max HP; at the end of a turn, restores their HP by 9% of her max HP. Also restores her own HP by 4% of her max HP.
  - Using the skill grants her a layer of **Dance of Recovery** stacking up to 4 layers and lasting 4 turns.
  - **Dance of Recovery** : Increases healing efficiency by 10%.
  - **Lv. 2** : Increases HP restored at the end of a turn to 10%.
  - **Lv. 3** : Increases the healing efficiency of**Dance of Recovery** to 25%.
  - **Lv. 4** : Increases HP restored at the end of a turn to 11%.
  - **Lv. 5** : Reduces orbs required to 2.

*"We revamped Sakura's skills, adding effects when she uses her skills actively, while still keeping her original traits. Her skill Recovery can no longer be affected by Suppress and other similar effects besides Morph. Under most conditions, she can heal her allies. By using her skills actively, she can also increase her healing efficiency.*

*We're now allowing Sakura to increase her healing efficiency at the end of an ally's turn. By doing that, we believe players will no longer be troubled by the dilemma of whether they should increase her SPD or healing efficiency when they use Sakura as a healing shikigami. By lowering her SPD requirement, player s can now focus more on increasing Sakura's healing efficiency by investing more on increasing her HP.*

*Tips: "At the end of an action" and "at the end of a turn" are different in skill effects. A turn ends when the Move Bar reaches the bottom. Some effects grants a new turn. Healing triggers when turn ends. Action refers to the action triggered by some effects (ie. counter-attacks), which is also referred as pseudo-turn by players. Healing triggers when action ends."*

- Skill 3 **Sakura Blizzard** :
  - Orb cost: 3
  - Makes cherry blossoms fall from above to attack all enemies, dispelling 3 buffs from each enemy with a 50% base chance (100% after evolution) of inflicting a 50% Heal Down lasting 2 turns on them. Also inflicts a **Cherry Blossom** lasting 2 turns on them, dealing indirect damage equal to 7% of her max HP (up to a max of 325% of Sakura's ATK).
  - **Lv. 2** : Increases**Cherry Blossom** 's indirect damage to 11% of her max HP.
  -  **Lv. 3** : Increases**Cherry Blossom** 's indirect damage to 15% of her max HP
  - **Lv. 4** : Heal Down effect cannot be dispelled.
  - **Lv. 5** : If no buffs are dispelled, 1 orb is refunded.

*"The once complicated Sakura Blizzard is now simplified. The damage of Cherry Blossom is now related to the Sakura's HP that most players would invest on increasing. Sakura's orb refunding effect while dispelling no buffs can be as much effective when she uses Sakura Blizzard even there's no buffs on to be dispelled on enemies. With the revamp of the shikigami skill, we tweaked her AI a little."*

- If she has no **Dance of Recovery** , she uses**Recovery** .
- If an ally's HP is below 80%, she uses **Recovery** .
- If she has **Dance of Recovery** , and the HP of all allies are above 80%, she uses**Sakura Blizzard** .
- If all allies are KO'd, Sakura, alone on her own, uses **Sakura Blizzard** .

- Single damage and AoE damage will be judged on the real situation when dealing damage instead of whether the target was specified when using skills. Judgement criteria will be based on the visual effects together with skill descriptions. Collateral damage won't be regarded as single damage.
- In the skill description, using following expressions will be regarded as single damage: enemy target, each enemy, a random enemy, any enemy.
- Using following expressions will be regarded as AoE damage: all enemies, other enemies.
- After the judgement method is changed, the following effects will be influenced: Soul Edge, Kingyo's Goldfish: Aid.
- Before the update, some single-target skills can deal AoE damage but the AoE damage dealt will be shared. After the update, only a small part of the damage will be shared.

- **Blessed Water** :
  - Changed how the skill works: When a flurry of damage is dealt, the skill now calculates "the ally with the lowest proportion of HP" in a more timely manner, meaning that when a team has multiple allies with damaged HP, the skill targets more evenly when healing them, rather than targeting only 1-2 allies when healing.
  - Skill improvement: The healing effect is now triggered only by damage dealt by his own skills (extra damage inflicted, such as from the soul Seductress, no longer triggers the healing effect). When a target receives healing multiple times in an action, the healing efficiency is now reduced by 15% for each extra healing received.
- **Giant Waves** :
  - Reduced the skill-casting animation time from 5.2s to 2.9s to speed up the pace.
  - Damage increased: The skill now deals damage equal to 45% of his ATK instead of 39% when at the max level.

- Improved the AI of Nekomata in auto mode. **Meowlee Attack** is now prioritized before**Meownified Attack** when either of the below conditions is met.
  - When there is an enemy with HP below 70%.
  - When there is only one enemy left.

- **Cursed Eye** Adjustments:
  - Dodomeki uses her ominous Ghost Eyes to gaze upon her enemies, with a 100% (+ Effect HIT) chance of inflicting **Gaze** on them for 1 turn. When inflicted with**Gaze** , all skills that consume orbs will be changed to**Evil Light** . Using**Evil Light** causes enemies to take damage equal to 211% of Dodomeki's ATK and frees all allies from**Gaze** .
  - No changes have been made to the levelled up skill.
  - Damage dealt by the **Evil Light** skill of**Gaze** state will be converted to collateral damage.
- Dodomeki uses her ominous Ghost Eyes to gaze upon her enemies, with a 100% (+ Effect HIT) chance of inflicting 

- **Blood Fury** Adjustments:
  - Lost HP of Vampira will grant her a damage bonus. Every time her HP is decreased by 1%, her damage dealt will be increased by 4%.
- **Blood Embrace** Adjustments:
  - Vampira transforms into a bat and grabs the enemy. Deals damage equal to 131% of her ATK on the enemy. Also restores her HP by 20% of the damage dealt for 1 turn.
  - No changes have been made to the levelled up skill.
  - Evolution Effect Adjustments:
    - Vampira transforms into a bat and grabs the enemy. Deals damage equal to 131% of her ATK on the enemy. Also grants a bat shield with HP equal to 20% of damage dealt for 1 turn. Grabbed enemy will receive damage equal to 10% of its Max HP per turn. (Every single damage won’t exceed 400% of Vampira’s ATK.) Lasts for 2 turns.
  - Passive skill won’t be only triggered by the normal attack. HP Steal of **Blood Embrace** will be adjusted to forming a shield. Staggered damage dealt after evolution will be added into collateral damage.

- **Venom Frenzy** Adjustments:
  - Adjusted from decreasing target’s DEF from a certain percentage to decreasing target’s DEF by a fixed amount.
  - Every time target is poisoned by Kiyohime, target’s DEF will be decreased by 10 and max DEF will be decreased by 150 till battle ends.
  - Every time target is poisoned by Kiyohime, target’s DEF will be decreased by 20 and max DEF will be decreased by 300 till battle ends.
- **Sacrificial Fire** Adjustments on the basic rate and level of triggering Poisoned with skill:
  - Changed from a 60% chance of triggering LV.2 Poisoned to a 100% chance of triggering LV.3 Poisoned.
  - Duration remains to be 5 turns.

- **Hands of Hell** Adjustments:
  - Raised the damage dealt by the taking life state after the turn from 132% of ATK (Max Level: 152%) to 158% of ATK (Max Level: 182%).
  - Adjustments on the basic rate and level of triggering Poisoned with skill after evolution:
    - Changed from an 80% chance of triggering Lv.3 Poisoned to a 100% chance of triggering Lv.4 Poisoned.
    - Duration remains to be 1 turn.

- **Maple Shot** Adjustments:
  - Shoots maple leaves at an enemy, dealing damage equal to 100% of her ATK.
  - No changes have been made to the leveled up skill. Skill damage will be increased by level.
- **Explosive Death** Adjustments:
  - Momiji will summon a **Maple Doll** to target when attacking target.**Maple Doll** will last for 2 turns. Target possessed by**Maple Doll** will be cursed, under which a 50% chance of receiving damage equal to 18% of current HP after attacking with normal attack each time. (Can’t exceed 250% of Momiji’s ATK.)
  - **Lv.2** : Chance of triggering Curse increases to 60%. Damage dealt increases to 22% of current HP.
  - **Lv.3** : Chance of triggering Curse increases to 70%. Damage dealt increases to 26% of current HP.
  - **Lv.4** : Chance of triggering Curse increases to 80%. Damage dealt increases to 30% of current HP.
  - **Lv.5** : When target possessed by**Maple Doll** uses the skill that requires orbs, it grants a 50% chance to make target use 1 more orb.
- Momiji will summon a 
- **Dance of Death** Skill basic effect remains the same:
  - Momiji transforms maple leaves into blades and sends them flying through all enemies. Deals damage equal to 132% of her ATK.
  - No changes have been made to the leveled up skill. Skill damage will be increased by level.
  - Evolution Effect Adjustments:
    - When target possessed by the **Maple Doll** dies, all maple dolls will explode. Each doll will deal damage equal to 42% of Momiji’s ATK to all targets.
  - When target possessed by the 

- **No Mercy** Adjustments:
  - When Hangan deals damage, every time the target loses 1% of Max HP, Crit Rate will be increased by 1%. Deals 10% extra damage to revive enemies.
  - **Lv.2** : Extra damage dealt will be increased to 20%.
  - **Lv.3** : Extra damage dealt will be increased to 30%.
  - **Lv.4** : Extra damage dealt will be increased to 40%.
  - **Lv.5** : Every 1% exceeded Crit Rate will be converted to 1% Crit Damage.
  - Still unlocks after evolution.
- **Death Penalty** Adjustments:
  - Hangan sentences all enemies to death, dealing damage equal to 79% of his ATK. Adds a healing **Death Verdict** state that can absorb the damage of the same amount for 1 turn. This state can’t be dispelled and will only be removed after absorbing enough healing amount. If**Death Verdict** is not removed, the target will receive damage equal to 79% of Hangan’s ATK before next move.
  - Skill damage will be increased by 5% per level. (Including the original damage and the later collateral damage.)
- Hangan sentences all enemies to death, dealing damage equal to 79% of his ATK. Adds a healing 

- **Dance of the Wind** Adjustments:
  - When Itsumade Co-ops or is invited to battle, its attack attempts can be increased according to the amount of **Golden Feather** . Adjusted in order to keep the consistency of the game rules.
- When Itsumade Co-ops or is invited to battle, its attack attempts can be increased according to the amount of 

- **Woman Scorned Lv.3** Skill Adjustments:
  - Dealing damage grants a 100% (+Effect HIT) chance to trigger an LV.5 Poisoned to target. (Decreases target’s SPD by 10% and ignores 50 of target’s DEF when calculating collateral damage.) Inflicts the target with a **Cunning Mark** .**Cunning Mark** will deal collateral damage equal to 10% of Mio’s ATK to its host each turn.
  - Removed the requirement of inflicting **Cunning Mark** by launching critical hit. Damage dealt will be added to collateral damage and it will be adjusted to absolute hit. An effect of triggering Poisoned to a single target will be added as well.
- Dealing damage grants a 100% (+Effect HIT) chance to trigger an LV.5 Poisoned to target. (Decreases target’s SPD by 10% and ignores 50 of target’s DEF when calculating collateral damage.) Inflicts the target with a 

- **Drunken Stupor** Adjustments:
  - Tanuki has a 20% chance to fall asleep at the end of the turn. When it wakes up, it will restore 6% HP. It has a 50% chance to be woken up by an attack. After being woken up, it will add a **Drunk** mark to the attacker.
  - **Lv.2** : HP Regen +32%.
  - **Lv.3** : Move Bar will be increased by 30% after being woken up.
  - **Lv.4** : Chance of falling asleep increases up to 40%.
  - **Lv.5** : Add a**Drunk** Mark to all enemies after being woken up.
- Tanuki has a 20% chance to fall asleep at the end of the turn. When it wakes up, it will restore 6% HP. It has a 50% chance to be woken up by an attack. After being woken up, it will add a 
- **Fiery Moonshine** Adjustments:
  - Tanuki swigs a mouthful of wine and restores its HP by 18% of Max HP. Spits out flames that burn all enemies to deal damage equal to 12% of Tanuki’s current HP.
  - Skill effects after evolution: Tanuki swigs a mouthful of wine and restores its HP by 18% of Max HP. Spits out flames that burn all enemies to deal damage equal to 12% of Tanuki’s current HP. Ignites all **Drunk** Marks on target to form wine fire. Each layer of wine fire will last for 1 turn to decrease target’s DEF by 10% and deal collateral damage equal to Tanuki’s Max HP after target’s turn.
  - Original damage will be increased by 15% per level.
- Passive adds **Accelerator** and increases the efficiency of stacking**Drunk** Marks. Grants**Fiery Moonshine** the effect of restoring HP. Adjusted damage data and rules and all**Drunk** Marks will be used.

- **Blade of Justice** Adjustments:
  - Karasu Tengu charges at the enemy and unleashes and cuts into them with his blade. Deals damage equal to 80% of his ATK. Has a 30% chance to make 1 ally join the attack.
  - **Lv. 2** : Skill damage increases by 10%.
  - **Lv.3** : Chance of making ally join the attack increases up to 35%.
  - **Lv. 4** : Skill damage increases by 10%.
  - **Lv.5** : Chance of making ally join the attack increases up to 40%.
- **Purification Wings** Adjustments:
  - At the beginning of the turn, Karasu Tengu has a 50% chance to dispel 1 negative effect for 1 random ally. (Including Taunt, Freeze, Silence, Daze, Sleep, Morph, Confuse.)
  - Lv.2: **Purification Wings** chance increases up to 70%
  - Lv.3: **Purification Wings** chance increases up to 90%
  - Lv.4: When attacking with your ally, all negative effects will be dispelled.
  - Still unlocked after evolution.
- **Deadly Flock** Adjustments:
  - Karasu Tengu summons crows to attack all enemies to deal damage equal to 119% of ATK to each enemy according to the HP. When dealing damage to each target, it has a 30% chance to make 1 ally to join the attack. (Each ally can only help once.) Every time one target is killed, skill damage dealt will be increased by 20%. Can be increased up to 100%.

- **Noxious Spray** Adjustments:
  - Kyonshi Ototo sprays noxious mist at all enemies to deal damage equal to 76% of his ATK and targets will receive collateral damage equal to 22% of Kyonshi Ototo’s ATK for 2 turns. When collateral damage is dispelled, target enters the Poison state, under which ATK will be decreased by 40% over 2 turns.
  - Staggered damage will be added to the collateral damage. Poison state effect will be adjusted as decreasing DEF.

- **Dance of Hope** Adjustments:
  - Dispel 3 negative effects for 1 ally and restore HP equal to 30% of Chocho’s Max HP for the ally. (Original rate: 24%)
  - Triggers **Butterflies Dance** state for 3 turns. Restores 30% HP for Chocho in the coming 3 turns.

- **Soul Slash** Adjustments:
  - Warrior Soul decreases the hit of the targets possessed by dead souls by 10%.
  - **Lv.2** : Effect HIT decrease up to 20%.
  - **Lv.3** : Effect HIT decrease up to 30%.
  - **Lv.4** : Effect HIT decrease up to 40%.
  - **Lv.5** : When dead souls are dispelled, targets will lose 1 orb.
- **Restless Rage** Adjustments:
  - Releases the restless souls of the dead to attack all enemies, dealing damage equal to 108% of Warrior Soul’s ATK. Souls will last for 3 turns. If an enemy uses any orbs while being possessed, it will receive damage equal to 54% of Warrior Soul’s ATK times the number of turns the souls have left. Enemy’s healing effect will be decreased by 40% over 2 turns.
  - Skill damage will be increased by 5% per level.

- **Defensive Wall** Adjustments:
  - Increases all allies’ DEF by 40% and Nurikabe’s DEF by 20% for 2 turns.
  - Increased the DEF bonus and effective turns.

- His second skill, **Truth and Reasoning** , has now been changed as follows:
  - After an enemy takes an action, Medicine Seller has a 40% (50% after his evolution) chance of observing the identity of the target and inflicting a **Scale** mark on them. The target can be inflicted with up to 3**Scale** Marks and cannot be dispelled. When Medicine Seller attacks a target with a**Scale** mark, each Scale mark increases his damage by 33%. Target with 1/2/3**Scale** marks will be revealed by Medicine Seller when their HP drops below 30%/40%/60%. Revealed state lasts 2 turns. Multiple Medicine Sellers do not cause the effect to stack.
  - In addition, **Scale** marks can now be inflicted onto Ushi no Toki's straw doll.
- After an enemy takes an action, Medicine Seller has a 40% (50% after his evolution) chance of observing the identity of the target and inflicting a 
- His third skill, **Defense** , has now been changed as follows:
  - Medicine Seller releases his sword and transforms into his inner self to attack a target, dealing damage equal to 263% of his ATK. Inflicts a **Scale** mark on the target if it's not KO'd by the attack. For a revealed target, damage (to a maximum of 600% of Medicine Seller's ATK) equal to their remaining HP is inflicted instead. The damage cannot be shared, transferred, or absorbed and ignores the target's soul effects and passive skills.
- Medicine Seller releases his sword and transforms into his inner self to attack a target, dealing damage equal to 263% of his ATK. Inflicts a 

Designer's comments:

*"The chance of Defense inflicting a Scale mark on the enemy has been increased from 75% to 100%. With this improvement, we hope to allow Medicine Seller to be more active when selecting his target while making the skill more stable.*

*The damage from Defense has been increased from 500% of Medicine Seller's Attack to 600% of his Attack. With this improvement, we hope to give him more stability when he tries to KO a revealed target.*

*We increased the damage inflicted on the target by Medicine Seller with Scale mark, hoping to allow him to deal a significant amount of damage even without the help of other powerful damage-dealing shikigami. The Critical Hit Rate and Critical Damage should also have an important impact on the battlefield in certain cases. Please note when using Defense to attack a revealed target that the damage dealt will not exceed 600% of Medicine Seller's Attack."*

- Effect removed from **Black Flame** : Has a 30% chance of increasing the damage the enemy takes by 20% for 2 turns.
- Effect added to **Rage Outlet** : When Ibaraki Doji's attack fails to KO an enemy, he gains a layer of**Enraged Arm** , increasing his damage by 33%.**Enraged Arm** stacks up to 3 layers.

- Her second skill, **Poisonous Beauty** , has been changed as follows:
  - Swiftly shoots a batch of feathers at all enemies, inflicting 2 layers of **Poisonous Feathers** on them. The enemy takes indirect damage equal to 1%/3%/6%/10%/15% (based on the layers of**Poisonous Feathers** it has) of its max HP at the beginning of its turn, to a maximum of 280% of Chin's ATK.**Poisonous Feathers** stack up to 5 layers and are reduced by 1 layer when the target takes poison damage.
  - Skill effects after level up:
    - **Lv. 2** : Increases indirect damage from**Poisonous Feathers** by 50%.
    - **Lv. 3** : Each layer of**Poisonous Feathers** on an enemy causes the indirect damage inflicted by Chin to ignore an extra 50 DEF when it's dealt to the enemy.
    - **Lv. 4** : Increases indirect damage from**Poisonous Feathers** by 50%.
    - **Lv. 5** : Any enemy with 5 layers of**Poisonous Feathers** takes damage equal to 30% of its max HP immediately when inflicted with**Poisonous Feathers** , to a maximum of 280% of Chin's ATK.
- Swiftly shoots a batch of feathers at all enemies, inflicting 2 layers of 
- Her third skill, **Poison Erosion** , has now been changed as follows:
  - Chin releases the toxins in her feathers to wreak vengeance on 1 enemy, dealing damage equal to 175% of her ATK and igniting all of Chin's feathers on the enemy, dealing an extra indirect damage equal to 35% x **Poisonous Feathers** layer count.
  - Skill effects after level up:
    - **Lv. 2** : All damage from the skill increases by 5%.
    - **Lv. 3** : All damage from the skill increases by 5%.
    - **Lv. 4** : All damage from the skill increases by 5%.
    - **Lv. 5** : All damage from the skill increases by 5%.
- Chin releases the toxins in her feathers to wreak vengeance on 1 enemy, dealing damage equal to 175% of her ATK and igniting all of Chin's feathers on the enemy, dealing an extra indirect damage equal to 35% x 
- Also, Chin's skill using AI has been optimized in auto mode.

*"After a period of observation and collection of statistics, we found that Chin's ability to deal a lot of damage has declined to some extent since indirect damage was adjusted. The main reason behind this is that the poison damage from Chin's feathers was decreased after the update, while her Poison Erosion, which players used less often, is still not being used effectively.*

*We hope to make Chin a mid-ranged damage-dealing shikigami whose expertise lies in dealing indirect damage. First, we increased her feathers' ability to deal high damage in this adjustment, adding an effect that allows her to ignore Defense. In addition, we removed the ability to deal direct damage from Poisonous Beauty, making the skill focus mainly on inflicting feathers and Poison debuffs. In this way, we improved Chin's ability to deal large amounts of damage. We also changed the damage type of part of the explosive damage dealt by Poison Erosion into indirect damage. This allows players to make consistent decisions when configuring her stats and choosing Souls for her. Again, we tried to make a single-target damage-dealing shikigami with the ability to deal explosive indirect damage. Now that we have changed the level up effects of her Poison Erosion from increasing the direct skill damage by 5% to increasing all damage (including indirect damage) from the skill by 5% (though we decreased the rate of damage from Poison Erosion by a fairly small percentage), Chin now has another build that allows her to deal damage mainly by using her Poison Erosion."*

- Poison is a common type debuff that can be dispelled and is affected by Effect HIT and Effect RES. Poison has 9 grades. Its effect reduces target's SPD by 10% and ignores target's DEF when resolving indirect damage by 10 x Poison debuff grade. The DEF ignoring effects from different grades of Poison can be stacked to unlimited layers, but only one instance of SPD reducing effect is effective. Details of each grade are as follows:
- **Grade I (1) Poison** : Reduces target's SPD by 10% and ignores 10 of target's DEF when resolving indirect damage.
- **Grade II (2) Poison** : Reduces target's SPD by 10% and ignores 20 of target's DEF when resolving indirect damage.
- **Grade III (3) Poison** : Reduces target's SPD by 10% and ignores 30 of target's DEF when resolving indirect damage.
- **Grade IV (4) Poison** : Reduces target's SPD by 10% and ignores 40 of target's DEF when resolving indirect damage.
- **Grade V (5) Poison** :  Reduces target's SPD by 10% and ignores 50 of target's DEF when resolving indirect damage.
- **Grade VI (6) Poison** : Reduces target's SPD by 10% and ignores 60 of target's DEF when resolving indirect damage.
- **Grade VII (7) Poison** : Reduces target's SPD by 10% and ignores 70 of target's DEF when resolving indirect damage.
- **Grade VIII (8) Poison** : Reduces target's SPD by 10% and ignores 80 of target's DEF when resolving indirect damage.
- **Grade IX (9) Poison** : Reduces target's SPD by 10% and ignores 90 of target's DEF when resolving indirect damage.
- Examples:
  - If a target is inflicted with 3 layers of Grade 4 Poison and a layer of Grade 2 Poison, the SPD of the target will be reduced by 10, and its DEF will be ignored by 3×40+1×20=140 when indirect damage is resolved.
  - If the target's DEF is below 140, its DEF will be treated as 0 when resolving indirect damage.

- The controlling effects negating trigger of Hana's **Painting Realm** has been updated:
  - When one of your units is already under the controlling effect of a debuff, if a new debuff of the same kind is inflicted on it, **Flying Bird** no longer triggers to negate the controlling effect.
  - If one of your units is inflicted by multiple kinds of controlling effects from one attack, **Flying Bird** 's chance of negating controlling effects triggers for each kind.
- When one of your units is already under the controlling effect of a debuff, if a new debuff of the same kind is inflicted on it, 

- After skill adjustments:
- **Random Element** :
  - Ryomen randomly uses Raijin or Fujin to strike an enemy target, dealing damage equal to 100% of his ATK if Raijin strikes or dealing damage equal to 25% of his ATK if Fujin strikes, and inflicts a **Wind Fury** mark on the target for 1 turn, dealing indirect damage equal to 125% of his ATK after target takes its turn.
  - Skill effect after level up:
    - **Lv. 2** : All damage from the skill increases by 5%.
    - **Lv. 3** : All damage from the skill increases by 5%.
    - **Lv. 4** : All damage from the skill increases by 5%.
    - **Lv. 5** : All damage from the skill increases by 10%.
- Ryomen randomly uses Raijin or Fujin to strike an enemy target, dealing damage equal to 100% of his ATK if Raijin strikes or dealing damage equal to 25% of his ATK if Fujin strikes, and inflicts a 
- **Eyes of Wrath** :
  - When Raijin attacks, the enemy's DEF is decreased by 10%. When Fujin attacks, the enemy's ATK is decreased by 10%.
  - Skill effect after level up:
    - **Lv. 2** : The skill now decreases DEF and ATK by 12%.
    - **Lv. 3** : The skill now decreases DEF and ATK by 14%.
    - **Lv. 4** : The skill now decreases DEF and ATK by 16%.
    - **Lv. 5** : Raijin lowers the Move Bar of all enemies with ATK lower than his by 8% when he deals damage. Fujin raises Ryomen's Move Bar by 8% when he deals indirect damage to enemies with DEF lower than his.
- **Divine Combo** :
  - Ryomen jumps into the enemy lineup to attack all enemies 3 times with Raijin or Fujin at random, dealing damage equal to 44% of his ATK if Raijin attacks or dealing damage equal to 11% of his ATK if Fujin attacks and inflicts a **Wind Fury** mark on the targets for 1 turn, dealing indirect damage equal to 55% of his ATK after they take their turns.
  - Skill effect after level up:
    - **Lv. 2** : All damage from the skill increases by 5%.
    - **Lv. 3** : All damage from the skill increases by 5%.
    - **Lv. 4** : All damage from the skill increases by 5%.
    - **Lv. 5** : All damage from the skill increases by 10%.
- Ryomen jumps into the enemy lineup to attack all enemies 3 times with Raijin or Fujin at random, dealing damage equal to 44% of his ATK if Raijin attacks or dealing damage equal to 11% of his ATK if Fujin attacks and inflicts a 

- After skill adjustments:
- **Soul Hunt** :
  - Summons 1 ghost with HP equal to 10% of Shiro Mujou's HP where an enemy was KO'd. The ghost will deal indirect damage to all enemies equal to 50% of Shiro Mujou's ATK after 1 turn and disappear. The target cannot be revived while the ghost is present. Whenever an enemy is KO'd, the Move Bar of Shiro Mujou is immediately raised by 50%.
  - Skill effect after level up:
    - **Lv. 2** : Ghost's HP increases to 15% of Shiro Mujou's HP. Indirect explosion damage increases to 60% of Shiro Mujou's ATK.
    - **Lv.3** : Ghost's HP increases to 20% of Shiro Mujou's HP. Indirect explosion damage increases to 70% of Shiro Mujou's ATK.
    - **Lv. 4** : Ghost's HP increases to 25% of Shiro Mujou's HP. Indirect explosion damage increases to 80% of Shiro Mujou's ATK.
    - **Lv. 5** : Ghost's HP increases to 30% of Shiro Mujou's HP. Indirect explosion damage increases to 90% of Shiro Mujou's ATK.
- **Hands of Hell** :
  - Shiro Mujou summons cursed hands from hell to attack all enemies 3 times consecutively, dealing damage equal to 32% of his ATK on each hit. Also inflicts a **Commanding Banner** mark on the targets for 1 turn, dealing indirect damage equal to 132% of his ATK  after they take their turns.
  - Skill effect after level up:
    - **Lv. 2** : Indirect damage increases by 5%.
    - **Lv. 3** : Indirect damage increases by 5%.
    - **Lv. 4** : Indirect damage  increases by 5%.
    - **Lv. 5** : Indirect damage lasts an extra turn.
- Shiro Mujou summons cursed hands from hell to attack all enemies 3 times consecutively, dealing damage equal to 32% of his ATK on each hit. Also inflicts a 
- Skill effect after evolution: Each hit has an 80% (+ Effect HIT) chance of inflicting a layer of Poison III (reduces target's SPD by 10% and ignores 30 of target's DEF when resolving indirect damage) on the targets for 1 turn.

- After skill adjustments:
- **Serpent Lash** :
  - Kiyohime whips 1 enemy, dealing damage equal to 86% of her ATK with a 100% (+ Effect HIT) chance of inflicting a layer of Poison III (reduces target's SPD by 10% and ignores 30 of target's DEF when resolving indirect damage) on the target for 5 turns. Also inflicts a **Viper mark** on the target for 1 turn, dealing indirect damage equal to 22% of her ATK after target takes its  turn.
  - Skill effect after level up:
    - **Lv. 2** : Skill damage increases by 5%.
    - **Lv. 3** : Skill damage increases by 5%.
    - **Lv. 4** : Skill damage increases by 5%.
    - **Lv. 5** : Skill damage increases by 5%.
    - **Lv. 6** : Viper marks deal an extra 50% indirect damage.
- Kiyohime whips 1 enemy, dealing damage equal to 86% of her ATK with a 100% (+ Effect HIT) chance of inflicting a layer of Poison III (reduces target's SPD by 10% and ignores 30 of target's DEF when resolving indirect damage) on the target for 5 turns. Also inflicts a 
- **Venom Frenzy** :
  - When Kiyohime inflicts Poison on a target, she also reduces the target's DEF by 1% (to a max of 12% for a single target) indefinitely.
  - Skill effect after evolution:
    - When Kiyohime inflicts Poison on a target, she also reduces the target's DEF by 2% (to a max of 24% for a single target) indefinitely. This skill cannot be leveled up.
- **Sacrificial Fire** :
  - Kiyohime breathes fire at all enemies 3 times, dealing damage equal to 36% of her ATK on each hit  with a 60% (+ Effect HIT) chance of inflicting a layer of Poison II (reduces target's SPD by 10% and ignores 20 of target's DEF when resolving indirect damage) on her targets for 5 turns. Also inflicts a **Viper** mark on her targets for 1 turn, dealing indirect damage equal to 66% of her ATK after they take their turns.
  - Skill effect after level up:
    - **Lv. 2** : Skill damage increases by 5%.
    - **Lv. 3** : Skill damage increases by 5%.
    - **Lv. 4** : Skill damage increases by 5%.
    - **Lv. 5** :**Viper** marks deal an extra 50% indirect damage.
- Kiyohime breathes fire at all enemies 3 times, dealing damage equal to 36% of her ATK on each hit  with a 60% (+ Effect HIT) chance of inflicting a layer of Poison II (reduces target's SPD by 10% and ignores 20 of target's DEF when resolving indirect damage) on her targets for 5 turns. Also inflicts a 

- After skill adjustments:
- **Chin's Feathers** :
  - Chin swiftly shoots a feather at an enemy, dealing damage equal to 80% of her ATK and inflicting 2 layers of **Poisonous Feathers** on them. Has a 100% (+ Effect HIT) chance of inflicting a layer of Poison (grade equal to the current**Poisonous Feathers** layers; reduces target's SPD by 10% and ignores target's DEF when resolving indirect damage by 10 x Poison grade) on them for 2 turns.
  - No changes have been made to the leveled up skill.
- Chin swiftly shoots a feather at an enemy, dealing damage equal to 80% of her ATK and inflicting 2 layers of 
- **Poisonous Beauty** :
  - Swiftly shoots a flurry of feathers at all enemies, dealing damage equal to 33% of her ATK and inflicting 2 layers of **Poisonous Feathers** on them. Has a 100% (+ Effect HIT) chance of inflicting a layer of Poison (grade equal to the current**Poisonous Feathers** layers; reduces target's SPD by 10% and ignores target's DEF when resolving indirect damage by 10 x Poison grade) on them for 2 turns. The enemy takes indirect damage at the beginning of its turn equal to 2% of its max HP for each layer of**Poisonous Feathers** it has to a maximum of 40% of Chin's ATK.**Poisonous Feathers** stack up to 3 layers and are reduced by 1 layer when the target takes poison damage.
  - No changes have been made to the leveled up skill.
- Swiftly shoots a flurry of feathers at all enemies, dealing damage equal to 33% of her ATK and inflicting 2 layers of 

- After skill adjustments:
- **Spider Symbol** :
  - Jorogumo has a 40% (+ Effect HIT) chance of inflicting a **Spider** mark on an enemy for 2 turns when she deals damage. Any enemy with a**Spider** mark takes indirect damage equal to 100% of Jorogumo's ATK when using any orb.
  - This skill cannot be leveled up.
- Jorogumo has a 40% (+ Effect HIT) chance of inflicting a 
- **Arachnid Horde** :
  - Jorogumo summons a horde of spiders to deal damage to all enemies equal to 72% of her ATK with a 20% (+ Effect HIT) (+1% for each 5 SPD difference for targets that are slower than Jorogumo) chance of inflicting Daze on the targets.
  - Skill effect after level up:
    - **Lv. 2** : Skill damage increases by 5%.
    - **Lv. 3** : Skill damage increases by 5%.
    - **Lv. 4** : Skill  damage increases by 5%.
    - **Lv. 5** : Inflicts a**Spider Toxin** mark on Undazed targets for 1 turn, dealing indirect damage equal to 136% of her ATK (+1% indirect damage for each 1 SPD difference for targets that are faster than Jorogumo) after they take their turns.

- After skill adjustments:
- **Sakura Blizzard** :
  - Sakura makes cherry blossoms fall from above to attack all enemies, dispelling all buffs with a 50% (+ Effect HIT) chance of decreasing the healing effect the targets receive by 30% for 2 turns. Also inflicts a **Cherry Blossom** mark on the targets for 1 turn, dealing indirect damage equal to 76% of her ATK after they take their turns. Has a 25% chance of inflicting Sleep on the targets for 1 turn when dispelling their buffs.
  - Skill effect after level up:
    - **Lv. 2** : Heal Down effect enhancement: Decreases healing effects received by 40%.
    - **Lv. 3** :**Cherry Blossom** marks deal extra indirect damage to targets without any buff equal to 8% of Sakura's max HP (The damage does not receive ATK bonus from Judge Banner in Duel).
    - **Lv. 4** : Heal Down effect enhancement: Decreases healing effects received by 50%.
    - **Lv. 5** : Heal Down effect now cannot be dispelled.
- Sakura makes cherry blossoms fall from above to attack all enemies, dispelling all buffs with a 50% (+ Effect HIT) chance of decreasing the healing effect the targets receive by 30% for 2 turns. Also inflicts a 

- After skill adjustments:
- **Fortification** :
  - Aobozu anoints **Buddha's Blessing** (at least 1 layer and max at 6 layers) on his allies. Whenever an ally is inflicted with Taunt, Freeze, Silence, Daze, Sleep, Morph, or Confuse, a layer of**Buddha's Blessing** is added as well. When Aobozu ends his turn, a layer of**Buddha's Blessing** disappears. Each layer of**Buddha's Blessing** increases his and his allies' Effect RES by 30% and 15%, respectively.
  - This skill cannot be leveled up.
- Aobozu anoints 
- **Peaceful Heart** :
  - Aobozu uses a soul spell to attack all enemies, dealing damage equal to 185% of his ATK. Constrained by **Buddha's Blessing** , Aobozu's attack this time deals 10% less damage for each layer of**Buddha's Blessing** he has.
  - No changes have been made to the leveled up skill.
  - No changes have been made to the skill effects after evolution. It continues to deal double damage to summoned entities.
- Aobozu uses a soul spell to attack all enemies, dealing damage equal to 185% of his ATK. Constrained by 

- After skill adjustments:
- **Healing Light** (after evolution):
  - Kusa restores the HP of all allies by 87% of her ATK and grants a **Healing Dandelion** mark on them for 2 turns, restoring their HP by 22% of her ATK on each of their turns. The first indirect damage dealt to allies with the**Healing Dandelion** mark is converted to an equal amount of HP healed.
  - No changes have been made to the leveled up skill.
- Kusa restores the HP of all allies by 87% of her ATK and grants a 

- After skill adjustments:
- **Bubble Shield** :
  - Koi forms bubbles into an energy shield to protect all allies. The bubble shield absorbs damage equivalent to 12% of Koi's maximum HP. Lasts 2 turns.
  - Skill effect after level up:
    - **Lv. 2** : Shield absorbs an extra 16% damage.
    - **Lv. 3** : Shield absorbs an extra 16% damage.
    - **Lv. 4** : Shield absorbs an extra 16% damage.
    - **Lv. 5** : Protected allies take 50% less indirect damage.

- After skill adjustments:
- **Karma** :
  - Counter-attack damage is now increased to 136% from 120% of her ATK.
  - No changes have been made to the leveled up skill.
- **Zen** :
  - Juzu meditates for 2 turns. While she meditates, each of her allies has a chance (40% +Juzu's orb count x 10%) of 1 debuff being dispelled at the beginning of their turn. Each dispelled debuff restores their HP by 3% of Juzu's max HP; also their Move Bar is raised by 30% at the end of their turns. Consumes 1 orb after the effect is triggered. Under meditation, Juzu gains 1 orb immediately when all her orbs are consumed.
  - Skill effect after level up:
    - **Lv. 2** : Increases the HP restoration effect to 4% of Juzu's max HP.
    - **Lv. 3** : Increases the dispelled debuffs to 2.
    - **Lv. 4** : Increases the HP restoration effect to 5% ofJuzu's max HP.
    - **Lv. 5** : Increases the dispelled debuffs to 3.

- After skill adjustments:
- **Bamboo Shelter** :
  - Kanko hides in his bamboo pipe, taking shelter from attacks and recharging his power, raising his Move Bar by 30%. The pipe inherits 20% of Kanko's max HP and 200% of his DEF. If the pipe is destroyed, Daze is inflicted upon Kanko for 1 turn.
  - Kanko can hide in his pipe for consecutive turns but the pipe's HP does not refresh. Each additional turn Kanko hides in his bamboo pipe increase his next damage by 75% up to a maximum of 300%.
  - Skill effect after level up:
    - **Lv. 2** : Increases bamboo pipe's HP to 25% of Kanko's max HP.
    - **Lv. 3** : Increases bamboo pipe's HP to 30% of Kanko's max HP.
    - **Lv. 4** : Increases Effect RES by 100% when in pipe.
- **Bamboo Blast** :
  - Kanko channels magic into his bamboo pipe and shoots lightning at 1 enemy, dealing damage equal to 221% of his ATK with a 50% chance of removing 1 orb from his opponent. Chance increases to 100% when launching a critical hit.
  - No changes have been made to the leveled up skill.

- The skill "**Lantern Support** " of Aoandon has been modified as below:
  - At the beginning of an ally's turn, Aoandon has a 10% chance of lighting her Lantern for the ally for 1 turn. Using skills under the Lantern's effect costs no orbs.
  - **Lv. 2** Trigger chance increases to 12%.
  - **Lv. 3** Trigger chance increases to 14%.
  - **Lv. 4** Trigger chance increases to 16%.
  - **Lv. 5** Trigger chance increases to 40% but reduces by 3% for each orb you have.

- The skill "**Recovery** " of Sakura has been modified as below:
  - Let the flowers heal you. Sakura recovers the HP of an ally by 5% of the ally's max HP when the ally takes an action. Has a 5% chance of doubling the HP restored.
  - **Lv. 2** The chance of triggering HP recovery increases to 10%.
  - **Lv. 3** The chance of triggering HP recovery increases to 15%.
  - **Lv. 4** The chance of triggering HP recovery increases to 20%.
  - **Lv. 5** HP restored increases to 7%.

- **Tile Fling** :
  - Jikikaeru throws a number of mahjong tiles at a target based on the dice he rolled, dealing damage equal to 49% of his ATK for each tile.
  - **Lv. 2** Skill damage increases by 5%.
  - **Lv. 3** Skill damage increases by 5%.
  - **Lv. 4** Skill damage increases by 5%.
  - **Lv. 5** Skill damage increases by 5%.
- **Change of Luck** :
  - When Jikikaeru is KO'd, he uses **Tile Fling** on all enemies without spending any orbs. Revives Jikikaeru immediately if there are equal numbers among the dice he throws, and restores his HP by 10% x the minimum equaled number.
  - CD: The maximum equaled number.
- When Jikikaeru is KO'd, he uses 

- **Bamboo Blast** :
  - Kanko channels magic into his bamboo pipe, spending 10% of his current HP. He shoots lightning at 1 enemy, dealing damage equal to 155% of his ATK with a 40% chance of removing 1 orb from his opponent. Chance increases to 80% when launching a critical hit.
  - **Lv. 2** Skill damage increases by 5%.
  - **Lv. 3** Skill damage increases by 5%.
  - **Lv. 4** Skill damage increases by 5%.
  - **Lv. 5** Skill damage increases by 5%.
- **Bamboo Shelter** :
  - Kanko hides in his bamboo pipe to take shelter from attacks and recharges his power. The bamboo pipe inherits 15% of Kanko's max HP and 200% of his DEF. If the pipe is destroyed, Daze is inflicted on Kanko for 1 turn. Kanko can hide in his bamboo pipe consecutive times, but the pipe's HP does not refresh. Each additional turn Kanko hides in his pipe increases the damage of his next attack by 100% to a maximum of 500%.
  - **Lv. 2** Increases bamboo pipe's HP to 20% of Kanko's max HP.
  - **Lv. 3** Increases bamboo pipe's HP to 25% of Kanko's max HP.
  - **Lv. 4** Increases his Effect RES by 100% when he hides in his bamboo pipe.


- Every time target's HP is decreased by 15%, it will deal 10% extra damage to target.

- When dealing damage, it grants a 15% chance to freeze the target for 1 turn. (If the target is under Slow effect, the chance will be increased to 30%.) When being attacked, it can slow attack by 30 for 1 turn.

- When attacking, if the target is under controlled, damage dealt will be increased by 45%.

- Counters the attacker when resisting an effect and increases damage by 50%. Increases Move Bar by 25% when under control effect.

- When any target dies, it can restore HP by 20% of Max HP and increase damage by 20% (max: 120%) till battle ends.

- When dealing damage, she grants a 10% chance to inflict Daze to target for 1 turn. If no target is under Daze, the chance will be increased to 20%.

- Increases healing effect by 20% when healing (If target’s HP is lower than 20%, the healing effect will be increased by 50%)

- Grants target a shield that can’t be dispelled for 2 turns when healing to absorb damage equal to 30% healing.

- When an ally is under a controlling effect, ally’s speed will be increased by 30 for 2 turns. The effect won’t be dispelled and can be stacked by 2x.

- Every time target’s HP is decreased by 1%, crit damage dealt will be decreased by 0.5%.

- The only passive skill. When dealing damage to monsters, it will add 1 Tsuchigumo Mark on the monster to decrease its SPD by 10% and deal 10% collateral damage for 1 turn. Max: 3 marks.
- (Damage dealt by Tsuchigumo will be adjusted as collateral damage and will be influenced by Crit and Crit DMG. When target’s DEF is 0, it will launch a critical attack for sure. Damage adjusted to 10% accordingly.)

- The only passive skill. Increases damage dealt with monsters by 10%. If being damaged by a monster, damage dealt will be increased by 25% over 1 turn.

- **Before** : 会心時、敵の防御の20%を無視してダメージを与える。
- **After** : 攻撃時、40%の確率で目標の防御力の50%を無視してダメージを与える。

- **Before** : 自身の回復量が30%上昇。
- **After** : 味方を回復した時、目標に１ターンの間HP回復量の25%相当のダメージを吸収するバリアを展開する。

The following adjustments occurred on February 27th, 2026 for CN servers.

The effect of **Rune: Purge** has been adjusted to: Spell: Purge amulet explosions' damage dealt to the enemy target increases by an additional 40% of the onmyoji's ATK; Fox Whispers: Purge permanently increases all allies' DEF by 10% when triggered for the first time.

- **Starlight Curse** Skill Adjustments:
  - Adjusted to: Has a 60% base chance to inflict Seal and Suppress on the designated enemy, and a 25% base chance to inflict Seal and Suppress on other enemies, lasting for 2 turns. Skill cooldown: 1 turn.
- Upgrade effects adjusted to:
  - **Lv. 2** level up effects changed to: Base chance on other enemies increased to 35%.
  - **Lv. 3** level up effects changed to: Base chance on the designated enemy increased to 80%.
  - **Lv. 4** level up effects changed to: Base chance on other enemies increased to 45%.
  - **Lv. 5** level up effects changed to: Base chance on the designated enemy increased to 100%.
- **Purification** Skill Adjustments:
  - Adjusted to: At the start of turn or when healing an ally, dispels all debuffs from self and 1 random ally. When any ally is affected by a control effect, raises self's Move Bar by 10%, once per turn.
- **Divination Sigil** Skill Adjustments:
  - Divination Sigil is adjusted to a toggled casting skill. When unlocked, the revival skill effect will be unlocked first; the damage-reflect and healing skills are adjusted to passive skills. Once unlocked, players can toggle between the damage-reflect and healing effects for casting. (The cooldowns of the 3 Divination Sigil effects are calculated independently.)
  - Divination Sigil revival skill effect adjusted to: At the start of battle, reveals all enemy shikigami's Souls. As the passive skills unlock, the effects of Divination Sigil can be toggled. Divination Sigil cannot stack.
- Active skill: Grants Divination Sigil to a designated ally for 1 turn. After being KO'd, the ally will revive upon their next action and heal themselves for 14% of their HP.
  - Divination Sigil damage-reflect skill effect adjusted to: Divination Sigil can be toggled to the damage-reflect effect: Grants Divination Sigil to a designated ally for 1 turn. When the ally is hit by a single-target attack or Indirect Damage, reflects 50% of the damage taken.
  - Divination Sigil healing skill effect adjusted to: Divination Sigil can be toggled to the healing effect: Grants Divination Sigil to a designated ally for 1 turn, healing them by 15% of their lost HP at the start of their turn.

The following adjustments occurred on August 2nd, 2025 for CN servers.

- **Channel: Storm** Skill Effect Adjustment:
  - Adjusted to: Uses spirit channeling to grant Force of Wind to one ally, increasing their ATK by 10%. In battles against Onmyoji, swaps Kagura's and the target's Move Bar positions. In battles against monsters, grants the target an extra turn without triggering cooldown.
- **Summon: Umbrella** Skill Effect Adjustment:
  - Adjusted to passive effect.
  - Original effect adjusted to: When any ally's HP falls below 60%, summons an enchanted umbrella to protect all allies, reducing damage taken by 20% for 1 turn. Triggers a 2-turn cooldown after activation.
- **Divine Fire** Skill Effect Adjustment:
  - Original effect adjusted to: Every time Kagura loses 15% of her starting HP, Hakuzosu casts Divine Fire to attack all enemies, dealing damage equal to 100% of Kagura's ATK (limited to 4 times before Kagura's turn starts). Each time Kagura uses a skill, her SPD permanently increases by 30, up to a maximum of 90.
  - **Lv. 2** level up effects changed to: Divine Fire Reduces target's DEF by 20% for 2 turns.
- **Summon: Purgatory** Skill Effect Adjustment:
  - Skill cooldown reduced to 1 turn.
  - **Lv. 2** level up effects changed to: Increases the skill damage by an additional 30%.
  - **Lv. 3** level up effects changed to: Deals double damage to shields.
  - **Lv. 5** level up effects changed to: Ignores the target's Soul effects.
- **Rune: Divine Fox** Skill Effect Adjustment:
  - Original effect adjusted to: Increases Divine Fire damage multiplier by 10%.
- Other Improvements
  - Improved the wording of some skills (no changes have been made to the effects.)
  - During auto-battle, **Channel: Storm** will now default to the target with the highest ATK.

The following adjustments occurred on May 20th, 2025 for CN servers.

- Base Stat Adjustments:
  - Base CRIT increased from 0% to 20%.
- **Double Release** Adjustments:
  - Skill cooldown reduced to 0.
- **Occult: Panther Eyes** Skill Adjustments:
  - Skill cooldown reduced to 0.
  - Upgrade effect adjustments:
  - **Lv. 5** level up effect changes to: When a shadow clone exists, additionally increases all allies' Move Bar by 15%
- **Rapid Release** Skill Adjustments:
  - Active skill adjusted to passive skill.
  - At the start of battle and after each turn, gains 3 stacks of Rapid Arrows. When an ally other than Hiromasa uses normal attacks during their turns, consumes 1 stack of Rapid Arrows to assist and increases Hiromasa's Move Bar by 10%.
  - **Rapid Release** : Max 3 stacks. Fires 3 consecutive arrows at an enemy target, each dealing damage equal to 50% of ATK, with each arrow's damage increasing by 25%.
  - **Lv. 2** level up effect changes to: Each arrow's damage increased to 55%
  - **Lv. 3** level up effect changes to: Each arrow's damage increased to 60%
  - **Lv. 4** level up effect changes to: Each arrow's damage increased to 65%
  - **Lv. 5** level up effect changes to: Each arrow's damage increased to 70%
- **Occult: Shadow Double** Skill Adjustments:
  - The shadow clone no longer not occupies summon slots.
  - Creates a shadow clone that inherits 90% of Hiromasa's stats and cannot be attacked. Every 3 attacks by Hiromasa, the shadow clone will use the same skill Hiromasa last used on the same target.
  - **Lv. 2** level up effect changes to: After casting, increases Hiromasa's Crit by 30%
  - **Lv. 3** level up effect changes to: Inherited stats increased to 100%.
  - **Lv. 4** level up effect changes to: After casting, increases Hiromasa's SPD by 30
  - **Lv. 5** level up effect changes to: After casting, increases Hiromasa's Move Bar by 70%
- **Occult: Pursuit** Skill Adjustments
  - When Hiromasa attacks with Celestial Arrow, Panther has 30% chance to perform a joint attack, dealing damage equal to 100% of Hiromasa's ATK.
- Other Improvements
  - Improved descriptions for some skills (without changing actual skill effects).
  - Improved skill descriptions for some Bondling Runes.
  - Fixed an issue where **Occult: Panther Eyes** couldn't increase Hiromasa's Crit DMG.
  - Fixed an issue with abnormal damage increase for **Rapid Release** to match description.
- Reminder:
  - Due to **Rapid Release** adjustments, please update your Onmyoji Spells accordingly.
- Due to 

- Improved the effect of **Occult: Pursuit** to:
  - When Hiromasa attacks with **Celestial Arrow** , the Panther has a 30% chance of attacking alongside, dealing damage equal to 100% of Hiromasa's ATK. Each time Hiromasa or his shadow double attacks, Hiromasa gains a**Charged Force** stack.
  - Added the **Charged Force** effect: Max 6 stacks. When Hiromasa attacks with**Celestial Arrow** on his turn, the Panther is guaranteed to attack with him, dealing damage equal to 100% of Hiromasa's ATK and removing all**Changed Force** stacks. Each**Charged Force** stack increases the damage by 50% (max 400% of Hiromasa's ATK.)
- When Hiromasa attacks with 
- Removed the skill cooldown of **Occult: Shadow Clone** .
- Improved the level-up effects of **Occult: Shadow Clone** to:
  - **Lv. 2** : Skill damage increases by 10%.
  - **Lv. 3** : Skill damage increases by 10%.
  - **Lv. 4** : Skill damage increases by 10%.
  - **Lv. 5** : Skill damage increases by 10%.
- Improved the target selecting logic for **Double Arrows** , changing its targets from all enemies to selected enemies.
- Changed the skill description of **Double Arrows** to:
  - Hiromasa draws back his bowstring and releases 2 magical arrows at 1 targeted enemy and 1 random enemy, dealing damage equal to 100% of his ATK for each arrow.
  - **Skill CD** : 1 turn.

- The skill **Occult: Panther Maul** improved to:
  - **Upper Hand** : Uses 'Occult: Panther Maul'. Panther will pounce on 1 random enemy, dealing damage equal to 100% of Hiromasa's ATK. (This doesn't count as a normal attack. The timing of this Upper Hand is the same as any other Upper Hand skills.)
- Skill effects at **Lv. 5** improved: Increases the skill damage by an additional 10% and the damage doesn't trigger the Soul effects and passive skills of all enemies.

---

**来源**: [fandom](https://onmyoji.fandom.com/wiki/Adjustments)  
**爬取时间**: 2026-09-21T09:01:50.145082+00:00
