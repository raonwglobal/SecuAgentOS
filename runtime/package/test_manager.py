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
