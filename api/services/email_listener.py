# -*- coding: utf-8 -*-
"""邮件监听服务 - 自动派单系统核心组件"""
import os
import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr
import asyncio
import json
import re
import fnmatch
from typing import List, Dict, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailMessage:
    """邮件消息数据类"""
    def __init__(
        self,
        msg_id: str,
        from_addr: str,
        from_name: str,
        to_addr: str,
        subject: str,
        date: str,
        body_text: str,
        body_html: str,
        attachments: List[Dict],
        raw_message: email.message.Message
    ):
        self.msg_id = msg_id
        self.from_addr = from_addr
        self.from_name = from_name
        self.to_addr = to_addr
        self.subject = subject
        self.date = date
        self.body_text = body_text
        self.body_html = body_html
        self.attachments = attachments
        self.raw_message = raw_message
    
    def to_dict(self) -> Dict:
        return {
            "msg_id": self.msg_id,
            "from_addr": self.from_addr,
            "from_name": self.from_name,
            "to_addr": self.to_addr,
            "subject": self.subject,
            "date": self.date,
            "body_text": self.body_text,
            "body_html": self.body_html,
            "attachments": [
                {"filename": att["filename"], "content_type": att["content_type"], "size": len(att.get("data", b""))}
                for att in self.attachments
            ]
        }
    
    def to_workflow_input(self) -> str:
        """转换为工作流输入格式"""
        attachment_info = ""
        if self.attachments:
            attachment_names = [att["filename"] for att in self.attachments]
            attachment_info = f"\n- 附件: {', '.join(attachment_names)}"
        
        return f"""收到新邮件:
- 发件人: {self.from_name} <{self.from_addr}>
- 主题: {self.subject}
- 时间: {self.date}{attachment_info}

邮件内容:
{self.body_text}
"""


