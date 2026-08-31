# BROKER-RUNBOOK-001 — macOS Account Broker Installation, Migration, and Rollback

Status: `IMPLEMENTATION_READY / EXECUTION_NOT_AUTHORIZED`

Owner: DevOps & Release Agent

Date: 2026-08-31

Applies to: one interactive macOS login user and the four governed aliases
`codex1`, `codex2`, `agy1`, and `agy2`.

## 1. Safety boundary

This runbook specifies a future operator procedure. Authoring and reviewing it
does not authorize installation, Keychain access, wrapper changes, provider
execution, migration, deployment, or secret inspection.

The migration is successful only when all four aliases retain their current
provider session homes, each literal wrapper unlock value exists exactly once
in the user's login Keychain with an exact broker-only ACL, all active wrappers
are owner-only and contain no secret, and sanitized health/quota checks pass.
Anything missing, ambiguous, stale, or mismatched stops the procedure.

Non-negotiable rules:

- Never display, log, hash for evidence, copy to the clipboard, or manually
  inspect unlock material.
- Never place unlock material in command arguments, process environment,
  shell variables, command substitutions, temporary filenames, or provider
  output. The only permitted live paths are broker-private memory and an
  anonymous pipe or echo-disabled PTY owned by the broker.
- Never `source`, `eval`, execute, or use a shell to parse a legacy wrapper.
- Never call provider login/logout, delete or replace a provider home, or copy
  provider credential files during migration.
- Never search for a replacement account, provider, home, or Keychain item.
  An unavailable selected alias is terminal. There is no alias fallback.
- Never auto-unlock a Keychain. A locked, missing, non-login, unreadable, or
  non-writable Keychain fails closed without presenting authentication UI.
- Never restore a plaintext legacy wrapper during rollback. Recovery backups
  are evidence/recovery artifacts only and are never executable rollback
  inputs.
- Run the complete synthetic-Keychain suite with the exact installed broker
  before touching the login Keychain or live wrappers.

## 2. Requirement gate

### GRILL REPORT

- D1 Scope boundary `[CONFIRMED]`: the only deliverable is this runbook. Future
  execution covers broker build/install, synthetic validation, four-alias live
  migration, sanitized smoke checks, lifecycle behavior, and rollback. It does
  not cover provider reauthentication, deployment, secret inspection, or
  changes to provider sessions.
- D2 Requirement delta `[AUTO]`: replace literal-bearing wrappers with an exact
  alias bridge backed by login-Keychain generic-password items, while retaining
  current `CODEX_HOME`/`AGY_HOME` session directories.
- D3 Acceptance and stop conditions `[CONFIRMED]`: Sections 13 and 18 define
  measurable gates. Any failed or indeterminate gate stops before the next
  alias.
- D4 Inputs and dependencies `[CONFIRMED]`: macOS, Swift toolchain, Security and
  CryptoKit frameworks, an administrator for the immutable system install, the
  logged-in target user for migration, four owner-approved wrapper paths, and
  the existing provider binaries/homes. Secrets are not inputs to the shell.
- D5 Ownership and handoff `[CONFIRMED]`: DevOps owns this document; a future
  Swift implementer, QA operator, and target login user execute separate gated
  phases with one editor per artifact.
- D6 Assumptions `[CONFIRMED]`: the governed live registry has exactly the four
  aliases listed above; each wrapper contains exactly one supported literal;
  the current provider homes already hold sessions and must not move. A live
  mismatch invalidates these assumptions and blocks execution.
- D7 Risk and recovery `[AUTO]`: risks and non-plaintext rollback are specified
  in Sections 16–19.
- D8 Evidence strategy `[AUTO]`: evidence is metadata-only, bounded, and uses
  the schema in Section 17. Raw wrapper/provider/Keychain data is prohibited.
- D9 Domain/HITL `[NOT-APPLICABLE]`: no metaphysical logic or data changes.

Gate status: `APPROVED` for runbook authoring only. Future execution requires a
fresh operator change approval and populated manifest.

## 3. Architecture and trust model

```text
owner-only alias wrapper (no secret)
        |
        v
exact root-owned immutable broker path
        |-- validates alias + binary + environment + login Keychain state
        |-- reads one exact generic-password item under broker-only ACL
        |-- builds a clean per-alias process environment
        `-- starts one exact provider; secret uses anonymous FD/PTY only

login Keychain
  service: com.horoconsultant.account-broker.unlock.v1
  account: one of codex1 | codex2 | agy1 | agy2
  sync: disabled
  ACL: installed broker only
