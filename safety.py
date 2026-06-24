from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS
import re

_client = Groq(api_key=GROQ_API_KEY)

_CLASSIFIER_SYSTEM_PROMPT = """You are a strict classifier for home repair safety. Classify the user's question into exactly one tier: safe, caution, or refuse.

Definitions:
- safe: routine maintenance or low-risk repairs; worst case is cosmetic damage or a broken fixture.
- caution: doable homeowner repairs that stay within an existing fixture/location and involve water or electricity where mistakes can be costly or mildly risky, but do not require new infrastructure or a permit.
- refuse: repairs where an amateur mistake can cause fire, flooding, structural failure, serious injury, or death, or where a licensed professional and permit are required.

Boundary rules:
- Replacing an existing outlet, switch, fixture, faucet, or toilet part at the same location is usually caution.
- Adding a new outlet, running new wire, adding a new circuit, modifying gas lines, or changing structural elements is refuse.
- Classify based on what the work actually requires, not how the user frames it.

Examples:
- "How do I replace an outlet that stopped working?" -> caution
- "How do I add a new outlet to my garage?" -> refuse
- "How do I replace a light switch at the same location?" -> caution
- "How do I move a light switch six inches to the left?" -> refuse
- "Can I replace my water heater myself?" -> refuse

Think through the answer carefully, then respond in the exact output format requested.

Output format:
Tier: <safe|caution|refuse>
Reason: <one short sentence>"""

_CLASSIFIER_USER_PROMPT = "Classify this home repair question:\n\n{question}"
_TIER_LINE_RE = re.compile(r"(?im)^\s*tier\s*:\s*(.+)$")
_REASON_LINE_RE = re.compile(r"(?im)^\s*reason\s*:\s*(.+)$")


def _normalize_tier(candidate: str) -> str | None:
  cleaned = candidate.strip().strip('"\'`.,:;!?()[]{}<>')
  if not cleaned:
    return None
  cleaned = cleaned.split()[0].lower()
  return cleaned if cleaned in VALID_TIERS else None


def _extract_tier(raw_response: str) -> str | None:
  match = _TIER_LINE_RE.search(raw_response)
  if match:
    tier = _normalize_tier(match.group(1))
    if tier:
      return tier

  fallback = re.search(r"\b(safe|caution|refuse)\b", raw_response, re.IGNORECASE)
  if fallback:
    tier = fallback.group(1).lower()
    if tier in VALID_TIERS:
      return tier

  return None


def _extract_reason(raw_response: str) -> str:
  match = _REASON_LINE_RE.search(raw_response)
  if match:
    return match.group(1).strip()
  return raw_response.strip()


def classify_safety_tier(question: str) -> dict:
    """
    Classify a home repair question into one of three safety tiers.

    TODO — Milestone 1:

    Before writing any code, complete specs/classifier-spec.md. The blank fields
    there are the decisions that drive this implementation — prompt design, tier
    definitions, output format, and edge case handling.

    Your implementation should:
      1. Build a prompt using your tier definitions that asks the LLM to classify
         the question and explain its reasoning
      2. Send a single chat completion request (no tools, no history)
      3. Parse the tier and reason out of the raw response text
      4. Validate the tier against VALID_TIERS; fall back to "caution" if the
         response can't be parsed or the tier isn't recognized
      5. Return {"tier": ..., "reason": ...}

    Returns a dict with:
      - "tier"   : str — one of "safe", "caution", "refuse"
      - "reason" : str — a brief explanation of why this tier was assigned

    The three tiers:
      - "safe"    : routine, low-risk repairs most homeowners can handle safely
      - "caution" : doable with care, but mistakes have real cost or mild risk
      - "refuse"  : high-risk repairs that require a licensed professional —
                    mistakes can cause fire, flooding, injury, or structural damage
    """
    completion = _client.chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        max_tokens=128,
        messages=[
            {"role": "system", "content": _CLASSIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": _CLASSIFIER_USER_PROMPT.format(question=question)},
        ],
    )

    raw_response = completion.choices[0].message.content or ""
    tier = _extract_tier(raw_response)
    reason = _extract_reason(raw_response)

    if tier not in VALID_TIERS:
        return {
            "tier": "caution",
            "reason": "Could not confidently parse the classifier output.",
        }

    return {
        "tier": tier,
        "reason": reason or "Classified based on the repair's risk level.",
    }
