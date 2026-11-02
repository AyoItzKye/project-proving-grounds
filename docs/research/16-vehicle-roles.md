# 16. Vehicle roles and strategies

Sources: Halopedia (Type-26 Banshee/Gameplay, Reach:Falcon, Reach:Scorpion, Reach:Mongoose, Type-26 Wraith/Gameplay,
Karo'etba-pattern Ghost/Gameplay, Plasma mortar, Rizvum-pattern Revenant, Boarding, Splatter), halo.bungie.org "Not So
Common Sense" vehicle guide (Halo 2), Giant Bomb (M12R Warthog, Ghost). Fan wikis: facts marked (wiki) are not from a
first-party source; button facts are checked live before the brain relies on them (docs/HANDOFF.md, VEHICLE TEST).

## Facts per vehicle (Halo: Reach first; the other games where they differ)

| Vehicle | Seats | Guns | Moves | Strength | Weakness |
|---|---|---|---|---|---|
| Warthog (chaingun, gauss, rocket) | driver, gunner, passenger | gunner's turret; rocket Warthog anti-vehicle (sources disagree: anti-air / anti-armor) | fast ground, jumps | transport, gunner kills infantry and light vehicles; splatter | driver unarmed, flips, rockets |
| Mongoose | driver, passenger | none (passenger shoots his own gun) | fastest ground, rough ground better in Reach | transport, flag runs | no armour, hijackable in Reach |
| Ghost | driver | two plasma cannons | hover, fast, short boost then cooldown (Reach), harder to steer than Halo 3 | hit-and-run, splatter (boost only from about two tank lengths: farther gives time to jump, stick or hijack) | weak point: fuel cell on its left side (Reach only); boarding from behind |
| Revenant | driver, passenger | light plasma mortar (Reach only) | hover, Ghost-like handling | mobile artillery backing infantry | light; boardable |
| Wraith | driver, gunner (anti-infantry plasma turret) | heavy plasma mortar on a fixed mount: must face the target | slow hover, boost | devastating splash against groups and vehicles | the gunner can be killed and the turret taken, then the driver bails; EMP (charged plasma pistol) dismounts; mortar poor against air and jump packs; boarders from the flanks |
| Scorpion | driver, gunner | 90 mm cannon (driver), anti-infantry gun (gunner) | tracks, slow | long range on open sightlines | Reach: much less armour than Halo 3 (a few sniper hits); boarded up close; useless once the gun is destroyed |
| Banshee | pilot | twin plasma cannons (alternate fire, accurate, short range); fuel rod bomb: homing on vehicles, slow (a Banshee outruns it), flips Warthogs/Ghosts, kills infantry on a direct hit | flies, cannot hover (Reach), limited boost (LT), limited tricks (rolls / flips) | ground attack, anti-vehicle | 5 frontal sniper hits, EMP shuts it down, rockets lock on (boost or dodge clear) |
| Falcon (Reach multiplayer) | pilot, 2 side gunners | side machine guns only; the pilot is unarmed | flies, hovers | transport and gun platform; good against Banshees | Banshees threaten it; slow target |
| Hornet (Halo 3) | pilot, 2 passengers | guns and lock-on missiles (pilot) | flies, hovers | air superiority, anti-vehicle | rockets, lock-ons |
| Chopper (Halo 3) | driver | cannons | heavy, boost and ram | splatter, rams vehicles | exposed rider |
| Elephant (Halo 3) | driver, gunners, passengers | turrets | very slow mobile base | mobile spawn / fort | slow |
| Mantis (Halo 4) | pilot | chaingun, missiles, stomp | walks | assault | slow, boardable |
| Turret / Shade | gunner | one gun | none | area denial | exposed gunner |

Counters every bot should know (on foot): rockets / Spartan laser / fuel rod / plasma launcher at vehicles (brain/bot.py
ANTI_VEHICLE), plasma pistol charge to dismount (EMP), board from behind or the flank, a sniper on a Banshee's front,
jump packs against Wraith mortars.

## Coded (brain/vehicles.py STRATEGY, brain/bot.py drive)

| Role | Vehicles | Driver does |
|---|---|---|
| splatter | Ghost, Chopper, Mongoose (no gun), Warthog (no gunner) | runs at infantry, boosts only in the last ~2 tank lengths, peels off when the man has a power weapon |
| strafe | Ghost, Revenant, Banshee | gun runs at 8-25 u, keeps moving side on, never parks |
| circle | Warthog / Spectre / Falcon with a gunner | circles the fight 15-25 u side on so the gunner works |
| artillery | Wraith, Revenant, Scorpion | holds 15-40 u, faces the target, backs off any man closer than 6 u (boarders), keeps moving between shots |
| air attack | Banshee, Hornet | low layer (learned strafing height) for runs, high layer to travel; fuel rod / missiles at vehicles and groups; boost away when hit or locked |
| transport | Mongoose, Warthog, Falcon, Elephant | carries the objective holder (ferry), drives the routes people drive (learned drive mesh) |