```

The broker is an on-demand Swift executable, not a daemon. It uses
Security.framework directly. It targets one explicitly verified login
Keychain with `kSecUseKeychain`; it never searches the user's Keychain search
list. Generic-password items use `kSecClassGenericPassword`, the fixed service,
and exact alias as their composite identity. `kSecAttrSynchronizable` and
`kSecUseDataProtectionKeychain` remain false/absent so the macOS `kSecAttrAccess`
ACL applies.

The broker must use `SecAccessCreate`/`SecTrustedApplicationCreateFromPath` to
create an access object containing only the exact installed executable. The
decrypt/data ACL must have one trusted application, no wildcard or null trusted
application list, and no migration/build helper. Lookup must set authentication
UI to fail and return a typed error rather than prompt.

The legacy `SecKeychain` and ACL APIs are deprecated but remain the macOS API
surface that supports a specified file-backed Keychain and per-item trusted-app
ACL. Their use is intentionally isolated behind a small `KeychainStore`
protocol so a future reviewed replacement can be introduced without changing
the wrapper or alias contracts.

## 4. Fixed artifact layout

Populate `BROKER_VERSION` and `BROKER_SHA256` from the reviewed release
artifact. Values below are identifiers and paths, never secrets.

```text
/Library/Application Support/HoroConsultant/AccountBroker/
  releases/<BROKER_SHA256>/hc-account-broker
  releases/<BROKER_SHA256>/hc-session-only-bridge
  manifests/<BROKER_SHA256>.json

~/Library/Application Support/HoroConsultant/AccountBroker/
  migration/<UTC_RUN_ID>/manifest.json             mode 0600
  migration/<UTC_RUN_ID>/backups/<alias>.wrapper   mode 0600
  runtime/<alias>/                                  mode 0700
    home/ xdg-config/ xdg-cache/ xdg-data/ xdg-state/ tmp/
```

System directories are `root:wheel`, mode `0755`, and not writable by the login
user. Release files are `root:wheel`, mode `0555`, carry `uchg`, and are invoked
through their exact release path. Do not use a writable `current` symlink.
Per-user migration/runtime directories are owned by the target user and mode
`0700`; manifests/backups are mode `0600` and regular non-symlink files.

The session-only bridge is independently signed and immutable. It never reads
Keychain data. It exists solely to launch an exact provider against its
existing exact session home during rollback; if that session requires unlock
material, it fails instead of prompting, switching aliases, or reading a
legacy backup.

## 5. Approved alias manifest

The operator must populate all absolute paths before execution and obtain owner
approval. No discovery, glob, shell alias resolution, or `${HOME}` expansion is
allowed inside the signed manifest. The installer canonicalizes each path,
rejects symlinks, and binds the manifest digest into the broker release record.

| Alias | Provider | Required provider-home key | Existing home (must be preserved) | Legacy wrapper | Replacement wrapper |
|---|---|---|---|---|---|
| `codex1` | `codex` | `CODEX_HOME` | approved absolute account1 path | approved absolute path | same path |
| `codex2` | `codex` | `CODEX_HOME` | approved absolute account2 path | approved absolute path | same path |
| `agy1` | `agy` | `AGY_HOME` | approved absolute account1 path | approved absolute path | same path |
| `agy2` | `agy` | `AGY_HOME` | approved absolute account2 path | approved absolute path | same path |

Each provider executable is an approved absolute regular-file path with a
recorded SHA-256 and code-signing identity where available. `PATH` lookup is
not an executable identity. The manifest contains `fallback: false` for every
alias and has no fallback field or array that can name another alias.

Stop if the live registry has fewer, more, or different aliases. In particular,
do not infer `codex3` or map an AGY alias to Codex (or vice versa).

## 6. Broker implementation contract

The reviewed Swift release must expose these shell-free subcommands. Arguments
contain only non-secret identifiers/paths.

```text
hc-account-broker verify-install --manifest <path> --json
hc-account-broker synthetic-test --manifest <path> --json
hc-account-broker preflight --manifest <path> --json
hc-account-broker migrate --alias <exact-alias> --source <exact-wrapper> \
  --backup-dir <exact-run-dir> --manifest <path> --json
hc-account-broker verify-alias --alias <exact-alias> --manifest <path> --json
hc-account-broker smoke --alias <exact-alias> \
  --check health|quota --manifest <path> --json
hc-account-broker run --alias <exact-alias> --manifest <path> -- <provider-args>
hc-account-broker rollback-wrapper --alias <exact-alias> \
  --mode session-only|disabled --manifest <path> --json
