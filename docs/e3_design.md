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
