# Finite Dungeons - Demo Version
# Finite Dungeons
# Created by Timothy
# Copyright © 2026 Timothy Tang

# To do list:
#outro

# -------------------------------------------------------------------
# Structure (kept Godot-4.7-port friendly):
#   0. VALUES        - every gameplay number: prices, limits, effects,
#                      unlock levels (calc/fdval.py is an identical copy)
#   1. CONTENT DATA  - names, descriptions and story text, built from VALUES
#                      -> Godot: Resources / JSON data files
#   2. MODEL         - Entity / Drone / Player / Profile state
#                      -> Godot: GDScript classes
#   3. SAVE          - base-61 save codes (format unchanged from original)
#   4. ENGINE        - pure game logic: no print()/input(), functions return
#                      message lists for the UI to show
#                      -> Godot: GDScript logic, messages become UI signals
#   5. TERMINAL UI   - every print()/input() in the game lives here
#                      -> Godot: scenes / UI nodes
# -------------------------------------------------------------------

import os
import time
import traceback

if os.name == "nt":
    os.system("color F0")

# ============================================================
# 0. VALUES
# ============================================================

# --- VALUES START ---
# Every number that decides how the game plays. The engine, the shop
# lines, the descriptions and the library all read these names, so
# changing a value here changes the rules AND the text explaining them.
# This block is identical in "FiniteDungeons.py" and calc/fdval.py:
# change both (CLAUDE.md has the check). Plain ASCII only.

# --- Runs and monsters ---
FINAL_LEVEL = 30           # beat this level to win (save codes store at most 31)
START_HP = 10              # max HP and HP when a run starts
START_STAT = 1             # ATK, DEF and SPD when a run starts
START_MONEY = 0            # money when a run starts
MONSTER_GROWTH = 1         # a level-L monster has L x this ATK, DEF and SPD,
MONSTER_EXTRA_HP = 4       #   and that + this many HP
WIN_MONEY = 4              # money for every monster beaten
MIN_DAMAGE = 1             # every hit does at least this much

# --- Shop: prices and limits ---
PRICE = {
    "sword": 2,            # ATK (not sold with the E-Sword or the Drone)
    "shield": 2,           # DEF
    "boots": 2,            # SPD (not sold with Cursed Socks)
    "chicken": 2,          # heals, see Chickens below
    "book": 3,             # every kind: Attack, Defence, Speed, Max HP, Healing
    "battery": 2,          # E-Sword only: counter-attacks
    "ink": 9,              # Forbidden Book only: kills the next monster outright
    "elixir": 2,           # Devotion only, see Artefacts below
}
LIMIT = {                  # how many you can buy in one run
    "sword": 1,
    "shield": 1,
    "boots": 1,
    "book": 3,             # of EACH kind of book
    "battery": 5,
    "ink": 10,             # one FORBIDDEN_MESSAGES line per ink: add lines if raised
    "elixir": 1,           # per shop visit, not per run
}
FLAT_ITEM_GAIN = 1         # Sword / Shield / Boots add this to ATK / DEF / SPD
BOOK_MULTIPLIER = 2        # Books of Attack / Defence / Speed / Max HP multiply
                           #   that stat (the Max HP book says "double")

# --- Chickens (the K*C membership card relics change them) ---
CHICKEN_HEAL = {"plain": 5, "bk": 8, "sk": 10}  # gold and diamond cards heal to max
CHICKEN_LIMIT = {"plain": 1, "bk": 2, "sk": 4}  # gold and diamond cards: no limit
CHICKEN_MIN_MISSING = 5    # plain/bronze/silver/gold: sold only with this much HP missing

# --- Relics ---
REVIVE_HP = 1              # Picture of Family: revives you once, at this HP
BLESSED_EVERY = 3          # Blessed Emblem: after every 3rd level,
BLESSED_MAX_HP = 5         #   +5 max HP, then a full heal;
BLESSED_START_HP_LOSS = 1  #   -1 HP when a run starts with it packed
INK_HOLD = 1               # Forbidden Book: inks you can carry at once
ESWORD_ATK = 1             # E-Sword: ATK it gives when equipped
BATTERY_COUNTERS = 1       # E-Sword: counter-attacks per battery
MEOWTON_DEF_LOSS = 1       # Meowton's 2nd lawsuit: DEF lost when equipped

# --- RAY-24 Drone: 4 upgrade tracks, 4 stages each ---
DRONE_SLOTS = 6            # paid upgrades per run, all tracks together
DRONE_STAGES = 4           # stages per track (the lists below have one per stage)
DRONE_STAGE_COSTS = [      # price of each stage
    [1, 2, 3, 4],          # track 1 Hardpoint munition upgrade: drone ATK
    [2, 2, 2, 4],          # track 2 Alpha strike: missiles at the start of fights
    [2, 2, 2, 3],          # track 3 FARP Protocol: healing after each win
    [2, 2, 2, 3],          # track 4 Materiel Recovery: money after each win
]
DRONE_T1_ATK_GAIN = [1, 2, 2, 8]  # track 1: drone ATK each stage adds
DRONE_MISSILE_MULTIPLIER = 2      # track 2 from stage 2: a missile hits for drone
                                  #   ATK x this (the text says "double")
DRONE_STAGE4_MISSILES = 3         # track 2 stage 4: missiles per fight, each
DRONE_SHRED_MULTIPLIER = 2        #   cutting monster DEF by its damage x this
DRONE_HEALS = [10, 20, 50]        # track 3 stages 1-3: HP healed after a win
                                  #   (they add up: 10, then 30, then 80)
DRONE_HEAL_MULTIPLIER = 2         # track 3 stage 4: all healing x this ("doubles")
DRONE_T4_MONEY = [10, 16]         # track 4 stages 2-3: money after a win
                                  #   (stage 1 gives money = drone ATK)
DRONE_INCOME_MULTIPLIER = 2       # track 4 stage 4: all income x this ("double")

# --- Artefacts ---
ELIXIR_SPD_LOSS = 1        # Devotion's Elixir: -1 SPD and -[Elixirs bought] max HP,
ELIXIR_EXTRA_SPD = 6       #   +6 extra SPD,
ELIXIR_FIGHTS = 3          #   wearing off over the next 3 fights:
ELIXIR_SPD_DECAY = 2       #   -2 extra SPD after each of them
SOCKS_MAX_HP = 3           # Cursed Socks: activate at this HP or less
AR_MAX_HP_LOSS = 5         # Abyssal Rad-Blood Oath: the water sample (once per run)
AR_LEVEL_STEP = 5          #   costs 5 max HP and pays
AR_POWER = 4               #   (levels beaten // 5) ** this money
COINPOT_STEP = 3           # Alchemist's Coinpot: every 3 money left when you leave
COINPOT_PAY = 2            #   the shop pays 2 money before the fight
VITALITY_HP = 50           # Heart of Excessive Vitality: start with 50 max HP and HP,
VITALITY_MONEY_LOSS = 0.10 #   lose this share of your money before each fight,
VITALITY_DRAIN_DIVISOR = 1 #   then lose HP = money / this
CARRIER_RELICS = 3         # Carrier of Legend: relics packed (switches = this - 1);
CARRIER_RESET = 1          #   HP, ATK, DEF and SPD drop to this at a switch

# --- Unlocks: (key, highest level beaten needed). List order = menu order. ---
RELIC_UNLOCKS = [
    ("family", 0),
    ("blessed", 0),
    ("forbidden", 0),
    ("e-sword", 999999),   # kept out of the game until it is balanced
    ("bk", 2),
    ("sk", 7),
    ("yd", 8),
    ("gk", 10),
    ("meowton", 15),
    ("dk", 30),
]
ARTEFACT_UNLOCKS = [
    ("devotion", 3),
    ("socks", 6),
    ("ar", 12),
    ("coinpot", 18),
    ("carrier", 20),
    ("vitality", 20),
]

# --- Achievements ---
RICH_MONEY = 25000000      # "you can't take it with you": die holding this much
FEW_RUNS = 3               # "The real game": beat FINAL_LEVEL within this many runs
HARD_MODE_LEVEL = 2        # "hard mode": die on this level with Meowton + Cursed Socks

# --- Interface ---
MENU_PAUSE = 0.3           # seconds of pause before the shop and main menu redraw
TEXT_COLOURS = {           # RGB colour of each kind of text (both screens are white)
    "muted": (160, 160, 160),    # greyed-out items, flavour lines, the fight forecast
    "story": (100, 100, 100),    # story scenes
    "good": (0, 128, 0),         # your hits, heals, purchases, wins
    "bad": (190, 0, 0),          # monster hits, drains, deaths
    "warning": (190, 0, 0),      # blocked purchases, invalid input
}                          # anything else (menus, stats, headings, money) is
                           # the normal text colour. Money lines are marked
                           # "money": add a "money" entry here to colour them.
COLOURS_ON = True          # colours at start; players can switch them off in-game
# --- VALUES END ---


# ============================================================
# 1. CONTENT DATA
# ============================================================

def ansi(rgb):
    """True-colour ANSI code for an (r, g, b) text colour."""
    return "\033[38;2;%d;%d;%dm" % rgb


GREY = ansi(TEXT_COLOURS["muted"])  # greyed-out shop items and flavour lines
RESET = '\033[39m'  # back to the terminal's own text colour (black on the color F0 console)

# Derived from VALUES for the texts below (not values of their own).
UNLOCK_LEVEL = dict(RELIC_UNLOCKS + ARTEFACT_UNLOCKS)
VITALITY_PERCENT = int(round(VITALITY_MONEY_LOSS * 100))
AR_POWER_SIGN = {2: "²", 3: "³", 4: "⁴"}.get(AR_POWER, f"^{AR_POWER}")
VITALITY_DRAIN_TEXT = "money" if VITALITY_DRAIN_DIVISOR == 1 else f"money/{VITALITY_DRAIN_DIVISOR}"

FORBIDDEN_MESSAGES = [
    "You wrote out the formula to beat this game (a wrong one), the monster dies laughing!",
    "You wrote out Navier-Stokes equation, the monster dies trying to understand!",
    "You wrote out Einstein’s field equations, the monster dies overwhelmed!",
    "You wrote out Schrodinger's equation, the monster dies in confusion!",
    "You scribbled down Maxwell's equations, the monster dies from panic!",
    "You wrote out Rocket propulsion formulas, the monster dies screaming!",
    "You jotted down Euler's formula, the monster dies in horror!",
    "You wrote out the cubic formula, the monster faints and dies!",
    "You scribbled out the Pythagorean theorem, the monster dies of fright!",
    "You wrote out the equation for the area of a triangle, the monster got scared to death!"
]

RELIC_NAMES = {
    "family": "Picture of Family",
    "blessed": "Blessed Emblem",
    "forbidden": "Forbidden Book",
    "bk": "K*C bronze membership card",
    "e-sword": "Automatic Counter E-Sword",
    "yd": "RAY-24 Drone",
    "sk": "K*C silver membership card",
    "meowton": "Meowton’s Second Lawsuit",
    "gk": "K*C gold membership card",
    "dk": "K*C diamond membership card"
}