```

Required internal controls:

1. Call `setrlimit(RLIMIT_CORE, 0)` before reading a secret. Disable diagnostic
   dumps, tracing, debug descriptions, and crash-report attachment of secret
   buffers.
2. Resolve the target user with `getuid()`/`getpwuid_r()`, not environment.
   Migration must reject UID 0 and a wrapper/home not owned by that same UID.
3. Open files using directory FDs and `openat` with `O_NOFOLLOW|O_CLOEXEC`.
   Require regular files, expected owner, `st_nlink == 1`, and no group/other
   write bits. Recheck metadata after open to prevent path races.
4. Parse wrapper bytes with a bounded, non-shell parser. Accept only the
   reviewed exact assignment/quoted-literal grammar and exactly one configured
   selector for the selected alias. Reject substitutions, expansions,
   concatenation, escapes outside the grammar, multiple candidates, NULs,
   oversized files, or provider/alias text inconsistent with the manifest.
5. Keep secrets as bounded bytes, never Swift `String`. Copy into a dedicated
   allocation, best-effort `mlock`, and `explicit_bzero` it on every success or
   error path. Avoid copy-on-write and interpolation. A transient Security
   framework `CFData` is released immediately after copying.
6. Disable Keychain interaction UI for broker operations. Verify the selected
   Keychain immediately before every add/read and handle lock races from the
   actual `SecItemAdd`/`SecItemCopyMatching` result.
7. Query with the exact Keychain, class, service, and account. A metadata query
   with match-all must return exactly one item before value retrieval. Missing,
   duplicate, wrong-class, wrong-service, or wrong-account is terminal.
8. Retrieve the secret only after all alias, executable, home, Keychain, item,
   and ACL gates pass. Never cache it across invocations.
9. Launch with `posix_spawn`/`posix_spawnp` only after resolving an absolute
   executable; never use `system`, a shell, `eval`, or Foundation argument/env
   convenience that creates hidden copies. Close all inherited FDs except the
   terminal and intentional anonymous transport.
10. If the provider needs an interactive unlock, use a provider-specific finite
    state machine with exact prompt bytes and a short deadline. Disable PTY
    `ECHO`/`ECHONL` before writing the bytes, write once, wait for the exact
    success transition, zeroize, and restore terminal flags. Unknown prompts,
    repeated prompts, timeout, EOF, or output that resembles the secret aborts
    the child. Do not retrieve or send a secret speculatively.
11. For migration and smoke, sanitize all child output in bounded memory and
    never persist raw provider stdout or stderr. For an ordinary interactive
    `run`, stream provider output to the caller without retaining or logging it,
    while scanning bounded chunks for the injected byte sequence and aborting
    before forwarding a match. Release evidence receives only the typed fields
    in Section 17.
12. Exit nonzero on every unknown state. No retry selects another alias,
    Keychain, provider, home, prompt adapter, or credential item.

Stable failure names must include:

```text
BROKER_ALIAS_UNKNOWN             BROKER_ALIAS_FALLBACK_FORBIDDEN
BROKER_INSTALL_INTEGRITY         BROKER_MANIFEST_MISMATCH
BROKER_LOGIN_KEYCHAIN_MISSING    BROKER_LOGIN_KEYCHAIN_LOCKED
BROKER_LOGIN_KEYCHAIN_MISMATCH   BROKER_KEYCHAIN_UI_REQUIRED
BROKER_ITEM_MISSING              BROKER_ITEM_CARDINALITY
BROKER_ITEM_ACL_MISMATCH         BROKER_WRAPPER_UNSAFE
BROKER_WRAPPER_PARSE_AMBIGUOUS   BROKER_BACKUP_FAILED
BROKER_ENV_ISOLATION_FAILED      BROKER_PROVIDER_IDENTITY_MISMATCH
BROKER_UNLOCK_PROTOCOL_MISMATCH  BROKER_HEALTH_UNKNOWN
BROKER_QUOTA_UNKNOWN
```

## 7. Process environment isolation

The broker starts from an empty child environment and adds only this allowlist:

| Key | Value |
|---|---|
| `HOME` | per-alias `runtime/<alias>/home`, mode `0700` |
| `CODEX_HOME` | exact existing home for `codex1`/`codex2` only |
| `AGY_HOME` | exact existing home for `agy1`/`agy2` only |
| `XDG_CONFIG_HOME` | per-alias `xdg-config`, mode `0700` |
| `XDG_CACHE_HOME` | per-alias `xdg-cache`, mode `0700` |
| `XDG_DATA_HOME` | per-alias `xdg-data`, mode `0700` |
| `XDG_STATE_HOME` | per-alias `xdg-state`, mode `0700` |
| `TMPDIR` | fresh per-invocation directory below alias `tmp`, mode `0700` |
| `PATH` | fixed system/approved package-manager directories only |
| `USER`, `LOGNAME` | name returned for the real UID |
| `SHELL` | fixed approved shell path; no startup file is evaluated |
| `LANG`, `LC_CTYPE`, `TERM`, `NO_COLOR` | fixed non-secret compatibility values |

For Codex aliases, `AGY_HOME` is absent. For AGY aliases, `CODEX_HOME` is
absent. All inherited variables are absent, including provider tokens,
`DYLD_*`, `LD_*`, `BASH_ENV`, `ENV`, `ZDOTDIR`, `PYTHONPATH`, `NODE_OPTIONS`,
`SSLKEYLOGFILE`, proxy variables, cloud credentials, and caller-supplied
`HOME`/XDG/TMP values. A required proxy or certificate path needs a separate
reviewed non-secret allowlist change; the broker must not inherit it ad hoc.

The per-invocation temp directory is opened by FD, recursively cleaned without
following symlinks after the child exits, and left quarantined mode `0700` if
safe cleanup cannot be proven. Cleanup failure is reported without exposing a
path containing the username.

## 8. Build and immutable installation

This phase touches no wrappers, provider homes, Keychain items, or providers.

1. Build the reviewed Swift package in release mode for the host architecture
   (or a reviewed universal binary). Link only Apple system libraries,
   Security.framework, and CryptoKit. Reject writable/non-system load paths.
2. Prefer a stable local code-signing identity created through Keychain Access
   UI and restricted to this host. An ad-hoc signature is acceptable only for
   a one-host, one-release installation; upgrades then require new ACL entries
   and full synthetic/live verification. Never use an unsigned binary.
3. Sign the broker and the independently built session-only bridge before
   installation. Record identifier, designated requirement, architecture,
   artifact SHA-256, and build source revision; record no signer private data.
4. As administrator, create the exact SHA-256 release directory, copy through
   a root-owned staging file, `fsync`, atomically rename, set `root:wheel` and
   mode `0555`, then set `uchg`. Do not install setuid/setgid bits.
5. Verify signature strictly, recompute SHA-256 from the installed file, verify
   root ownership/mode/flags, reject symlinks and extra writable ancestors, and
   compare the embedded manifest digest. The wrapper will later name this
   exact path, not a symlink or `PATH` command.
6. Run `verify-install`. Expected sanitized result is one `[OK]` record with
   `signature_valid=true`, `hash_match=true`, `immutable=true`, and
   `manifest_match=true`. Any other result stops before synthetic testing.

For an update, install a new version alongside the old one. Never overwrite an
ACL-trusted executable in place. Test the new exact path synthetically, add and
verify that exact trusted application on live items, atomically update wrappers,
then remove the prior ACL entry only after smoke gates pass.

## 9. Synthetic-Keychain release gate

Run as the target login user, never with `sudo`. `synthetic-test` creates a
fresh mode-`0600` Keychain file below a mode-`0700` temporary directory using a
random in-memory synthetic password. It uses `SecKeychainCreate` and
`kSecUseKeychain` directly, never adds the file to the user's search list,
never changes the default Keychain, and destroys its own synthetic secrets and
temporary files on completion. It must not open the login Keychain.

The exact installed broker and bridge must pass all tests:

| ID | Test | Required result |
|---|---|---|
| S01 | Missing synthetic Keychain | `BROKER_LOGIN_KEYCHAIN_MISSING`; no search/fallback |
| S02 | Locked synthetic Keychain | `BROKER_LOGIN_KEYCHAIN_LOCKED`; no UI and no child |
| S03 | Missing item | `BROKER_ITEM_MISSING`; no child |
| S04 | Exact add/read | one item, byte-for-byte internal match, no value output |
| S05 | Duplicate/cardinality fault | `BROKER_ITEM_CARDINALITY`; no arbitrary selection |
| S06 | ACL-positive | exact installed broker reads without prompt |
| S07 | ACL-negative | differently signed helper cannot read and cannot prompt |
| S08 | Broker replacement/tamper | signature/hash/inode change blocks before read |
| S09 | Wrapper parser valid fixture | exactly one synthetic literal migrates |
| S10 | Parser attacks | symlink, hardlink, unsafe mode, expansion, substitution, duplicate literal, oversized and malformed inputs all fail |
| S11 | Backup atomicity | byte-equal synthetic backup; regular file, owner-only, mode `0600`; interrupted copy leaves no accepted backup |
| S12 | Wrapper replacement | owner-only mode `0500`; fixed broker path; no fixture bytes or secret variable names |
| S13 | argv/env/process scan | synthetic marker absent from broker/provider argv, environment, status output, logs, and crash artifacts |
| S14 | FD/PTY transport | one write, echo disabled, exact prompt state; timeout/repeat/unknown prompt fails |
| S15 | Environment | exact allowlist and alias-specific home; opposite provider home absent; fresh mode-`0700` TMP |
| S16 | No fallback | each selected alias fails locally when its own item/home/provider is absent; no other alias is touched |
| S17 | Sleep/lock simulation | post-lock invocation fails; post-unlock invocation re-reads and succeeds; no cache survives |
| S18 | Rollback | session-only and disabled wrappers contain no secret and never read the backup |

The suite emits only test IDs and pass/fail/error names. It must include a
machine-readable `synthetic_gate_pass=true` only when all 18 are green. Retain
the exact installed binary hash and test report digest. Delete the synthetic
Keychain only after report finalization; deletion failure quarantines the
mode-`0700` directory and blocks live migration pending review.

## 10. Live preflight and change freeze

Obtain an explicit migration window approval. Run preflight as the logged-in
target user in an unlocked Aqua session. Do not use SSH, a headless context,
`sudo`, or a LaunchDaemon.

1. Confirm the exact four-alias manifest and wrapper paths with the owner.
2. Confirm no wrapper replacement is concurrently in progress. Existing
   provider processes may continue; do not terminate them. The broker uses a
   mode-`0600` advisory migration lock in the mode-`0700` run directory.
3. Metadata-check each provider home without opening credential files: exact
   path, directory type, owner, mode, and device/inode. Record only alias and
   pass/fail. Do not copy, rename, chmod, or scan contents.
4. Metadata-check each legacy wrapper without displaying content. Require a
   regular file owned by the user, `st_nlink == 1`, no symlink, and no
   group/other access. The broker's redacted parser reports only
   `eligible=true|false`; it emits no matching line, byte count, secret length,
   digest, or source excerpt.
5. Resolve and pin the login Keychain once. Require the user's default
   file-backed Keychain to be the owner-approved login Keychain and verify
   unlocked/readable/writable status using `SecKeychainGetStatus`. Store its
   canonical non-secret identity in the run manifest. Never open another
   Keychain if this one is absent or locked.
6. Require no pre-existing item for the fixed service and any of the four
   aliases. `errSecDuplicateItem` or any nonzero count is a collision and stops
   for owner review; migration never overwrites or rotates an existing item.
7. Recheck installed broker/bridge signature, hash, immutable flag, owner,
   mode, manifest digest, and the fresh synthetic test report.

Preflight output must be exactly one sanitized result per gate. All gates must
be `PASS`. Unlocking the login Keychain, if needed, is a deliberate user action
in Keychain Access or the normal login UI outside this procedure; the broker
does not request, accept, or retain a Keychain password.

## 11. Recoverable wrapper backup

Back up all four wrappers before inserting the first Keychain item. The broker
performs this operation internally; do not use commands that print files or
store their contents in shell variables.

For each wrapper, the broker:

1. opens the source safely and repeats owner/type/link/mode checks;
2. creates a new temporary destination with `O_CREAT|O_EXCL`, mode `0600`, and
   the target user's UID;
3. copies bytes without parsing or logging, flushes data and directory metadata,
   atomically renames to `<alias>.wrapper`, and reopens to verify byte equality
   internally;
4. stores integrity metadata inside the mode-`0600` run manifest but does not
   emit source/backup hashes, sizes, excerpts, or paths to ordinary logs; and
5. marks `backup_complete=true` only after all four backups are durable.

The backup directory remains mode `0700`; each backup is mode `0600`, has one
link, and is non-executable. The backups still contain sensitive legacy data.
Keep them only for the owner-approved recovery window on a FileVault-protected
volume. Never sync them to cloud storage, source control, Time Machine without
an approved encrypted policy, logs, tickets, or release evidence. Their later
secure disposition is a separate owner-approved action; SSD deletion must not
be represented as guaranteed physical erasure.

If any backup fails, remove only incomplete temporary destinations, leave every
live wrapper untouched, write a sanitized failure, and stop before Keychain
mutation.

## 12. Atomic live migration

Migrate serially in this fixed order: `codex1`, `codex2`, `agy1`, `agy2`.
Parallel live migration is prohibited. Complete all gates for one alias before
starting the next.

For alias A:

1. Acquire the run lock and validate run ID, manifest digest, installed binary,
   durable four-wrapper backup gate, provider home metadata, and unchanged
   source wrapper metadata.
2. Revalidate the exact login Keychain and unlocked/readable/writable bits with
   UI disabled. Any race to locked/missing stops before reading the wrapper.
3. Parse exactly one literal from A's wrapper into protected bytes. Do not
   evaluate the wrapper or retain its non-secret commands as migration logic.
4. Construct a `SecAccess` object whose only trusted application is the exact
   immutable installed broker. Add one non-synchronizing generic-password item
   to the exact Keychain with the fixed service and account A. The migration
   helper has no separate identity: migration runs inside that same installed
   broker so no second application needs Keychain access.
5. Query metadata with match-all and require cardinality one. Copy item access,
   enumerate the decrypt/data ACL, and require exactly the installed broker's
   designated requirement/path. Reject null/wildcard trust, unexpected apps,
   and interaction-required behavior.
6. Retrieve once through the normal broker path with authentication UI set to
   fail. Compare the returned bytes to parsed bytes in constant time inside the
   process. Emit only `round_trip_match=true`; zeroize both buffers.
7. Render A's replacement wrapper from a compiled constant template. It must
   contain only an exact immutable broker path, exact alias, exact manifest
   path, `--`, and forwarded user arguments. It must not contain the provider
   home, a secret variable, fallback logic, Keychain commands, shell aliases,
   or a provider command.
8. Write a sibling temporary wrapper mode `0500`, owner target UID, `fsync`,
   validate its fixed bytes and metadata, then atomically rename over the live
   path and `fsync` the parent directory. Do not modify the recovery backup.
9. Invoke `verify-alias` through the replacement wrapper's exact route. Require
   item cardinality, ACL, environment, provider identity, and wrapper integrity
   green. Do not start a quota-consuming prompt.
10. Run sanitized health then quota smoke as defined in Section 13. On success,
    seal A. On failure, execute Section 16 for A and stop; do not begin the next
    alias.

The broker must use create-only Keychain semantics. An existing item is never
updated in place. If wrapper replacement fails after item creation, replace the
live wrapper with the session-only or disabled rollback wrapper; retain the new
item for reviewed recovery and stop. Do not restore the plaintext wrapper.

## 13. Sanitized health and quota smoke

Smoke uses the replacement wrapper, exact alias, exact provider executable,
and existing exact provider home. It cannot send a model prompt, alter login
state, refresh by logging in, or select a fallback account.

`health` may perform only a documented local/version/session-status operation.
It captures raw output in bounded private memory, maps it to the following
closed result, zeroizes/discards raw bytes, and emits no provider text:

```json
{"alias":"codex1","provider":"codex","check":"health","status":"HEALTHY"}
```

Allowed status values are `HEALTHY`, `UNHEALTHY`, and `UNKNOWN`. HTTP 200,
process exit 0, or item readability alone is not sufficient if session health
cannot be determined. `UNKNOWN` fails closed.

`quota` may use only a provider-documented non-consuming account/quota status
operation. It emits a coarse band, never raw numbers, reset timestamps, email,
account identifiers, headers, cookies, tokens, or provider prose:

```json
{"alias":"codex1","provider":"codex","check":"quota","status":"HEALTHY"}
```

Allowed status values are `HEALTHY`, `CONSTRAINED`, `EXHAUSTED`, and `UNKNOWN`.
`UNKNOWN` or `EXHAUSTED` blocks executable dispatch for that alias but does not
trigger another alias. If a provider has no safe, documented, non-consuming
quota operation, report `BROKER_QUOTA_UNKNOWN` and stop for owner review; do not
probe by sending work.

Health/quota adapter versions and parser fixture digests are bound to the
release manifest. Unexpected output shape, extra records, truncation, timeout,
or parser drift is `UNKNOWN`, not success.

## 14. Wrapper contract

Each installed wrapper is a regular file owned by the login user, mode `0500`,
with one hard link. A POSIX shell wrapper may be used only if its entire content
is the reviewed fixed template below; a tiny compiled launcher is preferred.

```sh
#!/bin/sh
set -eu
umask 077
exec '/Library/Application Support/HoroConsultant/AccountBroker/releases/<BROKER_SHA256>/hc-account-broker' \
  run --alias '<EXACT_ALIAS>' \
  --manifest '/Library/Application Support/HoroConsultant/AccountBroker/manifests/<BROKER_SHA256>.json' \
  -- "$@"
