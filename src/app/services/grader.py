import logging, time
from app.schemas.practice import AnswerRequest, AnswerResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repo import get_question, insert_answer_record
from app.llm.chains import grade_chain

logger = logging.getLogger("svc.grader")

def _fallback_grade(answer: str, full: int = 10) -> dict:
    txt = (answer or "").strip()
    base = min(len(txt) / 100.0 * full, full)
    bonus = sum(0.8 for kw in ["目标","提问","反馈","评价","设计"] if kw in txt)
    total = max(0.0, min(float(full), base + bonus))
    logger.warning(f"LLM评分异常，使用兜底。base={base:.1f}, bonus={bonus:.1f}, total={total:.1f}")
    return {
        "total_score": round(total, 1),
        "subitem_scores": {"长度": round(min(base, full), 1), "关键词": round(min(bonus, 3.0), 1)},
        "comments": "（兜底机评）表达清晰，建议补充具体案例与证据支持。",
        "hit_score_points": ["长度","关键词"]
    }

async def submit_answer(body: AnswerRequest, session: AsyncSession) -> AnswerResponse:
    q = await get_question(session, body.question_id)
    if not q:
        logger.error(f"评分失败：题目不存在 q_id={body.question_id}")
        raise ValueError("题目不存在或已删除")

    full = int(q.score or 10)
    try:
        t0 = time.perf_counter()
        grading = await grade_chain().ainvoke({
            "full_score": full,
            "score_points": q.score_points or [],
            "rubric": q.scoring_criteria or "",
            "answer": body.original_answer
        })
        ms = (time.perf_counter() - t0) * 1000
        logger.info(f"LLM评分完成，用时 {ms:.0f}ms, q_id={body.question_id}, full={full}")
        grading["total_score"] = float(min(max(0.0, grading.get("total_score", 0.0)), full))
    except Exception as e:
        logger.exception(f"LLM评分异常: {e}")
        grading = _fallback_grade(body.original_answer, full)

    rec_id = await insert_answer_record(
        session,
        user_id=body.user_id,
        q_id=body.question_id,
        original_answer=body.original_answer,
        grading=grading
    )
    logger.info(f"评分入库: answer_record_id={rec_id}, total={grading['total_score']}")
    return AnswerResponse(
        answer_record_id=rec_id,
        total_score=grading["total_score"],
        subitem_scores=grading.get("subitem_scores"),
        dimension_scores=grading.get("dimension_scores"),
        comments=grading.get("comments"),
        hit_score_points=grading.get("hit_score_points"),
    )
