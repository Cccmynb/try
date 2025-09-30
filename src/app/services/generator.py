import logging, random, time
from typing import Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.schemas.practice import PracticeRequest, PracticeItem
from app.db import models as m
from app.db.repo import insert_question
from app.llm.chains import gen_chain
import json

logger = logging.getLogger("svc.generator")
SCORE_THRESHOLD = 8

def _ensure_min_len(text: str, n: int = 150) -> str:
    if len(text) >= n: return text
    pad = " 本课以交际为导向，教师根据学生水平分层提问，并通过同伴互评与即时反馈促进学习动机。"
    while len(text) < n: text += pad
    return text

async def _resolve_dimensions(session: AsyncSession, req: PracticeRequest) -> List[int]:
    if req.得分 is not None and req.得分 >= SCORE_THRESHOLD:
        k = random.randint(2, 4)
        rows = (await session.execute(
            select(m.KnowledgeDimension.id).order_by(func.random()).limit(k)
        )).scalars().all()
        logger.info(f"维度策略: 高分≥{SCORE_THRESHOLD} 抽{len(rows)}个 -> {rows}")
        if rows: return rows
    if req.维度:
        rows = (await session.execute(
            select(m.KnowledgeDimension.id).where(m.KnowledgeDimension.id.in_(req.维度))
        )).scalars().all()
        logger.info(f"维度策略: 使用传入维度过滤 -> {json.dumps(rows, ensure_ascii=False)}")
        if rows: return rows
    rows = (await session.execute(
        select(m.KnowledgeDimension.id).order_by(func.random()).limit(2)
    )).scalars().all()
    logger.warning(f"维度策略: 兜底随机 -> {rows}")
    return rows or [1]

def _fallback_item(req: PracticeRequest, dims: List[int]) -> PracticeItem:
    logger.warning(f"LLM输出异常，启用兜底模板。dims={dims}")
    material = (
        f"【情境材料】在一节中文为第二语言的课堂中，部分学生口语表达缺乏信心，讨论停留在表层。"
        f"教师尝试使用分层提问、同伴互评与即时反馈提升互动质量。关注维度ID：{dims}。"
    )
    core_points = ["明确目标", "分层提问", "即时反馈", "同伴互评"]
    random.shuffle(core_points)
    core_points = core_points[:random.randint(2,4)]
    return PracticeItem(
        材料=_ensure_min_len(material, 150),
        题目="请基于材料指出两个关键教学问题，并提出两条可操作的改进策略（说明原因）。",
        参考答案="要点1：目标可观察；要点2：分层提问+等待时间；要点3：同伴互评+教师反馈闭环；要点4：任务产出检核。",
        评分标准="满分：问题识别准确、策略可操作且对应；部分：能识别问题但策略笼统；不得分：偏题或未作答。",
        维度=dims,
        核心知识点=core_points,
        难度=req.难度,
        题型=req.题型,
        满分=10,
        建议用时=10,
        字数上限=200
    )

async def generate_practice_item(req: PracticeRequest, session: AsyncSession) -> Tuple[PracticeItem, int]:
    dims = await _resolve_dimensions(session, req)
    item: PracticeItem
    try:
        chain = gen_chain()
        t0 = time.perf_counter()
        raw = await chain.ainvoke({"kd_ids": dims, "difficulty": req.难度})
        ms = (time.perf_counter() - t0) * 1000
        logger.info(f"LLM生成完成，用时 {ms:.0f}ms，dims={dims} diff={req.难度}")
        raw.setdefault("维度", dims)
        raw.setdefault("难度", req.难度)
        raw.setdefault("题型", req.题型)
        raw.setdefault("满分", 10)
        raw.setdefault("建议用时", 10)
        item = PracticeItem(**raw)
        if len(item.材料) < 120 or not (2 <= len(item.核心知识点) <= 4):
            raise ValueError("LLM输出不达标")
    except Exception as e:
        logger.exception(f"LLM生成异常: {e}")
        item = _fallback_item(req, dims)

    qid = await insert_question(session, item_json=item.model_dump())
    logger.info(f"入库: question_id={qid} points={json.dumps(item.核心知识点, ensure_ascii=False)}")
    return item, qid