```

`<BROKER_SHA256>` and `<EXACT_ALIAS>` are installer substitutions validated
against the signed manifest. No other substitutions are permitted. The broker,
not the wrapper, discards the inherited environment and supplies the exact
provider home. The wrapper contains no fallback, provider path, home path,
unlock value, `security` invocation, `expect`, `eval`, or shell alias.

## 15. Sleep, logout, and reboot behavior

- Normal invocation: the broker reads the item for one process, injects it only
  if the exact provider prompt requires it, zeroizes memory, and exits with the
  provider. There is no secret cache.
- Display sleep/system sleep: do not assume sleep locks or preserves the login
  Keychain. Every post-wake invocation rechecks actual Keychain state. If
  locked, it returns `BROKER_LOGIN_KEYCHAIN_LOCKED` without UI or provider
  start. A process already running is not silently reauthenticated.
- Fast user switching: the broker requires the target UID's active Aqua
  session and exact login Keychain. It never uses another logged-in user's
  Keychain or process.
- Logout: no broker process or secret cache survives. Provider processes in the
  user session are allowed to terminate normally; the runbook does not preserve
  processes across logout. Provider session files remain untouched.
- Reboot: nothing auto-unlocks. After login, the login Keychain must be
  unlocked by normal user authentication before broker use. Missing or locked
  state remains fail-closed.
- Keychain auto-lock: honor it. Do not alter Keychain lock-on-sleep or timeout
  settings as part of this ticket.

### Optional LaunchAgent

Default: disabled and unnecessary. The immediate wrapper-to-broker path is the
supported production path.

If later approved, a per-user LaunchAgent may run a one-shot, metadata-only
`verify-install` at Aqua login. It must use `RunAtLoad=true`, `KeepAlive=false`,
no network, no provider execution, no Keychain value retrieval, no socket, no
credential cache, and `/dev/null` or an owner-only sanitized log. It must not
unlock the Keychain or turn a failed check into a retry loop. Use modern
ServiceManagement registration for an app-bundled agent when applicable.
A LaunchDaemon is prohibited.

Removing or disabling the optional agent must not affect wrappers, Keychain
items, provider sessions, or rollback.

## 16. Rollback without plaintext restoration

Trigger rollback for any failed live gate, item/ACL ambiguity, binary integrity
failure, environment leak, provider session regression, or owner stop request.
Rollback is per alias and then global if shared broker integrity is involved.

### Per-alias rollback

1. Stop new invocations using the mode-`0600` migration lock. Do not kill an
   already running provider unless the owner separately authorizes it.
2. If the broker is still trusted, invoke `rollback-wrapper --mode session-only`.
   It atomically installs an owner-only mode-`0500` wrapper that calls the exact
   immutable session-only bridge for the same alias/home. It never reads a
   Keychain item or backup. Existing authenticated sessions may continue; a
   request for unlock material fails closed.
3. If shared binary integrity is suspect, use the independently signed
   session-only bridge installer to install the same fixed wrapper. If its own
   integrity cannot be proven, install the reviewed disabled wrapper that emits
   only `BROKER_ROLLBACK_ACTIVE` and exits nonzero.
4. Leave the provider home untouched. Leave the new Keychain item in place by
   default so recovery remains possible. Mark it `QUARANTINED` in the run
   manifest; do not read, update, or delete it during rollback.
5. Never copy, rename, source, execute, or restore `<alias>.wrapper` from the
   recovery backup. Never reconstruct a plaintext wrapper from Keychain.
6. Emit the sanitized rollback result and stop. Resume migration only under a
   new run ID after root cause review and fresh synthetic gates.

### Global rollback

If the broker/manifest/shared ACL contract is suspect, install session-only or
disabled wrappers for all four aliases in fixed order, verify owner/mode/no
secret, and disable the optional LaunchAgent if present. Do not remove immutable
binaries or Keychain items during emergency rollback. Their reviewed removal is
a separate destructive change.

Rollback is successful when every live wrapper is a verified owner-only
session-only/disabled wrapper, no wrapper contains plaintext, no alias fallback
exists, provider homes are unchanged, and all Keychain items/backups are
quarantined but not activated.

## 17. Evidence and typed result contract

Store one mode-`0600` JSON report under the run directory. Console output is a
bounded subset. Allowed fields:

```json
{
  "schema_version": 1,
  "ticket": "BROKER-RUNBOOK-001",
  "run_id": "UTC_NON_SECRET_ID",
  "broker_sha256": "HEX",
  "manifest_sha256": "HEX",
  "signature_mode": "local|adhoc",
  "synthetic_gate_pass": true,
  "login_keychain": "UNLOCKED_VERIFIED|LOCKED|MISSING|MISMATCH",
  "aliases": {
    "codex1": {
      "backup": "PASS|FAIL",
      "item_cardinality": "ONE|ZERO|MULTIPLE|UNKNOWN",
      "acl": "EXACT|MISMATCH|UNKNOWN",
      "wrapper": "ACTIVE|SESSION_ONLY|DISABLED|UNKNOWN",
      "environment": "ISOLATED|FAILED|UNKNOWN",
      "health": "HEALTHY|UNHEALTHY|UNKNOWN",
      "quota": "HEALTHY|CONSTRAINED|EXHAUSTED|UNKNOWN",
      "result": "DONE|ROLLED_BACK|BLOCKED|NEEDS_HITL"
    }
  },
  "secret_exposure_detected": false,
  "overall": "DONE|ROLLED_BACK|BLOCKED|NEEDS_HITL"
}
```

Exactly four alias keys are required. Prohibited evidence includes secret
values or derivatives, wrapper excerpts/sizes/hashes, raw provider output,
email/account identity, Keychain persistent references, user/home paths,
environment dumps, process command lines containing user data, and crash dumps.

Command-facing log prefixes are only `[INFO]`, `[OK]`, `[WARNING]`, and
`[ERROR]`. A secret exposure signal immediately sets
`secret_exposure_detected=true`, aborts, quarantines outputs mode `0600`, and
requires human incident handling; it must not echo the detected bytes.

## 18. Acceptance and stop matrix

| Gate | Pass condition | Stop threshold |
|---|---|---|
| A. Install | exact signed hash, root-owned `0555`, `uchg`, immutable ancestors | any mismatch |
| B. Synthetic | S01–S18 all pass with exact installed broker | any fail/unknown/quarantine cleanup issue |
| C. Session preservation | four exact existing homes metadata-verified and never copied/mutated by installer | missing/moved/wrong owner or any login/logout action |
| D. Backups | four durable regular mode-`0600` owner-only backups under mode-`0700` run dir | any incomplete/unsafe backup |
| E. Login Keychain | exact owner-approved login Keychain, unlocked/readable/writable, no UI | locked/missing/mismatch/race |
| F. Items | exactly one service/account item per migrated alias, no sync | zero/multiple/collision |
| G. ACL | exact installed broker only; negative helper denied without prompt | extra/wildcard/null/unverifiable trust |
| H. Wrappers | four owner-only mode-`0500` fixed templates, no secret/fallback | unexpected bytes/mode/owner/link |
| I. Isolation | exact HOME/provider-home/XDG/TMP allowlist; opposite home absent | inherited/unknown variable or unsafe directory |
| J. Smoke | exact alias health `HEALTHY`; quota `HEALTHY` or owner-approved `CONSTRAINED` | unhealthy/unknown/exhausted or raw output |
| K. Lifecycle | locked/wake/logout/reboot behavior matches Section 15 | cache, auto-unlock, background provider start |
| L. Evidence | closed schema, exact four aliases, no prohibited data | missing/extra/stale or exposure signal |

Overall `DONE` requires A–L and all four per-alias results `DONE`. A local
success for one alias does not authorize or imply another. `CONSTRAINED` quota
needs an explicit owner decision before provider work but does not permit
fallback. `UNKNOWN` is never healthy.

## 19. Incident and recovery notes

- Unexpected disclosure: stop without repeating the value, restrict artifacts
  to mode `0600`, identify affected aliases by name only, and require owner-led
  rotation. Do not continue migration with a possibly exposed value.
- Lost/locked Keychain: leave session-only/disabled wrappers in place. The
  owner unlocks or repairs the login Keychain through normal macOS UI. Never
  use a backup wrapper as an executable workaround.
- Corrupt item or ACL: quarantine the alias, keep its session home untouched,
  and use a separately approved create-new-item rotation. Do not update an
  ambiguous item.
- Broker upgrade: side-by-side immutable release, synthetic tests, add exact new
  trusted app, wrapper cutover, smoke, then remove old ACL. Never overwrite the
  trusted binary.
- Backup expiry: deletion is a separate destructive approval. Verify wrappers,
  items, ACLs, rollback bridge, and recovery policy first. Report logical file
  deletion honestly; do not claim physical SSD erasure.

## 20. Operator checklist

```text
[ ] Fresh execution approval and named operator
[ ] Exact four-alias manifest populated and owner-approved
[ ] Exact provider homes metadata-verified; no provider login/logout
[ ] Signed broker + session-only bridge installed immutably
[ ] S01-S18 green for the exact installed hash
[ ] Login Keychain exact/unlocked/readable/writable with UI disabled
[ ] Four wrapper backups durable at 0600 under a 0700 directory
[ ] codex1 migrate -> ACL -> wrapper -> verify -> health -> quota
[ ] codex2 migrate -> ACL -> wrapper -> verify -> health -> quota
[ ] agy1 migrate -> ACL -> wrapper -> verify -> health -> quota
[ ] agy2 migrate -> ACL -> wrapper -> verify -> health -> quota
[ ] Sleep/lock negative check and post-unlock recheck
[ ] Four-alias closed evidence report reviewed for prohibited data
[ ] Optional LaunchAgent absent, or separately approved and metadata-only
[ ] Rollback wrappers and stop conditions reviewed before closure
```

## 21. Primary technical references

- Apple Security: [Keychain services](https://developer.apple.com/documentation/security/keychain-services)
- Apple Security: [`kSecClassGenericPassword`](https://developer.apple.com/documentation/security/ksecclassgenericpassword)
- Apple Security: [`kSecAttrAccess`](https://developer.apple.com/documentation/security/ksecattraccess)
- Apple Security: [Access Control Lists](https://developer.apple.com/documentation/security/access-control-lists)
- Apple Security: [`kSecUseKeychain`](https://developer.apple.com/documentation/security/ksecusekeychain)
- Apple Security: [`SecKeychainGetStatus`](https://developer.apple.com/documentation/security/seckeychaingetstatus%28_%3A_%3A%29)
- Apple Security: [Security Framework result codes](https://developer.apple.com/documentation/security/security-framework-result-codes)
- Apple: [macOS Code Signing In Depth](https://developer.apple.com/library/archive/technotes/tn2206/_index.html)
- Apple Service Management: [LaunchAgents and `SMAppService`](https://developer.apple.com/documentation/servicemanagement/)

## 22. Standard typed completion result

```text
Status: DONE | BLOCKED | NEEDS_HITL
Scope owned: plans/account_broker_installation_runbook_20260831.md only
Evidence: file path, static checks, and concise findings; no secret/live claims
Findings: implementation/migration/rollback readiness and unresolved inputs
Changed files: plans/account_broker_installation_runbook_20260831.md only
Residual risk: deprecated macOS file-Keychain ACL API; live wrapper grammar,
  paths, signing identity, provider prompt/status adapters, and current
  Keychain state require implementation and synthetic/live verification
Recommended next action: independent security review, then separately approved
  Swift implementation and S01-S18 synthetic gate; no live migration before it
```
