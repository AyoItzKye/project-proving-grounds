# Bad AI behaviours

What a bot must never look like (the player: "create a detailed Bad AI behaviors list for ollama so it can know
what to critique and send back"). The AI director's critic (brain/critic.py) reads this file every match: each line
starting with `- **B-` becomes one entry of its checklist, and every fault it reports names one of these IDs (NEW for
something not on the list). Its critiques land in logs/critique_<map>_<stamp>.jsonl / .md and, for a match with bug
reports, in that match's folder (logs/bug_reports/<recording>/). Add to this list whenever a new bad behaviour is
seen; keep each entry one line: the behaviour, then "seen as:" what it looks like in the numbers the critic gets.

The bar: a bot should play like a strong human on the same team (the player's H2 SWAT games set Legendary), "not too botty
and cheaty ... not absolutely stupid ... human like".

## Movement and navigation
- **B-01** Staring into a wall or the floor while moving or idle. seen as: wall_stare hits, pitch far below level out of a fight.
- **B-02** Pacing back and forth in a small area for no reason. seen as: pacing hits, many units walked inside a few units' circle.
- **B-03** Pushing into a wall, rail, crate or teammate without moving. seen as: push_wall hits, unstuck wiggles, the same spot for many seconds.
- **B-04** Running into waist-high handrails and low walls instead of going around. seen as: push_wall at walkway edges, wiggles beside a drop.
- **B-05** Going to the right spot on the wrong floor (above or below the objective) on multi-storey maps. seen as: goal reached in x/y but height 1.5+ units off for a long time.
- **B-06** Getting stuck on one-way shields or force-field doorways, trying to walk back through them. seen as: push_wall at a shield doorway, a goal behind a shield chosen again and again.
- **B-07** Lost: wandering with no purpose, turning around, a path that goes nowhere. seen as: roam goal most of the minute, walked far but net distance small, goal changing every few seconds.
- **B-08** Wedged in a spawn corner or nook for a long time. seen as: same position for 30+ s right after spawning.
- **B-09** Walking or jumping off a deadly edge. seen as: a death with no enemy near, a fall.
- **B-10** Bunching up: teammates walking into each other, queuing in doorways, standing in a pile. seen as: several bots within 1 unit for long, give-way stalls.
- **B-11** Moving like a robot: perfectly straight lines, instant 180s, no strafing in fights, no jumping when a human would. seen as: zero strafe while fighting, constant speed, no jumps all minute.

## Awareness and looking
- **B-12** Looking at the destination through walls instead of down the path or at threats. seen as: facing far off the walk direction out of a fight.
- **B-13** Wallhack awareness: tracking or pre-aiming players it cannot see or hear (cheaty). seen as: aiming at a hidden enemy, shots at men not in view.
- **B-14** Blind to obvious threats: no reaction to being shot from behind or to an enemy in the open close by. seen as: no_shot hits, damage taken with no turn.
- **B-15** Chasing a man nobody has seen for a long time. seen as: long_chase hits, hunt goal on an old belief.

## Fighting
- **B-16** Engaging from a range its weapon is bad at: assault rifle or SMG at long range, sniper or DMR up close. seen as: cq_rifle hits, fights at distances outside the weapon's band, low on-target share.
- **B-17** Holding fire at a man in view. seen as: no_shot hits.
- **B-18** Tapping an automatic up close or spamming a precision rifle. seen as: auto_tap hits, presses per second wrong for the weapon.
- **B-19** Firing an empty gun or reloading mid-fight instead of switching. seen as: dry_fire hits, no switches with an empty magazine.
- **B-20** Explosives inside its own blast radius. seen as: blast_hurt hits, deaths to its own rockets or grenades.
- **B-21** Shooting through a shield or barrier that blocks shots, or at a man behind a window it cannot hit. seen as: long fights with no damage dealt, on target but no hits.
- **B-22** Aim too perfect or too poor for its difficulty: instant snaps, perfect tracking at Easy, or Legendary missing an open man. seen as: on-target share far from the tier's band.
- **B-23** Never using grenades, or throwing them into walls or at its own feet. seen as: zero grenades in long fights, self-damage.
- **B-24** Never meleeing a man in its face, or meleeing at range. seen as: close fights with no melee.
- **B-25** Not retreating or recharging with broken shields; fighting to the death in the open. seen as: deaths soon after shields broke, no retreat goal.
- **B-26** Not using cover: fighting from the open when cover is a step away. seen as: fights in open ground, high deaths per fight.
- **B-27** Every bot on the same weapon all match; never switching. seen as: one weapon 90%+ of the time, zero switches.

## Weapons, pickups and abilities
- **B-28** Not picking up weapons dropped by enemies or lying on the map. seen as: zero item goals or no inventory change all match.
- **B-29** Not going for power weapons on spawn timers (sniper, rockets, sword, shotgun) at higher difficulties. seen as: power weapons left on the map, no item trips by Heroic or Legendary bots.
- **B-30** Never using its armor ability or equipment (sprint, camo, armor lock, jetpack, hologram), or using it badly (armor lock in the open at full shields). seen as: zero ability presses, ability use with no threat.
- **B-31** Keeping a weapon out of ammo instead of swapping it for one on the ground. seen as: dry gun carried, ammo lying near.

## Objectives
- **B-32** Ignoring the objective: never going for the enemy flag, bomb, hill, ball, territory or core. seen as: objective goal near zero, no pickups all match.
- **B-33** Defenders frozen on top of the objective instead of patrolling the area from cover. seen as: camp hits by defenders, one spot for minutes.
- **B-34** Carrying the flag or bomb but not scoring: wandering, stopping to fight, carrying it the wrong way. seen as: carrier time long, distance to the goal not shrinking.
- **B-35** Not returning or guarding its own dropped flag; not chasing the enemy carrier. seen as: own flag dropped long, no hunter on the carrier.
- **B-36** Not standing inside the hill or territory long enough to score, or loitering just outside it. seen as: objective goal with distance to the zone above its radius.
- **B-37** Invasion: attackers not pushing the phase, defenders not holding it, nobody picking up the core, bots on the wrong side of a phase. seen as: phase stuck, core idle, bots far from the phase's zones.
- **B-38** Throwing the objective: dropping the ball, switching weapons while carrying, leaving the hill to chase kills. seen as: carrier loses the item with no enemy near.

## Team play
- **B-39** No teamwork: every bot alone, no trading shots, no covering the carrier, no flanks set up. seen as: bots far apart in fights, no escort near the carrier.
- **B-40** Style not played: snipers not taking high sightlines or repositioning, rushers not rushing, campers moving everywhere. seen as: time by goal not matching the personality.
- **B-41** Everyone in one place (the whole team on one flank) or the whole team defending. seen as: all bots within a small area, no attackers.
- **B-42** Ignoring the director's orders or the person's honk / calls for long. seen as: order role never reached, goal unrelated to the order.

## Vehicles
- **B-43** Never getting in vehicles, or walking past a free Warthog on a long trip. seen as: no vehicle goals with vehicles nearby, long foot trips.
- **B-44** Driving badly: into walls, off cliffs, in circles, leaving the gunner behind, ignoring a carrier to ferry. seen as: vehicle stuck, driver alone with a gun seat empty.
- **B-45** Gunner not shooting, or a passenger seat taken from an objective holder. seen as: gunner seat with zero presses in fights.

## Difficulty feel
- **B-46** Too botty: robotic precision, perfect reactions, the same behaviour every time, no hesitation. seen as: identical timings, instant reactions at every tier.
- **B-47** Too stupid for the tier: Legendary bots making Easy mistakes (walking into fire, ignoring the objective, no power weapons). seen as: Legendary stats near Easy's.
- **B-48** Camping its own spawn or an odd corner all match out of a fight. seen as: camp hits far from any post.

## Fluidity
- **B-49** Walking blind: moving out of a fight while looking far away from where it walks (not strafing). seen as: walk_blind hits, walking blind share well above the real player's.
- **B-50** Aimbot snaps: turning tens of degrees in one tick, or a view that freezes and then jumps. seen as: snap_turn and view_freeze hits.
- **B-51** Firing far out of the gun's range: an assault rifle across the map is a waste of ammo (a short deterrent burst back at a man shooting it is fine). seen as: out_of_range hits, firing out of range share above the real player's.
- **B-52** Shot and not answering: losing shields without turning to fight or moving to cover. seen as: ignored_hit hits.
- **B-53** Too much standing still compared to a real player. seen as: standing still share far above the real player's (about 13%).
- **B-54** Never jumping or throwing grenades compared to a real player (Easy never jumps, on purpose). seen as: jumps and grenades a minute far below the real player's.
- **B-55** The whole team heading the same way by the same route every life: no variety in where bots go. seen as: every bot of a team on one path, the same way out of spawn every life.
- **B-56** Wrong target: aiming at one man while another visible enemy is shooting it and is the real threat. seen as: a bot dies to a man it never turned to.
- **B-57** Several bots freezing at once: views fixed and walking on in a straight line for a second or more, as if their inputs stopped. seen as: view_freeze hits on several bots at the same moment.
- **B-58** Loitering on the map's lowest floor (a pit, a basement) while the fights and power positions are above. seen as: far more time on the lowest floor than the real player.
- **B-59** Recharging in cover while facing the wall, not the way the enemy would come. seen as: retreat goal, standing still, view into a wall.
- **B-60** A Heroic or Legendary bot not juking while a man has it in his sights: straight-line strafes, no crouch or jump. seen as: few strafe changes and no crouch in fights against the real player.
- **B-61** Changing its mind every moment: the goal flipping between two things (a fight and an item, two men to hunt) several times a second, getting nowhere and not shooting. seen as: goal changes many times a minute, hunt targets jumping between men.
- **B-62** Swapping weapons back and forth on the same spot. seen as: the same two guns traded several times within seconds.
- **B-64** Misusing a sword or hammer: holding it out against a man far away or on another floor, strafing instead of closing in, never lunging. seen as: sword in hand with the target past 4 units, few lunges, sword users dying without kills.
- **B-63** Walking past a clearly better gun, a battle rifle with only an assault rifle in hand; skipping a spiker or needler is fine. seen as: one gun carried most of the match while better guns lie around.