RELIC_DESCRIPTIONS = {
    "family": f"Picture of Family — Revives once to {REVIVE_HP} HP when defeated.",
    "blessed": f"Blessed Emblem — Every {BLESSED_EVERY} monsters defeated, +{BLESSED_MAX_HP} max HP and heal max. -{BLESSED_START_HP_LOSS} HP when run starts",
    "forbidden": f"Forbidden Book — unlocks in shop: ink - costs {PRICE['ink']}, max purchase {LIMIT['ink']}, max hold {INK_HOLD}, auto consumed at start of fight and defeats the monster.",
    "bk": f"K*C bronze membership card - chicken heals {CHICKEN_HEAL['bk'] - CHICKEN_HEAL['plain']} more hp",
    "yd": f"RAY-24 Drone - have a drone to help you fight! Buy up to {DRONE_SLOTS} upgrades",
    "e-sword": f"E-Sword — Starts with +{ESWORD_ATK} ATK.",
    "sk": f"K*C silver membership card - chickens heal {CHICKEN_HEAL['sk'] - CHICKEN_HEAL['plain']} more hp, max purchase +{CHICKEN_LIMIT['sk'] - CHICKEN_LIMIT['plain']}",
    "meowton": f"Meowton's 2nd lawsuit — -{MEOWTON_DEF_LOSS} DEF when equipping, gain extra ATK = total SPD",
    "gk": f"K*C gold membership card - chickens heal max if missing >={CHICKEN_MIN_MISSING}, no max purchase limit",
    "dk": "K*C diamond membership card - chickens heal max, remove all conditions required to purchase chickens"
}

ARTEFACT_MENU_NAMES = {
    "devotion": "The Damned Proof of Devotion (i.e. corner shop loyalty card)",
    "socks": "Cursed (old, smelly) Socks",
    "coinpot": "Alchemist's Coinpot (savings account)",
    "ar": "Abyssal Rad-Blood Oath (suspicious nuclear food testing contract)",
    "carrier": "The carrier of legends (Backpack)",
    "vitality": "Heart of Excessive Vitality (Protein shake heath package plan)"
}

ARTEFACT_DESCRIPTIONS = {
    "devotion": f"The Damned Proof of Devotion - Elixir unlocked in shop - costs {PRICE['elixir']}, max hp - [elixir bought], SPD-{ELIXIR_SPD_LOSS}, extra spd+{ELIXIR_EXTRA_SPD}, for next {ELIXIR_FIGHTS} fights -{ELIXIR_SPD_DECAY} extra SPD after fight, can only buy one per turn.",
    "socks": f"Cursed Socks — Boots sealed. When HP <= {SOCKS_MAX_HP}, unlocks option in shop to decrease and seal max HP to current HP, gaining the same amount of ATK.",
    "coinpot": f"Alchemist's Coinpot — Every {COINPOT_STEP} money left before fight gives {COINPOT_PAY} money.",
    "ar": f"Abyssal Rad-Blood Oath - Unlocks a shop option once per run to lose {AR_MAX_HP_LOSS} max HP, gain money={{level beaten/{AR_LEVEL_STEP} (round down)}}{AR_POWER_SIGN}.",
    "carrier": f"Carrier of Legend — Choose {CARRIER_RELICS} relics, switch from the 1st to 2nd to 3rd one. All stats except max hp drains to {CARRIER_RESET} at relic switch.",
    "vitality": f"Heart of Excessive Vitality — Start with {VITALITY_HP} HP but lose {VITALITY_PERCENT}% money before fights, at the start of fights, lose HP equal to {VITALITY_DRAIN_TEXT}."
}

# Achievement save-code bit order, most significant bit first. Do NOT reorder:
# save codes pack these 8 flags into one byte in exactly this order.
ACH_BIT_ORDER = (
    "pic_kill", "negative_money", "shop_death", "one_shot",
    "trun", "okill", "drich", "hmode",
)

# Display order + text for the achievements screen.
# Hints listed here are hidden while the achievement is still locked.
ACHIEVEMENT_SECRET_HINTS = {"negative_money"}
ACHIEVEMENT_DISPLAY = [
    ("trun", "The real game", f"beat level {FINAL_LEVEL} in {FEW_RUNS} runs"),
    ("drich", "you can't take it with you", f"die with over {RICH_MONEY // 1000000}m money"),
    ("one_shot", "雑魚", "one shot a monster"),
    ("okill", "'just in case its still alive, you know?'", "shoot a Tomahawk Cruise Missile at a dead monster"),
    ("hmode", "hard mode", f"inevitably die on level {HARD_MODE_LEVEL}"),
    ("negative_money", "Well, you did say ALL conditions", "purchase a chicken without enough money"),
    ("shop_death", "as dangerous as 'monster'", "die in shop"),
    ("pic_kill", "one hp actually helps?!", "kill a monster after reviving"),
]

# --- RAY-24 drone upgrade texts ---
# Costs and effects are in VALUES and applied by apply_drone_stage(). The
# descriptions keep {atk} / {atk2} (the drone's current atk) for drone_menu()
# to fill in, which is why those braces are doubled in the f-strings.
DRONE_TRACK_NAMES = [
    "Hardpoint munition upgrade",  # the drone's regular attack - its ATK rides with yours
    "Alpha strike",                # the start-of-fight Tomahawk volley
    "FARP Protocol",               # post-fight healing (Forward Arming and Refueling Point)
    "Materiel Recovery",           # post-fight income. "Materiel" is the correct military
                                   # spelling and is deliberate - do not "fix" it to "Material".
]

DRONE_STAGE_DESCS = [
    [
        f"Stage 1-drone atk +{DRONE_T1_ATK_GAIN[0]}, cost: {DRONE_STAGE_COSTS[0][0]}",
        f"Stage 2-drone atk +{DRONE_T1_ATK_GAIN[1]}, cost: {DRONE_STAGE_COSTS[0][1]}",
        f"Stage 3-drone atk +{DRONE_T1_ATK_GAIN[2]}, cost: {DRONE_STAGE_COSTS[0][2]}",
        f"Stage 4-drone atk +{DRONE_T1_ATK_GAIN[3]}, cost: {DRONE_STAGE_COSTS[0][3]}",
    ],
    [
        f"Stage 1-at start of fight fire Tomahawk Cruise Missile, attacking monster with drone atk({{atk}}), cost: {DRONE_STAGE_COSTS[1][0]}",
        f"Stage 2-the Tomahawk Cruise Missile has double atk, cost: {DRONE_STAGE_COSTS[1][1]}",
        f"Stage 3-Tomahawk Cruise Missile penetrate defence=its attack({{atk2}}), cost: {DRONE_STAGE_COSTS[1][2]}",
        f"Stage 4-fires {DRONE_STAGE4_MISSILES - 1} more Tomahawk Cruise Missiles, Tomahawk Cruise Missiles decrease monster defence=their dmg*{DRONE_SHRED_MULTIPLIER}, cost: {DRONE_STAGE_COSTS[1][3]}",
    ],
    [
        f"Stage 1-when you defeat a monster heal {DRONE_HEALS[0]}, cost: {DRONE_STAGE_COSTS[2][0]}",
        f"Stage 2-heal max, when you defeat a monster heal {sum(DRONE_HEALS[:2])}, cost: {DRONE_STAGE_COSTS[2][1]}",
        f"Stage 3-heal max, when you defeat a monster heal {sum(DRONE_HEALS[:3])}, cost: {DRONE_STAGE_COSTS[2][2]}",
        f"Stage 4-heal max, healings(from all source) doubles, cost: {DRONE_STAGE_COSTS[2][3]}",
    ],
    [
        f"Stage 1-when you defeat a monster +money = drone atk, cost: {DRONE_STAGE_COSTS[3][0]}",
        f"Stage 2-when you defeat a monster +{DRONE_T4_MONEY[0]} money, upgrade all stage 1 upgrades into stage 2(doesn't take up one of the {DRONE_SLOTS} slots), cost: {DRONE_STAGE_COSTS[3][1]}",
        f"Stage 3-when you defeat a monster +{DRONE_T4_MONEY[1]} money, make all upgrades at least stage 1(does not take up slot), cost: {DRONE_STAGE_COSTS[3][2]}",
        f"Stage 4-double income (from all sources), upgrade all stage 3 into stage 4(doesn't take up slot), cost: {DRONE_STAGE_COSTS[3][3]}",
    ],
]

DRONE_BUY_MSGS = [
    [
        f"upgrade purchased, drone atk + {DRONE_T1_ATK_GAIN[0]}",
        f"upgrade purchased, drone atk + {DRONE_T1_ATK_GAIN[1]}",
        f"upgrade purchased, drone atk + {DRONE_T1_ATK_GAIN[2]}",
        f"upgrade purchased, drone atk + {DRONE_T1_ATK_GAIN[3]}",
    ],
    [
        "Upgrade purchased, drone will attack at start of fight!",
        f"upgrade purchased, Tomahawk Cruise Missile atk*{DRONE_MISSILE_MULTIPLIER}",
        "Upgrade purchased, Tomahawk Cruise Missiles will now penetrate defence!",
        f"Upgrade purchased, drone will now fire {DRONE_STAGE4_MISSILES - 1} more Tomahawk Cruise Missiles and they reduce monster def!",
    ],
    [
        "upgrade purchased, drone will now heal you after fight!",
        "upgrade purchased, drone healed you max will now heal more after fight!",
        "upgrade purchased, drone healed you max will now heal more after fight!",
        "upgrade purchased, drone will now double your heal!",
    ],
    [
        "upgrade purchased, drone will give extra money after fight!",
        "upgrade purchased, drone is developed and will give extra money after fight!",
        "upgrade purchased, drone is developed and will give extra money after fight!",
        "upgrade purchased, drone is enhanced and will double your income!",
    ],
]

# --- Long story texts ---
TRAMPLE_TEXT = "Harshly, you are shuffled to the ground. Out of your pocket a picture flew out, the picture that stands as your fuel, the picture that supported you up to here, the picture that captures the moment you can never return to...\nthen TRASH\nnot dramatically, not emotionally, the monster trampled on it.\nYou feel a string snapped inside you as the picture shattered into pieces.\nBefore you knew it, you were charging towards the monster with all your might..."

PIC_KILL_TEXT = "From that burst of energy not explainable by science, you regained just enough power to put the down the monster before dropping to the ground\nAfter what felt like eternities later, you dragged yourself up, and moved on, just like what they would have wanted to see..."

# Used when the revive happens with no monster around (shop deaths).
SHOP_REVIVE_TEXT = "Your knees buckle, and the picture slips out of your pocket, landing face-down in the dirt.\nNo monster, no dramatic music, no one to blame — just you, a shop, and a photograph you will never be able to look at the same way again.\nYou pick yourself up anyway. They would have wanted you to."

