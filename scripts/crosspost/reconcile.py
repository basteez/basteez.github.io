from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


def normalize_canonical_url(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None
    if not s.lower().startswith("https://"):
        return None
    scheme, rest = s.split("://", 1)
    if "/" in rest:
        host, path = rest.split("/", 1)
        path = "/" + path
    else:
        host, path = rest, "/"
    host = host.lower()
    while path.endswith("//"):
        path = path[:-1]
    if not path.endswith("/"):
        path = path + "/"
    return f"{scheme.lower()}://{host}{path}"


@dataclass
class DevToArticleSummary:
    id: int
    canonical_url_raw: str | None
    canonical_url_norm: str | None
    url: str
    published: bool


def build_canonical_index(
    summaries: list[DevToArticleSummary],
) -> dict[str, list[int]]:
    index: dict[str, list[int]] = {}
    for s in summaries:
        if s.canonical_url_norm is None:
            continue
        index.setdefault(s.canonical_url_norm, []).append(s.id)
    return index


class ReconciledAction(Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    ADOPT = "ADOPT"
    SKIP_DRAFT = "SKIP_DRAFT"
    SKIP_SCHEDULED = "SKIP_SCHEDULED"
    SKIP_UNCHANGED = "SKIP_UNCHANGED"
    SKIP_OPT_OUT = "SKIP_OPT_OUT"
    FAIL_MULTIPLE_MATCHES = "FAIL_MULTIPLE_MATCHES"
    FAIL_ID_MISMATCH = "FAIL_ID_MISMATCH"


@dataclass
class RefinedClassification:
    action: ReconciledAction
    reason: str
    devto_article_id: int | None = None
    devto_url: str | None = None
    conflicting_ids: list[int] = field(default_factory=list)


_SKIP_ACTIONS = {
    ReconciledAction.SKIP_DRAFT,
    ReconciledAction.SKIP_SCHEDULED,
    ReconciledAction.SKIP_UNCHANGED,
    ReconciledAction.SKIP_OPT_OUT,
}


def reconcile(
    post,
    state_entry: dict | None,
    index: dict[str, list[int]],
    article_lookup: dict[int, DevToArticleSummary],
    *,
    prior_action: ReconciledAction | None = None,
) -> RefinedClassification:
    if prior_action in _SKIP_ACTIONS:
        raise ValueError(
            f"reconcile() called on SKIP action {prior_action}; "
            "SKIP classifications must short-circuit before reconciliation"
        )

    key = normalize_canonical_url(post.canonical_url)
    matches = list(index.get(key, [])) if key is not None else []

    if state_entry is None:
        if not matches:
            return RefinedClassification(
                action=ReconciledAction.CREATE,
                reason="new post",
            )
        if len(matches) == 1:
            summary = article_lookup[matches[0]]
            return RefinedClassification(
                action=ReconciledAction.ADOPT,
                reason="adopted existing dev.to article",
                devto_article_id=summary.id,
                devto_url=summary.url,
            )
        ids_str = ", ".join(str(i) for i in matches)
        return RefinedClassification(
            action=ReconciledAction.FAIL_MULTIPLE_MATCHES,
            reason=(
                f"dev.to has multiple articles with canonical_url {post.canonical_url} "
                f"(ids: {ids_str}) — delete duplicates on dev.to and re-run"
            ),
            conflicting_ids=list(matches),
        )

    state_id = int(state_entry["devto_article_id"])
    if not matches:
        return RefinedClassification(
            action=ReconciledAction.UPDATE,
            reason="body hash changed",
            devto_article_id=state_id,
        )

    if state_id in matches:
        return RefinedClassification(
            action=ReconciledAction.UPDATE,
            reason="body hash changed",
            devto_article_id=state_id,
        )

    if len(matches) == 1:
        other = matches[0]
        conflicting = [state_id, other]
        ids_repr = str(other)
    else:
        conflicting = [state_id] + list(matches)
        ids_repr = ", ".join(str(i) for i in matches)
    return RefinedClassification(
        action=ReconciledAction.FAIL_ID_MISMATCH,
        reason=(
            f"state says article {state_id} but canonical_url {post.canonical_url} "
            f"on dev.to resolves to article(s) {ids_repr} — reconcile manually"
        ),
        conflicting_ids=conflicting,
    )
