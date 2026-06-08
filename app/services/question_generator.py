import hashlib
import random
import re
from collections import Counter


SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[\"“‘]?[A-Z])")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
STOPWORDS = {
    "about", "after", "again", "also", "among", "because", "before", "being",
    "between", "could", "does", "from", "have", "into", "more", "most",
    "other", "over", "same", "should", "some", "such", "than", "that",
    "their", "them", "there", "these", "they", "this", "those", "through",
    "under", "very", "what", "when", "where", "which", "while", "with",
    "would", "your",
}
ANTONYMS = {
    "accept": "reject", "active": "passive", "allow": "prevent",
    "benefit": "harm", "careful": "careless", "common": "rare",
    "complex": "simple", "different": "similar", "difficult": "easy",
    "encourage": "discourage", "increase": "decrease", "important": "minor",
    "include": "exclude", "likely": "unlikely", "positive": "negative",
    "possible": "impossible", "reduce": "increase", "remember": "forget",
    "success": "failure", "support": "oppose", "useful": "useless",
}
GRAMMAR_SWAPS = [
    (re.compile(r"\bis\b", re.I), "are"),
    (re.compile(r"\bare\b", re.I), "is"),
    (re.compile(r"\bwas\b", re.I), "were"),
    (re.compile(r"\bwere\b", re.I), "was"),
    (re.compile(r"\bhas\b", re.I), "have"),
    (re.compile(r"\bhave\b", re.I), "has"),
    (re.compile(r"\bdoes\b", re.I), "do"),
    (re.compile(r"\bdo\b", re.I), "does"),
]


QUESTIONS_PER_PART = 10


def generate_exam(
    passages,
    requested_parts=None,
    questions_per_part=QUESTIONS_PER_PART,
    total_questions=None,
):
    requested_parts = requested_parts or ["part1", "part2", "part3", "part4"]
    clean = [normalize_passage(p) for p in passages if p.strip()]
    if not clean:
        raise ValueError("문제를 만들 지문이 없습니다.")

    builders = {
        "part1": [grammar_question, vocabulary_question],
        "part2": [order_question, insertion_question],
        "part3": [title_question, topic_question, summary_question],
        "part4": [
            arrangement_question,
            irrelevant_question,
            composition_question,
            correction_question,
            translation_question,
        ],
    }
    if total_questions is not None:
        questions = generate_balanced_questions(
            clean, requested_parts, builders, int(total_questions)
        )
    else:
        questions = []
        for part in requested_parts:
            part_builders = builders.get(part, [])
            for passage_index, passage in enumerate(clean, start=1):
                for variation in range(questions_per_part):
                    builder = part_builders[variation % len(part_builders)]
                    rng = seeded_rng(
                        f"{part}:{passage_index}:{variation}:{passage}"
                    )
                    question = builder(passage, rng)
                    question["part"] = part.upper()
                    question["passage_number"] = passage_index
                    question["variation"] = variation + 1
                    question["number"] = len(questions) + 1
                    questions.append(question)

    return {
        "title": "고등학교 영어 모의고사 변형문제",
        "questions": questions,
        "parts": requested_parts,
        "passage_count": len(clean),
        "questions_per_part": questions_per_part,
        "requested_question_count": total_questions,
    }


def generate_balanced_questions(passages, requested_parts, builders, total):
    if total < 1:
        raise ValueError("생성할 문항 수는 1개 이상이어야 합니다.")

    questions = []
    counters = {
        (part, passage_index): 0
        for part in requested_parts
        for passage_index in range(len(passages))
    }
    for index in range(total):
        part = requested_parts[index % len(requested_parts)]
        part_round = index // len(requested_parts)
        passage_index = part_round % len(passages)
        passage = passages[passage_index]
        variation = counters[(part, passage_index)]
        part_builders = builders[part]
        builder = part_builders[variation % len(part_builders)]
        rng = seeded_rng(
            f"balanced:{total}:{part}:{passage_index}:{variation}:{passage}"
        )
        question = builder(passage, rng)
        question["part"] = part.upper()
        question["passage_number"] = passage_index + 1
        question["variation"] = variation + 1
        question["number"] = index + 1
        questions.append(question)
        counters[(part, passage_index)] += 1
    return questions


def normalize_passage(text):
    return re.sub(r"\s+", " ", text).strip()


def seeded_rng(value):
    seed = int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:16], 16)
    return random.Random(seed)


def sentences(text):
    items = [item.strip() for item in SENTENCE_RE.split(text) if item.strip()]
    return items if len(items) >= 2 else [text]


def keywords(text, limit=5):
    words = [w.lower() for w in WORD_RE.findall(text)]
    counts = Counter(w for w in words if len(w) >= 5 and w not in STOPWORDS)
    return [word for word, _ in counts.most_common(limit)]


def clip(text, length=620):
    return text if len(text) <= length else text[:length].rsplit(" ", 1)[0] + "..."


