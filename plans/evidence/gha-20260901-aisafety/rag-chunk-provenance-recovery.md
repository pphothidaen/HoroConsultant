# GHA-20260901-AIS-011-RECOVERY — RAG Chunk Provenance

**Status:** `BLOCKED`  
**Scope:** read-only recovery; this receipt owns only this file.  
**Observed:** 2026-09-01T03:27:53Z  
**Decision:** The failure node and its commit-addressed chunker/corpus inputs are recovered. The run's generated-vector baseline is not recoverable from the commit, Actions artifacts, or job log, so `AIS-011` cannot move to `DONE`.

## Immutable run binding

| Field | Recovered evidence |
| --- | --- |
| Run | [AI Safety Audit 33418206430](https://github.com/pphothidaen/HoroConsultant/actions/runs/33418206430), `completed` / `failure` |
| Run head | `f9f80487a5f01a176ce7c16d3f1657e2c8908e16` (`f9f8048`) |
| Job | `99573861466`, `Pre-Deployment Code Review and Safety Audit` |
| Failing step | `Execute code reviewer and safety audit` (step 5) |
| CI command | `python3 project/core/code_reviewer.py --review --use-python` |
| Test command inside reviewed commit | `python -m pytest -q --ignore=project/kaggle_kernel` |
| Suite result | `9 failed, 3791 passed, 45 skipped, 12 warnings in 280.11s` |
| Actions artifacts | `0` reported by `GET /repos/pphothidaen/HoroConsultant/actions/runs/33418206430/artifacts` |

The GitHub-hosted failed-job log is currently readable through `gh run view 33418206430 --repo pphothidaen/HoroConsultant --log-failed`. Direct job-log download remains unavailable to this identity (`GET .../actions/jobs/99573861466/logs` returns HTTP 403, "Must have admin rights to Repository"), but this does not prevent recovery of the relevant output.

## Exact recovered failure

```text
FAILED project/tests/test_meta_plan_003_baseline.py::TestVectorStoreAndRAGBaseline::test_chunk_text_functionality - assert 0 >= 3
 +  where 0 = len([])
```

At `f9f8048`, the test's only RAG-cardinality assertion is lines 580–584 of `project/tests/test_meta_plan_003_baseline.py` (blob `47d108d55309b850a9a402252ba7c31806794791`): it uses an inline three-paragraph `QianZiWen` string, calls `_chunk_text(..., chunk_size=20)`, and requires `len(chunks) >= 3`. It does **not** load the RAG corpus, FAISS metadata, or an expected value of `3,132`.

Thus the exact frozen values are **expected `>= 3` chunks; actual `0` chunks**, and the failure is a unit chunker contract, not evidence that a CI vector index contained `61` rather than `3,132` chunks.

## Commit-addressed baseline inputs

| Input | `f9f8048` identity | Finding |
| --- | --- | --- |
| Test module | `47d108d55309b850a9a402252ba7c31806794791` | Holds the inline input and `>= 3` assertion. |
| `_chunk_text` wrapper | `project/rag/vector_store.py`, blob `bfd842f130e884503826cfc36c2c960657e6c3f6` | Lines 135–137 delegate directly to `chunk_text_fast`. |
| Chunker implementation | `project/core/fast_math.py`, blob `63f41e51e1359e6b323eec1aea106387c836fa1d` | Lines 465–519 select `_native_kernel("chunk_text")` if available, otherwise omit paragraphs shorter than 30 characters before chunking. |
| Raw corpus tree | `project/data/raw_texts`, Git tree `0aae1dfa8a677b1b311b49573e1ce855e991c3a1` | Fifteen tracked files; deterministic listing digest (blob ID + path, SHA-256) `7493d7ae7159bad9512d96a9f3a79055ea704fe65970d6820045ccdbaac0b621`. |
| Generated vector metadata | `project/data/vector_store/metadata.json` | Absent from `f9f8048`; `git cat-file -e` exits 128. |
| Generated FAISS index | `project/data/vector_store/index.faiss` | Absent from `f9f8048`; `git cat-file -e` exits 128. |

`.gitignore` line 10 excludes the entire `project/data/vector_store/` directory. The run produced no Actions artifact. Therefore neither the index binary nor its metadata, creation command, embedding/runtime version, or exact count can be bound to the audited run. A current local index, even if it reports a count, is not evidence of the CI-run index.

## Sufficiency decision

The retrieved log and Git objects are immutable enough to complete **node-level failure provenance**. They are insufficient for the ticket's requested **frozen corpus/chunker/index baseline** because the index and metadata used (if any) by CI were untracked and unarchived. No exact-path correction reservation is authorized, and `GHA-20260901-AIS-020` remains blocked.

## Safe operator retrieval step

An authorized repository administrator may locate an archival snapshot that predates or is contemporaneous with the run's checkout and preserve, without rebuilding, all of the following as an immutable artifact: `project/data/vector_store/metadata.json`, `project/data/vector_store/index.faiss`, the full corpus file inventory with content hashes, the chunker configuration/runtime identity (including native-kernel availability), and the generation command/log. The operator should record SHA-256 hashes and a durable artifact URL/identifier, then provide that receipt for a new read-only binding review. Regenerating an index from today's tree cannot establish the index used by run `33418206430`.

## Read-only commands and results

```text
gh run view 33418206430 --repo pphothidaen/HoroConsultant --json ...
# completed/failure; headSha=f9f80487a5f01a176ce7c16d3f1657e2c8908e16; job=99573861466

gh run view 33418206430 --repo pphothidaen/HoroConsultant --log-failed
# recovered the exact node and `assert 0 >= 3` output above

git cat-file -e f9f8048:project/data/vector_store/metadata.json
git cat-file -e f9f8048:project/data/vector_store/index.faiss
# both exit 128: absent from the committed run tree

gh api repos/pphothidaen/HoroConsultant/actions/runs/33418206430/artifacts --jq '.total_count'
# 0
```
