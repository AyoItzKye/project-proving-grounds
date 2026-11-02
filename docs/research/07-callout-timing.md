# 07 - Callout timing: how fast real players call, and a latency model for the team director

Date: 2026-10-21. For: `brain/director.py` and `brain/callouts.py` (`VoiceChannel`, `TIMING`). Replaces the flat "0.5 to 2.5 s after the report" rule in `docs/BRAIN-DESIGN.md`.

Method: psycholinguistics papers, esports and FPS communication studies, coaching guides, shipped game AI source code (Counter-Strike bot, Quake III, Source/Half-Life 2), GDC material, and Bungie's own Halo 3 AI dialogue tables read from the locally installed Halo 3 Editing Kit. Every non-obvious number carries a source tag like [S11]; the URLs are in section 8. **UNVERIFIED** marks anything not confirmed from a primary source. **Design** marks a number I chose to fit the evidence; nobody measured it.

Headline: no study has measured "enemy seen to callout spoken" in any FPS (section 6). The model below is therefore built bottom-up from measured human stage times (word production, speaking rate, turn gaps, word recognition), checked against the one published FPS callout corpus (Tang et al., Halo 3 / TF2 / CS tournament finals [S11]) and against what Bungie's Halo 3 AI does [S37].

---

## 0. Recommended model (summary)

### 0.1 Stages and per-tier numbers

All times in seconds. "Recognition" is the bot's existing perception event (the moment `report()` is called). Lognormal: value = median x exp(N(0, sigma)).

| Stage | Novice | Average | Strong | Top | Evidence |
|---|---|---|---|---|---|
| 0. Recognize (bot perception, first visible to recognized). Unchanged | 0.45 | 0.30 | 0.22 | 0.18 | `BRAIN-DESIGN.md` |
| 1. Calls a fresh sighting at all, when not fighting (probability) | 0.40 | 0.65 | 0.85 | 0.95 | Design, anchored on [S11] [S12] [S37] |
| 2. `decide`: pick the message (count, zone, state); median / sigma | 0.45 / 0.40 | 0.25 / 0.35 | 0.15 / 0.30 | 0.10 / 0.25 | [S1] [S2] [S30] [S37]; tier split is design |
| 3. `onset`: word retrieval to first sound; median / sigma | 0.75 / 0.20 | 0.55 / 0.20 | 0.43 / 0.20 | 0.38 / 0.20 | [S1] [S2] [S4] |
| = speech start after recognition (median) | 1.20 | 0.80 | 0.58 | 0.48 | sum of 2 and 3 |
| = speech start after first sight (median) | 1.65 | 1.10 | 0.80 | 0.66 | human anchors: practised picture name 0.60 [S1]; unprimed name over 1.0 [S2]; describing a scene 1.5 [S2] |
| 4. Urgent pre-loaded word ("Flag!", "Grenade!", "Behind you!"): speech start after recognition, median (sigma 0.20) | 0.55 | 0.40 | 0.32 | 0.28 | prepared vocal response 0.215 s [S3]; Halo 3 AI warnings pre-delay 0.15 to 0.5 s [S37] |
| Hard floor: any speech start after recognition | 0.22 | 0.22 | 0.22 | 0.22 | prepared responses rarely under 0.20 s [S3] |
| 5. `rate`: syllables per second, calm (sigma 0.10). Urgent x1.15, cap 7.5 | 4.5 | 5.0 | 5.5 | 6.0 | spontaneous English 4.96 [S6]; intended-fast 5.5 to 6.8 [S8]; experts +29% words/s [S12] |
| Typical callout length, syllables | 6 to 10 | 4 to 8 | 4 to 6 | 3 to 5 | most expert callouts 8 words or fewer [S11]; 3 s max [S18]; split is design |
| 6. `hear`: after the key words end, until a teammate has understood. +0.15 if that listener is fighting | 0.30 | 0.25 | 0.20 | 0.15 | word recognized about 0.2 s after its onset, often before its end [S24]; auditory RT 0.14 to 0.16 [S23] |
| 7a. Busy speaker (in a duel): call dropped (`busy_skip`) | 0.50 | 0.30 | 0.15 | 0.05 | [S11] [S18] [S25] |
| 7b. Busy: extra delay before speaking (lognormal median, clamp 0.2 to 1.0); says the coarse area name | 0.40 | 0.40 | 0.40 | 0.40 | dual-task cost about 0.25 s [S26]; [S11] |
| 8. Dead speaker: says killer zone and state (probability); speech start after death (median) | 0.25; 1.0 | 0.50; 0.7 | 0.75; 0.5 | 0.90; 0.4 | dead players call more [S11]; "make the callout first" [S20]; design |

Worked example, from first sight of two enemies at Red tele, call "Red tele, two" (4 syllables, key words "Red tele" = 3), speaker free, medians:

| | Novice | Average | Strong | Top |
|---|---|---|---|---|
| Speech starts | 1.65 | 1.10 | 0.80 | 0.66 |
| Teammates understand | 2.62 | 1.95 | 1.55 | 1.31 |
| Same call while the speaker is fighting | 3.02 | 2.35 | 1.95 | 1.71 |
| Urgent "Flag going left lift" (5 syllables, all key) understood | 2.27 | 1.82 | 1.53 | 1.33 |

Old model for comparison: understood at recognition + uniform(0.5, 2.5), the same for every tier. For a top bot that is 0.68 to 2.68 s after first sight (mean 1.68). The new top tier is faster on average and loses the 2.5 s tail; the new novice is slower, wordier and often silent. That is the shape the player asked for: as fast as skilled players, still bounded by human stage times.

### 0.2 One shared voice channel per team

