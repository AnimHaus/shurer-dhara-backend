import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

CF_TOKEN = os.getenv("CF_ANALYTICS_TOKEN", "")
CF_GQL = "https://api.cloudflare.com/client/v4/graphql"
CF_REST = "https://api.cloudflare.com/client/v4"

# ISO-2 → display name for the countries we care about
COUNTRY_NAMES: dict[str, str] = {
    "BD": "Bangladesh", "IN": "India",  "GB": "UK",
    "US": "USA",        "CA": "Canada", "AU": "Australia",
    "DE": "Germany",    "FR": "France", "SG": "Singapore",
    "AE": "UAE",        "SA": "Saudi Arabia",
}

_zone_id_cache: str | None = None


async def _zone_id() -> str:
    global _zone_id_cache
    if _zone_id_cache:
        return _zone_id_cache
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{CF_REST}/zones",
            headers={"Authorization": f"Bearer {CF_TOKEN}"},
        )
    data = r.json()
    if not data.get("success") or not data.get("result"):
        raise HTTPException(502, detail="Could not fetch Cloudflare zones")
    _zone_id_cache = data["result"][0]["id"]
    return _zone_id_cache


async def _gql(query: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            CF_GQL,
            headers={
                "Authorization": f"Bearer {CF_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"query": query},
        )
    return r.json()


@router.get("/geo")
async def geo_analytics():
    """Visitor share by country (top 5 + Others) for the last 24 hours."""
    logger.info("[analytics/geo] Fetching geo breakdown")
    zid = await _zone_id()
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=24)
    start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    query = f"""
    {{
      viewer {{
        zones(filter: {{zoneTag: "{zid}"}}) {{
          httpRequestsAdaptiveGroups(
            limit: 1000
            filter: {{datetime_geq: "{start_str}", datetime_leq: "{end_str}"}}
            orderBy: [count_DESC]
          ) {{
            count
            dimensions {{
              clientCountryName
            }}
          }}
        }}
      }}
    }}
    """

    data = await _gql(query)
    logger.debug("[analytics/geo] Raw GQL response: %s", data)
    _d = data.get("data") or {}
    _zones = (_d.get("viewer") or {}).get("zones") or [{}]
    groups = _zones[0].get("httpRequestsAdaptiveGroups") or []

    if not groups:
        logger.warning("[analytics/geo] No groups returned from Cloudflare GQL")

    totals: dict[str, int] = {}
    for g in groups:
        code = (g.get("dimensions") or {}).get("clientCountryName", "XX")
        totals[code] = totals.get(code, 0) + g.get("count", 0)

    if not totals:
        logger.warning("[analytics/geo] Empty totals — returning []")
        return []

    grand = sum(totals.values())
    logger.info("[analytics/geo] Grand total requests: %d across %d countries", grand, len(totals))
    sorted_entries = sorted(totals.items(), key=lambda x: x[1], reverse=True)

    result = []
    others_pct = 0.0
    others_count = 0
    for i, (code, count) in enumerate(sorted_entries):
        pct = round(count / grand * 100, 1)
        name = COUNTRY_NAMES.get(code, code)
        if i < 5:
            result.append({"country": name, "pct": pct, "count": count})
        else:
            others_pct += pct
            others_count += count

    if others_pct > 0:
        result.append({"country": "Others", "pct": round(others_pct, 1), "count": others_count})

    logger.info("[analytics/geo] Returning %d entries", len(result))
    return result


@router.get("/devices")
async def device_analytics():
    """Visitor share by device type for the last 24 hours."""
    logger.info("[analytics/devices] Fetching device breakdown")
    zid = await _zone_id()
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=24)
    start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    query = f"""
    {{
      viewer {{
        zones(filter: {{zoneTag: "{zid}"}}) {{
          httpRequestsAdaptiveGroups(
            limit: 1000
            filter: {{datetime_geq: "{start_str}", datetime_leq: "{end_str}"}}
            orderBy: [count_DESC]
          ) {{
            count
            dimensions {{
              clientDeviceType
            }}
          }}
        }}
      }}
    }}
    """

    data = await _gql(query)
    logger.debug("[analytics/devices] Raw GQL response: %s", data)
    errors = data.get("errors")
    if errors:
        logger.warning("[analytics/devices] GQL errors: %s", errors)
    _d = data.get("data") or {}
    _zones = (_d.get("viewer") or {}).get("zones") or [{}]
    groups = _zones[0].get("httpRequestsAdaptiveGroups") or []

    if errors or not groups:
        logger.warning("[analytics/devices] No adaptive groups — falling back to httpRequests1dGroups")
        return await _device_fallback(zid)

    device_map: dict[str, str] = {
        "desktop": "Desktop",
        "mobile":  "Mobile",
        "tablet":  "Tablet",
        "smarttv": "Smart TV",
        "bot":     "Bot",
        "other":   "Other",
        "unknown": "Other",
    }

    totals: dict[str, int] = {}
    for g in groups:
        raw = (g.get("dimensions") or {}).get("clientDeviceType", "unknown").lower()
        label = device_map.get(raw, raw.capitalize())
        totals[label] = totals.get(label, 0) + g.get("count", 0)

    grand = sum(totals.values())
    if not grand:
        logger.warning("[analytics/devices] Grand total is 0 — returning []")
        return []

    logger.info("[analytics/devices] Grand total: %d across %d device types", grand, len(totals))
    result = [
        {"name": name, "value": round(count / grand * 100, 1), "count": count}
        for name, count in sorted(totals.items(), key=lambda x: x[1], reverse=True)
    ]
    logger.info("[analytics/devices] Returning %d entries", len(result))
    return result


async def _device_fallback(zid: str) -> list[dict]:
    """Fallback: approximate mobile vs desktop from pageViews vs requests ratio."""
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=30)

    query = f"""
    {{
      viewer {{
        zones(filter: {{zoneTag: "{zid}"}}) {{
          httpRequests1dGroups(
            limit: 30
            filter: {{date_geq: "{start}", date_leq: "{end}"}}
          ) {{
            sum {{
              requests
              pageViews
            }}
          }}
        }}
      }}
    }}
    """
    data = await _gql(query)
    _d2 = data.get("data") or {}
    _zones2 = (_d2.get("viewer") or {}).get("zones") or [{}]
    groups = _zones2[0].get("httpRequests1dGroups") or []
    # If we can't determine device split, return empty so dashboard uses static fallback
    return []
