"""Writes maps/bloodgulch/callouts.json: Blood Gulch callout zones laid out on the real map.

Names: the recommended set in docs/research/06-blood-gulch-callouts.md (section 8.1), taken from
the MCC Halo 1 big-team community's recorded voice comms and older Halo PC sources ("dark side"
is the north-east wall in shadow, "light side" the sunlit south-west wall; "port" = teleporter
exit). Geometry: coordinates from objects.json and the height map (research section 3).

A position takes the highest-priority zone that contains it (height band included); gaps take
the nearest large area ("area": true). Circles are written as 12-gons.
usage: python -I make_zones.py
"""
import json
import math
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "maps", "bloodgulch", "callouts.json")
RED, BLUE = (95.688, -159.449), (40.241, -79.123)


def circle(c, r, n=12):
    return [[round(c[0] + r * math.cos(2 * math.pi * k / n), 2), round(c[1] + r * math.sin(2 * math.pi * k / n), 2)] for k in range(n)]


def z(name, poly, side="mid", pri=10, zmin=None, zmax=None, full="", aka=(), area=False):
    d = {"poly": poly, "side": side, "priority": pri, "full": full, "aka": list(aka), "area": area}
    if zmin is not None:
        d["zmin"] = zmin
    if zmax is not None:
        d["zmax"] = zmax
    return name, d


ZONES = dict([
    # --- bases: inside (flag room) and roof, split by height
    z("Red base", circle(RED, 5.0), "red", 40, zmax=1.0, full="inside red base: flag room and doorways", aka=["red"]),
    z("Red top", circle(RED, 5.6), "red", 39, zmin=1.0, full="red roof: tele pad, sniper, health, Banshee", aka=["top red"]),
    z("Blue base", circle(BLUE, 5.0), "blue", 40, zmax=1.0, full="inside blue base: flag room and doorways", aka=["blue"]),
    z("Blue top", circle(BLUE, 5.6), "blue", 39, zmin=1.0, full="blue roof: tele pad, sniper, health, Banshee", aka=["top blue"]),
    # --- teleporter exits ("port"): red's exit is on the dark side, blue's on the light side
    z("Red port", circle((82.83, -114.53), 4.5), "red", 32, full="red teleporter exit, dark side next to the Water cave", aka=["red portal", "red portal exit"]),
    z("Blue port", circle((43.80, -126.23), 4.5), "blue", 32, full="blue teleporter exit, light side by Blue cliff", aka=["blue portal", "blue portal exit"]),
    # --- dark-side cave system (north-east wall)
    z("OS", [[100, -104], [112, -104], [113, -114], [100, -114]], "mid", 34, zmax=3.2,
      full="overshield pocket at the east end of the caves (flamethrower too)", aka=["OS cave", "overshield cave", "power up cave"]),
    z("Tunnel", [[89, -89], [100, -89], [106, -96], [111, -104], [111, -112], [100, -112], [96, -104], [89, -99]], "mid", 33, zmin=3.2,
      full="upper tunnel along the dark wall, from the bay by Big Hill to the OS", aka=["tunnels", "high cave"]),
    z("Water", [[86, -111], [92, -107], [100, -108], [100, -119], [92, -121], [86, -118]], "mid", 31,
      full="cave mouth right behind Red port", aka=["water cave", "the cave"]),
    z("Batcave", [[62, -86], [66, -80], [72, -76], [75, -63], [84, -63], [87, -78], [88, -92], [86, -97], [66, -98], [61, -92]], "blue", 26,
      full="blue's dark-side cave bulge: low mouth, raised cave with plasmas, ledge with a pistol", aka=["blue caves", "blue base cave"]),
    # --- light-side heights
    z("Sunny", [[38, -141], [48, -139], [58, -142], [66, -149], [66, -160], [71, -168], [72, -184], [57, -186], [52, -172], [46, -160], [37, -151]],
      "red", 28, zmin=1.8, full="light-side ridge over red base: ledge with pistol and plasmas, terrace to the south",
      aka=["Sunny ridge", "Sunnyside", "the ridge", "red cliff"]),
    z("Blue cliff", [[18, -100], [32, -99], [40, -112], [40, -124], [30, -126], [20, -114]], "blue", 28, zmin=1.8,
      full="light-side shelf by Blue port", aka=["blue sniper cliff", "light cliff"]),
    # --- back corners
    z("Camp hill", [[104, -166], [116, -166], [130, -172], [130, -190], [110, -190], [104, -178]], "red", 28, zmin=1.2,
      full="hill in red's back dark corner, with Sniper Rock", aka=["the hill behind red base", "Sniper Rock"]),
    z("Cubby", [[12, -48], [56, -48], [56, -66], [12, -66]], "blue", 27, zmin=1.8,
      full="crevice and overhang along the back wall behind blue base", aka=["cubbie hole"]),
    # --- field landmarks
    z("Big Hill", [[63, -98], [80, -97], [84, -104], [81, -111], [66, -112], [61, -105]], "mid", 24,
      full="tallest hill in the field, next to Red port", aka=["Hamburger Hill", "Hamburger", "BH"]),
    z("Camo", circle((60.0, -113.5), 5.0), "mid", 25, full="camo hump west of mid (spawn is 50% camo, 50% overshield)", aka=["middle power up"]),
    z("Rockets", circle((72.60, -126.34), 4.0), "mid", 25, full="rocket launcher mound south of mid", aka=["middle rockets", "RL"]),
    z("Fuel rod", circle((62.97, -136.52), 4.0), "mid", 25, full="fuel rod gun spawn, light side, red half", aka=["fuel rod rock"]),
    z("Red tree", circle((80.3, -145.5), 5.5), "red", 22, full="dead tree and small hill in front of red base", aka=["red front hill"]),
    z("Blue tree", circle((42.9, -95.6), 5.5), "blue", 22, full="white tree and small hill in front of blue base", aka=["blue front hill"]),
    # --- around each base
    z("Red front", [[83, -162], [90, -164.5], [92, -154], [99, -153.5], [103, -150], [100, -144], [90, -143], [84, -146], [82, -153]],
      "red", 20, full="field side of red base: front door, front rocks", aka=["front red"]),
    z("Blue front", [[33, -83], [34, -91], [41, -91.5], [49, -91], [54, -86], [53, -77], [46, -74.5], [45, -80]],
      "blue", 20, full="field side of blue base: front door, front rocks", aka=["front blue"]),
    z("Red back", [[84, -163], [90, -165], [100, -164], [104, -160], [108, -158], [112, -162], [108, -170], [104, -178], [95, -182], [80, -182], [78, -170]],
      "red", 18, full="behind red base: back door, hogs and tanks", aka=["back red", "behind red"]),
    z("Blue back", [[26, -74], [30, -70], [36, -62], [50, -60], [56, -66], [54, -74], [46, -74.5], [34, -75]],
      "blue", 18, full="behind blue base: back door, hogs and tanks", aka=["back blue", "behind blue"]),
    z("Light red", [[64, -158], [78, -155], [84, -162], [80, -172], [78, -182], [68, -184], [64, -172]], "red", 16,
      full="light-side ground next to red base", aka=["light side red"]),
    z("Dark red", [[98, -122], [112, -122], [120, -132], [116, -148], [108, -158], [102, -150], [100, -140], [96, -130]], "red", 16,
      full="dark-side ground next to red base", aka=["dark side red"]),
    z("Light blue", [[10, -74], [26, -74], [34, -84], [33, -92], [30, -100], [14, -100], [8, -88]], "blue", 16,
      full="light-side ground next to blue base", aka=["light side blue"]),
    z("Dark blue", [[46, -74.5], [54, -74], [56, -66], [64, -64], [70, -70], [66, -80], [62, -86], [54, -86]], "blue", 16,
      full="dark-side ground next to blue base, under the Batcave", aka=["dark side blue"]),
    # --- coarse areas: they also name every gap between the zones above
    z("Mid", [[52, -108], [64, -106], [84, -110], [88, -124], [84, -134], [56, -134], [50, -124]], "mid", 12,
      full="centre field between the two ports", aka=["middle", "center"], area=True),
    z("Light side", [[14, -100], [52, -100], [52, -108], [50, -124], [56, -134], [56, -142], [36, -150], [22, -130]], "mid", 10,
      full="the sunlit south-west wall and the strip along it", aka=["light", "sunny side"], area=True),
    z("Dark side", [[84, -96], [96, -96], [112, -104], [120, -124], [100, -122], [88, -124], [84, -110]], "mid", 10,
      full="the shaded north-east wall and the strip along it", aka=["dark"], area=True),
    z("Blue side", [[0, -40], [90, -40], [90, -100], [0, -100]], "blue", 8, full="blue's half of the canyon", area=True),
    z("Red side", [[30, -134], [60, -134], [88, -124], [100, -122], [125, -125], [135, -160], [135, -195], [30, -195]], "red", 8,
      full="red's half of the canyon", area=True),
])

