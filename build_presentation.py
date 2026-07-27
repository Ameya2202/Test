#!/usr/bin/env python3
"""Executive PowerPoint deck from AI Agent Memory System transcript."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import nsmap
from lxml import etree
import copy

# --- Palette: cool architecture briefing (not corporate purple / cream) ---
INK = RGBColor(0x08, 0x16, 0x28)       # near-black navy
DEEP = RGBColor(0x0F, 0x2A, 0x44)      # deep slate-navy
TEAL = RGBColor(0x00, 0xC2, 0xA8)      # electric teal accent
TEAL_DK = RGBColor(0x00, 0x8F, 0x7A)
CYAN = RGBColor(0x4D, 0xD0, 0xE1)      # secondary cool highlight
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
OFFWHITE = RGBColor(0xF2, 0xF6, 0xFA)  # cool light (not beige)
SLATE = RGBColor(0x5A, 0x6B, 0x7D)
MUTED = RGBColor(0x8A, 0x9B, 0xAB)
CARD = RGBColor(0x14, 0x35, 0x52)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H


def set_run(run, size, bold=False, color=WHITE, font="Calibri"):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font


def add_rect(slide, left, top, width, height, fill, line=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
    return shape


def add_round_rect(slide, left, top, width, height, fill, adjustments=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    return shape


def add_oval(slide, left, top, width, height, fill):
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    return shape


def add_textbox(slide, left, top, width, height, text, size=18, bold=False,
                color=WHITE, align=PP_ALIGN.LEFT, font="Calibri", anchor=MSO_ANCHOR.TOP):
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
    set_run(run, size, bold=bold, color=color, font=font)
    return box


def add_para(tf, text, size=18, bold=False, color=WHITE, align=PP_ALIGN.LEFT, space_before=6, space_after=4):
    p = tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    run = p.add_run()
    run.text = text
    set_run(run, size, bold=bold, color=color)
    return p


def set_notes(slide, text):
    notes = slide.notes_slide
    notes.notes_text_frame.text = text


def blank_slide():
    return prs.slides.add_slide(prs.slide_layouts[6])  # blank


# =============================================================================
# SLIDE 1 — Title (full-bleed statement)
# =============================================================================
s = blank_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, INK)
# Large teal geometric accent block (left panel visual)
add_rect(s, 0, 0, Inches(0.35), SLIDE_H, TEAL)
# Abstract memory nodes
add_oval(s, Inches(10.6), Inches(1.2), Inches(1.8), Inches(1.8), DEEP)
add_oval(s, Inches(11.4), Inches(2.6), Inches(1.1), Inches(1.1), TEAL_DK)
add_oval(s, Inches(10.2), Inches(3.4), Inches(0.7), Inches(0.7), TEAL)
add_oval(s, Inches(11.8), Inches(4.4), Inches(0.9), Inches(0.9), CARD)
add_textbox(s, Inches(0.9), Inches(1.6), Inches(9.5), Inches(2.4),
            "Your AI already remembers you.\nHere’s the architecture behind it.",
            size=40, bold=True, color=WHITE)
add_textbox(s, Inches(0.9), Inches(4.5), Inches(9.5), Inches(0.6),
            "Working · Procedural · Semantic · Episodic Memory for AI Agents",
            size=18, color=TEAL)
add_textbox(s, Inches(0.9), Inches(5.4), Inches(9.5), Inches(0.5),
            "Based on Sean’s AI Stories  ·  ~12 min briefing",
            size=14, color=MUTED)
set_notes(s, """SAY: Open by naming the paradox: products like ChatGPT and Claude already feel like they know the user and the company — but most builders cannot explain the memory stack underneath.

TRANSCRIPT SUPPORT: Opening — “you're probably already using a memory system without even realizing it.”

