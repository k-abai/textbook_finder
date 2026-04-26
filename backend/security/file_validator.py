from __future__ import annotations

from dataclasses import dataclass

from .url_scanner import URLScanner, URLValidationError


@dataclass(frozen=True)
class ResolutionSnapshot:
    hostname: str
    addresses: tuple
    classes: frozenset[str]


class FileValidator:
    """Validates that download targets remain in the same IP safety class."""

    def __init__(self, scanner: URLScanner | None = None) -> None:
        self.scanner = scanner or URLScanner()

    def prepare_download(self, url: str) -> ResolutionSnapshot:
        target = self.scanner.scan(url)
        return ResolutionSnapshot(
            hostname=target.hostname,
            addresses=target.addresses,
            classes=self.scanner.classify_addresses(target.addresses),
        )

    def validate_before_download(self, url: str, snapshot: ResolutionSnapshot) -> ResolutionSnapshot:
        """Re-resolve immediately before download to mitigate DNS rebinding."""
        target = self.scanner.scan(url)
        current_classes = self.scanner.classify_addresses(target.addresses)
        if current_classes != snapshot.classes:
            raise URLValidationError(
                "DNS resolution class changed before download; possible rebinding attempt"
            )

        return ResolutionSnapshot(
            hostname=target.hostname,
            addresses=target.addresses,
            classes=current_classes,
        )
