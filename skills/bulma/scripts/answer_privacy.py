"""Keep recognizable sensitive material out of Answer's direct-request evidence."""

import re


REDACTED = "[redacted]"
SAFE_REPLY = "Não posso compartilhar dados sensíveis nesta thread."
SECRET_PATTERNS = (
    re.compile(r"https://files\.slack\.com/[^\s<>|]+"),
    re.compile(r"-----BEGIN [^-\n]+PRIVATE KEY-----[\s\S]*?(?:-----END [^-\n]+PRIVATE KEY-----|\Z)"),
    re.compile(r"(?i)\b(?:bearer|basic)\s+[a-z0-9+/_.=-]{8,}"),
    re.compile(r"\b(?:xox[a-z]-[A-Za-z0-9-]{8,}|gh[pousr]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{12,}|sk_(?:live|test)_[A-Za-z0-9]{8,}|sk-[A-Za-z0-9_-]{16,}|(?:AKIA|ASIA)[A-Z0-9]{16})\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"(?i)\b(?:https?|postgres(?:ql)?|mysql|redis|mongodb(?:\+srv)?):\/\/[^\s/@]+:[^\s/@]+@[^\s<>]+"),
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?![ -]?\d)"),
    re.compile(
        r"(?i)\b(?:[\w.-]*?(?:api[_ -]?key|access[_ -]?key|token|password|passwd|secret|credential|senha)[\w.-]*)"
        r"[\"']?\s*(?::|=|\bis\b|\bé\b)\s*"
        r"(?:\"[^\"\n]+\"|'[^'\n]+'|[^\s,;)}\]>]{3,})"
    ),
)
SENSITIVE_LOCATOR = re.compile(
    r"(?i)(?:\.env(?:\.[\w.-]+)?\b|\b(?:keychain|printenv|process\.env|os\.environ|"
    r"getenv|environ|secrets?\s*manager|credentials?\s*store)\b|"
    r"\b[A-Z][A-Z0-9_]*_(?:TOKEN|SECRET|PASSWORD|API_KEY|PRIVATE_KEY)\b|"
    r"\.(?:pem|key|pfx|p12)\b)"
)


def redact(text, known=()):
    for value in known:
        if value:
            text = text.replace(value, REDACTED)
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(REDACTED, text)
    return text


def scrub(value, known=()):
    if isinstance(value, str):
        return redact(value, known)
    if isinstance(value, list):
        return [scrub(item, known) for item in value]
    if isinstance(value, dict):
        return {redact(key, known): scrub(item, known) for key, item in value.items()}
    return value


def safe_reply(text, known=()):
    return text if redact(text, known) == text and not SENSITIVE_LOCATOR.search(text) else SAFE_REPLY
