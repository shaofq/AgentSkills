# -*- coding: utf-8 -*-
"""SQLite数据库服务"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# 数据库文件路径
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "app.db"


class Database:
    """SQLite数据库管理类"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_db(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    email TEXT,
                    display_name TEXT,
                    role TEXT DEFAULT 'operator',
                    is_active INTEGER DEFAULT 1,
                    credits INTEGER DEFAULT 100,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_login TEXT
                )
            ''')
            
            # 积分记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS credit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    balance INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # 用户设置表（存储列映射等配置）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    setting_key TEXT NOT NULL,
                    setting_value TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(user_id, setting_key)
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_credit_logs_user_id ON credit_logs(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id)')
            
            # 数据库迁移：为现有用户表添加credits字段（如果不存在）
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'credits' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT 100')
                print("[Database] 已为用户表添加 credits 字段")
            
            # 检查是否有管理员用户，如果没有则创建默认管理员
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            if cursor.fetchone()[0] == 0:
                from api.services.auth_service import hash_password
                default_password = hash_password("admin123")
                cursor.execute('''
                    INSERT INTO users (username, hashed_password, display_name, role, email)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('admin', default_password, '系统管理员', 'admin', 'admin@example.com'))
                print("[Database] 创建默认管理员用户: admin / admin123")
            
            conn.commit()
            print(f"[Database] 数据库初始化完成: {self.db_path}")


class UserRepository:
    """用户数据访问层"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, username: str, hashed_password: str, email: str = None,
               display_name: str = None, role: str = 'operator') -> Dict[str, Any]:
        """创建用户"""
        now = datetime.now().isoformat()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, hashed_password, email, display_name, role, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, hashed_password, email, display_name, role, now, now))
            conn.commit()
            user_id = cursor.lastrowid
            # 在同一连接中查询
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有用户"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users ORDER BY id DESC LIMIT ? OFFSET ?', (limit, skip))
            return [dict(row) for row in cursor.fetchall()]
    
    def update(self, user_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        """更新用户"""
        if not kwargs:
            return self.get_by_id(user_id)
        
        kwargs['updated_at'] = datetime.now().isoformat()
        
        set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE users SET {set_clause} WHERE id = ?', values)
            return self.get_by_id(user_id)
    
    def update_last_login(self, user_id: int):
        """更新最后登录时间"""
        now = datetime.now().isoformat()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', (now, user_id))
    
    def delete(self, user_id: int) -> bool:
        """删除用户"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            return cursor.rowcount > 0
    
    def count(self) -> int:
        """获取用户总数"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            return cursor.fetchone()[0]


# 全局数据库实例
_db_instance: Optional[Database] = None
_user_repo: Optional[UserRepository] = None


def get_database() -> Database:
    """获取数据库实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


def get_user_repository() -> UserRepository:
    """获取用户仓库实例"""
    global _user_repo
    if _user_repo is None:
        _user_repo = UserRepository(get_database())
    return _user_repo
