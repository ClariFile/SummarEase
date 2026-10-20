"""Extractive summaries (record C12, C13): every line is a sentence, bullet or line taken word for word from the
document, with its page, slide or section. Nothing is reworded, joined or invented. File names are never seen here:
the input is the readable text only (C7).

Three methods (MILESTONES.md, M2) rank the document's lines; one level builder turns any ranking into the four
nested levels within their budgets, so every method obeys the same rules:
  baseline   the opening lines of the document, or of each section
  structure  slides: titles and bullets, slides chosen by structure (title, agenda and summary slides)
  ranking    prose: sentences scored by how central their words are to this document, near-duplicates removed
"""
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .readable import OWN_KINDS, words

LEVELS = ("brief", "key", "detailed", "comprehensive")
LEVEL_NAMES = {"brief": "Brief", "key": "Key points", "detailed": "Detailed", "comprehensive": "Comprehensive"}
LEVEL_HINTS = {
    "brief": "The main takeaway, in 1 to 3 lines.",
    "key": "The main points, in the document's order.",
    "detailed": "Section by section: each heading with up to 3 lines.",
    "comprehensive": "The fullest useful summary, never a copy of the document.",
}
DEFAULT_LEVEL = "key"
METHODS = ("baseline", "structure", "ranking")

# Length budgets [Default] (record C12), in words of the readable text W: (floor, share of W).
BUDGETS = {"brief": (30, 0.03), "key": (80, 0.10), "detailed": (150, 0.20), "comprehensive": (0, 0.40)}
BRIEF_LINES = 3
KEY_LINES = 12
SECTION_LINES = 3
NEAR_DUPLICATE = 0.6    # ranking: a line sharing this share of its words with a better line is a repeat
OCR_WEIGHT = 0.5        # ranking: OCR text weighs less than native text (C12)
SECTIONS_WITHOUT_HEADINGS = 8   # a document with no headings is cut into about this many page or paragraph ranges
SLIDE_PDF_WORDS = 150   # a PDF whose pages are mostly landscape with at most this many words each is a slide deck
KEY_SLIDE = re.compile(r"\b(summary|conclusions?|key (points|takeaways)|takeaways?|recap|wrap[- ]up|in short)\b", re.I)
GUIDE_SLIDE = re.compile(r"\b(agenda|outline|overview|objectives?|contents|goals?|introduction)\b", re.I)
STOPWORDS = frozenset("""a about above after again all also am an and any are as at be because been before being below
between both but by can could did do does doing down during each few for from further had has have having he her here
hers him his how i if in into is it its itself just me more most my no nor not now of off on once only or other our
ours out over own same she should so some such than that the their theirs them then there these they this those
through to too under until up very was we were what when where which while who whom why will with would you your
yours""".split())
ABBREVIATIONS = frozenset("""e.g. i.e. etc. vs. dr. mr. mrs. ms. prof. fig. figs. no. al. approx. cf. st. jr. sr. inc.
ltd. co. u.s. p. pp. vol. eq. eqs. ch. sec. ref. refs.""".split())


@dataclass(frozen=True)
class Line:
    id: int          # reading order in the document
    text: str        # word for word from the document (spaces normalized)
    unit: int        # the page, slide, block or pasted paragraph it comes from
    kind: str        # heading | sentence | bullet | ocr | note
    section: int


@dataclass
class Section:
    label: str                   # SummarEase's own label: the unit range ("Pages 3-5"), shown when there is no heading
    heading: Line | None
    lines: list = field(default_factory=list)
    first: int | None = None     # its first and last unit
    last: int | None = None


@dataclass
class Source:
    """What the summarizer needs: the readable blocks and a few facts about the document. No file name."""
    blocks: list
    unit: str                    # page | slide | block | paragraph
    slides: bool
    repeated: frozenset = frozenset()   # headers, footers: lines on at least half the units (spaces normalized)
    template: frozenset = frozenset()   # the reader's template lines, digits as # ("Page # of #")
    hidden: frozenset = frozenset()     # hidden slides: like speaker notes, shown only at Comprehensive


@dataclass
class Summary:
    level: str
    method: str
    sections: list               # [(Section, [Line shown under it])]; Brief and Key points: one section, label ""
    budget: int
    total: int                   # W: words of the readable text
    gaps: list                   # [(unit, detail)]: what couldn't be read, as in the readable text
    hidden: frozenset = frozenset()
    unit: str = "page"           # what a line's unit is: page | slide | block | paragraph
    labels: list = field(default_factory=list)   # each section's name: its heading, else its unit range
    empty: str = ""              # why nothing is shown: no_text | unusable (no line a summary can use) | none_fit
    whole: bool = False          # a short document: every line this level could use is shown (C12)
    tables: int = 0              # table blocks: in the Source, not summarized
    omitted: list = field(default_factory=list)  # [(section, first unit)] with material that did not fit the budget

    @property
    def lines(self):
        return [l for _, ls in self.sections for l in ls]

    @property
    def words(self):
        return sum(len(l.text.split()) for l in self.lines)


