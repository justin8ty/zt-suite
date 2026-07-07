"""Posture evaluation service."""

from datetime import datetime, timezone
import json

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.posture import PostureReport
from app.schemas.posture import PostureReportCreate
from app.services.device import device_service


class PostureService:
    """Service for posture evaluation."""

    @staticmethod
    def evaluate_compliance(report_in: PostureReportCreate) -> tuple[bool, int]:
        """Evaluate compliance based on report data.

        Returns:
            Tuple of (is_compliant, score).
        """
        raw_score = 0
        possible_score = 90 if report_in.os_up_to_date is None else 100

        # Simple scoring rules. Unknown patch status is excluded from the denominator
        # instead of being treated as a failed check.
        if report_in.antivirus_present and report_in.antivirus_enabled:
            raw_score += 40
        if report_in.firewall_enabled:
            raw_score += 30
        if report_in.disk_encrypted:
            raw_score += 20
        if report_in.os_up_to_date is True:
            raw_score += 10

        score = round((raw_score / possible_score) * 100)
        is_compliant = score >= 70
        return is_compliant, score

    @staticmethod
    def submit_report(
        db: Session, device: Device, report_in: PostureReportCreate
    ) -> PostureReport:
        """Submit and process a new posture report."""
        is_compliant, score = PostureService.evaluate_compliance(report_in)

        report = PostureReport(
            device_id=device.id,
            antivirus_present=report_in.antivirus_present,
            antivirus_enabled=report_in.antivirus_enabled,
            firewall_enabled=report_in.firewall_enabled,
            disk_encrypted=report_in.disk_encrypted,
            os_up_to_date=report_in.os_up_to_date,
            check_details=(
                json.dumps(report_in.check_details) if report_in.check_details else None
            ),
            compliance_score=score,
            is_compliant=is_compliant,
            timestamp=datetime.now(timezone.utc),
        )

        db.add(report)

        # Update device metadata from the agent's current posture report.
        if report_in.hostname:
            device.hostname = report_in.hostname
        if report_in.os_type:
            device.os_type = report_in.os_type
        if report_in.os_version:
            device.os_version = report_in.os_version
        if report_in.agent_version:
            device.agent_version = report_in.agent_version

        # Update device status
        device_service.update_compliance(db, device, is_compliant)

        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_latest_report(db: Session, device_id: int) -> PostureReport | None:
        """Get the most recent posture report for a device."""
        stmt = (
            select(PostureReport)
            .where(PostureReport.device_id == device_id)
            .order_by(desc(PostureReport.timestamp))
            .limit(1)
        )
        return db.execute(stmt).scalar_one_or_none()


posture_service = PostureService()
