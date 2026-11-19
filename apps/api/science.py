"""Daily closed-day demand only. All operational history in this release is simulated."""
from datetime import date, timedelta
from hashlib import sha256
import json
from math import ceil
from statistics import mean, median

MODELS = ("naive", "weekly naive", "trailing mean", "trailing median", "exponential smoothing")
VERSION = "daily-v1.0"
LABEL = "SIMULATED — NOT VALIDATED ON CLINIC DATA"


def estimate(values, model):
    if model == "naive":
        return values[-1]
    if model == "weekly naive":
        return values[-7]
    if model == "trailing mean":
        return mean(values[-14:])
    if model == "trailing median":
        return median(values[-14:])
    level = values[0]
    for v in values[1:]:
        level = .3 * v + .7 * level
    return level


def predictions(values, model, days):
    sequence = list(values)
    for _ in range(days):
        sequence.append(max(0, estimate(sequence, model)))
    return sequence[len(values):]


def score(pairs):
    n = len(pairs)
    error = sum(abs(a-p) for a, p in pairs)
    total = sum(a for a, _ in pairs)
    return dict(mae=round(error/n, 4), wape=round(error/total, 4) if total else None,
                smape=round(sum(2*abs(a-p)/(a+p) if a+p else 0 for a,p in pairs)/n, 4),
                bias=round(sum(p-a for a,p in pairs)/n, 4),
                shortage_units=round(sum(max(0,a-p) for a,p in pairs), 2))


def forecast(history, day, horizon=14):
    """Selection days precede independent prequential evaluation. Missing suffix blocks model."""
    by_day = {r["date"]: r["qty"] for r in history}
    cutoff = date.fromisoformat(day) - timedelta(days=1)
    cursor = cutoff
    while cursor.isoformat() in by_day and (cutoff-cursor).days < 180:
        cursor -= timedelta(days=1)
    dates = [(cursor+timedelta(days=k+1)).isoformat() for k in range((cutoff-cursor).days)]
    v = [by_day[d] for d in dates]
    result = dict(label=LABEL, evidence_level="SYNTHETIC_DEMO", version=VERSION, cutoff=cutoff.isoformat(),
                  coverage=len(v), horizon=horizon, history=history, scores=[], points=[], future=[],
                  prediction_interval=None, shortage_probability=None, chosen=None,
                  calculation_id=sha256(json.dumps([VERSION,history,day,horizon],sort_keys=True).encode()).hexdigest()[:16])
    if len(v) < 35:
        return dict(result, reason="Require 35 consecutive closed days ending yesterday. Review the count manually.")
    validation = range(max(14,len(v)-21),len(v)-7)
    losses = {m:mean(abs(v[i]-estimate(v[:i],m)) for i in validation) for m in MODELS}
    model = min(MODELS, key=losses.get)
    holdout = range(len(v)-7,len(v))
    result.update(chosen=model, reason="Lowest one-day MAE on preceding validation origins; ties prefer the simpler baseline.",
                  selection_end=dates[-8], holdout_start=dates[-7],
                  scores=[dict(model=m, **score([(v[i],estimate(v[:i],m)) for i in holdout])) for m in MODELS],
                  points=[dict(date=dates[i],actual=v[i],prediction=round(estimate(v[:i],model),3)) for i in holdout],
                  future=[round(x,3) for x in predictions(v,model,horizon)],
                  validation_mae=losses, config={"window":14,"alpha":.3,"weekly_lag":7})
    return result


def reorder(fc, position, lead, review, service, pack, moq, capacity):
    if not fc["chosen"]:
        return dict(quantity=0, reason=fc["reason"], position=position, point=None)
    lead_demand = sum(fc["future"][:lead])
    # Historical underprediction quantile as a stress buffer, not a calibrated service guarantee.
    errors = sorted(max(0,p["actual"]-p["prediction"]) for p in fc["points"])
    safety = ceil(errors[ceil(service*len(errors))-1] * lead)
    point = ceil(lead_demand+safety)
    target = ceil(sum(fc["future"][:lead+review])+safety)
    candidate = ceil(max(moq,target-position)/pack)*pack if position<=point and target>position else 0
    qty = min(candidate, max(0,(capacity-position)//pack)*pack)
    if qty < moq:
        qty = 0
    return dict(quantity=qty, point=point, position=position, target=target, safety=safety,
                lead_demand=round(lead_demand,2), pack=pack, moq=moq, capacity=capacity,
                reason="At or below threshold; capacity and pack rules applied." if candidate else "Position covers the reorder threshold.")

