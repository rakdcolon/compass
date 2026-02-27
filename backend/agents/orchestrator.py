"""
Compass multi-agent orchestrator powered by Amazon Nova 2 Lite.
Manages the full agentic loop: conversation → eligibility → resources → action plan.
"""

import json
import logging
import re
import uuid
from collections.abc import AsyncGenerator
from typing import Any, Optional

from backend.database import SessionStore
from backend.services.nova_lite import NovaLiteService

logger = logging.getLogger(__name__)

COMPASS_SYSTEM_PROMPT = """You are Compass, a compassionate and knowledgeable AI assistant helping people in need navigate government benefits and social services in the United States.

Your mission is to help people discover benefits they are entitled to but may not know about. Every year, $30 billion in government benefits go unclaimed because the systems are too complex, confusing, or inaccessible.

## Your Role
- Listen with empathy and without judgment
- Ask natural follow-up questions to understand their situation
- Use your tools to check eligibility and find local resources
- Provide clear, actionable guidance in plain language
- Be culturally sensitive and supportive

## Conversation Flow
1. Warmly greet the user and ask how you can help
2. Listen to their situation and ask ONLY necessary clarifying questions (income range, household size, state, any special circumstances like disability or pregnancy)
3. Once you have enough information (usually after 2-4 exchanges), use check_benefit_eligibility to run the analysis
4. Use find_local_resources to locate nearby help
5. If they upload a document, use analyze_document to extract relevant information
6. Create a clear action plan using create_action_plan
7. Offer to help them take the next steps

## Key Guidelines
- You speak with warmth, not clinical detachment
- Never make people feel ashamed about needing help
- Be direct about what programs they likely qualify for
- Explain benefits in simple terms (avoid jargon)
- For income, ask for ANNUAL gross household income (you can help them estimate from monthly/weekly if needed)
- Always emphasize: applying for benefits is their right, not charity
- If someone mentions a crisis (no food tonight, facing eviction, medical emergency), provide hotline numbers FIRST before gathering more information

## Available Tools
- check_benefit_eligibility: Determines which federal programs someone qualifies for
- find_local_resources: Finds nearby food banks, clinics, shelters, and services
- analyze_document: Reads and extracts info from uploaded documents (pay stubs, bills, etc.)
- create_action_plan: Generates a personalized step-by-step action plan

## Important Notes
- Compass is a screening tool. Always remind users to verify eligibility with official program offices.
- Income thresholds are based on 2024 federal guidelines; state programs may vary.
- Benefits are not charity — they are programs funded by taxpayers, for taxpayers."""

TOOL_DEFINITIONS = [
    {
        "toolSpec": {
            "name": "check_benefit_eligibility",
            "description": (
                "Check which federal benefit programs (SNAP, Medicaid, TANF, SSI, EITC, Section 8, etc.) "
                "a person likely qualifies for based on their income, household size, state, age, "
                "employment status, and special circumstances. Call this once you have gathered enough info."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "annual_income": {
                            "type": "number",
                            "description": "Gross annual household income in US dollars. If monthly income given, multiply by 12.",
                        },
                        "household_size": {
                            "type": "integer",
                            "description": "Total number of people in the household including the applicant.",
                        },
                        "state": {
                            "type": "string",
                            "description": "US state name or two-letter abbreviation (e.g., 'CA' or 'California').",
                        },
                        "age": {
                            "type": "integer",
                            "description": "Age of the primary applicant in years.",
                        },
                        "employment_status": {
                            "type": "string",
                            "enum": ["employed", "unemployed", "self_employed", "retired", "disabled", "student"],
                            "description": "Current employment status of the primary applicant.",
                        },
                        "special_circumstances": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "List of applicable circumstances: 'disabled', 'pregnant', 'infant_child', "
                                "'elderly' (65+), 'veteran', 'domestic_violence', 'homeless', "
                                "'immigrant', 'recently_unemployed'. Leave empty if none."
                            ),
                        },
                    },
                    "required": ["annual_income", "household_size", "state", "age", "employment_status", "special_circumstances"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "find_local_resources",
            "description": (
                "Find nearby community resources such as food banks, free health clinics, emergency shelters, "
                "legal aid, childcare assistance, and employment services based on the user's location and needs."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "zip_code": {
                            "type": "string",
                            "description": "User's zip code or city/state for finding nearby resources.",
                        },
                        "needs_list": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of needs, e.g., ['food', 'healthcare', 'housing', 'utilities', 'childcare', 'employment', 'mental_health', 'legal']",
                        },
                        "language": {
                            "type": "string",
                            "description": "Preferred language code (e.g., 'en', 'es', 'fr', 'zh'). Default is 'en'.",
                        },
                    },
                    "required": ["zip_code", "needs_list"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "analyze_document",
            "description": (
                "Analyze an uploaded document image (pay stub, tax return, utility bill, medical record, "
                "benefit letter, lease, etc.) and extract key financial and personal information. "
                "Use this when the user has shared a document."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "image_base64": {
                            "type": "string",
                            "description": "Base64-encoded image of the document.",
                        },
                        "document_type": {
                            "type": "string",
                            "description": "Type of document: 'pay_stub', 'tax_return', 'utility_bill', 'medical_record', 'id_document', 'benefit_letter', 'lease', 'bank_statement', 'unknown'",
                        },
                    },
                    "required": ["image_base64", "document_type"],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "create_action_plan",
            "description": (
                "Generate a personalized, prioritized action plan for the user listing the specific steps "
                "they should take to apply for benefits and access resources. Call after eligibility check and resource discovery."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "eligible_programs": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "List of eligible programs from check_benefit_eligibility results.",
                        },
                        "local_resources": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "List of local resources from find_local_resources results.",
                        },
                        "user_situation": {
                            "type": "string",
                            "description": "Brief summary of the user's situation, needs, and any urgent circumstances.",
                        },
                        "language": {
                            "type": "string",
                            "description": "Language for the action plan ('en', 'es', etc.).",
                        },
                    },
                    "required": ["eligible_programs", "local_resources", "user_situation"],
                }
            },
        }
    },
]