def grammar_question(passage, rng):
    candidates = [s for s in sentences(passage) if len(s) > 45]
    source = rng.choice(candidates) if candidates else passage
    altered = source
    original = ""
    replacement = ""
    swaps = list(GRAMMAR_SWAPS)
    rng.shuffle(swaps)
    for pattern, swap in swaps:
        match = pattern.search(source)
        if match:
            original = match.group(0)
            replacement = match_case(swap, original)
            altered = source[: match.start()] + f"[{replacement}]" + source[match.end():]
            break
    if not original:
        match = WORD_RE.search(source)
        original = match.group(0) if match else "word"
        replacement = original + "s"
        altered = source.replace(original, f"[{replacement}]", 1)
    return q(
        "어법",
        "다음 문장에서 대괄호 친 부분의 어법상 오류를 찾아 바르게 고치시오.",
        altered,
        original,
        f"문맥과 문장 구조상 '{replacement}'는 '{original}'로 고쳐야 한다.",
    )


def vocabulary_question(passage, rng):
    matches = [m for m in WORD_RE.finditer(passage) if m.group(0).lower() in ANTONYMS]
    if matches:
        match = rng.choice(matches)
        original = match.group(0)
        replacement = match_case(ANTONYMS[original.lower()], original)
    else:
        words = [m for m in WORD_RE.finditer(passage) if len(m.group(0)) >= 7]
        match = rng.choice(words) if words else WORD_RE.search(passage)
        original = match.group(0)
        replacement = "un" + original.lower()
    altered = passage[: match.start()] + f"[{replacement}]" + passage[match.end():]
    return q(
        "어휘",
        "다음 글의 흐름상 대괄호 친 낱말이 적절하지 않다. 가장 적절한 낱말로 고치시오.",
        clip(altered),
        original,
        f"원문의 의미 흐름을 유지하려면 '{replacement}' 대신 '{original}'가 적절하다.",
    )


def order_question(passage, rng):
    items = sentences(passage)
    if len(items) < 4:
        items = split_chunks(passage, 4)
    start = rng.randrange(0, max(1, len(items) - 3))
    selected = items[start:start + 4]
    if len(selected) < 4:
        selected = items[-4:]
    intro, rest = selected[0], selected[1:4]
    labels = ["(A)", "(B)", "(C)"]
    shuffled = list(rest)
    rng.shuffle(shuffled)
    displayed = "\n\n".join(f"{label} {text}" for label, text in zip(labels, shuffled))
    answer = " - ".join(labels[shuffled.index(item)] for item in rest)
    return q(
        "문장 순서",
        "주어진 글 다음에 이어질 글의 순서로 가장 적절한 것을 쓰시오.",
        f"{intro}\n\n{displayed}",
        answer,
        "대명사, 연결어, 원인과 결과의 흐름을 따라 원문의 순서로 배열한다.",
    )


def insertion_question(passage, rng):
    items = sentences(passage)
    if len(items) < 4:
        items = split_chunks(passage, 5)
    target_index = rng.randrange(1, max(2, len(items) - 1))
    target = items.pop(target_index)
    marked = []
    for index, sentence in enumerate(items):
        marked.append(sentence)
        if index < len(items) - 1:
            marked.append(f"({index + 1})")
    answer = str(target_index)
    return q(
        "문장 삽입",
        f"주어진 문장이 들어가기에 가장 적절한 곳의 번호를 쓰시오.\n\n[주어진 문장] {target}",
        clip(" ".join(marked), 900),
        answer,
        "앞뒤 문장의 지시어와 논리적 연결을 고려하면 원래 위치가 가장 자연스럽다.",
    )


def title_question(passage, rng):
    keys = keywords(passage, 3)
    main = title_from_keywords(keys)
    options = [
        main,
        "Why Familiar Habits Always Fail",
        "The Hidden Cost of Ignoring Every Change",
        "A Simple Guide to Unrelated Daily Tasks",
        "When Individual Choice Has No Meaning",
    ]
    rng.shuffle(options)
    return mcq("제목", "다음 글의 제목으로 가장 적절한 것은?", passage, options, main)


def topic_question(passage, rng):
    keys = keywords(passage, 4)
    main = f"the relationship between {keys[0]} and {keys[1]}" if len(keys) > 1 else "the central idea of the passage"
    options = [
        main,
        "the history of an unrelated invention",
        "ways to memorize isolated facts",
        "the disadvantages of all social interaction",
        "a travel guide for first-time visitors",
    ]
    rng.shuffle(options)
    return mcq("주제", "다음 글의 주제로 가장 적절한 것은?", passage, options, main)


