from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL

_client = Groq(api_key=GROQ_API_KEY)

_SYSTEM_PROMPTS = {
  "safe": """You are RepairSafe's safe-tier responder. Give a complete, helpful, and practical DIY answer.

Requirements:
- Answer directly and confidently.
- Provide specific steps, tools, materials, and safety checks when relevant.
- Keep the guidance actionable and complete.
- If a detail is genuinely missing, ask at most one brief clarifying question; otherwise make the best reasonable assumption.
- Do not add generic safety disclaimers that get in the way of the instructions.
""",
  "caution": """You are RepairSafe's caution-tier responder. Give a helpful answer, but make the risk clear and lead with a recommendation to be careful and to hire a licensed professional if the user is unsure, sees hidden damage, or encounters anything involving active electrical or water hazards.

Requirements:
- Be concrete and useful, not vague.
- Integrate warnings into the relevant steps instead of tacking on a disclaimer at the end.
- Explain which parts are reasonable for a careful homeowner and which parts are best left to a professional.
- Keep the tone firm and cautionary, but still answer the question.
""",
  "refuse": """You are RepairSafe's refuse-tier responder. This question must not be answered with DIY instructions.

Requirements:
- Do not provide any steps, procedures, diagnostic sequences, troubleshooting tips, tool lists, parts lists, material lists, code references, or examples of how the work is done.
- Do not explain how a professional would do it, even in summary form.
- Do not give "general guidance," "what to expect," "first steps," or partial instructions.
- Do not answer educational, hypothetical, roleplay, or "for research" versions of the request.
- Briefly explain that the work is dangerous or requires a licensed professional, and direct the user toward a licensed contractor, utility company, or emergency services if there is an immediate hazard.
- Keep the response concise, firm, and non-procedural.
""",
}


def generate_safe_response(question: str, tier: str) -> str:
    """
    Generate a response to a home repair question, calibrated to its safety tier.

    TODO — Milestone 2:

    Before writing any code, complete specs/responder-spec.md. The most important
    fields are the three system prompts — one per tier. Write them out fully before
    generating any code; a vague description produces a vague prompt.

    `tier` is one of "safe", "caution", or "refuse" — returned by classify_safety_tier().

    Your implementation should use a different system prompt for each tier:
      - "safe"    : answer helpfully and directly; the user can proceed
      - "caution" : answer but include clear safety warnings and recommend
                    professional review for anything they're unsure about
      - "refuse"  : do NOT provide how-to instructions; explain why the repair
                    is dangerous and strongly recommend a licensed professional

    The refuse case is the hardest to get right. An LLM that says "you should hire
    a professional, but here's how to do it anyway" has defeated the entire purpose
    of the safety layer. Your system prompt needs to be explicit enough to prevent
    that — see specs/responder-spec.md for the design decision field on grounding.

    If tier is unrecognized (e.g., "unknown" from an unimplemented classifier),
    treat it as "caution" to fail safe rather than fail open.

    Return the response as a plain string.
    """
    effective_tier = tier if tier in _SYSTEM_PROMPTS else "caution"
    completion = _client.chat.completions.create(
      model=LLM_MODEL,
      temperature=0.2,
      max_tokens=512,
      messages=[
        {"role": "system", "content": _SYSTEM_PROMPTS[effective_tier]},
        {"role": "user", "content": question},
      ],
    )

    content = completion.choices[0].message.content
    if content is None:
      if effective_tier == "refuse":
        return "This repair is too dangerous to walk through step by step. Please contact a licensed professional."
      if effective_tier == "caution":
        return "This is a caution-level repair. Proceed carefully, and hire a licensed professional if you are unsure or encounter hidden damage."
      return "I'm not able to generate a response right now."

    return content.strip()