| Rule | Value | Evidence |
|---|---|---|
| One speaker at a time; others queue | yes | CS bots [S31]; Source "talk semaphore" [S33]; "one voice per event" [S18]; 95% of conversation is one speaker [S2] |
| Gap before the next speaker starts | lognormal median 0.25 s, floor 0.20 s (urgent cut-in: none) | modal turn gap about 0.2 s [S2]; reaction to a speech offset 0.283 s [S3] |
| Same speaker's own next call | at least 0.5 s (strong, top), 1.0 s (average, novice) | Design; Halo 3 AI uses 2.5 to 5 s "post voc. delay" for barks [S37], expert humans chain faster [S11] |
| Priority classes | P0 urgent > P1 contact > P2 tactical > P3 social | Halo 3 priority enum [S37]; CS "important" statements [S31] |
| What each class holds | P0: flag carrier position and direction, flag dropped where, grenade at a teammate, enemy behind a teammate. P1: new count + zone, damage state ("one shot"), power weapon or power-up holder. P2: lost contact, pushing, rotating, clear. P3: acks, praise, trash talk | coaching guides [S18] [S19] [S20]; Halo vocabulary in doc 05 |
| Preemption | P0 cuts a P2 or P3 call at once. P1 waits for the current call. A cut P1 call is re-queued if still fresh | Halo 3 flags "immediate" and "cancel low priority" [S37] |
| Drop if not started within (from the event) | P0 1.5; P1 sighting 2.0 (current 2.5 is acceptable); damage state 1.5; lost contact 1.0; power weapon or vehicle 5.0; P3 1.0 | Halo 3 "allowable queue delay" 0.25 to 5 s [S37]; info stale "within a few short seconds" [S11] |
| Merge while queued (same kind and zone) | count = union of enemies | CS `IsRedundant` [S31] |
| "Covered" (same kind and zone said recently) | 4 s, unless the count rose or the state changed; then a short update ("three now", "he's one shot") | CS place repeat 20 s [S31]; Halo 3 AI repeat 10 to 30 s for sightings [S37]; design for faster human updates |
| Urgent repeat of the same zone | 1.5 s; a P0 call may double its key word ("Flag, flag!") with probability 0.3 | repetition 13.7% of Halo 3 expert callouts [S11]; design |
| Subject cooldowns | grenade warning 5 s; "has sniper"/power-weapon holder 20 s unless the zone changed; social 15 s | Halo 3 AI: grenade 5 s, sniper 150 s, praise 15 s [S37]; HL2 15 to 30 s [S33] |
| Replies and acks | at most one teammate replies (each with chance 1/(N-1)); one word; skipped 50% | Quake III [S32]; Halo 3 replies skipped 50 to 75% [S37]; "affirmation is one word" [S18] |
| Channel occupancy cap | at most 60% talk time in any 20 s window; above it drop P3, then P2 | busiest US approach-control radio is 62% occupied [S28]; "about 60 s of single-speaker info per 100 s round" [S18] |
| Content | read from the speaker's beliefs at speech start, never ground truth at queue time | L4D queries a line when it is spoken [S34]; CS notes reports "could be a few seconds out of date" [S31] |
| Team rate sanity check | top teams 15 to 25 calls/min; average 8 to 15; novice 3 to 8 | Halo 3 expert finals 25.5 phrases/min [S11]; lower tiers are design |

Anti-psychic invariants (assert these in the sim):
1. speech start >= recognition + 0.22 s.
2. teammate understanding >= speech start + time to say the key words + 0.10 s.
3. A call contains only what the speaker perceived; count >= 4 is said as "four plus" or fuzzed (subitizing limit, section 1.7).
4. A dead speaker only reports what it saw before dying (killer zone, damage dealt), once [S18] [S11].

### 0.3 Mapping onto `brain/callouts.py`

| Constant | Current | Recommended |
|---|---|---|
| `TIMING[*].decide` (novice / average / strong / top) | 0.35 / 0.22 / 0.14 / 0.08, sigma 0.25 | 0.45 / 0.25 / 0.15 / 0.10, sigma 0.40 / 0.35 / 0.30 / 0.25 |
| `TIMING[*].onset` | 0.62 / 0.52 / 0.45 / 0.38 | 0.75 / 0.55 / 0.43 / 0.38 (sigma 0.20, keep) |
| `TIMING[*].rate` | 4.5 / 5.0 / 5.5 / 6.0 | keep; add urgent x1.15, cap 7.5 |
| `TIMING[*].hear` | 0.30 / 0.25 / 0.22 / 0.20 | 0.30 / 0.25 / 0.20 / 0.15, use the listener's tier, +0.15 if the listener is fighting |
| `TIMING[*].busy_skip` | 0.45 / 0.30 / 0.15 / 0.05 | 0.50 / 0.30 / 0.15 / 0.05 |
| `BUSY_EXTRA` | 0.35 fixed | lognormal median 0.40, clamp 0.2 to 1.0; busy calls use the coarse `area` zone |
| `STALE_AFTER` | 2.5 for all non-urgent | per kind: sighting 2.0, damage 1.5, lost 1.0, weapon or vehicle 5.0, social 1.0 |
| `MERGE_WINDOW` | 3.0 | 4.0, but let a changed count or state through as an update |
| `URGENT_REPEAT` | 1.5 | keep |
| `ANNOUNCER` | 0.6 | keep until measured; better: end of the announcer's key word + listener `hear` (**UNVERIFIED**) |
| new | none | `P_CALL_FREE`, `URGENT_START`, `START_FLOOR = 0.22`, `TURN_GAP` (0.25, floor 0.20), `SELF_GAP`, `DEAD_CALL`, occupancy cap, re-queue cut P1 calls |

Implementation notes from reading the current code: (a) `hear` is taken from the speaker's tier; it belongs to the listener. (b) The next queued call can start the same tick the previous one ends; humans leave about 0.2 s [S2] [S3]. (c) A call cut by urgent news is lost; humans restart P1 information. None of these is a bug in the sense of a crash; they are realism gaps.

---

## 1. Speech production latency (speaker side)

### 1.1 Stages of saying a word after seeing something

Indefrey and Levelt's 2004 meta-analysis, updated by Indefrey in 2011 [S1] (table reproduced in [S2]):

| Stage | 2004 estimate | 2011 update |
|---|---|---|
| Conceptual preparation (picture onset to target concept) | 0 to 175 ms | 0 to 200+ ms |
| Lemma retrieval | 175 to 250 ms (75 ms) | from 200 ms, 75 ms (upper bound) |
| Phonological code retrieval | 250 to 330 ms (80 ms) | from 275 ms (upper bound) |
| Syllabification | 330 to 455 ms (25 ms per phoneme) | from 355 ms; 20 ms per phoneme, 50 to 55 ms per syllable |
| Phonetic encoding to articulation | 455 to 600 ms (145 ms) | from 455 ms (upper bound) |
| Articulation starts | 600 ms | 600 ms |

Key caveats from [S1]:
- The 600 ms figure comes from **repeated naming of the same pictures**, i.e. practised names.
- Reported naming latencies across recent studies range from 470 ms to over 2000 ms, depending on task, picture, familiarity, name length and frequency.
- Phonetic encoding can begin as soon as the **first syllable** is encoded, so speech can start before a long name is fully planned.

