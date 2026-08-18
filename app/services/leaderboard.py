from typing import Literal, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models import UserSolution
from app.logger import get_logger

logger = get_logger(__name__)

RankingMetric = Literal["average_score", "total_solved", "best_score", "sum_score"]

# Each metric maps to a SQL aggregate over UserSolution.overall_score.
# Changing how ranking works later = add/edit an entry here, not rewrite the query.
_METRIC_EXPRESSIONS = {
    "average_score": func.avg,
    "total_solved": func.count,
    "best_score": func.max,
    "sum_score": func.sum,
}

DEFAULT_METRIC: RankingMetric = "average_score"


class LeaderboardService:
    """Computes ranked leaderboards from user_solutions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_leaderboard(
        self,
        metric: RankingMetric = DEFAULT_METRIC,
        limit: int = 50,
    ) -> List[Dict]:
        if metric not in _METRIC_EXPRESSIONS:
            logger.warning(f"Unknown leaderboard metric '{metric}', falling back to {DEFAULT_METRIC}")
            metric = DEFAULT_METRIC

        agg_fn = _METRIC_EXPRESSIONS[metric]
        score_expr = agg_fn(UserSolution.overall_score).label("score")

        query = (
            select(
                UserSolution.user_id,
                score_expr,
                func.count(UserSolution.id).label("solutions_count"),
            )
            .group_by(UserSolution.user_id)
            .order_by(desc("score"))
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "rank": i + 1,
                "user_id": row.user_id,
                "score": round(float(row.score), 2) if row.score is not None else 0,
                "solutions_count": row.solutions_count,
            }
            for i, row in enumerate(rows)
        ]