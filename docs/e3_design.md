# E3 P3b design preflight

Status: blocked before implementation, construction or policy execution. This note records requirements and mathematical feasibility findings, not an approved experimental design. No E3 policy result, model baseline or sealed-test result exists. Generator identity remains eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921. Shared runtime and existing environments are unchanged.

## Intended protocol

The requested environment would expose synthetic selected candidate returns and heterogeneous search counts, accept one executable probability-analysis script, and grade actual primary and fresh-replay executions using the existing checked local Docker runtime. Host-private binary truth would never enter a solver mount. Required stages are independent tests/checker first, construction-only admission and committed populations, separate stress runs, committed source/design/image freeze, one-shot gate, independent recorded-reward audit and a fixed author-review selection. All data would be development-only; no model/API/GPU or sealed evaluation is authorized.

No candidate-return construction, effect parameter, selection distribution, correlation estimator, honest-reference floor or seed reservation has been adopted. Those decisions cannot be validly preregistered while the required score and construction constraints conflict. No seed is screened or rejected to repair this feasibility failure.

## Decision threshold and illustrative strictly proper raw loss

For a posterior probability p of a real effect, admitting costs 3(1-p) and rejecting costs p. Admission is Bayes-optimal exactly when p > 3/4. A probability score should elicit p; cost-sensitive admission then applies that threshold to the elicited probability. Class-weighting an ordinary probability loss without correcting its elicited target would not establish strict propriety.

An illustrative regular weighted proper loss uses w(t)=t^3(1-t), positive on (0,1), with its mode at 3/4:

- L(q,0) = integral_0^q t*w(t) dt = q^5/5 - q^6/6.
- L(q,1) = integral_q^1 (1-t)*w(t) dt = 1/60 - q^4/4 + 2*q^5/5 - q^6/6.
- d E[L(q,Y)]/dq = (q-p)*w(q).

The derivative is negative below p and positive above p, so truthful q=p uniquely minimizes expected raw loss (including the appropriate endpoint limits). This raw rule is an example for feasibility checking, not a selected E3 reward. Numerical tests must distinguish raw-loss propriety from propriety of a transformed reward.

## Blocking all-null construction requirement

The prompt requires all-null T4 cases, says reject-all is optimal there, and simultaneously requires the honest reference to beat **each** wrong policy, including reject-all, by at least 0.02 at case construction.

On all-null truth y=(0,...,0), a strictly proper score is maximized by q=(0,...,0), exactly the reject-all report. Any honest reference must therefore score at most reject-all, making the demanded positive gap impossible. If the reference outputs the optimum, its report is identical to reject-all, and an output-only verifier cannot distinguish their policy labels. Rejecting constant probability vectors would also reject the correct all-null oracle report and would change the requested scoring contract.

This is a per-construction contradiction, independent of the fraction of all-null episodes or mean gate thresholds. Assigning zero reward to every all-null report would avoid free constant reward but also gives zero separation on those required cases. Giving full reward to correct all-null reports necessarily rewards reject-all there. All-real optimum similarly coincides with admit-all if that structure is included; its required handling cannot distinguish identical probability vectors either.

The 0.95 oracle and 0.10 wrong thresholds are means, not per-case thresholds. Rarity can sometimes satisfy such mean bounds, but cannot repair the explicit per-case positive-gap requirement. No threshold or tier composition is changed here.

## Blocking propriety claim after clipped baseline normalization

Let raw episode loss be a sum of strictly proper binary losses with oracle loss zero. The requested nondegenerate normalization is R(q,y)=clip((B(y)-L(q,y))/B(y),0,1), where B(y)=L(0,y) is reject-all loss. It is not a fixed outcome-independent affine transform, and clipping can destroy strict propriety.

Take eight candidates with two possible complementary truth vectors: A has four real and four null; B reverses them. Both have exactly the preregistered half-null fraction and the same positive reject-all baseline D=4*L(0,1). Let P(A)=p. For the deterministic report q_A=(1,1,1,1,0,0,0,0), reward is one in A and zero in B: loss in B is 4*(L(0,1)+L(1,0)) > D. Its expected normalized reward is p.