Longer messages and unpractised names, as summarised in [S2]:
- Unprimed picture naming (Bates et al. 2003): averages above 1000 ms in seven languages, with every language's minimum above 650 ms.
- Two nouns: 740 to 800 ms before speech starts. Three-word utterances: 900 ms (Schnur et al. 2006).
- A simple sentence describing a scene ("boy kicking ball"): about 1500 ms (Griffin and Bock 2000).
- Planning runs 600 to 1200 ms or more before articulation, depending on ease of retrieval and length.
- Pre-articulation processes run 3 to 4 times faster than articulation itself (Wheeldon and Levelt 1995).

Mapping to the bot: the bot's recognition (0.18 to 0.45 s) covers roughly the conceptual-preparation stage. What remains for a practised one-word name is about 0.40 s of lemma, form and phonetic encoding (75 + 80 + 100 to 125 + 145 ms [S1]). That is the top-tier `onset` (0.38 s). Multiword and unpractised calls add the 140 to 300 ms seen for two and three words and the 400+ ms seen for unprimed names [S2]; that is where the average and novice values come from.

### 1.2 Pre-loaded responses (the floor)

Torreira and Bögels (2022): 23 speakers said a prepared "ja" as fast as possible. Responses to a tone onset averaged **215 ms**; responses to the end of speech-like sounds without final prosodic cues averaged **283 ms**, and fewer than 3% were under 200 ms [S3]. A fully prepared word ("Flag!") can therefore start about 0.2 to 0.3 s after its trigger, and not faster. Coaching guides tell players to do exactly this: "Pre-load the call in your head before you press the voice key" [S18]. This sets the urgent class and the 0.22 s floor.

### 1.3 Name frequency, familiarity, practice (why map names are fast for experts)

- Naming time tracks how common a name is (Oldfield and Wingfield 1965, a reciprocal relation with log frequency) [S5]. The millisecond size of the effect was not found in an accessible source (**UNVERIFIED**; usually described as tens of ms).
- Repetition removes it. Corps and Meyer (2023) found a strong frequency effect on the first presentation of a picture and much weaker effects on the second and third [S4]. Three naming rounds removed it within a session, though it came back after a week (Decuyper, Corps and Meyer 2025) [S4]. Six repetitions removed it for up to two weeks (Corps and Meyer 2026) [S4] (abstracts only).
- The 600 ms practised-naming figure is itself a repetition figure [S1].
- Consequence: a regular who says "Red tele" dozens of times a match retrieves it at practised speed. A novice either lacks the shared name ("You just make them up, unless they have a label" [S11]) or uses a description such as "the place where I died last round", which costs the speaker planning time and the listener "a beat of decoding every time" [S18].

### 1.4 Word length

- Syllabification costs about 20 ms per phoneme or 50 to 55 ms per syllable, but articulation can start after the first syllable [S1]. Long names therefore cost mostly **saying time**, not start time.
- Longer phrases are spoken at a faster syllable rate (anticipatory shortening) [S6].
- Model: length enters through `syllables / rate`, not through `onset`.

### 1.5 Speaking rate

| Measure | Value | Source |
|---|---|---|
| Spontaneous American English, 192 speakers, interpausal phrases of 5+ syllables (pauses excluded) | mean 4.96 syll/s (SD 0.60); men 5.09, women 4.92; Wisconsin 5.21, North Carolina 4.80; peaks in the mid-40s | [S6] |
| Same speakers reading isolated 7-syllable sentences | 3.20 syll/s (careful reading) | [S6] |
| Read text, 17 languages, 170 speakers (pauses over 150 ms excluded) | mean 6.63 syll/s (SD 1.15); slowest speaker about 4.3, fastest about 9.1 | [S7] |
| English in the 2011 seven-language study | 6.19 syll/s (secondary report) | [S9] |
| Intended "fast" vs "normal" reading, 3 German speakers | fast: speaking rate 5.54 to 6.75, articulation 6.06 to 7.43; normal: 4.33 to 4.98 and 4.81 to 5.68 | [S8] |
| "About an average of seven syllables per second" | quoted average | [S2] |
| Expert vs nonexpert CS:GO teams (between rounds) | experts 29.39% more words per second | [S12] |
| Maximum syllable repetition | 8 to 9 syll/s for a few seconds, about 6 sustained (Lenneberg 1967, secondhand, **UNVERIFIED**) | [S10] |
| Emotional arousal | anger and happiness usually faster, sadness slower, but studies conflict; no reliable syll/s figure found (**UNVERIFIED**) | none |

Model: calm rates 4.5 (novice) to 6.0 (top) syll/s sit between spontaneous speech (4.96 [S6]) and intended-fast speech (5.5 to 6.8 [S8]); the top/novice ratio 1.33 matches the expert +29% [S12]. Urgent x1.15 keeps the top tier at 6.9, inside the intended-fast articulation range (up to 7.43 [S8]); cap 7.5 stays below sustained maximum performance.

Time to say typical callouts (articulation only):

| Callout | Syllables | 4.5 syll/s | 5.0 | 6.0 | 7.0 |
|---|---|---|---|---|---|
| "Flag!" | 1 | 0.22 s | 0.20 | 0.17 | 0.14 |
| "One shot!" | 2 | 0.44 | 0.40 | 0.33 | 0.29 |
| "Red tele, two" | 4 | 0.89 | 0.80 | 0.67 | 0.57 |
| "Sniper's on BR tower" | 7 | 1.56 | 1.40 | 1.17 | 1.00 |
| "Flag carrier going left lift" | 8 | 1.78 | 1.60 | 1.33 | 1.14 |
| (novice style) | 13 | 2.89 | 2.60 | 2.17 | 1.86 |

Coaching cap: "Three seconds of speech, maximum" [S18].

### 1.6 Turn-taking (sets the gap between speakers)

From the review in [S2]:
- Gaps between speakers peak at about 200 ms. Between 70 and 82% of transitions are under 500 ms (Heldner and Edlund 2010). English mean floor-transfer offset 236 ms (Stivers et al. 2009).
- Overlap is rare and short: 3.8% of the signal was simultaneous speech; 30.1% of floor transfers overlapped, but with a modal overlap of 96 ms and a median of 205 ms; 73% of sampled overlaps involved a backchannel ("yeah", "mm hm").
- 200 ms gaps are possible only because listeners predict where a turn will end; a pure reaction to silence takes about 283 ms [S3].

Model: `TURN_GAP` median 0.25 s, floor 0.20 s, no planned overlap except urgent cut-ins.

### 1.7 Counting ("how many")

