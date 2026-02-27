"""
Amazon Nova 2 Lite service wrapper.
Handles text conversations, vision analysis, and tool use via the Bedrock Converse API.
"""

import json
import logging
from typing import Any, Generator, Optional

import boto3
from botocore.exceptions import ClientError

from backend.config import (
    AWS_REGION,
    NOVA_LITE_MODEL_ID,
    NOVA_LITE_MAX_TOKENS,
    NOVA_LITE_TEMPERATURE,
    NOVA_LITE_TOP_P,
)

logger = logging.getLogger(__name__)


class NovaLiteService:
    """Client for Amazon Nova 2 Lite via the Bedrock Converse API."""

    def __init__(self):
        self.client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        self.model_id = NOVA_LITE_MODEL_ID

    def converse(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: Optional[list[dict]] = None,
        max_tokens: int = NOVA_LITE_MAX_TOKENS,
        temperature: float = NOVA_LITE_TEMPERATURE,
    ) -> dict[str, Any]:
        """
        Send a conversation to Nova Lite and return the full response.

        Args:
            messages: List of conversation messages in Bedrock format
            system_prompt: System prompt for the model
            tools: Optional list of tool specifications (JSON schema format)
            max_tokens: Maximum tokens for response
            temperature: Sampling temperature

        Returns:
            dict with 'text', 'stop_reason', 'tool_calls', 'usage'
        """
        kwargs: dict[str, Any] = {
            "modelId": self.model_id,
            "messages": messages,
            "system": [{"text": system_prompt}],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature,
                "topP": NOVA_LITE_TOP_P,
            },
        }

        if tools:
            kwargs["toolConfig"] = {"tools": tools}

        try:
            response = self.client.converse(**kwargs)
        except ClientError as e:
            logger.error("Nova Lite converse error: %s", e)
            raise

        stop_reason = response.get("stopReason", "end_turn")
        output_message = response.get("output", {}).get("message", {})
        content_blocks = output_message.get("content", [])

        text_parts = []
        tool_calls = []

        for block in content_blocks:
            if "text" in block:
                text_parts.append(block["text"])
            elif "toolUse" in block:
                tool_calls.append({
                    "tool_use_id": block["toolUse"]["toolUseId"],
                    "name": block["toolUse"]["name"],
                    "input": block["toolUse"]["input"],
                })

        return {
            "text": "\n".join(text_parts) if text_parts else "",
            "stop_reason": stop_reason,
            "tool_calls": tool_calls,
            "raw_message": output_message,
            "usage": response.get("usage", {}),
        }

    def converse_stream(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: Optional[list[dict]] = None,
        max_tokens: int = NOVA_LITE_MAX_TOKENS,
        temperature: float = NOVA_LITE_TEMPERATURE,
    ) -> Generator[tuple, None, None]:
        """
        Stream a conversation response from Nova Lite using Bedrock streaming.

        Yields tuples:
          ("text", delta_str)   — text content delta as the model generates
          ("done", metadata)    — final event with stop_reason, tool_calls, raw_message

        Args:
            messages: Conversation messages in Bedrock format
            system_prompt: System prompt
            tools: Optional tool specifications
        """
        kwargs: dict[str, Any] = {
            "modelId": self.model_id,
            "messages": messages,
            "system": [{"text": system_prompt}],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature,
                "topP": NOVA_LITE_TOP_P,
            },
        }
        if tools:
            kwargs["toolConfig"] = {"tools": tools}

        try:
            response = self.client.converse_stream(**kwargs)
        except ClientError as e:
            logger.error("Nova Lite converse_stream error: %s", e)
            raise

        content_blocks: list[dict] = []
        current_block: Optional[dict] = None
        current_tool_input = ""
        stop_reason = "end_turn"

        for event in response.get("stream", []):
            if "contentBlockStart" in event:
                start = event["contentBlockStart"]["start"]
                if "text" in start or not start:
                    current_block = {"text": ""}
                elif "toolUse" in start:
                    current_block = {
                        "toolUse": {
                            "toolUseId": start["toolUse"]["toolUseId"],
                            "name": start["toolUse"]["name"],
                            "input": {},
                        }
                    }
                    current_tool_input = ""

            elif "contentBlockDelta" in event:
                delta = event["contentBlockDelta"]["delta"]
                if "text" in delta and current_block and "text" in current_block:
                    current_block["text"] += delta["text"]
                    yield ("text", delta["text"])
                elif "toolUse" in delta:
                    current_tool_input += delta["toolUse"].get("input", "")

            elif "contentBlockStop" in event:
                if current_block is not None:
                    if "toolUse" in current_block:
                        try:
                            current_block["toolUse"]["input"] = (
                                json.loads(current_tool_input) if current_tool_input else {}
                            )
                        except json.JSONDecodeError:
                            current_block["toolUse"]["input"] = {}
                    content_blocks.append(current_block)
                    current_block = None
                    current_tool_input = ""

            elif "messageStop" in event:
                stop_reason = event["messageStop"].get("stopReason", "end_turn")

        # Build tool calls list from content blocks
        tool_calls = [
            {
                "tool_use_id": b["toolUse"]["toolUseId"],
                "name": b["toolUse"]["name"],
                "input": b["toolUse"]["input"],
            }
            for b in content_blocks
            if "toolUse" in b
        ]

        yield ("done", {
            "stop_reason": stop_reason,
            "tool_calls": tool_calls,
            "raw_message": {"role": "assistant", "content": content_blocks},
        })

    def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        image_format: str = "jpeg",
        expect_json: bool = False,
    ) -> Any:
        """
        Analyze an image using Nova Lite's vision capability.

        Args:
            image_base64: Base64-encoded image data
            prompt: Instruction for what to extract from the image
            image_format: Image format ('jpeg', 'png', 'webp', 'gif')
            expect_json: If True, attempt to parse response as JSON

        Returns:
            Extracted text or parsed JSON dict
        """
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "image": {
                            "format": image_format,
                            "source": {"bytes": image_base64},
                        }
                    },
                    {"text": prompt},
                ],
            }
        ]

        system = (
            "You are a precise document analysis assistant. "
            "Extract information exactly as it appears in documents. "
            "When asked to return JSON, return ONLY valid JSON with no markdown formatting."
        )

        try:
            response = self.client.converse(
                modelId=self.model_id,
                messages=messages,
                system=[{"text": system}],
                inferenceConfig={
                    "maxTokens": 1024,
                    "temperature": 0.1,  # Low temperature for accurate extraction
                    "topP": 0.9,
                },
            )
        except ClientError as e:
            logger.error("Nova Lite vision error: %s", e)
            raise

        content = response.get("output", {}).get("message", {}).get("content", [])
        text = content[0]["text"] if content and "text" in content[0] else ""

        if expect_json:
            # Strip markdown code blocks if present
            text = text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                logger.warning("Could not parse JSON from image analysis response")
                return {"raw_text": text, "parse_error": True}

        return text

    def simple_chat(self, user_message: str, system_prompt: str = "") -> str:
        """
        Simple one-shot text chat with Nova Lite.

        Args:
            user_message: User's message
            system_prompt: Optional system prompt

        Returns:
            Model's text response
        """
        messages = [{"role": "user", "content": [{"text": user_message}]}]
        system = system_prompt or "You are a helpful assistant."
        result = self.converse(messages, system_prompt=system)
        return result["text"]

    @staticmethod
    def build_tool_spec(
        name: str,
        description: str,
        properties: dict[str, dict],
        required: list[str],
    ) -> dict:
        """
        Helper to build a Bedrock tool specification.

        Args:
            name: Tool function name
            description: What the tool does
            properties: Dict of parameter name → {type, description, [enum]}
            required: List of required parameter names

        Returns:
            Bedrock toolSpec dict
        """
        return {
            "toolSpec": {
                "name": name,
                "description": description,
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    }
                },
            }
        }
