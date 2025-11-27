from fastapi import APIRouter, HTTPException, UploadFile, File, Body
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import text
import logging
import os
import io
import re
import pandas as pd
import docx

from backend.database import engine

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== Pydantic模型定义 ====================

class QuestionRequest(BaseModel):
    question_order: Optional[int] = None
    question_type: Optional[str] = ""
    content: str
    score: float
    reference_answer: str
    scoring_rules: Optional[str] = ""

class QuestionUpdate(BaseModel):
    question_type: Optional[str] = None
    content: Optional[str] = None
    score: Optional[float] = None
    reference_answer: Optional[str] = None
    scoring_rules: Optional[str] = None

# ==================== 题目管理API ====================

@router.post("/api/exams/{exam_id}/questions")
def create_question(exam_id: int, question: QuestionRequest):
    """为考试添加题目"""
    try:
        with engine.connect() as conn:
            # 开启事务
            trans = conn.begin()
            try:
                # 1. 插入题目信息
                result = conn.execute(
                    text("""
                    INSERT INTO questions (type, content, score, reference_answer, scoring_rules)
                    VALUES (:type, :content, :score, :reference_answer, :scoring_rules)
                    """),
                    {
                        "type": question.question_type,
                        "content": question.content,
                        "score": question.score,
                        "reference_answer": question.reference_answer,
                        "scoring_rules": question.scoring_rules
                    }
                )
                question_id = result.lastrowid

                # 2. 插入考试题目关联
                # 如果没有提供序号，则放在最后
                final_order = question.question_order
                if final_order is None:
                    max_order = conn.execute(
                        text("SELECT MAX(question_order) FROM exam_questions WHERE exam_id = :exam_id"),
                        {"exam_id": exam_id}
                    ).scalar()
                    final_order = (max_order or 0) + 1

                conn.execute(
                    text("""
                    INSERT INTO exam_questions (exam_id, question_id, question_order)
                    VALUES (:exam_id, :question_id, :question_order)
                    """),
                    {
                        "exam_id": exam_id,
                        "question_id": question_id,
                        "question_order": final_order
                    }
                )
                
                trans.commit()
                return {"code": 1, "msg": "添加成功", "data": {"question_id": question_id}}
            except Exception as e:
                trans.rollback()
                raise e
    except Exception as e:
        logger.error(f"添加题目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加题目失败: {str(e)}")

@router.get("/api/exams/{exam_id}/questions")
def get_exam_questions(exam_id: int):
    """获取考试题目列表"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT q.*, eq.question_order 
                FROM questions q
                JOIN exam_questions eq ON q.id = eq.question_id
                WHERE eq.exam_id = :exam_id 
                ORDER BY eq.question_order
                """),
                {"exam_id": exam_id}
            )
            questions = []
            for row in result.fetchall():
                q = {
                    "id": row.id,
                    "question_order": row.question_order,
                    "type": row.type,
                    "content": row.content,
                    "score": float(row.score) if row.score is not None else 0,
                    "reference_answer": row.reference_answer,
                    "scoring_rules": row.scoring_rules,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                }
                questions.append(q)

            return {"code": 1, "msg": "获取成功", "data": questions}
    except Exception as e:
        logger.error(f"获取考试题目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取考试题目失败: {str(e)}")

@router.get("/api/exams/{exam_id}/available-questions")
def get_available_questions(exam_id: int, search: Optional[str] = None):
    """获取未分配到该考试的题目列表"""
    try:
        with engine.connect() as conn:
            # 检查考试是否存在
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            # 构建查询条件
            where_clause = "WHERE q.id NOT IN (SELECT eq.question_id FROM exam_questions eq WHERE eq.exam_id = :exam_id)"
            params = {"exam_id": exam_id}

            if search:
                where_clause += " AND (q.content LIKE :search OR q.type LIKE :search)"
                params.update({"search": f"%{search}%"})

            # 获取未分配到该考试的题目
            result = conn.execute(
                text(f"""
                SELECT q.*
                FROM questions q
                {where_clause}
                ORDER BY q.created_at DESC
                """),
                params
            )
            questions = []
            for row in result.fetchall():
                q = {
                    "id": row.id,
                    "type": row.type,
                    "content": row.content,
                    "score": float(row.score) if row.score is not None else 0,
                    "reference_answer": row.reference_answer,
                    "scoring_rules": row.scoring_rules,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                }
                questions.append(q)

            return {"code": 1, "msg": "获取成功", "data": questions}
    except Exception as e:
        logger.error(f"获取可用题目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取可用题目失败: {str(e)}")

