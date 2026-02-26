"""
Amazon Nova 2 Sonic voice service.
Implements real-time bidirectional audio streaming for conversational voice AI.

Nova 2 Sonic uses HTTP/2 bidirectional streaming via the Bedrock Runtime API.
The architecture bridges browser WebSocket audio ↔ Nova Sonic HTTP/2 stream.

Audio format: PCM 16kHz mono 16-bit (linear PCM)
"""

import asyncio
import base64
import json
import logging
import struct
import uuid
from typing import AsyncGenerator, Callable, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from backend.config import AWS_REGION, NOVA_SONIC_MODEL_ID, NOVA_SONIC_VOICES

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
CHANNELS = 1
BITS_PER_SAMPLE = 16

SONIC_SYSTEM_PROMPT = """You are Compass, a warm and compassionate voice assistant helping people in the United States navigate government benefits and social services.

You are speaking with someone who may be going through a difficult time. Be kind, patient, and non-judgmental. Speak clearly and at a comfortable pace.

Your goal is to understand their situation and help them discover benefits they may qualify for — things like food assistance, healthcare, housing help, and cash assistance.

Keep responses conversational and concise since this is a voice interface. Ask one question at a time. After gathering basic information (income, household size, state), let them know you'll look up what programs they may qualify for.

Important: Always maintain dignity and remind people that seeking help is a sign of strength, not weakness."""


class NovaSonicSession:
    """
    Manages a single Nova 2 Sonic bidirectional streaming session.

    Handles the full event protocol for Nova Sonic:
    sessionStart → promptStart → contentBlockStart → audioInput → contentBlockStop → promptStop
    """

    def __init__(self, session_id: str, voice_id: str = "matthew"):
        self.session_id = session_id
        self.voice_id = voice_id
        self.prompt_name = f"prompt-{uuid.uuid4().hex[:8]}"
        self._content_block_index = 0
        self._is_active = False
        self._stream = None
        self._bedrock_client = None

        # Callbacks
        self.on_audio_output: Optional[Callable[[bytes], None]] = None
        self.on_text_output: Optional[Callable[[str], None]] = None
        self.on_transcript: Optional[Callable[[str], None]] = None

    def _get_client(self):
        """Get bedrock-runtime client with appropriate configuration."""
        return boto3.client(
            "bedrock-runtime",
            region_name=AWS_REGION,
        )

    def _build_session_start_event(self) -> dict:
        return {
            "event": {
                "sessionStart": {
                    "inferenceConfiguration": {
                        "maxTokens": 1024,
                        "topP": 0.9,
                        "temperature": 0.7,
                    },
                    "voiceConfig": {
                        "voiceId": self.voice_id,
                    },
                    "systemPrompt": {
                        "text": SONIC_SYSTEM_PROMPT,
                    },
                }
            }
        }

    def _build_prompt_start_event(self) -> dict:
        return {
            "event": {
                "promptStart": {
                    "promptName": self.prompt_name,
                    "conversationConfig": {
                        "type": "DUPLEXED",
                        "audio": {
                            "startAudioEvent": {
                                "mediaType": "audio/lpcm",
                                "sampleRateHertz": SAMPLE_RATE,
                                "sampleSizeBits": BITS_PER_SAMPLE,
                                "channelCount": CHANNELS,
                                "audioType": "SPEECH",
                                "encoding": "base64",
                            }
                        },
                    },
                }
            }
        }

    def _build_content_block_start_event(self) -> dict:
        event = {
            "event": {
                "contentBlockStart": {
                    "promptName": self.prompt_name,
                    "contentBlockIndex": self._content_block_index,
                    "type": "audio",
                }
            }
        }
        return event

    def _build_audio_input_event(self, audio_b64: str) -> dict:
        return {
            "event": {
                "audioInput": {
                    "promptName": self.prompt_name,
                    "contentBlockIndex": self._content_block_index,
                    "content": audio_b64,
                }
            }
        }

    def _build_content_block_stop_event(self) -> dict:
        event = {
            "event": {
                "contentBlockStop": {
                    "promptName": self.prompt_name,
                    "contentBlockIndex": self._content_block_index,
                }
            }
        }
        self._content_block_index += 1
        return event

    def _build_prompt_stop_event(self) -> dict:
        return {
            "event": {
                "promptStop": {
                    "promptName": self.prompt_name,
                }
            }
        }

    def _build_session_end_event(self) -> dict:
        return {"event": {"sessionEnd": {}}}

    async def stream_audio(
        self,
        audio_chunks: AsyncGenerator[bytes, None],
    ) -> AsyncGenerator[dict, None]:
        """
        Stream audio to Nova Sonic and yield response events.

        This implements the bidirectional streaming protocol using
        Amazon Bedrock's InvokeModelWithBidirectionalStream API.

        Args:
            audio_chunks: Async generator yielding raw PCM audio bytes

        Yields:
            Response events with type 'audio', 'text', or 'transcript'
        """
        client = self._get_client()

        try:
            # Build the initial events as a generator
            async def input_event_stream():
                # 1. Session start
                yield {"bytes": json.dumps(self._build_session_start_event()).encode()}

                # 2. Prompt start
                yield {"bytes": json.dumps(self._build_prompt_start_event()).encode()}

                # 3. Content block start (audio)
                yield {"bytes": json.dumps(self._build_content_block_start_event()).encode()}

                # 4. Stream audio chunks
                async for chunk in audio_chunks:
                    if chunk:
                        audio_b64 = base64.b64encode(chunk).decode("utf-8")
                        yield {"bytes": json.dumps(self._build_audio_input_event(audio_b64)).encode()}

                # 5. End the content block and prompt
                yield {"bytes": json.dumps(self._build_content_block_stop_event()).encode()}
                yield {"bytes": json.dumps(self._build_prompt_stop_event()).encode()}
                yield {"bytes": json.dumps(self._build_session_end_event()).encode()}

            # Invoke the bidirectional stream
            response = client.invoke_model_with_bidirectional_stream(
                modelId=NOVA_SONIC_MODEL_ID,
                body=input_event_stream(),
            )

            # Process output events
            async for event in response["body"]:
                event_data = json.loads(event["bytes"].decode("utf-8"))
                parsed = self._parse_output_event(event_data)
                if parsed:
                    yield parsed

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("ValidationException", "ResourceNotFoundException"):
                logger.warning("Nova Sonic not available (%s), using fallback", error_code)
                async for event in self._fallback_response():
                    yield event
            else:
                logger.error("Nova Sonic error: %s", e)
                raise
        except Exception as e:
            logger.error("Unexpected Nova Sonic error: %s", e)
            # Yield fallback response
            async for event in self._fallback_response():
                yield event

    def _parse_output_event(self, event_data: dict) -> Optional[dict]:
        """Parse a Nova Sonic output event and return structured data."""
        event = event_data.get("event", {})

        if "audioOutput" in event:
            audio_b64 = event["audioOutput"].get("content", "")
            if audio_b64:
                return {
                    "type": "audio",
                    "data": audio_b64,  # base64-encoded PCM
                    "sample_rate": SAMPLE_RATE,
                }

        elif "textOutput" in event:
            text = event["textOutput"].get("content", "")
            if text:
                return {"type": "text", "data": text}

        elif "inputTranscript" in event:
            text = event["inputTranscript"].get("content", "")
            if text:
                return {"type": "transcript", "data": text}

        elif "completionEnd" in event:
            return {"type": "done"}

        return None

    async def _fallback_response(self) -> AsyncGenerator[dict, None]:
        """
        Fallback when Nova Sonic is unavailable.
        Returns a pre-recorded greeting using synthesized audio data representation.
        """
        logger.info("Using Nova Sonic fallback (text-only mode)")
        yield {
            "type": "text",
            "data": (
                "Hello! I'm Compass, your benefits navigator. "
                "I'm here to help you find government assistance programs you may qualify for. "
                "Could you start by telling me a bit about your situation? "
                "For example, are you having trouble with food, healthcare costs, housing, or something else?"
            ),
        }
        yield {"type": "done"}


