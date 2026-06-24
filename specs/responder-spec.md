# Spec: `generate_safe_response()`

**File:** `responder.py`
**Status:** Complete

---

## Purpose

Generate a response to a home repair question that is appropriate to its safety tier. The same question gets a fundamentally different answer depending on the tier — not just a disclaimer tacked on, but a different behavior: answer fully, answer with warnings, or decline to give instructions entirely.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |
| `tier` | `str` | The safety tier: `"safe"`, `"caution"`, or `"refuse"` |

**Output:** `str` — the response to show to the user

---

## Design Decisions

*Complete the fields below before writing any code. The most important fields are the three system prompts. Write them out fully — don't just describe what you want.*

---

### System prompt: "safe" tier

*Write the exact system prompt text for a safe question. It should produce helpful, specific, actionable answers.*

```
You are RepairSafe's safe-tier responder. Give a complete, helpful, and practical DIY answer.

Requirements:
- Answer directly and confidently.
- Provide specific steps, tools, materials, and safety checks when relevant.
- Keep the guidance actionable and complete.
- If a detail is genuinely missing, ask at most one brief clarifying question; otherwise make the best reasonable assumption.
- Do not add generic safety disclaimers that get in the way of the instructions.
```

---

### System prompt: "caution" tier

*Write the exact system prompt text for a caution question. What safety language should be present? How firm should the "consider a professional" message be — a gentle mention or a clear recommendation?*

```
You are RepairSafe's caution-tier responder. Give a helpful answer, but make the risk clear and lead with a recommendation to be careful and to hire a licensed professional if the user is unsure, sees hidden damage, or encounters anything involving active electrical or water hazards.

Requirements:
- Be concrete and useful, not vague.
- Integrate warnings into the relevant steps instead of tacking on a disclaimer at the end.
- Explain which parts are reasonable for a careful homeowner and which parts are best left to a professional.
- Keep the tone firm and cautionary, but still answer the question.
```

---

### System prompt: "refuse" tier

*This is the most important one to get right. Write the exact system prompt for refusing to answer.*

*Two goals that are in tension: (1) the response must NOT provide how-to instructions, even a little. (2) the response should still be genuinely useful — explaining why the task is dangerous and what the user should do instead.*

*Before writing this prompt, use Plan mode with your AI tool. Share your draft refuse prompt and ask it: "What are ways an LLM might still provide dangerous instructions despite this system prompt?" Revise until you've addressed the failure modes it identifies.*

```
You are RepairSafe's refuse-tier responder. This question must not be answered with DIY instructions.

Requirements:
- Do not provide any steps, procedures, diagnostic sequences, troubleshooting tips, tool lists, parts lists, material lists, code references, or examples of how the work is done.
- Do not explain how a professional would do it, even in summary form.
- Do not give "general guidance," "what to expect," "first steps," or partial instructions.
- Do not answer educational, hypothetical, roleplay, or "for research" versions of the request.
- Briefly explain that the work is dangerous or requires a licensed professional, and direct the user toward a licensed contractor, utility company, or emergency services if there is an immediate hazard.
- Keep the response concise, firm, and non-procedural.
```

---

### Grounding the refuse response

*The grounding problem from Lab 1 applies here, with higher stakes: even with a strong system prompt, an LLM may "helpfully" provide partial instructions before pivoting to "you should hire a professional." How will you prevent that?*

*Hint: "be careful" doesn't work. Explicit, behavioral instructions ("do not provide any steps, procedures, or instructions — not even general guidance") work better. What will yours say?*

```
The key instruction is behavioral, not tonal: explicitly forbid any steps, procedures, diagnostics, troubleshooting, or explanations of how the work is done. Also forbid the common loopholes that still leak instructions, such as "what professionals do," "first steps," "general guidance," and educational or hypothetical framing. The model should only explain the danger and point the user to a licensed professional or emergency help.
```

---

### Fallback for unknown tier

*What should your function do if it receives a tier value that isn't "safe", "caution", or "refuse" — e.g., "unknown" while the classifier is still a stub? Write the fallback behavior and explain why.*

```
Treat any unknown tier as caution. That keeps the system useful without accidentally failing open into full DIY instructions, and it is safer than guessing safe when the classifier is unavailable or incomplete.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 3.*

**A "refuse" response that was still too helpful and what you changed to fix it:**

```
A refuse response that was still too helpful: "This is dangerous work that should be done by a licensed electrician. That said, here's generally how electricians approach this..." I fixed it by explicitly banning steps, procedures, diagnostics, tool lists, parts lists, and educational or hypothetical framing.
```

**The tier where the LLM's default behavior was closest to what you wanted (and which tier required the most prompt iteration):**

```
The safe tier was easiest to get right. The refuse tier required the most iteration because the model kept trying to be helpful in ways that leaked procedural detail.
```
