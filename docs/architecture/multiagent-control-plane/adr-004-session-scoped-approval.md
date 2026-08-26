# ADR-004 — Session-scoped Parent and Derived Child Grants

**Status:** Owner-approved for the current root session only.

## Current facts

Rule 17 makes the root session orchestrator-only and requires bounded ownership,
evidence and external-mutation gates
([Rule 17](../../../.agents/rules/17-multi-account-agent-orchestration.md)).
Static route/config labels do not prove authority or execution.

## Parent Grant decision

`OD-SESSION-002` authorizes only frozen `MAREF-000..055` in-workspace
mutations in this root session through derived child grants. It is not a
wildcard runtime token and does not grant root direct implementation.

Each derived child grant must bind: canonical authenticated root-session ID,
parent-grant ID, ticket ID, action class, exact file/module ownership, normalized
scope digest, actor/role, issue/expiry times, maximum uses, current use counter,
attempt policy and revocation/supersession state. Server identity supplies
issuer/reviewer; request payloads cannot self-assert them.

## Native fallback Parent Waiver

`NW-SESSION-001` records the user's current-root-session approval: `อนุมัติ
native single-use waiver สำหรับ MAREF-010 และที่เกี่ยวข้องหรือคล้ายกันทั้งหมดนี้
ตลอด session`. It covers `MAREF-010..055` in-workspace native-collaboration
fallback only when governed alias execution is unavailable because of the same
objective/scope-binding/receipt limitation. It is not an implementation grant.
Its `approval_recorded_at` is `2026-08-26T12:11:01+07:00`; the canonical
session binding is `current runtime-enforced collaboration root thread /root`.
No opaque provider or session identifier is inferred.

Every use requires a separately derived, one-ticket child grant binding the
exact ticket, action, path/file ownership, actor/role, normalized scope digest,
`max_uses=1`, and current-root-session expiry. Dependencies, one-editor
ownership, Rule 18 classification and an independent review remain mandatory.
For that native child only, the waiver accepts that no alias/provider
ExecutionReceipt exists; it still requires a native WorkResult, scoped diff and
evidence, and reviewer `PASS` before the ticket can freeze.

The planned but unissued child `NW-SESSION-001/MAREF-010/1` is limited to
creating `docs/architecture/multiagent-control-plane/contracts/lifecycle-v1.md`
for the MAREF-010 lifecycle-contract action, with native `business_analyst`
route intent `gpt-5.6-sol/xhigh`, `max_uses=1`, current-root-session expiry and a
scope digest derived from the frozen ticket/action/path at issuance. No native
execution has occurred under this child.

## Per-ticket local commit closure

For `MAREF-010..055`, a numbered ticket whose implementation WorkResult is
`DONE` and whose independent reviewer result is `PASS` must receive a separate
post-PASS, exact per-ticket local-commit child grant. That child may commit only
the ticket's reviewed files/hunks and requires its own exact manifest and
`max_uses=1`. It cannot commit a `BLOCKED` or `NEEDS_HITL` ticket, unrelated
dirty content, or another ticket's changes. The commit action is delegated;
root remains orchestrator-only. No push is automatic or authorized.

This waiver-record mutation is support metadata rather than completion of a
numbered MAREF ticket, so it must not receive a local commit.

## Fail-closed boundary

A new root session, `/clear`, app restart or control-plane process restart
expires every grant and `NW-SESSION-001` immediately. Provider/internal
WebSocket reconnect alone does not expire a grant only when the same canonical
authenticated session is proven. Missing proof means expired. Cross-session
replay, digest mismatch, ticket/owner mismatch, over-use, expiry and
revoked/superseded grants fail.

## Explicit exclusions

Neither the grant nor `NW-SESSION-001` covers `MAREF-056/057` production or
external actions; deploy/publish/external writes; Git push or broad Git
operations; secrets or
credentials; paid or billing actions; destructive data/history/permission
changes; force/security bypass; root implementation; tests outside the child
ticket; new tickets/scopes; or any file outside the child ownership manifest.
The sole Git exception is the separately delegated, exact post-PASS local
commit above. Lease, quota, dependencies, Rule 18, security and all other gates
remain independent.
