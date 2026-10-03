import json
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.all_models import User, Video, Incident
from backend.app.api.auth import get_current_user

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/video/{video_id}/json")
def export_video_report_json(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    video = db.query(Video).filter(Video.id == video_id, Video.user_id == current_user.id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video record not found")

    incidents = db.query(Incident).filter(Incident.video_id == video.id).order_by(Incident.timestamp_sec.asc()).all()

    report_data = {
        "platform": "Phylax AI Camera Surveillance Platform",
        "tagline": "Detect. Alert. Protect.",
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "video": {
            "id": video.id,
            "filename": video.original_filename,
            "profile": video.profile,
            "duration_sec": video.duration_sec,
            "fps": video.fps,
            "resolution": f"{video.width}x{video.height}",
            "created_at": video.created_at.isoformat()
        },
        "incidents_summary": {
            "total_flagged": len(incidents),
            "confirmed_count": len([i for i in incidents if i.reviewed_status == "CONFIRMED"]),
            "false_alarm_count": len([i for i in incidents if i.reviewed_status == "FALSE_ALARM"]),
            "flagged_for_review_count": len([i for i in incidents if i.reviewed_status == "FLAGGED_FOR_REVIEW"])
        },
        "incidents": [
            {
                "id": inc.id,
                "type": inc.type,
                "severity": inc.severity,
                "timestamp_sec": inc.timestamp_sec,
                "frame_number": inc.frame_number,
                "confidence": inc.confidence,
                "description": inc.description,
                "reviewed_status": inc.reviewed_status,
                "bbox": inc.bbox
            }
            for inc in incidents
        ]
    }

    content = json.dumps(report_data, indent=2)
    headers = {"Content-Disposition": f'attachment; filename="phylax_report_video_{video.id}.json"'}
    return Response(content=content, media_type="application/json", headers=headers)


@router.get("/video/{video_id}/pdf")
def export_video_report_pdf(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    video = db.query(Video).filter(Video.id == video_id, Video.user_id == current_user.id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video record not found")

    incidents = db.query(Incident).filter(Incident.video_id == video.id).order_by(Incident.timestamp_sec.asc()).all()

    # Formatted HTML report suitable for browser print-to-PDF or saving
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Phylax Surveillance Audit Report - Video #{video.id}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0b0e14; color: #e2e8f0; padding: 40px; }}
            .header {{ border-bottom: 2px solid #06b6d4; padding-bottom: 20px; margin-bottom: 30px; }}
            .title {{ font-size: 28px; font-weight: bold; color: #06b6d4; letter-spacing: 1px; }}
            .subtitle {{ color: #94a3b8; font-size: 14px; margin-top: 5px; }}
            .card {{ background: #161f2e; border: 1px solid #1e293b; padding: 20px; border-radius: 8px; margin-bottom: 25px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #334155; }}
            th {{ background: #0f172a; color: #38bdf8; font-size: 12px; text-transform: uppercase; }}
            .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; display: inline-block; }}
            .critical {{ background: #ef4444; color: #fff; }}
            .high {{ background: #f97316; color: #fff; }}
            .medium {{ background: #eab308; color: #000; }}
            .notice {{ color: #94a3b8; font-size: 12px; margin-top: 40px; border-top: 1px dashed #334155; padding-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title">PHYLAX SURVEILLANCE REPORT</div>
            <div class="subtitle">Detect. Alert. Protect. | Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
        </div>

        <div class="card">
            <h3 style="margin-top:0; color:#06b6d4;">Video Source & Processing Summary</h3>
            <p><strong>Filename:</strong> {video.original_filename}</p>
            <p><strong>Location Profile:</strong> {video.profile}</p>
            <p><strong>Duration:</strong> {video.duration_sec}s ({video.fps} FPS, {video.width}x{video.height})</p>
            <p><strong>Total Incidents Flagged:</strong> {len(incidents)}</p>
        </div>

        <div class="card">
            <h3 style="margin-top:0; color:#06b6d4;">Flagged Incidents Log</h3>
            <table>
                <thead>
                    <tr>
                        <th>Time (sec)</th>
                        <th>Frame</th>
                        <th>Incident Type</th>
                        <th>Severity</th>
                        <th>Status</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
    """

    for inc in incidents:
        sev_class = inc.severity.lower()
        html_content += f"""
                    <tr>
                        <td>{inc.timestamp_sec:.2f}s</td>
                        <td>#{inc.frame_number}</td>
                        <td><strong>{inc.type}</strong></td>
                        <td><span class="badge {sev_class}">{inc.severity}</span></td>
                        <td>{inc.reviewed_status}</td>
                        <td>{inc.description or ''}</td>
                    </tr>
        """

    html_content += """
                </tbody>
            </table>
        </div>

        <div class="notice">
            <strong>Legal & Operational Notice:</strong> Phylax is an AI surveillance assistant that flags events for human review. All results are labeled "flagged for review" and require verification. Phylax notifies emergency contacts designated by the user and does NOT automatically contact emergency services.
        </div>
    </body>
    </html>
    """

    headers = {"Content-Disposition": f'attachment; filename="phylax_report_video_{video.id}.html"'}
    return Response(content=html_content, media_type="text/html", headers=headers)
