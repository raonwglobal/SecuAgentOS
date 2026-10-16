"""Minimal package manager and sandbox contract for SecuAgentOS."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Protocol

class PackageState(str, Enum):
    DISCOVERED = "DISCOVERED"
    VERIFIED = "VERIFIED"
    STAGED = "STAGED"
    INSTALLED = "INSTALLED"
    ACTIVATED = "ACTIVATED"
    DISABLED = "DISABLED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"
    FAILED = "FAILED"
    ROLLBACK = "ROLLBACK"

@dataclass(frozen=True)
class PackageManifest:
    name: str
    version: str
    package_type: str
    runtime_min: str
    capabilities: frozenset[str] = frozenset()
    permissions: frozenset[str] = frozenset()
    tools: frozenset[str] = frozenset()
    resources: Mapping[str, str] = field(default_factory=dict)
    network: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    publisher: str | None = None
    signature: str | None = None

@dataclass
class PackageRecord:
    manifest: PackageManifest
    state: PackageState = PackageState.DISCOVERED

class TrustVerifier(Protocol):
    def verify(self, manifest: PackageManifest) -> bool: ...

class RuntimeCompatibility(Protocol):
    def compatible(self, minimum_version: str) -> bool: ...

class PackageAudit(Protocol):
    def append(self, record: Mapping[str, object]) -> None: ...

class PackageSandbox:
    def context(self, manifest: PackageManifest) -> Mapping[str, object]:
        return {
            "capabilities": manifest.capabilities,
            "permissions": manifest.permissions,
            "tools": manifest.tools,
            "resources": dict(manifest.resources),
            "network": dict(manifest.network),
        }

class PackageManager:
    def __init__(self, trust: TrustVerifier, runtime: RuntimeCompatibility, audit: PackageAudit) -> None:
        self._trust, self._runtime, self._audit = trust, runtime, audit
        self._packages: dict[str, PackageRecord] = {}

    def discover(self, manifest: PackageManifest) -> PackageRecord:
        if manifest.name in self._packages:
            raise ValueError("package_already_discovered")
        record = PackageRecord(manifest)
        self._packages[manifest.name] = record
        self._audit.append({"package": manifest.name, "state": record.state.value, "event": "discover"})
        return record

    def verify(self, name: str) -> PackageRecord:
        record = self._packages[name]
        if record.state is PackageState.QUARANTINED:
            raise RuntimeError("package_quarantined_requires_recovery")
        if not self._trust.verify(record.manifest):
            record.state = PackageState.REJECTED
            self._audit.append({"package": name, "state": record.state.value, "event": "verify_failed"})
            return record
        if not self._runtime.compatible(record.manifest.runtime_min):
            record.state = PackageState.REJECTED
            self._audit.append({"package": name, "state": record.state.value, "event": "runtime_incompatible"})
            return record
        record.state = PackageState.VERIFIED
        self._audit.append({"package": name, "state": record.state.value, "event": "verified"})
        return record

    def stage(self, name: str) -> PackageRecord:
        record = self._packages[name]; self._require(record, PackageState.VERIFIED)
        record.state = PackageState.STAGED
        self._audit.append({"package": name, "state": record.state.value, "event": "stage"})
        return record

    def install(self, name: str) -> PackageRecord:
        record = self._packages[name]; self._require(record, PackageState.STAGED)
        record.state = PackageState.INSTALLED
        self._audit.append({"package": name, "state": record.state.value, "event": "install"})
        return record

    def activate(self, name: str) -> PackageRecord:
        record = self._packages[name]; self._require(record, PackageState.INSTALLED)
        record.state = PackageState.ACTIVATED
        self._audit.append({"package": name, "state": record.state.value, "event": "activate"})
        return record

    def disable(self, name: str) -> PackageRecord:
        record = self._packages[name]
        if record.state not in (PackageState.ACTIVATED, PackageState.DISABLED):
            raise RuntimeError("package_not_active")
        record.state = PackageState.DISABLED
        self._audit.append({"package": name, "state": record.state.value, "event": "disable"})
        return record

    def quarantine(self, name: str, reason: str = "security_review") -> PackageRecord:
        """Immediately revoke execution by quarantining an active package."""
        record = self._packages[name]
        if record.state not in (PackageState.ACTIVATED, PackageState.QUARANTINED):
            raise RuntimeError("package_not_active")
        record.state = PackageState.QUARANTINED
        self._audit.append({
            "package": name,
            "state": record.state.value,
            "event": "quarantine",
            "reason": reason,
        })
        return record

    def recover_quarantined(
        self, name: str, approved_by: str, reason: str
    ) -> PackageRecord:
        """Re-verify an explicitly approved quarantined package without activating it."""
        record = self._packages[name]
        if record.state is not PackageState.QUARANTINED:
            raise RuntimeError("package_not_quarantined")
        if not approved_by.strip() or not reason.strip():
            raise ValueError("recovery_approval_and_reason_required")

        if not self._trust.verify(record.manifest):
            self._audit.append({
                "package": name, "state": record.state.value,
                "event": "quarantine_recovery_failed", "reason": reason,
                "approved_by": approved_by, "failure": "trust_verification_failed",
            })
            raise PermissionError("trust_verification_failed")
        if not self._runtime.compatible(record.manifest.runtime_min):
            self._audit.append({
                "package": name, "state": record.state.value,
                "event": "quarantine_recovery_failed", "reason": reason,
                "approved_by": approved_by, "failure": "runtime_incompatible",
            })
            raise PermissionError("runtime_incompatible")

        record.state = PackageState.VERIFIED
        self._audit.append({
            "package": name, "state": record.state.value,
            "event": "quarantine_recovery_approved", "reason": reason,
            "approved_by": approved_by,
        })
        return record

    def get(self, name: str) -> PackageRecord:
        return self._packages[name]

    def sandbox_context(self, name: str) -> Mapping[str, object]:
        record = self._packages[name]
        self._require(record, PackageState.INSTALLED, PackageState.ACTIVATED)
        return PackageSandbox().context(record.manifest)

    @staticmethod
    def _require(record: PackageRecord, *states: PackageState) -> None:
        if record.state not in states:
            raise PermissionError(f"invalid_package_state:{record.state.value}")
