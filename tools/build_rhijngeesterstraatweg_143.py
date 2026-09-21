"""Emit examples/rhijngeesterstraatweg_143.json from the surveyed geometry.

Derived from:
  * the 1931 construction drawings (plan no. 590, M.C. van Straten, Leiden):
    unit width 7.15 m, main body 9.00 m deep, room names and service-band
    arrangement (keuken/wc/hal + salon/huiskamer);
  * the note on the approved sheet: as built 0.90 m deeper than drawn,
    hence a 9.90 m body, which also reconciles the 198 m2 over 3 floors;
  * the sale brochure for no. 143 (corner unit, 7 bedrooms, 2 bathrooms,
    fireplace, sliding partition, balcony, west garden / south side garden).
"""
import json

W, D = 7.15, 9.90           # unit width (S-N on plan x) and depth (E-W on plan y)
LB = 2.80                    # service band width (south side, with the side garden)
RB = W - LB                  # principal rooms band (4.35)


def R(name, typ, x, y, w, h, windows=(), doors=(), note="", features=(), furniture=()):
    d = {"name": name, "type": typ, "x": round(x, 3), "y": round(y, 3),
         "width": round(w, 3), "height": round(h, 3)}
    if windows:
        d["windows"] = list(windows)
    if doors:
        d["doors"] = list(doors)
    if note:
        d["note"] = note
    if features:
        d["features"] = list(features)
    if furniture:
        d["furniture"] = list(furniture)
    return d


def fix(name, x, y, w, h, kind="generic", color="#b09a76"):
    """A fixture pinned by the survey, offset from the room's corner."""
    return {"name": name, "x": round(x, 3), "y": round(y, 3),
            "width": round(w, 3), "height": round(h, 3), "kind": kind, "color": color}


def win(side, position, role):
    return {"side": side, "position": round(position, 3), "role": role}


def door(side, position, width, connects_to=None, kind="interior"):
    d = {"side": side, "position": round(position, 3), "width": width}
    if connects_to:
        d["connects_to"] = connects_to
    if kind != "interior":
        d["kind"] = kind
    return d


# --------------------------------------------------------------- begane grond
ground = [
    R("Entree", "entree", 0, 0, LB, 1.60,
      windows=[win("W", 0.80, "small")],
      doors=[door("S", 1.40, 1.10, kind="front_door"), door("N", 1.40, 1.00, "hal")],
      note="voordeur, oostzijde"),
    R("Hal", "hal", 0, 1.60, LB, 4.00,
      windows=[win("W", 2.00, "stair")],
      doors=[door("S", 1.40, 1.00, "entree"), door("E", 1.60, 1.00, "salon"),
             door("N", 0.52, 0.70, "toilet"), door("N", 1.57, 0.70, "berging"),
             door("N", 2.45, 0.85, "gang", kind="opening")],
      furniture=[fix("Trap", 0.0, 0.10, 1.00, 2.60, kind="stair", color="#a8926f")],
      note="bordestrap, hoge raampartij"),
    R("Toilet", "wc", 0, 5.60, 1.05, 1.10,
      windows=[win("W", 0.55, "toilet")],
      doors=[door("S", 0.52, 0.70, "hal")]),
    R("Berging", "berging", 1.05, 5.60, 1.05, 1.10,
      doors=[door("S", 0.52, 0.70, "hal")], note="trapkast"),
    R("Gang", "gang", 2.10, 5.60, 0.70, 1.10,
      doors=[door("S", 0.35, 0.70, "hal", kind="opening"),
             door("N", 0.35, 0.70, "keuken", kind="opening")]),
    R("Keuken", "keuken", 0, 6.70, LB, 3.20,
      windows=[win("W", 1.60, "kitchen"), win("N", 1.40, "kitchen")],
      doors=[door("S", 2.45, 0.70, "gang", kind="opening"),
             door("E", 1.20, 0.90, "huiskamer"),
             door("N", 1.40, 1.20, kind="garden")],
      note="aan de tuinzijde"),
    R("Salon", "salon", LB, 0, RB, 4.60,
      windows=[win("S", RB / 2, "living_front")],
      doors=[door("W", 3.20, 1.00, "hal"),
             door("N", RB / 2, 2.40, "huiskamer", kind="sliding")],
      furniture=[fix("Open haard", RB - 0.45, 1.65, 0.45, 1.30,
                     kind="fireplace", color="#6b5140")],
      note="open haard", features=["open haard", "schuifdeuren"]),
    R("Huiskamer", "huiskamer", LB, 4.60, RB, 5.30,
      windows=[win("N", RB / 2, "living_rear")],
      doors=[door("S", RB / 2, 2.40, "salon", kind="sliding"),
             door("W", 3.30, 0.90, "keuken"),
             door("N", RB / 2, 1.60, kind="garden")],
      note="eethoek aan de tuin", features=["schuifdeuren", "tuindeuren"]),
]

