from runtime.package.manager import PackageManager, PackageManifest, PackageState
from kernel.security.control import MemoryAuditSink

class Trust:
    def __init__(self, valid=True): self.valid = valid
    def verify(self, manifest): return self.valid

class Runtime:
    def __init__(self, compatible=True): self.value = compatible
    def compatible(self, minimum_version): return self.value

class ApprovalPolicy:
    def __init__(self, allowed=True): self.allowed = allowed
    def allows(self, approver, package_name, reason):
        return self.allowed and approver == "security-reviewer" and package_name == "secuagent"

def manifest():
    return PackageManifest("secuagent", "1.0.0", "security-application", "0.5.0", frozenset({"threat.detect", "incident.analyze"}), frozenset({"event.read"}), frozenset({"siem.query"}), {"cpu":"2","memory":"4Gi"}, {"allowed":("siem.internal",)}, "raonwglobal", "test-signature")

def manager(trust=True, compatible=True): return PackageManager(Trust(trust), Runtime(compatible), MemoryAuditSink())

def test_valid_package_lifecycle():
    pm=manager(); assert pm.discover(manifest()).state is PackageState.DISCOVERED
    assert pm.verify("secuagent").state is PackageState.VERIFIED
    assert pm.stage("secuagent").state is PackageState.STAGED
    assert pm.install("secuagent").state is PackageState.INSTALLED
    assert pm.activate("secuagent").state is PackageState.ACTIVATED

def test_untrusted_package_cannot_activate():
    pm=manager(False); pm.discover(manifest()); assert pm.verify("secuagent").state is PackageState.REJECTED

def test_incompatible_package_rejected():
    pm=manager(True, False); pm.discover(manifest()); assert pm.verify("secuagent").state is PackageState.REJECTED

def test_activation_requires_install():
    pm=manager(); pm.discover(manifest()); pm.verify("secuagent")
    try: pm.activate("secuagent")
    except PermissionError: pass
    else: raise AssertionError("activation must require install")

def test_sandbox_exposes_only_declared_contract():
    pm=manager(); pm.discover(manifest()); pm.verify("secuagent"); pm.stage("secuagent"); pm.install("secuagent")
    context=pm.sandbox_context("secuagent")
    assert context["capabilities"] == frozenset({"threat.detect","incident.analyze"})
    assert context["tools"] == frozenset({"siem.query"})
    assert context["resources"]["memory"] == "4Gi"

def test_quarantine_revokes_package_activation_and_is_audited():
    audit = MemoryAuditSink()
    pm = PackageManager(Trust(), Runtime(), audit)
    pm.discover(manifest())
    pm.verify("secuagent")
    pm.stage("secuagent")
    pm.install("secuagent")
    pm.activate("secuagent")

    record = pm.quarantine("secuagent", reason="integrity_alert")
    assert record.state is PackageState.QUARANTINED
    assert audit.records[-1]["event"] == "quarantine"
    assert audit.records[-1]["reason"] == "integrity_alert"

    try:
        pm.sandbox_context("secuagent")
    except PermissionError as exc:
        assert str(exc) == "invalid_package_state:QUARANTINED"
    else:
        raise AssertionError("quarantined package must not expose sandbox context")


def test_quarantine_rejects_package_that_was_never_active():
    pm = manager()
    pm.discover(manifest())
    try:
        pm.quarantine("secuagent", reason="unexpected_state")
    except RuntimeError as exc:
        assert str(exc) == "package_not_active"
    else:
        raise AssertionError("inactive package cannot be quarantined as active")

def test_quarantined_package_requires_explicit_recovery_and_fresh_verification():
    trust = Trust()
    runtime = Runtime()
    audit = MemoryAuditSink()
    pm = PackageManager(trust, runtime, audit, recovery_approval_policy=ApprovalPolicy())
    pm.discover(manifest())
    pm.verify("secuagent")
    pm.stage("secuagent")
    pm.install("secuagent")
    pm.activate("secuagent")
    pm.quarantine("secuagent", reason="integrity_alert")

    try:
        pm.verify("secuagent")
    except RuntimeError as exc:
        assert str(exc) == "package_quarantined_requires_recovery"
    else:
        raise AssertionError("ordinary verification must not bypass quarantine")

    trust.valid = False
    try:
        pm.recover_quarantined("secuagent", approved_by="security-reviewer", reason="review")
    except PermissionError as exc:
        assert str(exc) == "trust_verification_failed"
    else:
        raise AssertionError("untrusted package must not recover")
    assert pm.get("secuagent").state is PackageState.QUARANTINED
    assert audit.records[-1]["event"] == "quarantine_recovery_failed"

    trust.valid = True
    recovered = pm.recover_quarantined(
        "secuagent", approved_by="security-reviewer", reason="integrity-cleared"
    )
    assert recovered.state is PackageState.VERIFIED
    assert audit.records[-1]["event"] == "quarantine_recovery_approved"
    assert audit.records[-1]["approved_by"] == "security-reviewer"

    try:
        pm.recover_quarantined("secuagent", approved_by="reviewer", reason="again")
    except RuntimeError as exc:
        assert str(exc) == "package_not_quarantined"
    else:
        raise AssertionError("recovery must only apply to quarantined packages")



def test_quarantine_recovery_fails_closed_without_approver_policy():
    pm = manager()
    pm.discover(manifest())
    pm.verify("secuagent")
    pm.stage("secuagent")
    pm.install("secuagent")
    pm.activate("secuagent")
    pm.quarantine("secuagent")

    try:
        pm.recover_quarantined("secuagent", approved_by="security-reviewer", reason="review")
    except PermissionError as exc:
        assert str(exc) == "recovery_approver_not_authorized"
    else:
        raise AssertionError("missing approval policy must deny recovery")
    assert pm.get("secuagent").state is PackageState.QUARANTINED


def test_quarantine_recovery_rejects_unauthorized_approver():
    audit = MemoryAuditSink()
    pm = PackageManager(Trust(), Runtime(), audit, recovery_approval_policy=ApprovalPolicy(allowed=False))
    pm.discover(manifest())
    pm.verify("secuagent")
    pm.stage("secuagent")
    pm.install("secuagent")
    pm.activate("secuagent")
    pm.quarantine("secuagent")

    try:
        pm.recover_quarantined("secuagent", approved_by="security-reviewer", reason="review")
    except PermissionError as exc:
        assert str(exc) == "recovery_approver_not_authorized"
    else:
        raise AssertionError("unauthorized approver must be denied")
    assert pm.get("secuagent").state is PackageState.QUARANTINED
    assert audit.records[-1]["event"] == "quarantine_recovery_denied"


def test_quarantine_recovery_requires_auditable_approval_fields():
    pm = manager()
    pm.discover(manifest())
    pm.verify("secuagent")
    pm.stage("secuagent")
    pm.install("secuagent")
    pm.activate("secuagent")
    pm.quarantine("secuagent")
    for approver, reason in (("", "review"), ("reviewer", "  ")):
        try:
            pm.recover_quarantined("secuagent", approved_by=approver, reason=reason)
        except ValueError as exc:
            assert str(exc) == "recovery_approval_and_reason_required"
        else:
            raise AssertionError("recovery requires approver and reason")