class CompassOrchestrator:
    """
    Multi-agent orchestrator that manages the Compass conversation.
    Uses Nova 2 Lite with tool use for the full agentic loop.
    """

    def __init__(self, store: Optional[SessionStore] = None):
        self.nova_lite = NovaLiteService()
        self._sessions: dict[str, dict] = {}
        self.store = store

    async def get_or_create_session(self, session_id: str) -> dict:
        """Get existing session or create a new one (delegates to SessionStore when available)."""
        if self.store:
            return await self.store.get_or_create_session(session_id)
        # In-memory fallback (no store configured)
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "messages": [],
                "eligible_programs": [],
                "local_resources": [],
                "action_plan": None,
                "document_analysis": None,
                "user_profile": {},
            }
        return self._sessions[session_id]

    async def chat(
        self,
        session_id: str,
        user_message: str,
        document_base64: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Process a user message and return Compass's response.
        Runs the full agentic loop including tool calls.

        Args:
            session_id: Unique session identifier
            user_message: User's text message
            document_base64: Optional base64 document image attached to this message

        Returns:
            dict with 'response', 'tool_calls_made', 'session_data'
        """
        session = await self.get_or_create_session(session_id)

        # Build user message content
        content: list[dict] = []
        if document_base64:
            # Attach image to the message
            content.append({
                "image": {
                    "format": "jpeg",
                    "source": {"bytes": document_base64},
                }
            })
            content.append({"text": user_message or "I've uploaded a document. Can you analyze it?"})
        else:
            content.append({"text": user_message})

        session["messages"].append({"role": "user", "content": content})

        # Run the agentic loop
        response_text, tool_calls_made = await self._run_agent_loop(session)

        # Add assistant message to history
        session["messages"].append({
            "role": "assistant",
            "content": [{"text": response_text}],
        })

        if self.store:
            await self.store.save_session(session)

        return {
            "response": response_text,
            "tool_calls_made": tool_calls_made,
            "session_data": {
                "eligible_programs": session.get("eligible_programs", []),
                "local_resources": session.get("local_resources", []),
                "action_plan": session.get("action_plan"),
                "document_analysis": session.get("document_analysis"),
                "has_results": bool(session.get("eligible_programs")),
            },
        }

    async def chat_stream(
        self,
        session_id: str,
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        """
        Process a user message and stream Nova Lite's response as SSE events.
        Tool calls run silently between stream turns; the final text response
        is streamed token-by-token using Bedrock's converse_stream API.

        Yields SSE strings: 'data: {...}\\n\\n'
        Final event: 'data: {"done": true, "tool_calls": [...], "session_data": {...}}\\n\\n'
        """
        session = await self.get_or_create_session(session_id)
        session["messages"].append({"role": "user", "content": [{"text": user_message}]})
        messages = list(session["messages"])
        tool_calls_made: list[dict] = []
        full_response_text = ""

        for _ in range(10):
            done_payload: Optional[dict] = None
            iteration_text: list[str] = []

            # Use real Bedrock streaming for every turn
            for event_type, payload in self.nova_lite.converse_stream(
                messages=messages,
                system_prompt=COMPASS_SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
            ):
                if event_type == "text":
                    iteration_text.append(payload)
                    # Yield text deltas immediately to the client.
                    # Tool-use turns rarely emit text; end_turn turns emit the full answer.
                    yield f"data: {json.dumps({'delta': payload})}\n\n"
                elif event_type == "done":
                    done_payload = payload

            if not done_payload:
                break

            stop_reason = done_payload["stop_reason"]

            if stop_reason == "end_turn":
                raw_text = "".join(iteration_text)
                full_response_text = re.sub(
                    r"<thinking>.*?</thinking>", "", raw_text, flags=re.DOTALL
                ).strip()
                break

            elif stop_reason == "tool_use":
                # Append model message and execute tools silently
                messages.append(done_payload["raw_message"])
                tool_results = []
                for tc in done_payload["tool_calls"]:
                    tool_calls_made.append({"name": tc["name"], "input": tc["input"]})
                    try:
                        output = await self._execute_tool(session, tc["name"], tc["input"])
                    except Exception as e:
                        logger.error("Tool %s failed: %s", tc["name"], e)
                        output = {"error": str(e)}
                    tool_results.append({
                        "toolResult": {
                            "toolUseId": tc["tool_use_id"],
                            "content": [{"json": output}],
                        }
                    })
                messages.append({"role": "user", "content": tool_results})
            else:
                break

        # Store final assistant message in session
        session["messages"].append({
            "role": "assistant",
            "content": [{"text": full_response_text}],
        })

        if self.store:
            await self.store.save_session(session)

        # Send final SSE event with session metadata and clean response text
        session_data = {
            "eligible_programs": session.get("eligible_programs", []),
            "local_resources": session.get("local_resources", []),
            "action_plan": session.get("action_plan"),
            "document_analysis": session.get("document_analysis"),
            "has_results": bool(session.get("eligible_programs")),
        }
        yield f"data: {json.dumps({'done': True, 'response': full_response_text, 'tool_calls': tool_calls_made, 'session_id': session['session_id'], 'session_data': session_data})}\n\n"

    async def _run_agent_loop(self, session: dict) -> tuple[str, list]:
        """
        Run Nova Lite in a loop until it stops calling tools.
        Executes all tool calls and feeds results back to the model.

        Returns:
            (final_response_text, list_of_tool_calls_made)
        """
        messages = list(session["messages"])  # copy to avoid mutation during loop
        tool_calls_made = []

        for _ in range(10):  # max 10 iterations to prevent infinite loops
            result = self.nova_lite.converse(
                messages=messages,
                system_prompt=COMPASS_SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
            )

            if result["stop_reason"] == "end_turn":
                clean_text = re.sub(r'<thinking>.*?</thinking>', '', result["text"], flags=re.DOTALL).strip()
                return clean_text, tool_calls_made

            if result["stop_reason"] == "tool_use":
                # Add model's message (with tool_use blocks) to conversation
                messages.append(result["raw_message"])

                # Execute each tool call
                tool_results = []
                for tool_call in result["tool_calls"]:
                    tool_name = tool_call["name"]
                    tool_input = tool_call["input"]
                    tool_use_id = tool_call["tool_use_id"]

                    logger.info("Executing tool: %s", tool_name)
                    tool_calls_made.append({"name": tool_name, "input": tool_input})

                    try:
                        tool_output = await self._execute_tool(session, tool_name, tool_input)
                    except Exception as e:
                        logger.error("Tool %s failed: %s", tool_name, e)
                        tool_output = {"error": str(e)}

                    tool_results.append({
                        "toolResult": {
                            "toolUseId": tool_use_id,
                            "content": [{"json": tool_output}],
                        }
                    })

                # Add tool results to conversation
                messages.append({"role": "user", "content": tool_results})

            else:
                # Unexpected stop reason
                logger.warning("Unexpected stop reason: %s", result["stop_reason"])
                return result.get("text", "I encountered an issue. Please try again."), tool_calls_made

        return "I've gathered information about your situation. Please review the results.", tool_calls_made

    async def _execute_tool(self, session: dict, tool_name: str, tool_input: dict) -> Any:
        """Execute a tool and store results in session."""
        if tool_name == "check_benefit_eligibility":
            from backend.tools.eligibility import check_benefit_eligibility
            result = check_benefit_eligibility(**tool_input)
            session["eligible_programs"] = result.get("eligible_programs", [])
            session["user_profile"].update({
                "annual_income": tool_input.get("annual_income"),
                "household_size": tool_input.get("household_size"),
                "state": tool_input.get("state"),
            })
            return result

        elif tool_name == "find_local_resources":
            from backend.tools.resources import find_local_resources
            result = find_local_resources(**tool_input)
            session["local_resources"] = result.get("resources", [])
            return result

        elif tool_name == "analyze_document":
            from backend.tools.document_tool import analyze_document
            from backend.services.nova_lite import NovaLiteService
            result = analyze_document(
                image_base64=tool_input["image_base64"],
                document_type=tool_input.get("document_type", "unknown"),
                nova_lite_client=self.nova_lite,
            )
            session["document_analysis"] = result

            # Auto-update user profile from document if confidence is high
            if result.get("confidence") in ("high", "medium"):
                fields = result.get("key_fields", {})
                if result.get("annual_income_estimate"):
                    session["user_profile"]["annual_income"] = result["annual_income_estimate"]
                if fields.get("address"):
                    session["user_profile"]["address"] = fields["address"]

            return result

        elif tool_name == "create_action_plan":
            result = _build_action_plan(
                eligible_programs=tool_input.get("eligible_programs", []),
                local_resources=tool_input.get("local_resources", []),
                user_situation=tool_input.get("user_situation", ""),
                language=tool_input.get("language", "en"),
            )
            session["action_plan"] = result
            return result

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    async def get_session(self, session_id: str) -> Optional[dict]:
        if self.store:
            return await self.store.get_session(session_id)
        return self._sessions.get(session_id)

    async def clear_session(self, session_id: str) -> None:
        if self.store:
            await self.store.clear_session(session_id)
        self._sessions.pop(session_id, None)


def _build_action_plan(
    eligible_programs: list,
    local_resources: list,
    user_situation: str,
    language: str = "en",
) -> dict:
    """
    Build a structured, prioritized action plan.

    Organizes steps by urgency (immediate → short-term → ongoing).
    """
    immediate_steps = []
    short_term_steps = []
    ongoing_steps = []

    # Immediate: Crisis resources
    if any(r.get("type") in ("shelter", "crisis_support", "food_bank") for r in local_resources):
        immediate_steps.append({
            "step": 1,
            "title": "Get Immediate Help",
            "description": "Call 2-1-1 for emergency food, shelter, or crisis support available today.",
            "action": "Call or text 2-1-1",
            "urgency": "immediate",
        })

    # Short-term: Apply for benefits
    step_num = len(immediate_steps) + 1
    priority_programs = [p for p in eligible_programs if p.get("likelihood") == "High"][:3]
    for program in priority_programs:
        short_term_steps.append({
            "step": step_num,
            "title": f"Apply for {program['short_name']}",
            "description": f"Estimated value: {program.get('estimated_value', 'varies')}. {program.get('how_to_apply', '')}",
            "action": f"Apply at: {program.get('apply_url', 'benefits.gov')}",
            "timeline": program.get("timeline", ""),
            "urgency": "short_term",
            "program_id": program.get("id"),
        })
        step_num += 1

    # Gather documents step
    short_term_steps.append({
        "step": step_num,
        "title": "Gather Required Documents",
        "description": (
            "For most applications you'll need: photo ID, proof of address (utility bill or lease), "
            "proof of income (pay stubs or tax return), and Social Security numbers for household members."
        ),
        "action": "Collect documents before applying",
        "urgency": "short_term",
    })
    step_num += 1

    # Ongoing: Monitor and re-apply
    ongoing_steps.append({
        "step": step_num,
        "title": "Follow Up on Applications",
        "description": "Track your application status and respond promptly to any requests for additional information.",
        "action": "Keep records of all applications and confirmation numbers",
        "urgency": "ongoing",
    })

    # EITC reminder if in eligible programs
    eitc = next((p for p in eligible_programs if p.get("id") == "eitc"), None)
    if eitc:
        ongoing_steps.append({
            "step": step_num + 1,
            "title": "Claim Your Tax Credit",
            "description": f"File your taxes to claim the Earned Income Tax Credit. {eitc.get('estimated_value', '')}. Free tax prep available.",
            "action": "Call 1-800-906-9887 for free VITA tax preparation",
            "urgency": "ongoing",
        })

    all_steps = immediate_steps + short_term_steps + ongoing_steps

    return {
        "title": "Your Benefits Action Plan",
        "user_situation_summary": user_situation,
        "total_steps": len(all_steps),
        "immediate_steps": immediate_steps,
        "short_term_steps": short_term_steps,
        "ongoing_steps": ongoing_steps,
        "all_steps": all_steps,
        "reminder": (
            "This plan is a starting point. Eligibility decisions are made by program offices. "
            "Call 2-1-1 anytime for free help navigating these applications."
        ),
    }
