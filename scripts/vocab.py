"""Controlled vocabularies used to tag workouts from descriptions and captions.

Patterns are matched against text normalised by norm(): lower case, apostrophes
removed, hyphens/slashes turned into spaces, whitespace collapsed.
"""
import re


def norm(text):
    text = text.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"'", "", text)
    text = re.sub(r"[-/–—]", " ", text)
    return re.sub(r"\s+", " ", text)


N2 = r"(?:2|two|ii)"
N3 = r"(?:3|three|iii)"
N1 = r"(?:1|one|i)"

# canonical pose -> (regex alternatives, pose categories)
# Categories follow the spreadsheet's "Types of Poses" vocabulary.
POSES = {
    "Downward-Facing Dog": ([r"down(?:ward)? ?(?:facing )?dog", r"downdog"], []),
    "Three-Legged Dog": ([r"three legged (?:down(?:ward)? ?(?:facing )?)?dog", r"3 legged dog"], []),
    "Upward-Facing Dog": ([r"up(?:ward)? ?(?:facing )?dog", r"updog"], ["Backbend"]),
    "Puppy": ([r"puppy(?: pose)?", r"extended puppy"], ["Backbend"]),
    "Child's Pose": ([r"childs? pose", r"\bchilds\b"], ["Seated", "Forward Bend"]),
    "Cat-Cow": ([r"cat (?:and )?cow", r"cat cows"], ["Backbend"]),
    "Tabletop": ([r"(?<!reverse )table ?top"], []),
    "Reverse Tabletop": ([r"reverse table ?top"], ["Backbend"]),
    "Bird-Dog": ([r"bird dog"], ["Core"]),
    "Tiger Curls": ([r"tiger curls?"], ["Core"]),
    "Thread the Needle": ([r"thread (?:the|your) needle", r"thread the needle"], ["Twists"]),
    "Cobra": ([r"cobra"], ["Backbend"]),
    "Sphinx": ([r"sphinx"], ["Backbend"]),
    "Locust": ([r"locust"], ["Backbend"]),
    "Bow": ([r"\bbow pose", r"\b(?:half|full|floor|kneeling) bow\b",
             r"\b(?:into|to) (?:your |a )?bow\b(?! (?:forward|down|over|your))"], ["Backbend"]),
    "Camel": ([r"camel"], ["Backbend"]),
    "Wheel": ([r"\bwheel\b(?! of)", r"upward bow"], ["Backbend"]),
    "Bridge": ([r"bridge"], ["Backbend", "Reclined"]),
    "Fish": ([r"fish pose", r"\bfish\b"], ["Backbend", "Reclined"]),
    "Wild Thing": ([r"wild thing"], ["Backbend", "Arm Balance"]),
    "Dancer": ([r"dancers? pose", r"\bdancer\b"], ["Standing Balance", "Backbend"]),
    "Plank": ([r"(?<!side )(?<!reverse )\bplanks?\b"], ["Core"]),
    "Side Plank": ([r"side planks?"], ["Core", "Arm Balance"]),
    "Reverse Plank": ([r"reverse planks?"], ["Backbend"]),
    "Forearm Plank": ([r"forearm planks?"], ["Core"]),
    "Chaturanga": ([r"chaturanga"], ["Core"]),
    "Vinyasa": ([r"vinyasa"], []),
    "Sun Salutation": ([r"sun salutations?", r"surya namaskar"], ["Standing"]),
    "Boat": ([r"\bboat\b", r"high low boat"], ["Core", "Seated"]),
    "Mountain": ([r"mountain pose", r"\bmountain\b"], ["Standing"]),
    "Forward Fold": ([r"(?<!wide )(?<!seated )(?<!legged )forward folds?", r"standing folds?", r"ragdoll", r"rag doll"], ["Forward Bend", "Standing"]),
    "Halfway Lift": ([r"halfway lift", r"half lift"], ["Standing"]),
    "Wide-Legged Forward Fold": ([r"wide (?:legged )?(?:forward )?folds?", r"wide leg(?:ged)? folds?", r"straddle fold"], ["Forward Bend", "Standing"]),
    "Seated Forward Fold": ([r"seated (?:forward )?folds?", r"paschimottanasana"], ["Forward Bend", "Seated"]),
    "Head to Knee": ([r"head to (?:bent )?knee"], ["Forward Bend", "Seated"]),
    "Pyramid": ([r"pyramid"], ["Forward Bend", "Standing"]),
    "Chair": ([r"(?<!twisted )(?<!revolved )\bchair\b"], ["Standing"]),
    "Twisted Chair": ([r"(?:twisted|revolved) chair", r"prayer twist"], ["Standing", "Twists"]),
    "Low Lunge": ([r"low lunges?", r"anjaneyasana"], ["Standing", "Hip Opener"]),
    "High Lunge": ([r"high lunges?"], ["Standing"]),
    "Crescent Lunge": ([r"crescent(?: lunge)?"], ["Standing"]),
    "Twisted Lunge": ([r"(?:twisted|revolved) (?:crescent |high |low )?lunges?", r"lunge (?:with a )?twist"], ["Standing", "Twists"]),
    "Side Lunge": ([r"side lunges?", r"skandasana", r"lateral lunges?"], ["Standing", "Hip Opener"]),
    "Lizard": ([r"lizard"], ["Hip Opener"]),
    "Pigeon": ([r"(?<!flying )(?<!royal )(?<!upright )\bpigeon\b", r"half pigeon"], ["Hip Opener"]),
    "Flying Pigeon": ([r"flying pigeon"], ["Arm Balance"]),
    "Royal Pigeon": ([r"royal pigeon", r"king pigeon", r"mermaid"], ["Backbend", "Hip Opener"]),
    "Frog": ([r"\bfrog\b", r"half frog"], ["Hip Opener"]),
    "Butterfly": ([r"butterfly", r"bound angle"], ["Hip Opener", "Seated"]),
    "Reclined Butterfly": ([r"reclined (?:butterfly|bound angle)", r"supine butterfly"], ["Hip Opener", "Reclined"]),
    "Happy Baby": ([r"happy baby"], ["Hip Opener", "Reclined"]),
    "Figure Four": ([r"figure (?:4|four)"], ["Hip Opener"]),
    "Fire Log": ([r"fire ?log", r"double pigeon"], ["Hip Opener", "Seated"]),
    "90/90": ([r"90 ?90", r"ninety ninety"], ["Hip Opener", "Seated"]),
    "45/45": ([r"45 ?45"], ["Hip Opener", "Seated"]),
    "Cow Face": ([r"cow face"], ["Hip Opener", "Seated"]),
    "Garland": ([r"garland", r"malasana", r"yogi squat"], ["Hip Opener"]),
    "Goddess": ([r"goddess"], ["Standing", "Hip Opener"]),
    "Warrior 1": ([rf"warrior {N1}\b"], ["Standing"]),
    "Warrior 2": ([rf"warrior {N2}\b"], ["Standing", "Hip Opener"]),
    "Warrior 3": ([rf"warrior {N3}\b"], ["Standing Balance"]),
    "Reverse Warrior": ([r"reverse(?:d)? warrior", r"peaceful warrior"], ["Standing"]),
    "Humble Warrior": ([r"humble warrior"], ["Standing", "Forward Bend"]),
    "Triangle": ([r"(?<!revolved )(?<!twisted )(?<!fallen )(?<!bound )triangle"], ["Standing"]),
    "Revolved Triangle": ([r"(?:revolved|twisted) triangle"], ["Standing", "Twists"]),
    "Fallen Triangle": ([r"fallen triangle"], ["Arm Balance"]),
    "Extended Side Angle": ([r"(?:extended )?side angle"], ["Standing"]),
    "Half Moon": ([r"(?<!revolved )(?<!twisted )half moon"], ["Standing Balance"]),
    "Revolved Half Moon": ([r"(?:revolved|twisted) half moon"], ["Standing Balance", "Twists"]),
    "Tree": ([r"\btree\b(?! pose)", r"tree pose"], ["Standing Balance"]),
    "Eagle": ([r"eagle"], ["Standing Balance"]),
    "Airplane": ([r"airplane", r"aeroplane"], ["Standing Balance"]),
    "Hand to Big Toe": ([r"(?:hand|fingers?) to big toe", r"big toe hold"], ["Standing Balance"]),
    "Standing Splits": ([r"standing splits?"], ["Standing Balance", "Forward Bend"]),
    "Half Splits": ([r"half splits?"], ["Forward Bend"]),
    "Splits": ([r"(?<!half )(?<!standing )(?<!side )\bsplits?\b(?! stance)", r"hanumanasana"], ["Hip Opener"]),
    "Side Splits": ([r"side splits?"], ["Hip Opener"]),
    "Crow": ([r"(?<!side )(?<!baby )\bcrow\b", r"bakasana"], ["Arm Balance"]),
    "Side Crow": ([r"side crow"], ["Arm Balance", "Twists"]),
    "Baby Crow": ([r"baby crow"], ["Arm Balance"]),
    "Crane": ([r"\bcrane\b"], ["Arm Balance"]),
    "Dolphin": ([r"dolphin"], ["Inversion"]),
    "Headstand": ([r"head ?stand"], ["Inversion"]),
    "Shoulder Stand": ([r"shoulder ?stand"], ["Inversion"]),
    "Plow": ([r"\bplow\b", r"\bplough\b"], ["Inversion"]),
    "Legs Up the Wall": ([r"legs up (?:the|a) wall"], ["Inversion", "Reclined"]),
    "Seated Twist": ([r"seated (?:spinal )?twists?", r"half lord of the fishes", r"marichyasana"], ["Seated", "Twists"]),
    "Supine Twist": ([r"(?:supine|reclined|reclining|lying) (?:spinal )?twists?"], ["Reclined", "Twists"]),
    "Windshield Wipers": ([r"windshield wipers?", r"windscreen wipers?"], ["Twists", "Reclined"]),
    "Gate": ([r"gate pose", r"\bgate\b"], ["Seated"]),
    "Star": ([r"\bstar (?:pose|shape)", r"side plank star"], ["Standing"]),
    "Sugarcane": ([r"sugar ?cane"], ["Standing Balance", "Backbend"]),
    "Lotus": ([r"(?<!half )lotus"], ["Seated", "Hip Opener"]),
    "Hero": ([r"\bheros? (?:pose|seat)", r"virasana"], ["Seated"]),
    "Reclined Hero": ([r"reclined hero", r"supta virasana"], ["Reclined", "Backbend"]),
    "Toe Squat": ([r"toe squat"], ["Seated"]),
    "Squat": ([r"(?<!toe )(?<!yogi )\bsquats?\b"], ["Standing"]),
    "Savasana": ([r"savasana", r"shavasana", r"corpse pose", r"final rest"], ["Reclined"]),
    "Easy Seat": ([r"easy (?:seat|pose)", r"cross legged seat", r"comfortable seat"], ["Seated"]),
    "Pancake": ([r"pancake"], ["Forward Bend", "Seated"]),
    "L-Sit": ([r"\bl sit\b"], ["Core", "Arm Balance"]),
    "Eight-Angle": ([r"eight angle"], ["Arm Balance"]),
    "Bird of Paradise": ([r"bird of paradise"], ["Standing Balance"]),
    "Breath of Joy": ([r"breath of joy"], []),
}

