from typing import Dict, Any, List
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from .client import chat_completion_json

# 生成链：inputs -> JSON
_generate_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "你是国际教师资格教研专家。基于【维度ID】与【难度】生成一题【简答题】。\n"
     "严格以 JSON 输出（不要任何多余文字）。字段：材料(≥150字)、题目、参考答案、评分标准、维度(维度ID数组)、核心知识点(2-4个短语)、难度(1/2/3)、题型(1)、满分、建议用时、字数上限。"),
    ("user", "维度ID: {kd_ids}\n难度: {difficulty}\n题型: 1\n仅输出JSON。")
])

async def _gen_call(inputs: Dict[str, Any]) -> Dict[str, Any]:
    # 直接构造 OpenAI 兼容的 messages（与测试脚本同）
    sys_msg = _generate_prompt.messages[0].prompt.format()
    user_msg = _generate_prompt.messages[1].prompt.format(**inputs)
    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": user_msg},
    ]
    return await chat_completion_json(messages, temperature=0.2)

def gen_chain():
    return RunnableLambda(_gen_call)

# 评分链：inputs -> JSON
_grade_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "你是严格的阅卷老师。根据【评分标准】与【核心要点】对【作答】评分。\n"
     "只输出 JSON：total_score(0-满分)、subitem_scores(要点->分)、comments、hit_score_points(数组)。"),
    ("user", "满分: {full_score}\n核心要点: {score_points}\n评分标准: {rubric}\n作答: {answer}")
])

async def _grade_call(inputs: Dict[str, Any]) -> Dict[str, Any]:
    sys_msg = _grade_prompt.messages[0].prompt.format()
    user_msg = _grade_prompt.messages[1].prompt.format(**inputs)
    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": user_msg},
    ]
    return await chat_completion_json(messages, temperature=0.0)

def grade_chain():
    return RunnableLambda(_grade_call)