BLESSED_FUMBLE_TEXT = f"You fumble with the Blessed Emblem while getting ready and pinched yourself, losing {BLESSED_START_HP_LOSS} HP.....\nI am not laughing at you, I promise."

AR_SAMPLE_TEXT = f"You collected some Blight (glowing water) in the dungeon, despite knowing it is radioactive(crused), you still decided to betray your DNA(soul) and melded with(drank) it.\nReading your treatise(report), the demons(people at the summit of glorious achievement) decided to bestow(reward) you with {{arb}} money, given the deepness the sample is from.\nYou feel your body is already regretting this decision, max hp -{AR_MAX_HP_LOSS}!"


# ============================================================
# 2. MODEL
# ============================================================

class Entity:
    """Base class for player and monsters."""

    def __init__(self, hp, atk, df, spd):
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.df = df
        self.spd = spd
        self.extra_atk = 0
        self.extra_df = 0
        self.extra_spd = 0

    @property
    def total_atk(self):
        return self.atk + self.extra_atk

    @property
    def total_df(self):
        return self.df + self.extra_df

    @property
    def total_spd(self):
        return self.spd + self.extra_spd

    def is_alive(self):
        return self.hp > 0


class Drone:
    """RAY-24 state: four upgrade tracks (stage 0-DRONE_STAGES each), DRONE_SLOTS shared slots."""

    def __init__(self):
        self.atk = 0
        self.stages = [0, 0, 0, 0]
        self.slots_used = 0


class Player(Entity):
    """Player state: relic(s), artefact, money, purchases, drone, timers."""

    def __init__(self, relic, artefact):
        super().__init__(START_HP, START_STAT, START_STAT, START_STAT)
        self.money = START_MONEY
        self.artefact = artefact
        # Carrier of Legend holds 3 relics; only one is active at a time.
        if artefact == "carrier":
            self.relics = list(relic)
            self.active_relic_index = 0
            self.relic = self.relics[0]
        else:
            self.relics = None
            self.relic = relic
        self.switches = 0            # Carrier: relic switches performed (max CARRIER_RELICS - 1)

        self.revive_used = False     # Picture of Family
        self.revived_this_fight = False
        self.forbidden_ink = 0       # Forbidden Book: ink currently held (max INK_HOLD)
        self.forbidden_ink_total = 0  # Forbidden Book: total inks ever bought (max LIMIT["ink"])
        self.counters = 0            # E-Sword battery counters
        self.used_e_sword_before = False
        self.coinpot_bonus = 0       # Alchemist's Coinpot pending payout
        self.elixir_timers = []      # one ELIXIR_FIGHTS-fight countdown per elixir drunk
        self.bought_elixir_this_visit = 0
        self.books = {"atk": 0, "def": 0, "hp": 0, "spd": 0, "heal": 0}
        self.bought = {"sword": 0, "shield": 0, "boots": 0, "chicken": 0,
                       "battery": 0, "elixir": 0}
        self.socks_sealed = False    # Cursed Socks activated
        self.pending_hp_multiplier = 1  # Book of Max HP applies after next fight
        self.ar_used = False         # Abyssal Rad-Blood Oath: once per run
        self.vitality_drain_pending = False
        self.drone = Drone()

    # Totals are COMPUTED, never hand-maintained: Meowton's "extra ATK = total SPD"
    # and the drone's ATK can no longer drift out of sync with the stats they
    # derive from, no matter what the shop does to SPD.
    @property
    def total_atk(self):
        total = self.atk + self.extra_atk
        if self.relic == "yd":
            total += self.drone.atk
        if self.relic == "meowton":
            total += self.total_spd
        return total


class Profile:
    """Persistent progress: run count, highest level beaten, achievements."""

    def __init__(self):
        self.runs = 0
        self.highest = 0
        self.ac = {key: False for key in ACH_BIT_ORDER}


def create_monster(level):
    """Create monster stats based on level."""
    stat = level * MONSTER_GROWTH
    return Entity(stat + MONSTER_EXTRA_HP, stat, stat, stat)


# ============================================================
# 3. SAVE
# ============================================================
# Format (unchanged from the original): value = runs<<13 | highest<<8 | ach_bits,
# base-61 encoded (alphabet has no capital I), always exactly 5 characters.

SAVE_ALPHABET = "0123456789ABCDEFGHJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def save_code(profile):
    bits = 0
    for key in ACH_BIT_ORDER:
        bits = (bits << 1) | (1 if profile.ac[key] else 0)

    # load() rejects runs > 1024; cap here so a long-lived save can't self-corrupt.
    runs = min(profile.runs, 1024)
    value = (((runs << 5) | profile.highest) << 8) | bits

    if value == 0:
        code = SAVE_ALPHABET[0]
    else:
        code = ""
        while value > 0:
            code = SAVE_ALPHABET[value % 61] + code
            value //= 61

    return code.rjust(5, SAVE_ALPHABET[0])


def load_code(profile, code):
    """Decode a save code into profile. Returns (ok, message)."""
    if len(code) != 5 or any(char not in SAVE_ALPHABET for char in code):
        return False, "Invalid save code."

    value = 0
    for char in code:
        value = value * 61 + SAVE_ALPHABET.index(char)

    bits = value & 0xFF
    value >>= 8
    highest = value & 0b11111
    value >>= 5
    runs = value

    if runs > 1024 or highest > 30:
        return False, "Corrupted save code."

    profile.runs = runs
    profile.highest = highest
    for offset, key in enumerate(ACH_BIT_ORDER):
        profile.ac[key] = bool((bits >> (7 - offset)) & 1)

    return True, f"\nSave loaded successfully.\nRuns: {runs}   Highest lv. beaten: {highest}\n"


# ============================================================
# 4. ENGINE
# ============================================================
# Every function here mutates game state and returns a list of message strings
# for the UI to display. No print()/input() in this section.

def unlocked_relics(highest):
    return [r for r, lvl in RELIC_UNLOCKS if highest >= lvl]


def unlocked_artefacts(highest):
    return [a for a, lvl in ARTEFACT_UNLOCKS if highest >= lvl]


def vitality_money_penalty(player):
    """Deduct VITALITY_MONEY_LOSS of current money if artefact is Heart of Excessive Vitality."""
    out = []
    if player.artefact == "vitality" and player.money > 0:
        penalty = player.money * VITALITY_MONEY_LOSS
        player.money -= penalty
        out.append({"type": "vitality_penalty", "amount": penalty})
    return out


def coinpot_payout(player):
    """Pay out the Coinpot bonus accumulated on leaving the shop."""
    out = []
    if player.coinpot_bonus > 0:
        if player.drone.stages[3] == 4:
            player.coinpot_bonus *= DRONE_INCOME_MULTIPLIER
        out.append({"type": "coinpot_payout", "amount": player.coinpot_bonus})
        player.money += player.coinpot_bonus
        player.coinpot_bonus = 0
    return out


def try_revive(player, out, in_combat):
    """Picture of Family: revive once to REVIVE_HP. Returns True if it fired.

    EVERY place that can drop the player to 0 HP must call this - combat damage,
    the vitality drain, and the shop's elixir/water-sample self-harm alike -
    otherwise the relic silently fails to pay out on that death.
    """
    if player.hp <= 0 and player.relic == "family" and not player.revive_used:
        # The shop deaths clamp hp to max_hp, so they always arrive here with
        # max HP at 0 or below. You cannot hold 1 HP in a 0-capacity body, so
        # the picture drags that back to 1 as well - a revive into an instant
        # second death would not be a revive.
        player.max_hp = max(player.max_hp, REVIVE_HP)
        player.hp = REVIVE_HP
        player.revive_used = True
        player.revived_this_fight = True
        out.append({"type": "revive", "in_combat": in_combat})
        return True
    return False


# ---------- shop purchases ----------

def blocked(item, reason, **extra):
    return {"type": "buy_blocked", "item": item, "reason": reason, **extra}


def try_buy(player, item, ac):
    """Attempt one shop purchase. Returns (events, died_in_shop)."""
    out = []

    if item in ("sword", "shield", "boots"):
        if player.bought[item] >= LIMIT[item]:
            out.append(blocked(item, "limit"))
        elif item == "boots" and player.artefact == "socks":
            out.append(blocked(item, "socks"))
        elif player.money < PRICE[item]:
            out.append(blocked(item, "money"))
        else:
            player.money -= PRICE[item]
            player.bought[item] += 1
            if item == "sword":
                player.atk += FLAT_ITEM_GAIN
            elif item == "shield":
                player.df += FLAT_ITEM_GAIN
            else:
                player.spd += FLAT_ITEM_GAIN
            out.append({"type": "purchased", "item": item, "cost": PRICE[item]})

    elif item == "chicken":
        out += buy_chicken(player, ac)

    elif item.startswith("book_"):
        key = item.split("_")[1]
        if player.books[key] >= LIMIT["book"]:
            out.append(blocked("book", "limit", key=key))
        elif player.money < PRICE["book"]:
            out.append(blocked("book", "money", key=key))
        elif key == "hp" and player.socks_sealed:
            # Refused before charging (originally this still cost 3 money and a purchase)
            out.append(blocked("book", "sealed", key=key))
        else:
            if key == "heal":
                player.hp = player.max_hp
            elif key == "hp":
                player.pending_hp_multiplier *= BOOK_MULTIPLIER
            elif key == "spd":
                player.spd *= BOOK_MULTIPLIER
            elif key == "atk":
                player.atk *= BOOK_MULTIPLIER
            elif key == "def":
                player.df *= BOOK_MULTIPLIER
            player.books[key] += 1
            player.money -= PRICE["book"]
            out.append({"type": "purchased", "item": "book", "key": key, "cost": PRICE["book"]})

    elif item == "battery":
        if player.relic != "e-sword":
            out.append(blocked("battery", "no_esword"))
        elif player.bought["battery"] >= LIMIT["battery"]:
            out.append(blocked("battery", "limit"))
        elif player.money < PRICE["battery"]:
            out.append(blocked("battery", "money"))
        else:
            player.counters += BATTERY_COUNTERS
            player.money -= PRICE["battery"]
            player.bought["battery"] += 1
            out.append({"type": "purchased", "item": "battery", "cost": PRICE["battery"]})

    elif item == "ink":
        if player.forbidden_ink_total >= LIMIT["ink"]:
            out.append(blocked("ink", "max"))
        elif player.forbidden_ink >= INK_HOLD:
            out.append(blocked("ink", "held"))
        elif player.money < PRICE["ink"]:
            out.append(blocked("ink", "money"))
        else:
            player.forbidden_ink += 1
            player.forbidden_ink_total += 1
            player.money -= PRICE["ink"]
            out.append({"type": "purchased", "item": "ink", "cost": PRICE["ink"],
                        "total": player.forbidden_ink_total})

    elif item == "elixir":
        return buy_elixir(player, ac)

    return out, False