@router.post("/api/exams/{exam_id}/add-existing-questions")
def add_existing_questions_to_exam(exam_id: int, question_ids: List[int] = Body(...)):
    """添加已存在的题目到考试"""
    try:
        with engine.connect() as conn:
            # 检查考试是否存在
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            added_count = 0
            
            # 获取当前最大序号
            max_order = conn.execute(
                text("SELECT MAX(question_order) FROM exam_questions WHERE exam_id = :exam_id"),
                {"exam_id": exam_id}
            ).scalar()
            current_order = (max_order or 0) + 1

            for question_id in question_ids:
                try:
                    # 检查题目是否存在
                    question_result = conn.execute(
                        text("SELECT id FROM questions WHERE id = :question_id"),
                        {"question_id": question_id}
                    ).fetchone()

                    if not question_result:
                        continue

                    # 检查是否已经在该考试中
                    existing_relation = conn.execute(
                        text("SELECT 1 FROM exam_questions WHERE exam_id = :exam_id AND question_id = :question_id"),
                        {"exam_id": exam_id, "question_id": question_id}
                    ).fetchone()

                    if existing_relation:
                        continue

                    # 添加题目到考试
                    conn.execute(
                        text("""
                        INSERT INTO exam_questions (exam_id, question_id, question_order)
                        VALUES (:exam_id, :question_id, :question_order)
                        """),
                        {
                            "exam_id": exam_id,
                            "question_id": question_id,
                            "question_order": current_order
                        }
                    )
                    current_order += 1
                    added_count += 1

                except Exception as e:
                    logger.warning(f"添加题目失败 {question_id}: {str(e)}")
                    continue

            conn.commit()

            return {"code": 1, "msg": f"成功添加 {added_count} 道题目", "data": {"added_count": added_count}}
    except Exception as e:
        logger.error(f"添加已存在题目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加已存在题目失败: {str(e)}")

@router.post("/api/exams/{exam_id}/questions/remove-batch")
def remove_questions_batch(exam_id: int, question_ids: List[int] = Body(...)):
    """批量移除题目从考试"""
    try:
        with engine.connect() as conn:
            removed_count = 0
            for question_id in question_ids:
                result = conn.execute(
                    text("DELETE FROM exam_questions WHERE exam_id = :exam_id AND question_id = :question_id"),
                    {"exam_id": exam_id, "question_id": question_id}
                )
                if result.rowcount > 0:
                    removed_count += 1
            
            conn.commit()
            return {"code": 1, "msg": "移除成功", "data": {"removed_count": removed_count}}
    except Exception as e:
        logger.error(f"批量移除题目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量移除题目失败: {str(e)}")

@router.delete("/api/questions/{question_id}")
def delete_question(question_id: int):
    """彻底删除题目"""
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM questions WHERE id = :question_id"), {"question_id": question_id})
            conn.commit()
            return {"code": 1, "msg": "删除成功"}
    except Exception as e:
        logger.error(f"删除题目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除题目失败: {str(e)}")

@router.put("/api/questions/{question_id}")
def update_question(question_id: int, question: QuestionUpdate):
    """更新题目信息"""
    try:
        with engine.connect() as conn:
            # 构建动态更新语句
            update_fields = []
            update_params = {"question_id": question_id}

            if question.question_type is not None:
                update_fields.append("type = :type")
                update_params["type"] = question.question_type
            if question.content is not None:
                update_fields.append("content = :content")
                update_params["content"] = question.content
            if question.score is not None:
                update_fields.append("score = :score")
                update_params["score"] = question.score
            if question.reference_answer is not None:
                update_fields.append("reference_answer = :reference_answer")
                update_params["reference_answer"] = question.reference_answer
            if question.scoring_rules is not None:
                update_fields.append("scoring_rules = :scoring_rules")
                update_params["scoring_rules"] = question.scoring_rules
            
            if not update_fields:
                return {"code": 0, "msg": "没有更新字段"}

            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            query = f"UPDATE questions SET {', '.join(update_fields)} WHERE id = :question_id"
            conn.execute(text(query), update_params)
            conn.commit()

            return {"code": 1, "msg": "更新成功"}
    except Exception as e:
        logger.error(f"更新题目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新题目失败: {str(e)}")