def summary_question(passage, rng):
    keys = keywords(passage, 8)
    if len(keys) > 2:
        offset = rng.randrange(len(keys) - 1)
        keys = keys[offset:] + keys[:offset]
    first = sentences(passage)[0]
    answer = f"{keys[0] if keys else 'context'} / {keys[1] if len(keys) > 1 else 'understanding'}"
    prompt = (
        "다음 글을 한 문장으로 요약하려 한다. 빈칸 (A), (B)에 들어갈 핵심어를 영어로 쓰시오.\n\n"
        f"The passage explains that (A) ______ is closely related to (B) ______.\n\n{clip(passage)}"
    )
    return q("요약", prompt, first, answer, "반복되는 핵심어와 첫 문장의 중심 내용을 기준으로 요약한다.")


def arrangement_question(passage, rng):
    candidates = [
        s for s in sentences(passage)
        if 8 <= len(WORD_RE.findall(s)) <= 18
    ]
    sentence = rng.choice(candidates) if candidates else rng.choice(sentences(passage))
    chunks = sentence.rstrip(".?!").split()
    shuffled = list(chunks)
    rng.shuffle(shuffled)
    return q(
        "문장 배열",
        "주어진 어구를 모두 사용하여 원래 문장을 완성하시오.",
        " / ".join(shuffled),
        sentence,
        "문장의 주어와 동사를 먼저 찾고 수식어와 목적어를 원문의 어순에 맞춘다.",
    )


def irrelevant_question(passage, rng):
    source_items = sentences(passage)
    start = rng.randrange(0, max(1, len(source_items) - 3))
    items = source_items[start:start + 4]
    distractors = [
        "Many tourists also enjoy taking colorful photographs during their vacations.",
        "Modern smartphones are available in many different colors and sizes.",
        "Some restaurants change their menus according to the season.",
        "Professional athletes usually follow carefully designed training schedules.",
        "Public transportation systems vary greatly from city to city.",
    ]
    irrelevant = rng.choice(distractors)
    insert_at = rng.randrange(1, len(items) + 1)
    items.insert(insert_at, irrelevant)
    numbered = "\n".join(f"{index + 1}. {text}" for index, text in enumerate(items))
    return q(
        "무관한 문장",
        "다음 글에서 전체 흐름과 관계없는 문장의 번호를 쓰시오.",
        numbered,
        str(insert_at + 1),
        "해당 문장은 지문의 핵심어 및 논리 전개와 연결되지 않는다.",
    )


def composition_question(passage, rng):
    candidates = [s for s in sentences(passage) if 50 <= len(s) <= 150]
    sentence = rng.choice(candidates) if candidates else rng.choice(sentences(passage))
    keys = keywords(sentence, 3)
    hint = ", ".join(keys) if keys else "use the words in the passage"
    return q(
        "영작",
        "다음 우리말 의미가 되도록 보기의 핵심어를 활용하여 영어 문장을 완성하시오.",
        f"핵심어: {hint}\n\n의미: 지문에서 필자가 강조한 내용을 한 문장으로 표현하시오.",
        sentence,
        "모범 답안은 원문의 핵심 문장이다. 의미가 같고 문법적으로 정확한 답도 허용한다.",
    )


def correction_question(passage, rng):
    base = grammar_question(passage, rng)
    base["type"] = "어법 서술형"
    base["prompt"] = "다음 문장의 어법상 잘못된 부분을 찾아 고친 뒤, 그 이유를 우리말로 설명하시오."
    return base


def translation_question(passage, rng):
    candidates = sorted(sentences(passage), key=len, reverse=True)[:5]
    sentence = rng.choice(candidates)
    keys = keywords(sentence, 4)
    guide = ", ".join(keys)
    return q(
        "해석",
        "다음 문장을 문맥에 맞게 자연스러운 우리말로 해석하시오.",
        sentence,
        f"핵심어({guide})의 관계가 드러나도록 자연스럽게 해석",
        "교사용 답안은 핵심 의미 요소를 제시한다. 문맥상 의미가 같으면 다양한 번역을 인정한다.",
    )


def q(kind, prompt, passage, answer, explanation):
    return {
        "type": kind,
        "prompt": prompt,
        "passage": clip(passage, 1100),
        "options": [],
        "answer": answer,
        "explanation": explanation,
    }


def mcq(kind, prompt, passage, options, answer):
    item = q(kind, prompt, clip(passage), str(options.index(answer) + 1), "반복되는 핵심어와 글 전체의 논지에 가장 잘 부합하는 선택지이다.")
    item["options"] = options
    return item


def split_chunks(text, count):
    words = text.split()
    size = max(1, len(words) // count)
    chunks = [" ".join(words[i:i + size]) for i in range(0, len(words), size)]
    return chunks[:count]


def title_from_keywords(keys):
    if len(keys) >= 2:
        return f"Understanding {keys[0].title()} Through {keys[1].title()}"
    if keys:
        return f"Why {keys[0].title()} Matters"
    return "Understanding the Main Idea"


def match_case(value, source):
    return value.capitalize() if source[:1].isupper() else value
