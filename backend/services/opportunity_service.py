from __future__ import annotations

from scrapers import recommend_opportunities


def search_opportunities(branch: str, gpa: float) -> dict:
    results = recommend_opportunities(predicted_branch=branch, gpa=gpa)
    return {
        "stages": [item.to_dict() for item in results.get("stages", [])],
        "scholarships": [item.to_dict() for item in results.get("scholarships", [])],
    }
