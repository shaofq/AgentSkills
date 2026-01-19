# -*- coding: utf-8 -*-
"""
危险品识别系统数据库服务
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from api.models.hazmat import ProcessStatus, HazmatResult, RuleType


class HazmatDatabase:
    """危险品识别数据库"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '../../data/hazmat.db')
        
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # SDS文件表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sds_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    confidence REAL,
                    extracted_info TEXT,
                    matched_rules TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    confirmed_at TEXT,
                    confirmed_by TEXT
                )
            ''')
            
            # 规则表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    rule_type TEXT DEFAULT 'custom',
                    condition_field TEXT NOT NULL,
                    condition_operator TEXT NOT NULL,
                    condition_value TEXT NOT NULL,
                    result TEXT DEFAULT 'hazardous',
                    is_active INTEGER DEFAULT 1,
                    priority INTEGER DEFAULT 100,
                    created_at TEXT NOT NULL,
                    created_by TEXT
                )
            ''')
            
            # 处理历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS process_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    detail TEXT,
                    created_at TEXT NOT NULL,
                    created_by TEXT,
                    FOREIGN KEY (file_id) REFERENCES sds_files(id)
                )
            ''')
            
            conn.commit()
            
            # 初始化内置规则
            self._init_builtin_rules(cursor, conn)
            
            print(f"[HazmatDB] 数据库初始化完成: {self.db_path}")
    
    def _init_builtin_rules(self, cursor, conn):
        """初始化内置规则"""
        cursor.execute('SELECT COUNT(*) FROM rules WHERE rule_type = ?', (RuleType.BUILTIN.value,))
        if cursor.fetchone()[0] > 0:
            return
        
        builtin_rules = [
            # 基于危险性类别的规则
            ("GHS类别-易燃气体", "危险性类别包含易燃气体", "hazard_class", "contains", "易燃气体", "hazardous", 10),
            ("GHS类别-易燃液体", "危险性类别包含易燃液体", "hazard_class", "contains", "易燃液体", "hazardous", 10),
            ("GHS类别-易燃固体", "危险性类别包含易燃固体", "hazard_class", "contains", "易燃固体", "hazardous", 10),
            ("GHS类别-氧化性", "危险性类别包含氧化性", "hazard_class", "contains", "氧化", "hazardous", 10),
            ("GHS类别-高压气体", "危险性类别包含高压气体", "hazard_class", "contains", "高压气体", "hazardous", 10),
            ("GHS类别-急性毒性", "危险性类别包含急性毒性", "hazard_class", "contains", "急性毒性", "hazardous", 10),
            ("GHS类别-腐蚀性", "危险性类别包含腐蚀性", "hazard_class", "contains", "腐蚀", "hazardous", 10),
            ("GHS类别-爆炸性", "危险性类别包含爆炸性", "hazard_class", "contains", "爆炸", "hazardous", 10),
            ("GHS类别-自燃", "危险性类别包含自燃", "hazard_class", "contains", "自燃", "hazardous", 10),
            ("GHS类别-遇水放出易燃气体", "危险性类别包含遇水放出易燃气体", "hazard_class", "contains", "遇水", "hazardous", 10),
            
            # 基于象形图的规则
            ("象形图-火焰", "象形图包含火焰标志", "pictograms", "contains", "火焰", "hazardous", 20),
            ("象形图-骷髅头", "象形图包含骷髅头标志", "pictograms", "contains", "骷髅", "hazardous", 20),
            ("象形图-腐蚀", "象形图包含腐蚀标志", "pictograms", "contains", "腐蚀", "hazardous", 20),
            ("象形图-爆炸", "象形图包含爆炸标志", "pictograms", "contains", "爆炸", "hazardous", 20),
            ("象形图-气瓶", "象形图包含气瓶标志", "pictograms", "contains", "气瓶", "hazardous", 20),
            ("象形图-感叹号", "象形图包含感叹号标志", "pictograms", "contains", "感叹号", "hazardous", 30),
            
            # 基于信号词的规则
            ("信号词-危险", "信号词为危险", "signal_word", "equals", "危险", "hazardous", 15),
            ("信号词-Danger", "信号词为Danger", "signal_word", "equals", "Danger", "hazardous", 15),
            
            # 基于UN编号的规则
            ("存在UN编号", "存在联合国危险货物编号", "un_number", "exists", "", "hazardous", 5),
            
            # 基于运输名称的规则
            ("运输名称存在", "存在运输专用名称", "proper_shipping_name", "exists", "", "hazardous", 25),
            
            # MSDS/IMDG运输分类规则
            ("IMDG-Class 1", "IMDG运输分类为Class 1（爆炸物）", "hazard_class", "contains", "Class 1", "hazardous", 8),
            ("IMDG-Class 2", "IMDG运输分类为Class 2（气体）", "hazard_class", "contains", "Class 2", "hazardous", 8),
            ("IMDG-Class 3", "IMDG运输分类为Class 3（易燃液体）", "hazard_class", "contains", "Class 3", "hazardous", 8),
            ("IMDG-Class 4", "IMDG运输分类为Class 4（易燃固体）", "hazard_class", "contains", "Class 4", "hazardous", 8),
            ("IMDG-Class 5", "IMDG运输分类为Class 5（氧化性物质）", "hazard_class", "contains", "Class 5", "hazardous", 8),
            ("IMDG-Class 6", "IMDG运输分类为Class 6（毒性物质）", "hazard_class", "contains", "Class 6", "hazardous", 8),
            ("IMDG-Class 7", "IMDG运输分类为Class 7（放射性物质）", "hazard_class", "contains", "Class 7", "hazardous", 8),
            ("IMDG-Class 8", "IMDG运输分类为Class 8（腐蚀性物质）", "hazard_class", "contains", "Class 8", "hazardous", 8),
            ("IMDG-Class 9", "IMDG运输分类为Class 9（杂项危险物质）", "hazard_class", "contains", "Class 9", "hazardous", 8),
            
            # 包装组规则（Packing Group表示危险等级）
            ("包装组-PG I", "包装组为I类（高危险）", "hazard_class", "contains", "PG I", "hazardous", 6),
            ("包装组-PG II", "包装组为II类（中危险）", "hazard_class", "contains", "PG II", "hazardous", 7),
            ("包装组-PG III", "包装组为III类（低危险）", "hazard_class", "contains", "PG III", "hazardous", 9),
            
            # 海洋污染物规则
            ("海洋污染物", "标记为海洋污染物", "hazard_class", "contains", "Marine Pollutant", "hazardous", 12),
            
            # Flammable/Toxic英文关键词
            ("英文-Flammable", "包含Flammable关键词", "hazard_class", "contains", "Flammable", "hazardous", 10),
            ("英文-Toxic", "包含Toxic关键词", "hazard_class", "contains", "Toxic", "hazardous", 10),
            ("英文-Corrosive", "包含Corrosive关键词", "hazard_class", "contains", "Corrosive", "hazardous", 10),
            ("英文-Oxidizing", "包含Oxidizing关键词", "hazard_class", "contains", "Oxidizing", "hazardous", 10),
            ("英文-Explosive", "包含Explosive关键词", "hazard_class", "contains", "Explosive", "hazardous", 10),
        ]
        
        now = datetime.now().isoformat()
        for rule in builtin_rules:
            cursor.execute('''
                INSERT INTO rules (name, description, rule_type, condition_field, condition_operator, 
                                   condition_value, result, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (rule[0], rule[1], RuleType.BUILTIN.value, rule[2], rule[3], rule[4], rule[5], rule[6], now))
        
        conn.commit()
        print(f"[HazmatDB] 初始化 {len(builtin_rules)} 条内置规则")


