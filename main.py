# -*- coding: utf-8 -*-
import os
import json
import requests

# === 新增：从环境变量读取你的 API 密钥 ===
EXPECTED_API_KEY = os.getenv("MY_API_KEY")  # 注意：不是 DashScope 的 key！

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    raise EnvironmentError("❌ 未设置 DASHSCOPE_API_KEY")

MODEL_NAME = "qwen-turbo"
TIMEOUT = 10

def handler(event, context):
    try:
        # === Step 1: 解析 event ===
        if isinstance(event, bytes):
            event_dict = json.loads(event.decode('utf-8'))
        else:
            event_dict = event

        # === Step 2: 【新增】检查 API Key ===
        headers = event_dict.get("headers", {})
        client_key = headers.get("x-api-key") or headers.get("X-API-Key")
        
        if EXPECTED_API_KEY and client_key != EXPECTED_API_KEY:
            return _response(403, {"error": "无效的 API Key"})

        # === Step 3: 解析 body ===
        body_str = event_dict.get("body", "{}")
        body = json.loads(body_str)
        keyword = str(body.get("keyword", "")).strip()

        if not keyword:
            return _response(400, {"error": "缺少 keyword 字段"})

        # === Step 4: 调用 DashScope ===
        response = requests.post(
            url="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers={
                "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL_NAME,
                "input": {
                    "prompt": (
                        f"你是一个小红书爆款标题专家，请根据关键词\"{keyword}\"生成1个吸引眼球的标题。\n"
                        "要求：包含emoji，使用数字或惊叹句，不超过20字，只输出标题，不要解释。"
                    )
                },
                "parameters": {"temperature": 0.85}
            },
            timeout=TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        title = result["output"]["text"].strip()

        return _response(200, {"title": title})

    except Exception as e:
        print(f"Error: {str(e)}")
        return _response(500, {"error": "服务器内部错误"})

def _response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }