---
title: Antonina
description: It's me, Antonina! Your reliable network security assistant! Nice to meet you! ... Oh, it's you, Professor.
tags:
  - Specialist
  - Doll
---
/// note

Dear Professor, be aware that we're not fully operational yet.
///
/// html | div.infobox

//// html | div.infobox-top

**Antonina**
////
![Antonina!](Antonina/profile)
//// html | div.infobox-subtitle

**Basic Info**
////

| Entry            | Info                      |
|------------------|---------------------------|
| **Model**        | H-01                      |
| **Manufacturer** | 42Lab                     |
| **Career**       | Network Security Engineer |
| **Birthday**     | *Unknown*                 |
| **Rarity**       | 2*                        |
| **Voice Actor**  | Juri Nagatsuma            |
///

> It's me, Antonina! Your reliable network security assistant! Nice to meet you! ... Oh, it's you, Professor.

A basic introduction to Antonina. (Not quite sure what exactly to write here yet, but probably more on the
story/personality side of the character.)

## Analysis
Let me be completely honest with you: Antonina is only worth raising if you really like her as a character, or if you enjoy torturing enemies with stunlocking. She is not exactly bad, but she is a defensive “jack of all trades, master of none” concept of a unit which doesn’t see much use in practice.

Antonina specializes at applying Stun to enemies by piling up Trojan stacks on them: they debuff the enemy Attack Speed, and upon accumulating too many of those the enemy gets Stunned for a fair amount of time. As a byproduct of her design, she also procs the powerful Flush algorithm set and Specialist functions really well, and she is solid at depleting blue bars on top. But this is where the good news end; even though Stun spam effectively reduces the amount of normal attacks and Autoskills the enemy can use on you, each part of Antonina’s kit can be covered with something else and with generally more useful Dolls:

- Attack Speed debuffing is usually a less effective method of defending against normal attacks than the Dodge / Blind strategies provided by [[Groove]] AI, [[Willow]] AI, [[Mai]], or the semi-common Swift Crackdown function set.

- Stun is undeniably a good effect, but its Autoskill-stalling effect is done way more reliably by [[Angela]] or Mai. Hell, [[Banxsy]] AI3 can stall Autoskills with Dodge + Blind support just as well while actually doing a decent amount of damage in the process.

- Antonina’s blue bar breaking is quite potent, and she can fit into Hashrate-scaling teams (most of the BB breakers scale from ATK), but some players can use either [[Puzzle]], [[Souchun]] AI, or a strong ATK-scaling breaker like [[Lind]] or [[Centaureissi]] (despite the stat scaling conflict) instead of Antonina, all of which are either cheaper or more useful at something else than that.

- Antonina is not cheap. She relies on AI3, high rarity, and [[Taisch]] to be actually good and worth her cost.

However, Arma Inscripta 3 turns her into a rather unique and interesting unit which will be the focus of this guide because the rest of her kit is that uninteresting to talk about.
### Algorithms
/// tab | AI3 ATK build

| Slot      | Set                                                                                   | Main Stat                                                            | Note                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
|-----------|---------------------------------------------------------------------------------------|----------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Offensive | :algo-deduction:&nbsp;Deduction > :algo-feedforward:&nbsp;Feedforward                 | :attr-atk:&nbsp;Attack&nbsp;%                                        | The stat bonuses you gain from the algorithms are summed up with the Doll’s base stats and treated as a single inseparable number during the mission. For that reason, giving Antonina the Deduction set (Attack Speed +30) will make the multiplicative external Attack Speed buffs you get during the mission more effective on her. However, just +30 usually isn’t enough of a difference even in the best-case scenario, so you don’t miss out on much by running Feedforward instead. |
| Stability | :algo-threshold:&nbsp;Threshold                                                       | :attr-hp:&nbsp;HP&nbsp;#                                             | Filler slot, roll for ATK and crit substats here.                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Special   | :algo-exploit:&nbsp;Exploit = :algo-flush:&nbsp;Flush = :algo-delivery:&nbsp;Delivery | :attr-crate:&nbsp;Crit&nbsp;Rate / :attr-cdmg:&nbsp;Crit&nbsp;Damage | Exploit should be used if you already have both Flush and Delivery somewhere else in your team, otherwise Antonina should be using whichever other option that your team is lacking: she procs both of those fairly well.                                                                                                                                                                                                                                                                   |
Add substat priority here.
///

/// tab | Hashrate Support build

