#!/usr/bin/env python3
"""Build a PowerPoint summarizing the AI Daily Brief transcript:
'How to Get the Most Out of Fable 5 and GPT 5.6 Sol'."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# Palette
INK = RGBColor(0x14, 0x1B, 0x2E)      # deep navy
ACCENT = RGBColor(0x3B, 0x82, 0xF6)   # blue
ACCENT2 = RGBColor(0x22, 0xC5, 0x5E)  # green
LIGHT = RGBColor(0xF4, 0xF6, 0xFB)    # near-white panel
GREY = RGBColor(0x5B, 0x63, 0x74)     # muted text
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
SW, SH = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]


def add_slide():
    return prs.slides.add_slide(BLANK)


def rect(slide, x, y, w, h, color, line=None):
    from pptx.enum.shapes import MSO_SHAPE
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(1)
    shp.shadow.inherit = False
    return shp


def textbox(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    return tb, tf


def set_run(run, text, size, color, bold=False, italic=False, font="Calibri"):
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font


def bg(slide, color):
    rect(slide, 0, 0, SW, SH, color)


def title_bar(slide, kicker, title):
    rect(slide, 0, 0, SW, Inches(1.5), INK)
    rect(slide, 0, Inches(1.5), SW, Pt(4), ACCENT)
    tb, tf = textbox(slide, Inches(0.6), Inches(0.28), Inches(12), Inches(1.1))
    p = tf.paragraphs[0]
    set_run(p.add_run(), kicker.upper(), 12, ACCENT2, bold=True)
    p2 = tf.add_paragraph()
    set_run(p2.add_run(), title, 30, WHITE, bold=True)


def bullets(slide, items, x, y, w, h, size=18, gap=10, color=INK):
    tb, tf = textbox(slide, x, y, w, h)
    for i, (head, body) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        set_run(p.add_run(), "\u25B8 ", size, ACCENT, bold=True)
        set_run(p.add_run(), head, size, color, bold=True)
        if body:
            set_run(p.add_run(), " \u2014 " + body, size, GREY)
    return tb


# ---------------------------------------------------------------- Slide 1: Title
s = add_slide()
bg(s, INK)
rect(s, 0, Inches(3.35), SW, Pt(5), ACCENT)
tb, tf = textbox(s, Inches(0.9), Inches(1.7), Inches(11.5), Inches(3), MSO_ANCHOR.MIDDLE)
p = tf.paragraphs[0]
set_run(p.add_run(), "THE AI DAILY BRIEF", 16, ACCENT2, bold=True)
p2 = tf.add_paragraph()
set_run(p2.add_run(), "How to Get the Most Out of", 40, WHITE, bold=True)
p3 = tf.add_paragraph()
set_run(p3.add_run(), "Fable 5 & GPT-5.6 Sol", 40, WHITE, bold=True)
p4 = tf.add_paragraph()
p4.space_before = Pt(16)
set_run(p4.add_run(),
        "New prompting patterns for frontier models: boundaries, iterative steering, "
        "matching compute to the task, and looping until it hits the bar.",
        16, RGBColor(0xC7, 0xD2, 0xE5))
tb2, tf2 = textbox(s, Inches(0.9), Inches(6.7), Inches(11.5), Inches(0.6))
set_run(tf2.paragraphs[0].add_run(),
        "Source: The AI Daily Brief  |  Runtime 23:00  |  Published 2026-07-20", 12, GREY)

# --------------------------------------------------- Slide 2: What's changed
s = add_slide(); bg(s, WHITE)
title_bar(s, "The setup", "New models demand new ways of working")
bullets(s, [
    ("A new class of models", "Fable 5 and GPT-5.6 Sol are now in wide use after long early-access periods."),
    ("Benchmarks can't capture it", "The real gains come from trial, error, and shared tips \u2014 not scorecards."),
    ("Common threads across both", "Similar patterns emerge for Sol and Fable, hinting at new interaction norms."),
    ("More power, more consequence", "The stronger the model, the more your prompting habits help or hurt."),
], Inches(0.7), Inches(1.9), Inches(12), Inches(5), size=20, gap=16)

# --------------------------------------------------- Slide 3: Boundaries
s = add_slide(); bg(s, WHITE)
title_bar(s, "Tip 1 \u00b7 Eric Provencal (Codex)", "Set boundaries for tenacious models")
tb, tf = textbox(s, Inches(0.7), Inches(1.85), Inches(12), Inches(0.9))
set_run(tf.paragraphs[0].add_run(),
        "5.6 Sol is more tenacious and thorough. Boundaries are the few instructions that stop it "
        "from creating extra work or taking actions you didn't intend.", 17, GREY)
# example panel
rect(s, Inches(0.7), Inches(2.9), Inches(11.9), Inches(3.6), LIGHT)
rect(s, Inches(0.7), Inches(2.9), Pt(6), Inches(3.6), ACCENT)
bullets(s, [
    ("Keep approved dates & budget figures unchanged", ""),
    ("Use only the supplied sources", "stops internet rabbit-holes"),
    ("Flag missing information instead of guessing", ""),
    ("Keep recommendations within the stated budget", ""),
    ("Prepare the message as a draft \u2014 don't send it", "avoids costly premature actions"),
], Inches(1.1), Inches(3.2), Inches(11.1), Inches(3.1), size=18, gap=12)

# --------------------------------------------------- Slide 4: Iterate & steer
s = add_slide(); bg(s, WHITE)
title_bar(s, "Tip 2 \u00b7 Interaction", "Iterate and steer instead of fire-and-forget")
bullets(s, [
    ("Follow up to refine", "\u201ckeep the opening more direct,\u201d \u201cmove this part,\u201d \u201ckeep the evidence.\u201d"),
    ("Steer mid-run", "Send a message while it works to change direction or add a detail."),
    ("Queue for later", "Save a follow-up that waits until the current run finishes."),
    ("Lower collaboration latency", "Real-time steering matters more as models get more capable."),
    ("Chat vs. Work", "Different prompting best-practices now exist for each surface."),
], Inches(0.7), Inches(1.9), Inches(12), Inches(5), size=20, gap=15)

# --------------------------------------------------- Slide 5: Match compute
s = add_slide(); bg(s, WHITE)
title_bar(s, "Tip 3 \u00b7 GPT-5.6 best practices (Ollie Leeman)", "Match the compute to the job")
# two dials
def dial_card(x, title, rows):
    rect(s, x, Inches(1.95), Inches(5.7), Inches(2.5), LIGHT)
    rect(s, x, Inches(1.95), Inches(5.7), Inches(0.55), ACCENT)
    tb, tf = textbox(s, x + Inches(0.25), Inches(1.98), Inches(5.2), Inches(0.5), MSO_ANCHOR.MIDDLE)
    set_run(tf.paragraphs[0].add_run(), title, 17, WHITE, bold=True)
    tb2, tf2 = textbox(s, x + Inches(0.25), Inches(2.65), Inches(5.2), Inches(1.7))
    for i, (h, b) in enumerate(rows):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        p.space_after = Pt(6)
        set_run(p.add_run(), h + ": ", 15, INK, bold=True)
        set_run(p.add_run(), b, 15, GREY)

dial_card(Inches(0.7), "Dial 1 \u00b7 Model size", [
    ("Sol", "the hardest problems"),
    ("Terra", "everyday business work"),
    ("Luna", "cheap, fast tasks"),
])
dial_card(Inches(6.9), "Dial 2 \u00b7 Thinking effort", [
    ("6 levels", "from none to max"),
    ("Advice", "start at last setting, test one lower"),
    ("Max", "save for genuinely hardest problems"),
])
bullets(s, [
    ("Delete repeated instructions", "state each rule once \u2014 raised scores 10-15%, cut tokens up to 66%."),
    ("Recheck brevity rules", "5.6 already defaults shorter; blanket \u201ckeep it brief\u201d can cut too much."),
    ("Concrete beats abstract tone", "spell out behavior, not adjectives like \u201cfriendly.\u201d"),
], Inches(0.7), Inches(4.7), Inches(12), Inches(2.6), size=16, gap=9)

# --------------------------------------------------- Slide 6: Voice & context
s = add_slide(); bg(s, WHITE)
title_bar(s, "Tip 4 \u00b7 Context", "Feed the model richer context")
bullets(s, [
    ("The ramblers shall inherit the earth", "unstructured voice dictation often beats terse typed notes."),
    ("Use native dictation", "ChatGPT's built-in dictation is best-in-class \u2014 no extra tools needed."),
    ("Context is the bottleneck", "more information usually helps the model do its job well."),
    ("Onboard the model", "build a personal context portfolio so it can truly collaborate."),
], Inches(0.7), Inches(1.9), Inches(12), Inches(5), size=20, gap=16)

# --------------------------------------------------- Slide 7: Ambition
s = add_slide(); bg(s, WHITE)
title_bar(s, "Theme \u00b7 Christine Zhu", "Be more ambitious: move up the value stack")
tb, tf = textbox(s, Inches(0.7), Inches(1.8), Inches(12), Inches(0.7))
set_run(tf.paragraphs[0].add_run(),
        "Don't just clear the \u201cdopamine backlog.\u201d Push AI into high-leverage work "
        "(concept from Shreyas Doshi).", 17, GREY)
levels = [
    ("OPTICS", "Autopilot", "Automate ruthlessly \u2014 scheduled status updates, packaged for each audience.", ACCENT2),
    ("EXECUTION", "Co-pilot", "Weekly context dumps, planning skills, customer-theme analysis \u2014 ask for judgment.", ACCENT),
    ("IMPACT", "Sparring partner", "Hardest-to-start work: new bets, narratives, strategy. Onboard with context.", RGBColor(0x8B,0x5C,0xF6)),
]
x = Inches(0.7)
cw = Inches(3.95)
for name, mode, desc, col in levels:
    rect(s, x, Inches(2.7), cw, Inches(3.6), LIGHT)
    rect(s, x, Inches(2.7), cw, Inches(0.7), col)
    tb, tf = textbox(s, x + Inches(0.25), Inches(2.73), cw - Inches(0.5), Inches(0.64), MSO_ANCHOR.MIDDLE)
    set_run(tf.paragraphs[0].add_run(), name, 18, WHITE, bold=True)
    tb2, tf2 = textbox(s, x + Inches(0.25), Inches(3.55), cw - Inches(0.5), Inches(2.6))
    set_run(tf2.paragraphs[0].add_run(), "Claude as " + mode, 16, INK, bold=True)
    p = tf2.add_paragraph(); p.space_before = Pt(8)
    set_run(p.add_run(), desc, 15, GREY)
    x += cw + Inches(0.15)

# --------------------------------------------------- Slide 8: Unknowns
s = add_slide(); bg(s, WHITE)
title_bar(s, "Field guide \u00b7 Tariq (Claude Code)", "Find your unknowns \u2014 the map is not the territory")
bullets(s, [
    ("Known knowns", "what you put in the prompt \u2014 what you tell the agent you want."),
    ("Known unknowns", "what you haven't figured out yet, but know you haven't."),
    ("Unknown knowns", "so obvious you'd never write it, but you'd recognize it instantly."),
    ("Unknown unknowns", "what you haven't even considered."),
], Inches(0.7), Inches(1.9), Inches(12), Inches(2.6), size=19, gap=10)
rect(s, Inches(0.7), Inches(4.9), Inches(11.9), Inches(1.9), LIGHT)
rect(s, Inches(0.7), Inches(4.9), Pt(6), Inches(1.9), ACCENT2)
tb, tf = textbox(s, Inches(1.1), Inches(5.05), Inches(11.1), Inches(1.6))
set_run(tf.paragraphs[0].add_run(), "How to reduce them: ", 17, INK, bold=True)
set_run(tf.paragraphs[0].add_run(),
        "give context about your starting point; run a \u201cblind-spot pass\u201d to learn what you "
        "don't know; brainstorm & prototype early (e.g., \u201cshow me 4 wildly different design "
        "directions so I can react\u201d).", 17, GREY)

# --------------------------------------------------- Slide 9: Meta prompts
s = add_slide(); bg(s, WHITE)
title_bar(s, "Meta prompts \u00b7 Daniel Miessler", "Rerun these on every big intelligence jump")
bullets(s, [
    ("Harness optimization", "audit what your setup believes about you and close the gaps (context hygiene)."),
    ("Self-model audit", "flag where the system optimizes for who you said you were vs. who you are now."),
    ("Go really big", "life/work optimization prompts \u2014 priorities, projects, even ikigai."),
    ("Take the vibe temperature", "big-scope prompts reveal how a new model reasons about hard questions."),
], Inches(0.7), Inches(1.9), Inches(12), Inches(5), size=20, gap=15)

# --------------------------------------------------- Slide 10: Loops
s = add_slide(); bg(s, WHITE)
title_bar(s, "Technique \u00b7 Matt Schumer + Claude Devs", "Loop it until it hits the bar")
tb, tf = textbox(s, Inches(0.7), Inches(1.8), Inches(12), Inches(0.9))
set_run(tf.paragraphs[0].add_run(),
        "Don't use adjectives \u2014 give a hard, checkable bar for \u201cdone,\u201d then loop: build, "
        "check, find the biggest gap, close it, repeat. The model never decides it's finished.",
        17, GREY)
loops = [
    ("Turn-based", "You direct each turn; stops when task done or more context needed."),
    ("Goal-based", "Evaluator checks your success criteria until met or max turns."),
    ("Time-based", "Runs on an interval; good for recurring work."),
    ("Proactive", "Triggered by an event/schedule; runs itself until you turn it off."),
]
x = Inches(0.7); cw = Inches(2.9)
for name, desc in loops:
    rect(s, x, Inches(2.9), cw, Inches(3.4), LIGHT)
    rect(s, x, Inches(2.9), cw, Pt(6), ACCENT)
    tb, tf = textbox(s, x + Inches(0.22), Inches(3.1), cw - Inches(0.44), Inches(3.0))
    set_run(tf.paragraphs[0].add_run(), name, 17, INK, bold=True)
    p = tf.add_paragraph(); p.space_before = Pt(8)
    set_run(p.add_run(), desc, 14, GREY)
    x += cw + Inches(0.13)

# --------------------------------------------------- Slide 11: Takeaways
s = add_slide(); bg(s, INK)
rect(s, 0, Inches(1.5), SW, Pt(4), ACCENT2)
tb, tf = textbox(s, Inches(0.6), Inches(0.4), Inches(12), Inches(1))
set_run(tf.paragraphs[0].add_run(), "KEY TAKEAWAYS", 14, ACCENT2, bold=True)
p = tf.add_paragraph()
set_run(p.add_run(), "Two things to do with every model leap", 30, WHITE, bold=True)
items = [
    ("Unlearn old habits", "Find where prompting for old models no longer helps \u2014 or actively hurts."),
    ("Discover new patterns", "Chase the differentiated capabilities: steering, unknowns, loops."),
    ("Ratchet up ambition", "Assume no limits; try the biggest tasks to find where the limits really are."),
    ("New relationship with work", "The unlock isn't doing the same work faster \u2014 it's new categories of work."),
]
tb2, tf2 = textbox(s, Inches(0.7), Inches(2), Inches(12), Inches(5))
for i, (h, b) in enumerate(items):
    p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
    p.space_after = Pt(18)
    set_run(p.add_run(), "\u2192 ", 22, ACCENT2, bold=True)
    set_run(p.add_run(), h + "  ", 22, WHITE, bold=True)
    set_run(p.add_run(), b, 18, RGBColor(0xC7, 0xD2, 0xE5))

out = "/workspace/Fable5_GPT5.6_Sol_Prompting.pptx"
prs.save(out)
print("Saved", out, "with", len(prs.slides._sldIdLst), "slides")
