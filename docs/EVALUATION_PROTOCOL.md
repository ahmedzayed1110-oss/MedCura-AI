# Forecast and policy evaluation

Daily demand is the sum of normally issued base units for a branch and SKU on a closed Riyadh business date. A closed day with no issues is an observed zero in the simulation. A day with no close record is missing. Receipts, quarantined returns, adjustments, reservations and transfers do not enter consumption. A production close process must reconcile scans, outages, returns, substitutions and bulk issues with the branch lead. Latent demand lost during a stockout is generally unobserved.

Use the most recent continuous closed-day suffix ending immediately before the active business date. Demand estimation requires at least 35 consecutive days. The five models are last observation, weekly seasonal naive, trailing 14-day mean, trailing 14-day median and exponential smoothing with alpha 0.3. Each rolling origin uses only earlier observations. Choose the lowest one-step MAE over the earlier validation origins. Ties prefer the earlier, simpler model. Assess all models on the final seven later origins. Refit the chosen baseline at the current origin and recurse nonnegative expected daily quantities for lead plus review days. The run hash incorporates the history, version, cutoff, config-dependent horizon and policy position.

MAE is mean absolute error in base units. WAPE divides absolute error by total observed demand and is null on a zero denominator. sMAPE assigns zero error when prediction and actual are both zero. Bias averages prediction minus actual. Shortage units sum positive actual-minus-predicted differences; this is a forecast diagnostic. T05 and F11 describe generated data. Seven held-out days cannot establish calibrated intervals or service probabilities.

## Reorder and expiry

Reorder point equals forecast lead-time demand plus a one-sided empirical underprediction buffer. The selected quantile of the seven held-out positive errors, including zeroes, is scaled by lead days. This is a conservative heuristic. Service quantile does not establish a measured fill rate. A proposal triggers at or below the threshold and only when the target exceeds position. Round up to packs and MOQ, cap at whole packs within capacity, and decline an order that can no longer meet MOQ. Recheck the saved decision hash on approval.

The expiry watch flags positive balances within 30 days. A dated lot can generate a transfer candidate when both branches have adequate closed histories. Estimate surplus after origin consumption through expiry. Bound transfer by origin safety stock, destination target shortfall, and destination consumption after transport plus a two-day buffer. Check transport/handling cost against proposed units times the assumed unit write-off value. Recheck before requesting, approving and dispatching. No empirical disposal probability is estimated. Cost, shelf life, freight and stockroom handling assumptions require field validation.

## Stress bench

Run `python scripts/stress.py`. It compares a fixed threshold/fixed order and a rolling policy on the same time-ordered synthetic demand, measuring units short and unit-days held. The bench also applies a lead-time delay, a last-day spike, a missing scan day, a quarantined return, a shelf-life failure and inter-branch redistribution. Parameters and outputs are in data/demo/stress.json. Multi-site holdout validation, supplier lead-time distributions, manual baseline performance and independent pilot outcomes remain future evidence requirements.

