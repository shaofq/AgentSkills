# -*- coding: utf-8 -*-
"""
危险品识别系统数据模型
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ProcessStatus(str, Enum):
    """处理状态"""
    PENDING = "pending"        # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"    # 处理完成
    CONFIRMED = "confirmed"    # 已确认
    ERROR = "error"           # 处理错误


class HazmatResult(str, Enum):
    """危险品判断结果"""
    HAZARDOUS = "hazardous"       # 是危险品
    NON_HAZARDOUS = "non_hazardous"  # 非危险品
    UNCERTAIN = "uncertain"       # 待确认


# ========== SDS文件相关 ==========

class SDSFileBase(BaseModel):
    """SDS文件基础信息"""
    filename: str
    file_size: int = 0


class SDSFileCreate(SDSFileBase):
    """创建SDS文件"""
    pass


class SDSFileResponse(SDSFileBase):
    """SDS文件响应"""
    id: int
    status: ProcessStatus
    result: Optional[HazmatResult] = None
    confidence: Optional[float] = None
    extracted_info: Optional[Dict[str, Any]] = None
    matched_rules: Optional[List[Dict[str, Any]]] = None
    created_at: str
    updated_at: Optional[str] = None
    confirmed_at: Optional[str] = None
    confirmed_by: Optional[str] = None


# ========== 提取的关键信息 ==========

class ExtractedInfo(BaseModel):
    """从SDS文件提取的关键信息"""
    product_name: Optional[str] = None          # 产品名称
    cas_number: Optional[str] = None            # CAS号
    hazard_class: Optional[List[str]] = None    # GHS危险性类别
    pictograms: Optional[List[str]] = None      # 象形图
    signal_word: Optional[str] = None           # 信号词 (危险/警告)
    un_number: Optional[str] = None             # 联合国编号
    proper_shipping_name: Optional[str] = None  # 运输专用名称
    hazard_statements: Optional[List[str]] = None  # 危险性说明
    precautionary_statements: Optional[List[str]] = None  # 防范说明
    raw_text_section2: Optional[str] = None     # 第2节原文
    raw_text_section14: Optional[str] = None    # 第14节原文


class ExtractedInfoUpdate(BaseModel):
    """人工修正提取的信息"""
    field_name: str
    old_value: Optional[str] = None
    new_value: str


# ========== 规则相关 ==========

class RuleType(str, Enum):
    """规则类型"""
    BUILTIN = "builtin"   # 内置规则
    CUSTOM = "custom"     # 用户自定义规则


class RuleBase(BaseModel):
    """规则基础信息"""
    name: str
    description: Optional[str] = None
    condition_field: str      # 判断字段
    condition_operator: str   # 操作符: contains, equals, exists, regex
    condition_value: str      # 判断值
    result: HazmatResult = HazmatResult.HAZARDOUS  # 匹配后结果


class RuleCreate(RuleBase):
    """创建规则"""
    pass


class RuleResponse(RuleBase):
    """规则响应"""
    id: int
    rule_type: RuleType
    is_active: bool = True
    priority: int = 100
    created_at: str
    created_by: Optional[str] = None


class RuleUpdate(BaseModel):
    """更新规则"""
    name: Optional[str] = None
    description: Optional[str] = None
    condition_field: Optional[str] = None
    condition_operator: Optional[str] = None
    condition_value: Optional[str] = None
    result: Optional[HazmatResult] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None


# ========== 分析请求/响应 ==========

class AnalyzeRequest(BaseModel):
    """分析请求"""
    file_id: int
    use_llm: bool = True  # 是否使用大模型增强


class AnalyzeResponse(BaseModel):
    """分析响应"""
    file_id: int
    result: HazmatResult
    confidence: float
    extracted_info: ExtractedInfo
    matched_rules: List[Dict[str, Any]]
    suggestions: Optional[List[str]] = None


class ConfirmRequest(BaseModel):
    """确认请求"""
    file_id: int
    result: HazmatResult
    corrections: Optional[List[ExtractedInfoUpdate]] = None
    create_rule: bool = False  # 是否根据修正创建新规则
    rule_name: Optional[str] = None


# ========== 历史查询 ==========

class HistoryQuery(BaseModel):
    """历史查询参数"""
    keyword: Optional[str] = None
    status: Optional[ProcessStatus] = None
    result: Optional[HazmatResult] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    page: int = 1
    page_size: int = 20


# ========== 智能文档学习与规则生成器 ==========

class DocumentType(str, Enum):
    """文档类型"""
    SDS = "sds"              # 标准SDS/MSDS文档
    OTHER = "other"          # 其他文档（技术规格书、检测报告等）


class LearningStatus(str, Enum):
    """学习文档处理状态"""
    UPLOADING = "uploading"      # 上传中
    PREPROCESSING = "preprocessing"  # AI预处理中
    ANNOTATING = "annotating"    # 待标注
    GENERATING = "generating"    # 规则生成中
    PENDING_REVIEW = "pending_review"  # 待审核
    APPROVED = "approved"        # 已批准
    REJECTED = "rejected"        # 已拒绝
    COMPLETED = "completed"      # 已完成


class AnnotationType(str, Enum):
    """标注实体类型"""
    PRODUCT_NAME = "product_name"      # 产品名称
    CAS_NUMBER = "cas_number"          # CAS号
    UN_NUMBER = "un_number"            # UN编号
    FLASH_POINT = "flash_point"        # 闪点
    BOILING_POINT = "boiling_point"    # 沸点
    HAZARD_CLASS = "hazard_class"      # 危险类别
    PACKING_GROUP = "packing_group"    # 包装组
    PH_VALUE = "ph_value"              # pH值
    EXPLOSION_LIMIT = "explosion_limit"  # 爆炸极限
    HAZARD_KEYWORD = "hazard_keyword"  # 危险性关键词
    REGULATION_REF = "regulation_ref"  # 法规引用


class AIHighlight(BaseModel):
    """AI预识别高亮"""
    text: str                          # 高亮文本
    start: int                         # 起始位置
    end: int                           # 结束位置
    entity_type: AnnotationType        # 实体类型
    confidence: float = 0.0            # 置信度
    suggested_value: Optional[str] = None  # 建议值（如提取的数值）


class Annotation(BaseModel):
    """用户标注"""
    field: AnnotationType              # 标注字段
    value: str                         # 标注值
    text_span: str                     # 原文中的文本片段
    start: int                         # 起始位置
    end: int                           # 结束位置
    is_basis: bool = False             # 是否作为判断依据


class RuleDraftCondition(BaseModel):
    """规则草稿条件"""
    field: str                         # 字段名
    operator: str                      # 操作符: contains, equals, exists, regex, lt, gt, le, ge
    value: str                         # 匹配值
    description: str                   # 人类可读描述


class RuleDraft(BaseModel):
    """规则草稿"""
    id: Optional[int] = None
    name: str                          # 规则名称
    description: str                   # 规则描述
    conditions: List[RuleDraftCondition]  # 条件列表（AND关系）
    result: HazmatResult               # 判定结果
    suggested_class: Optional[str] = None  # 建议的危险类别
    source_file_id: int                # 来源文件ID
    created_by: Optional[str] = None   # 创建人
    status: str = "draft"              # draft/pending_review/approved/rejected


class LearningDocumentCreate(BaseModel):
    """创建学习文档"""
    filename: str
    doc_type: DocumentType = DocumentType.OTHER


class LearningDocumentResponse(BaseModel):
    """学习文档响应"""
    id: int
    filename: str
    file_size: int
    doc_type: DocumentType
    status: LearningStatus
    raw_text: Optional[str] = None
    ai_highlights: Optional[List[AIHighlight]] = None
    annotations: Optional[List[Annotation]] = None
    judgment: Optional[HazmatResult] = None
    rule_drafts: Optional[List[RuleDraft]] = None
    created_at: str
    created_by: Optional[str] = None
    updated_at: Optional[str] = None


class PreprocessResponse(BaseModel):
    """AI预处理响应"""
    file_id: int
    raw_text: str
    ai_highlights: List[AIHighlight]
    status: LearningStatus


class AnnotationSubmit(BaseModel):
    """提交标注"""
    file_id: int
    annotations: List[Annotation]
    judgment: HazmatResult             # 最终判断
    basis_fields: List[str]            # 判断依据字段列表


class GenerateRulesResponse(BaseModel):
    """规则生成响应"""
    file_id: int
    rule_drafts: List[RuleDraft]


class ReviewRuleRequest(BaseModel):
    """审核规则请求"""
    rule_id: int
    action: str                        # approve/reject/edit
    edited_rule: Optional[RuleDraft] = None  # 编辑后的规则（action=edit时）
    reason: Optional[str] = None       # 拒绝原因
