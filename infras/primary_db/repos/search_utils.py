from sqlalchemy import or_, and_, case, cast, String, literal

SEARCH_PAGE_SIZE = 50


def build_search_filter(query: str, fields: list, rank_fields: list = None):
    """Shared word-order-independent search used by every /search endpoint.

    Every word the user types must match at least one of `fields`
    (so 'annual audit 2026' finds 'Audit Log ... (Annual-Annual)-FY-2026'
    regardless of word order).

    Returns (condition, rank):
      condition — SQLAlchemy filter, or None when the query is empty
      rank      — order_by expression putting the best matches first:
                  value starts with the query < contains it < other field matches
    """
    terms = [t for t in (query or '').lower().split() if t]
    conds = []
    for t in terms:
        st = f"%{t}%"
        conds.append(or_(*[cast(f, String).ilike(st) for f in fields]))
    condition = and_(*conds) if conds else None

    full = (query or '').lower().strip()
    rank_fields = rank_fields or fields[:1]
    whens = []
    weight = 0
    if full:
        for f in rank_fields:
            whens.append((cast(f, String).ilike(f"{full}%"), weight))
            weight += 1
            whens.append((cast(f, String).ilike(f"%{full}%"), weight))
            weight += 1
    # empty query has nothing to rank — use a constant SQL expression
    # (a bare python int breaks order_by: "ORDER BY expression expected")
    rank = case(*whens, else_=weight) if whens else literal(0)

    return condition, rank
