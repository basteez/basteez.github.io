from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from .models import DevtoArticle, PostFile, TitleIndex

_WHITESPACE_RUN = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    nfc = unicodedata.normalize("NFC", title)
    stripped = nfc.strip()
    collapsed = _WHITESPACE_RUN.sub(" ", stripped)
    return collapsed.casefold()


def build_title_index(articles: Iterable[DevtoArticle]) -> TitleIndex:
    index = TitleIndex()
    for article in articles:
        index.add(article.title)
    return index


def decide(post: PostFile, index: TitleIndex) -> str:
    title = post.title
    if title is None:
        return "skipped_invalid"
    if index.contains(title):
        return "skipped_exists"
    return "drafted"
