import re
from pathlib import Path

from pypdf import PdfReader


QUESTION_MARKER = re.compile(r"(?<!\d)(1[89]|[2-4]\d)\.\s*")
CIRCLE_OPTION = re.compile(r"[①②③④⑤]")
SPACE = re.compile(r"[ \t]+")


def extract_pdf(path):
    reader = PdfReader(str(path))
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({"page": number, "text": clean_page_text(text)})

    full_text = "\n".join(item["text"] for item in pages)
    passages = extract_passages(full_text)
    if not passages:
        passages = fallback_paragraphs(full_text)

    return {
        "filename": Path(path).name,
        "page_count": len(reader.pages),
        "passages": passages,
    }


def clean_page_text(text):
    text = text.replace("\u00ad", "").replace("­", "")
    text = text.replace("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "\n")
    text = SPACE.sub(" ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_passages(text):
    matches = list(QUESTION_MARKER.finditer(text))
    results = []
    for index, match in enumerate(matches):
        number = int(match.group(1))
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        segment = text[match.end():end]
        passage = english_body(segment)
        if len(passage) < 180:
            continue
        results.append(
            {
                "id": f"q{number}",
                "source_number": number,
                "title": f"원문 {number}번",
                "text": passage,
                "selected": 18 <= number <= 45,
            }
        )
    return deduplicate(results)


def english_body(segment):
    option = CIRCLE_OPTION.search(segment)
    option_count = len(CIRCLE_OPTION.findall(segment))
    # Long passages usually place answer choices after the body. Shorter
    # positions often use circled numbers inside the passage itself.
    if option and (option.start() >= 350 or option_count <= 2):
        segment = segment[: option.start()]

    starts = list(re.finditer(r"(?<![A-Za-z])(?:[\"“‘]?[A-Z][A-Za-z])", segment))
    if not starts:
        return ""

    candidates = []
    for start in starts:
        body = segment[start.start():].strip()
        letters = sum(ch.isascii() and ch.isalpha() for ch in body)
        if letters >= 120:
            candidates.append(body)
    if not candidates:
        return ""

    body = max(candidates, key=len)
    body = re.sub(r"\s+", " ", body)
    body = re.sub(r"\s+([,.;:?!])", r"\1", body)
    return body.strip()


def fallback_paragraphs(text):
    chunks = re.split(r"\n\s*\n|(?<=[.!?])\s+(?=[A-Z])", text)
    results = []
    for chunk in chunks:
        chunk = re.sub(r"\s+", " ", chunk).strip()
        letters = sum(ch.isascii() and ch.isalpha() for ch in chunk)
        if len(chunk) >= 240 and letters / max(len(chunk), 1) > 0.65:
            results.append(
                {
                    "id": f"p{len(results) + 1}",
                    "source_number": None,
                    "title": f"추출 지문 {len(results) + 1}",
                    "text": chunk,
                    "selected": True,
                }
            )
    return results[:30]


def deduplicate(passages):
    seen = set()
    unique = []
    for passage in passages:
        key = passage["text"][:100].lower()
        if key not in seen:
            seen.add(key)
            unique.append(passage)
    return unique
