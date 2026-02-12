from __future__ import annotations
import json
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.stocks import list_universe_stocks
from repositories.templates import get_template_by_id
from repositories.candidates import create_candidates_bulk
from services.ta.signals import list_signal_rows
from models import CandidateCreate, CandidateStatus

# Rule schema expected from template_config_json["entry_rules"]:
# {"field": "rsi", "op": "lt", "value": 35}
def _rule_passes(rule: dict, latest: dict) -> bool:
    # Pull the rule parts explicitly so each decision branch is readable.
    field = rule.get("field")
    op = rule.get("op")
    value = rule.get("value")
    # `latest` is one computed signal row (ex: {"rsi": 29.3, "ema_20": 101.2, ...}).
    actual = latest.get(field)

    # Missing signal values should fail closed (no candidate), not pass by accident.
    if actual is None:
        return False
    # Simple deterministic operator mapping. Unknown operator => fail closed.
    if op == "lt":
        return actual < value
    if op == "lte":
        return actual <= value
    if op == "gt":
        return actual > value
    if op == "gte":
        return actual >= value
    if op == "eq":
        return actual == value
    return False

def build_candidates_from_template(
    *,
    universe_id: int,
    template_id: int,
    template_config_json: str,
    signal_map: dict[str, list[dict]],
) -> list[CandidateCreate]:
    # Template config is stored as JSON in DB, so parse once at function entry.
    cfg = json.loads(template_config_json)
    # `entry_rules` is a list of rule dicts consumed by `_rule_passes`.
    rules = cfg.get("entry_rules", [])
    # Optional score field (ex: "signal_strength", "rsi") used for ranking candidates.
    score_field = cfg.get("score_field")

    out: list[CandidateCreate] = []
    for ticker, rows in signal_map.items():
        # No signal rows means we cannot evaluate rules for this ticker.
        if not rows:
            continue
        # Signal rows are expected ascending by date, so the last row is current context.
        latest = rows[-1]

        # Candidate is valid only if every configured entry rule passes.
        if not all(_rule_passes(r, latest) for r in rules):
            continue

        # Score defaults to 0.0 when config has no score field.
        score = float(latest.get(score_field, 0.0)) if score_field else 0.0
        out.append(
            CandidateCreate(
                universe_id=universe_id,
                template_id=template_id,
                ticker=ticker,
                score=score,
                status=CandidateStatus.proposed,
                reason_code="template_rules_passed",
                # Store evaluation context for audit/debug later.
                payload_json=json.dumps(
                    {
                        "template_id": template_id,
                        "latest_signal": latest,
                        "applied_rules": rules,
                    }
                ),
            )
        )
    return out


async def load_latest_signal_map(
    session: AsyncSession,
    *,
    universe_id: int,
    provider: str = "yahooquery",
    interval: str ="1d"
) -> dict[str, list[dict]]:
    stocks = await list_universe_stocks(session, universe_id=universe_id)
    out: dict[str, list[dict]] = {}
    for stock in stocks:
        rows = await list_signal_rows(
            session,
            stock_id=stock.id,
            provider=provider,
            interval=interval,
            limit=1,
            order_desc=True,
        )
        out[stock.ticker] = [
            {
                "as_of": as_of.isoformat(),
                "rsi": rsi,
                "macd": macd,
                "macd_signal": macd_signal,
                "ema_20": ema_20,
                "ema_50": ema_50,
                "bb_upper": bb_upper,
                "bb_lower": bb_lower,
            }
            for (as_of, rsi, macd, macd_signal, ema_20, ema_50, bb_upper, bb_lower) in rows
        ]
    return out


async def generate_candidates_for_template(
    session: AsyncSession,
    *,
    universe_id: int,
    template_id: int,
    provider: str = "yahooquery",
    interval: str = "1d"
) -> int:
    template = await get_template_by_id(session, template_id)
    if template is None:
        raise ValueError("template not found")
    
    signal_map = await load_latest_signal_map(
        session,
        universe_id=universe_id,
        provider=provider,
        interval=interval,
    )
    items = build_candidates_from_template(
        universe_id=universe_id,
        template_id=template_id,
        template_config_json=template.config_json,
        signal_map=signal_map,
    )
    rows = await create_candidates_bulk(session, items)
    return len(rows)