class EmailListener:
    """邮件监听服务
    
    负责连接 IMAP 邮箱，拉取新邮件，并根据配置触发对应的工作流。
    """
    
    def __init__(self, config: Dict):
        """
        Args:
            config: 邮箱配置，包含 imap_server, imap_port, username, password_env 等
        """
        self.config = config
        self.account_id = config.get("id", "default")
        self.imap: Optional[imaplib.IMAP4_SSL] = None
        self.is_running = False
        self._workflow_callback: Optional[Callable] = None
    
    def set_workflow_callback(self, callback: Callable):
        """设置工作流触发回调函数
        
        Args:
            callback: 异步回调函数，签名为 async def callback(workflow_name: str, user_input: str, email_data: Dict)
        """
        self._workflow_callback = callback
    
    async def connect(self) -> bool:
        """连接到 IMAP 服务器
        
        Returns:
            连接是否成功
        """
        try:
            server = self.config["imap_server"]
            port = self.config.get("imap_port", 993)
            use_ssl = self.config.get("use_ssl", True)
            username = self.config["username"]
            password_env = self.config.get("password_env", "EMAIL_PASSWORD")
            password = os.environ.get(password_env, "")
            
            if not password:
                print(f"[EmailListener:{self.account_id}] 未找到密码环境变量: {password_env}")
                return False
            
            print(f"[EmailListener:{self.account_id}] 正在连接到 {server}:{port} (用户: {username})...")
            
            if use_ssl:
                self.imap = imaplib.IMAP4_SSL(server, port)
            else:
                self.imap = imaplib.IMAP4(server, port)
            
            imaplib.Commands['ID'] = ('AUTH')  # 注意：'AUTH'是元组
            self.imap.login(username, password)
            print(f"[EmailListener:{self.account_id}] 登录成功")
            
            # 163邮箱需要发送 ID 命令来标识客户端，否则会出现 Unsafe Login 错误
           # 3. 构造并发送ID命令[citation:7]
            client_id_args = ("name", "aigi", "version", "1.0.0", "vendor", "mycompany") # 可自定义
            try:
                # 注意参数的格式：用空格连接，整个字符串用括号包裹
                id_cmd = '("' + '" "'.join(client_id_args) + '")'
                typ, dat = self.imap._simple_command('ID', id_cmd)
                print(f"[EmailListener:{self.account_id}] 已发送ID命令，服务器响应: {typ}")
            except Exception as e:
                print(f"[EmailListener:{self.account_id}] ID命令发送异常: {e}")
            
            # 立即尝试选择 INBOX，避免先执行 list 触发安全检查
            print(f"[EmailListener:{self.account_id}] 立即尝试选择 INBOX...")
            status, data = self.imap.select('INBOX')
            print(f"[EmailListener:{self.account_id}] 初始 select(INBOX) 返回: status={status}, data={data}")
            
            # 列出可用的邮箱文件夹
            status, folders = self.imap.list()
            print(f"[EmailListener:{self.account_id}] list() 返回: status={status}")
            if status in ('OK', b'OK'):
                print(f"[EmailListener:{self.account_id}] 可用文件夹:")
                for folder in folders:
                    print(f"  - {folder}")
            
            return True
            
        except imaplib.IMAP4.error as e:
            print(f"[EmailListener:{self.account_id}] IMAP 连接失败: {e}")
            return False
        except Exception as e:
            print(f"[EmailListener:{self.account_id}] 连接异常: {e}")
            return False
    
    async def disconnect(self):
        """断开 IMAP 连接"""
        if self.imap:
            try:
                self.imap.logout()
                logger.info(f"[EmailListener:{self.account_id}] 已断开连接")
            except Exception as e:
                logger.warning(f"[EmailListener:{self.account_id}] 断开连接时出错: {e}")
            finally:
                self.imap = None
    
    def _decode_header_value(self, value: str) -> str:
        """解码邮件头部值（处理编码问题）"""
        if not value:
            return ""
        
        decoded_parts = []
        for part, encoding in decode_header(value):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or "utf-8", errors="replace"))
                except Exception:
                    decoded_parts.append(part.decode("utf-8", errors="replace"))
            else:
                decoded_parts.append(part)
        
        return "".join(decoded_parts)
    
    def _get_email_body(self, msg: email.message.Message) -> tuple:
        """提取邮件正文（纯文本和 HTML）
        
        Returns:
            (body_text, body_html)
        """
        body_text = ""
        body_html = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # 跳过附件
                if "attachment" in content_disposition:
                    continue
                
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        text = payload.decode(charset, errors="replace")
                        
                        if content_type == "text/plain":
                            body_text = text
                        elif content_type == "text/html":
                            body_html = text
                except Exception as e:
                    logger.warning(f"解析邮件正文时出错: {e}")
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    text = payload.decode(charset, errors="replace")
                    
                    if msg.get_content_type() == "text/html":
                        body_html = text
                    else:
                        body_text = text
            except Exception as e:
                logger.warning(f"解析邮件正文时出错: {e}")
        
        # 如果只有 HTML，尝试提取纯文本
        if not body_text and body_html:
            body_text = self._html_to_text(body_html)
        
        return body_text, body_html
    
    def _html_to_text(self, html: str) -> str:
        """简单的 HTML 转纯文本"""
        # 移除 script 和 style 标签
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # 移除所有 HTML 标签
        text = re.sub(r'<[^>]+>', ' ', text)
        # 处理 HTML 实体
        text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        # 压缩空白
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _get_attachments(self, msg: email.message.Message) -> List[Dict]:
        """提取邮件附件"""
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_header_value(filename)
                        content_type = part.get_content_type()
                        data = part.get_payload(decode=True)
                        
                        attachments.append({
                            "filename": filename,
                            "content_type": content_type,
                            "data": data
                        })
        
        return attachments
    
    async def fetch_new_emails(self, folder: str = "INBOX", mark_as_read: bool = True) -> List[EmailMessage]:
        """获取未读邮件
        
        Args:
            folder: 邮件文件夹，默认 INBOX
            mark_as_read: 是否标记为已读
            
        Returns:
            邮件消息列表
        """
        if not self.imap:
            logger.error(f"[EmailListener:{self.account_id}] 未连接到 IMAP 服务器")
            return []
        
        emails = []
        
        try:
            # 选择邮箱文件夹
            print(f"[EmailListener:{self.account_id}] 正在选择文件夹: {folder}")
            status, data = self.imap.select(folder)
            print(f"[EmailListener:{self.account_id}] select({folder}) 返回: status={status}, data={data}")
            
            # status 可能是字符串 'OK' 或字节 b'OK'
            if status not in ('OK', b'OK'):
                print(f"[EmailListener:{self.account_id}] 选择文件夹 {folder} 失败: {status}, data={data}")
                # 尝试重新连接后再选择
                return []
            
            status, messages = self.imap.search(None, "UNSEEN")
            print(f"[EmailListener:{self.account_id}] search(UNSEEN) 返回: status={status}, messages={messages}")
            
            msg_ids = messages[0].split()
            logger.info(f"[EmailListener:{self.account_id}] 发现 {len(msg_ids)} 封未读邮件")
            
            for msg_id in msg_ids:
                try:
                    _, msg_data = self.imap.fetch(msg_id, "(RFC822)")
                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)
                    
                    # 解析发件人
                    from_header = self._decode_header_value(msg.get("From", ""))
                    from_name, from_addr = parseaddr(from_header)
                    if not from_name:
                        from_name = from_addr.split("@")[0] if from_addr else "Unknown"
                    
                    # 解析收件人
                    to_header = self._decode_header_value(msg.get("To", ""))
                    _, to_addr = parseaddr(to_header)
                    
                    # 解析主题
                    subject = self._decode_header_value(msg.get("Subject", ""))
                    
                    # 解析日期
                    date = msg.get("Date", "")
                    
                    # 解析正文
                    body_text, body_html = self._get_email_body(msg)
                    
                    # 解析附件
                    attachments = self._get_attachments(msg)
                    
                    email_msg = EmailMessage(
                        msg_id=msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id),
                        from_addr=from_addr,
                        from_name=from_name,
                        to_addr=to_addr,
                        subject=subject,
                        date=date,
                        body_text=body_text,
                        body_html=body_html,
                        attachments=attachments,
                        raw_message=msg
                    )
                    
                    emails.append(email_msg)
                    
                    # 标记为已读
                    if mark_as_read:
                        self.imap.store(msg_id, '+FLAGS', '\\Seen')
                    
                    logger.info(f"[EmailListener:{self.account_id}] 处理邮件: {subject[:50]}...")
                    
                except Exception as e:
                    logger.error(f"[EmailListener:{self.account_id}] 解析邮件 {msg_id} 失败: {e}")
                    continue
            
        except imaplib.IMAP4.error as e:
            logger.error(f"[EmailListener:{self.account_id}] IMAP 错误: {e}")
            # 连接可能已断开，标记需要重连
            self.imap = None
        except Exception as e:
            logger.error(f"[EmailListener:{self.account_id}] 获取邮件失败: {e}")
        
        return emails
    
    def _match_sender(self, sender_addr: str, patterns: List[str]) -> bool:
        """检查发件人是否匹配白名单模式
        
        Args:
            sender_addr: 发件人邮箱地址
            patterns: 匹配模式列表，支持通配符 * 和 ?
            
        Returns:
            是否匹配
        """
        if not patterns or "*" in patterns:
            return True
        
        sender_addr = sender_addr.lower()
        for pattern in patterns:
            pattern = pattern.lower()
            if fnmatch.fnmatch(sender_addr, pattern):
                return True
        
        return False
    
    def _match_subject(self, subject: str, keywords: List[str]) -> bool:
        """检查主题是否包含关键词
        
        Args:
            subject: 邮件主题
            keywords: 关键词列表
            
        Returns:
            是否匹配（空列表表示匹配所有）
        """
        if not keywords:
            return True
        
        subject_lower = subject.lower()
        for keyword in keywords:
            if keyword.lower() in subject_lower:
                return True
        
        return False
    
    def find_matching_workflow(self, email_msg: EmailMessage) -> Optional[str]:
        """根据邮件内容查找匹配的工作流
        
        Args:
            email_msg: 邮件消息
            
        Returns:
            匹配的工作流名称，如果没有匹配则返回 None
        """
        workflow_bindings = self.config.get("workflow_bindings", [])
        default_workflow = None
        
        for binding in workflow_bindings:
            conditions = binding.get("conditions", {})
            allowed_senders = conditions.get("allowed_senders", ["*"])
            subject_contains = conditions.get("subject_contains", [])
            
            # 检查是否为默认工作流
            if binding.get("default", False):
                default_workflow = binding.get("workflow_name")
            
            # 检查发件人
            if not self._match_sender(email_msg.from_addr, allowed_senders):
                continue
            
            # 检查主题
            if not self._match_subject(email_msg.subject, subject_contains):
                continue
            
            # 匹配成功
            return binding.get("workflow_name")
        
        # 返回默认工作流
        return default_workflow
    
    async def process_emails(self) -> List[Dict]:
        """处理新邮件并触发工作流
        
        Returns:
            处理结果列表
        """
        results = []
        emails = await self.fetch_new_emails()
        
        for email_msg in emails:
            workflow_name = self.find_matching_workflow(email_msg)
            
            if workflow_name:
                logger.info(f"[EmailListener:{self.account_id}] 邮件 '{email_msg.subject}' 匹配工作流: {workflow_name}")
                
                if self._workflow_callback:
                    try:
                        user_input = email_msg.to_workflow_input()
                        await self._workflow_callback(workflow_name, user_input, email_msg.to_dict())
                        
                        results.append({
                            "email_id": email_msg.msg_id,
                            "subject": email_msg.subject,
                            "workflow": workflow_name,
                            "status": "triggered",
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception as e:
                        logger.error(f"[EmailListener:{self.account_id}] 触发工作流失败: {e}")
                        results.append({
                            "email_id": email_msg.msg_id,
                            "subject": email_msg.subject,
                            "workflow": workflow_name,
                            "status": "error",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        })
                else:
                    logger.warning(f"[EmailListener:{self.account_id}] 未设置工作流回调函数")
            else:
                logger.info(f"[EmailListener:{self.account_id}] 邮件 '{email_msg.subject}' 无匹配工作流，跳过")
                results.append({
                    "email_id": email_msg.msg_id,
                    "subject": email_msg.subject,
                    "workflow": None,
                    "status": "skipped",
                    "timestamp": datetime.now().isoformat()
                })
        
        return results
    
    async def _check_connection(self) -> bool:
        """检查 IMAP 连接是否有效"""
        if not self.imap:
            return False
        try:
            # 使用 NOOP 命令检查连接
            status, _ = self.imap.noop()
            return status in ('OK', b'OK')
        except Exception:
            return False
    
    async def start_polling(self, interval_seconds: int = 30):
        """开始轮询邮箱
        
        Args:
            interval_seconds: 轮询间隔（秒）
        """
        self.is_running = True
        print(f"[EmailListener:{self.account_id}] 开始轮询，间隔 {interval_seconds} 秒")
        
        # 首次启动时先断开旧连接再重新连接
        await self.disconnect()
        connected = await self.connect()
        if not connected:
            print(f"[EmailListener:{self.account_id}] 初始连接失败")
        
        while self.is_running:
            try:
                # 确保连接有效
                if not await self._check_connection():
                    await self.disconnect()
                    connected = await self.connect()
                    if not connected:
                        logger.error(f"[EmailListener:{self.account_id}] 连接失败，{interval_seconds} 秒后重试")
                        await asyncio.sleep(interval_seconds)
                        continue
                
                # 处理邮件
                await self.process_emails()
                
            except Exception as e:
                logger.error(f"[EmailListener:{self.account_id}] 轮询出错: {e}")
                # 重置连接
                await self.disconnect()
            
            await asyncio.sleep(interval_seconds)
        
        await self.disconnect()
        logger.info(f"[EmailListener:{self.account_id}] 轮询已停止")
    
    def stop_polling(self):
        """停止轮询"""
        self.is_running = False
        logger.info(f"[EmailListener:{self.account_id}] 正在停止轮询...")


class EmailListenerManager:
    """邮件监听管理器
    
    管理多个邮箱账户的监听服务。
    """
    
    def __init__(self, config_path: str = "config/email_triggers.json"):
        self.config_path = config_path
        self.listeners: Dict[str, EmailListener] = {}
        self.config: Dict = {}
        self._workflow_callback: Optional[Callable] = None
    
    def load_config(self) -> bool:
        """加载配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            logger.info(f"[EmailListenerManager] 已加载配置: {self.config_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"[EmailListenerManager] 配置文件不存在: {self.config_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"[EmailListenerManager] 配置文件格式错误: {e}")
            return False
    
    def set_workflow_callback(self, callback: Callable):
        """设置工作流触发回调函数"""
        self._workflow_callback = callback
    
    async def start_all(self):
        """启动所有已启用的邮件监听器"""
        if not self.config.get("enabled", False):
            logger.info("[EmailListenerManager] 邮件监听服务未启用")
            return
        
        email_accounts = self.config.get("email_accounts", [])
        poll_interval = self.config.get("poll_interval_seconds", 30)
        
        tasks = []
        for account in email_accounts:
            if not account.get("enabled", True):
                logger.info(f"[EmailListenerManager] 跳过未启用的账户: {account.get('id')}")
                continue
            
            listener = EmailListener(account)
            listener.set_workflow_callback(self._workflow_callback)
            self.listeners[account["id"]] = listener
            
            # 创建轮询任务
            task = asyncio.create_task(listener.start_polling(poll_interval))
            tasks.append(task)
        
        if tasks:
            logger.info(f"[EmailListenerManager] 已启动 {len(tasks)} 个邮件监听器")
            await asyncio.gather(*tasks)
    
    async def stop_all(self):
        """停止所有邮件监听器"""
        for listener_id, listener in self.listeners.items():
            listener.stop_polling()
        
        # 等待所有监听器停止
        await asyncio.sleep(1)
        logger.info("[EmailListenerManager] 所有邮件监听器已停止")
    
    def get_listener(self, account_id: str) -> Optional[EmailListener]:
        """获取指定账户的监听器"""
        return self.listeners.get(account_id)
