from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
import logging

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/api/exams/{exam_id}/images")
def get_exam_images(exam_id: int):
    """获取考试答题卡图片列表"""
    # 占位符实现
    return {"code": 1, "msg": "获取成功", "data": []}

@router.post("/api/exams/{exam_id}/images")
async def upload_exam_images(exam_id: int, files: List[UploadFile] = File(...)):
    """上传答题卡图片"""
    # 占位符实现
    return {"code": 1, "msg": "上传成功", "data": {"count": len(files)}}
