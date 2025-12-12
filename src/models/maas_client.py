"""
华为云MAAS API客户端
支持DeepSeek-V3等模型的调用
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class MaaSClient:
    """华为云MAAS API客户端"""

    def __init__(
        self,
        base_url: str = "https://api.modelarts-maas.com/v1",
        model: str = "DeepSeek-V3",
        api_key: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        初始化MaaS客户端

        Args:
            base_url: API基础URL
            model: 模型名称
            api_key: API密钥
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.logger = logging.getLogger(__name__)
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建带有重试策略的会话"""
        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 设置默认请求头
        session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}' if self.api_key else None
        })

        return session

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用聊天API

        Args:
            messages: 消息列表
            max_tokens: 最大生成token数
            temperature: 温度参数
            top_p: top_p参数
            **kwargs: 其他参数

        Returns:
            API响应结果
        """
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            **kwargs
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        return self._make_request("POST", url, json=payload)

    def complete(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        文本补全

        Args:
            prompt: 输入提示
            max_tokens: 最大生成token数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            API响应结果
        """
        url = f"{self.base_url}/completions"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            **kwargs
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        return self._make_request("POST", url, json=payload)

    def review_text(
        self,
        text: str,
        review_points: List[str],
        context: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        文本审核专用接口

        Args:
            text: 待审核文本
            review_points: 审核要点列表
            context: 上下文信息
            **kwargs: 其他参数

        Returns:
            审核结果
        """
        system_prompt = self._build_review_prompt(review_points)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self._build_user_prompt(text, context)}
        ]

        response = self.chat(
            messages=messages,
            temperature=0.3,  # 降低温度以获得更一致的结果
            **kwargs
        )

        return self._parse_review_response(response)

    def check_consistency(
        self,
        text_chunks: List[str],
        check_type: str = "terminology"
    ) -> Dict[str, Any]:
        """
        一致性检查

        Args:
            text_chunks: 文本块列表
            check_type: 检查类型 (terminology, facts, logic, requirements)

        Returns:
            一致性检查结果
        """
        system_prompt = self._build_consistency_prompt(check_type)

        # 将文本块组合成提示
        combined_text = "\n\n--- Chunk {} ---\n\n".format(
            "{}"
        ).join(text_chunks)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请检查以下文本块的{check_type}一致性：\n\n{combined_text}"}
        ]

        response = self.chat(
            messages=messages,
            temperature=0.2,  # 更低的温度以确保一致性
            max_tokens=2000
        )

        return self._parse_consistency_response(response)

    def _make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发起HTTP请求

        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 请求参数

        Returns:
            响应结果
        """
        try:
            self.logger.debug(f"发起 {method} 请求到 {url}")

            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求失败: {e}")
            raise

        except json.JSONDecodeError as e:
            self.logger.error(f"响应解析失败: {e}")
            raise

    def _build_review_prompt(self, review_points: List[str]) -> str:
        """构建审核系统提示"""
        points_str = "\n- ".join(review_points)
        return f"""你是一个专业的文本审核专家。请按照以下审核要点对文本进行审核：

审核要点：
- {points_str}

请对文本进行详细分析，并返回JSON格式的审核结果，包含以下字段：
1. overall_score: 整体评分 (0-100)
2. issues: 发现的问题列表，每个问题包含：
   - type: 问题类型
   - severity: 严重程度 (critical/high/medium/low)
   - description: 问题描述
   - location: 位置信息
   - suggestion: 修改建议
3. suggestions: 改进建议
4. summary: 审核总结

请确保返回的是有效的JSON格式。"""

    def _build_user_prompt(self, text: str, context: Optional[str] = None) -> str:
        """构建用户提示"""
        prompt = f"请审核以下文本：\n\n{text}"
        if context:
            prompt = f"上下文信息：\n{context}\n\n{prompt}"
        return prompt

    def _build_consistency_prompt(self, check_type: str) -> str:
        """构建一致性检查提示"""
        prompts = {
            "terminology": "你是一个术语一致性检查专家。请检查文本中术语使用的一致性。",
            "facts": "你是一个事实一致性检查专家。请检查文本中事实信息的一致性。",
            "logic": "你是一个逻辑一致性检查专家。请检查文本逻辑的一致性。",
            "requirements": "你是一个需求一致性检查专家。请检查需求定义的一致性。"
        }

        base_prompt = prompts.get(check_type, "你是一个一致性检查专家。")
        return f"""{base_prompt}

请识别并报告所有不一致的地方，返回JSON格式结果，包含：
1. consistency_score: 一致性评分 (0-100)
2. inconsistencies: 不一致问题列表
3. recommendations: 改进建议
4. critical_issues: 需要立即解决的关键问题

请确保返回的是有效的JSON格式。"""

    def _parse_review_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析审核响应"""
        try:
            if 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0]['message']['content']
                # 尝试解析JSON
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # 如果不是JSON格式，返回原始内容
                    return {
                        "raw_response": content,
                        "parsed": False
                    }
            return response
        except Exception as e:
            self.logger.error(f"解析审核响应失败: {e}")
            return {"error": str(e)}

    def _parse_consistency_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析一致性检查响应"""
        return self._parse_review_response(response)

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        url = f"{self.base_url}/models/{self.model}"
        return self._make_request("GET", url)

    def list_models(self) -> List[Dict[str, Any]]:
        """列出可用模型"""
        url = f"{self.base_url}/models"
        response = self._make_request("GET", url)
        return response.get('data', [])

    def health_check(self) -> bool:
        """健康检查"""
        try:
            # 发送一个简单的请求来检查API是否可用
            self.chat(messages=[{"role": "user", "content": "test"}], max_tokens=1)
            return True
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False

    def close(self):
        """关闭会话"""
        if self.session:
            self.session.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()