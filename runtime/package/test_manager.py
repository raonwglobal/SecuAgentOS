from runtime.package.manager import PackageManager, PackageManifest, PackageState
from kernel.security.control import MemoryAuditSink

class Trust:
    def __init__(self, valid=True): self.valid = valid
    def verify(self, manifest): return self.valid

class Runtime:
    def __init__(self, compatible=True): self.value = compatible
    def compatible(self, minimum_version): return self.value

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

