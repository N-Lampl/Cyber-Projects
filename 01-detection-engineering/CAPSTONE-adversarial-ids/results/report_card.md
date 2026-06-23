# IDS Robustness Report Card

**Target:** shared `ids_pipeline` RandomForest on synthetic flows
**Attack:** constrained FGSM (mutable-feature evasion, epsilon=2.0, steps=10)
**Defense:** adversarial training (constrained-FGSM augmentation)

## Overall grade: **A**

| Metric | Before hardening | After hardening |
|---|---|---|
| Clean accuracy | 0.926 | 0.924 |
| Clean ROC-AUC | 0.968 | 0.966 |
| Clean recall (attacks caught) | 0.796 | 0.781 |
| **Attack success rate** | **83.2%** | **0.0%** |
| Detected attacks evaded | 485/583 | 0/565 |

**Attack-success-rate dropped 83.2%** (from 83.2% to 0.0%) after hardening, while clean accuracy moved -0.002.

## Constraint compliance (adversarial flows)

- Immutable features preserved: 100.0%
- Per-feature validity (consistent flows): 100.0%
- Feasible (would survive a real network sanity check): 100.0%

Only mutable features (duration, src/dst bytes, connection counts) were perturbed, in attacker-feasible directions only; error/rate aggregates and the protocol/service/flag identity were held fixed.

## How to read this

A high *clean* accuracy says nothing about robustness. The pre-hardening row shows how many attacks the deployed model caught but a feasible, constraint-respecting perturbation then slipped past. The after row shows the same attack re-run against the hardened model. The gap between the two is the value of the defense.
