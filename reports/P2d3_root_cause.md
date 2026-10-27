# P2d3 teardown investigation

The initiating cause of the historical E6 round-two failure cannot be established.
The retained round-two artifact contains only the later borrowed-runtime lifetime
message, not its initiating exception chain. No historical artifact was altered.
The affected rollout remains T4/random/1003044 in results/p2d2_gate.json.

A masking mechanism is established by inspection and a controlled regression.
E1/E5/E6 finalizers deliberately remove the solver before protected scoring; Env
cleanup subsequently stops the same runtime. Installed verifiers Rollout.fail
checks whether its borrowed runtime has stopped before recording a scorer error.
At that legitimate post-finalize boundary, a scorer exception can therefore be
replaced by the borrowed-runtime guard. The regression invokes the real installed
guard with a chained scorer error, then verifies the compatibility wrapper keeps
the original chain while preserving the guard for premature shutdown. This does
not identify what originally failed in the historical rollout.

Runtime changes serialize idempotent teardown, preserve daemon cleanup failures,
bound trusted transfers, separate a 20-second in-container solver deadline from
a 60-second host deadline, and persist full cause/context chains before framework
summaries. The narrow fail wrapper applies only to this project's CheckedRuntime
after completed finalization, stopped solver and started scoring. Foreign/live
runtime lifetime guards remain active. A failed cleanup prevents retry until
resource release is established; no surviving container is silently reused.

A protected root-owned completion record distinguishes Docker exec transport
status from identical solver exit codes. Policy audit evidence takes precedence
over subsequent infrastructure errors. All financial source files remain intact.
Controlled Docker fault regressions cover teardown failure, host timeout and
actual solver timeout; these are design-seed tests, not historical reproduction.
Stress and historical replay results are reported separately in the phase report.

Evidence: tests/validation/test_p2d3_infrastructure.py,
tests/validation/test_p2d3_runtime.py, logs/p2d3_fault_regressions.xml,
logs/p2d3_transport_runtime_tests.xml and their complete exception journals in
logs/p2d3_exceptions/. Generator version:
eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921.