def chicken_variant(relic):
    """Which membership card (if any) governs chicken purchases."""
    return relic if relic in ("bk", "sk", "gk", "dk") else "plain"


def chicken_heal(player, variant):
    """HP a plain/bronze/silver chicken heals, including FARP stage 4."""
    heal = CHICKEN_HEAL[variant]
    if player.drone.stages[2] == 4:  # FARP stage 4 multiplies all healing
        heal *= DRONE_HEAL_MULTIPLIER
    return heal


def buy_chicken(player, ac):
    out = []
    variant = chicken_variant(player.relic)

    if variant in ("bk", "sk"):
        limit = CHICKEN_LIMIT[variant]
        if player.bought["chicken"] >= limit:
            out.append(blocked("chicken", "limit", variant=variant))
        elif player.money < PRICE["chicken"]:
            out.append(blocked("chicken", "money", variant=variant))
        elif player.max_hp - player.hp < CHICKEN_MIN_MISSING:
            out.append(blocked("chicken", "hp_full", variant=variant))
        else:
            heal = chicken_heal(player, variant)
            healed = min(player.hp + heal, player.max_hp) - player.hp
            player.hp += healed
            player.money -= PRICE["chicken"]
            player.bought["chicken"] += 1
            out.append({"type": "purchased", "item": "chicken", "variant": variant,
                        "cost": PRICE["chicken"], "healed": healed})

    elif variant == "gk":
        if player.money < PRICE["chicken"]:
            out.append(blocked("chicken", "money", variant=variant))
        elif player.max_hp - player.hp < CHICKEN_MIN_MISSING:
            out.append(blocked("chicken", "hp_full", variant=variant))
        else:
            healed = player.max_hp - player.hp
            player.hp = player.max_hp
            player.money -= PRICE["chicken"]
            player.bought["chicken"] += 1
            out.append({"type": "purchased", "item": "chicken", "variant": variant,
                        "cost": PRICE["chicken"], "healed": healed})

    elif variant == "dk":
        # Diamond card removes ALL purchase conditions - including having the money.
        healed = player.max_hp - player.hp
        player.hp = player.max_hp
        player.money -= PRICE["chicken"]
        player.bought["chicken"] += 1
        if player.money < 0:
            ac["negative_money"] = True
        out.append({"type": "purchased", "item": "chicken", "variant": variant,
                    "cost": PRICE["chicken"], "healed": healed})

    else:
        if player.bought["chicken"] >= CHICKEN_LIMIT["plain"]:
            out.append(blocked("chicken", "limit", variant=variant))
        elif player.money < PRICE["chicken"]:
            out.append(blocked("chicken", "money", variant=variant))
        elif player.max_hp - player.hp < CHICKEN_MIN_MISSING:
            out.append(blocked("chicken", "hp_full", variant=variant))
        else:
            heal = chicken_heal(player, "plain")
            healed = min(player.hp + heal, player.max_hp) - player.hp
            player.hp += healed
            player.money -= PRICE["chicken"]
            player.bought["chicken"] += 1
            out.append({"type": "purchased", "item": "chicken", "variant": variant,
                        "cost": PRICE["chicken"], "healed": healed})

    return out


def buy_elixir(player, ac):
    out = []
    if player.bought_elixir_this_visit >= LIMIT["elixir"]:
        out.append(blocked("elixir", "visit_limit"))
    elif player.money < PRICE["elixir"]:
        out.append(blocked("elixir", "money"))
    else:
        player.money -= PRICE["elixir"]
        player.bought["elixir"] += 1
        player.bought_elixir_this_visit += 1
        player.max_hp -= player.bought["elixir"]
        if player.hp > player.max_hp:
            player.hp = player.max_hp
        if player.hp <= 0 and not try_revive(player, out, False):
            ac["shop_death"] = True
            out.append({"type": "shop_death", "cause": "elixir"})
            return out, True

        player.spd -= ELIXIR_SPD_LOSS
        player.extra_spd += ELIXIR_EXTRA_SPD
        player.elixir_timers.append(ELIXIR_FIGHTS)
        out.append({"type": "purchased", "item": "elixir", "cost": PRICE["elixir"],
                    "total": player.bought["elixir"]})
    return out, False


def activate_socks(player):
    out = []
    if player.socks_sealed:
        out.append({"type": "socks_blocked", "reason": "already"})
    elif player.hp > SOCKS_MAX_HP:
        out.append({"type": "socks_blocked", "reason": "hp_too_high"})
    else:
        atk_gain = player.max_hp - player.hp
        player.atk += atk_gain
        player.max_hp = player.hp
        player.socks_sealed = True
        out.append({"type": "socks_activated", "atk_gain": atk_gain,
                    "max_hp": player.max_hp})
    return out


