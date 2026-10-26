# Workspace lifecycle

Read during workspace setup and before finish in every route. The root owns this
lifecycle, including when a PR is merged in a later session. A successful merge
must be followed by cleanup reconciliation before reporting the workflow complete.

## Ownership and authority

Record the canonical repository, task worktree/branch, selected merge target(s),
and temporary paths/processes created by this run in `<runtime-dir>/workspace.md`.
Distinguish run-created resources from pre-existing or shared ones. Keep previews,
scratch files, render output, and tool logs under the run's Git-local runtime root
or an explicitly recorded temporary directory; do not scatter them in the project
root. Keep required decisions/reports in OpenSpec and version them before delivery.

The selected Merge finish includes normal removal of this run's disposable
worktree and temporary outputs once the checks below pass. State that in the start
receipt; do not ask again at finish. Deploy includes this cleanup only if its
authorized delivery also includes a verified merge. A user instruction to retain
the workspace takes precedence. Cleanup never expands merge/deploy authority.

| Delivery state | Workspace disposition |
|---|---|
| Local, Commit, open PR, failed/unverified merge | Retain the worktree and branch; identify the next step. |
| Verified merge to every selected target | Remove eligible run-owned resources after preservation. |
| Deploy without a verified merge | Retain the source worktree; release eligible temporary processes/output. |
| Dirty, active, locked, shared, or ownership uncertain | Retain the affected resource with a concrete reason. |

Merge to `dev` is sufficient when `dev` is the selected destination; later promotion
of `dev` to `main` does not require keeping the feature worktree. If the user
requested both targets, finish both before cleanup. Do not infer success from a
branch name, PR closure, or the mere existence of `dev`/`main`.

## Verify before removal

For each repository independently:

1. Read `git worktree list --porcelain` and compare exact paths, branch, and HEAD
   with the ownership record. Never remove the primary checkout, a worktree shared
   with another task, a locked worktree, or a workspace used by active agents,
   servers, deployment, or another session. Finish/join this run's agents and stop
   only its recorded temporary processes; an unresolved owner means retain.
2. Verify the current task HEAD reached the selected target. For ordinary merges,
   require `git merge-base --is-ancestor <task-head> <target-head>` to succeed. For
   a remote target, refresh that exact ref and record its SHA; a stale tracking
   ref is insufficient. For squash/rebase, require provider evidence binding the
   merged PR's exact head to the selected repository/base and resulting commit(s)
   reachable from that target. New commits after the merged head, unavailable
   proof, or ambiguous patch equivalence mean retain.
3. Inspect staged, unstaged, untracked, and ignored content, including submodules:
   `git -C <worktree> status --porcelain=v1 --untracked-files=all --ignored=matching`.
   Inspect ignored directories as needed; a clean ordinary status is insufficient
   because Git may delete ignored files during worktree removal. Only disposable
   output proven created by this run may be removed automatically. Preserve user
   edits, local configuration/secrets, dumps, and unknown files; do not expose their
   contents in the receipt. If preservation/ownership cannot be proved, retain.
4. Confirm required OpenSpec decisions, review/acceptance reports, deferred-item
   dispositions, and delivery evidence exist outside the doomed worktree. Include
   versioned reports in the reviewed delivery before merging. Preserve any remaining
   local-only evidence using the archive below; never create an unreviewed source
   commit merely to make cleanup pass.

## Preserve, remove, and report

`git worktree remove` can also delete its administrative directory, including
`git rev-parse --git-path sk-workflow`. Preserve evidence **before** invoking it:

1. Resolve `git rev-parse --git-common-dir` to an absolute path. Use a unique
   `<common-dir>/sk-workflow-archive/<change>/<run-id>/` outside every worktree being
   removed. Never overwrite an existing archive. With all writers stopped and any
   review lease released, copy the run's journal, projection, and required evidence
   there; verify file hashes and helper `status`/`validate`. Preserve externally
   located evidence too. If other runs use the same worktree/admin directory, retain
   the worktree unless their owners have independently completed preservation.
2. Record old-to-archive paths and hashes in the archive's `workspace.md`. Preserve
   historical journal entries byte-for-byte. Continue subsequent helper writes only
   with this archived `--runtime-dir`; register relocated current artifacts through
   the helper, never by hand-editing state. Record the active archive location in
   both workspace records so an interrupted cleanup resumes with one writer even
   if the source directory still exists. If preservation or validation fails, keep
   the original workspace and report cleanup as blocked.
3. Change the orchestrator's working directory to a surviving checkout. Recheck
   HEAD, status, locks, and ownership immediately before removal. Invoke
   `git -C <surviving-checkout> worktree remove <exact-task-worktree>` without force.
   Never use `rm -rf`, `git clean`, `reset --hard`, or blanket glob deletion to
   bypass a refusal. If Git refuses (including submodule cases), retain and report
   the reason; do not escalate to force as routine cleanup.
4. Delete a run-created local topic branch only after the worktree is removed,
   merge proof is recorded, no other worktree uses it, and `git branch -d` accepts
   it. Never delete the primary/default, target, shared, or remote branch as part
   of this rule. If `-d` refuses, including after squash/rebase, retain the branch
   and its commits with the reason; do not substitute `-D`.
5. Release only recorded disposable temporary output after preserving referenced
   evidence. Do not purge OpenSpec archives, journals, final evidence, repository
   caches/environments, or unrelated previews based on age or directory name.
   Normal worktree removal unregisters it; `git worktree prune` is not directory
   cleanup and must not be used as a repository-wide substitute.
6. Re-read the worktree registry and verify filesystem results. Write `CLEANUP.md`
   in the surviving runtime directory with each repository/path/branch, merge
   evidence, `removed | retained | blocked | not_applicable`, reason, and surviving
   artifact paths. Register it via the existing `record-artifact` helper and include
   it in the final delivery summary before completing runtime state. A merge can
   succeed while cleanup is blocked: report both, never claim everything was
   removed. Retained resources need an explicit reason and next action.

On interruption/resume, reconcile registry, filesystem, archive hashes, and merge
evidence before retrying. An absent path alone is not proof of successful cleanup;
never repeat merge/deploy just to retry cleanup. If a PR-only run was completed
earlier, keep its journal intact and record a separate cleanup receipt on the
authorized merge follow-up.

For accumulated legacy worktrees, first inventory every owning repository and
present exact candidates with merge/dirty/ignored/active checks. A request to fix
the workflow is not blanket permission to delete pre-existing workspaces. When
legacy cleanup is requested, apply the same preservation and removal checks; never
classify `.env`, dumps, `.venv`, or unknown directories as trash by their names.