- Small sets (up to about 3 to 4) are enumerated at about 40 to 100 ms per item; beyond that, counting costs about 250 to 350 ms per item [S30]. Trick, Enns and Brodeur (1996) measured 250 to 300 ms per item, with the fast range holding for about 3 to 5 items in most adults [S30].
- CS bots wait up to 2 s to accumulate the enemy count before saying it, and say it immediately if more than 3 enemies are visible [S31].
- Model: the count is what the speaker has recognized by speech start (merging handles the accumulation). Counts of 1 to 3 cost nothing extra. Counts of 4 or more are either said as "four plus" or cost 0.3 s per extra enemy to be exact (design).

---

## 2. Esports and competitive FPS communication

### 2.1 The one FPS callout corpus with rates: Tang et al. 2012 (Halo 3, TF2, CS)

Tang, Massey, Wong, Reilly and Edwards recorded team voice channels at two local tournaments, analysing the final stages (the most successful teams), 49 players, plus a 24-response survey [S11].

| | Halo 3 | TF2 | CS |
|---|---|---|---|
| Minutes recorded | 68:49 | 82:08 | 212:23 |
| Callout rate (phrases per minute) | **25.5** | 10.5 | 16.2 |

Halo 3 experts produced one callout phrase every 2.35 s on average. At 0.8 s per phrase that is about 34% channel occupancy, which fits under the 60% cap in section 0.2.

Category shares, decoded from the PDF text layer [S11]. The row mapping follows the label order and fits the paper's own text (TF2 relative directions, scouting), but was not checked against the rendered table (**UNVERIFIED** mapping):

| Code | Halo 3 | TF2 | CS |
|---|---|---|---|
| Directive | 28.4% | 23.6% | 23.7% |
| About self | 27.5% | 20.4% | 38.7% |
| About enemy | 12.7% | 32.5% | 13.7% |
| Question | 5.9% | 5.1% | 3.2% |
| Confirmation | 9.8% | 1.9% | 1.1% |
| Location, general ("left") | 2.9% | 19.1% | 3.0% |
| Location, specific ("sewer") | 39.2% | 11.5% | 43.5% |
| Urgent, temporal | 13.7% | 7.6% | 11.3% |
| Urgent, enemy | 16.7% | 15.9% | 20.4% |
| Repeated | 13.7% | 26.1% | 15.1% |

Findings stated in the text [S11]:
- "Most call-outs are 8 words or fewer."
- "Most information is out of date within a few short seconds."
- Experts overwhelmingly use **named locations**: common references that work wherever the listener is.
- Producing correct callouts is hard under duress (navigating or fighting). Many such callouts were unintelligible, and one player hesitated and repaired mid-call. One player:
- **Dead players** freed from playing "become more involved in providing call-outs".
- Repetition is common, for three reasons: voice software can drop the first milliseconds, repetition conveys urgency, and it gives listeners a second chance.
- The vast majority of utterances push information (anticipation) rather than ask for it.

### 2.2 Experts talk more, and faster

Eldadi and Tenenbaum (2025, CS:GO, about 1,052 between-round statements, 4 expert vs 4 nonexpert teams): experts communicated 34.63% more often and had a 29.39% higher word count per second. Who did the talking did not differ [S12] (abstract).

### 2.3 Other studies (qualitative or abstract-level)

- Rusk, Ståhl and Taylor 2024; Rusk, Ståhl and Jusslin 2022 (CS:GO, conversation analysis): callouts are precise, well-timed spoken cues in shared map terms, used to build a common picture of enemy positions [S13] [S14] (abstract-level; full texts not accessible).
- Drenthe 2016 (two professional CS:GO teams): interrupting, talking over others and very fast speech shaped how informal roles formed [S16] (abstract).
- Vinot and Perez 2024 (League of Legends, coach interviews): the two problems coaches name are **duplicate communications** (the same idea several times in a short period) and **parasite communications** (unclear or irrelevant) [S15].
- A 2024 University of Twente essay (2 LoL teams, 38 h): the higher-performing side overlapped more and left fewer silences; the losing side talked less at key moments. Two teams only, directional [S17] (abstract).

### 2.4 Coaching rules (consistent across sources)

- Guild Order (Valorant) [S18]:
  - "Default to silence": the first second of a mid-round contact is listening.
  - "One voice per event"; the first voice owns it, others add only new info.
  - Grammar "[count] [location] [state]"; "Three seconds of speech, maximum. Pre-load the call in your head."
  - Confirm with one word.
  - "Do not narrate your peek, do not call your own duel"; call after it resolves.
  - A round has about 60 s of single-speaker info in about 100 s of play.
  - Ranked comms are about 70% information, 10% calls, 5% reads and 15% noise; competitive teams move toward 50/30 and near-zero noise.
  - "When you die, you stop talking."
- MetaBot (Valorant) [S19]: every call answers "who, where, and how much, in that order"; "'Two mid' said early beats a perfect description said late"; damage state ("one low", "cracked") is the most under-used, highest-value word; go quiet in a clutch.
- ProSettings (CS2) [S20]: say actual callouts, not "left" or "in your back" ("that location depends on where the listener is facing"); most important info first; "When you die, make the callout first"; never state a guess as fact; be quiet during clutches.
- Halo 5 (Prima guide, via search excerpt; page not opened) [S21]: every multiplayer map has fixed area names shown under the motion tracker; good calls name the threat and its location ("Sniper Rifle at Tower Two"); short calls matter most when voices collide.

### 2.5 Why maps get short, unique callout names

1. **Frame independence.** A named location means the same to every teammate; "left" depends on the listener's facing and on who is addressed [S20] [S11].
2. **Air time.** At 5 to 6 syll/s every syllable costs about 0.17 to 0.2 s of a channel that only one person can use [S6] [S7]. A 3-syllable name instead of a 10-syllable description returns about 1.2 to 1.5 s to the team.
3. **Speaker speed.** Shared names become practised words, retrieved at practised speed ([S1] [S4], section 1.3).
4. **Listener speed.** Spoken words are recognized at about 200 ms after onset, often before they end ([S24], section 3.2). A name whose first syllable differs from every other name on the map is recognized soonest. Design advice for `callouts.json`: avoid zone names that start alike (cohort-model inference, not tested).
5. **Standardization spreads.** Names come from distinctive landmarks, from hearing others, and from forum maps and screenshots [S11]; later Halo titles print them on the HUD [S21].

---

## 3. Listener side

### 3.1 Hearing and reacting

