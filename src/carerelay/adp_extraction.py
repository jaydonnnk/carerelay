"""Read-back port and explicitly offline extractor. No network or ADP activation."""
from dataclasses import dataclass
from typing import Literal, Protocol

from carerelay.domain.models import COMPARISON_FIELDS, SourceSpan
from carerelay.domain.rules import source_candidates


@dataclass(frozen=True)
class ExtractionInput:
    confirmed_text: str
    action_forms: frozenset[str]
    deadline_forms: frozenset[str]
    owner_forms: frozenset[str]
    correlation_id: str
    instruction_version: str
    schema_version: Literal["carerelay-readback-v1"]


@dataclass(frozen=True)
class RawExtraction:
    schema_version: Literal["carerelay-readback-v1"]
    action_span: SourceSpan | None
    deadline_span: SourceSpan | None
    next_owner_span: SourceSpan | None
    uncertain_fields: frozenset[str]
    refused: bool


@dataclass(frozen=True)
class ExtractionResult:
    mode: Literal["adp", "local-sim"]
    validation: Literal["valid", "invalid", "refused", "timeout", "transport", "disabled"]
    raw: RawExtraction | None
    request_id: str
    trace_id: str | None
    instruction_version: str
    schema_version: str
    model_version: str | None
    failure_category: str | None


class ReadbackExtractor(Protocol):
    def extract(self, request: ExtractionInput, *, budget_seconds: float) -> ExtractionResult: ...


class OfflineReadbackExtractor:
    """Exact-source lexical demo; code independently checks doubt and comparison."""

    def extract(self, request: ExtractionInput, *, budget_seconds: float = 5.0) -> ExtractionResult:
        fields = (request.action_forms, request.deadline_forms, request.owner_forms)
        spans = tuple(source_candidates(request.confirmed_text, forms) for forms in fields)
        selected = tuple(max(candidates, key=lambda span: span.end - span.start)
                         if candidates else None for candidates in spans)
        uncertain = frozenset(field for field, span in zip(COMPARISON_FIELDS, selected) if span is None)
        raw = RawExtraction("carerelay-readback-v1", *selected, uncertain, False)
        return ExtractionResult("local-sim", "valid", raw, request.correlation_id, None,
                                "offline-fixture-v1", "carerelay-readback-v1", None, None)


def eligible_offline_output(result: ExtractionResult, *, confirmed_text: str) -> RawExtraction | None:
    """Validate the injected port's output. Unavailable never triggers fallback."""
    if result.mode != "local-sim" or result.validation != "valid" or result.raw is None:
        return None
    raw = result.raw
    if raw.schema_version != "carerelay-readback-v1" or type(raw.refused) is not bool or raw.refused:
        return None
    if not isinstance(raw.uncertain_fields, frozenset) or not raw.uncertain_fields <= frozenset(COMPARISON_FIELDS):
        return None
    for field, span in zip(COMPARISON_FIELDS, (raw.action_span, raw.deadline_span, raw.next_owner_span)):
        if span is None:
            if field not in raw.uncertain_fields:
                return None
        elif (not isinstance(span, SourceSpan) or type(span.start) is not int or type(span.end) is not int
                or not 0 <= span.start < span.end <= len(confirmed_text)
                or confirmed_text[span.start:span.end] != span.text):
            return None
        elif (span.text[:1].isascii() and span.text[:1].isalnum() and span.start > 0
              and (confirmed_text[span.start - 1].isalnum() or confirmed_text[span.start - 1] == "_")):
            return None
        elif (span.text[-1:].isascii() and span.text[-1:].isalnum() and span.end < len(confirmed_text)
              and (confirmed_text[span.end].isalnum() or confirmed_text[span.end] == "_")):
            return None
    return raw
