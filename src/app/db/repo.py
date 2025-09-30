from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import models as m

async def sample_dimensions(session: AsyncSession, k:int) -> list[int]:
    rows = (await session.execute(
        select(m.KnowledgeDimension.id).order_by(func.random()).limit(k)
    )).scalars().all()
    return rows

async def insert_question(session: AsyncSession, *, item_json: dict) -> int:
    q = m.Question(
        question_type=item_json["题型"],
        difficulty=item_json["难度"],
        title=item_json["题目"],
        material=item_json["材料"],
        score=item_json.get("满分", 10),
        suggest_time=item_json.get("建议用时", 10),
        word_limit=item_json.get("字数上限"),
        score_points=item_json.get("核心知识点"),
        answer_content=item_json.get("参考答案"),
        scoring_criteria=item_json.get("评分标准"),
    )
    session.add(q)
    await session.flush()
    for kd in item_json["维度"]:
        session.add(m.QuestionKdRelation(q_id=q.id, kd_id=kd))
    await session.commit()
    return q.id

async def get_question(session: AsyncSession, q_id:int) -> m.Question | None:
    return await session.get(m.Question, q_id)

async def insert_answer_record(session: AsyncSession, *, user_id:int|None, q_id:int,
                               original_answer:str, grading:dict) -> int:
    row = m.AnswerRecord(
        user_id=user_id, q_id=q_id, answer_type=1,
        original_answer=original_answer,
        total_score=grading["total_score"],
        subitem_scores=grading.get("subitem_scores"),
        dimension_scores=grading.get("dimension_scores"),
        comments=grading.get("comments"),
        hit_score_points=grading.get("hit_score_points"),
    )
    session.add(row)
    await session.commit()
    return row.id
