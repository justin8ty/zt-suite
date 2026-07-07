"""Protected Resource Demo API routes."""

from fastapi import APIRouter, Depends, HTTPException, Response

from app.api.deps import DbSession, get_compliant_device, require_mfa
from app.core.permissions import RoleName, require_roles
from app.models.device import Device
from app.models.user import User
from app.services.access_log import access_log_service

router = APIRouter()


PROTECTED_FILES = [
    {
        "id": "q3-risk-assessment",
        "name": "q3-risk-assessment.pdf",
        "size": "18KB",
        "sensitivity": "high",
        "type": "pdf",
        "mime_type": "application/pdf",
        "summary": "Quarterly security risk assessment for fictional Acme Finance.",
        "content": """Q3 Security Risk Assessment

Classification: HIGH
Prepared for: Acme Finance Executive Steering Committee

Executive Summary
- Endpoint compliance improved from 71% to 86% after mandatory disk encryption rollout.
- Three privileged accounts still lack phishing-resistant MFA.
- Simulated exfiltration testing showed unusual outbound flow volume was detected within 90 seconds.

Priority Risks
1. Legacy payroll workstation remains on an unsupported OS build.
2. Finance file share allows broad read access to contractor accounts.
3. Alert triage SLA exceeded 4 hours in two tabletop exercises.

Recommended Actions
- Block protected resource access from non-compliant endpoints.
- Rotate stale service credentials used by reporting jobs.
- Require manager approval for exports above 500MB.

Note: This is synthetic demo data for the ZT Suite FYP environment.
""",
    },
    {
        "id": "employee-compensation-sample",
        "name": "employee-compensation-sample.csv",
        "size": "9KB",
        "sensitivity": "restricted",
        "type": "csv",
        "mime_type": "text/csv",
        "summary": "Synthetic compensation table used to demonstrate restricted file preview.",
        "content": """employee_id,name,department,role,base_salary,bonus_target,risk_note
E-1042,Alicia Tan,Finance,Controller,118000,15%,Privileged payroll approver
E-1188,Marcus Lee,Security,IR Lead,132000,12%,Has production incident access
E-1207,Nadia Rahman,Engineering,Platform Manager,126500,10%,Can approve infrastructure changes
E-1331,Daniel Wong,Operations,Vendor Manager,98500,8%,Handles contractor onboarding
E-1404,Sofia Lim,Executive,Chief Financial Officer,210000,25%,Board reporting access
""",
    },
    {
        "id": "merger-integration-plan",
        "name": "merger-integration-plan.txt",
        "size": "14KB",
        "sensitivity": "confidential",
        "type": "text",
        "mime_type": "text/plain",
        "summary": "Fictional confidential integration plan for protected-file demonstration.",
        "content": """CONFIDENTIAL - Project Northstar Integration Plan

Objective:
Consolidate identity, endpoint posture, and audit logging controls across the acquired subsidiary within 60 days of close.

Day 0-15:
- Inventory all managed laptops and server assets.
- Freeze new local administrator grants.
- Require MFA for finance, HR, and engineering repositories.

Day 16-30:
- Deploy endpoint agent to high-risk departments.
- Enforce compliant-device checks for protected files.
- Review network flow anomalies from acquired office VPN ranges.

Day 31-60:
- Migrate remaining users into centralized RBAC groups.
- Archive legacy access logs for audit retention.
- Run tabletop exercise for insider-risk and data-exfiltration scenarios.

This document is fictional sample content generated for a demo environment.
""",
    },
]


def _public_file_metadata() -> list[dict[str, object]]:
    return [
        {key: value for key, value in file.items() if key != "content" or file["type"] != "pdf"}
        for file in PROTECTED_FILES
    ]


def _find_file(file_id: str) -> dict[str, object] | None:
    return next((file for file in PROTECTED_FILES if file["id"] == file_id), None)


def _pdf_bytes(title: str, text: str) -> bytes:
    safe_lines = [title, "", *text.splitlines()]
    stream_lines = ["BT", "/F1 16 Tf", "72 760 Td", "18 TL"]
    for index, line in enumerate(safe_lines[:36]):
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if index == 0:
            stream_lines.append(f"({escaped}) Tj")
        else:
            stream_lines.append(f"T* ({escaped}) Tj")
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("utf-8")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)


@router.get(
    "/files",
    summary="Access Protected Files",
    description="Demo endpoint protected by full Zero-Trust chain (Auth + MFA + Role + Posture).",
)
async def get_protected_files(
    db: DbSession,
    current_user: User = Depends(require_mfa),
    device: Device = Depends(get_compliant_device),
    _: User = Depends(require_roles(RoleName.ADMIN, RoleName.USER)),
) -> dict[str, object]:
    """Get protected files list.

    Access requires:
    1. Authenticated User (handled by get_current_user/require_mfa)
    2. MFA Enabled (require_mfa)
    3. Compliant Device (get_compliant_device)
    4. Valid Role (require_roles)
    """

    # Log success
    access_log_service.log_access(
        db=db,
        action="resource_access_granted",
        status="success",
        user_id=current_user.id,
        resource="/api/protected/files",
        details=f"Device: {device.hostname}, ID: {device.id}",
    )

    return {
        "message": "Access Granted",
        "user": current_user.email,
        "device": device.hostname,
        "files": _public_file_metadata(),
    }


@router.get(
    "/files/{file_id}/content",
    summary="Preview protected file content",
    description="Return protected file bytes after the same Zero-Trust checks as the file list.",
)
async def get_protected_file_content(
    file_id: str,
    db: DbSession,
    current_user: User = Depends(require_mfa),
    device: Device = Depends(get_compliant_device),
    _: User = Depends(require_roles(RoleName.ADMIN, RoleName.USER)),
) -> Response:
    """Return protected file content for browser preview."""
    file = _find_file(file_id)
    if not file:
        raise HTTPException(status_code=404, detail="Protected file not found")

    access_log_service.log_access(
        db=db,
        action="resource_file_previewed",
        status="success",
        user_id=current_user.id,
        resource=f"/api/protected/files/{file_id}/content",
        details=f"Device: {device.hostname}, ID: {device.id}; File: {file['name']}",
    )

    content = str(file["content"])
    filename = str(file["name"])
    mime_type = str(file["mime_type"])
    if file["type"] == "pdf":
        body = _pdf_bytes(filename, content)
    else:
        body = content.encode("utf-8")

    return Response(
        content=body,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
