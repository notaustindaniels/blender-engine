# Native amd64 Probe Path — Proposal (D-002 R13) — AWAITING OWNER SIGN-OFF

**Date:** 2026-07-06 · **Status:** proposal only. No infrastructure will be provisioned or built
until the owner approves by reply (R13: "never self-provision").

## Problem
This host is arm64; Blender runs as `linux/amd64` under emulation. Large add-ons **crash**
(`quarantine`) — `bagapie` (both versions), `terrain-mixer@4.5`, and it capped L2 verification at
**15 of 27** candidates. That is an instrument defect, not ecosystem signal, and it is why the L2
coverage number is not decision-grade (D-002 basis #1).

## Option A — GitHub Actions, **$0** (PREFERRED)
`ubuntu-latest` runners are **native amd64** — no emulation, no crashes — and are **free for public
repos**. Docker is preinstalled, so the existing probe images + `run_probe.sh` containment flags
(`--network none`, read-only, non-root, cap-drop) work unchanged.

- **Flow:** a workflow `.github/workflows/native-probe.yml` that, per run: builds the 3 digest+SHA-pinned
  probe images → **re-acquires** the candidate archives from their source URLs (public, hash-verified;
  the vault is git-ignored and never leaves this machine, so CI re-downloads fresh) → runs
  `verify_matrix.py` over them → uploads `manifests/*.json` as a build artifact I pull back and index.
- **Security:** the acquire step needs network (public downloads, hash-checked); the **probe containers
  keep `--network none`**. Harvested code only ever runs inside the sandbox, on GitHub's throwaway VM.
  No secrets needed (public archives; `GH_TOKEN` only for enumeration, which already ran).
- **Scope of the first run:** the FULL 27-candidate L2 matrix + the L1 emulation-suspects
  (`bagapie` ×2, `terrain-mixer@4.5`). Version-aware skipping keeps it bounded.
- **Cost:** \$0. **Teardown:** automatic (ephemeral runner).

## Option B — single cloud VM, ≤ **$25/mo**, ephemeral (FALLBACK)
A small amd64 VM (Hetzner/DO), run the pipeline once, **tear down after use**. Hard cost cap \$25/mo.
Only if Option A is blocked (e.g., repo must stay private, or GHA Docker limits bite).

## Recommendation
**Option A (GitHub Actions, \$0).** Highest information, zero cost, ephemeral, sandbox-preserving.

## What your approval unblocks
The full native L2 matrix + L1 re-probes → **decision-grade** coverage → the R16 formal re-evaluation
and the D-003 decision request. Until you approve, verification stays on the bounded emulated sample
and R16 is deferred.

## The ask
Reply with: **approve Option A**, **approve Option B**, or **hold**. I will not create the workflow,
provision anything, or run a native probe until then.