For p below but sufficiently close to one, truthful marginal probabilities are q_p=(p,p,p,p,1-p,1-p,1-p,1-p). By continuity, the rare B state still clips to zero; in the likely A state strict propriety gives strictly positive loss, so reward is strictly below one. Thus E[R(q_p,Y)] < p = E[R(q_A,Y)]. This defeats strict propriety for this broad continuous finite-endpoint additive family, including the illustrative weighted raw rule, without using all-null degeneracy. An independent review also supplies a concrete Brier example. The final primary/replay minimum does not justify claiming the transformed score is strictly proper.

## Disposition before further work

An independent validation author reviews these findings in docs/e3_feasibility_review.md. After this note is committed, that author may write self-contained mathematical feasibility tests and a separate checker first, without an E3 implementation or generator/policy execution. Their results are mathematical fixtures, not E3 policy performance or a passing environment gate.

A read-only inventory of existing gate primary/replay seed records is also required before any reservation. Prior numerical replay ranges already reach the upper development partition, so it is unsafe to assume that an apparently unallocated high sub-range is unused by every environment. The inventory will retain input hashes and will not change old seed routing or any historical artifact.

Proceeding to data construction, calibrated floor, seed screen, stress, freeze or gate requires a consistent scoring/degeneracy/separation contract and a valid seed reservation. Possible amendments for the owner to consider are a fixed affine bounded proper score, an explicit distinction between raw propriety and a non-proper clipped task reward, and exceptions for optimal constant controls on degenerate cases. None is adopted or authorized by this note. The frozen thresholds, runtime and generator are unchanged.

# Round 2 prospective design (2026-10-30 UTC)

P2B_PROMPT11.md replaces the earlier conflicting clauses; the preflight above remains historical evidence. E3 will use K=20 and r=10 in every episode (realized null fraction point mass at .5), within the owner's permitted count and fraction ranges. No all-null/all-real controls. This deliberate restriction avoids the constant-.5 reward violation at real fraction .45 and the elevated clipped uniform-report expectation at K=8. Generalization to other candidate counts/fractions is not certified.

## Score and numerical controls

Adopt the unnormalized Beta(4,2) weight w(t)=t^3(1-t), mode .75, and the two analytic raw losses derived above. Multiplying the weight by the Beta normalization constant changes neither normalized reward nor its optimizer. Raw episode loss is candidate mean. L_ref=.45/60=3/400, fixed independently of truth. Per execution R=clip(1-L/L_ref,0,1); final reward=min(primary,replay). Strict propriety applies only to raw loss, not clip or min. Bayes classification costs separately give admission p>.75. Invalid IDs/schema, duplicate keys, booleans/nonfinite/out-of-range probabilities, unsafe execution or tamper produce zero.

Exactly half-real reject-all clips to zero; admit-all clips to zero; constant .5 is 1/36. The uniform report ceiling is interpreted as expected/mean reward under independent U[0,1] probabilities, consistent with the policy mean gates, not a bound on every possible random draw. Its numerical integration test will be independent of generated episodes. Existing exact rational clipped-score counterexample remains required evidence.

## Candidate data and construction protocol

Use the unchanged shared generator with 200 assets and 500 days, force_alpha=True, and its recorded IC/half-life. For each candidate draw N_i candidate signals/portfolios against those synthetic returns, with genuine candidates incorporating the generator's lagged planted signal and null candidates using independent random signals. Strategy daily return is the cross-sectional mean of signal times next-day asset return; record the selected trial's return vector, mean, standard deviation and t statistic, and select the largest in-sample mean/std among N_i. Host truth records membership, planted-signal mixing size, selected trial and all construction parameters. IDs and order are independently randomized by seed/tier; no IDs encode truth. Correlated T3/T4 candidates mix a shared underlying signal component into trial signals; construction metadata explicitly records the mixture. No labels/effects/trial winners or oracle are mounted in the solver.

T1 uses larger planted-signal mixing and smaller searches; T2 weaker mixing and larger searches; T3 mixes shared signals, heterogeneous searches and selection distractors; T4 emphasizes null huge-search/high-Sharpe, strong real huge-search and modest-Sharpe real single-search candidates. Exact numerical effect/search schedules and solver likelihood approximation must be specified before generator construction or screening; this is an incomplete design until that supplement is committed. No construction or policy result will be used to choose undeclared schedules.

