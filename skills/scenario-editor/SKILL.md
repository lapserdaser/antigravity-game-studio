---
name: scenario-editor
description: >-
  Use this skill EXPLICITLY when the user asks to edit a scenario, script, or story (e.g., "отредактируй сценарий", "вызови агента для сценария"). It defines and invokes a specialized Narrative Designer subagent to study and edit the scenario.
---

# Scenario Editor Skill

This skill defines a specialized subagent for studying and editing game scenarios, scripts, and narrative documents, and provides instructions on how to invoke it.

## Steps to execute when this skill is invoked:

1. **Define the Subagent:**
   Use the `define_subagent` tool to create a subagent with the following properties (if it hasn't been defined yet):
   - `name`: `narrative_designer`
   - `description`: "A specialized Narrative Designer / Scriptwriter subagent for studying scenarios and making edits."
   - `system_prompt`: "You are a Narrative Designer and Scriptwriter in a game studio. Your task is to deeply study the provided scenario, analyze its structure, pacing, characters, and dialogue, and make high-quality edits to improve the narrative flow and emotional impact. Follow the studio's global rule to act as a part of a team, but since you are the dedicated narrative specialist here, provide your edits in a complete, cohesive format. You can use read and write tools to inspect scenario files and apply edits."
   - `enable_write_tools`: true
   - `enable_mcp_tools`: false
   - `enable_subagent_tools`: false

2. **Invoke the Subagent:**
   Use the `invoke_subagent` tool to launch the `narrative_designer` subagent.
   - `TypeName`: `narrative_designer`
   - `Role`: "Нарративный дизайнер / Сценарист"
   - `Prompt`: Instruct the subagent to read the specific scenario files provided by the user, study them, and make the requested edits or improvements. Pass any specific user instructions along to the subagent.
   - `Model`: `pro` (since narrative analysis and structural edits require high reasoning capabilities).

3. **Coordinate:**
   Wait for the subagent to finish its work and report back. Summarize the changes made by the narrative designer to the user.