def water_sample_reward(player, level):
    """Money the 235 option pays at this level (doubled by drone track 4 stage 4)."""
    base = ((level - 1) // AR_LEVEL_STEP) ** AR_POWER
    return base * DRONE_INCOME_MULTIPLIER if player.drone.stages[3] == 4 else base


def take_water_sample(player, level, ac):
    """Abyssal Rad-Blood Oath's 235 shop option. Returns (events, died_in_shop)."""
    out = []
    if player.ar_used:
        out.append({"type": "water_sample_blocked"})
        return out, False

    player.ar_used = True
    player.max_hp -= AR_MAX_HP_LOSS
    player.hp = min(player.hp, player.max_hp)
    arb = water_sample_reward(player, level)
    player.money += arb  # the reward used to be printed but never actually granted
    out.append({"type": "water_sample", "money": arb, "max_hp_lost": AR_MAX_HP_LOSS})

    if player.hp <= 0 and not try_revive(player, out, False):
        ac["shop_death"] = True
        out.append({"type": "shop_death", "cause": "water_sample"})
        return out, True
    return out, False


def switch_relic(player):
    """Carrier of Legend's 888 shop option."""
    out = []
    if player.switches >= CARRIER_RELICS - 1:
        out.append({"type": "relic_switch_blocked"})
        return out

    player.switches += 1
    player.drone = Drone()
    player.hp = CARRIER_RESET
    player.atk = CARRIER_RESET
    player.df = CARRIER_RESET
    player.spd = CARRIER_RESET

    player.active_relic_index += 1
    player.relic = player.relics[player.active_relic_index]
    out.append({"type": "relic_switched", "relic": player.relic,
                "index": player.active_relic_index})

    if player.relic == "meowton":
        out.append({"type": "meowton_equipped"})
        player.df -= MEOWTON_DEF_LOSS
    if player.relic == "e-sword":
        player.used_e_sword_before = True
        had_sword = player.bought.get("sword", 0) > 0
        if not had_sword:
            player.atk += ESWORD_ATK
            player.counters = 0
        out.append({"type": "esword_equipped", "had_sword": had_sword})
    return out


# ---------- drone upgrades ----------

def apply_drone_stage(player, track):
    """Advance one drone track a single stage and apply its effect.

    Used by BOTH paid purchases and Track 4's free auto-upgrades, so free
    upgrades always grant the real effect (they used to only bump the number).
    """
    d = player.drone
    d.stages[track] += 1
    stage = d.stages[track]

    if track == 0:
        d.atk += DRONE_T1_ATK_GAIN[stage - 1]
    elif track == 2 and stage >= 2:
        player.hp = player.max_hp
    elif track == 3:
        if stage == 2:
            for t in range(3):
                if d.stages[t] == 1:
                    apply_drone_stage(player, t)
        elif stage == 3:
            for t in range(3):
                if d.stages[t] == 0:
                    apply_drone_stage(player, t)
        elif stage == 4:
            for t in range(3):
                if d.stages[t] == 3:
                    apply_drone_stage(player, t)


def buy_drone_upgrade(player, track):
    out = []
    d = player.drone
    if d.slots_used >= DRONE_SLOTS:
        out.append({"type": "drone_blocked", "reason": "slots", "track": track})
    elif d.stages[track] >= DRONE_STAGES:
        out.append({"type": "drone_blocked", "reason": "max", "track": track})
    else:
        stage = d.stages[track] + 1
        cost = DRONE_STAGE_COSTS[track][stage - 1]
        if player.money < cost:
            out.append({"type": "drone_blocked", "reason": "money", "track": track})
        else:
            player.money -= cost
            d.slots_used += 1
            apply_drone_stage(player, track)
            out.append({"type": "drone_upgraded", "track": track, "stage": stage,
                        "cost": cost, "drone_atk": d.atk})
    return out


# ---------- fight ----------

def player_strike(player, monster, out, ac):
    atk = player.total_atk
    df = monster.total_df
    dmg = max(atk - df, MIN_DAMAGE)
    monster_was_full = (monster.hp == monster.max_hp)
    hp_before = monster.hp
    monster.hp -= dmg
    out.append({"type": "player_hit", "dmg": dmg, "player_hp": player.hp,
                "monster_hp_before": hp_before, "monster_hp": monster.hp})
    # 雑魚: a true one-hit kill by YOUR attack (works on level 30 too;
    # ink and drone kills don't count).
    if monster_was_full and monster.hp <= 0:
        ac["one_shot"] = True


def monster_strike(monster, player, out):
    atk = monster.total_atk
    df = player.total_df
    dmg = max(atk - df, MIN_DAMAGE)
    hp_before = player.hp
    player.hp -= dmg
    out.append({"type": "monster_hit", "dmg": dmg, "player_hp_before": hp_before,
                "player_hp": player.hp, "monster_hp": monster.hp})

    try_revive(player, out, True)


def drone_volley(player, monster, out, ac):
    """RAY-24's start-of-fight attack (drone track 2)."""
    stage = player.drone.stages[1]
    if stage == 0:
        return
    datk = player.drone.atk

    if stage < 4:
        if stage == 1:
            dmg = max(datk - monster.df, MIN_DAMAGE)
        elif stage == 2:
            dmg = max(datk * DRONE_MISSILE_MULTIPLIER - monster.df, MIN_DAMAGE)
        else:
            dmg = max(datk * DRONE_MISSILE_MULTIPLIER - max(0, monster.df - datk * DRONE_MISSILE_MULTIPLIER), MIN_DAMAGE)
        out.append({"type": "drone_shot", "shot": 0, "dmg": dmg, "shreds_df": False,
                    "monster_hp_before": monster.hp, "monster_hp": monster.hp - dmg})
        monster.hp -= dmg
    else:
        # Stage 4: DRONE_STAGE4_MISSILES shots, each also shreds DEF by its damage x DRONE_SHRED_MULTIPLIER.
        for shot in range(DRONE_STAGE4_MISSILES):
            dmg = max(datk * DRONE_MISSILE_MULTIPLIER - max(0, monster.df - datk * DRONE_MISSILE_MULTIPLIER), MIN_DAMAGE)
            new_df = max(monster.df - dmg * DRONE_SHRED_MULTIPLIER, 0)
            out.append({"type": "drone_shot", "shot": shot, "dmg": dmg, "shreds_df": True,
                        "monster_hp_before": monster.hp, "monster_hp": monster.hp - dmg,
                        "monster_df_before": monster.df, "monster_df": new_df,
                        "df_loss": monster.df - new_df})
            monster.hp -= dmg
            monster.df = new_df
            if shot == DRONE_STAGE4_MISSILES - 2 and monster.hp <= 0:
                ac["okill"] = True
                out.append({"type": "drone_overkill"})


def fight(player, monster, level, ac):
    """Simulate the whole fight. Returns (player_won, events)."""
    out = []

    # Guaranteed one-shot? Smirk before the fight even starts.
    if player.total_atk >= monster.hp + monster.df:
        out.append({"type": "smirk"})

    if player.relic == "yd":
        drone_volley(player, monster, out, ac)

    # Heart of Excessive Vitality wallet drain. Clamped at 0 so negative money
    # can't heal you, and dying here is a real death - even with ink in your pocket.
    if player.vitality_drain_pending:
        player.vitality_drain_pending = False
        drain = max(0, int(player.money // VITALITY_DRAIN_DIVISOR))
        player.hp -= drain
        out.append({"type": "vitality_drain", "amount": drain, "player_hp": player.hp})
        try_revive(player, out, True)
        if not player.is_alive():
            return False, out

    # Forbidden Ink: instant kill. Don't burn ink on a monster the drone already killed.
    if player.forbidden_ink > 0 and monster.is_alive():
        # Plays the list bottom-up: simplest formula first, the "formula to
        # beat this game" saved for the last ink.
        msg_index = min(LIMIT["ink"] - player.forbidden_ink_total, len(FORBIDDEN_MESSAGES) - 1)
        out.append({"type": "ink_kill", "message_index": msg_index,
                    "final_boss": level == FINAL_LEVEL})
        monster.hp = 0
        player.forbidden_ink -= 1
        return True, out

    while player.is_alive() and monster.is_alive():
        if player.total_spd >= monster.total_spd:
            player_strike(player, monster, out, ac)
            if not monster.is_alive():
                break
            if player.counters > 0:
                player.counters -= 1
                player_strike(player, monster, out, ac)
            else:
                monster_strike(monster, player, out)
        else:
            if player.counters > 0:
                player.counters -= 1
                player_strike(player, monster, out, ac)
            else:
                monster_strike(monster, player, out)
                if not player.is_alive():
                    break
            if monster.is_alive():
                player_strike(player, monster, out, ac)

    won = player.is_alive()
    # The flag survives across the shop, so a revive bought at the elixir counter
    # still pays out on the next monster you put down.
    if won and player.revived_this_fight:
        out.append({"type": "pic_kill"})
        ac["pic_kill"] = True
        player.revived_this_fight = False
    return won, out


def post_fight(player, level):
    """Rewards and upkeep after winning a fight."""
    out = []

    if player.pending_hp_multiplier > 1:
        # A book bought BEFORE the socks sealed you still tries to fire here.
        # The seal wins - otherwise you keep the sealed ATK payout and get your
        # max HP back, which is the whole thing the seal is meant to cost you.
        if player.socks_sealed:
            out.append({"type": "book_hp_fizzled"})
        else:
            player.max_hp = int(player.max_hp * player.pending_hp_multiplier)
            out.append({"type": "book_hp_applied", "max_hp": player.max_hp})
        player.pending_hp_multiplier = 1

    # Money. Track 4 stage 4 "doubles income": it pays everything above
    # again, (DRONE_INCOME_MULTIPLIER - 1) more times.
    player.money += WIN_MONEY
    stages = player.drone.stages
    if stages[3] >= 1:
        player.money += player.drone.atk
    if stages[3] >= 2:
        player.money += DRONE_T4_MONEY[0]
    if stages[3] >= 3:
        player.money += DRONE_T4_MONEY[1]
    if stages[3] >= 4:
        player.money += (DRONE_INCOME_MULTIPLIER - 1) * (
            WIN_MONEY + player.drone.atk + DRONE_T4_MONEY[0] + DRONE_T4_MONEY[1])

    # Drone healing (track 3): the stages add up, and stage 4 "doubles" the
    # total by healing it again, (DRONE_HEAL_MULTIPLIER - 1) more times.
    heals = DRONE_HEALS + [(DRONE_HEAL_MULTIPLIER - 1) * sum(DRONE_HEALS)]
    for threshold, heal in enumerate(heals, 1):
        if stages[2] >= threshold:
            player.hp = min(player.hp + heal, player.max_hp)

    if player.relic == "blessed" and level % BLESSED_EVERY == 0:
        if not player.socks_sealed:
            player.max_hp += BLESSED_MAX_HP
        player.hp = player.max_hp

    # Elixir hangover: extra SPD wears off after each fight following a drink.
    remaining = []
    for timer in player.elixir_timers:
        timer -= 1
        player.extra_spd -= ELIXIR_SPD_DECAY
        if timer > 0:
            remaining.append(timer)
    player.elixir_timers = remaining

    return out


# ============================================================
# 5. TERMINAL UI
# ============================================================

def print_intro():
    print("\nWelcome to FINITE DUNGEONS(demo)!")
    print("Long long ago, in the blessed town of...skipping opening cutscene?! How dare you...\nfine, straight to tutorial...")
    print("--- How to play ---")
    print(f"This is an auto-combat game where life choices and shopping collide, and your aim is to defeat me, the level {FINAL_LEVEL} boss. Why me? Shouldn't have skipped the intro if you want to know😈\nCharacters have 4 stats: HP, ATK DEF and SPD.\nHP is shown in the form hp/max hp, others are shown in the form 'base+extra(total)'\nMonsters gain +{MONSTER_GROWTH} to every stat each level, while you mainly increase stats by purchasing stuff in the shop before each fight, using a (creative) currency called 'money'.\nThe effect of each item is shown to the right of its name, followed by its price and purchase limit.\nTo purchase an item, simply input its number (found at its left) and enter, repeat if you want multiple purchases.\nAll stat increases refer to base stats unless 'extra' is specified.\nAt the start of runs you can pick (usually) 1 'relics' and 'artefacts', which you will unlock more as your highest level reached increases.\nWhen you get defeated you go back to level 1 and can start a new run, probably with new relics and artefacts you unlocked on the previous run.\n\n\n\n-------combat system------\nFighting in each level consists of 2 main phases: hitting the monster and getting hit by the monster, these two phases loop until the HP of you or the monster reaches 0.\nThe character with higher SPD hits first, if SPD ties, I'll let you hit first, cause I'm genuinely nice.\nWhen getting hit, HP decreases by:\nAttacker total ATK-Defender total DEF (HP lost is at least one if this gives <1)\nThis whole fight is automatic.\nThis is a pretty short game and any% should be easily under 2 mins, with 100% nowhere over 5 mins.\nGood luck, and I shall see you at level {FINAL_LEVEL}.\n\n")


# ---------- event rendering ----------
# The engine emits data-only events; ALL wording lives here. A Godot port
# replaces this section with animations/labels and never has to parse prose.
# format_event returns 0+ lines, so events that are silent in the terminal
# (an ordinary Sword purchase) can still drive a sound or a tween elsewhere.

# Blocked-purchase wording, keyed (item, reason). sword/shield/boots fall
# through to the templated version below instead.
BUY_BLOCKED_TEXT = {
    ("chicken", "limit"): "Cannot buy Chicken — purchase limit reached.",
    ("chicken", "money"): "not enough money",
    ("chicken", "hp_full"): "Cannot buy Chicken — your hp is too high and would waste food if you bought chicken!",
    ("book", "limit"): "Cannot buy Book — purchase limit reached.",
    ("book", "money"): "Not enough money.",
    ("book", "sealed"): "max hp sealed by socks, don't ask how or why",
    ("battery", "limit"): "Cannot buy Battery — purchase limit reached.",
    ("battery", "money"): "Cannot buy Battery — not enough money .",
    ("battery", "no_esword"): "Your current sword is wooden, nowhere to put in battery!",
    ("ink", "max"): "You can't write another formula down again, it hurt too much when you got laughed at last time!",
    ("ink", "held"): "You already have a Forbidden Ink in your pocket, don't be greedy, ink spills easily!",
    ("ink", "money"): "Not enough money for Forbidden Ink.",
    ("elixir", "visit_limit"): "Cannot buy Elixir — turn purchase limit reached.",
    ("elixir", "money"): "Not enough money for the Elixir.",
    ("boots", "socks"): "Cannot buy Boots — no Cursed Socks inside sealed spaces.",
}

SHOP_DEATH_TEXT = {
    "elixir": "\nYou chug the elixir, hope it tasted good, as it's the last one you had.\n",
    "water_sample": "\nThe Blight was more cursed than radioactive — your body gives out right there in the shop.\n",
}

DRONE_BLOCKED_TEXT = {
    "slots": "Upgrade failed-slot is full.",
    "max": "This upgrade is already at maximum level.",
    "money": "Upgrade failed-not enough money",
}

SOCKS_BLOCKED_TEXT = {
    "already": "Cursed Socks are already activated.",
    "hp_too_high": f"Cursed Socks cannot activate unless HP is {SOCKS_MAX_HP} or less.",
}


def format_event(ev):
    """Render one engine event into 0+ terminal lines."""
    t = ev["type"]

    # --- shop ---
    if t == "buy_blocked":
        item, reason = ev["item"], ev["reason"]
        # The gold card is the one variant with its own phrasing.
        if item == "chicken" and ev.get("variant") == "gk" and reason == "money":
            return ["Cannot buy Chicken — not enough money"]
        if (item, reason) in BUY_BLOCKED_TEXT:
            return [BUY_BLOCKED_TEXT[(item, reason)]]
        if reason == "limit":
            return [f"Cannot buy {item.capitalize()} — purchase limit reached."]
        if reason == "money":
            return [f"Cannot buy {item.capitalize()} — not enough money."]
        return []

    if t == "purchased":
        item = ev["item"]
        if item == "chicken":
            return ["Chicken purchase successful"]
        if item == "book" and ev.get("key") == "hp":
            return ["Book of Max HP purchased! Max HP will double after your next fight."]
        if item == "ink":
            return [f"Forbidden Ink purchased! ({ev['total']}/{LIMIT['ink']}). Enter the Battle and instant kill the monster!"]
        if item == "elixir":
            return [f"You feel energised, your future self doesn't. SPD-{ELIXIR_SPD_LOSS}, extra spd +{ELIXIR_EXTRA_SPD}"]
        return []  # sword/shield/boots/other books/battery are silent

    if t == "shop_death":
        return [SHOP_DEATH_TEXT[ev["cause"]]]

    if t == "socks_blocked":
        return [SOCKS_BLOCKED_TEXT[ev["reason"]]]

    if t == "socks_activated":
        return [f"Cursed Socks activated!\n"
                f"- ATK increased by {ev['atk_gain']}\n"
                f"- Max HP sealed at {ev['max_hp']}"]

    if t == "water_sample":
        return [AR_SAMPLE_TEXT.format(arb=ev["money"])]

    if t == "water_sample_blocked":
        return ["You can't risk in taking another sample of voidous venom(contaminated water)"]

    if t == "relic_switch_blocked":
        return ["Cannot switch: you are already on your last relic!"]

    if t == "relic_switched":
        return [f"Your power is drained from activating multiple relics, stats go to {CARRIER_RESET}!",
                f"Active relic switched to: {RELIC_NAMES[ev['relic']]}"]

    if t == "meowton_equipped":
        return [f"A law suit is not one that provides defence ability, DEF-{MEOWTON_DEF_LOSS}"]

    if t == "esword_equipped":
        if ev["had_sword"]:
            return ["You swapped your wooden sword from shop into the Automatic Counter E-Sword!"]
        return [f"You equipped the Automatic Counter E-Sword! +{ESWORD_ATK} ATK!"]

    # --- drone ---
    if t == "drone_blocked":
        return [DRONE_BLOCKED_TEXT[ev["reason"]]]

    if t == "drone_upgraded":
        return [DRONE_BUY_MSGS[ev["track"]][ev["stage"] - 1]]

    # --- pre-fight ---
    if t == "vitality_penalty":
        return [f"Heart of Excessive Vitality drains {VITALITY_PERCENT}% of your money: -{ev['amount']:.2f} Money",
                "Apparently, being super healthy is expensive — your wallet got a protein shake tax!"]

    if t == "coinpot_payout":
        return [f"Coinpot bonus: +{ev['amount']:.2f} money before fight!"]

    # --- combat ---
    if t == "smirk":
        return ["'雑魚(pointless peasant)', you smirked"]

    if t == "drone_shot":
        head = ("a", "a second", "a third")[ev["shot"]]
        line = (f"RAY-24 fires {head} Tomahawk Cruise Missile at the monster!\n"
                f"monster hp: {ev['monster_hp_before']}-{ev['dmg']}={ev['monster_hp']}")
        if ev["shreds_df"]:
            line += (f"    monster def: {ev['monster_df_before']}-{ev['df_loss']}"
                     f"={ev['monster_df']}(minimum 0)")
        return [line]

    if t == "drone_overkill":
        return ["Stop wasting ammo on dead bodies!"]

    if t == "vitality_drain":
        return [f"weight of your wallet is draining your health, hp-{ev['amount']}"]

    if t == "ink_kill":
        if ev["final_boss"]:
            return ["Beat game special text not avalible in demo version"]
        return [FORBIDDEN_MESSAGES[ev["message_index"]]]

    if t == "player_hit":
        return [f"\nYou deal {ev['dmg']} dmg!",
                f"Your HP: {ev['player_hp']}       Monster's HP: "
                f"{ev['monster_hp_before']}-{ev['dmg']}={ev['monster_hp']}"]

    if t == "monster_hit":
        return [f"\nMonster deals {ev['dmg']} dmg!",
                f"Your HP: {ev['player_hp_before']}-{ev['dmg']}={ev['player_hp']}"
                f"       Monster's HP: {ev['monster_hp']}"]

    if t == "revive":
        return [TRAMPLE_TEXT if ev["in_combat"] else SHOP_REVIVE_TEXT]

    if t == "pic_kill":
        return [PIC_KILL_TEXT]

    # --- post-fight ---
    if t == "book_hp_applied":
        return [f"Book of Max HP activates! Your max HP is now {ev['max_hp']}."]

    if t == "book_hp_fizzled":
        return ["The Book of Max HP fizzles out against your sealed max HP. Cursed Socks don't negotiate."]

    raise ValueError(f"unknown event type: {t}")


# Session-only UI settings (not part of the save code).
# show_hits: print each ordinary player/monster hit; toggled in Options.
# colours: colour text by kind (TEXT_COLOURS); toggled in Options or main menu 7.
# Off leaves only the grey of greyed-out items and flavour lines.
UI = {"show_hits": True, "colours": COLOURS_ON}

# Colour of each event's lines (kinds are the keys of TEXT_COLOURS; missing = normal).
EVENT_COLOUR = {
    "buy_blocked": "warning", "purchased": "good", "shop_death": "bad",
    "socks_blocked": "warning", "socks_activated": "good", "water_sample": "story",
    "water_sample_blocked": "warning", "relic_switch_blocked": "warning",
    "drone_blocked": "warning", "drone_upgraded": "good",
    "vitality_penalty": "money", "coinpot_payout": "money",
    "smirk": "good", "drone_shot": "good", "drone_overkill": "good",
    "vitality_drain": "bad", "ink_kill": "good",
    "player_hit": "good", "monster_hit": "bad",
    "revive": "story", "pic_kill": "story",
    "book_hp_applied": "good", "book_hp_fizzled": "warning",
}


def paint(kind, text):
    """Colour text as kind ("good", "bad", ...) when colours are on."""
    if not UI["colours"] or kind not in TEXT_COLOURS:
        return text
    return ansi(TEXT_COLOURS[kind]) + text + RESET


def pause():
    time.sleep(MENU_PAUSE)


def render_events(events):
    for ev in events:
        if not UI["show_hits"] and ev["type"] in ("player_hit", "monster_hit"):
            continue
        kind = EVENT_COLOUR.get(ev["type"], "normal")
        for line in format_event(ev):
            print(paint(kind, line))


def shop_line(text, greyed):
    print(GREY + text + RESET if greyed else text)


def print_relic_descriptions(relics):
    print("\n--- RELIC DESCRIPTIONS ---")
    for r in relics:
        print(f"{RELIC_DESCRIPTIONS.get(r, 'No description.')}")
    input("\nPress Enter to return...")


def print_artefact_descriptions(artefacts):
    print("\n--- ARTEFACT DESCRIPTIONS ---")
    for a in artefacts:
        print(f"{ARTEFACT_DESCRIPTIONS.get(a, 'No description.')}")
    input("\nPress Enter to return...")


def display_player_and_next_monster(player, level):
    """Show current player stats and next monster stats."""
    print("\n--- Player Stats ---")
    print(f"HP: {player.hp}/{player.max_hp}")

    for label, base, total in (("ATK", player.atk, player.total_atk),
                               ("DEF", player.df, player.total_df),
                               ("SPD", player.spd, player.total_spd)):
        extra = total - base
        if extra != 0:
            print(f"{label}: {base}{extra:+d} ({total})")
        else:
            print(f"{label}: {base}")

    if player.relic == "family" and not player.revive_used:
        print("Revives: 1")
    if player.counters > 0:
        print(f"Counters: {player.counters}")

    m = create_monster(level)
    print(f"\nNext Monster - Level {level}")
    print(f"HP: {m.hp}")
    print(f"ATK: {m.atk}")
    print(f"DEF: {m.df}")
    print(f"SPD: {m.spd}")


def drone_menu(player, level):
    """RAY-24 upgrade menu (shop option 1 with the drone relic)."""
    while True:
        d = player.drone
        print(paint("money", f"Money: {player.money:.2f}"))
        print(f"RAY-24    Drone atk:{d.atk}    Upgrade slot {d.slots_used}/{DRONE_SLOTS}")
        for track in range(4):
            print(f"\n{track + 1} {DRONE_TRACK_NAMES[track]}-stage {d.stages[track]}/{DRONE_STAGES}")
            for stage in range(1, DRONE_STAGES + 1):
                desc = DRONE_STAGE_DESCS[track][stage - 1].format(atk=d.atk, atk2=d.atk * DRONE_MISSILE_MULTIPLIER)
                # Readable: stages you own plus the next one you can buy.
                shop_line(desc, greyed=stage > d.stages[track] + 1)
        print("\n0 return to shop")
        print(stat_bar(player, level))
        try:
            choice = int(input("> "))
        except ValueError:
            print(paint("warning", "Invalid input, please try again."))
            continue
        if choice == 0:
            break
        if choice in (1, 2, 3, 4):
            render_events(buy_drone_upgrade(player, choice - 1))
            continue
        print(paint("warning", "Invalid input, please try again"))


def describe_mine(player):
    """Descriptions of the relic(s) and artefact this run is using."""
    relics = [r for r in (player.relics or [player.relic]) if r]
    if relics:
        print_relic_descriptions(relics)
    else:
        print("You have no relic.")
    if player.artefact:
        print_artefact_descriptions([player.artefact])
    else:
        print("You have no artefact.")


def options_menu(player, profile):
    """Settings and run info: option 3 of the pre-fight menu."""
    while True:
        print("\n--- Options ---")
        print("1 Turn " + ("off" if UI["show_hits"] else "on") + " printing normal attacks in fight")
        print("2 Describe my relic and artefact")
        print("3 Show save code")
        print("4 Turn " + ("off" if UI["colours"] else "on") + " colours")
        print("0 Back")
        choice = input("> ")
        if choice == "0":
            return
        if choice == "1":
            UI["show_hits"] = not UI["show_hits"]
            print("Normal attacks will " + ("" if UI["show_hits"] else "not ") + "be printed.")
        elif choice == "2":
            describe_mine(player)
        elif choice == "3":
            print("Save code:", save_code(profile))
        elif choice == "4":
            UI["colours"] = not UI["colours"]
            print("Colours are now " + ("on." if UI["colours"] else "off."))
        else:
            print(paint("warning", "Invalid input, please try again"))


def stat_bar(player, level):
    """The calculator's top bar, printed above each prompt during a run."""
    return (f"HP {player.hp}/{player.max_hp}  ${player.money:.2f}"
            f"  A{player.total_atk} D{player.total_df} S{player.total_spd}  | Next: Lv{level}")


def shop_menu(player, level):
    """Print the numbered shop list; returns {typed number: item}."""
    options = {}
    i = 1

    # Slot 1: drone upgrade menu / Sword / Battery
    if player.relic == "yd":
        print(f"{i} Ray-24 upgrade menu")
        options[str(i)] = "yds"
        i += 1
    elif player.relic != "e-sword" and not player.used_e_sword_before:
        left = LIMIT["sword"] - player.bought["sword"]
        shop_line(f"{i} Sword (+{FLAT_ITEM_GAIN} atk) - {PRICE['sword']} ({left} left)", left == 0)
        options[str(i)] = "sword"
        i += 1
    else:
        left = LIMIT["battery"] - player.bought["battery"]
        shop_line(f"{i} Battery for Countering - {PRICE['battery']} ({left} left)", left == 0)
        options[str(i)] = "battery"
        i += 1

    # Shield
    left = LIMIT["shield"] - player.bought["shield"]
    shop_line(f"{i} Shield (+{FLAT_ITEM_GAIN} def) - {PRICE['shield']} ({left} left)", left == 0)
    options[str(i)] = "shield"
    i += 1

    # Boots (blocked by Cursed Socks)
    if player.artefact == "socks":
        shop_line(f"{i} Boots (+{FLAT_ITEM_GAIN} spd) - cannot buy due to Cursed Socks-some bad curse will occur if you try putting that sock into a sealed space, so this game might crash", True)
        options[str(i)] = "boots"  # keep the printed number selectable so try_buy() can explain why
    else:
        left = LIMIT["boots"] - player.bought["boots"]
        shop_line(f"{i} Boots (+{FLAT_ITEM_GAIN} spd) - {PRICE['boots']} ({left} left)", left == 0)
        options[str(i)] = "boots"
    i += 1

    # Chicken
    if player.relic == "gk":
        left = 1
        text = (f"{i} Chicken (heal max if missing >={CHICKEN_MIN_MISSING})"
                f" - {PRICE['chicken']} (∞ left)")
    elif player.relic == "dk":
        left = 1
        text = f"{i} Chicken (heal max) - {PRICE['chicken']} (∞ left)"
    else:
        card = chicken_variant(player.relic)  # "plain", "bk" or "sk"
        left = CHICKEN_LIMIT[card] - player.bought["chicken"]
        text = (f"{i} Chicken (+{chicken_heal(player, card)} hp if missing >={CHICKEN_MIN_MISSING})"
                f" - {PRICE['chicken']} ({left} left)")
    shop_line(text, left == 0)
    options[str(i)] = "chicken"
    i += 1

    # Books
    for key, name in (("atk", f"Book of Attack (x{BOOK_MULTIPLIER} atk)"),
                      ("def", f"Book of Defence (x{BOOK_MULTIPLIER} def)"),
                      ("spd", f"Book of Speed (x{BOOK_MULTIPLIER} spd)"),
                      ("hp", f"Book of Max HP (x{BOOK_MULTIPLIER} max hp)"),
                      ("heal", "Book of Healing (hp → max hp)")):
        left = LIMIT["book"] - player.books[key]
        greyed = left == 0 or (key == "hp" and player.socks_sealed)
        shop_line(f"{i} {name} - {PRICE['book']} ({left} left)", greyed)
        options[str(i)] = f"book_{key}"
        i += 1

    # Elixir (The Damned Proof of Devotion)
    if player.artefact == "devotion":
        left = LIMIT["elixir"] - player.bought_elixir_this_visit
        shop_line(f"{i} Elixir (*onster) - max hp-{player.bought['elixir'] + 1}, spd-{ELIXIR_SPD_LOSS}, extra spd+{ELIXIR_EXTRA_SPD}, extra spd -{ELIXIR_SPD_DECAY} after fight for {ELIXIR_FIGHTS} turns - {PRICE['elixir']} ({left} left)", left == 0)
        options[str(i)] = "elixir"
        i += 1

    # Forbidden Ink (Forbidden Book)
    if player.relic == "forbidden":
        left = LIMIT["ink"] - player.forbidden_ink_total
        shop_line(f"{i} Forbidden Ink (insta-kill next monster when entering next fight) - {PRICE['ink']} ({left} left)", left == 0)
        options[str(i)] = "ink"
        i += 1

    print("0 Back")
    if player.artefact == "ar":
        # Same helper the payout uses, so the advertised figure includes the
        # drone track-4 stage-4 doubling instead of understating it.
        print(f"235 Test water sample (max hp-{AR_MAX_HP_LOSS}, money+{water_sample_reward(player, level)})")
    if player.artefact == "socks":
        print("777 Activate cursed socks")
    if player.artefact == "carrier":
        print("888 Switch to next relic (currently active: {})".format(
            RELIC_NAMES.get(player.relic, player.relic)))
    return options


def shop(player, level, ac):
    """The shop submenu. Returns 'dead' if the player dies shopping, else None."""
    while True:
        pause()
        print("\n" + paint("money", f"--- Shop ---   Money: {player.money:.2f}"))
        options = shop_menu(player, level)
        print(stat_bar(player, level))
        choice = input("> ")

        if choice == "0":
            return None
        if choice == "777" and player.artefact == "socks":
            render_events(activate_socks(player))
            continue
        if choice == "235" and player.artefact == "ar":
            events, dead = take_water_sample(player, level, ac)
            render_events(events)
            if dead:
                return "dead"
            continue
        if choice == "888" and player.artefact == "carrier":
            render_events(switch_relic(player))
            continue
        if choice not in options:
            print(paint("warning", "Invalid input, please try again"))
            continue

        item = options[choice]
        if item == "yds":
            drone_menu(player, level)
            continue

        events, dead = try_buy(player, item, ac)
        render_events(events)
        if dead:
            return "dead"


def stats_screen(player, level):
    """The shop's old stats block, on its own screen."""
    display_player_and_next_monster(player, level)
    input("\nPress Enter to return...")


class QuitGame(Exception):
    """Raised after the player chose Quit; the program then stops."""


def confirm_quit(player, level):
    print("\nQuit the game? Levels beaten this run still count.")
    print("1 Yes, quit and show my save code")
    print("0 No, go back")
    print(stat_bar(player, level))
    return input("> ") == "1"


def pre_fight(player, level, profile):
    """Menu before each fight (the calculator's layout). Returns 'dead' (died
    in the shop), 'quit', or None once the fight should start."""
    ac = profile.ac
    player.bought_elixir_this_visit = 0
    while True:
        pause()
        print(f"\n--- Level {level} ---")
        print("1 Shop\n2 Stats\n3 Options\n4 Quit game (shows save code)\n0 Start fight")
        print(stat_bar(player, level))
        choice = input("> ")

        if choice == "1":
            if shop(player, level, ac) == "dead":
                return "dead"
        elif choice == "2":
            stats_screen(player, level)
        elif choice == "3":
            options_menu(player, profile)
        elif choice == "4":
            if confirm_quit(player, level):
                return "quit"
        elif choice == "0":
            # Coinpot charges up the moment you leave for the fight.
            if player.artefact == "coinpot" and player.money >= COINPOT_STEP:
                player.coinpot_bonus += (player.money // COINPOT_STEP) * COINPOT_PAY
            if player.artefact == "vitality":
                player.vitality_drain_pending = True

            atk = player.total_atk
            spd = player.total_spd
            df = player.total_df
            m = create_monster(level)
            print(paint("muted", f"\nYou will deal {atk}-{m.df}={max(atk - m.df, MIN_DAMAGE)}(at least {MIN_DAMAGE}) dmg,"))
            print(paint("muted", f"\nMonster will deal {m.atk}-{df}={max(m.atk - df, MIN_DAMAGE)}(at least {MIN_DAMAGE}) dmg"))
            print(paint("muted", f"Your spd is {spd} compared to the monster's {m.spd},"))
            if spd >= m.spd:
                print(paint("muted", "so you will go first!"))
            else:
                print(paint("muted", "so the monster will go first!"))
            return None
        else:
            print(paint("warning", "Invalid input, please try again"))


# ---------- run setup and main loop ----------

def choose_artefact(artefacts):
    if not artefacts:
        print("No artefacts unlocked yet! You must continue without one.")
        return None
    while True:
        print("\nChoose, with all your brain power, one artefact:")
        print("0 No artefact")
        for i, a in enumerate(artefacts, 1):
            print(f"{i} {ARTEFACT_MENU_NAMES[a]}")
        print("505 show artefact descriptions")
        try:
            choice = int(input("> "))
        except ValueError:
            print(paint("warning", "Invalid input. Please enter a number."))
            continue
        if choice == 0:
            return None
        if choice == 505:
            print_artefact_descriptions(artefacts)
            continue
        if 1 <= choice <= len(artefacts):
            return artefacts[choice - 1]
        print(paint("warning", "Invalid choice. Select a valid artefact number."))


def choose_relic(relics):
    while True:
        print("0 No relic")
        for i, r in enumerate(relics, 1):
            print(f"{i} {RELIC_NAMES[r]}")
        print("505 show relics description")
        try:
            choice = int(input("> "))
        except ValueError:
            print(paint("warning", "Invalid input. Please enter a number."))
            continue
        if choice == 0:
            return None
        if choice == 505:
            print_relic_descriptions(relics)
            continue
        if 1 <= choice <= len(relics):
            return relics[choice - 1]
        print(paint("warning", "Invalid choice. Select a valid relic number."))


def choose_carrier_relics(relics):
    print(f"You chose the Carrier of Legend! Pick {CARRIER_RELICS} relics in order (only the first one is active at start).")
    picked = []
    for n in range(1, CARRIER_RELICS + 1):
        while True:
            print(f"\nSelect relic #{n}:")
            for i, r in enumerate(relics, 1):
                print(f"{i} {RELIC_NAMES[r]}")
            print("505 show relic descriptions")
            raw = input("> ")
            if raw == "505":
                print_relic_descriptions(relics)
                continue
            try:
                choice = int(raw)
            except ValueError:
                print(paint("warning", "Invalid input."))
                continue
            if 1 <= choice <= len(relics):
                chosen = relics[choice - 1]
                if chosen in picked:
                    print(paint("warning", "You already picked that relic."))
                    continue
                picked.append(chosen)
                break
            print(paint("warning", "Invalid choice."))
    return picked


def end_of_run(profile, level_died_at):
    profile.highest = max(profile.highest, level_died_at - 1)
    print(paint("bad", f"\nYou died! Level completed this run: {level_died_at - 1}.   Highest: {profile.highest}"))


def run(profile):
    profile.runs += 1
    relics = unlocked_relics(profile.highest)
    artefacts = unlocked_artefacts(profile.highest)

    artefact = choose_artefact(artefacts)

    print("\nChoose, very carefully, your relic:")
    if artefact == "carrier":
        player = Player(choose_carrier_relics(relics), artefact)
    else:
        player = Player(choose_relic(relics), artefact)

    # Start-of-run effects
    if player.relic == "e-sword":
        player.atk += ESWORD_ATK
        print(f"You have your own sword, not needing the shop one! +{ESWORD_ATK} ATK!")
    if artefact == "vitality":
        player.max_hp = VITALITY_HP
        player.hp = VITALITY_HP
    if player.relic == "meowton":
        player.df -= MEOWTON_DEF_LOSS
        print(f"A law suit is not one that provides defence ability, DEF-{MEOWTON_DEF_LOSS}")
    # Blessed Emblem pinches you if it's anywhere in your luggage.
    blessed_packed = ("blessed" in player.relics) if player.relics else (player.relic == "blessed")
    if blessed_packed:
        player.hp -= BLESSED_START_HP_LOSS
        print(paint("story", BLESSED_FUMBLE_TEXT))

    for level in range(1, FINAL_LEVEL + 1):
        result = pre_fight(player, level, profile)
        if result == "quit":
            # Quitting ends the run like a death would: levels beaten count.
            profile.highest = max(profile.highest, level - 1)
            print(f"\nYou left the dungeon. Highest: {profile.highest}")
            print("Save code:", save_code(profile))
            raise QuitGame()
        if result == "dead":
            end_of_run(profile, level)
            print(f"\nRun {profile.runs} finished! \n")
            print("Save code:", save_code(profile))
            return

        render_events(vitality_money_penalty(player))
        render_events(coinpot_payout(player))

        won, events = fight(player, create_monster(level), level, profile.ac)
        render_events(events)

        if not won:
            end_of_run(profile, level)
            if player.money >= RICH_MONEY:
                profile.ac["drich"] = True
            if level == HARD_MODE_LEVEL and player.relic == "meowton" and player.artefact == "socks":
                profile.ac["hmode"] = True
                print("I don't balme you, you just attempted the hardest difficulty")
            print(f"\nRun {profile.runs} finished! \n")
            print("Save code:", save_code(profile))
            return

        render_events(post_fight(player, level))

    # Loop completed: level 30 beaten.
    print(paint("good", f"\nYou beat level {FINAL_LEVEL}. You win!"))
    profile.highest = FINAL_LEVEL
    if profile.runs <= FEW_RUNS:
        profile.ac["trun"] = True
        print(paint("good", "You beat the game with the fewest runs possible!"))
    print("Save code:", save_code(profile))


# ---------- menu screens ----------

def print_achievements(profile):
    print("---unlocked achievements---")
    for key, title, hint in ACHIEVEMENT_DISPLAY:
        if profile.ac[key]:
            print(title)
            print(GREY + hint + "\n" + RESET)
    print("---locked achievements---")
    for key, title, hint in ACHIEVEMENT_DISPLAY:
        if not profile.ac[key]:
            print(title)
            if key in ACHIEVEMENT_SECRET_HINTS:
                hint = "?????????"
            print(GREY + hint + "\n" + RESET)


def unlock_label(key):
    return GREY + f"(unlocks after beating lv. {UNLOCK_LEVEL[key]})" + RESET


def print_library(profile):
    print("\n---relics---")
    print(f"Picture of Family \nRevives once to {REVIVE_HP} HP when defeated.")
    print(GREY + "'If you don't believe in yourself, believe in me who believe in you'\n" + RESET)

    print(f"Blessed Emblem \nEvery {BLESSED_EVERY} monsters defeated, +{BLESSED_MAX_HP} max HP and fully heals. hp-{BLESSED_START_HP_LOSS} when run starts")
    print(GREY + "This Emblem is really blessed, definitely, trust.\n" + RESET)

    print(f"Forbidden Book \nUnlocks in the shop: ink-costs {PRICE['ink']}, max purchase {LIMIT['ink']}, max hold {INK_HOLD}, automatically consumed at start of fight and defeats the monster.")
    print(GREY + "What can be more cursed than a book full of equations?\n" + RESET)

    print("K*C bronze membership card " + unlock_label("bk") + f" \nChickens heal {CHICKEN_HEAL['bk'] - CHICKEN_HEAL['plain']} more HP")
    print(GREY + "A membership card that gets you extra food on order!\n" + RESET)

    print("K*C silver membership card " + unlock_label("sk") + f" \nChickens heal {CHICKEN_HEAL['sk'] - CHICKEN_HEAL['plain']} more HP, max purchase +{CHICKEN_LIMIT['sk'] - CHICKEN_LIMIT['plain']}")
    print(GREY + "Don't ask how a membership card increases stock, it's what you call a 'Fantasy world'\n" + RESET)

    print("RAY-24 Drone " + unlock_label("yd") + f" \nHave a drone to help you fight, having extra atk=its atk! Buy up to {DRONE_SLOTS} accumulative upgrades")
    print(GREY + "This relic is made in respect to my friend who managed to looked through this unimaginable messy code and spent a few hours given me insights\n" + RESET)

    print("K*C gold membership card " + unlock_label("gk") + f" \nChickens heal max if missing >={CHICKEN_MIN_MISSING}, no max purchase limit")
    print(GREY + "Shouldn't infinite K*C chicken damage your health? Anyways, eating ALWAYS heals...\n" + RESET)

    print("Meowton's 2nd lawsuit " + unlock_label("meowton") + f" \n-{MEOWTON_DEF_LOSS} DEF upon equipping, gain extra ATK = total SPD")
    print(GREY + "I know Newton's 2nd law is multiply, but I need to consider game balance ok?\n" + RESET)

    if profile.highest < UNLOCK_LEVEL["dk"]:
        print("????????" + unlock_label("dk") + " \n???????????\n")
    else:
        print("K*C diamond membership card " + unlock_label("dk") + " \nChickens heal max, remove all conditions required to purchase chickens\n")
        print(GREY + "Sorry for the 'yet another K*C card' disappointment, I am not a very creative person" + RESET)

    print("---artefacts--")
    print("The Damned Proof of Devotion " + unlock_label("devotion") + f" \nElixir unlocked in shop: costs {PRICE['elixir']}, max HP - [elixir bought], SPD-{ELIXIR_SPD_LOSS}, extra SPD+{ELIXIR_EXTRA_SPD}; for next {ELIXIR_FIGHTS} fights, -{ELIXIR_SPD_DECAY} extra SPD after fight, can only buy one per turn.")
    print(GREY + "But to some soul, isn't energy drinks their only 'elixir'?\n" + RESET)

    print("Cursed Socks " + unlock_label("socks") + f" \nBoots sealed. When HP <= {SOCKS_MAX_HP}, unlocks option in the shop to decrease and seal max HP to current HP, gaining the same amount of ATK.")
    print(GREY + "Socks in certain conditions can really have a high ATK, don't find it out the hard way...\n" + RESET)

    print("Abyssal Rad-Blood Oath " + unlock_label("ar") + f" \nUnlocks a shop option once per run to lose {AR_MAX_HP_LOSS} max HP, gain money = {{level beaten/{AR_LEVEL_STEP} (round down)}}{AR_POWER_SIGN}.")
    print(GREY + "A contract to test suspicious water samples in the dungeon, a world without power oppression wouldn't be a realistic one, would it?\n" + RESET)

    print("Alchemist's Coinpot " + unlock_label("coinpot") + f" \nEvery {COINPOT_STEP} money left before fight gives {COINPOT_PAY} money.")
    print(GREY + "So...do the monsters transfer money to you digitally when they get defeated?\n" + RESET)

    print("Heart of Excessive Vitality " + unlock_label("vitality") + f" \nStart with {VITALITY_HP} HP but lose {VITALITY_PERCENT}% money before fights, at start of fight HP - {VITALITY_DRAIN_TEXT}.")
    print(GREY + "I hope that is the right use of 'vitality', I don't fully understand that word till this day\n" + RESET)

    print("Carrier of Legend " + unlock_label("carrier") + f" \nChoose {CARRIER_RELICS} relics, switch from the 1st to 2nd to 3rd one. All stats except max HP drain to {CARRIER_RESET} at relic switch.")
    print(GREY + "The biggest relic is a drone, so the volume of this bag is realistic...I hope?\n" + RESET)


def print_credits():
    print("\nGuido van Rossum, creator of Python, who provided coding language to me")
    print("\nSteve Jobs, co-founder of Apple, who provided my device to me")
    print("\nNick Holonyak Jr., inventor of the practical LED, who provided glowing screens to me")
    print("\nOleg Losev, LED research pioneer, who provided more glowing things to type on to me")
    print("\nAlessandro Volta, inventor of the battery, who provided portable power to me")
    print("\nMichael Faraday, discoverer of electromagnetic induction, who provided electricity generation to me")
    print("\nTim Berners-Lee, creator of the World Wide Web, who provided internet access to me for reserches")
    print("\nLarry Page and Sergey Brin, founders of Google, who provided more searching ability to me")
    print("\nLinus Torvalds, creator of Linux, who provided computing foundations to me")
    print("\nDennis Ritchie, creator of C language, who provided programming foundations to me")
    print("\nThe inventors of WiFi, who provided freedom(wireless connection) to me")
    print("\nThe inventors of electricity, who provided energy to me(literally and metaphorically)")
    print("\nThe inventor of the chair, who provided comfort to me while coding")
    print("\n---special credits---")
    print("pianoplayer1224, who distracted me from making this game by giving me a code to solve, and by giving me a game of theirs to play, and by saying 'He wasn't impressed' at this very moment I am typing. But more importantly, for their contributions to my knowledge of coding and contributions to all angles of this game as the first playtester.")
    print("\nRachmaninov and blackpenredpen, who provided me with emotional support by writing a 2nd piano concerto and made YouTube videos respectively. (Check out Rach 2 and blackpenredpen if you don't know them!!)")
    print("\nMy family, who provided me with love, shelter, and most importantly, food, when I am making this game")
    print("\nAll my friends who played the paper version of this game, contributing huge to the balancing and shaping of this game")
    print("\nAnd of course, YOU, the player, who decided to read the credits instead of playing the game, proving to me how my game is not even as entertaining as some random credits, providing me with emotional damage\n")


def prompt_save_code(profile, cancel_hint, pause_first=False):
    while True:
        if pause_first:
            pause()
        code = input(f"Enter save code (or 0 to {cancel_hint}, there is no capital letter i): ").strip()
        if code == "0":
            return
        ok, message = load_code(profile, code)
        print(message if ok else paint("warning", message))
        if ok:
            return
        print(paint("warning", "Please try again.\n"))


def main(profile):
    prompt_save_code(profile, "start a new game", pause_first=True)

    while True:
        pause()
        print("MAIN MENU\n1 start run\n2 achievements\n3 library\n4 credits\n5 input save code\n6 obtain save code"
              "\n7 turn colours " + ("off" if UI["colours"] else "on"))
        try:
            act = int(input("> "))
        except ValueError:
            print(paint("warning", "Invalid input, please try again."))
            continue
        if act == 1:
            run(profile)
        elif act == 2:
            print_achievements(profile)
        elif act == 3:
            print_library(profile)
        elif act == 4:
            print("CREDITS\n\nI'd like to give HUGE thanks to these people, without you, this game wouldn't be possible.")
            print_credits()
        elif act == 5:
            prompt_save_code(profile, "cancel")
        elif act == 6:
            print("Save code:", save_code(profile))
        elif act == 7:
            UI["colours"] = not UI["colours"]
            print("Colours are now " + ("on." if UI["colours"] else "off."))
        else:
            print(paint("warning", "Invalid input, please try again"))


if __name__ == "__main__":
    print("Finite Dungeons by Timothy")
    print("Copyright © 2026 Timothy Tang")
    print_intro()
    profile = Profile()
    try:
        main(profile)
    except (KeyboardInterrupt, EOFError):
        raise
    except QuitGame:
        pass   # the save code is already printed
    except Exception:
        traceback.print_exc()
        print("sorry,an unknown error occurred...\nDo you mind telling me what happened?")
        print("Save code:", save_code(profile))
