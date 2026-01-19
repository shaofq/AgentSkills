# -*- coding: utf-8 -*-
"""
智能文档学习与规则生成服务
"""
import os
import re
import json
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from openai import OpenAI

from api.models.hazmat import (
    DocumentType, LearningStatus, AnnotationType, HazmatResult,
    AIHighlight, Annotation, RuleDraft, RuleDraftCondition,
    LearningDocumentResponse, PreprocessResponse, GenerateRulesResponse
)


class LearningService:
    """智能文档学习服务"""
    
    def __init__(self, db_path: str = "data/hazmat.db", upload_dir: str = "data/learning_uploads"):
        self.db_path = db_path
        self.upload_dir = upload_dir
        self.llm_client = None
        self.llm_model = "qwen-plus"
        
        # 确保上传目录存在
        os.makedirs(upload_dir, exist_ok=True)
        
        # 初始化数据库表
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 学习文档表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                doc_type TEXT DEFAULT 'other',
                status TEXT DEFAULT 'uploading',
                raw_text TEXT,
                ai_highlights TEXT,
                annotations TEXT,
                judgment TEXT,
                created_at TEXT,
                created_by TEXT,
                updated_at TEXT
            )
        ''')
        
        # 规则草稿表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                conditions TEXT NOT NULL,
                result TEXT NOT NULL,
                suggested_class TEXT,
                source_file_id INTEGER,
                status TEXT DEFAULT 'draft',
                created_at TEXT,
                created_by TEXT,
                reviewed_at TEXT,
                reviewed_by TEXT,
                reject_reason TEXT,
                FOREIGN KEY (source_file_id) REFERENCES learning_documents(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def set_llm_client(self, client: OpenAI, model: str = "qwen-plus"):
        """设置LLM客户端"""
        self.llm_client = client
        self.llm_model = model
    
    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    # ========== 文档管理 ==========
    
    def upload_document(self, filename: str, file_content: bytes, 
                       doc_type: DocumentType, created_by: str = None) -> int:
        """上传学习文档"""
        # 保存文件
        file_path = os.path.join(self.upload_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}")
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # 保存到数据库
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO learning_documents 
            (filename, file_path, file_size, doc_type, status, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (filename, file_path, len(file_content), doc_type.value, 
              LearningStatus.UPLOADING.value, datetime.now().isoformat(), created_by))
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return doc_id
    
    def get_document(self, doc_id: int) -> Optional[LearningDocumentResponse]:
        """获取学习文档"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM learning_documents WHERE id = ?', (doc_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_document(row)
    
    def _row_to_document(self, row) -> LearningDocumentResponse:
        """将数据库行转换为文档响应"""
        return LearningDocumentResponse(
            id=row[0],
            filename=row[1],
            file_size=row[3],
            doc_type=DocumentType(row[4]),
            status=LearningStatus(row[5]),
            raw_text=row[6],
            ai_highlights=json.loads(row[7]) if row[7] else None,
            annotations=json.loads(row[8]) if row[8] else None,
            judgment=HazmatResult(row[9]) if row[9] else None,
            rule_drafts=None,  # 需要单独查询
            created_at=row[10],
            created_by=row[11],
            updated_at=row[12]
        )
    
    def update_document_status(self, doc_id: int, status: LearningStatus):
        """更新文档状态"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE learning_documents 
            SET status = ?, updated_at = ?
            WHERE id = ?
        ''', (status.value, datetime.now().isoformat(), doc_id))
        conn.commit()
        conn.close()
    
    # ========== AI预处理 ==========
    
    def preprocess_document(self, doc_id: int) -> PreprocessResponse:
        """AI预处理文档：提取文本并识别关键信息"""
        # 获取文档
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM learning_documents WHERE id = ?', (doc_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"文档不存在: {doc_id}")
        file_path = row[0]
        conn.close()
        
        # 更新状态为预处理中
        self.update_document_status(doc_id, LearningStatus.PREPROCESSING)
        
        # 提取文本
        raw_text = self._extract_text(file_path)
        
        # AI识别关键信息
        ai_highlights = self._ai_recognize_entities(raw_text)
        
        # 保存结果
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE learning_documents 
            SET raw_text = ?, ai_highlights = ?, status = ?, updated_at = ?
            WHERE id = ?
        ''', (raw_text, json.dumps([h.dict() for h in ai_highlights]), 
              LearningStatus.ANNOTATING.value, datetime.now().isoformat(), doc_id))
        conn.commit()
        conn.close()
        
        return PreprocessResponse(
            file_id=doc_id,
            raw_text=raw_text,
            ai_highlights=ai_highlights,
            status=LearningStatus.ANNOTATING
        )
    
    def _extract_text(self, file_path: str) -> str:
        """从文件提取文本"""
        import fitz  # PyMuPDF
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            # 如果文本太少，尝试OCR
            if len(text.strip()) < 100:
                text = self._ocr_document(file_path)
            
            return text
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            return self._ocr_document(file_path)
        else:
            # 尝试作为文本文件读取
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return ""
    
    def _ocr_document(self, file_path: str) -> str:
        """OCR识别文档"""
        try:
            import pytesseract
            from PIL import Image
            import fitz
            import io
            
            ext = os.path.splitext(file_path)[1].lower()
            all_text = []
            
            if ext == '.pdf':
                doc = fitz.open(file_path)
                for page_num in range(min(len(doc), 10)):
                    page = doc[page_num]
                    mat = fitz.Matrix(150/72, 150/72)
                    pix = page.get_pixmap(matrix=mat)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    try:
                        text = pytesseract.image_to_string(img, lang='eng+chi_sim')
                        if text.strip():
                            all_text.append(text)
                    except:
                        pass
                doc.close()
            else:
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img, lang='eng+chi_sim')
                all_text.append(text)
            
            return "\n".join(all_text)
        except Exception as e:
            print(f"[LearningService] OCR失败: {e}")
            return ""
    
    def _ai_recognize_entities(self, text: str) -> List[AIHighlight]:
        """AI识别文本中的关键实体"""
        highlights = []
        
        # 1. 使用正则表达式识别常见模式
        highlights.extend(self._regex_recognize(text))
        
        # 2. 使用LLM进行智能识别
        if self.llm_client and len(text) > 50:
            try:
                llm_highlights = self._llm_recognize(text)
                # 合并结果，避免重复
                existing_spans = {(h.start, h.end) for h in highlights}
                for h in llm_highlights:
                    if (h.start, h.end) not in existing_spans:
                        highlights.append(h)
            except Exception as e:
                print(f"[LearningService] LLM识别失败: {e}")
        
        # 按位置排序
        highlights.sort(key=lambda x: x.start)
        
        return highlights
    
    def _regex_recognize(self, text: str) -> List[AIHighlight]:
        """使用正则表达式识别常见模式"""
        highlights = []
        
        patterns = [
            # CAS号
            (r'\b(\d{2,7}-\d{2}-\d)\b', AnnotationType.CAS_NUMBER, 0.9),
            # UN编号
            (r'\b(UN\s*\d{4})\b', AnnotationType.UN_NUMBER, 0.95),
            # 闪点
            (r'(?:闪点|Flash\s*Point)[:\s：]*([<>]?\s*-?\d+(?:\.\d+)?)\s*[°℃]?C?', AnnotationType.FLASH_POINT, 0.85),
            # 沸点
            (r'(?:沸点|Boiling\s*Point)[:\s：]*([<>]?\s*-?\d+(?:\.\d+)?)\s*[°℃]?C?', AnnotationType.BOILING_POINT, 0.85),
            # pH值
            (r'(?:pH|pH值)[:\s：]*(\d+(?:\.\d+)?)', AnnotationType.PH_VALUE, 0.8),
            # 包装组
            (r'(?:包装组|Packing\s*Group|PG)[:\s：]*(I{1,3}|[123])', AnnotationType.PACKING_GROUP, 0.9),
            # 危险性关键词
            (r'\b(易燃|Flammable|高度易燃|Highly\s*Flammable)\b', AnnotationType.HAZARD_KEYWORD, 0.85),
            (r'\b(腐蚀性|Corrosive|强腐蚀性)\b', AnnotationType.HAZARD_KEYWORD, 0.85),
            (r'\b(有毒|Toxic|剧毒|Highly\s*Toxic)\b', AnnotationType.HAZARD_KEYWORD, 0.85),
            (r'\b(爆炸|Explosive|易爆)\b', AnnotationType.HAZARD_KEYWORD, 0.85),
            (r'\b(氧化|Oxidizing|氧化性)\b', AnnotationType.HAZARD_KEYWORD, 0.85),
            (r'\b(刺激|Irritant|刺激性)\b', AnnotationType.HAZARD_KEYWORD, 0.8),
            # 信号词
            (r'\b(危险|Danger|警告|Warning)\b', AnnotationType.HAZARD_KEYWORD, 0.9),
            # 法规引用
            (r'\b(IATA\s*DGR|IMDG\s*Code|GB\s*\d+|DOT\s*\d+)', AnnotationType.REGULATION_REF, 0.85),
        ]
        
        for pattern, entity_type, confidence in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                highlights.append(AIHighlight(
                    text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    entity_type=entity_type,
                    confidence=confidence,
                    suggested_value=match.group(1) if match.lastindex else match.group(0)
                ))
        
        return highlights
    
    def _llm_recognize(self, text: str) -> List[AIHighlight]:
        """使用LLM识别实体"""
        if not self.llm_client:
            return []
        
        # 截取前8000字符避免超长
        text_sample = text[:8000] if len(text) > 8000 else text
        
        prompt = f"""请分析以下文档内容，识别出与危险品相关的关键信息。

对于每个识别出的信息，请返回：
- text: 原文中的文本片段
- type: 信息类型（product_name/cas_number/un_number/flash_point/boiling_point/hazard_class/packing_group/hazard_keyword/regulation_ref）
- value: 提取的值（如闪点数值、CAS号等）
- confidence: 置信度（0-1）

请以JSON数组格式返回，例如：
[
  {{"text": "闪点: 23°C", "type": "flash_point", "value": "23", "confidence": 0.9}},
  {{"text": "苯", "type": "product_name", "value": "苯", "confidence": 0.8}}
]

文档内容：
{text_sample}

请只返回JSON数组，不要其他说明。"""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            # 提取JSON
            json_match = re.search(r'\[[\s\S]*\]', result_text)
            if json_match:
                items = json.loads(json_match.group())
                highlights = []
                for item in items:
                    # 在原文中查找位置
                    text_to_find = item.get('text', '')
                    start = text.find(text_to_find)
                    if start >= 0:
                        entity_type = self._map_type(item.get('type', ''))
                        if entity_type:
                            highlights.append(AIHighlight(
                                text=text_to_find,
                                start=start,
                                end=start + len(text_to_find),
                                entity_type=entity_type,
                                confidence=item.get('confidence', 0.7),
                                suggested_value=item.get('value')
                            ))
                return highlights
        except Exception as e:
            print(f"[LearningService] LLM识别解析失败: {e}")
        
        return []
    
    def _map_type(self, type_str: str) -> Optional[AnnotationType]:
        """映射类型字符串到枚举"""
        mapping = {
            'product_name': AnnotationType.PRODUCT_NAME,
            'cas_number': AnnotationType.CAS_NUMBER,
            'un_number': AnnotationType.UN_NUMBER,
            'flash_point': AnnotationType.FLASH_POINT,
            'boiling_point': AnnotationType.BOILING_POINT,
            'hazard_class': AnnotationType.HAZARD_CLASS,
            'packing_group': AnnotationType.PACKING_GROUP,
            'ph_value': AnnotationType.PH_VALUE,
            'explosion_limit': AnnotationType.EXPLOSION_LIMIT,
            'hazard_keyword': AnnotationType.HAZARD_KEYWORD,
            'regulation_ref': AnnotationType.REGULATION_REF,
        }
        return mapping.get(type_str.lower())
    
    # ========== 标注管理 ==========
    
    def save_annotations(self, doc_id: int, annotations: List[Annotation], 
                        judgment: HazmatResult, created_by: str = None):
        """保存用户标注"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE learning_documents 
            SET annotations = ?, judgment = ?, status = ?, updated_at = ?
            WHERE id = ?
        ''', (json.dumps([a.dict() for a in annotations]), judgment.value,
              LearningStatus.GENERATING.value, datetime.now().isoformat(), doc_id))
        conn.commit()
        conn.close()
    
    # ========== 规则生成 ==========
    
    def generate_rules(self, doc_id: int, basis_fields: List[str], 
                      created_by: str = None) -> GenerateRulesResponse:
        """根据标注生成规则草稿"""
        # 获取文档
        doc = self.get_document(doc_id)
        if not doc:
            raise ValueError(f"文档不存在: {doc_id}")
        
        if not doc.annotations:
            raise ValueError("文档尚未标注")
        
        # 获取作为判断依据的标注
        basis_annotations = [a for a in doc.annotations if a.get('field') in basis_fields or a.get('is_basis')]
        
        if not basis_annotations:
            basis_annotations = doc.annotations[:3]  # 默认取前3个
        
        # 生成规则草稿
        rule_drafts = []
        
        for ann in basis_annotations:
            field = ann.get('field', '')
            value = ann.get('value', '')
            
            if not field or not value:
                continue
            
            rule = self._generate_rule_for_annotation(doc_id, field, value, doc.judgment, created_by)
            if rule:
                rule_drafts.append(rule)
        
        # 保存规则草稿
        for rule in rule_drafts:
            self._save_rule_draft(rule)
        
        # 更新文档状态
        self.update_document_status(doc_id, LearningStatus.PENDING_REVIEW)
        
        return GenerateRulesResponse(
            file_id=doc_id,
            rule_drafts=rule_drafts
        )
    
    def _generate_rule_for_annotation(self, doc_id: int, field: str, value: str, 
                                     judgment: HazmatResult, created_by: str) -> Optional[RuleDraft]:
        """为单个标注生成规则"""
        conditions = []
        name = ""
        description = ""
        suggested_class = None
        
        if field == 'flash_point':
            # 闪点规则：提取数值并判断
            num_match = re.search(r'[-]?\d+(?:\.\d+)?', value)
            if num_match:
                num_value = float(num_match.group())
                if num_value < 60:
                    conditions.append(RuleDraftCondition(
                        field="flash_point",
                        operator="lt",
                        value="60",
                        description=f"闪点 ({value}) 小于 60°C"
                    ))
                    name = "闪点低于60°C规则"
                    description = f"当文档中检测到闪点低于60°C时，判定为危险品（易燃液体）"
                    suggested_class = "3 (易燃液体)"
        
        elif field == 'cas_number':
            conditions.append(RuleDraftCondition(
                field="cas_number",
                operator="equals",
                value=value,
                description=f"CAS号等于 {value}"
            ))
            name = f"CAS号 {value} 规则"
            description = f"当文档中检测到CAS号 {value} 时，判定为危险品"
        
        elif field == 'un_number':
            conditions.append(RuleDraftCondition(
                field="un_number",
                operator="contains",
                value=value.replace('UN', '').strip(),
                description=f"包含UN编号 {value}"
            ))
            name = f"UN编号 {value} 规则"
            description = f"当文档中检测到UN编号 {value} 时，判定为危险品"
        
        elif field == 'hazard_keyword':
            conditions.append(RuleDraftCondition(
                field="text",
                operator="contains",
                value=value,
                description=f"文档包含关键词 \"{value}\""
            ))
            name = f"关键词 \"{value}\" 规则"
            description = f"当文档中包含危险性关键词 \"{value}\" 时，判定为危险品"
        
        elif field == 'packing_group':
            conditions.append(RuleDraftCondition(
                field="packing_group",
                operator="equals",
                value=value,
                description=f"包装组为 {value}"
            ))
            name = f"包装组 {value} 规则"
            description = f"当文档中检测到包装组 {value} 时，判定为危险品"
        
        else:
            # 通用规则：文本包含
            conditions.append(RuleDraftCondition(
                field="text",
                operator="contains",
                value=value,
                description=f"文档包含 \"{value}\""
            ))
            name = f"包含 \"{value}\" 规则"
            description = f"当文档中包含 \"{value}\" 时，判定为危险品"
        
        if conditions:
            return RuleDraft(
                name=name,
                description=description,
                conditions=conditions,
                result=judgment,
                suggested_class=suggested_class,
                source_file_id=doc_id,
                created_by=created_by,
                status="pending_review"
            )
        
        return None
    
    def _save_rule_draft(self, rule: RuleDraft) -> int:
        """保存规则草稿"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO rule_drafts 
            (name, description, conditions, result, suggested_class, source_file_id, status, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (rule.name, rule.description, json.dumps([c.dict() for c in rule.conditions]),
              rule.result.value, rule.suggested_class, rule.source_file_id, 
              rule.status, datetime.now().isoformat(), rule.created_by))
        rule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        rule.id = rule_id
        return rule_id
    
    # ========== 规则审核 ==========
    
    def get_pending_rules(self) -> List[RuleDraft]:
        """获取待审核的规则"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT rd.*, ld.filename 
            FROM rule_drafts rd
            LEFT JOIN learning_documents ld ON rd.source_file_id = ld.id
            WHERE rd.status = 'pending_review'
            ORDER BY rd.created_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        rules = []
        for row in rows:
            rules.append(RuleDraft(
                id=row[0],
                name=row[1],
                description=row[2],
                conditions=[RuleDraftCondition(**c) for c in json.loads(row[3])],
                result=HazmatResult(row[4]),
                suggested_class=row[5],
                source_file_id=row[6],
                status=row[7],
                created_by=row[9]
            ))
        
        return rules
    
    def review_rule(self, rule_id: int, action: str, reviewed_by: str,
                   edited_rule: RuleDraft = None, reason: str = None) -> bool:
        """审核规则"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        if action == 'approve':
            # 批准：将规则添加到主规则库
            cursor.execute('SELECT * FROM rule_drafts WHERE id = ?', (rule_id,))
            row = cursor.fetchone()
            if row:
                conditions = json.loads(row[3])
                # 取第一个条件作为主规则
                if conditions:
                    cond = conditions[0]
                    cursor.execute('''
                        INSERT INTO rules 
                        (name, description, rule_type, condition_field, condition_operator, 
                         condition_value, result, is_active, priority, created_at, created_by)
                        VALUES (?, ?, 'custom', ?, ?, ?, ?, 1, 50, ?, ?)
                    ''', (row[1], row[2], cond['field'], cond['operator'], cond['value'],
                          row[4], datetime.now().isoformat(), reviewed_by))
                
                # 更新草稿状态
                cursor.execute('''
                    UPDATE rule_drafts 
                    SET status = 'approved', reviewed_at = ?, reviewed_by = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), reviewed_by, rule_id))
        
        elif action == 'reject':
            cursor.execute('''
                UPDATE rule_drafts 
                SET status = 'rejected', reviewed_at = ?, reviewed_by = ?, reject_reason = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), reviewed_by, reason, rule_id))
        
        elif action == 'edit' and edited_rule:
            cursor.execute('''
                UPDATE rule_drafts 
                SET name = ?, description = ?, conditions = ?, result = ?, 
                    suggested_class = ?, updated_at = ?
                WHERE id = ?
            ''', (edited_rule.name, edited_rule.description, 
                  json.dumps([c.dict() for c in edited_rule.conditions]),
                  edited_rule.result.value, edited_rule.suggested_class,
                  datetime.now().isoformat(), rule_id))
        
        conn.commit()
        conn.close()
        return True
    
    def get_all_rule_drafts(self, status: str = None) -> List[Dict]:
        """获取所有规则草稿"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        if status:
            cursor.execute('''
                SELECT rd.*, ld.filename 
                FROM rule_drafts rd
                LEFT JOIN learning_documents ld ON rd.source_file_id = ld.id
                WHERE rd.status = ?
                ORDER BY rd.created_at DESC
            ''', (status,))
        else:
            cursor.execute('''
                SELECT rd.*, ld.filename 
                FROM rule_drafts rd
                LEFT JOIN learning_documents ld ON rd.source_file_id = ld.id
                ORDER BY rd.created_at DESC
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'conditions': json.loads(row[3]),
                'result': row[4],
                'suggested_class': row[5],
                'source_file_id': row[6],
                'status': row[7],
                'created_at': row[8],
                'created_by': row[9],
                'reviewed_at': row[10],
                'reviewed_by': row[11],
                'reject_reason': row[12],
                'source_filename': row[13] if len(row) > 13 else None
            })
        
        return results


# 单例
learning_service = LearningService()