class SDSFileRepository:
    """SDS文件数据访问层"""
    
    def __init__(self, db: HazmatDatabase):
        self.db = db
    
    def create(self, filename: str, file_path: str, file_size: int = 0) -> Dict[str, Any]:
        """创建SDS文件记录"""
        now = datetime.now().isoformat()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sds_files (filename, file_path, file_size, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (filename, file_path, file_size, ProcessStatus.PENDING.value, now))
            conn.commit()
            file_id = cursor.lastrowid
            cursor.execute('SELECT * FROM sds_files WHERE id = ?', (file_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_by_id(self, file_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取文件"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sds_files WHERE id = ?', (file_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('extracted_info'):
                    result['extracted_info'] = json.loads(result['extracted_info'])
                if result.get('matched_rules'):
                    result['matched_rules'] = json.loads(result['matched_rules'])
                return result
            return None
    
    def get_all(self, skip: int = 0, limit: int = 100, 
                status: str = None, result: str = None,
                keyword: str = None) -> List[Dict[str, Any]]:
        """获取所有文件"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM sds_files WHERE 1=1'
            params = []
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            if result:
                query += ' AND result = ?'
                params.append(result)
            if keyword:
                query += ' AND filename LIKE ?'
                params.append(f'%{keyword}%')
            
            query += ' ORDER BY id DESC LIMIT ? OFFSET ?'
            params.extend([limit, skip])
            
            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                if item.get('extracted_info'):
                    item['extracted_info'] = json.loads(item['extracted_info'])
                if item.get('matched_rules'):
                    item['matched_rules'] = json.loads(item['matched_rules'])
                results.append(item)
            return results
    
    def update(self, file_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        """更新文件"""
        if not kwargs:
            return self.get_by_id(file_id)
        
        # JSON序列化
        if 'extracted_info' in kwargs and isinstance(kwargs['extracted_info'], dict):
            kwargs['extracted_info'] = json.dumps(kwargs['extracted_info'], ensure_ascii=False)
        if 'matched_rules' in kwargs and isinstance(kwargs['matched_rules'], list):
            kwargs['matched_rules'] = json.dumps(kwargs['matched_rules'], ensure_ascii=False)
        
        kwargs['updated_at'] = datetime.now().isoformat()
        
        set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
        values = list(kwargs.values()) + [file_id]
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE sds_files SET {set_clause} WHERE id = ?', values)
            conn.commit()
            return self.get_by_id(file_id)
    
    def delete(self, file_id: int) -> bool:
        """删除文件"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sds_files WHERE id = ?', (file_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def count(self, status: str = None, result: str = None) -> int:
        """统计文件数量"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = 'SELECT COUNT(*) FROM sds_files WHERE 1=1'
            params = []
            if status:
                query += ' AND status = ?'
                params.append(status)
            if result:
                query += ' AND result = ?'
                params.append(result)
            cursor.execute(query, params)
            return cursor.fetchone()[0]


class RuleRepository:
    """规则数据访问层"""
    
    def __init__(self, db: HazmatDatabase):
        self.db = db
    
    def create(self, name: str, condition_field: str, condition_operator: str,
               condition_value: str, result: str = 'hazardous',
               description: str = None, priority: int = 100,
               created_by: str = None) -> Dict[str, Any]:
        """创建规则"""
        now = datetime.now().isoformat()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO rules (name, description, rule_type, condition_field, condition_operator,
                                   condition_value, result, priority, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, description, RuleType.CUSTOM.value, condition_field, condition_operator,
                  condition_value, result, priority, now, created_by))
            conn.commit()
            rule_id = cursor.lastrowid
            cursor.execute('SELECT * FROM rules WHERE id = ?', (rule_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_by_id(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取规则"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM rules WHERE id = ?', (rule_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all(self, include_inactive: bool = False, rule_type: str = None) -> List[Dict[str, Any]]:
        """获取所有规则"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM rules WHERE 1=1'
            params = []
            
            if not include_inactive:
                query += ' AND is_active = 1'
            if rule_type:
                query += ' AND rule_type = ?'
                params.append(rule_type)
            
            query += ' ORDER BY priority ASC, id ASC'
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def update(self, rule_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        """更新规则"""
        if not kwargs:
            return self.get_by_id(rule_id)
        
        # 检查是否为内置规则
        rule = self.get_by_id(rule_id)
        if rule and rule['rule_type'] == RuleType.BUILTIN.value:
            # 内置规则只允许修改 is_active
            allowed_keys = {'is_active'}
            kwargs = {k: v for k, v in kwargs.items() if k in allowed_keys}
            if not kwargs:
                return rule
        
        set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
        values = list(kwargs.values()) + [rule_id]
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE rules SET {set_clause} WHERE id = ?', values)
            conn.commit()
            return self.get_by_id(rule_id)
    
    def delete(self, rule_id: int) -> bool:
        """删除规则（仅自定义规则）"""
        rule = self.get_by_id(rule_id)
        if rule and rule['rule_type'] == RuleType.BUILTIN.value:
            return False
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM rules WHERE id = ? AND rule_type = ?', 
                          (rule_id, RuleType.CUSTOM.value))
            conn.commit()
            return cursor.rowcount > 0


# 单例实例
_hazmat_db: Optional[HazmatDatabase] = None
_sds_repo: Optional[SDSFileRepository] = None
_rule_repo: Optional[RuleRepository] = None


def get_hazmat_database() -> HazmatDatabase:
    """获取数据库实例"""
    global _hazmat_db
    if _hazmat_db is None:
        _hazmat_db = HazmatDatabase()
    return _hazmat_db


def get_sds_repository() -> SDSFileRepository:
    """获取SDS文件仓库"""
    global _sds_repo
    if _sds_repo is None:
        _sds_repo = SDSFileRepository(get_hazmat_database())
    return _sds_repo


def get_rule_repository() -> RuleRepository:
    """获取规则仓库"""
    global _rule_repo
    if _rule_repo is None:
        _rule_repo = RuleRepository(get_hazmat_database())
    return _rule_repo