@router.post("/api/exams/{exam_id}/questions/reorder")
def reorder_exam_questions(exam_id: int, question_ids: List[int] = Body(...)):
    """重新排序考试题目"""
    try:
        with engine.connect() as conn:
            # 检查考试是否存在
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")

            # 批量更新排序
            for index, question_id in enumerate(question_ids):
                conn.execute(
                    text("UPDATE exam_questions SET question_order = :question_order WHERE exam_id = :exam_id AND question_id = :question_id"),
                    {"question_order": index + 1, "exam_id": exam_id, "question_id": question_id}
                )
            
            conn.commit()
            return {"code": 1, "msg": "排序更新成功"}
    except Exception as e:
        logger.error(f"更新题目排序失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新题目排序失败: {str(e)}")

@router.post("/api/exams/{exam_id}/import-questions")
async def import_questions_from_file(exam_id: int, file: UploadFile = File(...)):
    """从文件导入题目"""
    try:
        # 验证考试是否存在
        with engine.connect() as conn:
            exam_result = conn.execute(text("SELECT exam_id FROM exams WHERE exam_id = :exam_id"), {"exam_id": exam_id}).fetchone()
            if not exam_result:
                raise HTTPException(status_code=404, detail=f"考试 {exam_id} 不存在")
            
            # 获取当前最大序号，用于追加
            max_order_res = conn.execute(text("SELECT MAX(question_order) FROM exam_questions WHERE exam_id = :exam_id"), {"exam_id": exam_id}).scalar()
            current_max_order = max_order_res if max_order_res is not None else 0

        filename = file.filename.lower()
        file_ext = os.path.splitext(filename)[1]
        content = await file.read()
        questions_to_add = []

        # 定义分隔符
        SEPARATOR = "@@@"

        try:
            if file_ext == '.docx':
                # 处理 Word 文档
                doc = docx.Document(io.BytesIO(content))
                for para in doc.paragraphs:
                    if 'w:drawing' in para._p.xml or 'w:object' in para._p.xml:
                        logger.info(f"跳过包含图片的段落: {para.text[:20]}...")
                        continue

                    text_content = para.text.strip()
                    if not text_content:
                        continue
                    
                    parts = text_content.split(SEPARATOR)
                    parts = [p.strip() for p in parts]
                    
                    if len(parts) < 4:
                        continue

                    try:
                        q_type = ""
                        content_str = ""
                        score = 0.0
                        ref_answer = ""
                        rules = ""

                        # 尝试解析，不再强制要求第一列是序号
                        # 兼容带序号和不带序号的格式
                        # 如果第一列看起来像数字，我们忽略它（使用自动排序），但内容往后移
                        # 如果不是数字，我们假设它不是序号

                        # 简单起见，我们假设用户可能提供序号，也可能不提供
                        # 重要的是提取内容、分值等
                        
                        # 策略：从后往前解析确定字段
                        # [可选序号] [可选题型] 内容 分值 答案 [可选规则] 
                        
                        # 为了简化，我们沿用之前的逻辑但忽略order字段
                        
                        if len(parts) >= 6:
                            # 完整格式：(序号), 题型, 内容, 分值, 答案, 规则
                            q_type = parts[1]
                            content_str = parts[2]
                            score = float(re.sub(r'[^\d.]', '', parts[3]) or 0)
                            ref_answer = parts[4]
                            rules = parts[5]
                        elif len(parts) == 5:
                            # 5个字段: (序号), 题型, 内容, 分值, 答案
                            q_type = parts[1]
                            content_str = parts[2]
                            score = float(re.sub(r'[^\d.]', '', parts[3]) or 0)
                            ref_answer = parts[4]
                        else: # len == 4
                            # 4个字段: (序号), 内容, 分值, 答案 (无题型)
                            content_str = parts[1]
                            score = float(re.sub(r'[^\d.]', '', parts[2]) or 0)
                            ref_answer = parts[3]
                        
                        if not content_str or score <= 0:
                            continue

                        type_map = {
                            "选择题": "choice", "选择": "choice",
                            "填空题": "fill_blank", "填空": "fill_blank",
                            "主观题": "essay", "简答题": "essay", "解答题": "essay", "问答题": "essay",
                            "计算题": "calculation", "计算": "calculation",
                            "判断题": "true_false", "判断": "true_false"
                        }
                        final_type = type_map.get(q_type, q_type if q_type else "essay")

                        questions_to_add.append({
                            "question_type": final_type,
                            "content": content_str,
                            "score": score,
                            "reference_answer": ref_answer,
                            "scoring_rules": rules
                        })

                    except ValueError:
                        continue

            elif file_ext in {'.xlsx', '.xls'}:
                # 处理 Excel
                df = pd.read_excel(io.BytesIO(content))
                for _, row in df.iterrows():
                    # 至少要有内容, 分值
                    if pd.isna(row.iloc[2]) or pd.isna(row.iloc[3]):
                        continue
                    
                    # 忽略第一列序号 row.iloc[0]
                    
                    raw_type = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                    type_map = {
                            "选择题": "choice", "选择": "choice",
                            "填空题": "fill_blank", "填空": "fill_blank",
                            "主观题": "essay", "简答题": "essay", "解答题": "essay", "问答题": "essay",
                            "计算题": "calculation", "计算": "calculation",
                            "判断题": "true_false", "判断": "true_false"
                    }
                    final_type = type_map.get(raw_type, raw_type if raw_type else "essay")

                    questions_to_add.append({
                        "question_type": final_type,
                        "content": str(row.iloc[2]),
                        "score": float(row.iloc[3]),
                        "reference_answer": str(row.iloc[4]),
                        "scoring_rules": str(row.iloc[5]) if len(row) > 5 and pd.notna(row.iloc[5]) else ""
                    })

            elif file_ext in {'.txt', '.csv'}:
                # 处理文本/CSV
                text_content = content.decode('utf-8')
                lines = text_content.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    
                    parts = line.split(SEPARATOR)
                    parts = [p.strip() for p in parts]
                    
                    if len(parts) < 4: continue
                    
                    try:
                        q_type = ""
                        content_str = ""
                        score = 0.0
                        ref_answer = ""
                        rules = ""

                        if len(parts) >= 6:
                            q_type = parts[1]
                            content_str = parts[2]
                            score = float(re.sub(r'[^\d.]', '', parts[3]) or 0)
                            ref_answer = parts[4]
                            rules = parts[5]
                        elif len(parts) == 5:
                            q_type = parts[1]
                            content_str = parts[2]
                            score = float(re.sub(r'[^\d.]', '', parts[3]) or 0)
                            ref_answer = parts[4]
                        else:
                            content_str = parts[1]
                            score = float(re.sub(r'[^\d.]', '', parts[2]) or 0)
                            ref_answer = parts[3]
                            
                        type_map = {
                            "选择题": "choice", "选择": "choice",
                            "填空题": "fill_blank", "填空": "fill_blank",
                            "主观题": "essay", "简答题": "essay", "解答题": "essay", "问答题": "essay",
                            "计算题": "calculation", "计算": "calculation",
                            "判断题": "true_false", "判断": "true_false"
                        }
                        final_type = type_map.get(q_type, q_type if q_type else "essay")

                        questions_to_add.append({
                            "question_type": final_type,
                            "content": content_str,
                            "score": score,
                            "reference_answer": ref_answer,
                            "scoring_rules": rules
                        })
                    except:
                        continue
            else:
                raise HTTPException(status_code=400, detail="不支持的文件格式")

        except Exception as parse_error:
            logger.error(f"解析文件失败: {str(parse_error)}")
            raise HTTPException(status_code=400, detail=f"解析文件失败: {str(parse_error)}")

        if not questions_to_add:
            raise HTTPException(status_code=400, detail="未解析到有效题目数据")

        imported_count = 0
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                for q in questions_to_add:
                    current_max_order += 1
                    
                    # 插入题目
                    res = conn.execute(
                        text("""
                        INSERT INTO questions (type, content, score, reference_answer, scoring_rules)
                        VALUES (:type, :content, :score, :reference_answer, :scoring_rules)
                        """),
                        {
                            "type": q["question_type"],
                            "content": q["content"],
                            "score": q["score"],
                            "reference_answer": q["reference_answer"],
                            "scoring_rules": q["scoring_rules"]
                        }
                    )
                    qid = res.lastrowid
                    
                    # 插入关联
                    conn.execute(
                        text("""
                        INSERT INTO exam_questions (exam_id, question_id, question_order)
                        VALUES (:exam_id, :question_id, :question_order)
                        """),
                        {
                            "exam_id": exam_id,
                            "question_id": qid,
                            "question_order": current_max_order
                        }
                    )
                    imported_count += 1
                
                trans.commit()
            except Exception as db_err:
                trans.rollback()
                raise db_err

        return {"code": 1, "msg": f"成功导入 {imported_count} 道题目", "data": {"count": imported_count}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入题目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导入题目失败: {str(e)}")