# body area -> regex alternatives (applied to normalised text)
BODY = {
    "Hips": [r"\bhips?\b(?! flexors?)", r"hip openers?", r"hip opening"],
    "Hip Flexors": [r"hip flexors?", r"psoas"],
    "Hamstrings": [r"hamstrings?", r"backs? of (?:your|the) legs?"],
    "Quads": [r"quads?\b", r"quadriceps", r"fronts? of (?:your|the) thighs?"],
    "Glutes": [r"glutes?\b", r"seat muscles"],
    "Inner Thighs": [r"inner thighs?", r"adductors?", r"groin"],
    "Outer Hips & IT Band": [r"outer hips?", r"\bit band", r"outer thighs?"],
    "Calves & Ankles": [r"calf\b", r"calves", r"ankles?", r"achilles"],
    "Feet": [r"\bfeet\b(?! (?:are|hip|together|apart|wide))", r"\bfoot\b", r"\btoes?\b"],
    "Lower Back": [r"lower back", r"low back", r"lumbar"],
    "Upper Back": [r"upper back", r"shoulder blades?", r"between your shoulders"],
    "Spine": [r"\bspines?\b", r"spinal"],
    "Back": [r"\bback\b(?! (?:to|up|down|into|in|out|leg|knee|foot|heel|toes|of|and forth|onto))"],
    "Side Body": [r"side body", r"sides of your body", r"obliques?"],
    "Core": [r"\bcore\b", r"\babs\b", r"abdominals?", r"belly button", r"navel"],
    "Chest": [r"\bchest\b", r"heart opener", r"pecs?\b"],
    "Shoulders": [r"shoulders?\b"],
    "Neck": [r"\bneck\b"],
    "Arms": [r"\barms?\b", r"triceps?", r"biceps?"],
    "Wrists": [r"wrists?"],
    "Legs": [r"\blegs?\b"],
}