AUDIENCE SHOULD: Feel oriented and curious; understand this is an architecture briefing, not a product demo.""")


# =============================================================================
# SLIDE 2 — Full-bleed statement (hook)
# =============================================================================
s = blank_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, DEEP)
add_rect(s, Inches(0.8), Inches(2.4), Inches(0.18), Inches(2.4), TEAL)
add_textbox(s, Inches(1.3), Inches(2.5), Inches(10.5), Inches(2.2),
            "You’re already using an agent memory system — without realizing it.",
            size=36, bold=True, color=WHITE)
add_textbox(s, Inches(1.3), Inches(5.0), Inches(10.5), Inches(0.6),
            "Ask who you are, what you asked last week, what your company does — it knows.",
            size=18, color=CYAN)
set_notes(s, """SAY: Ground the room in lived experience. Memory is not a future feature; it’s already shipping in mainstream tools.

TRANSCRIPT SUPPORT: “when you ask your AI tool about who you are and the question that you asked them for the past week, they all know what's going on.” Also founders: sometimes they remember the company without explanation.

AUDIENCE SHOULD: Accept that memory systems are production reality, so the rest of the deck explains how they work.""")


# =============================================================================
# SLIDE 3 — The illusion (process visual)
# =============================================================================
s = blank_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, OFFWHITE)
add_textbox(s, Inches(0.7), Inches(0.45), Inches(12), Inches(1.1),
            "A user prompt never hits the LLM alone.",
            size=36, bold=True, color=INK)

# Flow boxes
labels = ["User Prompt", "Working Memory", "LLM / Q&A Agent", "Reply"]
xs = [0.7, 3.7, 6.9, 10.2]
for i, (lab, x) in enumerate(zip(labels, xs)):
    fill = TEAL if i == 1 else DEEP
    add_round_rect(s, Inches(x), Inches(2.6), Inches(2.5), Inches(1.35), fill)
    add_textbox(s, Inches(x), Inches(2.95), Inches(2.5), Inches(0.8),
                lab, size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    if i < 3:
        # arrow chevron
        arr = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + 2.55), Inches(3.0), Inches(0.35), Inches(0.4))
        arr.fill.solid()
        arr.fill.fore_color.rgb = TEAL if i == 0 else SLATE
        arr.line.fill.background()

bullets = [
    "We imagine a direct chat with the model.",
    "Context is assembled before generation.",
    "Memory design decides what enters that context.",
]
box = s.shapes.add_textbox(Inches(0.7), Inches(4.6), Inches(11.5), Inches(2.2))
tf = box.text_frame
tf.word_wrap = True
for i, b in enumerate(bullets):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_before = Pt(8)
    run = p.add_run()
    run.text = "▸  " + b
    set_run(run, 18, color=DEEP)

set_notes(s, """SAY: Break the mental model. Users think they talk to a pink LLM bubble; architects know a context assembly step sits in front.

TRANSCRIPT SUPPORT: “We might think that we're asking the question to this pink bubble, which is an LLM… In between that, there's some more steps that's happening.”

AUDIENCE SHOULD: Shift from “chatbot magic” to “context engineering.”""")


# =============================================================================
# SLIDE 4 — Working memory triad
# =============================================================================
s = blank_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, OFFWHITE)
add_textbox(s, Inches(0.7), Inches(0.4), Inches(12), Inches(1.1),
            "Working memory is the agent’s context RAM.",
            size=36, bold=True, color=INK)

cards = [
    ("User Prompt", "The live question\nentering the system"),
    ("Chat History", "Everything said\nin this conversation"),
    ("System Prompt", "Role and rules\nshaping the reply"),
]
for i, (title, body) in enumerate(cards):
    x = 0.7 + i * 4.1
    add_round_rect(s, Inches(x), Inches(2.0), Inches(3.7), Inches(3.6), DEEP)
    add_oval(s, Inches(x + 1.35), Inches(2.35), Inches(1.0), Inches(1.0), TEAL)
    add_textbox(s, Inches(x + 1.35), Inches(2.55), Inches(1.0), Inches(0.7),
                str(i + 1), size=22, bold=True, color=INK, align=PP_ALIGN.CENTER)
    add_textbox(s, Inches(x + 0.25), Inches(3.55), Inches(3.2), Inches(0.6),
                title, size=22, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_textbox(s, Inches(x + 0.25), Inches(4.3), Inches(3.2), Inches(1.0),
                body, size=16, color=CYAN, align=PP_ALIGN.CENTER)

set_notes(s, """SAY: Define working memory as the active context window — prompt + history + system role — before any long-term store is involved.

