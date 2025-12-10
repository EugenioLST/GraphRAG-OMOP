# RULES.md — Universal Engineering Rules for AI Agents

These rules define **how the agent must behave in any project**, independent of stack or architecture.

---

# 1. Core Behavior Rules
- Ask clarifying questions when information is missing or ambiguous.
- Never assume APIs, modules, or functions exist unless verified.
- Validate file paths, directory names, and existing structure before referencing or modifying code.
- Produce a short plan before implementing significant changes.
- Prefer minimal, targeted edits; avoid broad refactors unless explicitly requested.
- Avoid destructive changes unless part of a defined task.

---

# 2. Code Quality Principles

<file_length_and_structure>
Never allow a file to exceed 500 lines.
Treat 1000 lines as unacceptable, even temporarily.
Use folders and naming conventions to keep small files logically grouped.
</file_length_and_structure>

<single_responsibility_and_component_structure>
Every functionality should live in a dedicated module or service.
Every module, component, or service must do one thing only.
If a unit has multiple responsibilities, split it immediately.
Code must be built for reuse, not just to “make it work.”
Favor composition over wrappers, and always think modularly.
</single_responsibility_and_component_structure>

<modular_and_scalable_design>
Code should connect like Lego—interchangeable, testable, and isolated.
Ask: “Can I reuse this module or service in another part of the system?” If not, refactor it.
Reduce tight coupling. Favor dependency injection or interfaces.
Always code for future growth with extensible, modular patterns.
Ensure flows, state, and orchestration can scale without rewrites.
Example for Python agents:
* `agent.py` - Main agent definition and execution logic
* `tools.py` - Tool functions used by the agent
* `prompts.py` - System prompts
</modular_and_scalable_design>


<naming_and_readability>
All module, function, and variable names must be descriptive and intention-revealing.
Avoid vague names like data, info, helper, temp.
Follow conventions: clear verbs for functions, PascalCase for classes, camelCase for services.
</naming_and_readability>


Extra:
- Code must be understandable to a mid-level engineer.
- Add comments explaining *why* behind non-obvious logic (`# Reason:`).
- Prefer composition over inheritance unless justified.


---
# 3. Testing Principles

- Every new feature or function requires:
  - 1 expected-case test  
  - 1 edge-case test  
  - 1 failure-case test  
- Tests must be deterministic and isolated.
* **Tests should live in a `/tests` folder** mirroring the main app structure.
- Update existing tests when logic changes.
- Keep tests simple, explicit, and reflective of intent.

---

# 4. UX & Reliability Guidelines
- Prefer optimistic updates when appropriate for smoother UX. 
- Handle errors gracefully with clear user-facing messages and logs when applicable.
- Avoid blocking operations unless required.
- Keep components/modules small and reusable.

---

# 5. Documentation Discipline
- Update documentation as part of the workflow, not afterward.
- Document new modules, decisions, or architectural changes.
- Use inline comments for complex logic.

---

# 6. Restrictions

- Do not introduce new dependencies without explicit approval.
- Do not modify unrelated files.
- Do not rewrite critical systems unless instructed.
- Do not refactor for “cleanliness” without functional benefit.

---

# 7. When in Doubt

- Ask questions. Nver assume missing context
- Restate assumptions.  
- Suggest alternatives with pros/cons.  
- Default to safe, minimal modifications.