| Slot      | Set                                                                                         | Main Stat                          | Note                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
|-----------|---------------------------------------------------------------------------------------------|------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Offensive | :algo-stack:&nbsp;Stack = :algo-progression:&nbsp;Progression > :algo-stack:&nbsp;Deduction | :attr-hash:&nbsp;Hashrate&nbsp;%   | The stat bonuses you gain from the algorithms are summed up with the Doll’s base stats and treated as a single inseparable number during the mission. For that reason, giving Antonina the Deduction set (Attack Speed +30) will make the multiplicative external Attack Speed buffs you get during the mission more effective on her. However, just +30 usually isn’t enough of a difference even in the best-case scenario, so you don’t miss out on much by running Feedforward instead. |
| Stability | :algo-threshold:&nbsp;Threshold                                                             | :attr-hp:&nbsp;HP&nbsp;#           | Filler slot, roll for ATK and crit substats here.                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Special   | :algo-exploit:&nbsp;Exploit = :algo-flush:&nbsp;Flush = :algo-delivery:&nbsp;Delivery       | :attr-haste:&nbsp;Skill&nbsp;Haste | Exploit should be used if you already have both Flush and Delivery somewhere else in your team, otherwise Antonina should be using whichever other option that your team is lacking: she procs both of those fairly well.                                                                                                                                                                                                                                                                   |
Add substat priority here.
///
   
### Teambuilding
/// tab | AI3 ATK build
Here Antonina is a DPS unit who might be lacking in damage, but her Stun spam and BB breaking will save your Dolls in some situations. Even if you go into Battlefield Overload, the ATK buff from it will benefit her anyway. Below is the list of Dolls who can support her:

| Doll                           | Priority    | Note                                                                                                                                                                                                                                                                                         |
|--------------------------------|-------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [[Mayuri]]                     | High        | The strongest buffer for ATK Dolls in the game, use her if you have her.                                                                                                                                                                                                                     |
| [[Taisch]]                     | High        | Her Ult generation and Ult CD shortening allow you to stunlock enemies via Antonina’s Ult (which would have the highest possible uptime against 2+ enemies).                                                                                                                                 |
| [[Groove]] AI / [[Willow]] AI2 | Medium-High | ATK Antonina deals damage through her normal attacks, so Attack Speed buffing is a given. We don’t really have any good options for non-environmental buffing, but those can do. (Willow AI2 would require manual teleporting but the teams with Antonina are rarely battery-hungry anyway.) |
| Alt. Ultimate Enablers         | Medium      | If you don’t have Taisch or you have to do some strict role compression, then [[Choco]] AI2, [[Daiyan]] AI3 or [[Helix]] can help you use Antonina’s oppressive Ult more often.                                                                                                              |
| Shield Stackers                | Niche       | Dolls like [[Bonee]], [[Kimie]], [[Millau]], and Turing can take advantage of Antonina stalling enemies to accumulate shields on your team much easier, which can save your backline from instant kills later or last for longer during Battlefield Overload.                                |
| [[Abigail]]                    | Low         | Antonina only really utilizes the crit buffing aspect of her kit, but it’s still a fine option if you have enough team slots or none of the better options.                                                                                                                                  |
| [[Rise]]                       | Low         | The “better than nothing” option if you don’t have anything else in this list.                                                                                                                                                                                                               |
///

/// tab | Hashrate Support build
There is no dedicated team for optimizing Hashrate Antonina because that’s not how she works: she is a defensive support who can do some damage with the Malignant Interference set, and that’s it. Simply put her into the most replaceable slot in your team whenever you actually need her support.

If you seriously want to make the most out of her Stun spam, a Guard-less team with either a Warrior or a tanky Specialist is where Hashrate Antonina should go. Taisch is especially welcome here.
///
### Tips
/// tab | AI3 ATK build
 - Pay attention to who Antonina is targeting with her normal attacks (I know it’s hard with her attack animations but the big crit numbers should be an easy indication to follow) since those are her primary means of doing damage and being useful in general.
 - Autoskill pauses her normal attack sequence and results in a damage loss for the ATK build. Don’t spam the battery on Antonina with this build and utilize smart positioning + her Ultimate for suppressing the enemies.
///