TRANSCRIPT SUPPORT: “the user prompt, the current chat history, and the system prompt are the basic components that will be fed into this working memory.” Elon Musk system-prompt example.

AUDIENCE SHOULD: Be able to name the three inputs to working memory.""")


# =============================================================================
# SLIDE 5 — Quote callout (ephemeral)
# =============================================================================
s = blank_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, INK)
# Large quotation mark as visual
add_textbox(s, Inches(0.8), Inches(0.8), Inches(2), Inches(1.5),
            "“", size=120, bold=True, color=TEAL)
add_textbox(s, Inches(1.2), Inches(2.2), Inches(10.8), Inches(2.8),
            "This session is ephemeral… we’re literally just making an LLM call.",
            size=36, bold=True, color=WHITE)
add_textbox(s, Inches(1.2), Inches(5.4), Inches(10), Inches(0.5),
            "— Shawn, on AI agent sessions without a memory store",
            size=16, color=MUTED)
# Accent shape
add_rect(s, Inches(1.2), Inches(5.1), Inches(1.5), Inches(0.08), TEAL)
set_notes(s, """SAY: Pause on this line. Without persistence, “memory” is only the in-flight chat buffer.

TRANSCRIPT SUPPORT: “this session is ephemeral, which means that nothing here will get saved unless you manually save them in a database… We're literally just making an LLM call right here.”

AUDIENCE SHOULD: Feel the fragility of session-only agents — and want a better design.""")


# =============================================================================
# SLIDE 6 — What ephemeral sessions forget
# =============================================================================
s = blank_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, OFFWHITE)
add_textbox(s, Inches(0.7), Inches(0.4), Inches(12), Inches(1.2),
            "Ephemeral sessions forget what makes service personal.",
            size=36, bold=True, color=INK)

items = [
    ("Inventory", "Product stocks and catalog state"),
    ("Purchases", "Prior order and delivery history"),
    ("Taste", "Customer preferences over time"),
    ("Conflict", "Past complaints and disputes"),
]
for i, (h, b) in enumerate(items):
    y = 1.9 + i * 1.15
    add_round_rect(s, Inches(0.7), Inches(y), Inches(11.8), Inches(1.0), DEEP if i % 2 == 0 else CARD)
    add_rect(s, Inches(0.7), Inches(y), Inches(0.18), Inches(1.0), TEAL)
    add_textbox(s, Inches(1.2), Inches(y + 0.15), Inches(2.5), Inches(0.7),
                h, size=20, bold=True, color=TEAL, anchor=MSO_ANCHOR.MIDDLE)
    add_textbox(s, Inches(4.0), Inches(y + 0.2), Inches(8), Inches(0.6),
                b, size=20, color=WHITE)

set_notes(s, """SAY: Use the e-commerce agent example. Current chat history ≠ business memory.

TRANSCRIPT SUPPORT: Session “does not know anything about your product stocks… previous purchase history, your customers' taste… any complaints in the past.”

