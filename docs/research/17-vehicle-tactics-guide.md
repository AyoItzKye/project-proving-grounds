# Halo: The Master Chief Collection: Vehicle Tactics, AI Profiles, and Objective Logic

This single reference combines every game's vehicle roster, weak points, ramming and boarding notes, proposed AI behavior, avoid lists, theft rules, and objective game-type logic.

**How to read it**
- **Yes:** Confirmed drivable in that game from retrieved sources.
- **Verify:** Not confirmed. Test in-game before relying on it.
- **Community:** Reported by players or wiki editors. Not tested.
- **Proposed:** Design logic built for the mod, not native MCC AI.

**File set (October 28, 2026).** This is file 1 of 4: the vehicle and combat brain. File 2 is `halo_mcc_objective_logic_brains.md` (per-gametype objective brains including Firefight). File 3 is `halo_mcc_equipment_powerups_brain.md` (power-ups, equipment, armor abilities). File 4 is `halo_mcc_bot_tiers_integration_and_coach.md` (difficulty tiers for these brains, the integration contract with the on-foot combat brain, and the optional Ollama coach layer). Each of files 1 to 3 ends with a patch section describing its tier scaling and coach hooks.

**Review log (October 28, 2026)**
Corrections made in this pass:
- The Brute Chopper did not exist in Halo 2. It was removed from the Halo 2 roster. It is a stock Halo 3 multiplayer vehicle, not "Verify".
- The Brute Chopper is a one-seat vehicle with driver-fired cannons, not a driver-plus-gunner vehicle. Its ramming role was badly understated and has been rewritten.
- The Spectre is a Halo 2 vehicle only (campaign and multiplayer). It was removed from the Halo 3, ODST, and Reach rosters.
- The Hornet is a stock Halo 3 multiplayer vehicle (Avalanche) and a Halo 2 Anniversary multiplayer vehicle. It was wrongly marked "Verify" for Halo 3.
- The Brute Prowler and the M313 Elephant were missing from Halo 3 entirely. Both were added.
- The Gungoose was added to the Halo 2 Anniversary roster.
- The Phaeton is a Halo 5 vehicle and is not in Halo 4. It was removed.
- The Pelican is not drivable in Halo 3, ODST, or Reach stock multiplayer. Those entries were corrected.
- Halo 2 Anniversary CTF variants (Classic CTF, Warlock Classic CTF, Neutral Flag CTF, Gungoose CTF) were listed under Halo 3 by mistake and were moved.
- Halo 3's collision-damage system (mass and speed based ramming that can destroy vehicles) was added to the Halo 3 facts.
- A note was added that in Halo CE only the Ghost and Banshee can be destroyed at all; the Warthog and Scorpion are indestructible.

