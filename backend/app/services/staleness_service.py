import logging

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.scheduling import SchedulingCycle

logger = logging.getLogger("exam_scheduler")


class StalenessService:
    """
    Central service hook for staleness signaling (Task P3.16, FR-05 step 10).
    Any create/update/delete of an enrollment, subject activation, or student status
    that affects a cycle marks that cycle's current graph snapshot and schedules as stale
    by incrementing the cycle's `data_version` counter.
    """

    @staticmethod
    def bump_cycle_data_version(db: Session, cycle_id: str) -> int:
        stmt = (
            update(SchedulingCycle)
            .where(SchedulingCycle.id == cycle_id)
            .values(data_version=SchedulingCycle.data_version + 1)
            .returning(SchedulingCycle.data_version)
        )
        new_version = db.scalar(stmt)
        if new_version:
            logger.info(f"Bumped data_version for cycle {cycle_id} to {new_version} (stale signal)")
            return new_version
        return 0


staleness_service = StalenessService()
