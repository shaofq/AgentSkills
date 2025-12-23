"""
工具执行服务
支持邮件发送、HTTP请求、文件写入等工具操作
"""
import smtplib
import os
import re
import json
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ToolExecutor:
    """工具执行器"""
    
    def __init__(self):
        # 邮件配置从环境变量读取
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.163.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_ssl = os.getenv("SMTP_USE_SSL", "true").lower() == "true"
    
    def execute(self, tool_type: str, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            tool_type: 工具类型 (email-send, http-request, file-write)
            params: 工具参数
            context: 上下文变量，用于替换参数中的变量
            
        Returns:
            执行结果
        """
        # 替换参数中的变量
        params = self._replace_variables(params, context or {})
        
        if tool_type == "email-send":
            return self._execute_email_send(params)
        elif tool_type == "http-request":
            return self._execute_http_request(params)
        elif tool_type == "file-write":
            return self._execute_file_write(params)
        else:
            return {
                "success": False,
                "error": f"不支持的工具类型: {tool_type}"
            }
    
    def _replace_variables(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """替换参数中的变量 {{variable}}"""
        result = {}
        for key, value in params.items():
            if isinstance(value, str):
                # 替换 {{variable}} 格式的变量
                def replace_var(match):
                    var_name = match.group(1).strip()
                    return str(context.get(var_name, match.group(0)))
                result[key] = re.sub(r'\{\{(\w+)\}\}', replace_var, value)
            else:
                result[key] = value
        return result
    
    def _execute_email_send(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行邮件发送"""
        try:
            to_addrs = params.get("to", "")
            subject = params.get("subject", "")
            body = params.get("body", "")
            body_type = params.get("bodyType", "text")
            
            if not to_addrs:
                return {"success": False, "error": "收件人不能为空"}
            if not subject:
                return {"success": False, "error": "邮件主题不能为空"}
            
            # 解析收件人列表
            recipients = [addr.strip() for addr in to_addrs.split(",") if addr.strip()]
            
            # 创建邮件
            if body_type == "html":
                msg = MIMEMultipart("alternative")
                msg.attach(MIMEText(body, "html", "utf-8"))
            else:
                msg = MIMEText(body, "plain", "utf-8")
            
            msg["Subject"] = subject
            msg["From"] = self.smtp_user
            msg["To"] = ", ".join(recipients)
            
            # 发送邮件
            if self.smtp_use_ssl:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.smtp_user, recipients, msg.as_string())
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.smtp_user, recipients, msg.as_string())
            
            logger.info(f"邮件发送成功: to={recipients}, subject={subject}")
            return {
                "success": True,
                "message": f"邮件已成功发送到 {', '.join(recipients)}",
                "recipients": recipients,
                "subject": subject
            }
            
        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            return {
                "success": False,
                "error": f"邮件发送失败: {str(e)}"
            }
    
    def _execute_http_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行HTTP请求"""
        try:
            url = params.get("url", "")
            method = params.get("method", "GET").upper()
            headers_str = params.get("headers", "")
            body = params.get("body", "")
            
            if not url:
                return {"success": False, "error": "请求URL不能为空"}
            
            # 解析请求头
            headers = {}
            if headers_str:
                try:
                    headers = json.loads(headers_str)
                except json.JSONDecodeError:
                    return {"success": False, "error": "请求头JSON格式错误"}
            
            # 解析请求体
            request_body = None
            if body and method in ["POST", "PUT", "PATCH"]:
                try:
                    request_body = json.loads(body)
                except json.JSONDecodeError:
                    request_body = body  # 非JSON格式，作为字符串发送
            
            # 发送请求
            with httpx.Client(timeout=30.0) as client:
                if method == "GET":
                    response = client.get(url, headers=headers)
                elif method == "POST":
                    response = client.post(url, headers=headers, json=request_body if isinstance(request_body, dict) else None, content=request_body if isinstance(request_body, str) else None)
                elif method == "PUT":
                    response = client.put(url, headers=headers, json=request_body if isinstance(request_body, dict) else None, content=request_body if isinstance(request_body, str) else None)
                elif method == "DELETE":
                    response = client.delete(url, headers=headers)
                else:
                    return {"success": False, "error": f"不支持的请求方法: {method}"}
            
            # 尝试解析响应JSON
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            logger.info(f"HTTP请求成功: {method} {url}, status={response.status_code}")
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response_data,
                "headers": dict(response.headers)
            }
            
        except httpx.TimeoutException:
            return {"success": False, "error": "请求超时"}
        except Exception as e:
            logger.error(f"HTTP请求失败: {str(e)}")
            return {
                "success": False,
                "error": f"HTTP请求失败: {str(e)}"
            }
    
    def _execute_file_write(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件写入"""
        try:
            file_path = params.get("path", "")
            content = params.get("content", "")
            append = params.get("append", False)
            
            if not file_path:
                return {"success": False, "error": "文件路径不能为空"}
            
            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            # 写入文件
            mode = "a" if append else "w"
            with open(file_path, mode, encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"文件写入成功: {file_path}, append={append}")
            return {
                "success": True,
                "message": f"文件已{'追加' if append else '写入'}到 {file_path}",
                "path": file_path,
                "size": len(content)
            }
            
        except Exception as e:
            logger.error(f"文件写入失败: {str(e)}")
            return {
                "success": False,
                "error": f"文件写入失败: {str(e)}"
            }


# 全局工具执行器实例
tool_executor = ToolExecutor()
