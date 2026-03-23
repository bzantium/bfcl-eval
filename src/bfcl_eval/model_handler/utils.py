"""Minimal model_handler utilities for compatibility with nemo-skills.

Only the memory-related helpers needed by BFCLGenerationTask are included.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bfcl_eval.eval_checker.multi_turn_eval.func_source_code.memory_api_metaclass import (
        MemoryAPI,
    )

MEMORY_AGENT_SETTINGS = {
    "student": "You are an academic-support assistant for college student. Remember key personal and academic details discussed across sessions, and draw on them to answer questions or give guidance.",
    "customer": "You are a general customer support assistant for an e-commerce platform. Your task is to understand and remember information that can be used to provide information about user inquiries, preferences, and offer consistent, helpful assistance over multiple interactions.",
    "finance": "You are a high-level executive assistant supporting a senior finance professional. Retain and synthesize both personal and professional information including facts, goals, prior decisions, and family life across sessions to provide strategic, context-rich guidance and continuity.",
    "healthcare": "You are a healthcare assistant supporting a patient across appointments. Retain essential medical history, treatment plans, and personal preferences to offer coherent, context-aware guidance and reminders.",
    "notetaker": "You are a personal organization assistant. Capture key information from conversations, like tasks, deadlines, and preferences, and use it to give reliable reminders and answers in future sessions.",
}

MEMORY_BACKEND_INSTRUCTION_UNIFIED = """{scenario_setting}

You have access to an advanced memory system, which is persistent across multiple conversations with the user, and can be accessed in a later interactions. You should actively manage your memory data to keep track of important information, ensure that it is up-to-date and easy to retrieve to provide personalized responses to the user later.

Here is the content of your memory system from previous interactions:
{memory_content}
"""

MEMORY_BACKEND_INSTRUCTION_CORE_ARCHIVAL = """{scenario_setting}

You have access to an advanced memory system, consisting of two memory types 'Core Memory' and 'Archival Memory'. Both type of memory is persistent across multiple conversations with the user, and can be accessed in a later interactions. You should actively manage your memory data to keep track of important information, ensure that it is up-to-date and easy to retrieve to provide personalized responses to the user later.

The Core memory is limited in size, but always visible to you in context. The Archival Memory has a much larger capacity, but will be held outside of your immediate context due to its size.

Here is the content of your Core Memory from previous interactions:
{memory_content}
"""


def add_memory_instruction_system_prompt(
    prompts: list[list[dict]],
    test_category: str,
    scenario: str,
    memory_backend_instance: "MemoryAPI",
) -> list[list[dict]]:
    """Add memory instruction system prompt for memory test categories.

    The input for prompts is a list of list of dictionaries, where each outer
    list item represents a conversation turn, and each inner list item
    represents a message in that turn. System prompts are added as the first
    message in the first turn of the conversation.
    """
    assert len(prompts) >= 1

    scenario_setting = MEMORY_AGENT_SETTINGS[scenario]
    memory_content = memory_backend_instance._dump_core_memory_to_context()

    if "rec_sum" in test_category:
        system_prompt_template = MEMORY_BACKEND_INSTRUCTION_UNIFIED
    else:
        system_prompt_template = MEMORY_BACKEND_INSTRUCTION_CORE_ARCHIVAL

    system_prompt = system_prompt_template.format(
        scenario_setting=scenario_setting, memory_content=memory_content
    )

    first_turn_prompts = prompts[0]
    if first_turn_prompts[0]["role"] == "system":
        first_turn_prompts[0]["content"] = (
            system_prompt + "\n\n" + first_turn_prompts[0]["content"]
        )
    else:
        first_turn_prompts.insert(
            0,
            {"role": "system", "content": system_prompt},
        )

    return prompts
