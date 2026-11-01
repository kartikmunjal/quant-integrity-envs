"""Standalone pure-mock evidence for the unchanged shared helper's ordering.

This diagnostic deliberately reproduces a missing lifecycle guarantee. Its
passing assertion is evidence of the simulated race, never a runtime gate pass.
No Docker command, model action, credential access, or network operation occurs.
Run with: .venv/bin/python tests/validation/p5a_runtime_cancellation_diagnostic.py
"""

from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
from pathlib import Path
from unittest.mock import patch

import qi_runtime


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "results" / "p5a_runtime_blocker.json"


async def reproduce_ordering() -> dict:
    """Cancel the actual helper while a fake daemon operation remains pending."""
    shared_path = ROOT / "src" / "qi_runtime" / "__init__.py"
    shared_before = shared_path.read_bytes()
    helper = inspect.unwrap(qi_runtime.execute_program)
    helper_source = inspect.getsource(helper)
    events: list[str] = []
    observations: list[str] = []
    counts = {"model_actions": 0, "writes": 0, "execution": 0, "answer_parsing": 0}
    provisioning = asyncio.Event()
    permit_daemon_creation = asyncio.Event()
    daemon_job = None
    fake_runtime = None

    class FakeDirectory:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return "pure-mock-no-filesystem"

        def __exit__(self, *args):
            observations.append("temporary_directory_exited")
            return False

    class FakeWorkPath:
        def __init__(self, value):
            pass

        def chmod(self, mode):
            pass

    class FakeRuntime:
        def __init__(self, workspace):
            nonlocal fake_runtime
            fake_runtime = self
            self.created = False
            self.stopped = False

        async def start(self):
            nonlocal daemon_job

            async def daemon_create():
                await permit_daemon_creation.wait()
                self.created = True
                events.append("created")

            # Model a daemon-side request that a disconnected/cancelled client
            # cannot retract. Shield only this fake daemon job, not helper.start.
            daemon_job = asyncio.create_task(daemon_create())
            provisioning.set()
            try:
                await asyncio.shield(daemon_job)
            except asyncio.CancelledError:
                observations.append("startup_client_cancelled")
                raise

        async def stop(self):
            events.append("removed" if self.created else "remove_before_create")
            self.created = False
            self.stopped = True

        async def write(self, *args):
            counts["writes"] += 1
            raise AssertionError("diagnostic must stop before setup/model work")

        async def execute(self):
            counts["execution"] += 1
            raise AssertionError("diagnostic must not execute submitted code")

    def parse_answer(value):
        counts["answer_parsing"] += 1
        raise AssertionError("diagnostic must not parse a submitted answer")

    cancelled = False
    task = None
    try:
        # These are process-local substitutions; production source stays intact.
        with (
            patch.object(qi_runtime.tempfile, "TemporaryDirectory", FakeDirectory),
            patch.object(qi_runtime, "Path", FakeWorkPath),
            patch.object(qi_runtime, "CheckedRuntime", FakeRuntime),
        ):
            task = asyncio.create_task(
                qi_runtime.execute_program({}, "print('{}')", parse_answer, "p5a-diagnostic")
            )
            await provisioning.wait()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                cancelled = True
            # Creation is permitted only after actual helper cleanup returned.
            permit_daemon_creation.set()
            await daemon_job
    finally:
        # Restore via patch context managers and join all fake work, including
        # the failure path. There is no real container or filesystem workspace.
        permit_daemon_creation.set()
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        if daemon_job is not None:
            await asyncio.gather(daemon_job, return_exceptions=True)

    assert cancelled, "the actual helper must propagate cancellation"
    assert events == ["remove_before_create", "created"], events
    assert all(value == 0 for value in counts.values()), counts
    assert fake_runtime.created and fake_runtime.stopped
    assert shared_path.read_bytes() == shared_before, "shared runtime must remain unchanged"
    return {
        "diagnostic": "P5a shared execute_program cancellation ordering",
        "environment": "shared runtime; no environment episode generated",
        "generator_version_hash": None,
        "simulation_only": True,
        "actual_docker_leak_observed": False,
        "actual_model_or_api_calls": 0,
        "paid_spend_usd": "0",
        "events": events,
        "observations": observations,
        "work_counters": counts,
        "helper_cancellation_propagated": cancelled,
        "fake_resource_created_after_stop": fake_runtime.created and fake_runtime.stopped,
        "source_path": "src/qi_runtime/__init__.py",
        "source_sha256": hashlib.sha256(shared_before).hexdigest(),
        "helper_source_sha256": hashlib.sha256(helper_source.encode()).hexdigest(),
        "shared_source_unchanged": True,
        "diagnostic_assertions_passed": True,
        "runtime_contract_passed": False,
        "limitation": (
            "A fake daemon operation models late creation after client cancellation. "
            "This establishes that unchanged execute_program permits cleanup-before-"
            "creation ordering; it does not measure real Docker timing or prove an "
            "actual Docker resource leak. No model/solver work was performed."
        ),
        "required_owner_review": (
            "Shared provisioning must retain/join its startup operation or otherwise "
            "reconcile daemon-side creation before final cleanup. Cancellation must "
            "join provisioning and shield/join teardown; an expired episode must "
            "perform cleanup only, without launching primary/replay continuation."
        ),
    }


def test_simulated_shared_helper_cleanup_precedes_late_creation():
    report = asyncio.run(reproduce_ordering())
    assert report["events"] == ["remove_before_create", "created"]
    assert report["actual_model_or_api_calls"] == 0


if __name__ == "__main__":
    report = asyncio.run(reproduce_ordering())
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
