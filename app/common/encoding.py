from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def detect_encoding(raw_bytes: bytes) -> str:
    """Detect the encoding of raw bytes using chardet.

    Returns a Python codec name (e.g. 'utf-8', 'gbk', 'gb2312').
    Falls back to 'utf-8' with replacement on detection failure.
    """
    try:
        import chardet

        result = chardet.detect(raw_bytes)
        encoding = result.get('encoding', 'utf-8') or 'utf-8'
        confidence = result.get('confidence', 0)
        logger.info('Encoding detected: %s (confidence: %.2f)', encoding, confidence)
        # Normalize common aliases
        encoding_lower = encoding.lower()
        if encoding_lower in ('gb2312', 'gbk', 'gb18030'):
            return 'gbk'
        if encoding_lower.startswith('utf-16'):
            return 'utf-16'
        return 'utf-8' if confidence < 0.7 else encoding
    except ImportError:
        logger.warning('chardet not installed, falling back to utf-8')
        return 'utf-8'


def decode_bytes(raw_bytes: bytes) -> str:
    """Decode raw bytes to string, trying detected encoding first, then fallbacks."""
    import codecs

    encoding = detect_encoding(raw_bytes)
    codecs_to_try = [encoding, 'utf-8', 'gbk', 'gb2312', 'latin-1']
    tried: set[str] = set()

    for codec in codecs_to_try:
        if codec in tried:
            continue
        tried.add(codec)
        try:
            return raw_bytes.decode(codec)
        except (UnicodeDecodeError, LookupError):
            continue

    # Ultimate fallback
    return raw_bytes.decode('utf-8', errors='replace')