AUDIENCE SHOULD: See concrete failure modes of memory-less agents in customer experience.""")


# =============================================================================
# SLIDE 7 — Three pillars (architecture diagram)
# =============================================================================
s = blank_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, OFFWHITE)
add_textbox(s, Inches(0.7), Inches(0.35), Inches(12), Inches(1.0),
            "Three pillars make working memory complete.",
            size=36, bold=True, color=INK)

# Center working memory
add_round_rect(s, Inches(4.4), Inches(1.7), Inches(4.5), Inches(1.2), TEAL)
add_textbox(s, Inches(4.4), Inches(2.0), Inches(4.5), Inches(0.7),
            "Working Memory", size=22, bold=True, color=INK, align=PP_ALIGN.CENTER)

pillars = [
    ("Procedural", "How to act\nSkills & habits"),
    ("Semantic", "What is true\nDurable facts"),
    ("Episodic", "What happened\nDated events"),
]
colors = [DEEP, CARD, DEEP]
for i, ((title, body), c) in enumerate(zip(pillars, colors)):
    x = 0.9 + i * 4.15
    add_round_rect(s, Inches(x), Inches(3.6), Inches(3.7), Inches(2.6), c)
    add_textbox(s, Inches(x + 0.2), Inches(3.9), Inches(3.3), Inches(0.6),
                title, size=24, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
    add_textbox(s, Inches(x + 0.2), Inches(4.7), Inches(3.3), Inches(1.2),
                body, size=18, color=WHITE, align=PP_ALIGN.CENTER)
    # connector line visual (thin rect)
    add_rect(s, Inches(x + 1.7), Inches(2.9), Inches(0.12), Inches(0.7), TEAL)

set_notes(s, """SAY: Introduce the stack as three complementary long-term layers feeding working memory.

TRANSCRIPT SUPPORT: “there are three main pillars… procedural memory, semantic memory, and episodic memory.”

AUDIENCE SHOULD: Hold the three-part model before diving into each pillar.""")


# =============================================================================
# SLIDE 8 — Procedural memory
# =============================================================================
s = blank_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, OFFWHITE)
add_textbox(s, Inches(0.7), Inches(0.4), Inches(12), Inches(1.2),
            "Procedural memory teaches agents how to behave.",
            size=36, bold=True, color=INK)

# Left visual panel
add_round_rect(s, Inches(0.7), Inches(1.9), Inches(5.2), Inches(4.6), DEEP)
add_textbox(s, Inches(1.0), Inches(2.3), Inches(4.6), Inches(0.6),
            "Think of it as habit", size=22, bold=True, color=TEAL)
add_textbox(s, Inches(1.0), Inches(3.1), Inches(4.6), Inches(2.8),
            "Not a fact to recall.\nA procedure to follow\nwhen a situation appears.",
            size=22, color=WHITE)

# Right bullets
add_round_rect(s, Inches(6.3), Inches(1.9), Inches(6.3), Inches(4.6), CARD)
bullets = [
    "Encodes behavior under pressure",
    "Often shipped as markdown skills",
    "Example: apologize when a customer is angry",
    "Feeds working memory as skill.md",
    "Separate from event logs and facts",
]
box = s.shapes.add_textbox(Inches(6.7), Inches(2.3), Inches(5.5), Inches(3.8))
tf = box.text_frame
tf.word_wrap = True
for i, b in enumerate(bullets):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_before = Pt(10)
    run = p.add_run()
    run.text = "▸  " + b
    set_run(run, 18, color=WHITE)

set_notes(s, """SAY: Procedural memory is policy-as-memory — how to act, not what happened.

TRANSCRIPT SUPPORT: Angry-customer apology skill; “habit you want to teach”; saved as files / skill.md.