# -------------------------------------------------------------- eerste etage
first = [
    R("Slaapkamer 4", "slaapkamer", 0, 0, LB, 3.00,
      windows=[win("S", 1.40, "bedroom"), win("W", 1.50, "small")],
      doors=[door("N", 1.40, 0.90, "overloop")]),
    R("Overloop", "overloop", 0, 3.00, LB, 2.60,
      furniture=[fix("Trap", 0.0, 0.0, 1.00, 2.60, kind="stair", color="#a8926f")],
      windows=[win("W", 1.30, "stair")],
      doors=[door("S", 1.40, 0.90, "slaapkamer_4"),
             door("E", 0.80, 0.90, "slaapkamer_1"),
             door("E", 2.10, 0.90, "slaapkamer_2"),
             door("N", 1.00, 0.80, "badkamer"),
             door("N", 2.40, 0.80, "gang_2", kind="opening")]),
    R("Badkamer", "badkamer", 0, 5.60, 2.00, 2.40,
      windows=[win("W", 1.20, "small")],
      doors=[door("S", 1.00, 0.80, "overloop")],
      note="douche, wastafel, closet"),
    R("Gang", "gang", 2.00, 5.60, 0.80, 2.40,
      doors=[door("S", 0.40, 0.80, "overloop", kind="opening"),
             door("N", 0.40, 0.80, "slaapkamer_3", kind="opening")]),
    R("Slaapkamer 3", "slaapkamer", 0, 8.00, LB, 1.90,
      windows=[win("N", 1.40, "bedroom")],
      doors=[door("S", 2.40, 0.80, "gang_2")]),
    R("Slaapkamer 1", "slaapkamer", LB, 0, RB, 4.60,
      windows=[win("S", 1.30, "bedroom"), win("S", 3.05, "bedroom")],
      doors=[door("W", 3.80, 0.90, "overloop")], note="voorzijde, straatzijde"),
    R("Slaapkamer 2", "slaapkamer", LB, 4.60, RB, 5.30,
      windows=[win("N", 1.30, "bedroom"), win("N", 3.05, "bedroom")],
      doors=[door("W", 0.50, 0.90, "overloop"),
             door("N", RB / 2, 1.00, kind="garden")],
      note="balkon, uitzicht achtertuin", features=["balkon"]),
]

# -------------------------------------------------------------- tweede etage
second = [
    R("Slaapkamer 7", "slaapkamer", 0, 0, LB, 3.00,
      windows=[win("S", 1.40, "dormer")],
      doors=[door("N", 1.40, 0.85, "overloop_2")], note="onder de kap"),
    R("Overloop", "overloop", 0, 3.00, LB, 2.60,
      furniture=[fix("Trap", 0.0, 0.0, 1.00, 2.60, kind="stair", color="#a8926f")],
      windows=[win("W", 1.30, "small")],
      doors=[door("S", 1.40, 0.85, "slaapkamer_7"),
             door("E", 0.80, 0.85, "slaapkamer_5"),
             door("E", 2.10, 0.85, "slaapkamer_6"),
             door("N", 1.00, 0.80, "badkamer_2"),
             door("N", 2.40, 0.80, "gang_3", kind="opening")]),
    R("Badkamer 2", "badkamer", 0, 5.60, 2.00, 2.00,
      windows=[win("W", 1.00, "small")],
      doors=[door("S", 1.00, 0.80, "overloop_2")], note="douche, closet, wastafel"),
    R("Gang", "gang", 2.00, 5.60, 0.80, 2.00,
      doors=[door("S", 0.40, 0.80, "overloop_2", kind="opening"),
             door("N", 0.40, 0.80, "bergruimte", kind="opening")]),
    R("Bergruimte", "bergruimte", 0, 7.60, LB, 2.30,
      windows=[win("W", 1.15, "small")],
      doors=[door("S", 2.40, 0.80, "gang_3")], note="onder de kap"),
    R("Slaapkamer 5", "slaapkamer", LB, 0, RB, 4.60,
      windows=[win("S", RB / 2, "dormer")],
      doors=[door("W", 3.80, 0.85, "overloop_2")], note="onder de kap"),
    R("Slaapkamer 6", "slaapkamer", LB, 4.60, RB, 5.30,
      windows=[win("N", RB / 2, "dormer")],
      doors=[door("W", 0.50, 0.85, "overloop_2")], note="onder de kap"),
]