**Sections**
- [Quick Reference: Mounting, Killing, and Taking Vehicles](#quick-reference-mounting-killing-and-taking-vehicles)
- [Bot Implementation Layer](#bot-implementation-layer)
- [Halo: Combat Evolved (MCC)](#halo-combat-evolved-mcc)
- [Halo 2 (MCC, including Anniversary Multiplayer)](#halo-2-mcc-including-anniversary-multiplayer)
- [Halo 3 (MCC)](#halo-3-mcc)
- [Halo 3: ODST (MCC)](#halo-3-odst-mcc)
- [Halo: Reach (MCC)](#halo-reach-mcc)
- [Halo 4 (MCC)](#halo-4-mcc)

---

## Quick Reference: Mounting, Killing, and Taking Vehicles

Use this when a vehicle profile below does not spell out the full procedure. Each profile also carries its own game-specific notes.

### How boarding works by game
- **Halo CE:** No boarding. Kill the occupant or flip the vehicle. Only the Ghost and Banshee can be destroyed at all (Halopedia).
- **Halo 2:** Hold the action button near an enemy vehicle. On Scorpions and Wraiths you jump onto the hull; you must melee the hatch off before you can plant a grenade, and the boarded player can jump out (Halopedia). On Ghosts, Banshees, Spectres, and Warthogs the boarder throws the driver out.
- **Halo 3 and ODST:** Boarding is faster. The grenade is shoved straight through the hatch and the occupant is trapped inside (Halopedia). The ejection melee heavily damages the thrown driver and kills them if their shields are down. ODST's boarding range is a little larger. Mongoose cannot be boarded.
- **Halo: Reach:** The boarder takes the seat they board on a Warthog. Mongoose boarding kicks driver and passenger off together. Banshee boarding kicks the pilot off. Scorpion and Wraith are still jump-on-top.
- **Halo 4:** Same as Reach for light vehicles. Wraith must be EMP'd first (usually four or five Plasma Pistol overcharges) because melee cannot kill the driver before the Wraith dies (Halopedia). Mantis: EMP it so it crouches, or drop onto the cockpit from above.

### Tank procedure (Scorpion and Wraith), Halo 2 through Reach
1. **Kill the gunner first.** The tank's gunner can shoot anyone climbing on (Halopedia). A Scorpion with no gunner is blind to boarders.
2. **Get on top.** Approach from the rear or side, outside the main cannon's arc. EMP the tank first if you can (Halo 3 onward) so it cannot drive off.
3. **Choose melee or grenade.**
   - **Melee:** Punch the hatch repeatedly. This exposes the driver and then kills them. The tank survives and is yours to drive (Halopedia). Reach walkthrough tip: standing on a Wraith and meleeing without the board command damages the vehicle less than boarding.
   - **Grenade:** Plant a grenade. This kills every occupant and destroys the tank (Halopedia). In Halo 2 you plant it only after the hatch is gone, and you can be hurt by it; in Halo 3 onward it goes through the hatch instantly.
4. **Counter-boarding (Reach, Halopedia):** A driver who sees a boarder coming gets out before they arrive. If the driver is willing to lose the tank, they board it back as soon as the attacker climbs in and melee or grenade it.
5. **Commandeer instead (Reach and Halo 4):** Kill the gunner, take the gunner's turret seat yourself, and the AI or player driver exits. Kill them on the way out (Halopedia).

### Where tanks are weak (community testing; verify per game)
- **Scorpion rear engine vent (Halo 3 era testing):** damage tripled. One Spartan Laser, one rocket, or a full sniper magazine to the vent kills it. Treads take double damage once their armor plates are shot off. The cannon barrel takes less than half damage, so never shoot the gun.
- **Scorpion in Reach:** much less armor than Halo 3. Two sniper shots or 21 DMR shots remove the driver's canopy; the exposed driver can then be headshot. The rear is the weak spot, which is why drivers reverse in.
- **Scorpion in Halo 2:** the turret is almost invulnerable; the body and the four motor housings are the weak points. A rocket into a still-attached hatch destroys it.
- **Wraith:** front and rear fins take about 20 percent more damage than the nose; the rear is as strong as the nose. Its mortar is poor against airborne targets, so jetpacks (Reach) and Banshees are the safest attackers. The Halo 2 Wraith also has two small hood plasma cannons that guard it from infantry at close range.

### EMP (Halo 3 onward)
- Charged Plasma Pistol shot, a manually detonated Grenade Launcher round (Reach), a Power Drain (Halo 3), or a Splinter Grenade (Halo 5 only, not in MCC) stops a vehicle's engine and leaves it open to boarding. Aircraft drop out of the sky. The Mantis and Mongoose crouch.

### Light vehicles and aircraft
- **Warthog:** a frag grenade flips it and throws the occupants out; a stuck plasma grenade does heavy damage or destroys it; two direct grenade hits or one rocket destroys it (Halo 3 onward). Kill the gunner before boarding the driver. Halo 3 trick: a boarded driver turns 90 degrees right to face the boarder and melee; a boarder turns 90 degrees left to melee the stunned driver.
- **Ghost:** dodge it so it boosts into a wall, then board it from behind while it backs out. EMP it to stop the boost.
- **Banshee:** EMP drops it. Halo 3: shoot the pilot's legs to kill the pilot without hurting the craft. ODST: a sniper round through the gap between hull and canopy kills the pilot. Reach: a rocket fits through the same gap. Rockets lock on in Halo 2 and Reach but not Halo 3.
- **Hornet and Falcon:** both are among the vehicles most often boarded (Halopedia). EMP them when they hover to let passengers shoot; the drop makes boarding easy.
- **Mongoose:** Halo 3 and ODST cannot be boarded; melee the driver off as they pass, or sit in the passenger seat and melee or headshot the driver. Reach and later: board it and both riders are kicked off.
- **Revenant and Spectre:** harder to board because they move in every direction (Halopedia). Explosives and rockets are the reliable answer.
- **Elephant:** cannot be destroyed. Walk up the rear ramp and kill the driver, ideally from behind or from a Banshee so they do not see you in third person.

---

## Bot Implementation Layer

This section is written for the AI that will code the bots. It gives the operating model of each vehicle, the hard numbers that exist, where to pull the numbers that do not, and a decision architecture with explicit thresholds. Everything marked **Proposed** is a default to tune in testing; everything marked **Tag** comes from the game's own tag files.

### 1. Where the numbers live, and what is already known

**The only game with published tag-extracted vehicle stats is Halo: Reach** (Steam guide "Halo Reach Statistics" by Kawasko, August 2025, read from the MCC Reach tags). Those numbers are reproduced below. **For Halo CE, 2, 3, ODST, and 4 the bot developer must pull the equivalents from the MCC mod tools**, because no published source lists them. The procedure is the same in every game:

1. Open the vehicle's `.vehicle` tag (for example `objects\vehicles\warthog\warthog.vehicle` in Halo 3 and ODST; `vehicles\warthog\warthog.vehicle` in Halo CE; Reach and Halo 4 follow the Halo 3 layout).
2. Follow its `model` reference. Microsoft's Halo 3 tagging documentation says the model tag's **new damage info** block holds **maximum vitality** (total health), **maximum shield vitality**, the **damage sections** (named regions such as hatch, treads, wheels, each with a **vitality percentage** of the whole), and **instant responses** with a **damage threshold** (1 = full health, 0 = destroyed) that fire effects such as the hatch popping or the vehicle entering its destroyed state. The **collision damage reporting type** is how a Warthog splatter is credited to the driver.
3. Follow each seat's `weapon` reference for `fire recovery time`, rate of fire, heat, and the `damage_effect` reference for per-hit damage and the **damage type**.
4. Open `globals\globals` (and the per-game `damage_globals` or material table) to read the **damage type versus material type** multipliers. Reach's matrix is given below; expect the other games to differ.
5. Read movement from the `.vehicle` tag's physics block: maximum forward and reverse speed, acceleration, turning, boost (duration, cooldown, speed multiplier), and anti-gravity hover height. Halo 3 Rebalanced's change list confirms these exact fields exist: "max speed, acceleration, ground friction, gravity scale" for Warthog and Mongoose; "sliding speeds" and "backhatch vitality percent" for the Wraith; "fire recovery time" and "projectile speed" for the Banshee bomb.

**Known structural differences between games that change the bot math**
- **Halo CE:** Warthog and Scorpion have no destructible vitality at all; Ghost and Banshee do (campaign). No boarding, no EMP.
- **Halo 2 and Halo 3:** community analysis of the era (Rampancy, "Building the Ultimate Halo Game") describes vehicle damage as partly passed through to the occupants, so a Warthog that is being shot bleeds its driver's shields before the hull dies. Treat occupant health and hull vitality as two coupled pools, not one.
- **Reach onward:** explicit hull vitality with separate damage sections (back hatch, treads, canopy, gas tank). Reach vehicles also explode after enough critical parts are destroyed even if the occupant is alive (Halopedia Banshee changes list).
- **Halo 4:** Halopedia and fan documentation note the Wraith's boost lasts longer and responds faster than in Halo 3, the mortar arcs less with less splash, and the Scorpion's speed was reduced. Fandom lists Halo 4 vehicle skins with +20 to +75 percent vehicle health for some REQ-style variants; those are Halo 5, ignore them.

### 2. Reach hard numbers (Tag)

These are campaign tag values read from MCC. Multiplayer may apply different global modifiers (Spartan shields in particular), so treat the ratios as reliable and the absolute Spartan numbers as approximate.

**Vehicle durability**

| Vehicle | Vitality | Hull material | Weak parts (their material) | Separate weapon health |
|---|---|---|---|---|
| Mongoose | 400 | hard_metal_thin | wheels: tough_inorganic | none |
| Ghost | 355 | hard_metal_thin | gas tank: brittle_mech | none |
| Banshee | 330 | hard_metal_thick | none listed | none |
| Revenant | 400 | hard_metal_thick | none listed | none |
| Warthog (all turret variants) | 500 | hard_metal_thick | front glass: brittle_glass; wheels: tough_inorganic | none |
| Falcon | 500 | hard_metal_thick | canopy: brittle_glass | none |
| Scorpion | 600 | hard_metal_solid | treads: hard_metal_thick; back hatch: brittle_mech | cannon 300 |
| Wraith | 600 | hard_metal_solid | back hatch: brittle_mech | mortar 300 |
| Phantom (not drivable) | 2000 | hard_metal_solid | engines: hard_metal_thin | chin gun 200 |

Point values (Firefight/campaign score, usable as a threat-weight seed): Mongoose 50, Ghost 150, Banshee 150, Revenant 250, Warthog 250, Scorpion 350, Wraith 350, Falcon 350, Phantom 1000.

**Vehicle weapons**

| Weapon | Fire recovery | Rate of fire | Damage per hit | Splash | Damage type | Notes |
|---|---|---|---|---|---|---|
| Warthog chaingun | 0.333 s | 5 rps spinning up to 15 rps | 7 to 8 | none | bullet_turret | spin-up means first second does one third damage |
| Gauss cannon | 0.8 s | single | 200 | 45 in 0.25 to 1.0 wu | collision + explosion_small | one-shots infantry |
| Rocket hog | 2.0 s per salvo | 3.5 rps within salvo | 45 x 6 rockets | 45 each, 0.9 to 2.0 wu | collision + explosion_large | tracks air in Reach |
| Scorpion coax | 0.125 s | 8 to 15 rps | 7 | none | bullet_turret | driver-fired in Reach |
| Scorpion cannon | 3.0 s | single | 334 | 334 in 0.75 to 1.75 wu | collision + explosion_large | cannon has its own 300 health |
| Ghost cannons | 0.133 s | 7.5 rps | 8 | none | plasma_turret | |
| Banshee cannons | 0.1 s | 10 rps | 12 | none | plasma_turret | |
| Banshee bomb | 3.0 s | single | 167 | 167 in 1.25 to 1.75 wu | explosion_large | homes on vehicles in Reach, slow |
| Wraith anti-infantry gun | 0.1 s | 13 rps | 8 | none | plasma_turret | gunner seat |
| Wraith mortar | 3.0 s | single | 223 | 445 in 0.75 to 2.25 wu | collision + explosion_large | mortar has its own 300 health |
| Revenant mortar | 1.5 s | single | 60 | 60 in 0.5 to 1.75 wu | collision + explosion_small | |
| Falcon chin gun | 0.25 s | 10 rps, 5 rounds per trigger | 20 | none | bullet_turret | campaign and Forge only; MP Falcon has no chin gun |

**Infantry weapons that matter to vehicles (Reach, Tag):** Rocket Launcher 200 direct + 240 splash (collision + explosion_large), 0.8 s, 2 rounds. Plasma Launcher 175 per bolt, 300 attached (explosion_small), up to four bolts per charge, locks on. Fuel Rod 100 + 60 splash. Sniper 80 (sniper type, which keeps full value against thick armor and 75 percent against solid). DMR 17.5 (bullet_fast). Plasma grenade 250, 350 attached (explosion_small). Frag 160 (explosion_small). Plasma Pistol overcharge 200 of damage type emp, which does essentially zero hull damage but stuns the engine; Grenade Launcher manual detonation also carries an emp component of 100 with a 2.5 wu outer radius.

**Damage type versus vehicle material (Reach, Tag)**

| Damage type | hard_metal_thin (Ghost, Mongoose) | hard_metal_thick (Warthog, Banshee, Falcon, Revenant, Scorpion treads) | hard_metal_solid (Scorpion, Wraith hull) | brittle_mech (gas tank, back hatches) | brittle_glass (Warthog windshield, Falcon canopy) | energy_shield_thin (Spartan shield) |
|---|---|---|---|---|---|---|
| bullet_turret (chainguns, coax) | 1.0 | 0.75 | 0.5 | 1.0 | 0.5 | 1.0 |
| bullet_fast (DMR, BR) | 1.0 | 0.5 | 0.25 | 1.0 | 0.5 | 1.0 |
| bullet_slow (AR, Magnum) | 1.0 | 0.25 | 0.125 | 1.5 | 1.0 | 1.0 |
| sniper | 1.0 | 1.0 | 0.75 | 1.0 | 0.5 | 1.0 |
| plasma_turret (Ghost, Banshee, Wraith AI gun) | 1.0 | 0.5 | 0.25 | 0.5 | 0.5 | 1.0 |
| plasma_slow (Plasma Pistol, Rifle, Spiker) | 0.4 | 0.125 | 0.0625 | 1.0 | 0.25 | 1.6 |
| collision (direct hits of Gauss, rockets, cannons, mortars; splatters) | 1.0 | 0.75 | 0.5 | 2.0 | 2.0 | 1.0 |
| explosion_small (Gauss splash, Revenant, Plasma Launcher, grenades) | 0.75 | 0.5 | 0.45 | 2.0 | 2.0 | 0.5 |
| explosion_large (rockets, cannon, mortar, Banshee bomb, fuel rod) | 1.0 | 0.75 | 0.5 | 3.0 | 3.0 | 0.75 |
| laser (Spartan Laser) | 1.0 | 1.0 | 0.5 | 2.0 | 2.0 | 0.25 |
| melee | 1.0 | 0.25 | 0.125 | 2.0 | 2.0 | 1.0 |
| emp | 0 | 0.001 | 0.001 | 0 | 0 | 1.0 |

What this means for a bot:
- **Small arms are nearly useless against tanks** (DMR does 4.4 per round to a Scorpion hull; 137 rounds to kill). Bots on foot should never try to shoot a Scorpion or Wraith hull down; they should EMP, board, stick, or hit the brittle_mech back hatch, where a rocket's direct component does 400 and its splash 720.
- **Back hatches and gas tanks are the weak parts by material, not by lore.** brittle_mech takes 2x collision, 3x explosion_large, 2x melee. That is why "melee the hatch" works and why a rocket into the Wraith's rear hatch is the kill shot. A bot aiming at a tank should steer its shot toward the rear hatch whenever the angle allows.
- **plasma_turret is poor against thick and solid armor.** A Ghost's cannons do 2 per bolt to a Scorpion (178 bolts, 24 seconds of continuous fire). A Ghost bot should not duel tanks; its guns are for infantry, Mongooses, and other Ghosts.
- **The Gauss cannon is the universal anti-vehicle gun.** 150 to a Warthog or Banshee (4 shots, 3.2 s), 190 to a Ghost (2 shots), 120 to a Scorpion hull (5 shots, 4 s), and it one-shots infantry. Gauss bots should prioritise vehicles over infantry because anything else wastes its 0.8 s cycle.
- **The Scorpion cannon and Wraith mortar one-shot every light vehicle on a direct hit** and kill a Warthog, Banshee, Falcon, or Revenant in two.

**Computed time-to-kill matrix (Reach, derived from Tag values).** Each cell is: effective damage per hit (direct plus splash where both apply) / hits to destroy / approximate time at the listed cycle. Assumes every hit lands and lands on the hull material, not a weak part. Use it to seed engagement decisions and to decide when a bot should disengage.

| Attack | Mongoose | Ghost | Banshee | Revenant | Warthog | Falcon | Scorpion | Wraith |
|---|---|---|---|---|---|---|---|---|
| Warthog chaingun (per round, 15/s spun up) | 8 / 54 hits / ~3.6s | 8 / 48 hits / ~3.2s | 6 / 59 hits / ~3.9s | 6 / 72 hits / ~4.8s | 6 / 89 hits / ~5.9s | 6 / 89 hits / ~5.9s | 4 / 160 hits / ~10.7s | 4 / 160 hits / ~10.7s |
| Scorpion coax (per round, up to 15/s) | 7 / 58 hits / ~3.9s | 7 / 51 hits / ~3.4s | 5 / 63 hits / ~4.2s | 5 / 77 hits / ~5.1s | 5 / 96 hits / ~6.4s | 5 / 96 hits / ~6.4s | 4 / 172 hits / ~11.5s | 4 / 172 hits / ~11.5s |
| Ghost cannon (per bolt, 7.5/s) | 8 / 50 hits / ~6.7s | 8 / 45 hits / ~6.0s | 4 / 83 hits / ~11.1s | 4 / 100 hits / ~13.3s | 4 / 125 hits / ~16.7s | 4 / 125 hits / ~16.7s | 2 / 300 hits / ~40.0s | 2 / 300 hits / ~40.0s |
| Banshee cannon (per bolt, 10/s) | 12 / 34 hits / ~3.4s | 12 / 30 hits / ~3.0s | 6 / 55 hits / ~5.5s | 6 / 67 hits / ~6.7s | 6 / 84 hits / ~8.4s | 6 / 84 hits / ~8.4s | 3 / 200 hits / ~20.0s | 3 / 200 hits / ~20.0s |
| Wraith anti-infantry gun (per bolt, 13/s) | 8 / 50 hits / ~3.8s | 8 / 45 hits / ~3.5s | 4 / 83 hits / ~6.4s | 4 / 100 hits / ~7.7s | 4 / 125 hits / ~9.6s | 4 / 125 hits / ~9.6s | 2 / 300 hits / ~23.1s | 2 / 300 hits / ~23.1s |
| Gauss cannon (per shot, 0.8 s) | 234 / 2 hits / ~1.6s | 234 / 2 hits / ~1.6s | 172 / 2 hits / ~1.6s | 172 / 3 hits / ~2.4s | 172 / 3 hits / ~2.4s | 172 / 3 hits / ~2.4s | 120 / 5 hits / ~4.0s | 120 / 5 hits / ~4.0s |
| Rocket hog (per 6-rocket salvo, 2 s) | 540 / 1 hits / ~2.0s | 540 / 1 hits / ~2.0s | 405 / 1 hits / ~2.0s | 405 / 1 hits / ~2.0s | 405 / 2 hits / ~4.0s | 405 / 2 hits / ~4.0s | 270 / 3 hits / ~6.0s | 270 / 3 hits / ~6.0s |
| Revenant mortar (per shot, 1.5 s) | 105 / 4 hits / ~6.0s | 105 / 4 hits / ~6.0s | 75 / 5 hits / ~7.5s | 75 / 6 hits / ~9.0s | 75 / 7 hits / ~10.5s | 75 / 7 hits / ~10.5s | 57 / 11 hits / ~16.5s | 57 / 11 hits / ~16.5s |
| Banshee bomb (per shot, 3 s) | 334 / 2 hits / ~6.0s | 334 / 2 hits / ~6.0s | 250 / 2 hits / ~6.0s | 250 / 2 hits / ~6.0s | 250 / 2 hits / ~6.0s | 250 / 2 hits / ~6.0s | 167 / 4 hits / ~12.0s | 167 / 4 hits / ~12.0s |
| Scorpion cannon (per shot, 3 s) | 668 / 1 hits / ~3.0s | 668 / 1 hits / ~3.0s | 501 / 1 hits / ~3.0s | 501 / 1 hits / ~3.0s | 501 / 1 hits / ~3.0s | 501 / 1 hits / ~3.0s | 334 / 2 hits / ~6.0s | 334 / 2 hits / ~6.0s |
| Wraith mortar (per shot, 3 s) | 668 / 1 hits / ~3.0s | 668 / 1 hits / ~3.0s | 501 / 1 hits / ~3.0s | 501 / 1 hits / ~3.0s | 501 / 1 hits / ~3.0s | 501 / 1 hits / ~3.0s | 334 / 2 hits / ~6.0s | 334 / 2 hits / ~6.0s |
| Rocket Launcher (per rocket, 0.8 s) | 440 / 1 hits / ~0.8s | 440 / 1 hits / ~0.8s | 330 / 1 hits / ~0.8s | 330 / 2 hits / ~1.6s | 330 / 2 hits / ~1.6s | 330 / 2 hits / ~1.6s | 220 / 3 hits / ~2.4s | 220 / 3 hits / ~2.4s |
| Fuel Rod Gun (per shot, 0.4 s) | 160 / 3 hits / ~1.2s | 160 / 3 hits / ~1.2s | 120 / 3 hits / ~1.2s | 120 / 4 hits / ~1.6s | 120 / 5 hits / ~2.0s | 120 / 5 hits / ~2.0s | 80 / 8 hits / ~3.2s | 80 / 8 hits / ~3.2s |
| Plasma Launcher (per bolt, attached) | 225 / 2 hits / ~0.4s | 225 / 2 hits / ~0.4s | 150 / 3 hits / ~0.6s | 150 / 3 hits / ~0.6s | 150 / 4 hits / ~0.8s | 150 / 4 hits / ~0.8s | 135 / 5 hits / ~1.0s | 135 / 5 hits / ~1.0s |
| Plasma grenade (attached) | 262 / 2 hits / ~2.3s | 262 / 2 hits / ~2.3s | 175 / 2 hits / ~2.3s | 175 / 3 hits / ~3.4s | 175 / 3 hits / ~3.4s | 175 / 3 hits / ~3.4s | 158 / 4 hits / ~4.6s | 158 / 4 hits / ~4.6s |
| Frag grenade | 120 / 4 hits / ~4.6s | 120 / 3 hits / ~3.4s | 80 / 5 hits / ~5.8s | 80 / 5 hits / ~5.8s | 80 / 7 hits / ~8.0s | 80 / 7 hits / ~8.0s | 72 / 9 hits / ~10.3s | 72 / 9 hits / ~10.3s |
| Sniper Rifle (per round, 0.75 s) | 80 / 5 hits / ~3.8s | 80 / 5 hits / ~3.8s | 80 / 5 hits / ~3.8s | 80 / 5 hits / ~3.8s | 80 / 7 hits / ~5.2s | 80 / 7 hits / ~5.2s | 60 / 10 hits / ~7.5s | 60 / 10 hits / ~7.5s |
| DMR (per round, 0.33 s) | 18 / 23 hits / ~7.6s | 18 / 21 hits / ~6.9s | 9 / 38 hits / ~12.5s | 9 / 46 hits / ~15.2s | 9 / 58 hits / ~19.1s | 9 / 58 hits / ~19.1s | 4 / 138 hits / ~45.5s | 4 / 138 hits / ~45.5s |
| Spartan Laser | the guide's tag entry is incomplete (10 per tick at 20 ticks/s over a 2.5 s charge); in play it kills every light vehicle in one beam and a tank in one to two | | | | | | | |
| Plasma Pistol overcharge (EMP) | engine stun, no meaningful hull damage on any vehicle | | | | | | | |
| Grenade Launcher EMP | engine stun, no meaningful hull damage on any vehicle | | | | | | | |

**Vehicle weapons versus a Spartan (Reach campaign tags: 100 shield energy_shield_thin, 60 body hard_metal_thin; MP shields may differ)**

| Vehicle weapon | Dmg to shield per hit | Dmg to body per hit | Hits to kill (100 shield + 60 body) | Time at listed RoF |
|---|---|---|---|---|
| Warthog chaingun (per round, 15/s spun up) | 8 | 8 | 22 | ~1.5s |
| Scorpion coax (per round, up to 15/s) | 7 | 7 | 23 | ~1.5s |
| Ghost cannon (per bolt, 7.5/s) | 8 | 8 | 20 | ~2.7s |
| Banshee cannon (per bolt, 10/s) | 12 | 12 | 14 | ~1.4s |
| Wraith anti-infantry gun (per bolt, 13/s) | 8 | 8 | 20 | ~1.5s |
| Gauss cannon (per shot, 0.8 s) | 222 | 234 | 1 | ~0.8s |
| Rocket hog (per 6-rocket salvo, 2 s) | 472 | 540 | 1 | ~2.0s |
| Revenant mortar (per shot, 1.5 s) | 90 | 105 | 2 | ~3.0s |
| Banshee bomb (per shot, 3 s) | 250 | 334 | 1 | ~3.0s |
| Scorpion cannon (per shot, 3 s) | 584 | 668 | 1 | ~3.0s |
| Wraith mortar (per shot, 3 s) | 557 | 668 | 1 | ~3.0s |

Reading: a Banshee's cannons kill an exposed Spartan in about one second of sustained hits; a Ghost needs almost three seconds, which is why Ghost bots should splatter rather than shoot anything within ram range; every cannon, mortar, Gauss round, and Banshee bomb direct hit is a one-shot kill on infantry, and the Wraith mortar's splash alone (334 to shields) kills everyone in its inner radius.

### 3. Per-vehicle operating model

Each entry lists control inputs, the movement envelope, weapon mechanics, crew, damage states, and the sensory cues a human uses. Numbers marked (Tag) are Reach values; other games need the extraction in section 1. Movement figures are qualitative until extracted.

#### Warthog family (chaingun, Gauss, rocket, transport)
- **Inputs:** throttle forward/reverse, steer, e-brake (Halo 3 onward), horn. The driver has no weapon. Steering is through the front wheels, so it understeers at speed and oversteers under e-brake.
- **Movement:** fast, high centre of gravity; rolls on hard turns at speed and on side slopes (Halopedia). Four-wheel drive climbs most slopes. Reverse is roughly half forward speed. No boost.
- **Weapon (gunner):** turret rotates a full 360 degrees but the gunner's own cab and the bed's roll bar occlude low shots forward; the best firing arcs are rear and both sides. Chaingun spins up from 5 to 15 rps over its first second (Tag), so a gunner bot should pre-spin (hold fire into empty space) when a target is about to appear. Gauss is a single 0.8 s shot with a flat, fast projectile, led only against fast crossing targets. Rocket hog fires six rockets per trigger with a 2 s cycle and tracks air (Reach).
- **Crew:** driver, gunner, one passenger (bed). Transport hog: driver plus bed riders, no gun.
- **Damage states:** 500 vitality (Tag, Reach), thick hull, glass windshield and tough wheels as separate parts. Visual cues: smoke from the engine at roughly half health, flames below a quarter; an upside-down Warthog is a dead Warthog until flipped.
- **Human cues to imitate:** humans keep the hog moving in a wide arc around the fight so the gunner has a side arc on the target; they brake hard and reverse out when a Scorpion barrel swings onto them; they drive backwards into a base so the gunner faces out.

#### Mongoose and Gungoose
- **Inputs:** throttle, steer, e-brake, horn. Gungoose adds driver-fired LMGs (H2A only).
- **Movement:** fastest ground acceleration, lightest chassis; wobbles and tips on uneven ground (Prima). Lands hard from jumps.
- **Weapon:** none except the passenger's own gun (and Gungoose LMGs). A ram only kills infantry on a direct, full-speed hit (Prima).
- **Crew:** driver, passenger.
- **Damage:** 400 vitality (Tag), thin hull, so bullet_turret, bullet_fast, and plasma_turret all do full damage; it dies to a chaingun in about 3.6 s.
- **Human cues:** humans never stop; they drop a passenger at the objective at speed and loop back.

#### Scorpion
- **Inputs:** throttle, pivot-steer (it can rotate in place), turret rotation independent of hull, cannon fire, coax fire (driver in CE/H2/Reach/H4; separate gunner seat in Halo 3 and ODST).
- **Movement:** slowest ground vehicle, about 3 s to full speed (StrategyWiki Halo 3), reduced further in Halo 4. Turret traverse is slower than the Warthog's. The cannon cannot elevate high enough to hit a Banshee directly overhead: the overhead cone is a blind spot (Halopedia Halo 5 note, same geometry in earlier games).
- **Weapon:** 334 direct + 334 splash (Tag), 3 s cycle, CE reportedly 4 s in MCC MP. Projectile is fast but not hitscan: lead crossing targets by roughly a vehicle length per 30 m. Shell drop is negligible inside normal map ranges.
- **Crew:** driver, gunner, riders on the tread pods (CE and some later titles).
- **Damage:** 600 solid hull, 300-health cannon that can be knocked out separately, treads thick, back hatch brittle_mech (Tag). Community Halo 3 testing: rear vent triples damage, tread armour once stripped doubles damage, cannon barrel halves damage.
- **Human cues:** humans park with the rear against a wall, keep the turret moving between the two most likely approaches, fire the coax at anything inside 15 m, and bail out the moment a boarder jumps on (Reach counter-board).

#### Wraith
- **Inputs:** throttle, steer (hover, slides on slopes), boost (short burst in Halo 3, longer and more responsive in Halo 4), mortar fire, gunner turret (Halo 3 onward; Halo 2 has two automatic hood guns instead).
- **Movement:** slides; momentum carries it past the steering input. Boost is for repositioning, not chasing.
- **Weapon:** mortar 223 direct + 445 splash (Tag), 3 s cycle, high arc with 2 to 3 s flight time at range; the bot must fire at where the target will be in that flight time, so aim at chokepoints and parked vehicles, not weaving ones. Halo 4 arcs less and splashes less. Mortar is poor against aircraft.
- **Crew:** driver, gunner.
- **Damage:** 600 solid hull, mortar has its own 300 health, back hatch brittle_mech (Tag). Front and rear fins take about 20 percent more than the nose (community). ODST: explodes on driver death or exit.
- **Human cues:** humans sit at maximum range behind a crest, lob at the objective, and reverse-boost away when a Warthog or Chopper starts a run.

#### Ghost
- **Inputs:** throttle, strafe (it can move sideways and backwards without turning), boost (unlimited in most games; Reach imposes limits on the Banshee, not the Ghost), twin cannons.
- **Movement:** hover; fastest sustained ground speed under boost; cannot fire while boosting in most games (Temple Ghost in Halo 5 is the exception). Hitting a wall head-on at speed can kill the driver (Halopedia, Halo 3).
- **Weapon:** 8 per bolt at 7.5 rps (Tag), plasma_turret, slow bolts that must be led. Weak against thick and solid armour.
- **Crew:** driver only.
- **Damage:** 355 thin hull, gas tank brittle_mech (Tag, Reach; Halo 2 gas tanks were a shootable weak point, removed as a weak point in Halo 3 per community).
- **Human cues:** humans strafe-fire at infantry from medium range, boost only for the last one to two Scorpion lengths of a splatter, and never boost into a wall-lined lane.

#### Banshee
- **Inputs:** pitch, yaw, roll, throttle, boost (limited in Reach), trick rolls and flips (Halo 2 and 3 freely; Reach and Halo 4 restricted), weapon switch (Reach: separate reticles for cannons and bomb), hover (ODST onward when not moving).
- **Movement:** cannot pitch below 45 degrees in Halo 3 (Halopedia), can face nearly straight down in ODST onward. Boost velocity higher in Halo 3 than Halo 2. Tricks give brief invulnerability windows against rockets and are how humans dodge lock-ons.
- **Weapon:** cannons 12 per bolt at 10 rps (Tag, Reach); bomb 167 + 167 splash every 3 s, homes on vehicles in Reach but is slower than the Banshee itself (Halopedia), does not track in Halo 4, not available in Halo 2 MP or H2A MP.
- **Crew:** pilot only.
- **Damage:** 330 thick hull (Tag), the lowest vitality of any vehicle; dies to a Gauss round in 3 hits, a rocket in 2, a Scorpion shell in 1. Wings and anti-grav pods can be shot off in some titles without stopping flight.
- **Human cues:** humans never fly level and straight for more than a second near rockets, they attack from the enemy's rear quarter, they bomb vehicles from above where the tank cannot elevate, and they land only when stealing or when the hull is smoking.

#### Brute Chopper (Halo 3, ODST)
- **Inputs:** throttle, steer (the whole front assembly swings), boost, driver-fired forward cannons.
- **Movement:** average speed, poor handling (Neoseeker). Turning radius is the worst of the light vehicles; a boost is roughly a one-second burst (verify in tags). Cannot flip. Boost-jumps clear gaps.
- **Weapon:** forward cannons (community: "similar to a plasma cannon", lore 35 mm). Ram: boosted head-on contact destroys any vehicle except Wraith and Scorpion (Giant Bomb; Halopedia confirms the Warthog kill).
- **Crew:** driver only.
- **Damage:** tougher than a Ghost, well below a tank (Fandom). Extract vitality from tags.
- **Human cues:** cavalry charge in a straight line, boost late, peel off after contact, never stop.

#### Hornet (Halo 3, ODST Firefight, H2A) and Falcon (Reach)
- **Inputs:** collective (altitude), pitch, yaw, throttle, pilot guns (Hornet: machine gun and two missiles; Reach MP Falcon: none, side gunners only; campaign and Forge Falcon: chin gun 20 per round, 5-round bursts, 10 rps, Tag).
- **Movement:** VTOL hover; slower than a Banshee, cannot roll. Hovering to let passengers shoot is the standard human use and the standard way to die.
- **Crew:** Hornet pilot plus two side riders; Falcon pilot plus two side gunners (standard) or more seats (nose-gun and transport variants).
- **Damage:** Falcon 500 thick with a glass canopy (Tag). Hornet: extract.
- **Human cues:** humans hover behind cover with only the gunners' side exposed, drop riders on rooftops, and dive away the instant a Banshee appears.

#### Revenant (Reach) and Spectre (Halo 2)
- **Inputs:** throttle, steer, strafe (hover), boost (Revenant), driver-fired mortar (Revenant) or gunner turret (Spectre).
- **Movement:** hover, slides, slow turn. Revenant mortar 60 + 60 splash on a 1.5 s cycle (Tag), a short arc, fine for infantry groups and Mongooses, poor against anything thick.
- **Crew:** Revenant driver plus passenger; Spectre driver, gunner, two riders.
- **Damage:** Revenant 400 thick (Tag). Spectre: extract.

#### Mantis (Halo 4)
- **Inputs:** walk, turn, arm gun, missile pod, stomp (melee).
- **Movement:** slowest unit on foot speed terms, can step over low cover, crouches when EMP'd.
- **Weapon:** machine-gun arm and missile pod (verify stats), stomp is a short-range area kill.
- **Damage:** extract. Has shields in Halo 4 (community); verify in tags.

#### Elephant (Halo 3 Sandtrap)
- Invincible, open deck, rear-cabin driver, multiple turret seats, carries a Mongoose. Operate it as a slow moving base; the bot driver's only job is positioning.

### 4. Bot decision architecture

**4.1 Vehicle agent state machine (Proposed)**

```
IDLE        -> PATROL        when assigned a route or objective
PATROL      -> ACQUIRE       when a target enters sensor range
ACQUIRE     -> ENGAGE_GUN    when weapon_profile.can_hit(target) and ram_score < gun_score
ACQUIRE     -> ENGAGE_RAM    when vehicle.can_ram and ram_score >= gun_score
ENGAGE_*    -> PURSUE        when target leaves weapon range but is still an objective threat (carrier, bomb, hill)
ENGAGE_*    -> EVADE         when incoming_threat (rocket lock tone, Scorpion barrel on us, EMP charging, boarder within boarding radius)
ANY         -> RETREAT       when hull_fraction < retreat_threshold or weapon_disabled or driver_shield_down (H2/H3)
RETREAT     -> ABANDON       when hull_fraction < abandon_threshold or vehicle is EMP'd with an enemy inside 8 m
ANY         -> OBJECTIVE     when the gametype hook fires (flag taken, hill moved, bomb dropped); objective rules in the game sections override
```

Default thresholds (Proposed, tune per game):
- `retreat_threshold`: 0.40 for armed vehicles, 0.60 for transports, 0.25 for the Chopper (it is at its best when reckless).
- `abandon_threshold`: 0.15, or immediately when a boarder is on a tank's hull and the gunner is dead (Reach counter-board rule).
- `boarding_alert_radius`: 6 m for ground vehicles, 10 m for hovering aircraft. Response: accelerate to full speed and turn away; a vehicle moving at full speed cannot be boarded (Halopedia).
- `sensor_range`: 60 m ground, 120 m air; `weapon_range`: chaingun 40 m, Gauss 90 m, cannon 100 m, mortar 80 m (lobbed), Ghost cannons 30 m, Banshee cannons 40 m, bomb 60 m. All Proposed.

**4.2 Target scoring (Proposed)**

```
score(t) = base_threat(t) * objective_weight(t) * killability(self, t) * angle_factor(self, t) - exposure(self, t)
base_threat:    Banshee 1.0, Hornet/Falcon 0.9, Scorpion 1.0, Wraith 1.0, Gauss hog 0.9, Chopper 0.8,
                Warthog 0.7, Revenant 0.6, Ghost 0.5, Mongoose 0.3, infantry 0.3, infantry with rockets/laser/PL 0.9
objective_weight: flag/bomb/ball carrier 2.0, player inside hill 1.5, anything inside 10 m of our objective 1.3, else 1.0
killability:    1 / expected_time_to_kill from the Reach TTK matrix (or the extracted per-game equivalent); 0 if we cannot damage it
angle_factor:   1.0 if target is inside our weapon arc now, 0.5 if we must turn more than 90 degrees, 0.2 if it is in our blind cone (tank overhead, Chopper rear)
exposure:       0.5 if engaging puts us inside a Scorpion/Wraith lane, 0.3 if it drags us past a rocket spawn, 0.4 if a Banshee is above us and we have no anti-air
```
Vehicle-specific overrides: Banshee multiplies air targets by 2; Gauss multiplies vehicles by 1.5 and infantry by 0.5; Ghost and Chopper multiply any target inside ram range by 1.5 and tanks by 0 for ramming; Wraith multiplies stationary targets by 1.5 and moving infantry by 0.4; transports score every target 0 and only run the escort and objective logic.

**4.3 Ram geometry (Proposed, applies to Warthog, Mongoose, Ghost, Chopper, Revenant)**

```
can_commit = closing_speed > v_min(vehicle) and |heading_error| < theta(vehicle) and path_clear(2 * commit_distance) and not target.armor_lock
v_min:            Warthog 0.6 * max, Ghost 0.8 * max (needs boost), Chopper 0.7 * max (needs boost), Mongoose 0.9 * max
theta:            Warthog 20 deg, Ghost 12 deg, Chopper 8 deg, Mongoose 15 deg   (narrower = worse steering)
commit_distance:  1 to 2 Scorpion lengths (Halopedia); start boost here, not before
aim_point:        target.position + target.velocity * (distance / closing_speed)   (lead the splatter like a projectile)
abort:            if the target sidesteps more than one vehicle width after commit, do not steer into them; drive through, boost out, re-acquire
post_hit:         keep throttle for 1.5 s, then check hull and reassess; never stop beside the kill
vehicle-vs-vehicle: Warthog and Chopper head-on against Ghost/Mongoose/Prowler = commit; Chopper head-on against Warthog/Hornet-on-ground/Chopper = commit (boosted); anyone against Scorpion/Wraith/Elephant = never
armor_lock (Reach): a locked target damages or kills the rammer (Wikipedia, Halopedia); treat an Armor Lock glow as a hard no-ram and switch to the gun or go around
```

**4.4 Gunnery (Proposed)**
- **Hitscan or near-hitscan (chaingun, Gauss, coax, sniper):** aim at current position plus a small lead for Gauss on crossing targets.
- **Slow projectiles (Ghost, Banshee cannons, Wraith AI gun):** `lead = target.velocity * (range / bolt_speed)`; read `bolt_speed` from the projectile tag. Fire in bursts and walk the stream onto the target; plasma_turret has no spin-up.
- **Lobbed (Wraith, Revenant mortars):** solve the arc for the mortar's muzzle speed and gravity scale from the projectile tag; prefer targets whose predicted position in `flight_time` is inside the 2.25 wu outer splash radius, which in practice means stopped vehicles, turret users, hill campers, and flag stands.
- **Chaingun spin-up:** hold the trigger on empty air for 0.7 s when a target is expected inside two seconds; Tag ramp is 5 to 15 rps.
- **Banshee bomb:** in Reach it homes on vehicles, so fire it at any vehicle inside 60 m and keep flying; in Halo 3 it does not track, so dive to under 30 m and release on a stationary target; in Halo 4 lead manually; never in Halo 2 MP.
- **Scorpion overhead blind spot:** if a Banshee is inside a 50-degree cone above the tank, stop trying to elevate, drive to put a wall or slope between you, and let the coax or the escort deal with it.
- **Weak-part aiming:** when the Reach matrix applies, prefer the brittle_mech rear hatch of tanks (3x explosion_large, 2x collision) and the Ghost's gas tank over the hull; prefer the Warthog's glass over its hull for explosive splash (2x to 3x).

**4.5 Crew coordination (Proposed)**
- Driver keeps the gunner's best arc (Warthog sides and rear, Scorpion turret front 180) on the highest-scored target; the driver's steering loop takes the gunner's desired bearing as an input.
- Gunner reports `target_lost` and `reloading`/`overheated` so the driver changes course rather than circling a target nobody can shoot.
- Tank gunners (Halo 3 and ODST coax seat) have one standing order: shoot anything on the hull or inside 10 m before shooting anything else.
- Passengers in a Warthog bed, Hornet, Falcon, or Prowler use their own loadout on the driver's current target unless they are the objective carrier, in which case they do not fire at all and the driver's route optimises for cover, not kills.
- Transport driver waits at the pickup until riders are seated or 8 s elapses, then leaves; it returns on a `pickup_request` from any bot inside 40 m.

**4.6 Threat response table (Proposed)**

| Cue | Vehicle response |
|---|---|
| Rocket lock-on tone (Halo 2, Reach) | Banshee: roll or flip immediately, then break line of sight. Ground: hard turn across the rocket's path; a 90-degree change at 25 m beats a tracking rocket in Reach. |
| Scorpion or Wraith barrel aligned within 10 degrees | Light vehicle: reverse and break line of sight inside 1.5 s (cannon cycle is 3 s). Ghost: boost perpendicular. Banshee: climb into the overhead cone. |
| Plasma Pistol charge glow or Grenade Launcher held | Full throttle away from the holder; do not approach within 15 m. If hit (engine dead), driver and gunner exit on the side away from enemies if any enemy is inside 10 m. |
| Boarder inside `boarding_alert_radius` | Accelerate and turn away. Tank: gunner engages boarder; if gunner is dead, driver exits (Reach rule) and re-boards after the boarder commits. |
| Hull below `retreat_threshold` | Move toward the nearest friendly spawn or armoured friendly, keep the gunner firing to the rear. |
| Vehicle smoking plus explosive incoming | Exit now; vehicles explode on destruction and kill occupants. |
| Armor Lock glow on a target (Reach) | Cancel any ram; fire from range; never drive within 3 m. |
| Hill or flag event | Hand control to the objective rules in the game section (rule IDs CE-, H2-, H3-, ODST-, REACH-, H4-). |

**4.7 Vehicle selection at spawn (Proposed)**

Priority is by role, not by vehicle strength: one anti-air (Banshee, Hornet, Falcon, rocket hog), one anti-vehicle (Gauss hog, Scorpion, Wraith, Chopper), one transport (Warthog, Transport Hog, Mongoose, Prowler, Falcon), then fill with harassers (Ghost, Chopper, Mongoose). A bot picks the highest-priority unfilled role it is nearest to. Objective modes bias transport up (CTF, Assault) or anti-vehicle up (KOTH, Territories).

### 5. Known gaps that block a human-fidelity bot
- Per-game vitality, material tables, speeds, and boost timings for Halo CE, 2, 3, ODST, and 4 are not published; they must be extracted with the mod tools as described in section 1.
- Splatter damage values (vehicle mass times speed per game) are in the collision damage tags and are not reproduced here.
- Reach Spartan multiplayer shield and body values may differ from the campaign tag values used in the Spartan table.
- Bolt speeds and mortar muzzle velocities are in the projectile tags; without them the lead formulas in 4.4 are structural only.
- The Reach TTK matrix assumes hull hits; real fights mix hull, weak-part, and occupant damage.

---

## Halo: Combat Evolved (MCC)

**Status key**
- **Yes:** Confirmed drivable in this game from retrieved sources.
- **Verify:** Not confirmed. Test in-game.
- **Community:** Reported by players or wiki editors. Not tested by us.
- **Proposed:** Design target for the mod, not native MCC AI.

---

### Critical Halo CE facts for your mod

- **Warthog and Scorpion cannot be destroyed in Halo CE at all.** Halopedia: in Halo CE only the Ghost and Banshee can actually be destroyed. Players also report that in MCC CE multiplayer vehicles are invulnerable and only occupants can be killed, so even the Ghost and Banshee may be indestructible in MP. Verify before building any "destroy the vehicle" logic.
- **No boarding in Halo CE.** Boarding was introduced in Halo 2. Theft rules do not apply to CE vehicles unless your mod adds them.
- **No EMP in Halo CE.** Plasma pistol EMP was added in Halo 3.
- **Mongoose is not in CE multiplayer.** Wraith is not usable in CE.

---

### Roster

| Vehicle | Status |
|---|---|
| M12 Warthog (chaingun) | Yes |
| M12A1 Rocket Warthog (LAAV) | Yes (PC and CE MCC per sources) |
| M808 Scorpion | Yes |
| Ghost | Yes |
| Banshee | Yes |

---

### M12 Warthog (Chaingun)

- **Seats:** Driver, gunner (chaingun), passengers
- **Weapons:** Chaingun turret
- **Theft:** Not applicable in CE

**Weak points**
- Community: in MCC multiplayer, the Warthog reportedly cannot be destroyed. The targets are the driver and gunner.
- Kill the gunner first. The gunner is the only crew member who can hurt infantry at range.
- Flip: Halopedia says a frag grenade flips a Warthog and knocks the driver and passenger out. Verify this in CE, because flip behavior varies between games.

**Running people over and ramming**
- Halopedia notes the Warthog was the best splatter vehicle in CE, because it was indestructible in the campaign and fast.
- Drive at full speed. Swerving hard at speed can roll the Warthog.
- Halopedia: in Halo 2 and Halo 3, a head-on ram at full speed against an enemy Ghost destroys it, as long as you are not going uphill. Verify whether this works in CE.
- Community "hog wars": two Warthogs ram each other's sides or front bumpers. Flipped drivers can be finished on foot.

**Mount, kill, and take it**
- No boarding exists in Halo CE. The only ways to remove this vehicle from play are to kill its occupants or to flip it.
- A frag grenade under the chassis flips it and throws the driver and gunner out; finish them on foot. A stuck plasma grenade on the bumper also flips it (community CE vehicle guide).
- Melee: a Spartan standing beside a stopped Warthog can melee the gunner off the turret. The driver is exposed from the side.

**AI tactics (Proposed)**
- Patrol flanking routes around the objective. Keep moving.
- The gunner suppresses infantry at range. The driver does not stop in the open.
- Ram infantry when speed is above a threshold and no Scorpion is lined up on the Warthog.
- Retreat below half health.

**Avoid**
- Scorpion cannon lines. A Scorpion destroys Warthog occupants quickly.
- Any Banshee in the air. The Warthog has no anti-air.
- Uphill head-on approaches toward a Ghost, which has the height advantage.

---

### M12A1 Rocket Warthog (LAAV)

- **Seats:** Driver, gunner
- **Weapons:** Rocket pods (anti-armor)

**Weak points**
- Community: in CE MP the vehicle reportedly cannot be destroyed. Target the crew.
- Verify whether a frag grenade flip works on this variant.

**Running people over**
- Not a ram vehicle. Use it at range against vehicles. Ramming infantry wastes its main weapon and leaves it exposed.

**Mount, kill, and take it**
- No boarding exists in Halo CE. The only ways to remove this vehicle from play are to kill its occupants or to flip it.
- A frag grenade under the chassis flips it and throws the driver and gunner out; finish them on foot. A stuck plasma grenade on the bumper also flips it (community CE vehicle guide).
- Melee: a Spartan standing beside a stopped Warthog can melee the gunner off the turret. The driver is exposed from the side.

**AI tactics (Proposed)**
- Fire from maximum range at vehicles, then withdraw.
- Keep distance from other rocket users so two rocket vehicles do not commit to the same target.

**Avoid**
- Banshee, close-range infantry, and any vehicle that can ram it.

---

### M808 Scorpion (Main Battle Tank)

- **Seats:** Driver, gunner
- **Weapons:** 90mm cannon (main), coaxial chaingun (secondary)

**Weak points**
- Community: the Scorpion reportedly cannot be destroyed in CE MP. The targets are the driver and gunner.
- The driver is exposed when the vehicle is stopped, per community reports. Headshots on a still driver work.
- Community reports a cannon cooldown of about four seconds in MCC CE multiplayer. Verify.

**Running people over**
- Too heavy and slow to be a real ramming vehicle. It crushes infantry it drives over, but the cannon and coaxial chaingun do the real work.
- Community tip: stop and fire at infantry rather than chasing them.

**Mount, kill, and take it**
- No boarding exists in Halo CE. The only ways to remove this vehicle from play are to kill its occupants or to flip it.
- The CE Scorpion cannot be destroyed. Headshot the driver through the open hatch when the tank stops, and shoot the gunner off the turret. Pistol and sniper headshots work (community).
- Grenades and rockets do nothing to the hull; they only matter if they flip the tank, which is rare.

**AI tactics (Proposed)**
- Hold a fixed position covering the objective. Do not chase.
- Coaxial chaingun on infantry, cannon for vehicles.
- Back toward cover when a Banshee approaches, since the cannon cannot track air.

**Avoid**
- Banshee. The cannon cannot track air.
- Head-on Scorpion duels, which waste time in CE multiplayer.
- Open ground between two enemy Scorpions.

---

### Ghost

- **Seats:** Driver
- **Weapons:** Twin plasma cannons (main). Boost is a movement ability.

**Weak points**
- Community: the Ghost reportedly cannot be destroyed in CE MP. The target is the driver.
- Shooting a moving Ghost is hard. Community tip from later games: a teammate in Armor Lock forces the driver to wait, which gives you time to shoot.

**Running people over**
- The Ghost is the lightest ground vehicle with a boost, which makes it the fastest splatter option in CE.
- Halopedia's splatter guidance (from later Halo games): do not boost until you are about one to two Scorpion lengths from the target. Boosting from farther away gives the target time to jump, boost sideways, stick you with a grenade, or board you.
- If you miss the ram, switch to the plasma cannons or boost to a new target.

**Mount, kill, and take it**
- No boarding exists in Halo CE. The only ways to remove this vehicle from play are to kill its occupants or to flip it.
- The driver has no canopy. Pistol and sniper headshots kill the driver while the hull keeps moving. Melee the driver as the Ghost passes at low speed.

**AI tactics (Proposed)**
- Fast flank harassment. Run down infantry in the open.
- Use the plasma cannons on vehicles and on infantry too far to ram.
- Boost out of Scorpion cannon lines, but check the escape route first so you do not boost into a wall.
- Retreat when two or more enemy vehicles are close.

**Avoid**
- Scorpion cannon lines.
- Banshee. The Ghost has no anti-air.
- Enclosed areas where infantry can corner it.

---

### Banshee

- **Seats:** Pilot
- **Weapons:** Twin plasma cannons (main). Fuel rod cannon (secondary).

**Weak points**
- Community: in CE MP the Banshee reportedly cannot be destroyed. The target is the pilot.
- Rocket Launcher lock-on: Halopedia says the Rocket Launcher can lock onto fast vehicles like Banshees in Halo 2 and Reach. Verify whether CE's Rocket Launcher locks on in MCC.
- Halopedia notes that a good Banshee pilot can throw the aircraft around to break locks and avoid rockets.

**Running people over**
- The Banshee's damage comes from plasma cannons and the fuel rod cannon, not from ramming.
- Halopedia notes the fuel rod can flip Warthogs and Mongooses in later games. Verify whether this works on Warthogs in CE.
- Banshee boosting can launch the pilot a long way ("Banshee launch"), which is movement, not a kill.

**Mount, kill, and take it**
- No boarding exists in Halo CE. The only ways to remove this vehicle from play are to kill its occupants or to flip it.
- Halopedia: the Banshee is one of the two CE vehicles that can actually be destroyed (campaign). In MCC CE multiplayer players report it is invulnerable, so plan on killing the pilot.
- The pilot is exposed when the Banshee banks or lands. Pistol fire at the cockpit kills the pilot. Rocket lock-on is unverified in MCC CE.
- Grenades: a stuck plasma grenade on a landed or low Banshee kills the pilot; thrown frags rarely connect with it in the air. No boarding exists in CE.

**AI tactics (Proposed)**
- Patrol the air above the objective.
- Attack other flying vehicles first.
- Attack ground vehicles next, using the fuel rod on Warthogs and Ghosts.
- Attack infantry with plasma cannons. Use the fuel rod on clusters.
- Swoop attacks: dive onto ground targets, then climb out.

**Avoid**
- Scorpion cannon when the Banshee is grounded or slow.
- Infantry with Rocket Launchers, especially when the Banshee is turning.

---

### Theft rules (CE)

- **Not applicable.** Halo CE has no boarding.
- If your mod adds theft to CE, mark it as a custom mod feature.

---

### Open items

- Confirm CE MP vehicle invulnerability in MCC.
- Confirm Rocket Launcher lock-on in MCC CE.
- Confirm the fuel rod's effect on Warthogs in CE.
- Confirm Scorpion cooldown in MCC CE.

---

### Objective Game Types (Halo CE)

**Scope and status**
- **Confirmed for CE:** Capture the Flag (Blood Gulch is the reference map in sources), and King of the Hill variants listed by Halopedia for CE: King, Classic King, Classic King Pro, Crazy King, Team King, Phantom King.
- **Verify:** Oddball in MCC CE multiplayer. Confirm which King variants are in MCC CE.
- **CE-specific constraints:** No boarding (so carriers cannot be hijacked). No EMP. Vehicles are reportedly indestructible in MCC MP, so pursuit and escort tactics rely on occupant kills, flips, and speed rather than destroying the vehicle.
- **Flag damage:** Halopedia says the flag was not an instant kill in CE. Carriers are not instantly killed by a single hit.

#### Capture the Flag (CE)

**Best vehicles (community, Blood Gulch):** Ghost, Warthog, Banshee (Halo PC and Xbox One only, which covers MCC).

**Core carrier logic**
- **CE-CTF-01 Enter-grab-leave:** IF your team has a Warthog parked at the entrance, THEN drive it into the enemy entrance, grab the flag on foot, and drive out. Community: this works because the enemy must go through the other entrance to reach you.
- **CE-CTF-02 Teleporter park:** IF a Warthog, Ghost, or Banshee is parked at the relevant teleporter, THEN the carrier walks into the enemy base, takes the flag, runs back through the teleporter, and drives or flies away.
- **CE-CTF-03 Support circle:** IF one escort drives a Warthog circling the enemy base, THEN the other Warthog or Banshee bombards defenders while the carrier takes the flag. Community: drop a rider or gunner and keep circling to avoid sniping and bombardment.
- **CE-CTF-04 Gunner-through-wall:** IF a Warthog is driven backward into an entrance, THEN the gunner can shoot through the wall where the flag sits. Community reported.
- **CE-CTF-05 Solo grab:** IF the enemy is engaged in combat elsewhere, THEN a solo player runs in, takes the flag, and gets into a Warthog immediately.

**Pursuit logic**
- **CE-PUR-01 Chase vehicle assignment:** IF an enemy carrier leaves in a Warthog, THEN dispatch a Ghost (faster, boosts) to intercept, not another Warthog that cannot close the gap.
- **CE-PUR-02 Intercept point:** Predict the carrier's path and aim for where the vehicle will be in about two seconds (community: "aim where their head will be"). Halopedia: follow the carrier's vehicle as long as possible.
- **CE-PUR-03 Shot discipline:** IF chasing a Warthog, THEN the Banshee fuel rod can flip it, which is a stronger play than a plasma stream.

**Defense logic**
- **CE-DEF-01 Park over the flag:** IF no enemy carrier is active, THEN park a Warthog or Scorpion directly over your flag. The vehicle blocks the spot and is a visual warning.
- **CE-DEF-02 Hold the teleporter:** IF an enemy carrier uses a teleporter, THEN the defending Ghost or Banshee waits at the exit.

**Map logic (Blood Gulch)**
- Two entrances per base. Assign one escort to each entrance.

#### King of the Hill (CE)

**Hill rules**
- Halopedia lists CE King modes: King (2 minutes to win), Team King (uncontested control to win), Crazy King (hill moves every minute), Phantom King (everyone has active camo, hill does not move).

**Logic**
- **CE-KOTH-01 One scorer:** IF your team controls the hill, THEN one player stays on the hill scoring while the rest fan out and defend (Halopedia's team tactic).
- **CE-KOTH-02 Vehicle anchor:** IF the hill is uncontested, THEN park a Scorpion or Warthog inside the ring to block approaches. Community reports say CE vehicles behave differently in MCC multiplayer, so verify this in-game.
- **CE-KOTH-03 Moving hill:** IF Crazy King moves the hill, THEN the first team with a Ghost or Warthog at the new location gets the points. Ghosts reposition fastest.
- **CE-KOTH-04 Contested hill:** IF an enemy enters the ring, THEN a Warthog gunner fires from outside the ring. Do not drive into the ring while enemies are inside.

#### Oddball (CE, verify)
- **CE-ODD-01 Carrier control:** IF your team holds the ball, THEN the carrier should not be driven alone. Escort with a Warthog or Ghost.
- **CE-ODD-02 Hunt the carrier:** IF the enemy holds the ball in a vehicle, THEN kill the carrier from a Banshee or Scorpion before the ball is passed or dropped.

---

## Halo 2 (MCC, including Anniversary Multiplayer)

**Status key**
- **Yes:** Confirmed drivable in this game from retrieved sources.
- **Verify:** Not confirmed. Test in-game.
- **Community:** Reported by players or wiki editors. Not tested by us.
- **Proposed:** Design target for the mod, not native MCC AI.

---

### Critical Halo 2 facts for your mod

- **Boarding starts here.** Players hold the action button near an enemy vehicle to board it. Scorpions and Wraiths are boarded differently from other vehicles.
- **Banshee fuel rod bomb is not in Halo 2 multiplayer.** Halopedia says the Banshee's fuel rod cannon became usable in multiplayer in Halo 3. The Halo 2 Anniversary multiplayer Banshee also has no fuel rod cannon. Do not give Halo 2 Banshees a fuel rod unless your mod adds it.
- **Vehicles are destroyable in Halo 2.** Halopedia notes Warthogs can be destroyed starting in Halo 2.

---

### Roster

| Vehicle | Status |
|---|---|
| M12 Warthog (chaingun) | Yes |
| M12G1 Gauss Warthog | Yes |
| M808 Scorpion | Yes |
| Ghost | Yes |
| Banshee | Yes |
| Wraith | Yes |
| Spectre | Yes (campaign: Quarantine Zone, Uprising, The Great Journey. Multiplayer: Halopedia shows a Spectre on Coagulation, and Halo 2 Anniversary has one) |
| M274 Mongoose | Anniversary multiplayer only. Not in Halo 2 Classic MP (the April 2022 MCC update removed it from random light-vehicle spawns; it survives only in the mod tools) |
| M274-M Gungoose | Anniversary multiplayer only. A Mongoose with two front-mounted, driver-fired M67 LMGs (Halopedia) |
| Hornet | Anniversary multiplayer only (Halopedia Hornet page shows an H2A MP Hornet and the MCC achievement "Shook the Hornet's Nest") |

**Not in Halo 2:** Brute Chopper (first appears in Halo 3), Brute Prowler, Revenant, Falcon.

**Not drivable:** Phantom (troop transport).

---

### M12 Warthog (Chaingun)

- **Seats:** Driver, gunner, passengers
- **Weapons:** Chaingun turret
- **Theft:** Boarding possible

**Weak points and boarding**
- Boarders must melee the hatch off or otherwise clear the driver before planting a grenade. In Halo 2 the boarded player can jump out.
- Kill the gunner first. Community reports say the gunner is the most dangerous crew member to a boarder.
- Flip: Halopedia notes a frag grenade flips a Warthog and knocks the driver and passenger out.

**Running people over and ramming**
- Halopedia notes Warthogs can be destroyed starting in Halo 2. A Warthog at speed is still the best ground splatter vehicle against infantry.
- Halopedia reports that in Halo 2 and Halo 3, a head-on ram at full speed destroys an enemy Ghost, as long as you are not going uphill.
- Community "hog wars": ram the other Warthog's side or front bumper to flip it.

**AI tactics (Proposed)**
- Flank routes around the objective. Keep moving.
- Gunner suppresses infantry. Driver does not stop in the open.
- Ram infantry above a speed threshold. Do not ram infantry standing beside a Scorpion.
- Retreat below half health.

**Avoid**
- Banshee, which can strafe the Warthog from above.
- Wraith mortar zones. Halopedia notes Wraiths are heavy damage at range.
- Scorpion cannon lanes.

---

### M12G1 Gauss Warthog

- **Seats:** Driver, gunner
- **Weapons:** Gauss cannon
- **Theft:** Boarding possible

**Weak points and boarding**
- Board the driver the same way as the chaingun Warthog.
- Gauss gunner is exposed when the vehicle is stopped. Community tip: shoot the gunner from range while the Warthog is parked.

**Running people over**
- Same as the chaingun Warthog, but the gunner is a slower, more accurate threat at range.

**Mount, kill, and take it**
- **Mount:** kill the gunner first (if it has one), then board the driver. In Halo 2 the thrown driver can fight back, so melee them immediately.
- **Grenades:** a frag under the chassis flips it and throws everyone out; a stuck plasma grenade does heavy damage or destroys it; two direct grenade hits or one rocket destroys it (Halo 3 onward).
- **Melee:** a Spartan beside a stopped Warthog can melee the gunner off the turret or the passenger out of the seat.
- **Gauss gunner:** the gunner is fully exposed and must stop moving to aim. Snipe the gunner while the hog is parked on overwatch; the Gauss cannon has no close-range answer.

**AI tactics (Proposed)**
- Long-range overwatch on choke points.
- Reposition after each few shots. Do not stand still in one spot.
- Do not chase fleeing targets past the objective.

**Avoid**
- Banshee, close-range Scorpion engagements, and flanks without cover.

---

### M808 Scorpion

- **Seats:** Driver, gunner
- **Weapons:** 90mm cannon (main), coaxial chaingun (secondary)
- **Theft:** Boarding possible, but harder than most vehicles

**Weak points and boarding**
- Halopedia: boarding a Scorpion works differently. The boarder jumps onto the tank and can melee the hatch or plant a grenade. A Scorpion gunner can fire on boarders, so kill the gunner before boarding.
- Halo 2 specifics: the boarder has to melee the hatch off before planting a grenade, and the boarded player can jump out. Community: a rocket aimed at the hatch destroys the tank if the hatch is still on.
- Halo 2 Scorpion turret: community reports say the turret is almost invulnerable. The body and four motors are the weak points.
- Community: each tread takes double damage once its armor is shot off. Verify.

**Running people over**
- Too heavy and slow to be a ramming vehicle. It crushes infantry it drives over, but the cannon does the work.

**AI tactics (Proposed)**
- Hold a fixed position covering the objective.
- Coaxial chaingun on infantry, cannon for vehicles.
- Back toward cover when a Banshee approaches.

**Avoid**
- Banshee, which can circle the Scorpion above its cannon's arc.
- Wraith mortar range.
- Head-on approaches toward enemy Scorpions.

---

### Ghost

- **Seats:** Driver
- **Weapons:** Twin plasma cannons (main). Boost is a movement ability.
- **Theft:** Boarding possible

**Weak points and boarding**
- Boarders melee the hatch off, then plant a grenade. The boarded player can jump out in Halo 2.
- Halopedia: the Ghost is harder to board than some vehicles because it moves in all directions.
- Halopedia's trick: dodge a Ghost so it boosts into a wall, then board it from behind while it backs out.

**Running people over**
- Halopedia's splatter guidance from later games: do not boost until about one to two Scorpion lengths from the target. Boosting from farther away gives the target time to jump, boost sideways, stick the Ghost with a grenade, or board it.
- If the ram misses, switch to plasma cannons or boost to a new target.
- Halopedia notes Ghosts can run down infantry on flat ground but are weak to a head-on Warthog ram.

**AI tactics (Proposed)**
- Fast flank harassment. Run infantry down in the open.
- Plasma cannons for vehicles and far targets.
- Boost out of Scorpion cannon lines, after checking the escape route.
- Retreat when two or more enemy vehicles are close.

**Avoid**
- Scorpion cannon lines.
- Banshee air superiority. The Ghost has no anti-air.
- Wraith mortar and Ghost-on-Ghost ramming in narrow lanes.

---

### Banshee

- **Seats:** Pilot
- **Weapons:** Twin plasma cannons (main). No fuel rod in Halo 2 multiplayer.
- **Theft:** Boarding possible

**Weak points and boarding**
- Boarding a Banshee: melee the hatch off, then plant a grenade, as with other vehicles in Halo 2.
- Community: a Rocket Launcher can lock onto Banshees in Halo 2 and tracks them well.
- Halopedia: in Halo 2 both anti-grav pods on a Banshee can be shot off and the Banshee still flies. Verify whether the pods can be shot off in MCC.

**Running people over**
- Not a ramming vehicle. The Banshee's damage comes from plasma cannons and swoops.
- Halopedia notes Banshee "launches" (super jumps) exist in Halo 2 and can be used for movement.

**AI tactics (Proposed)**
- Air patrol over the objective.
- Attack other flying vehicles first.
- Attack ground vehicles next.
- Attack infantry with plasma cannons. Dive and climb out after each swoop.

**Avoid**
- Players with Rocket Launchers, who can lock on.
- Wraith mortar. Community reports say the mortar is less effective against flying targets in Reach. Verify in Halo 2.
- Scorpion cannon when the Banshee is grounded or slow.

---

### Wraith

- **Seats:** Driver, gunner
- **Weapons:** Plasma mortar (main). Two small automatic plasma cannons on the hood (secondary).
- **Theft:** Boarding possible

**Weak points and boarding**
- Halopedia: the two hood plasma cannons protect the Wraith from nearby infantry. If a boarder gets past them and jumps onto the vehicle, they can melee the driver.
- Community: front and back fins take about 20 percent more damage than the nose. The rear is as strong as the nose. This comes from community testing and the game version is not stated, so verify in Halo 2.
- Community: the Wraith's mortar is less effective against flying targets.

**Running people over**
- Wraiths are slow and not used for ramming. Community: a Warthog run can end a Wraith's life, so Warthogs are the main answer to Wraiths on foot.

**Mount, kill, and take it**
- **Mount:** kill the gunner, then board from the rear or side, outside the cannon arc. Jump-on-top boarding: melee the hatch until the driver is exposed and dead (keeps the tank), or plant a grenade (kills all occupants and destroys the tank). See the Quick Reference for the per-game hatch rules.
- Halo 2: melee the hatch off before the grenade; the boarded player can jump out, and the planted grenade can hurt you. A rocket into an intact hatch destroys the tank.
- **No EMP in Halo 2.** Stop the tank by killing the driver or by catching it against terrain.

**AI tactics (Proposed)**
- Hold a long-range position and shell the approach to the objective.
- Relocate after every few shots.
- Do not advance into close-range combat.

**Avoid**
- Banshee in the air. Community reports say the Wraith's mortar struggles against flying targets, which makes a Banshee the main anti-Wraith threat in the air. Verify in Halo 2.
- Hornet and Ghost flanks.
- Warthog runs, which are the main threat to a Wraith.

---

### Mongoose (Anniversary MP: Verify)

- **Seats:** Driver, passenger
- **Weapons:** None mounted. Passenger weapon only.
- **Theft:** Verify whether it can be boarded in Halo 2 Anniversary

**Weak points**
- Community: Mongoose is small and fragile. A grenade or a passenger's shot can flip or destroy it.

**Running people over**
- Lighter than the Warthog. Community: to run down heavier targets like Brutes, hit them directly at top speed.

**Mount, kill, and take it**
- **Mount:** board it and both driver and passenger are kicked off together (Reach onward).
- **Grenades:** any grenade near it flips it; a stuck grenade kills both riders. It has no armor, so rifle fire at the riders is enough.

**AI tactics (Proposed)**
- Fast flanking and objective runs.
- Passenger dismounts to capture or defend.

**Avoid**
- Mounted-gun vehicles, Banshees, and Wraith mortars.

---

### M274-M Gungoose (Anniversary MP only)

- **Seats:** Driver, passenger
- **Weapons:** Two front-mounted M67 LMGs fired by the driver (Halopedia)
- **Theft:** Boarding rules follow the Mongoose. Verify in H2A.

**Running people over**
- Same light chassis as the Mongoose. Hit infantry directly at top speed or the ram does nothing.

**Mount, kill, and take it**
- **Mount:** board it and both driver and passenger are kicked off together (Reach onward).
- **Grenades:** any grenade near it flips it; a stuck grenade kills both riders. It has no armor, so rifle fire at the riders is enough.

**AI tactics (Proposed)**
- Fast flanking with driver fire. The passenger dismounts for objectives.
- Gungoose CTF (H2A): the vehicle itself is used to steal the enemy flag and score (Halopedia). Keep the Gungoose moving through the flag stand rather than stopping.

**Avoid**
- Anything with a mounted gun, Banshees, Wraith mortars, and Chopper-style rams (Warthog head-on).

---

### Hornet (Anniversary MP only)

- **Seats:** Pilot plus two side passengers
- **Weapons:** Pilot-fired machine gun (main) and missiles (secondary)
- **Theft:** Boarding possible (Halopedia lists Hornets among commonly boarded vehicles)

**Mount, kill, and take it**
- **Mount:** boardable. EMP is not in Halo 2, so wait for it to hover low or land, then board or shoot the exposed pilot.
- **Kill the crew:** the pilot and side passengers are all exposed. Battle Rifle, Carbine, and sniper headshots kill them without touching the airframe, which leaves the vehicle free to take.
- **Grenades and rockets:** a stuck plasma grenade on the fuselage destroys it; Spartan Laser and rockets kill it in one or two hits; the Missile Pod (Halo 3) locks on.

**AI tactics (Proposed)**
- Strafing runs on ground vehicles. Break off when a Banshee engages.
- Passengers fire their own weapons from the side mounts, so the Hornet doubles as an air transport for two players.

**Avoid**
- Banshee head-on, Wraith mortar, Scorpion cannon, and rocket lock-on (Halo 2 Classic rockets track vehicles since April 2022; verify H2A).

---

### Spectre (campaign and multiplayer)

- **Seats:** Driver, gunner
- **Weapons:** Plasma cannon turret
- **Theft:** Boarding possible, but Halopedia says it is harder because the Spectre moves in all directions

**Weak points**
- Halopedia: the Spectre's plasma bolts are reflected by a Scorpion's armor, so the turret performs poorly against tanks.
- Halopedia: boarding is harder against a Spectre because it moves in all directions. Board it while it is stopped or turning.

**Mount, kill, and take it**
- **Mount:** boardable, but Halopedia warns it is harder than most because the hover chassis moves in every direction. Board it when it is stopped, reversing, or wedged on terrain. The driver is thrown out and the vehicle is yours.
- **Kill the crew:** the driver and gunner sit exposed; headshots remove them one at a time. Kill the gunner first.
- **Grenades and rockets:** community: explosives are the reliable answer. A stuck plasma grenade on the driver's seat or a rocket kills it. Frags under it do little because hover vehicles do not flip easily.

**AI tactics (Proposed)**
- Fast infantry assault. Avoid vehicle duels.

**Avoid**
- Scorpion, Wraith, and Banshee.

---

### Theft rules (Halo 2)

- Boarding is the main theft mechanic. A player can hold the action button near an AI vehicle to board it.
- **Stealable:** Warthog, Gauss Warthog, Ghost, Banshee, Scorpion, Wraith, Spectre.
- **Steal radius (Proposed):** 3 m for ground vehicles, 4 m for Banshees.
- **Trigger (Proposed):** a player can steal an AI vehicle when the AI driver is not engaged in combat.
- **Engaged driver:** does not eject. The player has to kill the driver or the gunner first.

---

### Open items

- Confirm Mongoose, Gungoose, and Hornet behavior in Anniversary MP.
- Confirm Spectre map placements in Classic and Anniversary MP.
- Confirm Wraith front and back fin damage in Halo 2.
- Confirm whether Banshee anti-grav pods can be shot off in MCC.

---

### Objective Game Types (Halo 2, including Anniversary Multiplayer)

**Scope and status**
- **Confirmed for Halo 2:** Capture the Flag, Assault (bomb), King of the Hill variants (King, Team King, Team Crazy King), and Oddball (verify in MCC Classic and Anniversary).
- **Anniversary-specific:** Halo 2 Anniversary multiplayer has the Gungoose, a Mongoose variant with two front-mounted, driver-fired M67 LMGs (Halopedia's cut-vehicle page). Halo 2 Anniversary CTF variants listed by Halopedia: Multi Flag CTF, Classic CTF, Warlock Classic CTF, Neutral Flag CTF (capture the neutral flag and return it to your base), and Gungoose CTF (use a vehicle to steal the enemy flag and score).
- **Classic MP:** The Mongoose will not spawn in Halo 2 Classic custom games with random light vehicles (April 2022 MCC update). It remains available in Halo 2's mod tools only. Do not give Classic Halo 2 AI a Mongoose.
- **Rocket lock-on:** Rockets in Halo 2 Classic MP lock onto and track vehicles (April 2022 MCC update). Use this when a Banshee or Ghost is the target.
- **Banshee:** No fuel rod in Halo 2 multiplayer (see the Banshee profile above).

#### Capture the Flag (Halo 2)

**Vehicle assignment**
- **H2-CTF-01 Carrier vehicle:** IF a Warthog or Ghost is available at your base, THEN the carrier boards it for the run. Halopedia (Halo 2 campaign page) calls the Ghost the fastest hit-and-run option on the beach. Use the same logic in MP.
- **H2-CTF-02 Cram rule (community):** IF your team has one Warthog, THEN put the carrier in the driver seat and the other players on the bed or gunner seat. Passengers falling out or dying reduce the vehicle's speed and killing power.
- **H2-CTF-03 Escort ratio:** IF the carrier is in a vehicle, THEN at least one escort vehicle stays within 15 m. Community: lone carriers die.

**Carrier logic**
- **H2-CTF-04 Flip avoidance:** IF the carrier is driving through a narrow lane, THEN avoid hard turns at speed. Halopedia: Warthogs roll easily on hard turns and in Halo 2 can be destroyed.
- **H2-CTF-05 Gauss overwatch:** IF the enemy has a Gauss Warthog at a choke point, THEN the carrier's escort should engage it first, because a Gauss hit kills the carrier vehicle quickly.

**Pursuit logic**
- **H2-PUR-01 Rocket lock:** IF an enemy carrier is in a Ghost or Warthog, THEN a player with a Rocket Launcher uses the lock-on (Classic MP tracks vehicles since April 2022).
- **H2-PUR-02 Ram the chaser:** IF a Ghost is chasing your carrier head-on at full speed on flat ground, THEN a Warthog ram destroys it (Halopedia, Halo 2 and 3 Ghost ram).
- **H2-PUR-03 Follow distance:** IF you are the chaser, THEN stay 15 to 25 m behind the carrier. Closer and you get hit by the carrier's escort; farther and the carrier escapes.

**Defense logic**
- **H2-DEF-01 Flag guard vehicle:** IF no enemy carrier is active, THEN park a Warthog with a gunner over the flag.
- **H2-DEF-02 Tank block:** IF your base has a tank, THEN park it in the main entrance. Halo 2 Scorpion turret is almost invulnerable, so it blocks entrance traffic well (community).

#### Assault (Halo 2)

**Bomb logic**
- **H2-ASS-01 Sticky arming:** IF the bomb carrier dies during arming, THEN the arming time passes to a teammate who is inside the arm site (Sticky Arming option). Keep a second player in the circle.
- **H2-ASS-02 Arm time:** Halopedia says the arm time is usually around five seconds but can be changed. Plan vehicle escort around that window.
- **H2-ASS-03 Carrier protection:** Halopedia: have at least two teammates near the carrier and retreat if needed. A carrier with no blockers can drop the bomb, fight, and pick it up again.
- **H2-ASS-04 Drop-and-fight:** IF the carrier is attacked without teammates, THEN drop the bomb, kill the attacker, and recover it.

**Vehicle use**
- **H2-ASS-05 Drop-off vehicle:** IF the bomb carrier is pinned in the enemy base, THEN a Warthog or Ghost waiting outside the entrance gives the carrier a fast exit.
- **H2-ASS-06 Scorpion arm-site blocker:** IF your team has the Scorpion, THEN park it across the arm site entrance to block defenders from disarming.

#### King of the Hill (Halo 2)

**Modes**
- King: 2 minutes control to win, hill does not move.
- Team King: 1 minute uncontested control to win, hill does not move (Halopedia).
- Team Crazy King (Anniversary): earn points uncontested on the moving hill.

**Logic**
- **H2-KOTH-01 One scorer, rest defend:** Halopedia's team tactic applies here. One player scores inside the hill while the rest fan out and watch approaches.
- **H2-KOTH-02 Vehicle ring:** IF the hill is uncontested, THEN a Warthog gunner covers the entrance from outside the ring.
- **H2-KOTH-03 Moving hill:** IF Team Crazy King moves the hill, THEN the first Ghost or Warthog to reach the new location claims it. Ghost boost gives the fastest reposition.

#### Oddball (Halo 2, verify)
- **H2-ODD-01:** Carrier escort by Warthog gunner; Ghost reposition if the ball moves.
- **H2-ODD-02:** Banshee air cover from above a carrier is limited because the fuel rod is not in Halo 2 MP.

#### Headroom
- Halo 2 Anniversary multiplayer has the Gungoose. Verify its CTF and Oddball use before assigning roles. Do not assume it is in Classic MP.

---

## Halo 3 (MCC)

**Status key**
- **Yes:** Confirmed drivable in this game from retrieved sources.
- **Verify:** Not confirmed. Test in-game.
- **Community:** Reported by players or wiki editors. Not tested by us.
- **Proposed:** Design target for the mod, not native MCC AI.

---

### Critical Halo 3 facts for your mod

- **Boarding is fastest here.** Halopedia: in Halo 3, the boarding grenade can be shoved through the hatch and the occupant is trapped inside the vehicle. Boarding takes less time than in Halo 2.
- **EMP is available.** A charged Plasma Pistol shot, a manually detonated Grenade Launcher round, or a Power Drain disables a vehicle's engines and leaves it open to boarding. Halopedia says disabled vehicles crouch or deactivate.
- **Mongoose cannot be boarded.** You can melee the driver off as you pass, or board the passenger seat and kill the driver. Halopedia says Mongoose is vulnerable to EMP, which makes it easier to board when crouched.
- **Scorpion's secondary gun is manned by a second crew member.** Prima's guide says the driver has no control over the secondary machine gun, so an ally must man it.
- **Vehicles can be destroyed by grenades and rockets** in Halo 3 MP. Halopedia: a couple of direct grenade hits or a well-placed rocket destroys a Warthog.
- **Ramming is a real weapon from Halo 3 onward.** Halopedia: starting in Halo 3, vehicles take collision damage based on their mass and speed and can destroy one another by ramming. The Brute Chopper can destroy a Warthog with a head-on ram, and a Ghost that hits a solid object head-on can kill its driver. Build collision damage into the AI as a primary attack for the Chopper and a secondary attack for the Warthog.

---

### Roster

| Vehicle | Status |
|---|---|
| M12 Warthog (chaingun) | Yes |
| M12G1 Gauss Warthog | Yes |
| M831 Troop Transport Warthog ("Transport Hog") | Yes |
| M274 Mongoose | Yes |
| M808 Scorpion | Yes |
| Ghost | Yes |
| Banshee | Yes |
| Wraith | Yes |
| Hornet | Yes (stock on Avalanche; Forge object on Sandbox and Sandtrap; Transport Hornet without missiles on Avalanche and Sandbox) |
| Brute Chopper | Yes (stock MP on Sandtrap and Valhalla, and on the "Heavy" variants of Avalanche and Standoff; Forge object on many maps) |
| Brute Prowler | Yes (Forge only; not on any map by default, per Fandom. Campaign: The Ark, The Covenant) |
| M313 Elephant | Yes (Sandtrap only, one at each end of the map) |

**Not in Halo 3:** Spectre (Halo 2 only), Revenant (Reach only), Falcon (Reach only).

**Not drivable:** Pelican, Phantom, Scarab.

---

### M12 Warthog (Chaingun)

- **Seats:** Driver, gunner, passengers
- **Weapons:** Chaingun turret
- **Theft:** Boarding possible

**Weak points and boarding**
- Boarding the driver: the boarder's view matters. Community: when a Warthog's driver is boarded, turn your view 90 degrees to the right to face the boarder and melee them. When boarding a Warthog yourself, turn 90 degrees to the left to melee the stunned driver.
- Kill the gunner before boarding. The gunner can shoot anyone trying to board.
- Halopedia: ODST and Marines can flip Warthogs by hand in Halo 3 and ODST. A frag grenade flips a Warthog, knocking the driver and passenger out.
- Community: a sticky grenade does heavy damage. A couple of direct grenade hits or a single rocket destroys a Warthog.

**Running people over and ramming**
- Halopedia: a Warthog ram at full speed is the most reliable way to kill light vehicles. A Warthog can destroy an enemy Ghost head-on, as long as the Warthog is not going uphill.
- Halopedia: the Warthog is the second-best ramming vehicle against a Shade turret.
- The Prima Halo 3 guide advises keeping your passengers on the vehicle. Passengers falling out reduce the vehicle's offensive value.

**AI tactics (Proposed)**
- Flank routes around the objective.
- Escort the Transport Hog and suppress threats near it.
- Ram light infantry when speed is above a threshold.
- Gunner suppresses. Driver does not stop in the open.
- Retreat below half health.

**Avoid**
- Banshee overhead, which can dive on the Warthog.
- Wraith mortar zones.
- Scorpion cannon lanes.
- Brute Choppers. Halopedia notes that going bumper to bumper with a Chopper is dangerous because its heavy guns rip through light vehicles.

---

### M12G1 Gauss Warthog

- **Seats:** Driver, gunner
- **Weapons:** Gauss cannon
- **Theft:** Boarding possible

**Weak points and boarding**
- Same boarding and flip behavior as the chaingun Warthog.
- Community: a Gauss Warthog is lethal in the hands of a skilled gunner, but Halopedia notes it must change positions often or it will be overwhelmed.

**Running people over**
- Same as the chaingun Warthog.

**Mount, kill, and take it**
- **Mount:** kill the gunner first (if it has one), then board the driver. In Halo 3 and ODST the thrown driver is heavily damaged by the ejection melee; turn 90 degrees left after boarding to melee them again.
- **Grenades:** a frag under the chassis flips it and throws everyone out; a stuck plasma grenade does heavy damage or destroys it; two direct grenade hits or one rocket destroys it (Halo 3 onward).
- **Melee:** a Spartan beside a stopped Warthog can melee the gunner off the turret or the passenger out of the seat.
- **Gauss gunner:** the gunner is fully exposed and must stop moving to aim. Snipe the gunner while the hog is parked on overwatch; the Gauss cannon has no close-range answer.
- **EMP:** stops it so a boarder can walk up to it.

**AI tactics (Proposed)**
- Long-range overwatch on choke points.
- Reposition after each few shots.
- Do not chase fleeing targets past the objective.

**Avoid**
- Banshee and close-range Scorpion engagements.

---

### M831 Troop Transport Warthog ("Transport Hog")

- **Seats:** Driver, passenger bed (troops)
- **Weapons:** None
- **Theft:** Boarding possible. Stealable when the driver is idle or fleeing (Proposed rule below)

**Weak points and boarding**
- Same as the Warthog. Passengers on the bed can be thrown off when the vehicle flips.

**Running people over**
- Do not ram. Its job is transport, and a flipped Transport Hog loses its passengers.

**Mount, kill, and take it**
- **Mount:** kill the gunner first (if it has one), then board the driver. In Halo 3 and ODST the thrown driver is heavily damaged by the ejection melee; turn 90 degrees left after boarding to melee them again.
- **Grenades:** a frag under the chassis flips it and throws everyone out; a stuck plasma grenade does heavy damage or destroys it; two direct grenade hits or one rocket destroys it (Halo 3 onward).
- **Melee:** a Spartan beside a stopped Warthog can melee the gunner off the turret or the passenger out of the seat.
- **Transport Hog:** no gunner, so a single boarder takes it uncontested. The riders on the bed are the only defense; kill them with a grenade on the bed before boarding.
- **EMP:** stops it so a boarder can walk up to it.

**AI tactics (Proposed)**
- Drive players to and from objectives or points of interest.
- Stop at a safe distance and wait for passengers.
- Retreat toward the nearest friendly zone when attacked.
- Do not cross open ground without an escort Warthog or Mongoose.

**Avoid**
- Ghost, Wraith, Scorpion, Banshee lanes, and hostile infantry clusters.

---

### M274 Mongoose

- **Seats:** Driver, passenger
- **Weapons:** None mounted. Passenger weapon only.
- **Theft:** Cannot be boarded. Melee the driver off instead (see below).

**Weak points**
- Halopedia: the Mongoose cannot be boarded in Halo 3. A player can melee the driver off as they pass, or get in the passenger seat and kill the driver with a few quick melee attacks or shots to the back of the head.
- Halopedia: an EMP makes the Mongoose crouch and deactivate, which makes it easier to take the driver out.
- Prima: the Mongoose wobbles and falls over on uneven terrain. Keep it on all four wheels.

**Running people over**
- Prima: the Mongoose is much lighter than the Warthog. To run over a Brute, hit it directly at top speed.
- Community: ramming with a Mongoose is risky. Glancing off a rock can cost you your shields and alert the enemy. The enemy can then spin you and flip you.

**Mount, kill, and take it**
- **Mount:** cannot be boarded. Melee the driver off as it passes, or jump into the passenger seat and melee or headshot the driver from behind (Halopedia).
- **Grenades:** any grenade near it flips it; a stuck grenade kills both riders. It has no armor, so rifle fire at the riders is enough.
- **EMP:** it crouches and stops, which makes the riders sitting targets.

**AI tactics (Proposed)**
- Fast flanking and objective runs.
- Passenger dismounts to capture or defend objectives.
- Do not stay in one place for more than a few seconds.

**Avoid**
- Mounted-gun vehicles, Banshees, Wraith mortars, and Hornets.

---

### M808 Scorpion

- **Seats:** Driver, gunner (cannon), secondary machine gunner (ally-manned)
- **Weapons:** 90mm cannon (main), coaxial chaingun or secondary machine gun (manned by second crew)
- **Theft:** Boarding possible. Boarders jump onto the tank and do not use the normal boarding animation.

**Weak points and boarding**
- Halopedia: the boarder jumps onto the Scorpion and can either melee the hatch, exposing and killing the driver, or plant a grenade to kill all occupants and destroy the vehicle.
- Halopedia: a Scorpion's gunner can fire on anyone trying to board. Kill the gunner first.
- Halo 3 specifics: the grenade can be shoved through the hatch, and the occupant is trapped inside.
- Prima: the principal threats to a Scorpion's driver are Wraiths, Shade turrets, Banshees, Ghosts (especially in groups), and Brutes with fuel rod cannons.
- EMP: a charged Plasma Pistol shot disables the Scorpion's engines. Halopedia says a disabled vehicle is open to boarding.
- Community: a Scorpion's armor is tough, but a point-blank Mongoose ram explodes and damages the tank. Verify damage values in Halo 3.

**Running people over**
- Too heavy and slow to be a ramming vehicle. It crushes infantry it drives over.

**AI tactics (Proposed)**
- Hold a fixed position covering the objective.
- Coaxial or secondary chaingun on infantry, main cannon for vehicles.
- Back toward cover when a Banshee approaches, since the cannon cannot track air.
- Keep the second crew member manning the secondary gun at all times.

**Avoid**
- Banshee overhead.
- Wraith mortar.
- Gauss Warthog flank routes.
- Head-on approaches toward an enemy Scorpion.

---

### Ghost

- **Seats:** Driver
- **Weapons:** Twin plasma cannons (main). Boost is a movement ability.
- **Theft:** Boarding possible. Halopedia: harder against Ghosts because they move in all directions.

**Weak points and boarding**
- Halopedia's trick: dodge a Ghost so it boosts into a wall. While it backs out, board it from behind.
- Halo 3: boarding is fast. The boarder melees the hatch or plants a grenade through it.
- Halopedia: an EMP from a charged Plasma Pistol shot or Grenade Launcher round disables the Ghost's engines, which makes boarding much easier.

**Running people over**
- Halopedia's splatter guidance: do not boost until you are about one to two Scorpion lengths from the target. Boosting too early gives the target time to jump, boost sideways, stick you with a grenade, or board you.
- If the ram misses, switch to the plasma cannons or boost to a new target.
- Community: Ghosts are good splatter vehicles on enclosed floors, where there is little room for infantry to dodge.
- Halopedia: a Warthog ramming a Ghost head-on destroys it, the same way a Chopper ram does.

**AI tactics (Proposed)**
- Fast flank harassment. Run infantry down in the open.
- Plasma cannons for vehicles and far targets.
- Boost out of Scorpion and Wraith fire, after checking the escape route.
- Retreat when two or more enemy vehicles are close.

**Avoid**
- Scorpion cannon and Wraith mortar lines.
- Banshee air superiority.
- Narrow lanes where a Warthog can ram you head-on. A head-on Warthog hit destroys a Ghost.

---

### Banshee

- **Seats:** Pilot
- **Weapons:** Twin plasma cannons (main). Fuel rod cannon (secondary, usable in Halo 3 multiplayer).
- **Theft:** Boarding possible.

**Weak points and boarding**
- Halopedia: a charged Plasma Pistol shot or an M319 grenade launcher round disables a Banshee with an EMP, which makes it far easier to destroy or board.
- Halopedia: shooting the pilot's legs can kill the pilot without damaging the craft. The Banshee then becomes free to take.
- Halo 3 Banshees can have the anti-grav pods shot off and still fly. Verify.
- Boarding a Banshee: melee the hatch off, then plant a grenade, or shove a grenade through the hatch.

**Running people over**
- The Banshee's damage comes from plasma cannons and the fuel rod cannon. It is not a ramming vehicle.
- Halopedia: a direct fuel rod hit kills infantry instantly, and one fuel rod can clear a group of infantry.
- Halopedia: the Banshee's fuel rod cannon can flip Warthogs and Mongooses.

**AI tactics (Proposed)**
- Patrol the air above the objective.
- Attack flying vehicles first, then ground vehicles, then light infantry.
- Use the fuel rod on infantry clusters and on Warthogs or Mongooses to flip them.
- Swoop attacks: dive onto targets, then climb out.
- Can be stolen if a player gets within 4 m while the pilot is not engaged in air combat.

**Avoid**
- Rocket Launchers. Halopedia notes the M41 Rocket Launcher lost its lock-on in Halo 3, so Banshees are harder to hit with rockets. Verify.
- Scorpion cannon when grounded.
- Wraith mortar.
- Hornet head-on.

---

### Wraith

- **Seats:** Driver, gunner
- **Weapons:** Plasma mortar (main). Anti-personnel plasma (secondary, verify).
- **Theft:** Boarding possible.

**Weak points and boarding**
- Halopedia: boarding a Wraith in Halo 3 works like other vehicles. Melee or throw a grenade at the driver.
- Halopedia: in the campaign, a Brute that boards your Wraith traps you inside, and you cannot leave to escape. You can fire the main cannon, which damages the Wraith but kills the Brute.
- Halo 3 Wraiths can be disabled with an EMP. Verify.
- Community: a Wraith is near-perfect in the hands of a skilled player. A Warthog run can end its life.

**Running people over**
- Wraiths are slow and not used for ramming.

**AI tactics (Proposed)**
- Hold a long-range position and shell the approach to the objective.
- Relocate after every few shots.
- Do not advance into close-range combat.

**Avoid**
- Banshee, Hornet, Ghost flanks, and Warthog runs.

---

### Hornet

- **Seats:** Pilot plus two side passengers (community Halo 3 guide). Passengers use their own weapons.
- **Weapons:** Pilot fires a machine gun and two missiles. The Transport Hornet has no missiles and a slower machine gun (Halopedia).
- **Theft:** Boarding possible. Halopedia lists Hornets among the vehicles most often boarded.

**Weak points and boarding**
- A Hornet that hovers to let passengers shoot is a stationary target for a Banshee or Spartan Laser.
- EMP (Plasma Pistol overcharge or Grenade Launcher round) disables it in the air; it drops and is open to boarding.
- Halopedia (Avalanche CTF): the Hornet is grabbed almost instantly by a player with a passenger, so it is also the first thing the enemy will try to steal at spawn.

**Running people over**
- Not a ramming vehicle.

**Mount, kill, and take it**
- **Mount:** among the vehicles most often boarded (Halopedia). When it hovers low for its passengers to shoot, jump and board; the pilot is thrown out. EMP it to force it down.
- **Kill the crew:** the pilot and side passengers are all exposed. Battle Rifle, Carbine, and sniper headshots kill them without touching the airframe, which leaves the vehicle free to take.
- **Grenades and rockets:** a stuck plasma grenade on the fuselage destroys it; Spartan Laser and rockets kill it in one or two hits; the Missile Pod (Halo 3) locks on.

**AI tactics (Proposed)**
- Strafing runs against ground vehicles.
- Break off when a Banshee engages.

**Avoid**
- Banshee head-on, Wraith mortar, and Scorpion cannon.

---

### Brute Chopper

- **Seats:** One. The driver only (Halopedia: crew, one driver). There is no gunner seat.
- **Weapons:** Two forward-facing 35mm autocannons fired by the driver (Halopedia lists four 35mm heavy cannons on later models; in-game it fires as a paired forward cannon). Boost (left trigger) is the second weapon, because it turns the front wheel into a ram.
- **Theft:** Boarding possible. Halopedia lists the Brute Chopper among the vehicles most often boarded. The driver sits exposed at the rear, so a boarder approaches from behind or the side.

**Ramming is the Chopper's primary attack, not a side effect**
- Halopedia (Halo 3 page): the Chopper can destroy a UNSC Warthog with a head-on ram.
- Fandom (Jiralhanae gameplay): the Chopper's ram, assisted by boost, destroys most light vehicles, including other Choppers, in one hit.
- Giant Bomb: by boosting, it can destroy any vehicle except the Wraith and the Scorpion on impact.
- Halopedia (Look Both Ways achievement): the Chopper can splatter vehicles by crushing them, and it is one of the two best Splatter Spree vehicles alongside the Ghost because of its size and boost.
- Community Halo 3 guide: the big front wheel crushes small vehicles without much damage to the Chopper.
- Halopedia: it can splatter a Shade turret unharmed in Halo 3 and ODST.
- Neoseeker: the Chopper is unwieldy and best used in brief, cavalry-style charges through the enemy's ranks. Boosting into a jump clears bigger gaps than most vehicles.

**Running people over (AI procedure, Proposed)**
1. Pick a straight line. The Chopper turns slowly, so do not try to chase a weaving target. Choose infantry or vehicles that are committed to a direction, such as a flag carrier, a player sprinting between cover, or a Warthog on a road.
2. Boost late. Use the Ghost rule: hold boost until roughly one to two Scorpion lengths out so the target cannot sidestep or stick you.
3. Aim the wheel, not the cannons, at vehicles. A head-on boost ram kills a Warthog, Mongoose, Ghost, Hornet on the ground, Prowler, or another Chopper outright. Save the cannons for targets you cannot line up.
4. Never ram a Scorpion or Wraith. The ram does not kill them and the Chopper stops dead in front of their guns.
5. After the ram, keep rolling. Stopping next to the wreck invites boarding from behind.
6. Chain targets. Splatter Spree and Vehicular Manslaughter medals come fastest from a Chopper that stays at speed and strings rams together.

**Cannons (secondary)**
- Halopedia: the heavy guns rip through light vehicles, so bumper-to-bumper fights against a Chopper are not safe for a Warthog, Ghost, or Mongoose. Use the cannons on targets that are too agile to ram or on infantry at medium range.
- The cannons are forward-facing, so the Chopper has to point its nose at the target. It cannot shoot while turning away.

**Weak points and how to beat it**
- Halopedia: near impossible to flip, so grenades under it do little. Attack the driver instead.
- Halopedia: follow behind the Chopper and shoot the driver. It turns slowly and takes a long time to come around.
- The driver is exposed at the rear with no canopy. Sniper, Battle Rifle, and Carbine headshots from behind or the side kill the driver without touching the vehicle.
- EMP it (Plasma Pistol overcharge, Grenade Launcher round, Power Drain) to stop the ram and open it to boarding.
- A Scorpion or Wraith shot destroys it; it is tougher than a Ghost but not a tank (Fandom).
- Sidestep the ram. A boosting Chopper cannot correct its line, so a player who moves sideways late makes it overshoot, and the Chopper then has to make a slow turn to come back.

**AI tactics (Proposed)**
- Primary role: anti-vehicle ram and splatter. Patrol roads and lanes where enemy Warthogs, Mongooses, and Ghosts travel, and intercept them head-on with boost.
- Second role: cannon suppression on infantry when no ram line exists.
- Hold near the objective's main vehicle approach, nose pointed down the lane, and boost the moment an enemy vehicle commits to it.
- After a ram, boost out to open ground to reset the next charge rather than idling.
- Do not engage air at all. The cannons cannot track a Banshee or Hornet well.

**Avoid**
- Scorpion cannon lines and Wraith mortar zones; the ram does nothing to either.
- Banshee overhead, which can hit the exposed driver.
- Tight rooms and sharp corners, where the slow turn makes it a sitting target.
- Players with Plasma Pistols, Grenade Launchers, or Power Drains during a charge.
- Infantry standing beside a wall, because a missed ram ends with the Chopper stopped next to them.

---

### Brute Prowler (Forge only)

- **Seats:** Four. Driver, turret gunner, and two side riders. Fandom: the highest passenger count of any drivable Covenant vehicle in Halo 3. The driver only drives.
- **Weapons:** Turret plasma cannon fired by the gunner. Side riders fire their own weapons.
- **Theft:** Boarding possible. It is a hover vehicle like the Ghost, so Halopedia's note that all-direction movement makes boarding harder applies.
- **Availability:** Fandom: the Prowler does not appear on any Halo 3 map by default. It is placed through Forge or by replacing another vehicle in game settings. Campaign: The Ark and The Covenant.

**Running people over**
- Hover chassis with a wide front, so it splatters infantry at speed like a Warthog. It has no boost, so it cannot one-shot other vehicles the way a Chopper does.

**Mount, kill, and take it**
- **Mount:** boardable, but Halopedia warns it is harder than most because the hover chassis moves in every direction. Board it when it is stopped, reversing, or wedged on terrain. The driver is thrown out and the vehicle is yours.
- **Kill the crew:** the driver and gunner sit exposed; headshots remove them one at a time. Kill the gunner first.
- **Grenades and rockets:** community: explosives are the reliable answer. A stuck plasma grenade on the driver's seat or a rocket kills it. Frags under it do little because hover vehicles do not flip easily.
- **EMP:** stops it dead and makes boarding simple.

**AI tactics (Proposed)**
- Covenant-side Warthog. Use it as a four-seat carrier transport in Forge maps: driver, gunner covering the rear, flag or bomb carrier as a side rider, and one escort rider.
- Gunner suppresses infantry while the driver keeps moving.

**Avoid**
- Chopper head-on rams (the Prowler is a light vehicle and dies to a boosted Chopper), Scorpion, Wraith, Banshee.

---

### M313 Elephant (Sandtrap only)

- **Seats:** Driver in a rear cabin reached by the cargo ramp, plus multiple mounted turrets and open deck space for riders and a Mongoose.
- **Weapons:** Mounted machine-gun turrets manned by riders. The driver has no weapon.
- **Durability:** Halopedia: completely invincible and open-topped. It cannot be destroyed.
- **Theft:** Anyone can walk up the ramp and take the driver's seat once the driver is dead. Halopedia: kill the driver from behind, preferably from a Banshee, because a driver in third person will see a boarder walking in and counterattack.

**Running people over**
- Slow, but it crushes anything it rolls over and nothing can ram it. Do not plan around it as a splatter vehicle; plan around it as a moving wall.

**Mount, kill, and take it**
- **Mount:** it cannot be destroyed, so nothing you throw matters. Walk up the rear cargo ramp. The driver sits in the rear cabin and will see you in third person, so kill them from behind first, ideally from a Banshee or Hornet, then take the seat (Halopedia).
- **Grenades:** useful only for clearing riders off the deck and turrets, not for the vehicle.
- **EMP:** does not disable the Elephant in a useful way; verify.

**AI tactics (Proposed)**
- Mobile base. Drive it to the objective and park it so its ramp faces away from the enemy.
- Keep at least one rider on a turret at all times. Riders cover the deck against boarders.
- In Assault on Sandtrap, Halopedia's tactic is to move the Elephant next to the tower holding the bomb, defend it, and climb straight onto the Elephant with the bomb. The Elephant then drives the bomb toward the arm site.
- Park a Mongoose on the deck so the flag or bomb carrier has a fast exit.

**Avoid**
- Nothing destroys it, so avoid lists are about the crew: keep it out of Scorpion and Wraith lanes that can clear the deck, and watch the rear ramp for boarders.

---

### Theft rules (Halo 3)

- **Boarding:** Players hold the action button near an AI vehicle to board it. Scorpions and Wraiths use the jump-on-top method.
- **Cannot be boarded:** Mongoose. Melee the driver off instead.
- **Elephant:** not boarded in the normal sense. Walk up the ramp and kill or replace the driver.
- **EMP:** A disabled vehicle is open to boarding. Plasma Pistol overcharge or Grenade Launcher round disables it.
- **Steal radius (Proposed):** 3 m for ground vehicles, 4 m for Banshees and Hornets, 6 m for the Elephant ramp.
- **Trigger (Proposed):** The AI driver is not engaged in combat.
- **Engaged driver:** does not eject. The player has to kill the driver or the gunner first.

---

### Open items

- Confirm which Halo 3 maps spawn the Chopper and Hornet by default in MCC playlists versus Forge-only placements.
- Confirm Prowler placement options in Halo 3 custom game settings.
- Confirm Wraith's anti-personnel secondary and EMP behavior in Halo 3.
- Confirm Banshee anti-grav pod behavior in Halo 3.
- Confirm Rocket Launcher lock-on behavior in Halo 3.

---

### Objective Game Types (Halo 3)

**Scope and status**
- **Confirmed for Halo 3 (StrategyWiki and Halopedia):**
  - **CTF:** Multi Flag, One Flag, and Tank Flag (carrier is very tough but very slow, per Halopedia). The Classic CTF, Warlock Classic CTF, Neutral Flag CTF, and Gungoose CTF variants belong to Halo 2 Anniversary and are listed there.
  - **Oddball:** Oddball (FFA), Team Oddball, and Ninjaball (fast, fragile carrier).
  - **Assault:** Assault, Neutral Bomb, One Bomb, and Attrition Bomb.
  - **King of the Hill:** Crazy King (FFA points), Team King (150 points, uncontested), and Moshpit (single unmoving hill where everyone inside is tougher).
- **Halo 3 specifics:** Flag carriers in Halo 3 can be adjusted in traits, so a flag can kill instantly or do much less damage (Halopedia).
- **Avalanche:** Hornets and Ghosts spawn near the teleporter. Halopedia notes the Hornet is taken almost instantly by a player with a passenger.
- **Standoff:** Halopedia and Fandom both describe door, window, and escape-route mechanics in Standoff.

#### Capture the Flag (Halo 3)

**Vehicle assignment**
- **H3-CTF-01 Carrier vehicle:** IF a Warthog or Ghost is available within 15 m of your base, THEN the carrier boards it. Community: a Warthog allows a speedy getaway.
- **H3-CTF-02 Cram rule:** IF a Warthog is carrying the flag, THEN keep teammates aboard. Community (Halo 3 strategy guides): a Warthog transport can get everyone killed if it drives into a crowd, so use an escort to clear the path.
- **H3-CTF-03 Warthog havoc:** IF the Warthog carrier is blocked at the enemy base, THEN the second Warthog drives into the base to draw fire. The carrier escapes on foot or into an allied Mongoose (Standoff tactic).
- **H3-CTF-04 Hornet steal (Avalanche):** IF the enemy's Hornet spawns, THEN a player with a passenger takes it and meets the carrier at the teleporter.

**Carrier logic**
- **H3-CTF-05 Outskirts route (Standoff):** IF the map has a center route and an outer route, THEN take the outer route. Halopedia: the enemy expects the carrier to cut through the middle.
- **H3-CTF-06 Warthog middle warning:** Community: do not cut through the middle with a Warthog, because it can get stuck or be boarded.
- **H3-CTF-07 Bubble Shield approach:** Halopedia: a Bubble Shield thrown down before grabbing the enemy flag buys time for a Mongoose or Warthog to arrive.
- **H3-CTF-08 Back door:** IF the base has a back entrance, THEN enter from the back. Fewer defenders are near the flag (Standoff).

**Pursuit logic**
- **H3-PUR-01 Ghost chaser:** IF an enemy carrier is in a Warthog, THEN a Ghost intercepts with plasma cannon fire and a boost, staying out of the Warthog's head-on ram path. Halopedia says a Warthog head-on ram destroys a Ghost, so the Ghost should not meet the Warthog head-on.
- **H3-PUR-02 Splatter spacing:** Halopedia: do not boost until about one to two Scorpion lengths from the target. Early boosts let the carrier jump or boost aside.
- **H3-PUR-03 Chopper pursuit:** IF the enemy carrier has a Brute Chopper, THEN do not engage bumper to bumper. Follow behind and shoot the driver (Halopedia).
- **H3-PUR-04 Chopper as interceptor:** IF your team has a Chopper and the enemy carrier is in a Warthog, Mongoose, Ghost, or Prowler, THEN the Chopper is the best chaser on the map. Line up on the carrier's road, boost late, and ram head-on; the collision destroys the carrier vehicle outright (Halopedia, Halo 3 collision damage). The flag or bomb drops where the wreck lands, so a second vehicle follows to collect it.
- **H3-PUR-05 Chopper cannot carry:** A Chopper has one seat, so it never transports the carrier. It escorts or intercepts only.
- **H3-PUR-06 Chopper vs tank carrier (Tank Flag):** IF the mode is Tank Flag and the carrier is slow and tough, THEN the Chopper runs the carrier down with repeated rams and cannon bursts while the Warthog gunner finishes.

**Defense logic**
- **H3-DEF-01 Park over the flag:** IF no carrier is active, THEN park a Warthog or Mongoose over the flag.
- **H3-DEF-02 Shade or Scorpion anchor:** IF a Scorpion is parked near the flag, THEN its gunner covers the most likely approach.
- **H3-DEF-03 Chopper road block:** IF the enemy's main vehicle approach to your flag is a road or lane, THEN station the Chopper facing down it. Any enemy Warthog or Mongoose that commits to the lane is boost-rammed before it reaches the flag.
- **H3-DEF-04 Elephant wall (Sandtrap):** IF the mode is CTF on Sandtrap, THEN park the Elephant across the flag stand's open side and keep two riders on turrets. The Elephant cannot be destroyed, so it is a permanent wall.
- **H3-DEF-05 Prowler as mobile flag guard (Forge):** IF a Prowler is placed, THEN its four seats make it the best flag-guard vehicle: two riders stay on foot by the flag while the gunner and driver circle.

#### Oddball and Ninjaball (Halo 3)

- **H3-ODD-01 Carrier escort:** IF your team holds the ball in Team Oddball, THEN a Warthog or Ghost escorts the carrier. Keep teammates close.
- **H3-ODD-02 Ninjaball:** IF the mode is Ninjaball, THEN the carrier is fast and vulnerable. Use a Ghost for the carrier and keep the second vehicle on the enemy approach.
- **H3-ODD-03 Carrier kill medal:** Halopedia notes the Oddball Kill medal is earned for killing a player holding the ball. Vehicles that can splatter or shoot the carrier earn the most value from this.
- **H3-ODD-04 Carrier melee:** Ball carriers cannot fire weapons (Halopedia). A vehicle chasing the carrier is safer than an infantry chaser.

#### Assault (Halo 3)

**Bomb rules (Halopedia)**
- The bomb carrier can ride any vehicle that carries passengers, but not in the gunner seat.
- The carrier can stand on top of a tank and ride it.
- When the bomb is hidden, it disappears from view. An enemy aiming at a vehicle with the bomb sees a glowing red bomb icon.
- A melee from the bomb is an instant kill.

**Logic**
- **H3-ASS-01 Bomb carrier vehicle:** IF a Warthog is near the bomb, THEN the carrier rides as passenger, not as gunner.
- **H3-ASS-02 Tank rider:** IF a Scorpion is parked nearby and the carrier needs to move under fire, THEN the carrier can stand on the Scorpion and ride it. Use this only when the tank is not under attack.
- **H3-ASS-03 Hidden-bomb rule (Halopedia):** Do not place the bomb down while hiding. The bomb respawns, and the other team will most likely get it.
- **H3-ASS-04 Door escape:** IF the base has a switch-operated door, THEN open it for the carrier to run out to a waiting Warthog.
- **H3-ASS-05 Elephant ambush (Sandtrap):** Halopedia: move the enemy Elephant next to the tower holding the bomb and defend it, then hop onto the Elephant.
- **H3-ASS-06 Defender count:** Halopedia: the more players on the bomb, the faster it is disarmed. Defenders should stack the arm circle.
- **H3-ASS-07 Active camo:** Halopedia: on One Bomb maps, Active Camo is usually somewhere on the map. A carrier with it has a big advantage.
- **H3-ASS-08 Elephant bomb run (Sandtrap):** IF the bomb carrier is on the Elephant deck, THEN the Elephant drives toward the enemy arm site with turrets manned. It cannot be destroyed, so the only way to stop it is to kill the driver from behind or kill the carrier on the deck. Keep the carrier low in the cabin end of the deck, away from the open rear.
- **H3-ASS-09 Chopper counter-Elephant:** IF the enemy Elephant is carrying the bomb, THEN do not ram it. Send a Banshee or a Chopper around the rear ramp to shoot the driver and the carrier on the deck.

#### King of the Hill (Halo 3)

**Logic**
- **H3-KOTH-01 One scorer:** One player stays on the hill and scores while the rest defend approaches (Halopedia).
- **H3-KOTH-02 Vehicle anchor:** IF the hill is uncontested, THEN park a Scorpion or Warthog gunner outside the ring to cover approaches.
- **H3-KOTH-03 Moshpit (single hill):** Everyone inside is tougher. Hold the hill with a vehicle at each entrance.
- **H3-KOTH-04 Crazy King moving hill:** IF the hill moves, THEN the first Ghost or Warthog to the new location claims it.
- **H3-KOTH-05 Team King:** The hill must be uncontested to score. Do not enter the ring with enemies inside it.
- **H3-KOTH-06 Chopper hill sweep:** IF enemies are inside the hill on open ground, THEN the Chopper boost-rams straight through the ring and out the other side, then turns for a second pass. It clears the hill without the Chopper stopping inside it, which keeps the ring contestable by your own infantry.

#### Headroom
- Confirm which Halo 3 maps spawn the Chopper and Hornet by default in MCC matchmaking versus Forge-only placements.
- Verify which Halo 3 CTF variant allows vehicle theft (Gungoose CTF entry).

---

## Halo 3: ODST (MCC)

**Status key**
- **Yes:** Confirmed drivable in this game from retrieved sources.
- **Verify:** Not confirmed. Test in-game.
- **Community:** Reported by players or wiki editors. Not tested by us.
- **Proposed:** Design target for the mod, not native MCC AI.

---

### Critical ODST facts for your mod

- **ODST boarding is mostly the same as Halo 3.** Halopedia says the distance from which you can board seems larger in ODST.
- **Wraiths explode when the driver dies or exits.** Halopedia says the Wraith is rigged to explode in ODST. Halopedia links a method called "Drive an AA Wraith" to get around this. Verify the details in-game before relying on it.
- **EMP works here too.** Plasma Pistol overcharge and Grenade Launcher rounds disable vehicles, as in Halo 3.
- **Mongoose cannot be boarded.** Melee the driver off as you pass.
- **Hornet is in Firefight.** Halopedia says the Hornet was added to ODST Firefight when ODST came to PC, and it can be used on the map Lost Platoon.
- **Firefight is the main splatter environment.** Community guides on the Firefight achievement "Last Exit" describe hijacking Ghosts for Splatter Sprees.

---

### Roster

| Vehicle | Status |
|---|---|
| M12 Warthog (chaingun) | Yes |
| M12G1 Gauss Warthog | Yes |
| M831 Troop Transport Warthog ("Transport Hog") | Yes |
| M274 Mongoose | Yes |
| M808 Scorpion | Yes |
| Ghost | Yes |
| Banshee | Yes |
| Wraith | Yes (rigged to explode on driver death or exit) |
| Hornet | Yes (Firefight, Lost Platoon) |
| Brute Chopper | Yes (campaign and Firefight; Halopedia confirms Chopper use in Halo 3 and ODST) |

**Not in ODST:** Spectre (Halo 2 only). Prowler appears in the campaign only; verify Firefight placement.

**Not drivable:** Pelican, Phantom.

---

### M12 Warthog (Chaingun)

- **Seats:** Driver, gunner, passengers
- **Weapons:** Chaingun turret
- **Theft:** Boarding possible

**Weak points and boarding**
- Boarding the driver: turn your view 90 degrees to the right to face the boarder and melee them. When boarding yourself, turn 90 degrees to the left to melee the stunned driver. Community: this carries over from Halo 3.
- Kill the gunner first. The gunner can shoot anyone trying to board.
- Halopedia: ODSTs and Marines can flip Warthogs by hand. A frag grenade flips a Warthog and knocks the driver and passenger out.
- Community: sticky grenades do heavy damage, and a couple of direct grenade hits or one rocket destroys a Warthog.

**Running people over and ramming**
- Halopedia: a Warthog ram at full speed is the most reliable way to kill light vehicles. A Warthog destroys an enemy Ghost head-on, as long as it is not going uphill.
- Halopedia: the Warthog is the second-best ramming vehicle against a Shade turret.
- Keep passengers aboard. Passengers falling out reduce the vehicle's offensive value.

**AI tactics (Proposed)**
- Flank routes around the objective.
- Escort the Transport Hog and suppress threats near it.
- Ram light infantry when speed is above a threshold.
- Gunner suppresses. Driver does not stop in the open.
- Retreat below half health.

**Avoid**
- Banshee overhead.
- Wraith mortar zones.
- Scorpion cannon lanes.
- Brute Choppers. Halopedia notes they rip through light vehicles.

---

### M12G1 Gauss Warthog

- **Seats:** Driver, gunner
- **Weapons:** Gauss cannon
- **Theft:** Boarding possible

**Weak points and boarding**
- Same as the chaingun Warthog.
- Halopedia: a Gauss turret is lethal, but the gunner must change positions often or be overwhelmed.

**Mount, kill, and take it**
- **Mount:** kill the gunner first (if it has one), then board the driver. In Halo 3 and ODST the thrown driver is heavily damaged by the ejection melee; turn 90 degrees left after boarding to melee them again.
- **Grenades:** a frag under the chassis flips it and throws everyone out; a stuck plasma grenade does heavy damage or destroys it; two direct grenade hits or one rocket destroys it (Halo 3 onward).
- **Melee:** a Spartan beside a stopped Warthog can melee the gunner off the turret or the passenger out of the seat.
- **Gauss gunner:** the gunner is fully exposed and must stop moving to aim. Snipe the gunner while the hog is parked on overwatch; the Gauss cannon has no close-range answer.
- **EMP:** stops it so a boarder can walk up to it.

**AI tactics (Proposed)**
- Long-range overwatch on choke points.
- Reposition after each few shots.
- Do not chase fleeing targets past the objective.

**Avoid**
- Banshee and close-range Scorpion engagements.

---

### M831 Troop Transport Warthog ("Transport Hog")

- **Seats:** Driver, passenger bed (troops)
- **Weapons:** None
- **Theft:** Boarding possible. Stealable when the driver is idle or fleeing (Proposed rule below)

**Weak points and boarding**
- Same as the Warthog. Passengers can be thrown when the vehicle flips.

**Running people over**
- Do not ram. A flipped Transport Hog loses its passengers.

**Mount, kill, and take it**
- **Mount:** kill the gunner first (if it has one), then board the driver. In Halo 3 and ODST the thrown driver is heavily damaged by the ejection melee; turn 90 degrees left after boarding to melee them again.
- **Grenades:** a frag under the chassis flips it and throws everyone out; a stuck plasma grenade does heavy damage or destroys it; two direct grenade hits or one rocket destroys it (Halo 3 onward).
- **Melee:** a Spartan beside a stopped Warthog can melee the gunner off the turret or the passenger out of the seat.
- **Transport Hog:** no gunner, so a single boarder takes it uncontested. The riders on the bed are the only defense; kill them with a grenade on the bed before boarding.
- **EMP:** stops it so a boarder can walk up to it.

**AI tactics (Proposed)**
- Drive players to and from objectives or points of interest.
- Stop at a safe distance and wait for passengers.
- Retreat toward the nearest friendly zone when attacked.
- Do not cross open ground without an escort Warthog or Mongoose.

**Avoid**
- Ghost, Wraith, Scorpion, Banshee lanes, and hostile infantry clusters.

---

### M274 Mongoose

- **Seats:** Driver, passenger
- **Weapons:** None mounted. Passenger weapon only.
- **Theft:** Cannot be boarded. Melee the driver off instead.

**Weak points**
- Halopedia: a player can melee the driver off as they pass, or take the passenger seat and kill the driver with a few melee attacks or shots to the back of the head.
- Halopedia: an EMP makes the Mongoose crouch and deactivate, which makes it easier to take the driver out.
- Prima: the Mongoose wobbles on uneven terrain. Use the e-brake to slide around obstacles.

**Running people over**
- Prima: the Mongoose is much lighter than the Warthog. To run over a Brute, hit it directly at top speed.
- Community: ramming with a Mongoose is risky. Glancing off a rock can cost you shields and alert the enemy.

**Mount, kill, and take it**
- **Mount:** cannot be boarded. Melee the driver off as it passes, or jump into the passenger seat and melee or headshot the driver from behind (Halopedia).
- **Grenades:** any grenade near it flips it; a stuck grenade kills both riders. It has no armor, so rifle fire at the riders is enough.
- **EMP:** it crouches and stops, which makes the riders sitting targets.

**AI tactics (Proposed)**
- Fast flanking and objective runs.
- Passenger dismounts to capture or defend objectives.
- Do not stay in one place for more than a few seconds.

**Avoid**
- Mounted-gun vehicles, Banshees, Wraith mortars, and Hornets.

---

### M808 Scorpion

- **Seats:** Driver, gunner (cannon), secondary machine gunner (ally-manned)
- **Weapons:** 90mm cannon (main), coaxial chaingun or secondary machine gun
- **Theft:** Boarding possible. Boarders jump onto the tank.

**Weak points and boarding**
- Halopedia: the boarder jumps onto the tank and can melee the hatch to expose and kill the driver, or plant a grenade to kill all occupants.
- Kill the gunner first. Halopedia notes the gunner can fire on boarders.
- Halo 3 method: a grenade can be shoved through the hatch, trapping the occupant inside.
- Prima: the main threats to a Scorpion driver are Wraiths, Shade turrets, Banshees, Ghosts in groups, and Brutes with fuel rod cannons.
- EMP: a charged Plasma Pistol shot disables the engines and leaves the tank open to boarding.

**Running people over**
- Too heavy and slow to ram. It crushes infantry it drives over.

**AI tactics (Proposed)**
- Hold a fixed position covering the objective.
- Secondary chaingun on infantry, main cannon for vehicles.
- Back toward cover when a Banshee approaches.
- Keep the second crew member manning the secondary gun.

**Avoid**
- Banshee overhead, Wraith mortar, and head-on approaches toward an enemy Scorpion.

---

### Ghost

- **Seats:** Driver
- **Weapons:** Twin plasma cannons (main). Boost is a movement ability.
- **Theft:** Boarding possible

**Weak points and boarding**
- Halopedia: dodge a Ghost so it boosts into a wall. While it backs out, board it from behind.
- Halopedia: an EMP disables a Ghost's engines, which makes boarding easier.

**Running people over**
- Halopedia's splatter guidance: do not boost until about one to two Scorpion lengths from the target. Boosting from farther away gives the target time to jump, boost sideways, stick you with a grenade, or board you.
- Community Firefight tips from the "Last Exit" achievement guide: when facing Chieftains with Gravity Hammers, splatter them before their invincibility activates. When facing Chieftains with Fuel Rod Guns, approach slowly while dodging left and right, then boost to splatter once close.
- Halopedia: Phantoms drop Ghosts on Mombasa Streets in Firefight. Ghosts there are a good way to start a splatter run.
- Halopedia: a Warthog ram destroys a Ghost head-on.

**Mount, kill, and take it**
- **Mount:** dodge it so it boosts into a wall, then board from behind while it reverses (Halopedia). The driver is thrown out; melee them before they stand.
- **Grenades:** a stuck plasma grenade on the driver's back kills them; a frag under the nose can flip it (it flips less easily than a Warthog).
- **EMP:** stops the boost mid-charge and leaves it open to boarding.

**AI tactics (Proposed)**
- Fast flank harassment. Run infantry down in the open.
- Plasma cannons for vehicles and far targets.
- Boost out of Scorpion and Wraith fire, after checking the escape route.
- Retreat when two or more enemy vehicles are close.

**Avoid**
- Scorpion cannon and Wraith mortar lines.
- Banshee air superiority.
- Narrow lanes where a Warthog can ram you head-on.

---

### Banshee

- **Seats:** Pilot
- **Weapons:** Twin plasma cannons (main). Fuel rod cannon (secondary).
- **Theft:** Boarding possible

**Weak points and boarding**
- Halopedia: a charged Plasma Pistol shot or M319 grenade launcher round disables a Banshee with an EMP, which makes it easier to destroy or board.
- Halopedia: shooting the pilot's legs can kill the pilot without damaging the craft.
- Halopedia: in ODST, a Sniper Rifle can shoot the pilot through the small gap between the Banshee's body and canopy without damaging the craft.
- Boarding: melee the hatch off, then plant a grenade, or shove a grenade through the hatch.

**Running people over**
- Not a ramming vehicle. The damage comes from plasma cannons and the fuel rod cannon.
- Halopedia: a direct fuel rod hit kills infantry instantly, and one fuel rod can clear a group.
- Halopedia: the fuel rod can flip Warthogs and Mongooses.

**AI tactics (Proposed)**
- Patrol the air above the objective.
- Attack flying vehicles first, then ground vehicles, then light infantry.
- Fuel rod on infantry clusters and on Warthogs or Mongooses.
- Swoop attacks: dive onto targets, then climb out.
- Can be stolen if a player gets within 4 m while the pilot is not engaged in air combat.

**Avoid**
- Rocket Launchers. Halopedia notes the M41 lost lock-on in Halo 3 and ODST, so a Banshee is harder to hit with rockets.
- Scorpion cannon when grounded.
- Wraith mortar.
- Hornet head-on.

---

### Wraith

- **Seats:** Driver, gunner
- **Weapons:** Plasma mortar (main). Anti-personnel plasma (secondary, verify).
- **Theft:** Boarding possible, with the explosion rule below

**Weak points and boarding**
- Halopedia: Wraiths can be boarded as in Halo 3. The player can melee or throw a grenade at the driver.
- **Explosion rule:** Halopedia says the Wraith is rigged to explode when the driver dies or exits. A player who steals it must expect it to blow up when they kill the driver.
- Halopedia: there is a method to get around this and capture a Wraith. Verify in-game.
- Halopedia: in the campaign, a Brute that boards your Wraith traps you inside. Fire the main cannon to kill the Brute.

**Running people over**
- Not a ramming vehicle.

**AI tactics (Proposed)**
- Hold a long-range position and shell the approach to the objective.
- Relocate after every few shots.
- Do not advance into close-range combat.

**Avoid**
- Banshee, Hornet, Ghost flanks, and Warthog runs.

---

### Hornet (Firefight, Lost Platoon)

- **Seats:** Pilot, gunner
- **Weapons:** Chaingun (main). Missiles (secondary).
- **Theft:** Verify

**Weak points**
- Halopedia: the Hornet is usable on Lost Platoon in Firefight.

**Mount, kill, and take it**
- **Mount:** among the vehicles most often boarded (Halopedia). When it hovers low for its passengers to shoot, jump and board; the pilot is thrown out. EMP it to force it down.
- **Kill the crew:** the pilot and side passengers are all exposed. Battle Rifle, Carbine, and sniper headshots kill them without touching the airframe, which leaves the vehicle free to take.
- **Grenades and rockets:** a stuck plasma grenade on the fuselage destroys it; Spartan Laser and rockets kill it in one or two hits; the Missile Pod (Halo 3) locks on.

**AI tactics (Proposed)**
- Strafing runs against ground vehicles.
- Break off when a Banshee engages.

**Avoid**
- Banshee head-on, Wraith mortar, and Scorpion cannon.

---

### Brute Chopper

- **Seats:** One. Driver only, no gunner.
- **Weapons:** Two forward-facing driver-fired 35mm autocannons. Boost turns the front wheel into a ram.
- **Theft:** Boarding possible from the rear or side, where the driver sits exposed.

**Ramming is the primary attack**
- Everything in the Halo 3 Chopper profile applies in ODST: a boosted head-on ram destroys any vehicle except the Wraith and Scorpion, it crushes small vehicles without much self-damage, it splatters Shade turrets unharmed, and it is one of the two best Splatter Spree vehicles with the Ghost.
- Firefight: Brute packs arrive with Choppers. A hijacked Chopper is the most reliable splatter tool against Grunt and Jackal waves because it cannot be flipped and shrugs off small arms.
- Chieftains: use the same rules as the Ghost. Splatter Hammer Chieftains before invincibility triggers; approach Fuel Rod Chieftains while weaving, then boost at the end.

**AI procedure (Proposed)**
1. Pick a straight lane with committed targets.
2. Boost late, about one to two Scorpion lengths out.
3. Use the wheel on vehicles, the cannons on targets you cannot line up.
4. Never ram a Wraith or Scorpion.
5. Keep rolling after the hit; stopping invites boarding from behind.

**Weak points**
- Halopedia: near impossible to flip. Attack the driver, who is exposed at the rear. Follow behind and shoot; it turns slowly.
- EMP stops the charge and opens it to boarding.
- Boarding: approach from behind or the side where the driver sits exposed, board, and the driver is thrown out; melee them before they stand. A stuck plasma grenade on the driver's seat kills the driver and usually the vehicle. Frags under it do nothing useful because it will not flip.
- Wraith mortar and Scorpion cannon destroy it.

**Avoid**
- Wraith and Scorpion lanes, Banshees overhead, tight corners, and players holding Plasma Pistols during a charge.

---

### Theft rules (ODST)

- **Boarding:** Players hold the action button near an AI vehicle to board it.
- **Cannot be boarded:** Mongoose.
- **EMP:** A disabled vehicle is open to boarding.
- **Wraith explosion:** The Wraith explodes when the driver dies or exits.
- **Steal radius (Proposed):** 3 m for ground vehicles, 4 m for Banshees.
- **Trigger (Proposed):** The AI driver is not engaged in combat.
- **Engaged driver:** does not eject.

---

### Open items

- Confirm which vehicles are drivable in ODST multiplayer versus Firefight.
- Confirm the "Drive an AA Wraith" method and whether it works in the MCC version.
- Confirm Prowler placement in Firefight maps.
- Confirm Wraith anti-personnel secondary.

---

### Objective and Firefight Objective Tactics (ODST)

**Scope and status**
- **Verify which objective modes ODST has in MCC multiplayer.** The sources I found describe Firefight as the main ODST mode. Most objective logic in this file reuses Halo 3 rules, which should apply where the mode exists.
- **Firefight vehicle notes (Halopedia and community):**
  - Hornet is usable on Lost Platoon in Firefight.
  - Phantoms drop a Ghost on Mombasa Streets.
  - Community guides for "Last Exit" describe hijacking a Ghost for Splatter Sprees.
- **Wraith explosion rule:** The Wraith explodes when the driver dies or exits. Do not give objective logic that assumes a captured Wraith survives the driver's death.

#### Capture the Flag and Assault (if available in your ODST build)
Use the Halo 3 rules (see the Halo 3 file). Two ODST-specific changes to apply:
- **ODST-OBJ-01 Wraith carrier:** Do not assign a Wraith as a flag carrier vehicle. If the driver dies, it explodes with the carrier inside.
- **ODST-OBJ-02 Boarding distance:** Halopedia says the boarding distance seems larger in ODST. Escorts should keep 3 to 5 m more spacing around carriers if enemies can board.

#### Firefight objective logic (Proposed)
- **ODST-FF-01 Ghost run:** IF a Ghost spawns on Mombasa Streets (Phantom drop), THEN the first player to it runs enemies down on the route to the next objective.
- **ODST-FF-02 Chieftain with Gravity Hammer:** Community: splatter the Chieftain before its invincibility activates. Do not wait for the animation.
- **ODST-FF-03 Chieftain with Fuel Rod Gun:** Community: approach slowly, dodging left and right, then boost to splatter once close.
- **ODST-FF-04 Splatter spree chain:** Community: a hijacked Ghost can earn Splatter Sprees and Vehicular Manslaughter quickly. Keep the Ghost alive by avoiding walls at full speed.
- **ODST-FF-05 Lost Platoon Hornet:** Use the Hornet to transport a squad between Firefight zones. Keep it away from Banshees.
- **ODST-FF-06 Hijacked Chopper lane control:** IF a Chopper has been hijacked, THEN assign it to the widest open lane on the Firefight map and let it boost-ram waves as they spawn in. Pull it back to cover whenever a Wraith is dropped.

#### Oddball and King of the Hill (if available)
- **ODST-OBJ-03 Hill and ball:** Use the Halo 3 KOTH and Oddball rules (see the Halo 3 file).

#### Headroom
- Verify the ODST multiplayer game type list in MCC.
- Verify the "Drive an AA Wraith" method before using it for objectives.

---

## Halo: Reach (MCC)

**Status key**
- **Yes:** Confirmed drivable in this game from retrieved sources.
- **Verify:** Not confirmed. Test in-game.
- **Community:** Reported by players or wiki editors. Not tested by us.
- **Proposed:** Design target for the mod, not native MCC AI.

---

### Critical Reach facts for your mod

- **Armor Lock stops splatters.** Community reports say a Banshee or Ghost that splatters a target with Armor Lock active is killed in the process, and the vehicle is destroyed. Build this into AI so vehicles do not attack Armor Lock targets with splatter runs.
- **Boarding changes you into the seat.** Halopedia: when boarding a Warthog in Reach, the boarder takes the place of the driver, passenger, or gunner, which makes it easier to take control.
- **Mongoose can be boarded.** Boarding a Mongoose kicks off both the driver and passenger.
- **Custom games can make vehicles invincible.** Community: a Reach custom game setting makes vehicles invincible, which is useful for testing AI.
- **Civilian vehicles are campaign-only** and do not have weapons. They are not in the AI roster.

---

### Roster

| Vehicle | Status |
|---|---|
| M12 Warthog (chaingun) | Yes |
| M12G1 Gauss Warthog | Yes |
| M12R Rocket Warthog (anti-air) | Yes |
| M831 Troop Transport Warthog ("Transport Hog") | Yes |
| M274 Mongoose | Yes |
| M808 Scorpion | Yes |
| Ghost | Yes |
| Banshee | Yes |
| Wraith | Yes |
| Type-48 Revenant | Yes |
| UH-144 Falcon | Yes (standard and nose-gun variants are in MP. Halopedia says the Falcon in Reach MP lacks the chin autocannon the pilot normally uses. Transport Falcon appears on Forge maps.) |
| D77-TC Pelican | Not drivable in stock Reach. Community reports say the Pelican and Phantom were added to the MCC Reach Forge palette; verify in-game |
| FSS-1000 Sabre (MCC Forge only) | Yes, Forge (Forge World, Tempest) |
| Morsam-pattern Seraph (MCC Forge only) | Yes, Forge (Forge World, Tempest) |
| UH-144 Falcon Transport variant (MCC Forge) | Yes, Forge |
| UH-144 Falcon grenade-launcher variant (MCC Forge) | Yes, Forge |
| Forklift (MCC Forge) | Yes, Forge |
| Troop Warthog (MCC Forge) | Yes, Forge (likely the M831; verify) |
| Cart, Spade, HC1500 (civilian, MCC Forge) | Campaign drivable. Forge drivability: Verify |

**Not in Reach:** Hornet, Brute Chopper, Brute Prowler, Spectre. Fandom: the Prowler, Chopper, and Hornet did not return in Reach or Halo 4 as drivable vehicles. The Falcon fills the Hornet role.

**Not drivable in stock multiplayer:** Phantom.

**Note on Forge vs stock multiplayer:** The Sabre and Seraph are not in Reach's standard multiplayer playlists, per Halopedia. They appear in MCC's Reach Forge palette on Forge World and Tempest, under the category "Vehicles (MCC)". MCC's August 2022 update notes say players with Elite as their preferred species can enter Sabres in multiplayer. Verify how Sabres spawn in custom games before relying on them in a playlist.

**Not official:** Steam Workshop mods such as "Recon Sabre," "Rocket Hog," "Ultra" variants, and community Seraph flight mods are not part of MCC. Do not include them in the official roster.

---

### M12 Warthog (Chaingun)

- **Seats:** Driver, gunner, passengers
- **Weapons:** Chaingun turret
- **Theft:** Boarding possible. The boarder takes the seat.

**Weak points and boarding**
- Halopedia: in Reach, when boarding a Warthog, the boarder takes the place of the driver, passenger, or gunner.
- Kill the gunner before boarding. The gunner can fire on boarders.
- Community: a Warthog that is not moving is easier to hit with rockets, Spartan Lasers, and Banshee bombs.

**Running people over and ramming**
- Community: a Warthog ram at speed kills light infantry and can flip light vehicles.
- Community: Warthog runs can end a Wraith's life.
- Be careful who you splatter. Armor Lock targets can kill the attacker.

**Mount, kill, and take it**
- **Mount:** kill the gunner first (if it has one), then board the driver. In Reach the boarder takes the seat they board.
- **Grenades:** a frag under the chassis flips it and throws everyone out; a stuck plasma grenade does heavy damage or destroys it; two direct grenade hits or one rocket destroys it (Halo 3 onward).
- **Melee:** a Spartan beside a stopped Warthog can melee the gunner off the turret or the passenger out of the seat.
- **EMP:** stops it so a boarder can walk up to it.

**AI tactics (Proposed)**
- Flank routes around the objective.
- Escort the Transport Hog and suppress threats near it.
- Ram light infantry above a speed threshold. Do not ram Armor Lock targets.
- Gunner suppresses. Driver does not stop in the open.
- Retreat below half health.

**Avoid**
- Banshees overhead. Community: a Banshee's fuel rod can flip a Warthog.
- Revenant, which is resistant to small arms but dangerous at range.
- Scorpion cannon lanes.

---

### M12G1 Gauss Warthog

- **Seats:** Driver, gunner
- **Weapons:** Gauss cannon
- **Theft:** Boarding possible

**Weak points and boarding**
- Same as the chaingun Warthog.
- Community: the Gauss turret is lethal, but change positions often or the gunner will be overwhelmed.

**Mount, kill, and take it**
- **Mount:** kill the gunner first (if it has one), then board the driver. In Reach the boarder takes the seat they board.
- **Grenades:** a frag under the chassis flips it and throws everyone out; a stuck plasma grenade does heavy damage or destroys it; two direct grenade hits or one rocket destroys it (Halo 3 onward).
- **Melee:** a Spartan beside a stopped Warthog can melee the gunner off the turret or the passenger out of the seat.
- **Gauss gunner:** the gunner is fully exposed and must stop moving to aim. Snipe the gunner while the hog is parked on overwatch; the Gauss cannon has no close-range answer.
- **EMP:** stops it so a boarder can walk up to it.

**AI tactics (Proposed)**
- Long-range overwatch on choke points.
- Reposition after each few shots.

**Avoid**
- Banshees and close-range Scorpion engagements.

---

### M12R Rocket Warthog (Anti-Air)

- **Seats:** Driver, gunner
- **Weapons:** Anti-air rockets (main)
- **Theft:** Boarding possible

**Weak points and boarding**
- Same as the Warthog. The gunner is the target before boarding.
- Community: the rocket launcher can lock onto Banshees.

**Running people over**
- Not a ramming vehicle. It is built for air targets.

**Mount, kill, and take it**
- **Mount:** kill the gunner first (if it has one), then board the driver. In Reach the boarder takes the seat they board.
- **Grenades:** a frag under the chassis flips it and throws everyone out; a stuck plasma grenade does heavy damage or destroys it; two direct grenade hits or one rocket destroys it (Halo 3 onward).
- **Melee:** a Spartan beside a stopped Warthog can melee the gunner off the turret or the passenger out of the seat.
- **Rocket hog gunner:** the rockets are slow to track ground targets at close range, so rush it on foot or in a Ghost and board.
- **EMP:** stops it so a boarder can walk up to it.

**AI tactics (Proposed)**
- Track aircraft over objectives.
- Hold fire on ground targets unless a vehicle blocks the objective.
- Stay close to a support vehicle.

**Avoid**
- Ground infantry and Scorpion cannon.

---

### M831 Troop Transport Warthog ("Transport Hog")

- **Seats:** Driver, passenger bed (troops)
- **Weapons:** None
- **Theft:** Boarding possible. Stealable when the driver is idle or fleeing (Proposed rule below)

**Weak points and boarding**
- Same as the Warthog. Passengers can be thrown when the vehicle flips.

**Mount, kill, and take it**
- **Mount:** kill the gunner first (if it has one), then board the driver. In Reach the boarder takes the seat they board.
- **Grenades:** a frag under the chassis flips it and throws everyone out; a stuck plasma grenade does heavy damage or destroys it; two direct grenade hits or one rocket destroys it (Halo 3 onward).
- **Melee:** a Spartan beside a stopped Warthog can melee the gunner off the turret or the passenger out of the seat.
- **Transport Hog:** no gunner, so a single boarder takes it uncontested. The riders on the bed are the only defense; kill them with a grenade on the bed before boarding.
- **EMP:** stops it so a boarder can walk up to it.

**AI tactics (Proposed)**
- Drive players to and from objectives or points of interest.
- Stop at a safe distance and wait for passengers.
- Retreat toward the nearest friendly zone when attacked.
- Do not cross open ground without an escort.

**Avoid**
- Ghost, Wraith, Scorpion, Banshee lanes, and hostile infantry clusters.

---

### M274 Mongoose

- **Seats:** Driver, passenger
- **Weapons:** None mounted. Passenger weapon only.
- **Theft:** Boarding possible. Halopedia: boarding kicks both the driver and passenger off at once, similar to the Banshee boarding animation.

**Weak points**
- Halopedia: an EMP makes the Mongoose crouch and deactivate, which makes boarding easier.
- Community: a Mongoose suicide ram into a Scorpion does damage, and a point-blank explosion hurts the tank.

**Running people over**
- Light and fast. Community: ramming with a Mongoose is risky because glancing off terrain can cost you shields and alert the enemy.

**Mount, kill, and take it**
- **Mount:** board it and both driver and passenger are kicked off together (Reach onward).
- **Grenades:** any grenade near it flips it; a stuck grenade kills both riders. It has no armor, so rifle fire at the riders is enough.
- **EMP:** it crouches and stops, which makes the riders sitting targets.

**AI tactics (Proposed)**
- Fast flanking and objective runs.
- Passenger dismounts to capture or defend.

**Avoid**
- Mounted-gun vehicles, Banshees, and Wraith mortars.

---

### M808 Scorpion

- **Seats:** Driver, gunner
- **Weapons:** 90mm cannon (main), coaxial chaingun (secondary)
- **Theft:** Boarding possible. Halopedia describes two methods below.

**Weak points and how to remove the driver**
- Community: the Scorpion's canopy protects the driver. Two Sniper Rifle shots destroy the canopy, and 21 DMR shots do the same. Once the canopy is gone, a still driver can be headshot.
- Community: the back of the Scorpion is a weak spot. Shots from the rear do more damage, so Scorpions that drive in backwards are still vulnerable.
- Community: the Scorpion has considerably less armor in Reach than in Halo 3, so a few well-placed Sniper Rifle shots can destroy one.
- Community: a Plasma Pistol shot or a timed grenade can EMP the tank.
- Community: a Plasma Launcher charges four shots that can be held behind cover. The lock holds while you stay in range.

**Boarding and grenade or melee destruction**
- Halopedia: the boarder jumps onto the Scorpion. From there, they can melee the vehicle to expose and kill the driver, or plant a grenade to kill everyone and destroy the vehicle.
- Halopedia: a Scorpion or Wraith gunner can fire on boarders. Kill the gunner before boarding.
- Halopedia counter-boarding tactic: get out as soon as an attacker gets close. If you are willing to sacrifice the vehicle, board it right when the attacker gets in, then destroy the tank with a grenade or melee.
- Halopedia: a grenade planted on the Scorpion destroys it and kills all occupants.

**Running people over**
- Too heavy to ram effectively. Community: a Mongoose can suicide into a Scorpion for damage.

**AI tactics (Proposed)**
- Hold a fixed position covering the objective.
- Coaxial chaingun on infantry, main cannon for vehicles.
- Back toward cover when a Banshee approaches.
- Do not engage Armor Lock targets.

**Avoid**
- Banshee, Wraith mortar, and enemy Scorpions head-on.
- Plasma Pistol users, who can EMP the tank.

---

### Ghost

- **Seats:** Driver
- **Weapons:** Twin plasma cannons (main). Boost is a movement ability.
- **Theft:** Boarding possible

**Weak points and boarding**
- Halopedia: boarding a Ghost is harder than boarding some vehicles because it can move in all directions.
- Halopedia: dodge a Ghost so it boosts into a wall. While it backs out, board it from behind.
- Community: Ghosts are hard to hit while moving. A teammate in Armor Lock forces the driver to wait, which lets you shoot.

**Running people over**
- Halopedia: do not boost until about one to two Scorpion lengths from the target. Boosting from farther away gives the target time to jump, boost sideways, stick you with a grenade, or board you.
- Halopedia: be careful who you splatter in Reach. Armor Lock targets can kill the attacker.
- If the ram misses, switch to the plasma cannons or boost to a new target.

**Mount, kill, and take it**
- **Mount:** dodge it so it boosts into a wall, then board from behind while it reverses (Halopedia). The driver is thrown out; melee them before they stand.
- **Grenades:** a stuck plasma grenade on the driver's back kills them; a frag under the nose can flip it (it flips less easily than a Warthog).
- **EMP:** stops the boost mid-charge and leaves it open to boarding.

**AI tactics (Proposed)**
- Fast flank harassment. Run infantry down in the open.
- Plasma cannons for vehicles and far targets.
- Boost out of Scorpion and Revenant fire, after checking the escape route.
- Do not splatter Armor Lock targets.
- Retreat when two or more enemy vehicles are close.

**Avoid**
- Scorpion cannon lines, Revenant, and Banshee air superiority.

---

### Banshee

- **Seats:** Pilot
- **Weapons:** Twin plasma cannons (main). Fuel rod cannon (secondary).
- **Theft:** Boarding possible. Halopedia: boarding a Banshee kicks the pilot off.

**Weak points and boarding**
- Halopedia: the Banshee's fuel rod can flip Warthogs and Mongooses and can damage infantry.
- Halopedia: a Rocket Launcher lock-on works in Reach, but a skilled pilot throws the Banshee around to break the lock.
- Community: a rocket shot through the crack between the cockpit and hull does not harm the Banshee.
- Community: a Banshee's fuel rod homes in on vehicles in Reach, but the projectile is slow, so a Banshee can outrun its own shot.

**Running people over**
- Not a ramming vehicle. Its damage comes from plasma cannons and fuel rods.
- Community: a Banshee swoop onto a target with Armor Lock active kills the Banshee.

**Mount, kill, and take it**
- **Mount:** boarding kicks the pilot out. EMP it first (Halo 3 onward) so it drops to the ground in front of you.
- **Kill the pilot without the craft:** Halo 3 shoots the pilot's legs; ODST and Reach have the hull-to-canopy gap for a sniper round or a rocket. A free Banshee is then yours.
- **Grenades:** a stuck plasma grenade on the wing kills most Banshees; a frag under a landed Banshee flips it and strands the pilot.
- **Rockets:** lock on in Halo 2 and Reach, not in Halo 3 or ODST. Halo 4 Banshees do slower tricks, so rockets and the Railgun hit them more often.

**AI tactics (Proposed)**
- Patrol the air above the objective.
- Attack flying vehicles first, then ground vehicles, then light infantry.
- Fuel rod on Warthogs and Mongooses to flip them. Fuel rod on infantry clusters.
- Swoop attacks: dive onto targets, then climb out.
- Can be stolen if a player gets within 4 m while the pilot is not engaged in air combat.

**Avoid**
- Armor Lock targets, which can kill the attacker.
- Rocket Launchers.
- Scorpion cannon when grounded.
- Wraith mortar.

---

### Wraith

- **Seats:** Driver, gunner
- **Weapons:** Plasma mortar (main). Anti-personnel plasma (secondary, verify).
- **Theft:** Boarding possible

**Weak points and boarding**
- Halopedia: in Reach, you can commandeer a Wraith by killing its gunner and operating the plasma turret. The driver then exits and can be killed.
- Halopedia: boarding a Wraith in Reach works like a Scorpion. Board, then melee or grenade the driver.
- Community: the Wraith's mortar is less effective against flying targets. A jetpack is useful when fighting Wraiths.
- Halopedia: when fighting a Wraith in Reach, Evade, Sprint, or Armor Lock help you avoid the mortar.

**Running people over**
- Slow and not used for ramming.
- Community: a Warthog run can end a Wraith's life.

**AI tactics (Proposed)**
- Hold a long-range position and shell the approach to the objective.
- Relocate after every few shots.
- Do not advance into close-range combat.

**Avoid**
- Banshee overhead, Hornet, Ghost flanks, and Warthog runs.

---

### Type-48 Revenant

- **Seats:** Driver, gunner
- **Weapons:** Plasma mortar (main). Halopedia: the Revenant fires a Class-2 plasma mortar.
- **Theft:** Boarding is harder because the Revenant moves in all directions (Halopedia).

**Weak points**
- Community: the Revenant is resistant to small arms and is best taken out with explosives.
- Community: use Rocket Launchers or grenades.

**Running people over**
- Heavy and slow. Halopedia: the Revenant can overrun groups of infantry, but its speed is low.

**Mount, kill, and take it**
- **Mount:** boardable, but Halopedia warns it is harder than most because the hover chassis moves in every direction. Board it when it is stopped, reversing, or wedged on terrain. The driver is thrown out and the vehicle is yours.
- **Kill the crew:** the driver and gunner sit exposed; headshots remove them one at a time. Kill the gunner first.
- **Grenades and rockets:** community: explosives are the reliable answer. A stuck plasma grenade on the driver's seat or a rocket kills it. Frags under it do little because hover vehicles do not flip easily.
- **EMP:** stops it dead and makes boarding simple.

**AI tactics (Proposed)**
- Slow, heavy assault on objectives.
- Route toward infantry-heavy defenses.

**Avoid**
- Rocket Warthog, explosives, Wraith mortar, and Scorpion head-on.

---

### UH-144 Falcon

- **Seats:** Pilot, gunner(s), troop bay (variant dependent)
- **Weapons:** Side-mounted machine guns (standard). Nose gun variant has a pilot-controlled gun.
- **Theft:** Boarding possible (verify)

**Weak points**
- Halopedia: in Reach multiplayer, the Falcon lacks the chin autocannon the pilot normally uses. Originally, this was for balance reasons.
- Community: the windshield on AI-controlled Falcons is solid grey, so the pilot cannot see through it.

**Mount, kill, and take it**
- **Mount:** among the vehicles most often boarded (Halopedia). When it hovers low for its passengers to shoot, jump and board; the pilot is thrown out. EMP it to force it down.
- **Kill the crew:** the pilot and side passengers are all exposed. Battle Rifle, Carbine, and sniper headshots kill them without touching the airframe, which leaves the vehicle free to take.
- **Grenades and rockets:** a stuck plasma grenade on the fuselage destroys it; Spartan Laser and rockets kill it in one or two hits; the Missile Pod (Halo 3) locks on.

**AI tactics (Proposed)**
- Hover near objectives and cover squad movement.
- Use the side guns on infantry and light vehicles.

**Avoid**
- Banshee, Phantom, and Wraith mortar.

---

### D77-TC Pelican (Verify)

- **Seats:** Pilot, gunner(s), troop bay
- **Weapons:** Verify
- **Theft:** Verify

**Weak points**
- Community: the windshield on AI-controlled Pelicans is solid grey, which matters for AI pilots.

**Mount, kill, and take it**
- Not drivable in multiplayer, so no boarding rules apply. In the Halo 4 campaign mission it cannot be boarded by enemies.

**AI tactics (Proposed)**
- Drop troops at the objective, then loiter at safe altitude.

**Avoid**
- Banshee and anti-air rockets.

---

### Hornet, Spectre, Chopper, Prowler (not in Reach)

- These vehicles do not exist in Halo: Reach. Do not assign them AI roles in Reach. Halopedia notes the Falcon replaced the Hornet's role.

---

### MCC Forge additions (Reach)

These vehicles were added to Reach in Halo: The Master Chief Collection through the Forge palette. They are not in the original Reach campaign or multiplayer. The Forge update was added to Forge World and Tempest, according to Halopedia.

#### FSS-1000 Sabre (Forge)
- **Status:** Yes (Forge, Forge World and Tempest)
- **Seats:** Pilot only (single occupant, per Halopedia)
- **Weapons:** Auto cannons (main). Lock-on missiles (secondary).
- **Shields:** Has energy shields. Halopedia's screenshot caption shows shields taking fire in combat.
- **Theft:** Verify whether Sabres can be boarded. Proposed steal radius: 4 m.

**Weak points**
- Halopedia does not give verified weak points. Test the Sabre's shield and hull damage in Forge before tuning AI.
- Community: the Sabre is highly maneuverable for its size, so tracking it is hard in close combat.

**Ramming and collision**
- Halopedia: a Sabre collision kill registers as "Collision Damage" and the attacker receives a "Collision Damage" kill. It does not count as a splatter, so there is no splatter medal.
- Use collision damage as an AI tactic against infantry on the ground, but do not rely on it for medal-driven play.

**Counterparts and matchups**
- Halopedia: the Seraph and Space Banshee fill similar roles on the Covenant side. The Seraph operates almost the same as the Sabre, with differences in damage and shields.
- Halopedia: leading targets is recommended against fast fighters, mainly the Seraph.

**AI tactics (Proposed)**
- Patrol the air above the objective.
- Attack other aircraft first, using lock-on missiles on fast targets and auto cannons on slower ones.
- Attack ground vehicles with auto cannons.
- Lead targets when the enemy is a Seraph.

**Avoid**
- Seraph fuel rod cannon lanes. Halopedia lists the Seraph's armament as fuel rod cannons aimed at air targets.
- Head-on chases with a Seraph, which is fast.
- Ground infantry carrying Rocket Launchers or Plasma Pistols while the Sabre is slow or turning.

---

#### Morsam-pattern Seraph (Forge)
- **Status:** Yes (Forge, Forge World and Tempest)
- **Seats:** Pilot only
- **Weapons:** Four fuel rod cannons (per Halopedia's Seraph infobox, the Forge in-game vehicle). The fuel rods are anti-air.
- **Theft:** Halopedia describes a glitch in the campaign level Long Night of Solace where a Plasma Pistol EMP stuns a Seraph and lets the player hijack it. This is a campaign glitch. Verify whether it works on Forge Seraphs.

**Weak points**
- Halopedia: Seraphs can be stunned with a Plasma Pistol EMP, the same mechanic used against other vehicles in later Halo games.
- Verify the Seraph's hull and shield values in Forge.

**Ramming and collision**
- Same collision damage rules as the Sabre. No splatter medal for collision kills.

**AI tactics (Proposed)**
- Fire fuel rod cannons on aircraft first.
- Stay at range against Sabres, since the Sabre's lock-on missiles are effective against fast targets.
- Use the Seraph's speed to break off after an attack.

**Avoid**
- Plasma Pistol EMP users, who can stun the Seraph.
- Head-on runs against a Sabre, which leads well against fast fighters.

---

#### UH-144 Falcon Transport variant (Forge)
- **Status:** Yes (Forge)
- **Seats:** Pilot, passengers. Halopedia says the Transport Falcon carries five passengers.
- **Weapons:** None (unarmed transport version, per Halopedia)
- **Theft:** Verify.

**Weak points**
- Unarmed. Its only defense is staying out of range.

**AI tactics (Proposed)**
- Drop passengers at the objective. Stay hovering only as long as the drop requires.
- Retreat when attacked.

**Avoid**
- Anything with anti-air. This variant has no weapons.

#### UH-144 Falcon grenade-launcher variant (Forge)
- **Status:** Yes (Forge)
- **Seats:** Pilot, gunner(s)
- **Weapons:** Rapid-fire grenade launchers in place of the standard twin chainguns (per Halopedia's Forge page)
- **Theft:** Verify.

**AI tactics (Proposed)**
- Strafe ground targets with grenades, staying at a safe altitude.
- Break off when a Banshee or Seraph engages.

**Avoid**
- Banshee and Seraph fuel rod lanes.

---

#### Forklift (Forge)
- **Status:** Yes (Halopedia lists it under gameplay drivable vehicles in the Forge palette)
- **Seats:** Driver
- **Weapons:** None
- **Theft:** Verify.

**AI tactics (Proposed)**
- Non-combat. Use only for moving objects or as a barrier in Forge maps.

**Avoid**
- Any vehicle with a weapon.

---

#### Troop Warthog (Forge)
- **Status:** Yes (Forge). Likely the M831 Troop Transport Warthog. Verify.
- **Seats:** Driver, passenger bed
- **Weapons:** None
- **Theft:** Boarding possible, same as the M831.

**AI tactics (Proposed)**
- Same as the Transport Hog profile above.

---

#### Cart, Spade, and HC1500 (civilian, Forge)
- **Status:** Campaign drivable. Forge drivability: Verify.
- **Weapons:** None. Halopedia: the Spade lets the Jorge-052 character mount his chaingun on its rear platform in the campaign.
- **Notes:** Halopedia lists the HC1500 as also having a tractor variant.

**AI tactics (Proposed)**
- Non-combat. Use as traffic or scenery unless Forge testing shows they are drivable and useful.

---

### Theft rules (Reach)

- **Boarding:** Players hold the action button near an AI vehicle to board it.
- **Warthog:** the boarder takes the seat.
- **Mongoose:** boarding kicks both occupants off.
- **Banshee:** boarding kicks the pilot off.
- **Scorpion and Wraith:** board from the top. Kill the gunner first.
- **Steal radius (Proposed):** 3 m for ground vehicles, 4 m for Banshees and aircraft.
- **Trigger (Proposed):** The AI driver is not engaged in combat.
- **Armor Lock:** Do not allow AI to steal from or splatter Armor Lock targets.

---

### Open items

- Confirm whether the Pelican and Phantom are drivable in the MCC Reach Forge palette.
- Confirm Wraith anti-personnel secondary.
- Confirm Revenant weapon stats in MCC.
- Confirm Armor Lock interaction with splatter in MCC.

---

### Objective Game Types (Halo: Reach)

**Scope and status**
- **Confirmed for Reach:** Capture the Flag (1 Flag CTF Pro in the Team Objective playlist), Invasion (6v6 phases, with vehicles unlocked by phase), Headhunter (skull collection and drop site that moves), Assault (bomb), Oddball, and King of the Hill (Reach can place the hill on a vehicle, per Halopedia).
- **Verify:** Stockpile, Generator Defense (mentioned in 2010 coverage, not verified in MCC), Invasion Slayer.
- **Reach-specific rules:** A vehicle that rams a player with Armor Lock active takes heavy damage (Wikipedia). Armor Lock also kills splatter attackers in some cases (community). Vehicles spawned in Forge only are not in stock objective playlists.

#### 1 Flag CTF (Reach)

**Halopedia objective logic**
- Defending team: defend the flag from pursuing offense. If a flag is taken, kill the carrier and return the flag.
- Defense must watch for multiple entries, since most bases have more than one way in.

**Carrier logic**
- **REACH-CTF-01 Carrier weapon:** Halopedia: give the potential carrier a close-combat weapon, such as an Energy Sword or Shotgun, with a sniper covering. If the carrier gets into trouble, drop the flag, kill the opponent, and resume.
- **REACH-CTF-02 Vehicle escort:** IF a vehicle is used to attack, THEN keep it gunning and moving while waiting for the carrier (Halopedia).
- **REACH-CTF-03 Active camo sneak (Standoff):** IF Active Camo is on the map, THEN sneak into the base and either run out with the flag or kill defenders quietly.
- **REACH-CTF-04 Armor Lock caution:** Do not run a splatter attack at a carrier with Armor Lock active. The attacker takes heavy damage or dies.

**Pursuit logic**
- **REACH-PUR-01 Sniper cover:** A skilled sniper covers the carrier and the chase route (Halopedia).
- **REACH-PUR-02 Fuel rod on Warthogs:** IF the carrier is in a Warthog or Mongoose, THEN a Banshee fuel rod can flip it (Halopedia Reach Banshee).
- **REACH-PUR-03 Falcon interception:** IF the enemy carrier flees by air or the map has a Falcon, THEN the Falcon pilot should cut the carrier off at a choke point. Falcon MP has no pilot chin gun in Reach (see the Reach profile), so use the side guns.

**Defense logic**
- **REACH-DEF-01 Flag reset:** Halopedia: defenders hovering around the flag can reset it. Picking the flag up, even at the cost of your own life, can prevent it returning.
- **REACH-DEF-02 Park the defense:** IF no carrier is active, THEN park a Warthog or Scorpion where the flag is visible from the main entrance.

#### Invasion (Reach)

**Phase logic (Halopedia and Twinfinite)**
- Invasion is 6v6 and runs in phases. Phase 1 opens only one portion of the map with no vehicles.
- Teams move forward as they complete objectives. New loadouts, weapons, and vehicles unlock with each phase.
- Mutual spawning is strong. Small teams of two or three can change results, especially with the Falcon on Spire.

**Spire logic (Halopedia)**
- Spartans take the Data Core to the top of the Spire, then move it to a Pelican on the beach.
- If the Data Core does not reach the Pelican in time, the defending Elites win.

**Logic**
- **REACH-INV-01 Falcon control:** IF your team controls the Falcon on Spire, THEN use it to deliver the Data Core to the beach Pelican faster than the Elite defenders can intercept.
  - **Correction: the core is carried as a turret, not a flag; its carrier cannot ride.** The Falcon carries the attackers to the top (to take the core and escort it), not the core to the Pelican.
- **REACH-INV-02 Pelican escort:** IF a Pelican is waiting on the beach, THEN keep a Warthog or Mongoose escort within 20 m of the pickup point.
- **REACH-INV-03 Phase transitions:** IF the next phase unlocks vehicles, THEN prioritize spawn placement near the new vehicle depot so the team can take them before the defenders.

#### Headhunter (Reach)

**Halopedia and 2010 coverage**
- Pick up skulls from kills and drop them at a designated drop site that moves around the map.

**Logic (Proposed)**
- **REACH-HH-01 Drop-site vehicle:** IF the drop site moves, THEN send a Warthog or Mongoose ahead of carriers to clear the route.
- **REACH-HH-02 Skull escort:** IF a player carries multiple skulls, THEN a Ghost or Warthog escorts them to the drop site. Halopedia calls Headhunter Slayer with objective stylings, so kills still matter.
- **REACH-HH-03 Skull steal:** IF the enemy carries skulls near a vehicle spawn, THEN a Ghost or Mongoose ram or flip their vehicle.

#### King of the Hill (Reach)

**Halopedia**
- Control the hill to earn points. The hill can be placed on a vehicle.
- A useful tactic is one person inside the hill scoring while the rest fan out to defend.

**Logic (Proposed)**
- **REACH-KOTH-01 Vehicle hill:** IF the hill is on a vehicle, THEN the scorer stays inside the vehicle while the escort covers it. Do not leave the driver alone.
- **REACH-KOTH-02 Armor Lock on the hill:** IF an enemy with Armor Lock is on the hill, THEN do not ram. Use a gunner or a Banshee fuel rod from outside.

#### Assault (Reach)

**Halopedia**
- Assault is listed as a Reach game type. Team tactics follow Halo 2 and Halo 3 Assault rules.
- Keep at least two teammates near the bomb carrier. Retreat when needed.

**Logic (Proposed)**
- **REACH-ASS-01 Carrier vehicle:** IF the bomb carrier rides a Warthog, THEN an escort Warthog or Mongoose covers the rear.
- **REACH-ASS-02 Armor Lock block:** IF a defender has Armor Lock, THEN throw a grenade or switch to a Banshee fuel rod instead of trying to splatter them.

#### Oddball (Reach)
- The Oddball Kill medal applies in Reach (Halopedia). Carriers can be killed with melee or Assassination.
- **REACH-ODD-01 Carrier assassination:** Halopedia: Assassinations are available in Reach. Whether a carrier seated in a vehicle can be assassinated is unverified, so test before assigning carrier roles in vehicles.

#### Headroom
- Verify Stockpile and Generator Defense rules.
- Verify whether vehicles can carry the ball or the hill in MCC.

---

## Halo 4 (MCC)

**Status key**
- **Yes:** Confirmed drivable in this game from retrieved sources.
- **Verify:** Not confirmed. Test in-game.
- **Community:** Reported by players or wiki editors. Not tested by us.
- **Proposed:** Design target for the mod, not native MCC AI.

---

### Critical Halo 4 facts for your mod

- **Wraiths require an EMP before boarding.** Halopedia: in Halo 4 (campaign and Spartan Ops), you cannot kill the Wraith's driver with melee before the Wraith is destroyed. You must EMP it first with a Plasma Pistol overcharge, which usually takes four or five shots. Then you can force the driver to eject and board.
- **Mantis is boarded differently.** Halopedia: hit it with a fully charged Plasma Pistol shot, or use Active Camouflage to evade the driver's sight and rush the cockpit. Dropping onto it from above or standing level with the cockpit also works and is safer. EMP makes the Mantis crouch as if deactivated, which removes the need to jump.
- **Revenant is not stock.** The Phelent-pattern Revenant was added to Halo 4's files for MCC but can only be spawned through mods. Do not include it in the stock AI roster.
- **Wraiths can be commandeered.** Halopedia: in Halo 4, you can take a Wraith by killing its gunner and operating the plasma turret. The driver then exits.

---

### Roster

| Vehicle | Status |
|---|---|
| M12 Warthog (chaingun) | Yes |
| M12G1 Gauss Warthog | Yes |
| M12R Rocket Warthog (anti-air) | Yes |
| M274 Mongoose | Yes |
| M808 Scorpion | Yes |
| Ghost | Yes |
| Wraith | Yes (EMP first; see above) |
| Banshee | Yes (multiplayer; appears on large maps such as Exile and Ragnarok. This comes from general knowledge, not a retrieved source, so confirm map placements) |
| Mantis | Yes (multiplayer; appears on Ragnarok and other large maps. Also from general knowledge; confirm) |
| D79-TC Pelican | Campaign only (one mission). Not drivable in multiplayer |

**Not in Halo 4:** Phaeton (a Halo 5 vehicle, listed here by mistake in an earlier draft), Hornet, Brute Chopper, Prowler, Spectre, Falcon, Transport Hog, Elephant.

**Not stock:** Phelent-pattern Revenant (mod only).

**Not drivable:** Phantom.

---

### M12 Warthog (Chaingun)

- **Seats:** Driver, gunner, passengers
- **Weapons:** Chaingun turret
- **Theft:** Boarding possible

**Weak points and boarding**
- Kill the gunner before boarding.
- Community: the driver can be pulled out with melee, or a grenade planted in the vehicle.
- Community: the Warthog flips from a frag grenade and knocks the occupants out.

**Running people over and ramming**
- Halopedia: a Warthog ram at full speed is the most reliable light-vehicle kill. A head-on Warthog ram destroys a Ghost.
- Keep passengers aboard. Passengers thrown out reduce the vehicle's value.

**AI tactics (Proposed)**
- Flank routes around the objective.
- Suppress threats near escorted vehicles.
- Ram light infantry above a speed threshold.
- Retreat below half health.

**Avoid**
- Banshee overhead.
- Wraith mortar zones.
- Scorpion cannon lanes.

---

### M12G1 Gauss Warthog

- **Seats:** Driver, gunner
- **Weapons:** Gauss cannon
- **Theft:** Boarding possible

**Weak points and boarding**
- Same as the chaingun Warthog.
- Community: the Gauss gunner is exposed when the vehicle is stopped.

**Mount, kill, and take it**
- **Mount:** kill the gunner first (if it has one), then board the driver. Boarding throws the driver out; melee them before they recover.
- **Grenades:** a frag under the chassis flips it and throws everyone out; a stuck plasma grenade does heavy damage or destroys it; two direct grenade hits or one rocket destroys it (Halo 3 onward).
- **Melee:** a Spartan beside a stopped Warthog can melee the gunner off the turret or the passenger out of the seat.
- **Gauss gunner:** the gunner is fully exposed and must stop moving to aim. Snipe the gunner while the hog is parked on overwatch; the Gauss cannon has no close-range answer.
- **EMP:** stops it so a boarder can walk up to it.

**AI tactics (Proposed)**
- Long-range overwatch on choke points.
- Reposition after each few shots.

**Avoid**
- Banshee and close-range Scorpion engagements.

---

### M12R Rocket Warthog (Anti-Air)

- **Seats:** Driver, gunner
- **Weapons:** Anti-air rockets (main)
- **Theft:** Boarding possible

**Weak points and boarding**
- Kill the gunner before boarding.
- Community: the rocket launcher can lock onto Banshees.

**Running people over**
- Not a ramming vehicle.

**Mount, kill, and take it**
- **Mount:** kill the gunner first (if it has one), then board the driver. Boarding throws the driver out; melee them before they recover.
- **Grenades:** a frag under the chassis flips it and throws everyone out; a stuck plasma grenade does heavy damage or destroys it; two direct grenade hits or one rocket destroys it (Halo 3 onward).
- **Melee:** a Spartan beside a stopped Warthog can melee the gunner off the turret or the passenger out of the seat.
- **Rocket hog gunner:** the rockets are slow to track ground targets at close range, so rush it on foot or in a Ghost and board.
- **EMP:** stops it so a boarder can walk up to it.

**AI tactics (Proposed)**
- Track aircraft over objectives.
- Hold fire on ground targets unless a vehicle blocks the objective.

**Avoid**
- Ground infantry and Scorpion cannon.

---

### M274 Mongoose

- **Seats:** Driver, passenger
- **Weapons:** None mounted. Passenger weapon only.
- **Theft:** Verify whether it can be boarded in Halo 4

**Weak points**
- Halopedia: an EMP makes the Mongoose crouch and deactivate, which makes boarding easier.

**Running people over**
- Light and fast. Ramming is risky because glancing off terrain can cost you shields.

**Mount, kill, and take it**
- **Mount:** board it and both driver and passenger are kicked off together (Reach onward).
- **Grenades:** any grenade near it flips it; a stuck grenade kills both riders. It has no armor, so rifle fire at the riders is enough.
- **EMP:** it crouches and stops, which makes the riders sitting targets.

**AI tactics (Proposed)**
- Fast flanking and objective runs.
- Passenger dismounts to capture or defend.

**Avoid**
- Mounted-gun vehicles and Wraith mortars.

---

### M808 Scorpion

- **Seats:** Driver, gunner
- **Weapons:** 90mm cannon (main), coaxial chaingun (secondary)
- **Theft:** Verify Halo 4 boarding method for Scorpions

**Weak points and boarding**
- Kill the gunner before boarding.
- Halopedia: an EMP disables the engine and makes boarding possible. Verify whether a Scorpion can be EMP'd in Halo 4 the same way as a Wraith.
- Community: the back of the Scorpion is a weak spot in later games. Verify in Halo 4.

**Running people over**
- Too heavy to ram effectively.

**Mount, kill, and take it**
- **Mount:** kill the gunner, then board from the rear or side, outside the cannon arc. Jump-on-top boarding: melee the hatch until the driver is exposed and dead (keeps the tank), or plant a grenade (kills all occupants and destroys the tank). See the Quick Reference for the per-game hatch rules.
- Halo 4: EMP with a Plasma Pistol overcharge to stop it, board from the rear, melee the hatch to kill the driver and keep the tank, or plant a grenade to destroy it with all occupants. Verify whether Halo 4 Scorpions need the multi-shot EMP that Wraiths do.
- **EMP:** a charged Plasma Pistol shot stops the engine so the tank cannot drive away from a boarder.

**AI tactics (Proposed)**
- Hold a fixed position covering the objective.
- Coaxial chaingun on infantry, main cannon for vehicles.
- Back toward cover when a Banshee approaches.

**Avoid**
- Banshee, Wraith mortar, and enemy Scorpions head-on.

---

### Ghost

- **Seats:** Driver
- **Weapons:** Twin plasma cannons (main). Boost is a movement ability.
- **Theft:** Boarding possible

**Weak points and boarding**
- Halopedia: boarding a Ghost is harder because it moves in all directions.
- Halopedia: dodge a Ghost so it boosts into a wall. While it backs out, board it from behind.
- Verify whether Halo 4 Ghosts can be boarded from the rear the same way they can in Halo 3.

**Running people over**
- Halopedia: do not boost until about one to two Scorpion lengths from the target. Boosting from farther away gives the target time to jump, boost sideways, stick you with a grenade, or board you.
- Community: Armor Lock targets can kill the attacker. Verify in Halo 4.

**Mount, kill, and take it**
- **Mount:** dodge it so it boosts into a wall, then board from behind while it reverses (Halopedia). The driver is thrown out; melee them before they stand.
- **Grenades:** a stuck plasma grenade on the driver's back kills them; a frag under the nose can flip it (it flips less easily than a Warthog).
- **EMP:** stops the boost mid-charge and leaves it open to boarding.

**AI tactics (Proposed)**
- Fast flank harassment. Run infantry down in the open.
- Plasma cannons for vehicles and far targets.
- Boost out of Scorpion and Wraith fire, after checking the escape route.
- Retreat when two or more enemy vehicles are close.

**Avoid**
- Scorpion cannon and Wraith mortar lines.
- Banshee air superiority.

---

### Wraith

- **Seats:** Driver, gunner
- **Weapons:** Plasma mortar (main). Anti-personnel plasma (secondary, verify).
- **Theft:** Boarding requires an EMP first (see critical facts above)

**Weak points and boarding**
- Halopedia: EMP the Wraith with a Plasma Pistol overcharge, usually four or five shots, to force the driver out.
- Halopedia: you cannot melee the driver to death before the Wraith is destroyed, so the EMP step is required.
- Halopedia: you can commandeer the Wraith by killing its gunner and operating the plasma turret. The driver then exits.
- Community: the mortar is less effective against flying targets.

**Running people over**
- Slow and not used for ramming.
- Community: a Warthog run can end a Wraith's life.

**Mount, kill, and take it**
- **Mount:** kill the gunner, then board from the rear or side, outside the cannon arc. Jump-on-top boarding: melee the hatch until the driver is exposed and dead (keeps the tank), or plant a grenade (kills all occupants and destroys the tank). See the Quick Reference for the per-game hatch rules.
- Halo 4: EMP first (four or five Plasma Pistol overcharges). Then board, melee, or grenade as normal. Or kill the gunner and take the turret seat so the driver exits.
- **EMP:** a charged Plasma Pistol shot stops the engine so the tank cannot drive away from a boarder.

**AI tactics (Proposed)**
- Hold a long-range position and shell the approach to objectives.
- Relocate after every few shots.
- Do not advance into close-range combat.

**Avoid**
- Banshee, Hornet, Ghost flanks, and Warthog runs.

---

### Banshee

- **Seats:** Pilot
- **Weapons:** Twin plasma cannons (main). Fuel rod cannon (secondary). Halopedia: in Halo 4 the fuel rod no longer tracks vehicles, and acrobatics are slower than in Reach.
- **Theft:** Boarding possible; the boarder kicks the pilot out.

**Weak points**
- Halopedia: when heavily damaged it emits a deep beeping sound, which tells nearby players it is about to die.
- Slower tricks than Reach, so it is easier to hit with the Rocket Launcher and the Railgun.
- EMP (Plasma Pistol overcharge) drops it and opens it to boarding.

**Mount, kill, and take it**
- **Mount:** boarding kicks the pilot out. EMP it first (Halo 3 onward) so it drops to the ground in front of you.
- **Kill the pilot without the craft:** Halo 3 shoots the pilot's legs; ODST and Reach have the hull-to-canopy gap for a sniper round or a rocket. A free Banshee is then yours.
- **Grenades:** a stuck plasma grenade on the wing kills most Banshees; a frag under a landed Banshee flips it and strands the pilot.
- **Rockets:** lock on in Halo 2 and Reach, not in Halo 3 or ODST. Halo 4 Banshees do slower tricks, so rockets and the Railgun hit them more often.

**AI tactics (Proposed)**
- Patrol the air above the objective.
- Attack flying vehicles first, then ground vehicles, then light infantry.
- Swoop attacks on ground targets, climbing out after each pass.
- Since the fuel rod does not track in Halo 4, fire it only at slow or stationary targets (parked vehicles, infantry clusters, the Mantis).

**Avoid**
- Scorpion cannon when grounded.
- Wraith mortar.

---

### Mantis

- **Seats:** Pilot (bipedal walker)
- **Weapons:** Arm-mounted machine gun and a missile pod (verify exact stats in MCC). It can also stomp.
- **Theft:** Halopedia: boarding works by landing on the cockpit or hitting it with a fully charged Plasma Pistol shot.

**Weak points and boarding**
- Halopedia: a fully charged Plasma Pistol shot to the Mantis, or Active Camouflage to evade the driver's sight and rush the cockpit.
- Halopedia: drop onto the Mantis from an elevated height, or stand level with the cockpit. This is safer than jumping.
- Halopedia: EMP makes the Mantis crouch as if deactivated, which removes the need to jump.

**Running people over**
- Too slow to run anyone down, but its stomp is a melee-range area attack that kills infantry next to it. Use the stomp on boarders and on infantry that rush it.

**Mount, kill, and take it**
- **Grenade:** once on the cockpit (after an EMP crouch or a drop from above), plant a grenade to destroy it or melee the cockpit to kill the pilot. Stuck plasma grenades on the legs do heavy damage while it is crouched.

**AI tactics (Proposed)**
- Hold the objective with a slow, heavy assault.
- Vehicles first, then infantry.

**Avoid**
- Banshee, Wraith mortar, and rocket-armed Warthogs.

---

### D79-TC Pelican (Verify)

- **Seats:** Pilot, side gunner seats, troop bay
- **Weapons:** Verify
- **Theft:** Verify

**Mount, kill, and take it**
- Not drivable in multiplayer, so no boarding rules apply. In the Halo 4 campaign mission it cannot be boarded by enemies.

**AI tactics (Proposed)**
- Drop troops at the objective, then loiter at safe altitude.

**Avoid**
- Banshee and anti-air rockets.

---

### Theft rules (Halo 4)

- **Boarding:** Players hold the action button near an AI vehicle to board it.
- **Wraith:** EMP first with a Plasma Pistol overcharge, usually four or five shots.
- **Mantis:** Full-charge Plasma Pistol shot, or Active Camouflage rush, or drop from above.
- **Steal radius (Proposed):** 3 m for ground vehicles, 4 m for aircraft and the Mantis.
- **Trigger (Proposed):** The AI driver is not engaged in combat.
- **Engaged driver:** does not eject.
- **Moving targets:** Halopedia says a target that keeps moving at full speed is hard to board, and can sometimes splatter attackers.

---

### Open items

- Confirm Banshee and Mantis map placements in MCC Halo 4 playlists.
- Confirm Mantis weapon stats and stomp damage in MCC.
- Confirm Scorpion boarding method in Halo 4.
- Confirm Wraith anti-personnel secondary.
- Confirm Mantis weapon loadout.

---

### Objective Game Types (Halo 4)

**Scope and status**
- **Confirmed for Halo 4 (Halopedia):**
  - **Capture the Flag:** Halopedia's image caption shows three Spartans delivering a flag in a Warthog. Flags can be used in assassinations in CTF (Halopedia).
  - **Oddball:** Carrier Kill and Carrier Kill Assist lines exist, and the Ball Kill medal (Halopedia). Oddball assassinations are a Halo 4 weapon-exclusive animation.
  - **Regicide:** A free-for-all where the leading scorer becomes King, with a bounty on their head.
  - **King of the Hill:** Halopedia lists a Halo 4 section on the KOTH page. Confirm the variants in MCC.
- **Verify:** Assault in Halo 4 (not confirmed by sources).
- **Halo 4 constraints:** Wraiths require an EMP before boarding. Mantis is boarded through a full-charge Plasma Pistol shot, Active Camo rush, or a drop from above (see the Halo 4 profile above).

#### Capture the Flag (Halo 4)

**Vehicle assignment**
- **H4-CTF-01 Three-Spartan Warthog:** Halopedia's image caption shows three Spartans delivering a flag in a Warthog. IF the Warthog has a driver and two passengers, THEN assign one passenger as flag runner and one as a rear defender with a Battle Rifle or Sniper.
- **H4-CTF-02 Warthog vs Ghost:** The Ghost is the faster escape. Warthog carries more players. Choose by the threat level on the route.

**Carrier logic**
- **H4-CTF-03 Carrier protection:** IF the carrier is in a Warthog, THEN keep the Warthog's gunner on the enemy side and the rear passenger watching the route behind.
- **H4-CTF-04 Assassinate defender:** Halopedia: flags can be used in assassinations in CTF. IF a defender stands in a narrow approach to your flag, THEN a carrier on foot can use the assassination to clear them and keep moving.

**Pursuit logic**
- **H4-PUR-01 Warthog ram:** Halopedia: a Warthog ram at full speed is the most reliable light-vehicle kill. A head-on ram destroys a Ghost.
- **H4-PUR-02 Mantis chase:** IF the enemy carrier escapes in a Warthog, THEN the Mantis does not chase (too slow). It holds a lane and fires missiles at the Warthog as it passes.
- **H4-PUR-03 Wraith blocking:** IF the enemy has a Wraith covering an approach, THEN do not drive a Warthog into its mortar line. Use an EMP first (Plasma Pistol overcharge) to disable the Wraith.

**Defense logic**
- **H4-DEF-01 Park over flag:** IF the flag is safe, THEN park a Warthog or Ghost over the flag.
- **H4-DEF-02 Flag hover:** Halopedia (Reach CTF, applying the same idea): defenders hovering around the flag can reset it. Hold a defender on the flag at all times if an enemy is near.

#### Oddball (Halo 4)

- **H4-ODD-01 Carrier escort:** IF your team holds the ball, THEN a Warthog or Ghost escorts the carrier.
- **H4-ODD-02 Ball Kill target:** Halopedia: the Ball Kill medal is awarded for killing a carrier. Vehicles chasing a carrier in a Warthog should shoot the driver first, since a stopped vehicle cannot keep the carrier moving (proposed).
- **H4-ODD-03 Carrier melee power:** Halopedia: carriers have more powerful melee attacks, usually one hit kills. Keep escorts within 5 m of the carrier so enemies cannot close in on foot.

#### Regicide (Halo 4)

Halopedia's guidance applies to vehicles as well as infantry:
- Playing it safe does not score. Players crowd the same location.
- Use a hologram to distract or delay players heading toward the King.
- The King earns Kingtacular and an Overshield after 20 seconds.

**Logic**
- **H4-REG-01 Vehicle hunter:** IF the King is in the open, THEN a Warthog or Ghost run down the King. Kill bounty is 15 to 35 points.
- **H4-REG-02 Hologram baiting:** IF a Hologram is available, THEN place it near the King's escape route so defenders waste time on it.
- **H4-REG-03 Armor-lock caution:** Community reports from Reach say splatters on Armor Lock targets can kill the attacker. Verify whether the same applies in Halo 4 before relying on splatter kills against a King with Armor Lock.

#### King of the Hill (Halo 4)

- **H4-KOTH-01 One scorer:** One player stays inside the hill while others defend the approaches.
- **H4-KOTH-02 Vehicle anchor:** IF the hill is uncontested, THEN a Scorpion or Warthog gunner covers approaches from outside the ring.
- **H4-KOTH-03 Mantis anchor:** The Mantis is the best hill anchor in Halo 4. It stands inside or beside the ring, stomps boarders, and uses missiles on vehicles. Keep infantry nearby to stop Plasma Pistol EMP users from disabling it.

#### Headroom
- Verify Halo 4 Assault and KOTH variants in MCC.
- Verify whether the Oddball carrier can drive a vehicle in Halo 4.

---

## Patch: Difficulty tiers and optional coach hooks (vehicle brain)

This file assumes a bot executes every rule at full strength. Two things modify that, both defined in `halo_mcc_bot_tiers_integration_and_coach.md`:

**Difficulty tiers (Part 2.1 of that file).** Reaction to vehicle threats, ram commit precision, the never-ram list, gunnery lead, weak-part aiming, boarding, retreat thresholds, vehicle selection, blind-spot awareness, boost timing, crew coordination, and air evasion all scale with the bot's tier (Easy, Normal, Heroic, Legendary, Mixed) and carry the per-bot 10 percent variance. Personalities (rusher, camper, flanker, sniper, driver, pilot, tanker, support) bias which vehicle a bot claims and how it uses it (Part 3).

**Optional coach (Part 4 of that file).** When an Ollama coach is attached, the objective brain may pass these overrides into the vehicle brain. They are advisory, validated, bounded, and expire; the vehicle brain runs unchanged when no coach is present.

| Hook | Allowed range | Hard limits that always win |
|---|---|---|
| `COACH-VEH-lane` | one of the map's enumerated lanes for a driver | the lane must exist; tanks and Elephants never enter lanes marked infantry-only |
| `COACH-VEH-role` | reassign a seated bot's role (ESCORT, AIR_DENIAL, LANE_BLOCK, ANCHOR, TRANSPORT) | a CARRIER passenger keeps CARRIER; no role may order a ram on tanks, Wraiths, Elephants, or Armor-Locked targets |
| `COACH-VEH-target_weight` | 0.5 to 2.5 per entity class | killability of 0 (cannot damage) still zeroes the score; the `exposure` term still applies |
| `COACH-VEH-retreat_threshold` | plus or minus 0.15 around the tier default | abandon threshold and "smoking plus incoming explosive" exit cannot be disabled |
| `COACH-VEH-spawn_request` | which vehicle role to claim next (4.7) | anti-air stays first whenever an enemy aircraft is active |
| `COACH-VEH-bait` | place a vehicle as bait with a trip mine or Armor Lock bot in its lane (`EQ-MINE-03`, `EQ-LOCK-06`) | never bait with the transport that the carrier needs |
| `COACH-VEH-air_mode` | Banshee/Hornet/Falcon this life: AIR_DENIAL, GROUND_SUPPORT, CARRIER_COVER, HILL_BOMB | AIR_DENIAL is forced when an enemy aircraft is up and no other anti-air exists |

Coach plays that touch this brain: `PLAY-ESCORT-HOG`, `PLAY-AIR-DENIAL`, `PLAY-TANK-FIRST`, `PLAY-CHOPPER-LANE`, `PLAY-VEHICLE-BAIT`, `PLAY-FF-ROOF` (all in the addendum's Part 4.6).