# "intent" tags: what someone might be in the mood for
MOODS = {
    "Sleep & Wind Down": [r"\bsleep", r"bedtime", r"before bed", r"\bbed\b", r"wind down", r"winding down",
                          r"\bevening", r"\bnight", r"end of (?:the|your|a long) day", r"unwind"],
    "Morning": [r"morning", r"wake up", r"start (?:of )?your day", r"start the day", r"rise and shine"],
    "Relax & Restore": [r"restorative", r"relax", r"\brest\b", r"calm", r"gentle", r"soothing", r"\byin\b",
                        r"longer holds?", r"long holds?", r"slow down", r"stress"],
    "Strength": [r"strength", r"strong", r"build heat", r"create heat", r"power", r"burn"],
    "Balance": [r"balanc"],
    "Flexibility & Mobility": [r"flexib", r"mobility", r"\bmobile\b", r"range of motion", r"stretch"],
    "Breathwork": [r"breathwork", r"breath work", r"breathing (?:exercise|technique|practice)", r"pranayama"],
    "Fundamentals": [r"fundamental", r"beginner", r"foundation", r"basics", r"new to yoga"],
    "Peak Pose": [r"peak pose", r"build(?:s|ing)? (?:up )?to(?:wards)?", r"work(?:ing)? toward"],
    "Mindfulness": [r"mindful", r"meditat", r"gratitude", r"intention", r"reflect"],
}

