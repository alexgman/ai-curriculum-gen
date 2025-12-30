"""Research API endpoints - Report Downloads.

The main conversational research flow is handled by chat.py.
This file provides report download endpoints.
"""
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.report_generator import report_generator
from app.database import get_db
from app.crud.sessions import get_session


router = APIRouter()


@router.get("/{session_id}/report/docx")
async def download_docx(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Download research report as DOCX."""
    # Get session
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get final report from research_data or clarification_state
    research_data = session.research_data or {}
    clarification_state = session.clarification_state or {}
    
    final_report = research_data.get("final_report")
    
    # If not in research_data, try to build from clarification_state
    if not final_report:
        findings = clarification_state.get("findings", {})
        if findings:
            # Compile findings into report
            topic = clarification_state.get("topic", session.industry or "Research")
            final_report = f"# {topic} Research Report\n\n"
            
            if findings.get("providers"):
                final_report += "## Course Providers\n\n" + findings["providers"] + "\n\n"
            if findings.get("certifications"):
                final_report += "## Certifications\n\n" + findings["certifications"] + "\n\n"
            if findings.get("publications"):
                final_report += "## Publications & Resources\n\n" + findings["publications"] + "\n\n"
    
    if not final_report:
        raise HTTPException(status_code=404, detail="No report available for this session")
    
    # Generate DOCX
    topic = research_data.get("topic", session.industry or "Research")
    docx_buffer = report_generator.markdown_to_docx(final_report, topic)
    
    # Generate filename
    filename = report_generator.generate_filename(topic, "docx")
    
    return Response(
        content=docx_buffer.read(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/{session_id}/report/pdf")
async def download_pdf(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Download research report as PDF."""
    # Get session
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get final report from research_data or clarification_state
    research_data = session.research_data or {}
    clarification_state = session.clarification_state or {}
    
    final_report = research_data.get("final_report")
    
    # If not in research_data, try to build from clarification_state
    if not final_report:
        findings = clarification_state.get("findings", {})
        if findings:
            topic = clarification_state.get("topic", session.industry or "Research")
            final_report = f"# {topic} Research Report\n\n"
            
            if findings.get("providers"):
                final_report += "## Course Providers\n\n" + findings["providers"] + "\n\n"
            if findings.get("certifications"):
                final_report += "## Certifications\n\n" + findings["certifications"] + "\n\n"
            if findings.get("publications"):
                final_report += "## Publications & Resources\n\n" + findings["publications"] + "\n\n"
    
    if not final_report:
        raise HTTPException(status_code=404, detail="No report available for this session")
    
    # Generate PDF
    topic = research_data.get("topic", session.industry or "Research")
    
    try:
        pdf_buffer = report_generator.markdown_to_pdf(final_report, topic)
        filename = report_generator.generate_filename(topic, "pdf")
        
        return Response(
            content=pdf_buffer.read(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        # PDF generation might fail if WeasyPrint dependencies aren't installed
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}. Try downloading as DOCX instead."
        )


@router.get("/{session_id}/status")
async def get_research_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get current research status for a session."""
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    clarification_state = session.clarification_state or {}
    
    return {
        "session_id": session_id,
        "topic": clarification_state.get("topic"),
        "step": clarification_state.get("step", "initial"),
        "has_providers": bool(clarification_state.get("findings", {}).get("providers")),
        "has_certifications": bool(clarification_state.get("findings", {}).get("certifications")),
        "has_publications": bool(clarification_state.get("findings", {}).get("publications")),
        "has_report": bool(session.research_data and session.research_data.get("final_report")),
    }
