import re

def fix_hyphenated_words(text: str) -> str:
    """
    Joins words split across line breaks with a hyphen.
    e.g. 'compa-\nñero' or 'compa—\nñero' -> 'compañero'
    """
    # Matches word character + hyphen/dash + newline + optional whitespace + word character
    pattern = re.compile(r'(\b\w+)[-\u2010\u2013\u2014]\s*\n\s*(\w+\b)', re.UNICODE)
    return pattern.sub(r'\1\2', text)


def clean_dialogue_dashes(text: str) -> str:
    """
    Cleans dialogue dashes (—, –, -) for natural speech synthesis in TextAloud.
    - Removes opening dialogue dashes at paragraph start.
    - Converts narrator incises/acotaciones delimited by dashes into comma-separated pauses.
    """
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append('')
            continue

        # 1. Remove opening dialogue dash at line start
        stripped = re.sub(r'^[—–-]\s*', '', stripped)

        # 2. Handle narrator incises/acotaciones within dialogue
        # e.g., "Hola —dijo Juan—, pasa por favor." -> "Hola, dijo Juan, pasa por favor."
        def replace_incise_double(match):
            incise_text = match.group(1).strip()
            following_punct = match.group(2) or ''
            if following_punct in [',', ';']:
                return f", {incise_text}{following_punct} "
            elif following_punct in ['.', '!', '?']:
                return f", {incise_text}{following_punct} "
            else:
                return f", {incise_text}, "

        stripped = re.sub(r'\s+[—–-]\s*(.*?)\s*[—–-]\s*([.,;!?])?', replace_incise_double, stripped)

        # Match single dash incise at end of line/clause: " —dijo Juan."
        def replace_incise_single(match):
            incise_text = match.group(1).strip()
            punct = match.group(2) or ''
            return f", {incise_text}{punct}"

        stripped = re.sub(r'\s+[—–-]\s*(.*?)([.,;!?])?$', replace_incise_single, stripped)

        # Clean any double commas or punctuation artifacts created by replacement
        stripped = re.sub(r',\s*,', ',', stripped)
        stripped = re.sub(r'([.,!?])\s*,', r'\1', stripped)
        stripped = re.sub(r'\s+', ' ', stripped).strip()

        cleaned_lines.append(stripped)

    return '\n'.join(cleaned_lines)


def join_paragraphs(text: str) -> str:
    """
    Joins broken lines inside paragraphs while preserving paragraph breaks.
    """
    lines = text.split('\n')
    paragraphs = []
    current_para = []

    for line in lines:
        line_str = line.strip()
        if not line_str:
            if current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []
            continue

        if not current_para:
            current_para.append(line_str)
        else:
            prev_line = current_para[-1]
            # Check if previous line ended a sentence with terminal punctuation
            ends_sentence = re.search(r'[.!?:]\s*$', prev_line) is not None

            if ends_sentence:
                # Previous line ended a sentence; treat this new line as starting a new paragraph
                paragraphs.append(' '.join(current_para))
                current_para = [line_str]
            else:
                # Continuation line of same paragraph
                current_para.append(line_str)

    if current_para:
        paragraphs.append(' '.join(current_para))

    return '\n\n'.join(paragraphs)


def remove_headers_footers_and_page_numbers(pages_text: list[str]) -> list[str]:
    """
    Detects recurring top headers, bottom footers, and page numbers across pages and removes them.
    """
    if not pages_text:
        return []

    top_candidates = {}
    bottom_candidates = {}

    page_lines_list = []
    for p_idx, page in enumerate(pages_text):
        lines = [l.strip() for l in page.split('\n') if l.strip()]
        page_lines_list.append(lines)

        if lines:
            top_line = lines[0]
            if not re.match(r'^\d+$', top_line):
                top_candidates[top_line] = top_candidates.get(top_line, 0) + 1

            bottom_line = lines[-1]
            if not re.match(r'^\d+$', bottom_line):
                bottom_candidates[bottom_line] = bottom_candidates.get(bottom_line, 0) + 1

    num_pages = len(pages_text)
    threshold = max(2, num_pages * 0.25)

    repeated_headers = {line for line, count in top_candidates.items() if count >= threshold}
    repeated_footers = {line for line, count in bottom_candidates.items() if count >= threshold}

    cleaned_pages = []
    for lines in page_lines_list:
        filtered_lines = []
        for idx, line in enumerate(lines):
            if re.match(r'^(pág|página|page)?\s*[-–—]?\s*\d+\s*[-–—]?$', line, re.IGNORECASE):
                continue
            if idx == 0 and line in repeated_headers:
                continue
            if idx == len(lines) - 1 and line in repeated_footers:
                continue
            filtered_lines.append(line)

        cleaned_pages.append('\n'.join(filtered_lines))

    return cleaned_pages


def clean_text_for_textaloud(text: str,
                            fix_hyphens: bool = True,
                            clean_dialogues: bool = True,
                            merge_paragraphs: bool = True) -> str:
    """
    Main cleaning pipeline for text prior to TextAloud processing.
    """
    cleaned = text

    if fix_hyphens:
        cleaned = fix_hyphenated_words(cleaned)

    if clean_dialogues:
        cleaned = clean_dialogue_dashes(cleaned)

    if merge_paragraphs:
        cleaned = join_paragraphs(cleaned)

    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()