class NovaSonicService:
    """
    Service layer for Nova 2 Sonic voice sessions.
    Manages session lifecycle and provides WebSocket bridge.
    """

    def __init__(self):
        self._sessions: dict[str, NovaSonicSession] = {}

    def create_session(self, session_id: str, language: str = "en") -> NovaSonicSession:
        """Create a new Nova Sonic session."""
        voice_id = NOVA_SONIC_VOICES.get(language, "matthew")
        session = NovaSonicSession(session_id=session_id, voice_id=voice_id)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[NovaSonicSession]:
        return self._sessions.get(session_id)

    def close_session(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session:
            session._is_active = False

    async def process_audio_websocket(
        self,
        session_id: str,
        websocket,
        language: str = "en",
    ) -> None:
        """
        Bridge between a WebSocket connection and Nova Sonic.

        Protocol:
        - Browser sends binary PCM audio chunks OR JSON control messages
        - We forward audio to Nova Sonic
        - Nova Sonic returns audio/text events
        - We forward responses back to browser

        Control messages (JSON strings):
            {"type": "start", "language": "en"}
            {"type": "stop"}
        """
        session = self.create_session(session_id, language)
        audio_queue: asyncio.Queue[Optional[bytes]] = asyncio.Queue()

        async def receive_audio():
            """Receive audio from browser and put in queue."""
            try:
                while True:
                    data = await websocket.receive()

                    if data.get("type") == "websocket.disconnect":
                        break

                    if "bytes" in data:
                        # Binary audio data
                        await audio_queue.put(data["bytes"])
                    elif "text" in data:
                        msg = json.loads(data["text"])
                        if msg.get("type") == "stop":
                            await audio_queue.put(None)  # Signal end
                            break
                        elif msg.get("type") == "ping":
                            await websocket.send_json({"type": "pong"})
            except Exception as e:
                logger.error("WebSocket receive error: %s", e)
            finally:
                await audio_queue.put(None)

        async def audio_chunk_generator():
            """Async generator that yields audio chunks from the queue."""
            while True:
                chunk = await audio_queue.get()
                if chunk is None:
                    break
                yield chunk

        # Start receiving in background
        receive_task = asyncio.create_task(receive_audio())

        try:
            # Stream through Nova Sonic
            async for event in session.stream_audio(audio_chunk_generator()):
                if event["type"] == "audio":
                    # Send audio back to browser as binary
                    audio_bytes = base64.b64decode(event["data"])
                    await websocket.send_bytes(audio_bytes)
                    # Also send metadata
                    await websocket.send_json({
                        "type": "audio_meta",
                        "sample_rate": event.get("sample_rate", SAMPLE_RATE),
                    })
                elif event["type"] == "text":
                    await websocket.send_json({
                        "type": "response_text",
                        "text": event["data"],
                    })
                elif event["type"] == "transcript":
                    await websocket.send_json({
                        "type": "transcript",
                        "text": event["data"],
                    })
                elif event["type"] == "done":
                    await websocket.send_json({"type": "done"})

        except Exception as e:
            logger.error("Nova Sonic WebSocket bridge error: %s", e)
            await websocket.send_json({
                "type": "error",
                "message": "Voice processing error. Please try text chat instead.",
            })
        finally:
            receive_task.cancel()
            self.close_session(session_id)