# pose category -> words that name the category directly (used on descriptions)
TYPE_WORDS = {
    "Standing": [r"standing poses?", r"standing sequence", r"standing flow", r"lunges"],
    "Seated": [r"seated poses?", r"seated sequence", r"on the floor", r"low to the ground"],
    "Reclined": [r"reclined", r"on your back", r"supine"],
    "Inversion": [r"inversions?", r"upside down"],
    "Arm Balance": [r"arm balances?", r"arm balancing"],
    "Standing Balance": [r"balance poses?", r"balancing poses?", r"standing balances?", r"a balance pose", r"balance work"],
    "Forward Bend": [r"forward bends?", r"forward folds?", r"folds"],
    "Backbend": [r"back ?bends?", r"heart openers?", r"chest openers?"],
    "Twists": [r"twists?", r"twisting"],
    "Hip Opener": [r"hip openers?", r"hip opening", r"open(?:ing)? (?:up )?your hips"],
    "Core": [r"\bcore\b", r"planks", r"\babs\b"],
}

POSE_RE = {k: re.compile("|".join(v[0])) for k, v in POSES.items()}
BODY_RE = {k: re.compile("|".join(v)) for k, v in BODY.items()}
MOOD_RE = {k: re.compile("|".join(v)) for k, v in MOODS.items()}
TYPE_RE = {k: re.compile("|".join(v)) for k, v in TYPE_WORDS.items()}


def counts(text, table):
    t = norm(text)
    return {k: n for k, rx in table.items() if (n := len(rx.findall(t)))}
