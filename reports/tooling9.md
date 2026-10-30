# Tooling9: release scanner and public documentation cleanup

Outcome: PASS for tooling/software checks. Actual project release review with real terms was not run. No private terms file or file under the owner's private directory was opened for this work; scanner invocations used only fake terms in disposable synthetic repositories.

Implementation commit: `a548b757ff1826188071b06955a0c9f1b5f6b092`. Baseline: `869bac89f6f2269400d04c5eb0dcee225630eb29`. The final evidence/report commit follows separately in Git history. Machine-readable checks: `results/tooling9_checks.json`.

## Built

Upgraded `scripts/release_review.py` in place. Before editing, the result freeze manifests were checked for this path; none binds it. The final preservation check covers all eleven freeze/preflight JSON records listed in the checks file, and no changed path is referenced by them. No alternate release_review2 script was needed. Historical reports, results, logs and manifests and all frozen executable sources remain unchanged from the cleanup baseline.

The scanner reads nonblank entries from its configured terms file, removes CR line endings and uses one compiled, escaped combined literal regex. Long terms match case-insensitive substrings; short terms require letter/digit boundaries, with underscores, hyphens, dots and slashes acting as boundaries. Positive lookahead and precomputed prefix aliases preserve overlapping matches and same-offset prefix terms without a regex search per term. The same compiled matcher redacts sensitive location fragments, including short substrings that must not be printed even when they are not token matches.

Working files are visited once, including ignored files but excluding .git directories and symlink targets. NUL-containing or non-UTF8 content is treated as binary and excluded, including files discovered to be binary after earlier text lines. Only capped pending locations and a count are buffered during classification. Tracked paths and branch/tag names are scanned separately. A single `git log --all -p` stream, with root and per-parent merge diffs and rename detection disabled, scans all reachable commit messages and full patch content. Commit messages are counted once per commit even when a merge emits multiple parent diffs. File headers are decoded semantically rather than repeatedly counting their quoted path representations.

Patch locations use the hunk's running old/new line counters; removed lines explicitly say `(old)`. Context lines use new-side numbering. Non-content path/header metadata has a labelled metadata/path location, since it has no source hunk line. Commit, branch and tag hits have their own labelled locations. Git C-quoted names and control characters are decoded/escaped safely for single-line output.

Stdout has only PASS/FAIL, TOTAL count and up to 200 `location term=index` lines. Every match occurrence contributes to the total, including distinct source domains and overlapping terms. Index means the original 1-based physical line in the terms file, so skipped blank lines do not renumber later entries. Paths/hashes that contain a term are redacted before printing. No matched line or term value is echoed. Exit codes are 0 clean, 1 hits and 2 errors; missing/empty terms fail closed without sensitive exception text. A daemon heartbeat emits only the unique commit count to stderr every 60 seconds, including during a long working-tree scan.

README now opens with four plain-language sentences above At a glance. It states the purpose, synthetic data, scripted verifier-validation scope and absence of model results. Owner/process wording was removed from the public README while technical execution/replay/validation caveats remain. Resume bullet wording now uses second-checker agreement and describes the historical corrected-runtime reruns with zero reward differences. Every displayed measurement remains generated from the existing result artifacts.

## Criteria and measured checks

| Requirement | Measured result | Outcome |
|---|---|---|
| Tests before implementation | 20 expected failures against the original scanner; console retained locally with hash in checks | PASS |
| New release scanner tests | 24 passing cases in the final suite | PASS |
| Full suite, real Docker integration enabled | 607 passed; 0 failures, 0 errors, 0 skipped | PASS |
| Table check | README and resume exactly reproduce stored evidence | PASS |
| Combined matcher/history stream | Test asserts one compiled term regex and one all-refs Git log process | PASS |
| Token, hex, underscore/hyphen and Unicode-letter boundaries | Fake-term pass/fail fixtures | PASS |
| Paths, messages, deleted lines, branches and tags | Fake temporary repos, old-side line number verified | PASS |
| Output privacy and hit cap | No fake term/line text; 250 occurrences counted with only 200 locations printed | PASS |
| CR/blank terms and exit codes | Physical indices preserved; 0/1/2 verified | PASS |
| Progress | Synthetic short-interval heartbeat fixture verifies commit count on stderr | PASS |
| Preserved historical/frozen files | No changes to old reports/results/logs/manifests or scientific source | PASS |
| Real terms review | Not run; fake terms only | NOT RUN |
| No license / no em dashes | None introduced in changed/new text | PASS |