DATA = {
    "map": "bloodgulch",
    "base_radius": 4.8,
    "roof_z": 1.7,
    "points": {"mid": [67.3, -119.8, 0.2], "mid_hill": [72.8, -103.6, 4.1]},
    # spots defenders and campers hold (ground level; the sim cannot climb roofs)
    "holds": {"red": [[95.7, -159.4, -0.3], [90.0, -152.0, 0.1], [101.0, -151.0, 0.1]],
              "blue": [[40.2, -79.1, -0.3], [46.0, -86.0, 0.1], [34.0, -86.0, 0.1]]},
    # attack lanes: dark side by Red port, mid, light side by Blue port
    "lanes": [[82.8, -114.5, 0.7], [67.3, -119.8, 0.2], [45.0, -124.0, 0.3]],
    # sneaky routes skilled players take to the enemy flag (waypoint lists, research 06 places):
    # red attacking blue, blue attacking red
    "sneak": {
        "red": [[[86, -110, 1], [90, -98, 2], [75, -95, 1.5], [58, -84, 0.3]],      # dark side: bay, Batcave shelf, Dark blue
                [[44, -130, 0.3], [30, -110, 2.6], [24, -92, 1.0]]],                # light side: Blue cliff, Light blue
        "blue": [[[44, -130, 0.3], [46, -146, 2.0], [60, -152, 6.0], [72, -166, 1.0]],  # light side: up Sunny, Light red
                 [[84, -112, 0.7], [106, -132, 0.5], [104, -150, 0.2]]],              # dark side: Red port, Dark red
    },
    "zones": ZONES,
}

if __name__ == "__main__":
    json.dump(DATA, open(OUT, "w"), indent=1)
    print(f"{len(ZONES)} zones ->", os.path.abspath(OUT))