/// tab | Hashrate Support build
 - The Malignant Interference and Efficiency Accumulation function sets make the Hashrate build more useful than the AI3 ATK one each in their own ways, and they effectively make Hashrate Antonina not a dead team slot: Malignant Interference pushes her own DPS above the AI3 ATK threshold and supports the actual Hashrate DPS buddy as well, meanwhile Efficiency Accumulation has great supportive and survivability-oriented cards that are useful for the entire team, and Antonina procs them really well. Those two sets also synergize with each other really well (especially in a Specialist-heavy team) so keep an eye on them.
 - Antonina is a fairly strong blue bar breaker, and her Stun spam really fucks over the enemies with long, channeling skills who are often protected by blue bars: Entropic Fortitude (purple porcupine who rolls like a ball) and Sinspreader EX (red flower) will be left helpless, while Odile and Odette have shield phases that can be bypassed if you use a crowd control effect on them in the meantime. While the latter two are bosses, they usually come with reasonably depletable blue bars. Ptolemaea is meant to be defeated with blue bar breakers, and Antonina qualifies as one.
 - The Ultimate is pretty straightforward: it just stuns the entire field twice for a relatively long time. The only two things I can add here:
    - There is a slight delay between Ult activation and the actual Stun happening (around 0.5 sec), keep that in mind.
    - Taisch allows you to spam her suppressing Ult more and achieve the maximum stunlocking potential.
///

## Skills and Stats
### Skills and Explanation
/// tab | Passive
![Data Corrosion Icon](Antonina/passive){ .skill-icon }
#### Data Corrosion
Normal attacks inflict 1 stack of [Trojan] on target. Targets with 6 stacks of [Trojan] will be ~r{stunned} for 3 seconds, then all it [Trojan] stacks will be removed. When the target falls, its Trojan stacks will be transferred to a random enemy.

~ai{[Arma Inscripta I]} ~r{Stun} caused by [Trojan] lasts 2 seconds longer.

~ai{[Arma Inscripta III]} Normal attacks target 2 enemies, and apply 1 stack of [Trojan].

#### Notes
- Stun caused by Antonina’s Trojan in particular is represented differently - the enemy gets briefly encased in a yellow octagon, then teal cubes surround the enemy (instead of the yellow swirl above the enemy’s head unlike with other Stun sources).
- Mechanically, Antonina’s Trojan-caused Stun has the same properties as the normal Stun (prevent the enemy from doing anything and pause their Autoskill charge).
- The on-death Trojan transfer is represented by a red trail connecting the dead enemy and the inheritor.
- If the Trojan stack amount on the enemy overflows beyond 6 before the Trojan-caused Stun occurs, the excessive stacks will actually remain on the enemy. In fact, sometimes the Trojan-caused Stun does not happen immediately and you might actually see 7 or more stacks on the same enemy for a brief moment. This might be a hidden cooldown mechanic to make Antonina’s stunlocking less oppressive.
- Antonina’s Trojan stacks are different from those applied by Crash Data Matrix (the Enigma Trojan server). They will stack up on the enemy independently from each other, they both debuff the enemy’s Attack Speed (f.e. 4+2 stacks from different sources result in -60 Attack Speed in total), and they both will trigger Stun when either of those reaches 6 stacks. The Stun animation & duration will be different, however, and Stun triggered by either type of Trojan will not clear the Trojan stacks from the other source.

~ai{**AI3**}: Antonina attacks one more enemy with her normal attacks, and Trojan gets applied to that enemy as well. If there is only one enemy on the field, that enemy gets hit twice with a slight delay between each hit, and two Trojan stacks get applied to that enemy in total.

This unintentionally enables her ATK DPS build which I personally consider to be superior to her Hashrate one almost every time. If you want to be using Antonina, you would need to pay for AI3 because otherwise it doesn’t feel like she is doing enough to justify her investment and team slot cost.

The second target priority (it’s janky, be aware):

 - It’s usually the most “vulnerable” class enemy within Antonina’s attack range (Medic > Sniper > Specialist > Warrior > Guard).
 - If there is only one enemy within Antonina’s attack range, the second attack goes to that enemy.
 - The sniper tile seems to set the furthest enemy as the secondary target, while the closest enemy becomes her primary target. If another enemy becomes the closest one to Antonina, she will begin targeting that enemy with her primary attack.
 - When affected by the sniper tile, the closest enemy gets hit first while the furthest enemy gets hit the second. That is why I assume the closest enemy is her actual primary target. Moreover, the projectile for the closest enemy spawns first.
 - Focus Fire makes only one of her attacks go to the marked target. The other hit follows default logic described above: for example, the retargeting tactical command gives a brief fullscreen attack range so Antonina will target the most “vulnerable” enemy with her other shot.