spec = {
    "name": "Rhijngeesterstraatweg 143",
    "address": "Rhijngeesterstraatweg 143, 2341 BT Oegstgeest",
    "year_built": 1931,
    "architect": "M.C. van Straten, arch., Leiden — plan no. 590",
    "style": "heritage",
    "units": "m",
    "width": W,
    "height": D,
    # Plan is drawn with the rear garden up: +Y therefore faces west.
    # Front door (S on plan) -> east / street; W on plan -> south side garden;
    # E on plan -> north party wall, which is blind.
    "north_angle_deg": 270,
    "blind_sides": ["E"],
    "scale_note": "schaal 1:100 · maten in meters",
    "provenance": {
        "drawings": "Bouwtekeningen BD03308, Tek-001 t/m Tek-004",
        "project": "Zes landhuizen a/d Rijksstraatweg te Oegstgeest",
        "plan_no": "590",
        "architect": "M.C. van Straten, Leiden, maart 1931",
        "approval": "Goedgekeurd B&W Oegstgeest, 1 juli 1931",
        "as_built_note": "0.90 m dieper dan bouwteekening (aanvraag 15-6-1931)",
        "brochure": "Panne van Soest Makelaars — 198 m² wonen, 456 m² perceel",
        "estate": "Terrein v/h landhuis 'Enna'",
    },
    "storeys": [
        {"name": "Begane grond", "level": 0, "ceiling_height": 3.05, "rooms": ground,
         "note": "entree, hal met bordestrap, salon en huiskamer en-suite, keuken aan de tuin"},
        {"name": "Eerste etage", "level": 1, "ceiling_height": 2.95, "rooms": first,
         "note": "vier slaapkamers, badkamer, balkon aan de tuinzijde"},
        {"name": "Tweede etage", "level": 2, "ceiling_height": 2.60, "rooms": second,
         "note": "drie slaapkamers onder de kap, tweede badkamer, bergruimte"},
    ],
}

# ---- validate the tiling before writing -----------------------------------
def check(rooms, label):
    total = 0.0
    for i, a in enumerate(rooms):
        total += a["width"] * a["height"]
        assert a["x"] >= -1e-9 and a["y"] >= -1e-9, (label, a["name"])
        assert a["x"] + a["width"] <= W + 1e-9, (label, a["name"], "overruns width")
        assert a["y"] + a["height"] <= D + 1e-9, (label, a["name"], "overruns depth")
        for b in rooms[i + 1:]:
            overlap = not (a["x"] + a["width"] <= b["x"] + 1e-9 or b["x"] + b["width"] <= a["x"] + 1e-9
                           or a["y"] + a["height"] <= b["y"] + 1e-9 or b["y"] + b["height"] <= a["y"] + 1e-9)
            assert not overlap, (label, a["name"], b["name"], "overlap")
    assert abs(total - W * D) < 1e-6, (label, "area", total, W * D)
    return total

tot = 0.0
for st in spec["storeys"]:
    a = check(st["rooms"], st["name"])
    tot += a
    print(f"{st['name']:<16} {len(st['rooms'])} rooms, {a:.2f} m2 (tiles {W*D:.2f} m2)")
print(f"gross floor area over 3 storeys: {tot:.1f} m2  (brochure: 198 m2 net)")

with open("examples/rhijngeesterstraatweg_143.json", "w", encoding="utf-8") as f:
    json.dump(spec, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("written")