- Average simple reaction time: auditory 140 to 160 ms, visual 180 to 200 ms (Kosinski's review, via BioNumbers) [S23]. Acting on a callout is a choice reaction and slower; the bots' existing perception model can treat a heard callout like a sighting with about 0.8 x the visual reaction time (design, from the ratio in [S23]).

### 3.2 Understanding a short spoken call

- In connected speech, words are recognized about 200 ms after word onset, for short and long words (Marslen-Wilson 1985, via van Heuven and Hagman; secondary) [S24]. Gating studies show most words are identified before their acoustic end [S24].
- People can comprehend speech at 3 to 4 times the speed they produce it [S2].
- Bungie's Halo 3 AI has a field for this, "notification delay": (0.25 s for the lines that use it) [S37].
- Model: a teammate has the information `hear` = 0.15 to 0.30 s after the key words end (`key_part()` in `callouts.py`). With "[zone], [count]" or "[count] [zone]" ordering, that is before the whole call ends.

### 3.3 Talking costs the talker

- Boiteau et al. (2014): people tracking a moving target while conversing tracked worse while talking than while listening. The disruption rose at the start of speaking segments, which the authors attribute to planning and monitoring speech [S25].
- Caird et al. (2008), 33 studies: phone conversation slowed driving reaction by about 0.25 s on average, hands-free about the same [S26].
- Model: busy speakers defer (7b) or drop (7a) calls. Optionally, a speaking bot gets a small aim or reaction penalty for the call's duration (+0.1 s reaction; magnitude **UNVERIFIED**, driving is not shooting).

### 3.4 Overlap and congestion

- Brungart (2001): with two simultaneous talkers, informational masking dominates. The same voice as competitor is worst, a different same-sex voice is better, an opposite-sex voice is best [S27]. A later summary puts each step at about 15 to 20 percentage points (secondary, **UNVERIFIED** at any specific level).
- Busiest US approach-control radio (Prinzo and McClellan 2005, about 8,000 transmissions): average transmission 2,849 ms (setup 81, voice 2,568, pauses 127, propagation 73 ms), separated by 1,736 ms of silence. Blocked, stepped-on and clipped transmissions together were only 1.16% [S28]. That is a professional, disciplined shared channel running at about 62% occupancy.
- Clipping of the first word happens both on radio (transmission started before setup completes) [S28] and in game voice software [S11].
- Model: serialize the channel, keep it under about 60% occupancy, and do not simulate overlap except an urgent cut-in.

### 3.5 Network voice delay

ITU-T G.114: mouth-to-ear delay under 150 ms is preferred, 150 to 400 ms is usable with growing impairment, and over 400 ms is unacceptable [S29]. Bots share one process, so this is zero for bot-to-bot callouts. If callouts are voiced to a human through text-to-speech, use the real clip length and add the engine's start latency instead of `syllables / rate`.

---

## 4. Game AI precedent

### 4.1 Counter-Strike bot chatter (Valve, Michael Booth) [S31]

From `cs_bot_chatter.cpp/.h` and `cs_bot_radio.cpp` (ReGameDLL_CS, which preserves Valve's code and comments):
- **One speaker per team.** `GetActiveStatement()` scans all teammates' statements. If one is being spoken, it blocks everyone; otherwise the statement that has waited longest goes next, once its start time arrives.
- **Verbosity levels.** OFF, MINIMAL (only "important", mission-critical statements), NORMAL. Dead bots add no statements unless forced.
- **Redundancy.** A new statement is dropped if the bot is already waiting to say one of the same type about the same place or subject.
- **Lifetimes** (statement expires if not said): visible enemies 10 s; most information 10 s; enemy action 3 s; acknowledge 3 s; enemies remaining 5 s; emotes 1 to 15 s; killed-friend 2 s; friendly-fire 1 s.
- **Counting.** "Enemy spotted" says the place, then waits up to 2.0 s to accumulate the count (immediately if more than 3 enemies are visible). It is valid only while the bot is attacking.
- **Place repeat.** A place name is not said again if any teammate said it within 20 s.
- **"Me too."** The same plan at the same place becomes "me too" after 0.5 to 1.0 s; the same plan at a different place waits 3 to 4 s for others.
- **Phrasing.** Phrases inside one statement are separated by 0.1 s; a radio command occupies 2.0 s.
- **When to talk.** Bots stay silent if every remaining friend is nearby ("everyone is together"). After 30 s of radio silence they ask for a report-in. Sniper warnings have a 60 s cooldown; noise reports a 20 s timer with a 33% chance.
- **Death.** A bot that dies mid-sentence emits a pain gargle and its queued statements are removed.
- **Radio replies** wait `1 + 2 x ReactionTime` s, i.e. 1.4 to 1.8 s for 0.2 to 0.4 s profiles (profile values per doc 01, community-sourced).

### 4.2 Quake III Arena (id Software) [S32]

- Team replies are scheduled at `FloatTime() + 2 * random()`, uniform 0 to 2 s (`ai_cmd.c`, `ai_dmq3.c`).
- **Dedupe of responders:** for a message not addressed to one bot, each teammate returns early with chance `random() > 1/(N-1)`, so on average one teammate reacts (`ai_cmd.c`: "make sure not everyone reacts to this message").
- `BotChatTime()` returns a constant 2.0 s; a typing-speed formula based on the `CHAT_CPM` characteristic (1 to 4000 characters per minute) is commented out (`ai_chat.c`, `chars.h`).
- Team-leader election waits 5 + 10 x random() s; leaders re-issue orders about every 120 s (`ai_team.c`).

### 4.3 Source engine / Half-Life 2 [S33]

- A global `g_AIFriendliesTalkSemaphore` (and one for foes): an ally that speaks acquires it for the line's duration plus delay, and other allies cannot speak until it is released (`ai_speech.cpp/.h`).
- Three cooldown levels per speech concept (`ai_playerally.cpp/.h`): global category delay, personal category delay, per-concept delay. Examples: idle category 10 to 20 s global; "hello" 5 to 10 s; "ally killed" 15 to 30 s; "player pushing me" 15 to 30 s; "player reload" 60 s. Flags `AICF_SPEAK_ONCE` and `AICF_PROPAGATE_SPOKEN` (once one ally says it, it counts as said for all). Responses carry an `odds` percentage and a `delay`.

### 4.4 Left 4 Dead (Elan Ruskin, GDC 2012) [S34]

- Bots "call out things like weapon caches, as if they were humans"; the same context-triggered speech was then given to human-controlled characters.
- Follow-up lines are looked up **when the previous line finishes**, not when it starts: "The situation may have changed during the time it took the first line to be said." A conversation self-terminates when its criteria fail (a zombie attacks mid-chat), so no explicit interruption system is needed.
- Memory facts can carry automatic expiry ("Nick is speaking for the next few seconds") to keep lines from playing too close together.
- Follow-ups can be broadcast to everyone within earshot, and the best reply wins. Long monologues are cut into short pieces so they can be abandoned.

### 4.5 F.E.A.R. (Jeff Orkin, GDC 2006) [S35]

- Squad dialogue makes coordination visible:
- Lines are exchanges between characters rather than single announcements. Dialogue also explains inaction.
- No timing numbers are given.

### 4.6 Killzone 3 (Guerrilla) [S36]

Bots report completed orders and observed threats up a commander, squad and individual hierarchy. No voice or callout timing is published.

### 4.7 Halo 3 AI dialogue, Bungie's own data [S37]

Halo 3 shipped its AI vocalization design as spreadsheets inside the official Halo 3 Editing Kit: `data/ai/ai_dialogue_globals.xls` (461 rows, 325 vocalizations, file date 25 Sep 2007, Halo 3's release day) and `data/ai/ai_dialogue_rules.xls` (329 event rules). They were read from the locally installed `H3EK.7z` (section 8). Column headers: VOCALIZATIONS, PRIORITY, SAMPLE, WEIGHT, SKIP %, PLAYER SKIP %, FLOOD SKIP %, MAX COMBAT STATUS, ANIMATION, PERCEPTION, S-FREEZE, L-FREEZE, SPEAKER EMOTION, LISTENER EMOTION, QUEUE DELAY, PRE DELAY, NOTIF. DELAY, POST DELAY, REPEAT DELAY, PERMUTATION REPEAT DELAY, PROXY.

Field meanings, from help strings inside `guerilla.exe`:
- "pre voc. delay: seconds#How long to wait to actually start the vocalization".
- "allowable queue delay: seconds#How long to wait to actually start the vocalization". The help text duplicates pre-delay; read as the maximum time a line may wait in the queue (interpretation, **UNVERIFIED**).
-.
- "post voc. delay: seconds#How long speech is suppressed in the speaking unit after vocalizing".
- "speaker freeze time#speaker won't move for the given amount of time".
- A character "skip fraction modifier": "For vocalization with priority < react, multiplies the skip fraction in the dialogue globals tag."
- Skip fractions use 0 = always, 1 = never (by analogy with the equipment skip help text in the same binary).

Priority enum order visible in the binary: recall < idle_response < postcombat < respond < act < react < involuntary < scream. Other names (warn, status, and so on) are pooled elsewhere in the binary, so their positions are **UNVERIFIED**. Vocalization flags: "immediate" and "cancel low priority". Combat-status gate: uninspected, definite, certain, clear_los, dangerous.

Lines relevant to PvP callouts (queue = allowable queue delay, pre = pre voc. delay, repeat = repeat delay; seconds):

| Line (sample) | Priority | Skip | Queue | Pre | Post | Repeat |
|---|---|---|---|---|---|---|
| hrdfoe "Did you hear that?!" | warn | none listed | 2.0 | 0.5 | none | 15 |
| seefoe "We've got company!" | warn | 0.25 | 2.0 | 0.5 | none | 30 |
| morefoe "There's another one!" | warn | 0.35 | 2.0 | 0.5 | none | 15 |
| foundfoe "Over here!" | warn | 0.25 | 2.0 | 0.5 | none | 10 |
| foundfoe_re "On my way!" (reply) | none | 0.75 | 2.0 | 0.25 | none | 30 |
| warn "Incoming!" / "Grenade!!!" | warn | 0.25 / 0.25 | 1.5 | 0.25 | none | 30 / 5 |
| warn_weapon "Sniper!" | warn | 0.5 | 5.0 | 1.0 | none | 60 (Sniper! 150) |
| warn_chr "Stealth camo!" | warn | 0.2 | 3.0 | 1.0 | none | 300 |
| rmd "Somebody take out that sniper!" | none | 0.25 | 2.5 | none | none | 60 |
| dwn "Sniper down!" | none | 0.75 | 5.0 | 0.75 | none | 60 |
| lst_cntct "Lost contact!" | none | 0.65 | 0.5 | 0.5 | none | 15 |
| ordr_re "Yes sir!" (reply) | none | 0.25 | 1.0 | 0.25 | none | 15 |
| lmnt_deadally "Man down!" | status | 0.5 | 2.0 | 1.25 | 2.5 | 60 |
| scld_plr_hrtme "Hey it's me!" (shot by player) | react | 0.0 | 2.0 | 0.15 | 2.5 | none |
| ok "Ok." / thnk "Thanks." | none | 0.0 | 0.25 | 0.25 | none | 0 |
| prs "Good job!" | status | 0.5 | 2.25 | 1.25 | none | 15 |
| rtrt_ldrdead "Leader dead run away!" | warn | 0.5 | none | none | none | 10 |

Distributions across all 325 vocalizations:
- SKIP % most often 0.25 (71 rows) or 0.5 (54).
- PRE DELAY mostly 0.25 to 1.0 s.
- QUEUE DELAY mostly 1 to 2.5 s (up to 5).
- POST DELAY 2.5 to 5 s.
- REPEAT DELAY mostly 15, 30 or 60 s (up to 600).

The rules sheet maps game events to who speaks by role (cause, subject, enemy, friend) and gates on combat status, danger level and damage type. Example: an enemy of the dead sniper says "Sniper down!".

Cross-check: Griesemer and Butcher's GDC 2002 deck says Grunts shout "Leader dead, run" about half the time [S38]; the table's skip fraction for that line is 0.5.

What to take from it: Bungie's AI deliberately (a) skips 25 to 50% of informative lines, (b) waits 0.25 to 1.25 s before speaking, (c) drops lines it cannot start within 0.25 to 5 s, (d) rate-limits each speaker and each line type, and (e) skips replies more than initiations. These are AI barks designed for players to overhear, so the repeat delays are longer than human comms need; the skip, pre-delay and queue-limit patterns transfer directly.

### 4.8 Later Halo PvP

- Halo 5 printed area names under the motion tracker [S21].
- Halo Infinite has a "Spartan Chatter" toggle for automatic character callouts. Halo Waypoint's recommended competitive settings reportedly advise leaving it on because it can reveal opponents (via search excerpts; the page returned 403, wording **UNVERIFIED**) [S22].
- So automatic, name-based team callouts are an established Halo design, not an invention of this project.

---

## 5. How the recommended numbers were derived

1. **Recognition is upstream.** The bot's perception delay (0.18 to 0.45 s) already covers seeing and identifying the enemy, roughly the conceptual-preparation stage of picture naming [S1]. The callout clock starts there.
2. **`onset`.** For a practised name, the remaining word-production stages total about 0.40 s [S1], hence top 0.38 and strong 0.43. Average adds part of the two-noun cost (+140 to 200 ms [S2]): 0.55. Novice adds the unpractised-name penalty (unprimed naming over 1.0 s versus 0.6 s practised [S2] [S1]): 0.75.
3. **`decide`.** Choosing what to say. For experts this is near-automatic: counts of 1 to 3 are subitized at 40 to 100 ms per item [S30], and the call is pre-loaded [S18]. Novices hesitate and search for a name [S11]. Halo 3's own AI uses 0.25 to 1.25 s pre-delays [S37].
4. **Checks against human totals.** Speech start after first sight: top 0.66 s vs practised naming 0.60 s [S1]; average 1.10 s vs unprimed naming over 1.0 s [S2]; novice 1.65 s vs describing a scene 1.5 s [S2].
5. **Urgent.** A prepared single word starts about 0.215 to 0.283 s after its trigger [S3]; small decision costs are added per tier; floor 0.22 s.
6. **Rates.** Section 1.5.
7. **`hear`.** Words are recognized about 0.2 s after their onset, often before their end [S24]; the post-key-word residual for an attentive expert is about 0.1 to 0.2 s, more for novices or fighting listeners. Bungie's "notification delay" of 0.25 s into a line is consistent [S37].
8. **Busy.** Talking degrades tracking, worst when speech starts [S25]; conversation adds about 0.25 s to reactions [S26]; experts "blurt out the general area" under pressure [S11]; coaches say not to call your own duel [S18]. Hence drop or defer, an extra 0.4 s, and coarse names.
9. **Dead.** Humans give one immediate report after dying, then stop ([S18] [S20]); dead players "become more involved in providing call-outs" [S11]. In Halo the dead period is short, so the model allows exactly one dead call.
10. **Free-call probability (stage 1).** Design. Anchors: Halo 3 AI says "We've got company!" 75% of the time [S37]; experts produce 35% more statements than nonexperts [S12]; ranked players carry about 15% noise and miss calls [S18].
11. **Channel rules.** Section 0.2 cites each.

---

## 6. Gaps and how to calibrate

1. **No measured event-to-callout latency in any FPS** was found (searched esports, CSCW and psychology literature). The model is built from stage times. Calibrate it: take 50 or more events from recorded team-comms videos (Halo or other FPS "mic'd up" footage), and mark the frame the caller's screen first shows the enemy and the audio frame where the call starts. Fit a lognormal per skill level.
2. Halo 3 "allowable queue delay" semantics (its help text duplicates pre-delay) and "player skip fraction" are **UNVERIFIED**. Test in Sapien/H3EK if needed.
3. The exact Brungart two-talker percentages, the millisecond size of name-frequency effects, and emotional speech-rate numbers were not obtained (**UNVERIFIED**).
4. The free-call probabilities, self-gap, dead-call values and team-rate ranges per tier are design values. Tune them in blind clip reviews.
5. Sim acceptance checks for `brain/sim.py`:
   - per-tier median (speech start minus recognition) within 10% of section 0.1;
   - the floor never violated;
   - team calls per minute in the section 0.2 ranges (top teams near Tang's 25.5 when fighting is constant);
   - occupancy at most 60%;
   - stale drops under 15% for top teams;
   - no call ever contains information its speaker did not perceive.

---

## 7. Notes on sources opened vs reported

Opened and read directly: [S1] [S2] [S3] (abstract) [S6] [S7] [S8] [S11] [S12] (abstract) [S15] [S18] [S19] [S20] [S28] (abstract) [S31] [S32] [S33] [S34] [S35] [S36] [S37]. The rest were reported through search excerpts or secondary summaries and are marked as such where used.

---

## 8. Sources

- [S1] Indefrey, P. (2011). The spatial and temporal signatures of word production components: a critical update. Frontiers in Psychology 2:255. https://pmc.ncbi.nlm.nih.gov/articles/PMC3191502/ (original: Indefrey and Levelt 2004, Cognition 92, https://forms.mpi.nl/node/50341)
- [S2] Levinson, S. C. and Torreira, F. (2015). Timing in turn-taking and its implications for processing models of language. Frontiers in Psychology 6:731. https://pmc.ncbi.nlm.nih.gov/articles/PMC4464110/
- [S3] Torreira, F. and Bögels, S. (2022). Vocal reaction times to speech offsets. Journal of Phonetics 94. https://research.tilburguniversity.edu/en/publications/vocal-reaction-times-to-speech-offsets-implications-for-processin/
- [S4] Corps and Meyer (2023), Acta Psychologica 241:104073, abstract: https://doaj.org/article/8896ab7a2208450c8bd4a31f14e70f90 ; Decuyper, Corps and Meyer (2025): https://www.mpi.nl/publications/item3599389/how-stable-are-effects-word-frequency-and-name-agreement-picture-naming ; Corps and Meyer (2026): https://forms.mpi.nl/node/56900 (abstracts only)
- [S5] Oldfield and Wingfield (1965), QJEP 17: https://doi.org/10.1080/17470216508416445 ; Jescheniak and Levelt (1994): https://forms.mpi.nl/node/51506 (abstracts only)
- [S6] Jacewicz, Fox and Wei (2010). Between-speaker and within-speaker variation in speech tempo of American English. JASA. https://pmc.ncbi.nlm.nih.gov/articles/PMC2933259/
- [S7] Coupé, Oh, Dediu and Pellegrino (2019). Different languages, similar encoding efficiency. Science Advances. https://pmc.ncbi.nlm.nih.gov/articles/PMC6984970/
- [S8] Trouvain, J. Phonus 8, chapter 6, Production experiments: effects of tempo (Table 6.1). https://www.coli.uni-saarland.de/~trouvain/Phonus8/06_chapter6.pdf
- [S9] Pellegrino et al. (2011) English 6.19 syll/s, secondary report: https://kottke.org/11/09/the-speed-and-density-of-language
- [S10] Lenneberg (1967) maximum syllable rate, secondhand: https://lists.nottingham.ac.uk/pipermail/reading-hall-of-fame/2009-November/000280.html
- [S11] Tang, Massey, Wong, Reilly and Edwards (2012). Verbal coordination in first person shooter games. CSCW 2012. https://faculty.cc.gatech.edu/~keith/pubs/cscw2012-fps.pdf
- [S12] Eldadi and Tenenbaum (2025). Between-rounds verbal communication in expert and nonexpert esports team players. https://cris.iucc.ac.il/en/publications/between-rounds-verbal-communication-in-expert-and-nonexpert-espor/
- [S13] Rusk, Ståhl and Taylor (2024). Callouts as a coordinating device in a team-based networked FPS. Social Sciences and Humanities Open. https://doaj.org/article/6bbb57da4fa347799c8fea3c4fc4afc8 (via search excerpt)
- [S14] Rusk, Ståhl and Jusslin (2022). Eludamos. https://septentrio.uit.no/index.php/eludamos/article/download/6629/7159/27925 (via search excerpt)
- [S15] Vinot and Perez (2024). Voice communication analysis in esports. https://arxiv.org/html/2411.19793v1
- [S16] Drenthe (2016). Informal roles within eSport teams (CS:GO). https://jyx.jyu.fi/handle/123456789/50122 (abstract)
- [S17] University of Twente essay (2024). Strategic communication in esports. https://essay.utwente.nl/essays/104050 (via search excerpt)
- [S18] Guild Order. Valorant comms and callouts. https://guildorder.com/games/valorant/guides/comms-and-callouts
- [S19] MetaBot. How to communicate in Valorant. https://metabot.gg/en/valorant/guides/valorant-communication-callouts-guide
- [S20] ProSettings. Communication in CS2: the ultimate guide. https://prosettings.net/blog/communication-in-cs2-guide/
- [S21] Prima Games, Halo 5: Guardians eGuide, Teamwork. https://primagames.com/eguides/halo-5-guardians-eguide/multiplayer/tactical-primer/teamwork (via search excerpt; page 403)
- [S22] Halo Waypoint support, Recommended competitive settings for Halo Infinite. https://support.halowaypoint.com/hc/articles/21193250866196-Recommended-Competitive-Settings-for-Halo-Infinite (via search excerpt; page 403); Kotaku impressions: https://kotaku.com/halo-infinites-crystal-clear-visual-design-puts-its-mur-1848167032
- [S23] BioNumbers 110800, reaction times to sound, light and touch (Kosinski review). https://bionumbers.hms.harvard.edu/bionumber.aspx?id=110800
- [S24] van Heuven and Hagman, citing Marslen-Wilson (1985), recognition about 200 ms after word onset (secondary): https://scholarlypublications.universiteitleiden.nl/access/item%3A2729322/download ; gating overview: Grosjean (1980), Perception and Psychophysics 28, 267 to 283.
- [S25] Boiteau, Malone, Peters and Almor (2014). Interference between conversation and a concurrent visuomotor task. JEP: General 143. https://pubmed.ncbi.nlm.nih.gov/23421443/
- [S26] Caird, Willness, Steel and Scialfa (2008). A meta-analysis of the effects of cell phones on driver performance. https://swov.nl/en/publicatie/meta-analysis-effects-cell-phones-driver-performance
- [S27] Brungart (2001). Informational and energetic masking effects in the perception of two simultaneous talkers. JASA 109. https://scholar.usuhs.edu/en/publications/informational-and-energetic-masking-effects-in-the-perception-of--2/
- [S28] Prinzo and McClellan (2005). Terminal radar approach control: measures of voice communications system performance. DOT/FAA/AM-05/19. https://www.faa.gov/data_research/research/med_humanfacs/oamtechreports/2000s/2005/0519
- [S29] ITU-T G.114 (05/2003), one-way transmission time: https://www.cs.columbia.edu/~andreaf/new/documents/other/T-REC-G.114-200305.pdf ; 3GPP excerpt of the bands: https://www.itecspec.com/3gpp/22.105/s/b.2.1
- [S30] Trick, Enns and Brodeur (1996): https://visionlab-psych.sites.olt.ubc.ca/files/2015/06/36_Trick_etal_DP96.pdf ; Trick thesis abstract (40 to 100 and 250 to 350 ms per item): https://ir.lib.uwo.ca/digitizedtheses/2008
- [S31] Counter-Strike bot source (ReGameDLL_CS): https://github.com/rehlds/ReGameDLL_CS/blob/master/regamedll/dlls/bot/cs_bot_chatter.cpp , https://github.com/rehlds/ReGameDLL_CS/blob/master/regamedll/dlls/bot/cs_bot_chatter.h , https://github.com/rehlds/ReGameDLL_CS/blob/master/regamedll/dlls/bot/cs_bot_radio.cpp
- [S32] Quake III Arena source: https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/ai_cmd.c , https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/ai_dmq3.c , https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/ai_chat.c , https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/ai_team.c
- [S33] Source SDK 2013: https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/game/server/ai_speech.cpp , https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/game/server/ai_speech.h , https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/game/server/ai_playerally.cpp , https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/game/server/ai_playerally.h
- [S34] Ruskin, E. (2012). AI-driven dynamic dialog through fuzzy pattern matching. GDC 2012, Valve. http://media.steampowered.com/apps/valve/2012/GDC2012_Ruskin_Elan_DynamicDialog.pdf
- [S35] Orkin, J. (2006). Three states and a plan: the A.I. of F.E.A.R. GDC 2006. https://pages.cs.wisc.edu/~dyer/cs540/handouts/gdc2006_orkin_jeff_fear.pdf
- [S36] Game AI Pro, chapter 29: Hierarchical AI for multiplayer bots in Killzone 3. https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter29_Hierarchical_AI_for_Multiplayer_Bots_in_Killzone_3.pdf
- [S37] Bungie, Halo 3 AI dialogue tables, from the official Halo 3 Editing Kit (local primary source, no public URL): `<Steam library>\steamapps\common\H3EK\H3EK.7z` members `data/ai/ai_dialogue_globals.xls` and `data/ai/ai_dialogue_rules.xls`. Read-only extraction: `C:\Windows\System32\tar.exe -xf H3EK.7z data/ai/ai_dialogue_globals.xls data/ai/ai_dialogue_rules.xls` into a temporary folder. Field help strings from `<Steam library>\steamapps\common\H3EK\guerilla.exe`. The CSV import path is documented at https://c20.reclaimers.net/h3/h3-ek/h3-tool/
- [S38] Griesemer and Butcher (2002). The illusion of intelligence. GDC 2002 deck. https://www.jmeiners.com/shamans/papers/ai/the_illusion_of_intelligence.pdf ("Leader dead, run" about half the time, via search excerpt of the deck)
- Project docs: `docs/BRAIN-DESIGN.md` (bot recognition medians), `docs/research/01-human-like-bot-behavior.md` (CS profile reaction times, earlier delay recommendation), `docs/research/05-how-humans-play-halo.md` (Halo callout vocabulary).
