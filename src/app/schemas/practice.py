from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# 约定：1=初级,2=中级,3=高级；1=简答题,2=教学设计题
Difficulty = Literal[1, 2, 3]
QType = Literal[1, 2]

class PracticeRequest(BaseModel):
    得分: Optional[int] = Field(None, ge=0, le=10, description="上一题得分；首次练习可为空")
    维度: List[int] = Field(..., min_items=1, description="知识维度ID列表（kd_id）")
    难度: Difficulty = Field(..., description="1=初级,2=中级,3=高级")
    题型: QType = Field(..., description="1=简答题,2=教学设计题")
    user_id: Optional[int] = Field(None, description="可选，用户ID")

    model_config = {
        "json_schema_extra": {
        "example": {
            "得分": None,
            "维度": [101, 103],
            "难度": 1,
            "题型": 1,
            "user_id": 10001
        }
    }
    }

class PracticeItem(BaseModel):
    材料: str = Field(..., description="题面材料，≥150字")
    题目: str = Field(..., description="题干/问题")
    参考答案: str = Field(..., description="要点式参考答案")
    评分标准: str = Field(..., description="满分/部分/不得分分档标准")
    维度: List[int] = Field(..., description="本题实际使用的维度ID")
    核心知识点: List[str] = Field(..., min_items=2, max_items=4, description="2-4个关键要点")
    难度: Difficulty
    题型: QType
    满分: int = Field(10, ge=1, description="本题满分，默认10")
    建议用时: int = Field(10, ge=1, description="建议作答时间（分钟）")
    字数上限: Optional[int] = Field(None, ge=1, description="可选，字数上限")

    model_config = {
        "json_schema_extra": {
            "example": {
                "材料": "在新班级中，中文作为第二语言课堂上，学生……（示例）",
                "题目": "请分析材料中教师面临的关键问题，并提出两条可操作的改进建议。",
                "参考答案": "要点1：……；要点2：……；要点3：……",
                "评分标准": "满分：覆盖关键要点且论证充分；部分：覆盖部分要点；零分：偏题或未作答。",
                "维度": [101, 106],
                "核心知识点": ["问题识别与聚焦", "课堂提问设计"],
                "难度": 1,
                "题型": 1,
                "满分": 10,
                "建议用时": 10,
                "字数上限": 200
            }
        }
    }

class GenerateResponse(BaseModel):
    question_id: int = Field(..., example=50001)
    item: PracticeItem

class AnswerRequest(BaseModel):
    question_id: int = Field(..., description="题目ID")
    original_answer: str = Field(..., min_length=1, description="用户作答文本")
    user_id: Optional[int] = Field(None, description="可选，用户ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "question_id": 50001,
                "original_answer": "我认为材料中的关键问题是……因此应当……（示例作答）",
                "user_id": 10001
            }
        }
    }

class AnswerResponse(BaseModel):
    answer_record_id: int = Field(..., example=70001)
    total_score: float = Field(..., ge=0, description="总分")
    subitem_scores: Optional[dict] = Field(
        None, description="要点级得分（字典或数组），例如：{\"要点1\": 3, \"要点2\": 2}"
    )
    dimension_scores: Optional[dict] = Field(None, description="按维度得分（可选）")
    comments: Optional[str] = Field(None, description="机评评语")
    hit_score_points: Optional[list] = Field(None, description="命中要点列表")

class ErrorResponse(BaseModel):
    code: int = Field(..., example=40001)
    message: str = Field(..., example="参数校验失败")