def norm(text):
    return " ".join(text.split())


# -- sources --------------------------------------------------------------------------------------------------
def source_from_record(record, blocks):
    half = max(2, math.ceil(len(record.units) / 2))
    repeated = {norm(l["line"]) for l in record.recurring_lines if len(l["pages"]) >= half} \
        | {norm(l["line"]) for l in record.running_lines}
    template = {norm(l["line"]) for l in record.template_lines}
    slides = record.format == "pptx" or (record.format == "pdf" and _slide_pdf(record))
    hidden = frozenset(u.index for u in record.units if u.kind == "hidden slide")
    return Source(blocks, record.unit, slides, frozenset(repeated), frozenset(template), hidden)


def source_from_text(blocks):
    return Source(blocks, "paragraph", False)


def _slide_pdf(record):
    pages = [u for u in record.units if (u.layout or {}).get("width")]
    if not pages:
        return False
    landscape = sum(u.layout["width"] > u.layout["height"] for u in pages) / len(pages)
    per_page = sorted(len(u.text.split()) for u in record.units)[len(record.units) // 2]
    return landscape >= 0.8 and per_page <= SLIDE_PDF_WORDS


# -- the document's lines -------------------------------------------------------------------------------------
def sentences(text):
    """Split prose into sentences without changing a word. Abbreviations and initials do not end a sentence."""
    tokens = text.split()
    out, cur = [], []
    for i, t in enumerate(tokens):
        cur.append(t)
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        if nxt and re.search(r"[.!?][\"')\]”’]*$", t) and t.casefold() not in ABBREVIATIONS \
                and not re.fullmatch(r"[A-Z]\.|\(?(\d{1,3}|[A-Za-z])[.)]", t) and (nxt[0].isupper() or nxt[0].isdigit() or nxt[0] in "\"'“‘(["):
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def sections_of(src):
    """The document as sections of Lines. Slides: one section per slide. Prose: a section per heading; with no
    headings at all, page (or paragraph) ranges."""
    sections, n = [], 0

    def add(kind, text, unit):
        nonlocal n
        line = Line(n, norm(text), unit, kind, len(sections) - 1)
        n += 1
        return line

    current_unit = object()
    for b in src.blocks:
        if b.kind in OWN_KINDS or b.kind == "table" or not b.words():
            continue
        new_unit = b.unit != current_unit
        current_unit = b.unit
        heading = b.kind in ("title", "heading") and norm(b.text) not in src.repeated   # a running header is none
        if not sections or (src.slides and new_unit) or (not src.slides and heading):
            sections.append(Section("", None, first=b.unit))
        s = sections[-1]
        s.last = b.unit
        if heading and s.heading is None and not s.lines:
            s.heading = add("heading", b.text, b.unit)
            continue
        if b.kind == "list":
            parts = [("bullet", i) for i in b.rows]
        elif b.kind == "ocr":
            parts = [("ocr", l) for l in b.text.split("\n")]
        elif b.kind == "notes":
            parts = [("note", l) for l in b.text.split("\n")]
        elif src.slides or heading:
            parts = [("bullet" if not heading else "heading", l) for l in b.text.split("\n")]
        else:
            parts = [("sentence", s_) for s_ in sentences(b.text)]
        s.lines += [add(k, t, b.unit) for k, t in parts if t.strip()]
    if not src.slides and len(sections) == 1 and sections[0].heading is None and sections[0].lines:
        sections = _ranges(sections[0].lines)
    for s in sections:
        s.label = _range_label(src.unit, s.first, s.last)
    return sections


def _repeated(src, text):
    """A header, footer or template line: not summary material."""
    return norm(text) in src.repeated or re.sub(r"\d", "#", norm(text)) in src.template


def _ranges(lines):
    units = sorted({l.unit for l in lines})
    size = max(1, math.ceil(len(units) / SECTIONS_WITHOUT_HEADINGS))
    out = []
    for i, start in enumerate(range(0, len(units), size)):
        first, last = units[start], units[min(start + size, len(units)) - 1]
        out.append(Section("", None, [Line(l.id, l.text, l.unit, l.kind, i) for l in lines if first <= l.unit <= last],
                           first, last))
    return out


def _range_label(unit, first, last):
    name = {"page": "Page", "slide": "Slide", "paragraph": "Paragraph"}.get(unit, "Part")
    if unit == "block":
        return f"Part {first}" if first == last else f"Parts {first}-{last}"
    return f"{name} {first}" if first == last else f"{name}s {first}-{last}"


def candidates(sections, src):
    """Lines a summary may use: at least 3 words (2 for a bullet or title) with 2 that are words, not a header,
    footer or template line, and not an exact repeat of an earlier line."""
    seen, out = set(), []
    for s in sections:
        for l in ([s.heading] if s.heading else []) + s.lines:
            toks = l.text.split()
            alpha = sum(bool(re.search(r"[A-Za-z]{2}", t)) for t in toks)
            key = l.text.casefold()
            if alpha < 2 or len(toks) < (2 if l.kind in ("bullet", "heading") else 3) or key in seen \
                    or _repeated(src, l.text):
                continue
            seen.add(key)
            out.append(l)
    return out


# -- methods: each orders the candidate lines, best first -----------------------------------------------------
def baseline(sections, cands, src):
    """The opening lines: document order."""
    return [l for l in cands if l.kind != "heading" or src.slides]


def structure(sections, cands, src):
    """Slides by structure, not by ranking sentences (C12): the deck's title, then the bullets of summary slides,
    then the titles and bullets of agenda and overview slides and of slides an agenda names, then every other
    slide's title, then bullets slide by slide, first bullets first."""
    ok = {l.id for l in cands}
    title = lambda s: s.heading.text if s.heading else ""
    agenda = {l.text.casefold() for s in sections if GUIDE_SLIDE.search(title(s)) for l in s.lines}
    first, key, guide, titles, bullets = [], [], [], [], defaultdict(list)
    for i, s in enumerate(sections):
        mine = [l for l in s.lines if l.id in ok]
        if s.heading and s.heading.id in ok:
            (first if i == 0 else titles).append(s.heading)
        if i and KEY_SLIDE.search(title(s)):
            key += mine
        elif i and (GUIDE_SLIDE.search(title(s)) or title(s).casefold() in agenda):
            guide += ([s.heading] if s.heading in titles else []) + mine
        for r, l in enumerate(mine):
            bullets[r].append(l)
    order = first + key + guide + titles + [l for r in sorted(bullets) for l in bullets[r]]
    seen, out = set(), []
    for l in order:
        if l.id not in seen:
            seen.add(l.id)
            out.append(l)
    return out


def ranking(sections, cands, src):
    """Sentences scored by how central their words are to this document (TF-IDF over its own lines, cosine to the
    whole), OCR weighed less, near-duplicates of a better line removed. Headings are structure, not candidates."""
    lines = [l for l in cands if l.kind != "heading"]
    toks = [[w for w in re.findall(r"[a-z0-9]+", l.text.casefold()) if w not in STOPWORDS and len(w) > 1] for l in lines]
    df = Counter(w for t in toks for w in set(t))
    n = len(lines)
    idf = {w: math.log((1 + n) / (1 + c)) + 1 for w, c in df.items()}
    vecs = [{w: c * idf[w] for w, c in Counter(t).items()} for t in toks]
    centre = Counter()
    for v in vecs:
        centre.update(v)
    centre_norm = math.sqrt(sum(x * x for x in centre.values())) or 1

    def score(i):
        v = vecs[i]
        nv = math.sqrt(sum(x * x for x in v.values())) or 1
        s = sum(x * centre[w] for w, x in v.items()) / (nv * centre_norm)
        return s * (OCR_WEIGHT if lines[i].kind == "ocr" else 1)

    order = sorted(range(n), key=lambda i: (-round(score(i), 12), lines[i].id))
    kept, index, out = [], defaultdict(list), []
    for i in order:   # ponytail: overlap counted through an inverted index; fine for documents of a few 10k lines
        mine = set(toks[i])
        shared = Counter(k for w in mine for k in index[w])
        if any(c / len(mine | set(toks[k])) >= NEAR_DUPLICATE for k, c in shared.items()) if mine else False:
            continue
        for w in mine:
            index[w].append(i)
        out.append(lines[i])
    return out


# -- levels ---------------------------------------------------------------------------------------------------
def budget(level, total):
    floor, share = BUDGETS[level]
    return max(floor, int(share * total))


def build(src, level, method):
    """The summary of src at one level, from one method's order. Detailed is built first (each section's heading
    and up to 3 lines), Key points and Brief are chosen from it, and Comprehensive adds to it, so every level holds
    the lines of the level below (C12). A level never goes over its budget, headings included: a section that does
    not fit is left out and named in the summary (Q1, owner 2026-10-20)."""
    sections = sections_of(src)
    cands = candidates(sections, src)
    order = {"baseline": baseline, "structure": structure, "ranking": ranking}[method](sections, cands, src)
    rank = {l.id: i for i, l in enumerate(order)}
    total = sum(len(b.words()) for b in src.blocks if b.kind not in OWN_KINDS)
    native = any(l.kind != "ocr" for l in order)
    late = lambda l: l.kind == "note" or l.unit in src.hidden    # speaker notes and hidden slides: Comprehensive only
    is_head = lambda l: sections[l.section].heading is l

    def groups(keep):
        """{section: (heading still to show, its lines best first)} for the lines keep() accepts. A heading comes
        with its section's first line; a section with no such line may show its heading alone."""
        by_section = defaultdict(list)
        for l in order:
            if keep(l) and not is_head(l):
                by_section[l.section].append(l)
        out = {}
        for i, s in enumerate(sections):
            head = s.heading if s.heading and keep(s.heading) and (s.lines or src.slides) else None
            if by_section[i] or head:
                out[i] = (head, by_section[i] or [head])
        return out

    to_detail = groups(lambda l: not late(l))
    detailed = _rounds(to_detail, rank, budget("detailed", total), SECTION_LINES)
    chosen = {"detailed": detailed}
    pool = [l for l in order if l in detailed and (l.kind != "heading" or src.slides)]
    chosen["key"] = _greedy(pool, budget("key", total), KEY_LINES)
    pool = [l for l in order if l in chosen["key"] and (l.kind != "ocr" or not native)]
    chosen["brief"] = _greedy(pool, budget("brief", total), BRIEF_LINES)
    limit = budget(level, total)
    eligible = set(to_detail)
    if level == "comprehensive":
        # C12 (record 0.5): Comprehensive's budget is at least Detailed's, so it holds Detailed even below 375
        # words, where 40% of W is less than Detailed's floor.
        limit = max(limit, budget("detailed", total))
        to_add = groups(lambda l: l not in detailed)
        eligible |= set(to_add)
        chosen["comprehensive"] = detailed | _rounds(to_add, rank, limit - _words(detailed), None)
    shown = chosen[level]

    usable = {l for l in order if level == "comprehensive" or not late(l)}
    if level in ("detailed", "comprehensive"):
        usable |= {s.heading for i, s in enumerate(sections) if i in eligible and s.heading
                   and (level == "comprehensive" or not late(s.heading)) and (s.lines or src.slides)}
    else:
        usable = {l for l in usable if l.kind != "heading" or src.slides}
        if level == "brief" and native:
            usable = {l for l in usable if l.kind != "ocr"}
    gaps = next((b.rows for b in src.blocks if b.kind == "gaps"), [])
    labels = [s.heading.text if s.heading else s.label for s in sections]
    facts = dict(
        empty="" if shown else "no_text" if not total else "unusable" if not cands else "none_fit",
        whole=bool(shown) and total <= limit and usable <= shown,
        tables=sum(b.kind == "table" for b in src.blocks),
        omitted=[(i, sections[i].first) for i in sorted(eligible) if not any(l.section == i for l in shown)]
        if level in ("detailed", "comprehensive") else [],
    )
    done = lambda parts: Summary(level, method, parts, limit, total, gaps, src.hidden, src.unit, labels, **facts)
    if level in ("brief", "key"):
        flat = Section("", None, sorted(shown, key=lambda l: l.id))
        return done([(flat, flat.lines)] if shown else [])
    out = []
    for i, s in enumerate(sections):
        mine = sorted((l for l in shown if l.section == i and l is not s.heading), key=lambda l: l.id)
        if s.heading in shown or mine:
            out.append((s, ([s.heading] if s.heading in shown else []) + mine))
    return done(out)


def _words(lines):
    return sum(len(l.text.split()) for l in lines)


def _greedy(pool, room, most):
    """The best lines that fit the room, at most `most` of them."""
    out = set()
    for l in pool:
        if len(out) == most:
            break
        if len(l.text.split()) <= room:
            out.add(l)
            room -= len(l.text.split())
    return out


def _rounds(groups, rank, room, most):
    """Round by round, each section's next best line while it fits the room (at most `most` per section); within a
    round, the sections whose next line ranks best go first. groups: {section: (heading, lines)}; a heading not yet
    shown comes with its section's first line, and its words count against the room too."""
    out, nxt = set(), {s: 0 for s in groups}
    r = 0
    while nxt and (most is None or r < most):
        r += 1
        for s in sorted(nxt, key=lambda s: (rank.get(groups[s][1][nxt[s]].id, math.inf), s)):
            head, lines = groups[s]
            l = lines[nxt[s]]
            take = [l] + ([head] if head and head is not l and head not in out else [])
            if _words(take) <= room:
                out.update(take)
                room -= _words(take)
            nxt[s] += 1
        nxt = {s: i for s, i in nxt.items() if i < len(groups[s][1])}
    return out


def method_for(src):
    """What the app shows: slides by structure (C12); prose by the opening-lines baseline until a method beats it
    on the owner's rubric (MILESTONES.md, M2)."""
    return "structure" if src.slides else "baseline"


def summarize(src, level, method=None):
    return build(src, level, method or method_for(src))