AUDIENCE SHOULD: Distinguish skills/procedures from RAG knowledge.""")


# =============================================================================
# SLIDE 9 — Two-column comparison: Semantic vs Episodic
# =============================================================================
s = blank_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, OFFWHITE)
add_textbox(s, Inches(0.7), Inches(0.35), Inches(12), Inches(1.0),
            "Semantic stores truth. Episodic stores the timeline.",
            size=36, bold=True, color=INK)

# Left column
add_round_rect(s, Inches(0.6), Inches(1.6), Inches(5.9), Inches(5.2), DEEP)
add_rect(s, Inches(0.6), Inches(1.6), Inches(5.9), Inches(0.9), TEAL)
add_textbox(s, Inches(0.6), Inches(1.75), Inches(5.9), Inches(0.6),
            "Semantic Memory", size=24, bold=True, color=INK, align=PP_ALIGN.CENTER)
left = [
    "Durable facts and profiles",
    "Company, brand, products",
    "Stable customer identity",
    "Retrieved via RAG / top-K",
    "Condensed for reuse",
]
box = s.shapes.add_textbox(Inches(1.0), Inches(2.8), Inches(5.1), Inches(3.6))
tf = box.text_frame
for i, b in enumerate(left):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_before = Pt(12)
    run = p.add_run()
    run.text = "▸  " + b
    set_run(run, 18, color=WHITE)

# Right column
add_round_rect(s, Inches(6.8), Inches(1.6), Inches(5.9), Inches(5.2), CARD)
add_rect(s, Inches(6.8), Inches(1.6), Inches(5.9), Inches(0.9), CYAN)
add_textbox(s, Inches(6.8), Inches(1.75), Inches(5.9), Inches(0.6),
            "Episodic Memory", size=24, bold=True, color=INK, align=PP_ALIGN.CENTER)
right = [
    "Dated events and activities",
    "Past chat histories",
    "Purchases, deliveries, complaints",
    "Living log after each reply",
    "Too large to search every turn",
]
box = s.shapes.add_textbox(Inches(7.2), Inches(2.8), Inches(5.1), Inches(3.6))
tf = box.text_frame
for i, b in enumerate(right):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_before = Pt(12)
    run = p.add_run()
    run.text = "▸  " + b
    set_run(run, 18, color=WHITE)

set_notes(s, """SAY: Drive the contrast hard: “what is true” vs “what happened when.”

TRANSCRIPT SUPPORT: Semantic = durable facts/user profile; Episodic = dated events/timeline/past chat history; e-commerce examples for episodic.

AUDIENCE SHOULD: Stop treating “vector memory” as one bucket.""")


# =============================================================================
# SLIDE 10 — Quote callout (durable facts)
# =============================================================================
s = blank_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, INK)
add_textbox(s, Inches(0.8), Inches(0.7), Inches(2), Inches(1.4),
            "“", size=120, bold=True, color=TEAL)
add_textbox(s, Inches(1.2), Inches(2.0), Inches(10.8), Inches(3.2),
            "Because the foundational model does not know who you are, you need to save durable facts.",
            size=36, bold=True, color=WHITE)
add_textbox(s, Inches(1.2), Inches(5.5), Inches(10), Inches(0.5),
            "— Shawn, on semantic memory for unknown brands and builders",
            size=16, color=MUTED)
add_rect(s, Inches(1.2), Inches(5.2), Inches(1.5), Inches(0.08), TEAL)
set_notes(s, """SAY: Famous brands may already live in training data or web search; everyone else must persist profile facts.

TRANSCRIPT SUPPORT: Walmart contrast; “foundational large language model does not know who you are, you need to save some durable facts… in a database.”

AUDIENCE SHOULD: Treat company/customer profiles as first-class memory assets.""")


# =============================================================================
# SLIDE 11 — Data highlight (1M tokens + top-K)
# =============================================================================
s = blank_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, OFFWHITE)
add_textbox(s, Inches(0.7), Inches(0.35), Inches(12), Inches(1.0),
            "Selective retrieval beats stuffing the whole database.",
            size=36, bold=True, color=INK)

# Big number cards
add_round_rect(s, Inches(0.7), Inches(1.7), Inches(5.7), Inches(4.6), DEEP)
add_textbox(s, Inches(0.7), Inches(2.3), Inches(5.7), Inches(1.5),
            "~1M", size=96, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
add_textbox(s, Inches(1.0), Inches(4.0), Inches(5.1), Inches(1.5),
            "tokens ≈ common LLM\ncontext window ceiling",
            size=20, color=WHITE, align=PP_ALIGN.CENTER)

add_round_rect(s, Inches(6.9), Inches(1.7), Inches(5.7), Inches(4.6), CARD)
add_textbox(s, Inches(6.9), Inches(2.3), Inches(5.7), Inches(1.5),
            "Top-5", size=96, bold=True, color=CYAN, align=PP_ALIGN.CENTER)
add_textbox(s, Inches(7.2), Inches(4.0), Inches(5.1), Inches(1.5),
            "if K = 5, RAG feeds only\nthe most relevant chunks",
            size=20, color=WHITE, align=PP_ALIGN.CENTER)

set_notes(s, """SAY: Surface the two hard numbers from the talk. Overloading context is expensive, slow, and less accurate.

