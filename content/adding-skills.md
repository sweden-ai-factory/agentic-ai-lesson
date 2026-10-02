# 4. Skills

- Give a motivation for skills
- Explain how they work
- What gets loaded in

```{literalinclude} agent-skills/travel-policy/SKILL.md
```

- How to include the skills file into the framework
- https://github.com/agentskills/agentskills
- How do skills compare to related ideas like system prompts, MCP, tool calls, 
- Discussion: What would be skills that you could imagine?

```{literalinclude} 05_skills.py
:start-at: agent = Agent(
:end-before: async def main():
```

- try out the skill
```bash
uv run 05_skills.py
```

