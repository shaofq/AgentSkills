# -*- coding: utf-8 -*-
"""
危险品识别核心服务 - 规则引擎和业务逻辑
"""
import os
import re
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from openai import OpenAI

from api.models.hazmat import (
    ProcessStatus, HazmatResult, ExtractedInfo,
    AnalyzeResponse, RuleType
)
from api.services.hazmat_database import (
    get_sds_repository, get_rule_repository,
    SDSFileRepository, RuleRepository
)
from api.services.hazmat_parser import get_sds_parser, LLMEnhancedParser


class RuleEngine:
    """危险品判断规则引擎"""
    
    def __init__(self, rule_repo: RuleRepository):
        self.rule_repo = rule_repo
    
    def evaluate(self, extracted_info: Dict[str, Any]) -> Tuple[HazmatResult, float, List[Dict]]:
        """
        根据提取的信息和规则库进行判断
        
        Args:
            extracted_info: 提取的信息字典
            
        Returns:
            (result, confidence, matched_rules): 判断结果、置信度、匹配的规则列表
        """
        rules = self.rule_repo.get_all(include_inactive=False)
        matched_rules = []
        
        for rule in rules:
            if self._match_rule(rule, extracted_info):
                matched_rules.append({
                    'id': rule['id'],
                    'name': rule['name'],
                    'description': rule['description'],
                    'condition': f"{rule['condition_field']} {rule['condition_operator']} '{rule['condition_value']}'",
                    'result': rule['result'],
                    'priority': rule['priority'],
                    'rule_type': rule['rule_type']
                })
        
        # 按优先级排序匹配的规则
        matched_rules.sort(key=lambda x: x['priority'])
        
        # 确定最终结果
        if matched_rules:
            # 有匹配的规则，取最高优先级的结果
            result = HazmatResult(matched_rules[0]['result'])
            # 置信度基于匹配规则数量
            confidence = min(0.5 + len(matched_rules) * 0.1, 0.99)
        else:
            # 没有匹配任何规则，判断为非危险品（低置信度）
            result = HazmatResult.NON_HAZARDOUS
            confidence = 0.6
        
        return result, confidence, matched_rules
    
    def _match_rule(self, rule: Dict, info: Dict) -> bool:
        """检查单条规则是否匹配"""
        field = rule['condition_field']
        operator = rule['condition_operator']
        value = rule['condition_value']
        
        # 获取字段值
        field_value = info.get(field)
        
        if operator == 'exists':
            # 检查字段是否存在且非空
            if isinstance(field_value, list):
                return len(field_value) > 0
            return field_value is not None and str(field_value).strip() != ''
        
        if field_value is None:
            return False
        
        if operator == 'equals':
            # 完全匹配（忽略大小写）
            if isinstance(field_value, list):
                return any(str(v).lower() == value.lower() for v in field_value)
            return str(field_value).lower() == value.lower()
        
        if operator == 'contains':
            # 包含匹配
            if isinstance(field_value, list):
                return any(value.lower() in str(v).lower() for v in field_value)
            return value.lower() in str(field_value).lower()
        
        if operator == 'regex':
            # 正则匹配
            try:
                pattern = re.compile(value, re.IGNORECASE)
                if isinstance(field_value, list):
                    return any(pattern.search(str(v)) for v in field_value)
                return pattern.search(str(field_value)) is not None
            except:
                return False
        
        return False


