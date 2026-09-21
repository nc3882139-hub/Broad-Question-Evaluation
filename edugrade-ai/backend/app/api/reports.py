import json

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.models.database import Evaluation, get_db
from app.services import report_service

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/report/{evaluation_id}")
def report(evaluation_id: int, format: str = "json", db: Session = Depends(get_db)):
    row = db.get(Evaluation, evaluation_id)
    if not row:
        raise HTTPException(404, "Evaluation not found")
    rep = report_service.build_report(json.loads(row.result_json))
    name = f"edugrade-report-{evaluation_id}"
    if format == "csv":
        return Response(report_service.report_to_csv(rep), media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename={name}.csv"})
    if format == "pdf":
        pdf = report_service.report_to_pdf(rep)
        if pdf:
            return Response(pdf, media_type="application/pdf",
                            headers={"Content-Disposition": f"attachment; filename={name}.pdf"})
        return Response(report_service.report_to_html(rep), media_type="text/html",
                        headers={"Content-Disposition": f"attachment; filename={name}.html",
                                 "X-Note": "Install reportlab for true PDF export"})
    return rep