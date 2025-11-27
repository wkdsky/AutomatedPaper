from fastapi import APIRouter
import logging

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/api/exams/{exam_id}/scores")
def get_exam_scores(exam_id: int):
    """获取考试成绩"""
    # 占位符实现
    return {"code": 1, "msg": "获取成功", "data": []}
