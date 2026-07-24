#!/usr/bin/env python3
"""Build a senior-consultant-grade PowerPoint from the Fable 5 / GPT-5.6 Sol transcript."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.oxml import parse_xml
from copy import deepcopy
from lxml import etree

# --- Design system -----------------------------------------------------------
INK = RGBColor(0x0B, 0x12, 0x20)
INK_SOFT = RGBColor(0x16, 0x1F, 0x33)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
OFF_WHITE = RGBColor(0xF4, 0xF6, 0xF9)
TEAL = RGBColor(0x00, 0xC2, 0xA8)
TEAL_DEEP = RGBColor(0x00, 0x8F, 0x7A)
CORAL = RGBColor(0xFF, 0x5A, 0x36)
SLATE = RGBColor(0x5B, 0x65, 0x77)
MUTED = RGBColor(0x8B, 0x95, 0xA8)
CARD = RGBColor(0xE8, 0xEC, 0xF2)
CARD_DARK = RGBColor(0x1C, 0x27, 0x3D)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def set_run_font(run, size_pt, color, bold=False, name="Calibri"):
    run.font.size = Pt(size_pt)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = name
    rPr = run._r.get_or_add_rPr()
    # Disable East Asian fallback oddities
    for child in list(rPr):
        if "latin" in child.tag or "ea" in child.tag or "cs" in child.tag:
            rPr.remove(child)
    latin = parse_xml(
        f'<a:latin xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" typeface="{name}"/>'
    )
    rPr.append(latin)


def add_textbox(slide, left, top, width, height, text, size, color, bold=False,
                align=PP_ALIGN.LEFT, font="Calibri", anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    try:
        tf._txBody.bodyPr.set("anchor", {MSO_ANCHOR.TOP: "t", MSO_ANCHOR.MIDDLE: "ctr", MSO_ANCHOR.BOTTOM: "b"}[anchor])
    except Exception:
        pass
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    set_run_font(run, size, color, bold=bold, name=font)
    return box


def add_paragraph(text_frame, text, size, color, bold=False, align=PP_ALIGN.LEFT,
                  space_before=0, space_after=6, font="Calibri", level=0):
    if text_frame.paragraphs[0].text == "" and len(text_frame.paragraphs) == 1 and not text_frame.paragraphs[0].runs:
        p = text_frame.paragraphs[0]
    else:
        p = text_frame.add_paragraph()
    p.alignment = align
    p.level = level
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    run = p.add_run()
    run.text = text
    set_run_font(run, size, color, bold=bold, name=font)
    return p


def fill_solid(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def add_rect(slide, left, top, width, height, color):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    fill_solid(shape, color)
    return shape


def add_round_rect(slide, left, top, width, height, color, radius=0.1):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    fill_solid(shape, color)
    # Adjust corner radius via adj
    try:
        shape.adjustments[0] = radius
    except Exception:
        pass
    return shape


def set_slide_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_notes(slide, text):
    notes = slide.notes_slide
    tf = notes.notes_text_frame
    tf.text = text


def add_bullet_block(slide, left, top, width, height, items, size=18, color=INK, bullet_color=TEAL):
    """Bullets with a teal square marker drawn beside each line."""
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_before = Pt(8 if i else 0)
        p.space_after = Pt(10)
        # bullet char
        run_b = p.add_run()
        run_b.text = "▸  "
        set_run_font(run_b, size, bullet_color, bold=True)
        run = p.add_run()
        run.text = item
        set_run_font(run, size, color, bold=False)
    return box


def accent_orb(slide, left, top, size, color):
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, left, top, size, size)
    fill_solid(shape, color)
    return shape


def make_prs():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]  # blank

    # =========================================================================
    # 1. TITLE
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, INK)
    # bold left color block
    add_rect(s, 0, 0, Inches(0.35), SLIDE_H, TEAL)
    # decorative orb
    accent_orb(s, Inches(11.2), Inches(-0.6), Inches(3.2), INK_SOFT)
    accent_orb(s, Inches(10.4), Inches(5.4), Inches(2.4), CARD_DARK)
    add_textbox(s, Inches(0.9), Inches(1.5), Inches(11), Inches(0.4),
                "THE AI DAILY BRIEF  ·  JULY 2026", 14, TEAL, bold=True)
    add_textbox(s, Inches(0.9), Inches(2.1), Inches(11.2), Inches(2.2),
                "How to get the most out of\nFable 5 and GPT-5.6 Sol",
                40, WHITE, bold=True)
    add_textbox(s, Inches(0.9), Inches(4.6), Inches(10.5), Inches(1.0),
                "Unlearn last-generation prompts. Raise your ambition.\nAdopt new interaction patterns that unlock the leap.",
                18, MUTED, bold=False)
    add_textbox(s, Inches(0.9), Inches(6.7), Inches(10), Inches(0.35),
                "A field guide for frontier-model operators", 13, SLATE)
    add_notes(s,
        "Open with energy. Frame the episode: this is not more model drama — it's a practical field guide. "
        "Tell the audience the through-line up front: every intelligence jump forces two moves — unlearn old prompting habits, "
        "and raise ambition until the real limits show up. Mention Fable 5 and GPT-5.6 Sol as the current frontier pair.")

    # =========================================================================
    # 2. FULL-BLEED STATEMENT — thesis
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, INK)
    add_rect(s, 0, 0, SLIDE_W, SLIDE_H, INK)
    add_rect(s, Inches(0.9), Inches(2.4), Inches(0.18), Inches(2.4), CORAL)
    add_textbox(s, Inches(1.4), Inches(2.2), Inches(10.8), Inches(2.9),
                "Every big model leap demands you unlearn old prompts — and raise your ambition until the limits appear.",
                36, WHITE, bold=True)
    add_textbox(s, Inches(1.4), Inches(5.5), Inches(10), Inches(0.5),
                "THE CORE ARGUMENT", 12, CORAL, bold=True)
    add_notes(s,
        "This is the thesis slide. Pause. Let people read. From the episode: tips converge in two directions — "
        "stale rule lists, brevity hacks, and maxed settings backfire on more tenacious models; the real unlock is higher ambition "
        "and new patterns like loops. Audience should feel: 'I need to change how I work, not just what I type.'")

    # =========================================================================
    # 3. PROBLEM — still prompting like before
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, OFF_WHITE)
    add_rect(s, 0, 0, Inches(0.28), SLIDE_H, TEAL)
    add_textbox(s, Inches(0.8), Inches(0.55), Inches(11.5), Inches(1.5),
                "Most people still prompt frontier models like last year's tools.",
                36, INK, bold=True)
    items = [
        "Tips can't be captured in benchmarks alone",
        "Trial and error reveals what actually works",
        "Common threads span Fable 5 and 5.6 Sol",
        "New interaction patterns are already emerging",
        "Old habits often actively hurt performance",
    ]
    add_bullet_block(s, Inches(0.8), Inches(2.5), Inches(7.5), Inches(4.2), items, size=20, color=INK)
    # right visual card
    add_round_rect(s, Inches(9.0), Inches(2.3), Inches(3.6), Inches(3.8), INK, radius=0.08)
    add_textbox(s, Inches(9.3), Inches(2.7), Inches(3.0), Inches(0.4),
                "THE GAP", 12, TEAL, bold=True)
    add_textbox(s, Inches(9.3), Inches(3.3), Inches(3.0), Inches(2.4),
                "Capability jumped.\nBehavior didn't.\n\nThat's the wasted unlock.",
                18, WHITE, bold=True)
    add_notes(s,
        "NLW opens by noting everyone now has Fable 5 and GPT-5.6 Sol, and tips are flooding in. Emphasize that this knowledge "
        "isn't in leaderboards — it comes from practice. The right-side card drives urgency: the models changed; most workflows didn't. "
        "Audience should feel slightly called out, then curious.")

    # =========================================================================
    # 4. QUOTE — Eric Provencher / tenacity
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, INK)
    accent_orb(s, Inches(-1.2), Inches(-1.0), Inches(3.5), INK_SOFT)
    add_textbox(s, Inches(1.0), Inches(1.6), Inches(1.0), Inches(1.0),
                "“", 96, TEAL, bold=True)
    add_textbox(s, Inches(1.0), Inches(2.5), Inches(11.2), Inches(2.5),
                "5.6 Sol is a lot more tenacious and thorough than previous models.",
                36, WHITE, bold=True)
    add_textbox(s, Inches(1.0), Inches(5.4), Inches(11), Inches(0.6),
                "— Eric Provencher, Codex team", 16, MUTED, bold=False)
    add_rect(s, Inches(1.0), Inches(6.3), Inches(2.2), Inches(0.08), TEAL)
    add_notes(s,
        "Deliver this as the first hard landing. Eric's point: people still prompt 5.6 Sol exactly like 5.5. "
        "Tenacity means the model will push further, explore more, and take more agency — which is power and risk. "
        "Audience should rethink 'set it and forget it' prompting.")

    # =========================================================================
    # 5. TWO-COLUMN — boundaries
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, OFF_WHITE)
    add_textbox(s, Inches(0.7), Inches(0.4), Inches(12), Inches(1.35),
                "Tenacious models need sharper boundaries, not longer prompts.",
                36, INK, bold=True)
    # left column — why (3 bullets)
    add_round_rect(s, Inches(0.7), Inches(2.0), Inches(5.7), Inches(4.6), WHITE, radius=0.06)
    add_rect(s, Inches(0.7), Inches(2.0), Inches(0.14), Inches(4.6), TEAL)
    add_textbox(s, Inches(1.1), Inches(2.25), Inches(5.0), Inches(0.4),
                "WHY BOUNDARIES MATTER", 13, TEAL, bold=True)
    left_items = [
        "Stop unintended high-agency actions",
        "Prevent costly rabbit-hole exploration",
        "Protect unapproved sends and decisions",
    ]
    add_bullet_block(s, Inches(1.1), Inches(3.0), Inches(5.0), Inches(3.2), left_items, size=17, color=INK)
    # right column — examples as stacked callouts (not bullets)
    add_round_rect(s, Inches(6.8), Inches(2.0), Inches(5.8), Inches(4.6), INK, radius=0.06)
    add_textbox(s, Inches(7.2), Inches(2.25), Inches(5.1), Inches(0.35),
                "SAY IT EXPLICITLY", 13, TEAL, bold=True)
    examples = [
        "Keep approved dates and budgets unchanged",
        "Use only the supplied sources",
        "Draft the message — don't send it",
        "Steer mid-run; queue the follow-up",
    ]
    ey = Inches(2.85)
    for ex in examples:
        add_round_rect(s, Inches(7.2), ey, Inches(5.1), Inches(0.7), CARD_DARK, radius=0.1)
        add_textbox(s, Inches(7.45), ey + Inches(0.18), Inches(4.7), Inches(0.4),
                    ex, 14, WHITE, bold=False)
        ey += Inches(0.85)
    add_notes(s,
        "Walk the left column as consequence, right as tactics from Eric's learn.chatgpt.com guide. "
        "Call out Steer vs Queue as the collaboration latency win when Codex behaviors land in ChatGPT. "
        "Audience should leave with 1–2 boundaries they'll add to their next prompt.")

    # =========================================================================
    # 6. DATA HIGHLIGHT — delete old instructions
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, OFF_WHITE)
    add_textbox(s, Inches(0.7), Inches(0.35), Inches(12), Inches(1.3),
                "Delete old repeated instructions — they now cost quality and tokens.",
                36, INK, bold=True)
    # three big stat cards
    cards = [
        ("10–15%", "Score lift from stating\neach instruction once", TEAL),
        ("66%", "Token cut by removing\nduplicated instructions", CORAL),
        ("6", "Effort levels on 5.6's\nthinking dial, none → max", INK),
    ]
    x = Inches(0.7)
    for label, sub, accent in cards:
        add_round_rect(s, x, Inches(2.0), Inches(3.85), Inches(4.4), WHITE, radius=0.06)
        add_rect(s, x, Inches(2.0), Inches(3.85), Inches(0.14), accent)
        add_textbox(s, x + Inches(0.35), Inches(2.6), Inches(3.2), Inches(1.4),
                    label, 54, accent, bold=True)
        add_textbox(s, x + Inches(0.35), Inches(4.3), Inches(3.2), Inches(1.5),
                    sub, 16, SLATE, bold=False)
        x += Inches(4.1)
    add_notes(s,
        "Ollie Lehmann's summary of OpenAI's GPT-5.6 best practices. State each instruction exactly once — "
        "giant rule lists written for older models make answers worse and cost more. Tie the third card forward: "
        "effort is a dial you will use, not a vanity setting. Audience should want to open their system prompt tonight.")

    # =========================================================================
    # 7. TWO-COLUMN — two dials
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, INK)
    add_textbox(s, Inches(0.7), Inches(0.4), Inches(12), Inches(1.3),
                "Match compute to the job — size and effort are separate dials.",
                36, WHITE, bold=True)
    # left
    add_round_rect(s, Inches(0.7), Inches(2.0), Inches(5.8), Inches(4.6), CARD_DARK, radius=0.06)
    add_textbox(s, Inches(1.05), Inches(2.3), Inches(5.1), Inches(0.4),
                "MODEL SIZE", 13, TEAL, bold=True)
    sizes = [
        ("Sol", "Hardest problems"),
        ("Terra", "Everyday business work"),
        ("Luna", "Cheap, fast tasks"),
    ]
    y = Inches(3.0)
    for name, desc in sizes:
        add_round_rect(s, Inches(1.05), y, Inches(5.1), Inches(0.85), INK, radius=0.08)
        add_textbox(s, Inches(1.3), y + Inches(0.18), Inches(1.6), Inches(0.5),
                    name, 20, TEAL, bold=True)
        add_textbox(s, Inches(3.1), y + Inches(0.22), Inches(2.8), Inches(0.5),
                    desc, 16, WHITE)
        y += Inches(1.05)
    # right
    add_round_rect(s, Inches(6.85), Inches(2.0), Inches(5.8), Inches(4.6), CARD_DARK, radius=0.06)
    add_textbox(s, Inches(7.2), Inches(2.3), Inches(5.1), Inches(0.4),
                "THINKING EFFORT", 13, CORAL, bold=True)
    add_textbox(s, Inches(7.2), Inches(3.0), Inches(5.1), Inches(2.8),
                "Start at your last model's setting.\nThen test one level lower.\n\nThe new generation usually needs less.\nSave max for genuinely hard problems.",
                18, WHITE, bold=False)
    add_notes(s,
        "Make the emotional point: everyone wants to crank to max. OpenAI's advice is counterintuitive — try one level lower. "
        "Walk Sol/Terra/Luna quickly. Audience should leave knowing they have two knobs, not one 'smartest' button.")

    # =========================================================================
    # 8. STATEMENT — max is wrong
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, CORAL)
    add_textbox(s, Inches(1.0), Inches(2.4), Inches(11.2), Inches(2.6),
                "Dialing every task to max feels smart. It is usually the wrong move.",
                36, WHITE, bold=True)
    add_textbox(s, Inches(1.0), Inches(5.4), Inches(11), Inches(0.5),
                "Even before cost — more compute is not always more quality.", 16, RGBColor(0xFF, 0xD8, 0xCF))
    add_notes(s,
        "Short punch slide. NLW calls this emotionally hard advice. Hold silence after the headline. "
        "Then: outside of cost, overthinking can degrade outcomes. Transition: if settings aren't the unlock, ambition is.")

    # =========================================================================
    # 9. QUOTE — Christine Zhu ambition
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, INK)
    add_rect(s, Inches(0.9), Inches(1.8), Inches(0.16), Inches(3.6), TEAL)
    add_textbox(s, Inches(1.4), Inches(1.85), Inches(10.8), Inches(2.9),
                "The biggest unlock happened when I went beyond automating busywork to high-leverage work.",
                34, WHITE, bold=True)
    add_textbox(s, Inches(1.4), Inches(5.1), Inches(10.5), Inches(0.5),
                "— Christine Zhu, AI UX PM at Intuit", 16, MUTED)
    add_textbox(s, Inches(1.4), Inches(5.9), Inches(10.5), Inches(0.6),
                "Stop clearing the “dopamine backlog.” Start asking for judgment.", 16, TEAL, bold=True)
    add_notes(s,
        "Pivot to ambition. Christine cleared little tasks for months, then used Fable for work she didn't trust Claude with before — "
        "and that was the leap. Quote Shreyas Doshi's three levels briefly as setup for the next slide. "
        "Audience should audit what % of their AI use is dopamine vs impact.")

    # =========================================================================
    # 10. THREE MODES — optics / execution / impact
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, OFF_WHITE)
    add_textbox(s, Inches(0.7), Inches(0.35), Inches(12), Inches(1.2),
                "Use Fable differently for optics, execution, and impact work.",
                36, INK, bold=True)
    modes = [
        ("AUTOPILOT", "Optics", "Automate visibility.\nStatus boards, updates,\naudience packaging.", TEAL),
        ("CO-PILOT", "Execution", "Ask for judgment.\nWeekly context dumps,\nplanning, customer themes.", CORAL),
        ("SPARRING\nPARTNER", "Impact", "Start the hard work.\nStrategy bets, narratives,\nstress-tested plans.", INK),
    ]
    x = Inches(0.7)
    for mode, level, body, accent in modes:
        add_round_rect(s, x, Inches(1.8), Inches(3.9), Inches(4.9), WHITE, radius=0.06)
        add_rect(s, x, Inches(1.8), Inches(3.9), Inches(0.16), accent)
        add_textbox(s, x + Inches(0.3), Inches(2.2), Inches(3.3), Inches(0.35),
                    level.upper(), 12, accent, bold=True)
        add_textbox(s, x + Inches(0.3), Inches(2.7), Inches(3.3), Inches(1.3),
                    mode, 26, INK, bold=True)
        add_textbox(s, x + Inches(0.3), Inches(4.4), Inches(3.3), Inches(1.8),
                    body, 16, SLATE)
        x += Inches(4.15)
    add_notes(s,
        "Map Christine's framework: optics → Claude as autopilot (Cowork scheduled status sheets); "
        "execution → co-pilot skills (Context Dump, Jira/roadmap, support themes); "
        "impact → sparring partner with a personal context portfolio. Automate optics ruthlessly so you stay in flow for impact. "
        "Audience should assign their next three AI tasks to a mode.")

    # =========================================================================
    # 11. QUOTE — Tariq unknowns
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, OFF_WHITE)
    add_round_rect(s, Inches(0.8), Inches(1.3), Inches(11.7), Inches(4.9), INK, radius=0.05)
    add_textbox(s, Inches(1.3), Inches(1.7), Inches(10.5), Inches(0.4),
                "FIELD GUIDE TO FABLE", 12, TEAL, bold=True)
    add_textbox(s, Inches(1.3), Inches(2.2), Inches(10.5), Inches(2.7),
                "Fable is the first model where quality is bottlenecked by my ability to clarify its unknowns.",
                32, WHITE, bold=True)
    add_textbox(s, Inches(1.3), Inches(5.2), Inches(10.5), Inches(0.5),
                "— Tariq, Claude Code team   ·   The map is not the territory", 15, MUTED)
    add_notes(s,
        "Introduce map vs territory: prompts/skills/context are the map; codebase and constraints are the territory. "
        "Unknowns force guesses. Working with Fable is discovering unknowns before, during, and after implementation — "
        "blind spot passes, brainstorm-and-prototype. Audience should feel responsible for clarifying, not just assigning.")

    # =========================================================================
    # 12. CONTENT — unknowns toolkit + meta-prompts
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, OFF_WHITE)
    add_rect(s, 0, 0, Inches(0.28), SLIDE_H, CORAL)
    add_textbox(s, Inches(0.8), Inches(0.4), Inches(11.8), Inches(1.3),
                "Invite the model to surface unknowns — and rerun meta-prompts every leap.",
                34, INK, bold=True)
    # left card — 4 unknown types as compact rows
    add_round_rect(s, Inches(0.8), Inches(2.0), Inches(5.8), Inches(4.6), WHITE, radius=0.06)
    add_textbox(s, Inches(1.15), Inches(2.25), Inches(5.2), Inches(0.35),
                "CLARIFY UNKNOWNS", 13, CORAL, bold=True)
    unk_rows = [
        ("Known knowns", "Already in the prompt"),
        ("Known unknowns", "Gaps you can name"),
        ("Unknown knowns", "Obvious but unwritten"),
        ("Unknown unknowns", "Not considered yet"),
    ]
    uy = Inches(2.85)
    for label, desc in unk_rows:
        add_round_rect(s, Inches(1.15), uy, Inches(5.2), Inches(0.75), CARD, radius=0.1)
        add_textbox(s, Inches(1.35), uy + Inches(0.18), Inches(2.4), Inches(0.4),
                    label, 14, INK, bold=True)
        add_textbox(s, Inches(3.8), uy + Inches(0.18), Inches(2.35), Inches(0.4),
                    desc, 14, SLATE)
        uy += Inches(0.85)
    # right card — 5 meta bullets max
    add_round_rect(s, Inches(6.9), Inches(2.0), Inches(5.7), Inches(4.6), INK, radius=0.06)
    add_textbox(s, Inches(7.25), Inches(2.25), Inches(5.1), Inches(0.35),
                "META-PROMPTS TO RERUN", 13, TEAL, bold=True)
    meta = [
        "Self-model audit of stale harness context",
        "Compare files to recent real behavior",
        "Run big-picture priority and ikigai prompts",
        "Refresh agents.md when intelligence jumps",
        "Treat each release as context-hygiene day",
    ]
    add_bullet_block(s, Inches(7.25), Inches(2.85), Inches(5.1), Inches(3.4),
                     meta, size=15, color=WHITE, bullet_color=TEAL)
    add_notes(s,
        "Combine Tariq's four unknowns with Daniel Meissler's tactical meta-prompts. "
        "Too specific → over-follow; too vague → generic best practices. "
        "Self-model audit quote idea: flag where the system optimizes for who you said you were. "
        "Audience should schedule a harness cleanup on the next model drop.")

    # =========================================================================
    # 13. QUOTE / STATEMENT hybrid — loops bar
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, INK)
    add_textbox(s, Inches(0.9), Inches(1.3), Inches(11.4), Inches(0.4),
                "NEW INTERACTION PATTERN", 13, CORAL, bold=True)
    add_textbox(s, Inches(0.9), Inches(1.9), Inches(11.4), Inches(2.2),
                "Don't use adjectives. Give Fable a bar it can check — then loop until it hits.",
                34, WHITE, bold=True)
    add_round_rect(s, Inches(0.9), Inches(4.5), Inches(11.4), Inches(2.0), CARD_DARK, radius=0.06)
    add_textbox(s, Inches(1.3), Inches(4.8), Inches(10.6), Inches(1.4),
                "“A stranger can't tell our render from the real photo.”\n"
                "Build → check → close the biggest gap → go again. Fable never decides it's finished.",
                18, WHITE, bold=False)
    add_notes(s,
        "Matt Schumer's tip. Vague 'high quality' stops at the model's too-low good enough. "
        "Concrete bars + /loop. The whole point: Fable never gets to decide it's finished. "
        "Audience should rewrite one quality adjective into a checkable test before the next creative run.")

    # =========================================================================
    # 14. FOUR LOOPS — data/framework visual
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, OFF_WHITE)
    add_textbox(s, Inches(0.7), Inches(0.35), Inches(12), Inches(1.2),
                "Four loop types turn one-shot prompts into goal-seeking systems.",
                36, INK, bold=True)
    loops = [
        ("01", "Turn-based", "You direct each turn.\nBest for short, one-off tasks.", TEAL),
        ("02", "Goal-based", "Evaluator enforces criteria.\nStops at success or max turns.", CORAL),
        ("03", "Time-based", "Triggered on an interval.\nBuilt for recurring work.", INK),
        ("04", "Proactive", "Event or schedule starts it.\nNo human needed in real time.", TEAL_DEEP),
    ]
    positions = [
        (Inches(0.7), Inches(1.8)),
        (Inches(6.85), Inches(1.8)),
        (Inches(0.7), Inches(4.5)),
        (Inches(6.85), Inches(4.5)),
    ]
    for (num, title, body, accent), (lx, ty) in zip(loops, positions):
        add_round_rect(s, lx, ty, Inches(5.75), Inches(2.4), WHITE, radius=0.06)
        add_rect(s, lx, ty, Inches(0.14), Inches(2.4), accent)
        add_textbox(s, lx + Inches(0.4), ty + Inches(0.3), Inches(1.2), Inches(0.45),
                    num, 22, accent, bold=True)
        add_textbox(s, lx + Inches(1.6), ty + Inches(0.35), Inches(3.7), Inches(0.45),
                    title, 22, INK, bold=True)
        add_textbox(s, lx + Inches(0.4), ty + Inches(1.1), Inches(5.0), Inches(1.0),
                    body, 15, SLATE)
    add_notes(s,
        "From the Claude Devs post NLW cites. Emphasize goal-based: defining success criteria stops early exits; "
        "an evaluator model sends work back. Preview: next months of exploration will push loops into creative and knowledge work. "
        "Audience should pick one recurring task for a time-based or proactive loop experiment.")

    # =========================================================================
    # 15. STATEMENT — organizational twin
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, INK)
    add_rect(s, 0, Inches(0), Inches(0.35), SLIDE_H, TEAL)
    add_textbox(s, Inches(1.0), Inches(1.7), Inches(11.2), Inches(2.5),
                "Organizations keep using AI for the same work — just faster, cheaper, slightly better.",
                34, WHITE, bold=True)
    add_textbox(s, Inches(1.0), Inches(4.5), Inches(11.2), Inches(1.4),
                "The unlock is a new relationship with work — and categories of work that weren't possible before.",
                20, TEAL, bold=True)
    add_notes(s,
        "Close the individual → organizational analogy. Default is accelerating known work; the prize is unlocking new work. "
        "Harder, more exciting. Set up the takeaways as the personal and team checklist. "
        "Audience should feel ambition at the org level, not just prompt craft.")

    # =========================================================================
    # 16. TAKEAWAYS
    # =========================================================================
    s = prs.slides.add_slide(blank)
    set_slide_bg(s, OFF_WHITE)
    add_rect(s, 0, 0, SLIDE_W, Inches(1.55), INK)
    add_textbox(s, Inches(0.7), Inches(0.4), Inches(12), Inches(0.85),
                "What to do differently starting today", 36, WHITE, bold=True)
    takes = [
        "Set explicit boundaries for tenacious models",
        "Delete repeated rules; match Sol/Terra/Luna and effort",
        "Automate optics; co-pilot execution; spar on impact",
        "Clarify unknowns; refresh harness on every leap",
        "Replace quality adjectives with loops against a hard bar",
    ]
    y = Inches(1.95)
    for i, t in enumerate(takes, 1):
        add_round_rect(s, Inches(0.7), y, Inches(11.9), Inches(0.85), WHITE, radius=0.08)
        add_round_rect(s, Inches(0.9), y + Inches(0.18), Inches(0.5), Inches(0.5), TEAL if i % 2 else CORAL, radius=0.2)
        add_textbox(s, Inches(0.95), y + Inches(0.25), Inches(0.4), Inches(0.4),
                    str(i), 16, WHITE, bold=True, align=PP_ALIGN.CENTER)
        add_textbox(s, Inches(1.7), y + Inches(0.22), Inches(10.5), Inches(0.5),
                    t, 18, INK, bold=True)
        y += Inches(1.0)
    add_notes(s,
        "Recap without rushing. One line each. End on ambition: assume no limits, try the biggest hard things, "
        "and let real limits reveal themselves. Thank the audience; point them to the episode if they want the full source stories.")

    out = "/workspace/podcast_presentation.pptx"
    prs.save(out)
    return out, len(prs.slides)


if __name__ == "__main__":
    path, n = make_prs()
    print(f"Wrote {path} with {n} slides")