TRANSCRIPT SUPPORT: “context window for most LLMs is roughly 1 million tokens”; “if K is five, then it's looking for the top five most relevant pieces.”

AUDIENCE SHOULD: Internalize why RAG exists economically and operationally.""")


# =============================================================================
# SLIDE 12 — RAG / vector stores
# =============================================================================
s = blank_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, OFFWHITE)
add_textbox(s, Inches(0.7), Inches(0.4), Inches(12), Inches(1.1),
            "RAG turns meaning into searchable numbers.",
            size=36, bold=True, color=INK)

# Process strip
steps = ["Text", "Embeddings", "Vector Store", "Similarity", "Context"]
for i, step in enumerate(steps):
    x = 0.6 + i * 2.5
    add_oval(s, Inches(x + 0.55), Inches(1.9), Inches(1.1), Inches(1.1), TEAL if i % 2 == 0 else DEEP)
    add_textbox(s, Inches(x), Inches(3.2), Inches(2.2), Inches(0.6),
                step, size=16, bold=True, color=INK, align=PP_ALIGN.CENTER)
    if i < 4:
        arr = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + 1.9), Inches(2.2), Inches(0.4), Inches(0.4))
        arr.fill.solid()
        arr.fill.fore_color.rgb = SLATE
        arr.line.fill.background()

bullets = [
    "Computers process numbers, not documents",
    "Each word becomes a numeric vector",
    "Similarity search selects relevant facts",
    "Only those facts enter working memory",
]
box = s.shapes.add_textbox(Inches(0.9), Inches(4.3), Inches(11.5), Inches(2.5))
tf = box.text_frame
for i, b in enumerate(bullets):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_before = Pt(8)
    run = p.add_run()
    run.text = "▸  " + b
    set_run(run, 20, color=DEEP)

set_notes(s, """SAY: Explain embeddings simply: text → vectors → similarity → top-K into the prompt.

TRANSCRIPT SUPPORT: Vector store as embedded arrays; “computers cannot process text… only process numbers”; turning words into lists of numbers; similarity search = RAG.

AUDIENCE SHOULD: Connect vector DBs to the memory story without drowning in tooling.""")


# =============================================================================
# SLIDE 13 — Quote callout (don't always search episodic)
# =============================================================================
s = blank_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, INK)
add_textbox(s, Inches(0.8), Inches(0.7), Inches(2), Inches(1.4),
            "“", size=120, bold=True, color=TEAL)
add_textbox(s, Inches(1.2), Inches(2.0), Inches(10.8), Inches(3.0),
            "You don’t want the agent always searching a huge episodic database of everything that happened.",
            size=36, bold=True, color=WHITE)
add_textbox(s, Inches(1.2), Inches(5.5), Inches(10.5), Inches(0.5),
            "— Shawn, on why efficient systems prefer durable summarized facts",
            size=16, color=MUTED)
add_rect(s, Inches(1.2), Inches(5.2), Inches(1.5), Inches(0.08), TEAL)
set_notes(s, """SAY: This is the efficiency thesis: raw history is necessary but not sufficient for every turn.

TRANSCRIPT SUPPORT: “you don't want the AI agent to always search these kind of information from an episodic memory because that's just a huge database… You want some kind of durable summarized facts.”