class HazmatService:
    """危险品识别服务"""
    
    UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '../../data/hazmat_uploads')
    
    def __init__(self):
        self.sds_repo = get_sds_repository()
        self.rule_repo = get_rule_repository()
        self.parser = get_sds_parser()
        self.rule_engine = RuleEngine(self.rule_repo)
        
        # 初始化LLM客户端
        self._init_llm()
        
        # 确保上传目录存在
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
    
    def _init_llm(self):
        """初始化大模型客户端"""
        api_key = os.environ.get('DASHSCOPE_API_KEY')
        if api_key:
            try:
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
                self.parser.set_llm_client(client, 'qwen-plus')
                print("[HazmatService] LLM客户端初始化成功")
            except Exception as e:
                print(f"[HazmatService] LLM客户端初始化失败: {e}")
    
    def upload_file(self, filename: str, file_content: bytes) -> Dict[str, Any]:
        """
        上传SDS文件
        
        Args:
            filename: 文件名
            file_content: 文件内容
            
        Returns:
            文件记录
        """
        # 生成唯一文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(self.UPLOAD_DIR, safe_filename)
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # 创建数据库记录
        file_record = self.sds_repo.create(
            filename=filename,
            file_path=file_path,
            file_size=len(file_content)
        )
        
        print(f"[HazmatService] 文件上传成功: {filename}, ID: {file_record['id']}")
        return file_record
    
    def analyze_file(self, file_id: int, use_llm: bool = True) -> AnalyzeResponse:
        """
        分析SDS文件
        
        Args:
            file_id: 文件ID
            use_llm: 是否使用大模型增强
            
        Returns:
            分析结果
        """
        # 获取文件记录
        file_record = self.sds_repo.get_by_id(file_id)
        if not file_record:
            raise ValueError(f"文件不存在: {file_id}")
        
        # 更新状态为处理中
        self.sds_repo.update(file_id, status=ProcessStatus.PROCESSING.value)
        
        try:
            # 解析PDF
            file_path = file_record['file_path']
            
            # 优先使用LLM增强解析
            if use_llm and self.parser.use_llm:
                print(f"[HazmatService] 使用LLM增强解析: {file_path}")
                extracted_info, full_text = self.parser.parse_with_llm(file_path)
            else:
                print(f"[HazmatService] 使用基础解析: {file_path}, use_llm={use_llm}, parser.use_llm={self.parser.use_llm}")
                extracted_info, full_text = self.parser.parse_pdf(file_path)
            
            # 调试日志
            print(f"[HazmatService] 提取结果: product_name={extracted_info.product_name}, hazard_class={extracted_info.hazard_class}, un_number={extracted_info.un_number}")
            
            # 转换为字典
            info_dict = extracted_info.model_dump()
            
            # 使用规则引擎判断
            result, confidence, matched_rules = self.rule_engine.evaluate(info_dict)
            
            # 更新数据库
            self.sds_repo.update(
                file_id,
                status=ProcessStatus.COMPLETED.value,
                result=result.value,
                confidence=confidence,
                extracted_info=info_dict,
                matched_rules=matched_rules
            )
            
            print(f"[HazmatService] 分析完成: ID={file_id}, 结果={result.value}, 置信度={confidence:.2f}")
            
            # 生成建议
            suggestions = self._generate_suggestions(info_dict, result, matched_rules)
            
            return AnalyzeResponse(
                file_id=file_id,
                result=result,
                confidence=confidence,
                extracted_info=extracted_info,
                matched_rules=matched_rules,
                suggestions=suggestions
            )
            
        except Exception as e:
            # 更新状态为错误
            self.sds_repo.update(file_id, status=ProcessStatus.ERROR.value)
            print(f"[HazmatService] 分析失败: {e}")
            raise
    
    def _generate_suggestions(self, info: Dict, result: HazmatResult, 
                             matched_rules: List) -> List[str]:
        """生成建议"""
        suggestions = []
        
        # 检查关键信息是否缺失
        if not info.get('un_number'):
            suggestions.append("未检测到UN编号，建议人工确认第14节运输信息")
        
        if not info.get('hazard_class'):
            suggestions.append("未检测到危险性类别，建议人工确认第2节危险性概述")
        
        if not info.get('signal_word'):
            suggestions.append("未检测到信号词，建议核对文档是否为完整SDS")
        
        if result == HazmatResult.HAZARDOUS and len(matched_rules) < 2:
            suggestions.append("仅匹配少量规则，建议仔细核对判断结果")
        
        if result == HazmatResult.NON_HAZARDOUS:
            suggestions.append("判断为非危险品，但建议核实是否有遗漏信息")
        
        return suggestions
    
    def confirm_result(self, file_id: int, result: HazmatResult,
                       corrections: List[Dict] = None,
                       confirmed_by: str = None) -> Dict[str, Any]:
        """
        确认分析结果
        
        Args:
            file_id: 文件ID
            result: 确认的结果
            corrections: 人工修正的字段列表
            confirmed_by: 确认人
            
        Returns:
            更新后的文件记录
        """
        file_record = self.sds_repo.get_by_id(file_id)
        if not file_record:
            raise ValueError(f"文件不存在: {file_id}")
        
        update_data = {
            'status': ProcessStatus.CONFIRMED.value,
            'result': result.value,
            'confirmed_at': datetime.now().isoformat(),
            'confirmed_by': confirmed_by
        }
        
        # 应用修正
        if corrections:
            extracted_info = file_record.get('extracted_info', {})
            for correction in corrections:
                field = correction.get('field_name')
                new_value = correction.get('new_value')
                if field and new_value is not None:
                    extracted_info[field] = new_value
            update_data['extracted_info'] = extracted_info
            
            # 重新评估规则
            new_result, confidence, matched_rules = self.rule_engine.evaluate(extracted_info)
            update_data['matched_rules'] = matched_rules
            update_data['confidence'] = confidence
        
        updated = self.sds_repo.update(file_id, **update_data)
        print(f"[HazmatService] 结果已确认: ID={file_id}, 结果={result.value}")
        
        return updated
    
    def get_file(self, file_id: int) -> Optional[Dict[str, Any]]:
        """获取文件详情"""
        return self.sds_repo.get_by_id(file_id)
    
    def get_file_list(self, skip: int = 0, limit: int = 20,
                      status: str = None, result: str = None,
                      keyword: str = None) -> Tuple[List[Dict], int]:
        """获取文件列表"""
        files = self.sds_repo.get_all(skip, limit, status, result, keyword)
        total = self.sds_repo.count(status, result)
        return files, total
    
    def delete_file(self, file_id: int) -> bool:
        """删除文件"""
        file_record = self.sds_repo.get_by_id(file_id)
        if file_record:
            # 删除物理文件
            file_path = file_record.get('file_path')
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            # 删除数据库记录
            return self.sds_repo.delete(file_id)
        return False
    
    def get_file_content(self, file_id: int) -> Optional[bytes]:
        """获取文件内容"""
        file_record = self.sds_repo.get_by_id(file_id)
        if file_record:
            file_path = file_record.get('file_path')
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return f.read()
        return None
    
    # ========== 规则管理 ==========
    
    def get_rules(self, include_inactive: bool = False, 
                  rule_type: str = None) -> List[Dict]:
        """获取规则列表"""
        return self.rule_repo.get_all(include_inactive, rule_type)
    
    def get_rule(self, rule_id: int) -> Optional[Dict]:
        """获取规则详情"""
        return self.rule_repo.get_by_id(rule_id)
    
    def create_rule(self, name: str, condition_field: str,
                    condition_operator: str, condition_value: str,
                    result: str = 'hazardous', description: str = None,
                    priority: int = 100, created_by: str = None) -> Dict:
        """创建规则"""
        rule = self.rule_repo.create(
            name=name,
            condition_field=condition_field,
            condition_operator=condition_operator,
            condition_value=condition_value,
            result=result,
            description=description,
            priority=priority,
            created_by=created_by
        )
        print(f"[HazmatService] 规则已创建: {name}")
        return rule
    
    def update_rule(self, rule_id: int, **kwargs) -> Optional[Dict]:
        """更新规则"""
        return self.rule_repo.update(rule_id, **kwargs)
    
    def delete_rule(self, rule_id: int) -> bool:
        """删除规则"""
        return self.rule_repo.delete(rule_id)
    
    def toggle_rule(self, rule_id: int, is_active: bool) -> Optional[Dict]:
        """启用/禁用规则"""
        return self.rule_repo.update(rule_id, is_active=1 if is_active else 0)
    
    # ========== 统计 ==========
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self.sds_repo.count()
        pending = self.sds_repo.count(status=ProcessStatus.PENDING.value)
        completed = self.sds_repo.count(status=ProcessStatus.COMPLETED.value)
        confirmed = self.sds_repo.count(status=ProcessStatus.CONFIRMED.value)
        hazardous = self.sds_repo.count(result=HazmatResult.HAZARDOUS.value)
        non_hazardous = self.sds_repo.count(result=HazmatResult.NON_HAZARDOUS.value)
        
        rules = self.rule_repo.get_all(include_inactive=True)
        builtin_rules = len([r for r in rules if r['rule_type'] == RuleType.BUILTIN.value])
        custom_rules = len([r for r in rules if r['rule_type'] == RuleType.CUSTOM.value])
        
        return {
            'total_files': total,
            'pending': pending,
            'completed': completed,
            'confirmed': confirmed,
            'hazardous': hazardous,
            'non_hazardous': non_hazardous,
            'total_rules': len(rules),
            'builtin_rules': builtin_rules,
            'custom_rules': custom_rules
        }


# 单例
_hazmat_service: Optional[HazmatService] = None


def get_hazmat_service() -> HazmatService:
    """获取危险品识别服务实例"""
    global _hazmat_service
    if _hazmat_service is None:
        _hazmat_service = HazmatService()
    return _hazmat_service