Additional notes:

 - The secondary attack will not trigger Impactor’s pseudo-Backlash if the Impactor in question is Antonina’s secondary target. This is intentional with how Impactor’s skill is worded.
 - The 4-pcs effect of Multi-End Enhancement adds only one normal attack aimed at Antonina’s primary target, coming out with a slight delay after the first two.
 - The Blade of Silence card (Mental Cage set) cannot proc on the secondary target, but it seems that the second hit done on the primary target can proc it.
///
/// tab | Active
![Chain Pollution Icon](Antonina/active){ .skill-icon }
#### Chain Pollution
Deals ~b{Operand Damage equal to 120% Hashrate} to target enemy with greatest ATK, and ~b{[Derivative] Operand Damage equal to 60% Hashrate} to other enemies, applying 1 stack of [Trojan].

~ai{[Arma Inscripta II]} If any enemy triggers Data Corrosion within 3 seconds of skill activation activate [Transmittance].

#### Notes
- The visual representation of this attack is: Antonina produces an instant thick red beam that connects with the highest ATK enemy, then the smaller red beams will originate from that enemy and go towards all other enemies. Antonina has a bunch of different visual effects, and she won’t hesitate to flood your screen with them, so I find this one lowkey important to point out.
- The Transmittance damage ignores the enemy OpDEF for some reason.
- The Transmittance damage can be crit-enabled by Daiyan or Penumbra.
- Transmittance seems to prioritize the most “vulnerable” classes as its targets: in practice, it would often target the enemy Medics and Snipers regardless of who Antonina is attacking and how the enemies are placed around the field.
- Transmittance is visually represented by a group of small red dots originating from the affected enemy and flying towards their targets.
///
/// tab | Ultimate
![Global Intrusion Icon](Antonina/ultimate){ .skill-icon }
#### Global Intrusion
Antonina ~r{Stuns} all enemies for 7 seconds. After 7 seconds, she inflicts 4 stacks of [Trojan] to all enemies.
///
### Stats
+---------------------------------------------------------------------------------------------------------------------+
| Maximum Stats (without Algorithms)                                                                                  |
+--------------------------------------+---------------+-------------------------------------------------+------------+
| :attr-hp: &emsp; Max HP              | 17225 + 20422 | :attr-crate: &emsp; Crit Rate                   | 8%         |
+--------------------------------------+---------------+-------------------------------------------------+------------+
| :attr-atk: &emsp; Attack             | 549 + 571     | :attr-cdmg: &emsp; Crit Damage                  | 50%        |
+--------------------------------------+---------------+-------------------------------------------------+------------+
| :attr-hash: &emsp; Hashrate          | 562 + 639     | :attr-phpen: &emsp; Physical Penetration        | 343 + 257  |
+--------------------------------------+---------------+-------------------------------------------------+------------+
| :attr-phdef: &emsp; Physical Defense | 355 + 266     | :attr-oppen: &emsp; Operand Penetration         | 347 + 260  |
+--------------------------------------+---------------+-------------------------------------------------+------------+
| :attr-opdef: &emsp; Operand Defense  | 375 + 280     | :attr-dodge: &emsp; Dodge Rate                  | 3%         |
+--------------------------------------+---------------+-------------------------------------------------+------------+
| :attr-spd: &emsp; Attack Speed       | 100           | :attr-battle-regen: &emsp; Post-battle HP Regen | 546 + 1485 |
+--------------------------------------+---------------+-------------------------------------------------+------------+
### Gift Preferences
#### Liked
 - ~i-epic{Meal for Two}
 - ~i-rare{Working Meal}
 - ~i-uncommon{Fast Food}
#### Disliked
 - ~i-epic{Teddy Bear}
 - ~i-rare{Cartoon Doll}
 - ~i-uncommon{Plushie Charm}

*[Trojan]: Debuff: Attack Speed reduced by 10 points.
*[stunned]: Debuff: Immobilizes target, interrupts skill release and halts Auto SKill recharge. This is a control effect.
*[stuns]: Debuff: Immobilizes target, interrupts skill release and halts Auto SKill recharge. This is a control effect.
*[Stun]: Debuff: Immobilizes target, interrupts skill release and halts Auto SKill recharge. This is a control effect.
*[Stuns]: Debuff: Immobilizes target, interrupts skill release and halts Auto SKill recharge. This is a control effect.
*[Transmittance]: Deal [Derivative] Operand Damage equal to 60% to at most 2 other enemies, applying 1 stack of [Trojan].
*[Derivative]: Damage is affeted by Physical and Operand DEF but, does not trigger Backlash, Life Steal or other damage-related effects, and it does not trigger Functions or the damage condition for most skills.