AUDIENCE SHOULD: Anticipate consolidation as the missing link.""")


# =============================================================================
# SLIDE 14 — Consolidation gate (diagram)
# =============================================================================
s = blank_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, OFFWHITE)
add_textbox(s, Inches(0.7), Inches(0.35), Inches(12), Inches(1.0),
            "A consolidation gate turns noisy history into facts.",
            size=36, bold=True, color=INK)

# Flow stages
stages = [
    ("Episodic Log", "Every chat &\nactivity append"),
    ("Gate", "After N chats\nor activities"),
    ("Summarizer", "Compress what\nmatters most"),
    ("Semantic Store", "Durable facts\nfor retrieval"),
]
for i, (t, b) in enumerate(stages):
    x = 0.55 + i * 3.2
    fill = TEAL if i == 1 else DEEP
    add_round_rect(s, Inches(x), Inches(1.8), Inches(2.9), Inches(3.2), fill)
    add_textbox(s, Inches(x + 0.1), Inches(2.2), Inches(2.7), Inches(0.7),
                t, size=20, bold=True, color=INK if i == 1 else TEAL, align=PP_ALIGN.CENTER)
    add_textbox(s, Inches(x + 0.15), Inches(3.2), Inches(2.6), Inches(1.4),
                b, size=16, color=INK if i == 1 else WHITE, align=PP_ALIGN.CENTER)
    if i < 3:
        arr = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + 2.95), Inches(3.1), Inches(0.22), Inches(0.35))
        arr.fill.solid()
        arr.fill.fore_color.rgb = TEAL
        arr.line.fill.background()

add_textbox(s, Inches(0.7), Inches(5.4), Inches(12), Inches(1.2),
            "Gate examples from the talk: consolidate after ~20 conversations — or ~100 activities.\nResult: lower token spend, faster tools, editable core memories (ChatGPT / Claude pattern).",
            size=16, color=DEEP)

set_notes(s, """SAY: Walk the pipeline. Without a gate, summarization just duplicates storage.

TRANSCRIPT SUPPORT: Summarize at a frequency into semantic memory; gate after certain chats (20 / 100); summarizer agent; token savings and speed; editable memories in ChatGPT/Claude.

AUDIENCE SHOULD: See consolidation as a designed control loop, not continuous dump.""")


# =============================================================================
# SLIDE 15 — Takeaways
# =============================================================================
s = blank_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, INK)
add_rect(s, 0, 0, Inches(0.35), SLIDE_H, TEAL)
add_textbox(s, Inches(0.9), Inches(0.4), Inches(11.5), Inches(0.9),
            "Build memory as a context layer — not a chat log.",
            size=36, bold=True, color=WHITE)

takeaways = [
    "Working memory = prompt + history + system role",
    "Procedural memory encodes skills and habits",
    "Semantic memory holds durable facts via RAG",
    "Episodic memory is the dated activity timeline",
    "Gate consolidation to keep tokens fast and cheap",
]
for i, t in enumerate(takeaways):
    y = 1.5 + i * 0.95
    add_round_rect(s, Inches(0.9), Inches(y), Inches(11.5), Inches(0.8), DEEP)
    add_oval(s, Inches(1.15), Inches(y + 0.15), Inches(0.5), Inches(0.5), TEAL)
    add_textbox(s, Inches(1.15), Inches(y + 0.22), Inches(0.5), Inches(0.4),
                str(i + 1), size=16, bold=True, color=INK, align=PP_ALIGN.CENTER)
    add_textbox(s, Inches(1.9), Inches(y + 0.18), Inches(10), Inches(0.5),
                t, size=20, bold=True, color=WHITE)

set_notes(s, """SAY: Close on the full system: four layers working together as a context layer on top of interaction.

TRANSCRIPT SUPPORT: Closing synthesis — record efficiently, summarize into core semantic memory, keep episodic timeline, define behavioral skills; “memory that will be added as a context layer.”

AUDIENCE SHOULD: Leave with a repeatable architecture checklist they can apply to their agents.""")


out = "/workspace/podcast_presentation.pptx"
prs.save(out)
print(f"Saved {out} with {len(prs.slides)} slides")
