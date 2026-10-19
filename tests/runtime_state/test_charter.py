from __future__ import annotations

from runtime_state.support import RuntimeCase, object_at

DIGEST = "c" * 64


class CharterTests(RuntimeCase):
    def test_full_route_budget_covers_full_targeted_and_recovery_cycles(self) -> None:
        runtime = self.base / "full-budgets"
        state = self.expect_ok(
            "init",
            "--runtime-dir",
            str(runtime),
            "--change",
            "full-budgets",
            "--workflow",
            "sk-team",
            "--policy-revision",
            "test-policy",
            "--route",
            "full",
        )
        assert state is not None
        self.assertEqual(
            object_at(state, "charter", "budgets"),
            {"attempts": 20, "review_rounds": 3, "remediations": 2},
        )

    def test_init_persists_explicit_charter_and_delivery(self) -> None:
        runtime = self.base / "charter"
        state = self.expect_ok(
            "init",
            "--runtime-dir",
            str(runtime),
            "--change",
            "charter",
            "--workflow",
            "sk-team",
            "--policy-revision",
            "test-policy",
            "--route",
            "quick",
            "--assurance",
            "elevated",
            "--authorization",
            "yolo",
            "--scope-sha256",
            DIGEST,
            "--workspace",
            "auto",
            "--workspace-resolved",
            "worktree",
            "--workspace-path",
            "/tmp/charter-worktree",
            "--destination",
            "merge",
            "--destination-target",
            "main",
            "--attempt-budget",
            "5",
            "--review-round-budget",
            "2",
            "--remediation-budget",
            "1",
        )
        assert state is not None
        self.assertEqual(state["schema_version"], 3)
        charter = object_at(state, "charter")
        self.assertEqual(charter["route"], "quick")
        self.assertEqual(charter["assurance"], "elevated")
        self.assertEqual(charter["authorization"], "yolo")
        self.assertEqual(
            object_at(charter, "workspace"),
            {
                "requested": "auto",
                "resolved": "worktree",
                "path": "/tmp/charter-worktree",
            },
        )
        self.assertEqual(object_at(charter, "destination"), {"kind": "merge", "target": "main"})
        self.assertEqual(object_at(state, "delivery")["status"], "pending")

    def test_yolo_auto_decides_ceremony_but_not_authority_gate(self) -> None:
        runtime = self.base / "yolo-gates"
        state = self.expect_ok(
            "init",
            "--runtime-dir",
            str(runtime),
            "--change",
            "yolo-gates",
            "--workflow",
            "sk-team",
            "--policy-revision",
            "test-policy",
            "--authorization",
            "yolo",
        )
        assert state is not None
        self.mutate(runtime, 1, "enter-stage", "--stage", "planning")
        state = self.mutate(
            runtime,
            2,
            "request-gate",
            "--stage",
            "planning",
            "--gate",
            "phase-complete",
            "--reason",
            "artifact ready",
            "--kind",
            "ceremony",
            "--reason-code",
            "phase.complete",
        )
        ceremony = object_at(state, "workflow", "stages", "planning", "gates", "phase-complete")
        self.assertEqual(ceremony["status"], "approved")
        self.assertEqual(ceremony["decision_source"], "policy")

        state = self.mutate(
            runtime,
            3,
            "request-gate",
            "--stage",
            "planning",
            "--gate",
            "scope",
            "--reason",
            "material product choice",
            "--kind",
            "authority_decision",
            "--reason-code",
            "decision.material_product",
        )
        authority = object_at(state, "workflow", "stages", "planning", "gates", "scope")
        self.assertEqual(authority["status"], "pending")
        waited = self.mutate(
            runtime,
            4,
            "wait-user",
            "--gate-id",
            "planning/scope",
            "--reason-code",
            "decision.material_product",
        )
        self.assertEqual(object_at(waited, "control")["kind"], "waiting_user")

    def test_blanket_authorization_persists_and_releases_ceremony_wait(self) -> None:
        runtime, _ = self.init_runtime("authorization-change")
        self.mutate(runtime, 1, "enter-stage", "--stage", "planning")
        self.mutate(
            runtime,
            2,
            "request-gate",
            "--stage",
            "planning",
            "--gate",
            "design-ready",
            "--reason",
            "design complete",
            "--kind",
            "ceremony",
            "--reason-code",
            "artifact.ready",
        )
        self.mutate(
            runtime,
            3,
            "wait-user",
            "--gate-id",
            "planning/design-ready",
            "--reason-code",
            "approval.requested",
        )
        state = self.mutate(
            runtime,
            4,
            "change-authorization",
            "--authorization",
            "yolo",
            "--source",
            "user",
            "--reason",
            "approved on all remaining in-scope work",
        )
        self.assertEqual(object_at(state, "charter")["authorization"], "yolo")
        self.assertEqual(object_at(state, "control")["kind"], "ready")
        gate = object_at(state, "workflow", "stages", "planning", "gates", "design-ready")
        self.assertEqual(gate["status"], "approved")
        self.assertEqual(gate["decision_source"], "policy")

    def test_checkpoints_auto_decides_ceremony_but_not_scope_lock(self) -> None:
        runtime = self.base / "checkpoint-gates"
        state = self.expect_ok(
            "init",
            "--runtime-dir",
            str(runtime),
            "--change",
            "checkpoint-gates",
            "--workflow",
            "sk-team",
            "--policy-revision",
            "test-policy",
            "--authorization",
            "checkpoints",
        )
        assert state is not None
        self.mutate(runtime, 1, "enter-stage", "--stage", "discovery")
        state = self.mutate(
            runtime,
            2,
            "request-gate",
            "--stage",
            "discovery",
            "--gate",
            "artifact-ready",
            "--reason",
            "proposal ready",
            "--kind",
            "ceremony",
            "--reason-code",
            "phase.complete",
        )
        ceremony = object_at(state, "workflow", "stages", "discovery", "gates", "artifact-ready")
        self.assertEqual(ceremony["status"], "approved")
        self.assertEqual(ceremony["decided_by"], "policy:checkpoints")

        state = self.mutate(
            runtime,
            3,
            "request-gate",
            "--stage",
            "discovery",
            "--gate",
            "scope-lock",
            "--reason",
            "scope requires user authority",
            "--kind",
            "authority_decision",
            "--reason-code",
            "decision.material_scope",
        )
        scope = object_at(state, "workflow", "stages", "discovery", "gates", "scope-lock")
        self.assertEqual(scope["status"], "pending")

    def test_route_escalation_typed_stop_and_terminal_receipt(self) -> None:
        runtime = self.base / "terminal"
        state = self.expect_ok(
            "init",
            "--runtime-dir",
            str(runtime),
            "--change",
            "terminal",
            "--workflow",
            "sk-team",
            "--policy-revision",
            "test-policy",
            "--route",
            "micro",
            "--destination",
            "merge",
            "--destination-target",
            "main",
        )
        assert state is not None
        state = self.mutate(
            runtime,
            1,
            "escalate-route",
            "--route",
            "quick",
            "--assurance",
            "elevated",
            "--reason",
            "trust boundary discovered",
        )
        self.assertEqual(object_at(state, "charter")["route"], "quick")
        self.assertEqual(object_at(state, "charter")["assurance"], "elevated")
        self.assertEqual(
            object_at(state, "charter", "budgets"),
            {"attempts": 6, "review_rounds": 3, "remediations": 2},
        )
        self.mutate(runtime, 2, "enter-stage", "--stage", "acceptance")
        self.mutate(runtime, 3, "complete-stage", "--stage", "acceptance", "--outcome", "succeeded")
        errors = self.invoke_error(
            runtime, 4, "early-complete", "complete", "--outcome", "completed"
        )
        self.assertIn("terminal action", errors)

        state = self.mutate(
            runtime,
            4,
            "record-terminal",
            "--kind",
            "merge",
            "--target",
            "main",
            "--outcome",
            "succeeded",
            "--evidence",
            "merge commit abc123",
        )
        self.assertEqual(object_at(state, "delivery")["status"], "succeeded")
        state = self.mutate(runtime, 5, "complete", "--outcome", "completed")
        self.assertEqual(object_at(state, "control")["outcome"], "completed")

    def test_auto_workspace_can_be_resolved_only_once(self) -> None:
        runtime = self.base / "workspace-once"
        state = self.expect_ok(
            "init",
            "--runtime-dir",
            str(runtime),
            "--change",
            "workspace-once",
            "--workflow",
            "sk-team",
            "--policy-revision",
            "test-policy",
            "--workspace",
            "auto",
        )
        assert state is not None
        self.mutate(runtime, 1, "resolve-workspace", "--resolved", "current")
        errors = self.invoke_error(
            runtime,
            2,
            "resolve-workspace-again",
            "resolve-workspace",
            "--resolved",
            "worktree",
        )
        self.assertIn("already been resolved", errors)

    def test_blocker_uses_stable_stop_reason(self) -> None:
        runtime, _ = self.init_runtime("typed-stop")
        self.mutate(runtime, 1, "enter-stage", "--stage", "implementation")
        state = self.mutate(
            runtime,
            2,
            "block",
            "--blocker-id",
            "production-access",
            "--reason-code",
            "boundary.external_access",
            "--reason",
            "provider approval is required",
            "--required-action",
            "approve provider access",
        )
        blocker = object_at(state, "blockers", "production-access")
        self.assertEqual(blocker["reason_code"], "boundary.external_access")

    def test_policy_cannot_expand_authorization_or_destination(self) -> None:
        runtime = self.base / "authority-boundary"
        state = self.expect_ok(
            "init",
            "--runtime-dir",
            str(runtime),
            "--change",
            "authority-boundary",
            "--workflow",
            "sk-team",
            "--policy-revision",
            "test-policy",
            "--authorization",
            "manual",
        )
        assert state is not None
        errors = self.invoke_error(
            runtime,
            1,
            "policy-yolo",
            "change-authorization",
            "--authorization",
            "yolo",
            "--source",
            "policy",
        )
        self.assertIn("only the user may increase", errors)
        errors = self.invoke_error(
            runtime,
            1,
            "policy-destination",
            "change-destination",
            "--kind",
            "merge",
            "--target",
            "main",
            "--source",
            "policy",
        )
        self.assertIn("only the user may change", errors)

    def test_policy_cannot_decide_material_authority_gate(self) -> None:
        runtime = self.base / "policy-gate"
        state = self.expect_ok(
            "init",
            "--runtime-dir",
            str(runtime),
            "--change",
            "policy-gate",
            "--workflow",
            "sk-team",
            "--policy-revision",
            "test-policy",
            "--authorization",
            "yolo",
        )
        assert state is not None
        self.mutate(runtime, 1, "enter-stage", "--stage", "planning")
        self.mutate(
            runtime,
            2,
            "request-gate",
            "--stage",
            "planning",
            "--gate",
            "scope",
            "--reason",
            "material scope choice",
            "--kind",
            "authority_decision",
            "--reason-code",
            "decision.material_scope",
        )
        errors = self.invoke_error(
            runtime,
            3,
            "policy-scope",
            "decide-gate",
            "--stage",
            "planning",
            "--gate",
            "scope",
            "--decision",
            "approved",
            "--decided-by",
            "policy:test",
            "--decision-source",
            "policy",
        )
        self.assertIn("ceremony gates only", errors)