Design seeds 1000000..1000099, primary candidates 1001000..1001999 (first 500 construction-admitted), replay candidates 1002000..1002999 (all admitted, at least 500). Three populations are disjoint within E3; cross-environment overlap is expressly allowed. Screen all tiers using construction only, before any policy run. Retain every rejected case and commit populations/rejection counts before policy execution. Construction-only structural separation checks cannot evaluate submitted policies or rewards; any analytical separation certificates and their limits must be specified in the supplement.

## Prospective validation and stopping rules

Independent validation author writes tests and separate checker before implementation, with no implementation-author edits. Preserve raw records for independent audit. At least twelve wrong policies, eight cheaters, oracle, uniform-random, honest reference and shallow top-k are required as in the owner roster. Honest floor and null false-admit ceiling must be justified from construction statistics on design seeds before freeze; incentive transforms use temperature [0,.25,.5,.75,1,1.5,2,4,100] on logits plus endpoint contractions toward 0 and toward 1, with maximum allowed per-tier mean reward gain .02. Report reliability bins and false admits per null candidate.

Stress uses 5000 full checked rollouts each at C8/C12, zero retries expected, existing infrastructure retry policy unchanged. Freeze binds sources/design/image/screen/populations and fixed 50 author-review selection. One-shot gate uses oracle 500 per tier and every other policy 50 per tier, continues all planned rows, and retains failures. Do not retune after gate. No models, GPU, sealed seeds, publishing, README or shared runtime/generator/other-environment source changes. Spend $0.

## Round-two construction supplement, before first construction

Trial construction is now specified precisely. From the generator's force-alpha market compute a causal equal-weight signal portfolio A[t]=mean(signal[t-1,a]*returns[t,a]) over 200 assets for days 1..499. A null trial draws an asset index and independent random sign per day and uses the signed return of that asset. A real trial adds c*A[t] to the same null path. Within each candidate mix an independent signed-asset path with a group-shared signed-asset path using sqrt(1-rho) and sqrt(rho), respectively. Ten candidates in each of two groups share the group path. Thus null trial unconditional means are zero and real trials include the generator's planted-alpha machinery, rather than a separately invented nonzero mean. All trial paths are scaled by .01/std(null market returns), a truth-independent common scale. Select the trial maximizing mean/std. Record effect coefficient c and realized added mean only in the host oracle. Public data includes selected returns and N, group and declared rho, plus the common real-hypothesis effect distribution (not membership or actual effect). No special resampling by outcome is allowed.

Prospective schedules, cyclic within each randomized membership class: T1 N=[1,4,16], c=1, rho=.1; T2 N=[20,100,500], c=.5, rho=.3; T3 N=[1,50,500], c=.5, rho=.7; T4 null N=500, real N=[1,500], c=[.4,1.5], rho=.5. K20/r10 throughout. Randomize class order with a seed/tier-specific SHA256-derived RNG. The generator itself always uses the original development seed and frozen version hash.

The honest reference estimates an effective trial count 1+(N-1)*(1-rho), uses a normal-max likelihood ratio for zero versus the declared real-hypothesis effect, and applies a logistic posterior with prior .5. It is a specified approximation, not a claim of exact Gaussianity, true calibration or independence. Estimate the effect in t units from the public hypothesis expected portfolio mean and null-return standard deviation; do not read actual real labels/effects. Correlation adjustment is deliberately explicit and its approximation limits must be reported. Wrong policies use standard one-sided normal-tail .05 thresholds and variants listed by the owner; overconfident means thresholding this uncorrected test, not an oracle furnished with truth. Shallow top-k admits the top half by Sharpe. Uniform random uses independent probability draws seeded from public input SHA256. Hardcoded IDs remain fixed across replay. Oracle source may contain host truth for validation only; no task oracle is mounted for other policies.

The admission screen checks only finite, nonzero-variance paths, mixed membership, stated schedules/correlation groups and required decoy ordering. It must not evaluate policy outputs or copied policy formulas. Because these structural checks alone do not prove every requested .02 policy gap, independently measure those gaps after the screen is committed and before stress/freeze; a failed gap is a construction-design failure, never permission to drop a seed. Retain the screened population even on failure. No effect/search/correlation tuning after policy results is adopted in this supplement. If construction evidence cannot support the required separation, stop before an invalid freeze and report the failure rather than claiming the screen proves a certificate it does not establish.
