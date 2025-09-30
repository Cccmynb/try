import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.practice import PracticeRequest, GenerateResponse, AnswerRequest, AnswerResponse, ErrorResponse
from app.deps import get_db
from app.services.generator import generate_practice_item
from app.services.grader import submit_answer
import json

logger = logging.getLogger("routes.practice")
router = APIRouter(prefix="/practice", tags=["Practice"])

@router.post("/generate", response_model=GenerateResponse,
             responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def generate(req: PracticeRequest, request: Request, session: AsyncSession = Depends(get_db)) -> GenerateResponse:
    rid = getattr(request.state, "request_id", "-")
    logger.info(f"[{rid}] /practice/generate req={json.dumps(req.model_dump(), ensure_ascii=False)}")
    try:
        item, qid = await generate_practice_item(req, session)
        logger.info(f"[{rid}] generate OK qid={qid} dims={item.维度} diff={item.难度} points={len(item.核心知识点)}")
        return GenerateResponse(question_id=qid, item=item)
    except Exception as e:
        logger.exception(f"[{rid}] generate FAIL: {e}")
        raise HTTPException(status_code=502, detail=f"生成失败：{e}")

@router.post("/answer", response_model=AnswerResponse,
             responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def answer(body: AnswerRequest, request: Request, session: AsyncSession = Depends(get_db)) -> AnswerResponse:
    rid = getattr(request.state, "request_id", "-")
    logger.info(f"[{rid}] /practice/answer req={{'q':{body.question_id},'user':{body.user_id}}}")
    try:
        resp = await submit_answer(body, session)
        logger.info(f"[{rid}] answer OK ar_id={resp.answer_record_id} total={resp.total_score}")
        return resp
    except Exception as e:
        logger.exception(f"[{rid}] answer FAIL: {e}")
        raise HTTPException(status_code=502, detail=f"评分失败：{e}")
