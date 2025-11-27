from fastapi import APIRouter
import logging

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/api/exams/{exam_id}/grade")
def start_grading(exam_id: int):
    """开始AI阅卷"""
    # 占位符实现
    return {"code": 1, "msg": "阅卷任务已启动", "data": {"task_id": "mock_task_id"}}
