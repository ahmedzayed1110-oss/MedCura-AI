# Chain economics and market entry

All values in the economics workspace and T04 carry **SCENARIO**. The population of reachable chain decision-makers remains commercially unverified. Annual outreach inputs represent distinct, newly reachable chain accounts in that year. They require a qualified prospect list. The model has no link that turns regional facility counts into accounts or customers.

## Calculation

Each calendar year, multiply newly reachable accounts by the qualified share, then by the share entering completed pilots, then by the paid conversion rate. Round down to whole chains at each stage. Contract churn applies to opening paid chains at the beginning of the year and rounds to the nearest whole account, half up. Retained chains generate 12 months of billings. Each newly paying chain generates six months. The model assumes a constant number of active branches per paying chain.

| Measure | Formula |
|---|---|
| Closing contracts | Opening contracts − churned contracts + new paid conversions |
| Closing paying branches | Closing contracts × active branches per contract |
| Billable branch-months | Active branches per contract × (12 × retained contracts + 6 × new contracts) |
| Exit MRR and ARR | Closing paying branches × monthly price, then 12 × exit MRR |
| Recognized revenue | Billable branch-months × monthly price + onboarding fee × new contracts |
| Cost of delivery | Billable branch-months × (hosting + support) + deployment cost × new contracts |
| Gross margin | (Recognized revenue − delivery cost) / recognized revenue. Undefined at zero revenue. |
| Operating result | Gross profit − CAC × new contracts − 12 × fixed monthly expense |
| Recurring break-even | Ceiling of fixed monthly expense / (price − hosting − support). Undefined if unit contribution is nonpositive. |

Break-even covers recurring operations. Acquisition and onboarding flow through annual operating results. The comparison uses nominal SAR and excludes tax, financing, capital expenditure and VAT. It assumes capacity to service the input funnel. A pilot acquisition may use a one-branch footprint even where successful conversion later deploys multiple branches.

## Sensitivity and timing

T04 in `data/demo/T04_scenario_sensitivity.csv` lists every editable input, unit and resulting year-by-year output across conservative, base and favorable cases. Rates are percentages and fees and costs use SAR. For example, the base case begins with 12 new reachable chains, six qualified chains, three completed pilots and one paid conversion. Two branches at SAR 600 per month give SAR 1,200 exit MRR and SAR 14,400 exit ARR. Six billed months per newly converted branch plus a SAR 1,500 onboarding fee give SAR 8,700 recognized revenue in 2027. These prices and conversion rates are proposal inputs with no external price validation.

Select a preset or saved scenario, edit assumptions and calculate. Saving makes a named snapshot of inputs and all three output years in the authenticated tenant. Scenario history retains the actor and UTC save time. Unknown chain population remains null even after a user saves a scenario.

## Expansion gates

- **2027, Riyadh.** Start the first operational pilot in one branch. Obtain baseline data, signer authority, staff adoption and a scoped integration review. Revisit reachable-account and conversion assumptions using documented outreach.
- **2028, Makkah and Eastern Province.** Add sites only after the Riyadh review and a support/cost check. Verify the site count for each signing entity and avoid duplicate contracts.
- **2029, Asir, Madinah, Qassim and Jazan.** Qualify each region against evidence of repeatable integration, customer retention, viable service cost and model monitoring. The seven-region footprint describes geographic reach.