Final full-suite proof is `results/tooling9_test_summary.json`, `logs/tooling9_full_tests.xml` and its console. The original JUnit XML (6437673 bytes) is retained losslessly in `logs/tooling9_junit_originals/tooling9_full_tests.xml-9f577a118029abed.gz` (30013 compressed bytes); both original and compact hashes are recorded. The compact display XML retains every test and suite result. Source scientific version numbers are not relabelled by this tooling task.

## Synthetic history benchmark

`results/tooling9_release_benchmark.json` records a disposable repository with 2000 commits modifying one public text file and 100 fake terms. Scanner wall time was **0.846780 seconds**, excluding repository construction. It returned exit 0 and PASS/TOTAL 0. This proves completion of that synthetic benchmark, not clearance of the actual project or a timing guarantee for its larger working tree.

Reproduction helper: `benchmark_history` in `tests/test_release_review.py`, also exercised by the full suite. It builds the temporary history using fast-import and overrides RELEASE_REVIEW_TERMS with its own fake file. The standalone benchmark uses the same helper. During setup, a system-Python invocation lacked pytest and a relative helper path needed resolving; neither invoked a real-terms review. The helper now always resolves the scanner path absolutely. All temporary benchmark repositories were removed by their context managers.

## Interpretation and limits

The prohibition on real terms applies to the owner's existing environment value; fake terms are explicitly required by the tests and substitute that value only in child test processes. The final full suite was launched with RELEASE_REVIEW_TERMS removed from its environment; scanner tests provide their own synthetic paths. No actual terms were inspected, printed, inferred or copied.

Binary classification is NUL/non-UTF8, and symlink content is skipped to avoid traversing outside the repository. Name matching remains enabled for every tracked path, including binary paths. History format metadata does not have a genuine source line; its labelled location is separate from old/new hunk locations. These choices and physical term-line indices make underspecified locations/counting explicit.

No em dashes were introduced in authored text. Existing frozen/historical text is retained as required, rather than globally rewritten. This is software and packaging cleanup, not E3 or a new scientific evaluation. No environment verifier, reward, threshold, generator, seed plan or freeze was changed. No independent verifier-author review session was needed because no scientific verifier was authored. Actual release-review status remains unknown until a separately authorized run with real terms.

## Repo size and compute

Pre-evidence-commit snapshot at `a548b757ff1826188071b06955a0c9f1b5f6b092`. Tracked size excludes the still-untracked new evidence/report files at the snapshot; directory sizes include local files and overlap the tracked aggregate.

| Component | Bytes | MiB |
|---|---:|---:|
| Git storage | 131149605 | 125.07 |
| Tracked working files | 681769736 | 650.19 |
| logs directory | 255833149 | 243.98 |
| results directory | 427654744 | 407.84 |
| Local artifacts | 2394620355 | 2283.69 |

Largest existing tracked file: 725192 bytes. No history or scientific artifact was removed to reduce size. Only newly generated JUnit display output was compacted with its complete original bytes preserved.

The full software suite records 226.604 local wall seconds; the scanner benchmark records 0.846780 seconds. These are separate measurements, not a complete phase CPU-time estimate. Earlier targeted tests and editing/setup overhead are not included. Project model API spend and GPU spend are $0; no model call, GPU job, paid pilot or scientific gate was run. Existing Docker integration tests ran as software validation. No sealed-test metric was computed.

## STOP

Tooling9 cleanup is complete. Commit/push the new report/evidence, delete only P2B_PROMPT9.md at completion, and wait for the owner. No license, repository rename, package/Hub publication or next phase was performed.
