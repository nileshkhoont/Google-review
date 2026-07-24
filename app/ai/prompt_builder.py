"""Builds dynamic prompts sent to Gemini for review generation."""

from __future__ import annotations
import json
import random

# -------------------------------------------------------------------------
# Review tone
# -------------------------------------------------------------------------

_TONE_VARIANTS = [
    "warm and appreciative",
    "friendly and conversational",
    "genuinely impressed",
    "relaxed and natural",
    "professional but human",
    "pleasant and authentic",
    "enthusiastic without exaggeration",
    "calm and satisfied",
]

# -------------------------------------------------------------------------
# Review length
# -------------------------------------------------------------------------

_LENGTH_VARIANTS = [
    "75-110 characters",
    "110-150 characters",
    "150-175 characters",
    "175-200 characters",
]

# -------------------------------------------------------------------------
# Writing style
# -------------------------------------------------------------------------

_WRITING_STYLES = [
    "sound like a first-time customer",
    "sound like a returning customer",
    "sound sincere and appreciative",
    "sound naturally conversational",
    "sound straightforward and honest",
    "sound relaxed and genuine",
]

# -------------------------------------------------------------------------
# Review structure
# -------------------------------------------------------------------------


_REVIEW_STRUCTURES = [
    "Start with the overall experience, then mention the most meaningful part, then finish naturally.",
    "Start with what stood out first, then explain why, then conclude naturally.",
    "Describe the experience first, then explain what impressed you most.",
    "Begin naturally, mention one memorable moment, then finish positively.",
    "Start with a genuine first impression, then explain the experience, then finish naturally.",
]

# -------------------------------------------------------------------------
# Opening guidance
# -------------------------------------------------------------------------

_OPENING_GUIDANCE = [
    "Begin naturally without sounding scripted.",
    "Do not always begin with 'I had a great experience'.",
    "Use varied sentence openings.",
    "Write as though this customer is sharing a genuine experience.",
    "Keep the opening simple and believable.",
]

# -------------------------------------------------------------------------
# Ending guidance
# -------------------------------------------------------------------------

_ENDING_GUIDANCE = [
    "Finish naturally.",
    "Do not sound promotional.",
    "Avoid generic endings.",
    "End with a realistic final thought.",
    "Keep the ending human and believable.",
]



# -------------------------------------------------------------------------
# Generic fallback aspects
# -------------------------------------------------------------------------

_FALLBACK_ASPECTS = [
    "overall experience",
    "professionalism",
    "communication",
    "responsiveness",
    "service quality",
    "attention to detail",
    "customer care",
    "reliability",
]

# -------------------------------------------------------------------------
# Rating guidance
# -------------------------------------------------------------------------

_RATING_GUIDANCE = {
    5: (
        "The customer is extremely satisfied. "
        "Write a naturally enthusiastic review without exaggeration."
    ),

    4: (
        "The customer is very satisfied. "
        "Write a positive review with a balanced, believable tone."
    ),

    3: (
        "The customer had a generally good experience. "
        "Write a pleasant review without making it sound perfect."
    ),
}

# -------------------------------------------------------------------------
# Helper
# -------------------------------------------------------------------------

def build_review_prompt(
    business_name: str,
    service_type: str,
    business_description: str | None = None,
    rating: int | None = None,
    selected_review_aspects: list[str] | None = None,
    review_count: int = 1,
) -> str:
    """
    Build a prompt that generates highly unique, human-like Google reviews.

    Priority Order

    CASE 1 (Customer selected aspects)

        1. Selected Review Aspects
        2. Business Description
        3. Rating
        4. Service Type
        5. Business Name
        6. Random writing style

    CASE 2 (No selected aspects)

        1. Business Description
        2. Fallback Review Aspects
        3. Rating
        4. Service Type
        5. Business Name
        6. Random writing style
    """

    # ---------------------------------------------------------
    # Normalize rating
    # ---------------------------------------------------------

    if rating is None:
        effective_rating = 5
    else:
        effective_rating = max(3, min(int(rating), 5))

    rating_instruction = _RATING_GUIDANCE[effective_rating]

    # ---------------------------------------------------------
    # Random writing variation
    # (Only affects HOW the review is written,
    # not WHAT is written.)
    # ---------------------------------------------------------

    tone = random.choice(_TONE_VARIANTS)
    length = random.choice(_LENGTH_VARIANTS)
    writing_style = random.choice(_WRITING_STYLES)
    structure = random.choice(_REVIEW_STRUCTURES)
    opening = random.choice(_OPENING_GUIDANCE)
    ending = random.choice(_ENDING_GUIDANCE)

    # ---------------------------------------------------------
    # Business description
    # ---------------------------------------------------------

    has_description = (
        business_description is not None
        and business_description.strip() != ""
    )

    if has_description:

        description_block = f"""
BUSINESS DESCRIPTION

{business_description.strip()}
"""

    else:

        description_block = """
BUSINESS DESCRIPTION

No business description was provided.

Use only the Business Name and Service Type.
"""

    # ---------------------------------------------------------
    # Customer selected aspects
    # ---------------------------------------------------------

    selected_review_aspects = [
        a.strip()
        for a in (selected_review_aspects or [])
        if a.strip()
    ]

    if selected_review_aspects:

        aspects_block = f"""

CUSTOMER SELECTED REVIEW ASPECTS

The customer selected these review aspects:

{", ".join(selected_review_aspects)}

IMPORTANT

These aspects represent the customer's actual experience.

Every selected aspect MUST naturally appear somewhere in the review.

Do NOT simply list the aspects.

Blend them naturally into complete sentences.

The review should feel like the customer genuinely experienced these things.
"""

    else:

        fallback = random.sample(
            _FALLBACK_ASPECTS,
            k=min(2, len(_FALLBACK_ASPECTS))
        )

        aspects_block = f"""

NO REVIEW ASPECTS WERE SELECTED

Use these fallback review aspects:

{", ".join(fallback)}

Treat these as the customer's experience.

These fallback aspects are ONLY used because the customer did not select any aspects.
"""

    # ---------------------------------------------------------
    # Priority instructions
    # ---------------------------------------------------------

    if selected_review_aspects:

        priority_block = """
CONTENT PRIORITY

1. Customer Selected Review Aspects (Highest Priority)

Every selected aspect must naturally appear in the review.

2. Business Description

Use it to explain and support those customer experiences.

Never contradict the Business Description.

Never invent information.

3. Rating

Adjust only the positivity.

4. Service Type

Use only if needed.

5. Business Name

Mention naturally if it fits.
"""

    else:

        priority_block = """
CONTENT PRIORITY

1. Business Description (Highest Priority)

Build the review mainly from the Business Description.

2. Fallback Review Aspects

Use them only to decide what the customer appreciated.

Never let fallback aspects override the Business Description.

3. Rating

Adjust only the positivity.

4. Service Type

Use only if needed.

5. Business Name

Mention naturally if appropriate.
"""
    return f"""
You are writing a Google Review.

The review must sound exactly like it was written by a real customer after using this business.

--------------------------------------------------
BUSINESS INFORMATION
--------------------------------------------------

Business Name:
{business_name}

Service Type:
{service_type}

{description_block}

--------------------------------------------------
CUSTOMER RATING
--------------------------------------------------

The customer selected {rating if rating is not None else 5} stars.

When generating the review, write with the tone of a {effective_rating}-star experience.

{rating_instruction}

--------------------------------------------------
CUSTOMER EXPERIENCE
--------------------------------------------------

{aspects_block}

--------------------------------------------------
CONTENT PRIORITY
--------------------------------------------------

{priority_block}

--------------------------------------------------
BUSINESS DESCRIPTION RULES
--------------------------------------------------

If a Business Description exists:

• Treat it as the primary source of business knowledge.

• Use it to support the customer's selected experience.

• Mention only the details that naturally relate to the selected review aspects.

• Never copy sentences from the description.

• Never rewrite the description.

• Never list every service.

• Never sound like marketing content.

If NO Business Description exists:

• Use only the Business Name.

• Use only the Service Type.

• Never invent services.

• Never invent products.

• Never invent facilities.

• Never invent departments.

• Never invent equipment.

• Never invent technologies.

--------------------------------------------------
CUSTOMER EXPERIENCE RULES
--------------------------------------------------

If customer selected review aspects:

• Every selected aspect MUST naturally appear in the review.

• Integrate the aspects into natural sentences instead of listing them.

• Use the Business Description to support and expand those experiences whenever possible.

• If the Business Description does not support a selected aspect, mention it only in a general, believable way.

If NO review aspects were selected:

• Build the review primarily from the Business Description.

• Use the fallback aspects only as secondary guidance for what the customer appreciated.

• The Business Description always has higher priority than fallback aspects.

--------------------------------------------------
ANTI-HALLUCINATION
--------------------------------------------------

Never invent any product, service, facility, treatment, department, equipment, technology, event, or customer experience that is not supported by the provided Business Description, Business Name, Service Type, or Customer Selected Review Aspects.

If information is limited, keep the review general rather than making assumptions.

Every statement in the review must be supported by at least one of:

• Business Description

• Business Name

• Service Type

• Customer Selected Review Aspects

--------------------------------------------------
UNIQUENESS
--------------------------------------------------

Assume this business may receive thousands of AI-generated reviews.

Every review must feel like it was written by a different real customer.

Naturally vary:

• wording

• vocabulary

• sentence structure

• review flow

• sentence length

• emphasis

• openings

• endings

• writing style

Never repeat common phrases or follow the same sentence pattern.

Even when customers choose the same rating and the same review aspects, generate a distinctly different review while preserving the same meaning and remaining fully relevant to this business.

--------------------------------------------------
WRITING STYLE
--------------------------------------------------

Tone:
{tone}

Length:
{length}

Style:
{writing_style}

Structure:
{structure}

Opening:
{opening}

Ending:
{ending}

These writing preferences are ONLY for writing style.

They must NEVER override:

1. Customer Selected Review Aspects

2. Business Description

3. Rating

--------------------------------------------------
OUTPUT
--------------------------------------------------
Generate exactly {review_count} completely different reviews.

Each review MUST:
• Follow every rule above.
• Be about the same business.
• Be between 75 and 200 characters, including spaces. Never shorter than 75 characters. Never longer than 200 characters.
• Naturally include the customer's selected review aspects.
• Sound like it was written by a different customer.
• Never repeat wording, sentence structure, or review flow from another review.

Return ONLY valid JSON.

valid Format:

{{
  "reviews": [
    {{
      "review": "First review..."
    }},
    {{
      "review": "Second review..."
    }}
  ]
}}

Rules:

Return exactly {review_count} reviews.
Do not return fewer reviews.
Do not return more reviews.
Do not wrap the JSON in markdown.
Do not add any text before or after the JSON.
Do NOT use quotation marks.
Do NOT use emojis.
Do NOT use hashtags.
Do NOT mention star ratings.
Do NOT add titles.
Do NOT add labels.
Do NOT explain your reasoning.
Return only the final review text.
""".strip()


def build_review_aspects_prompt(
    service_type: str,
    business_description: str | None = None,
) -> str:
    """
    Build a prompt that asks Gemini to generate customer review aspect
    suggestions for a business owner.
    """

    description = business_description.strip() if business_description else "Not provided"

    return f"""
You are helping a business owner create review suggestion options.

Business Type:  
{service_type}

Business Description:
{description}

Generate exactly 8 short review aspects that customers may naturally mention in a review.

Rules:

- Return plain text only.
- Return exactly one aspect per line.
- Do NOT use numbering.
- Do NOT use bullet points.
- Do NOT use quotation marks.
- Do NOT return JSON.
- Do NOT include explanations or headings.
- Do NOT include markdown.
- Each aspect should contain only 2-4 words.
- Think from a real customer's perspective.
- Keep the aspects broad enough that many customers can relate to them.
- Avoid duplicates.
- Use the business description only as background context.

Example output:

Friendly staff
Quick response
Professional service
Clean environment
Easy booking
Clear communication
Comfortable atmosphere
Reasonable pricing
"""

def build_translation_prompt(
    reviews: list[str],
    language: str,
) -> str:
    """
    Build a prompt that rewrites an English review into natural
    Roman Gujarati or Roman Hindi.

    The meaning, tone and customer experience must remain unchanged.
    """

    if language == "Gujarati":
        language_name = "Roman Gujarati"
        native_language = "Gujarati"
        example = """Example:
        English:
        What impressed me the most was how clean the hospital was and how caring the staff were.
        Output (Roman Gujarati):
        Mane sauthi vadhu je vastu game e hati hospital ni safai ane staff no caring nature. Badhae khub prem thi vaat kari ane darek vaat ma madad kari.

        Example 
        English:
        The modern equipment made me feel confident that I was receiving good treatment.
        Output (Roman Gujarati):
        Hospital ma modern equipment joi ne mane kharekhar confidence aavyo ke hu sacha jagyae treatment lai rahyo chu.
        Notice:
        - Sounds like a real Gujarati customer.
        - Natural WhatsApp typing style.
        - NOT a word-for-word translation.
        - Uses everyday Gujarati that people actually speak.
        """.strip()

    elif language == "Hindi":
        language_name = "Roman Hindi"
        native_language = "Hindi"
        example = """Example :
           English:
           What impressed me the most was how clean the hospital was and how caring the staff were.
           Output (Roman Hindi):
           Mujhe sabse zyada hospital ki safai aur staff ka caring nature pasand aaya. Sabne bahut pyaar se baat ki aur har jagah madad ki.
           
           Example :
           English:
           The modern equipment made me feel confident that I was receiving good treatment.
           Output (Roman Hindi):
           Hospital me modern equipment dekhkar mujhe bharosa ho gaya ki mera treatment sahi jagah ho raha hai.
           Notice:
           - Sounds like a real Hindi customer.
           - Natural WhatsApp typing style.
           - NOT a word-for-word translation.
           - Uses everyday spoken Hindi.
            """.strip()

    else:
        raise ValueError("Unsupported language")

    return f"""
Rewrite the following English Google Reviews into natural {language_name}.
The input contains multiple independent customer reviews.
Treat every review separately.
Do NOT merge reviews.
Do NOT split reviews.
Translate each review independently while preserving its own meaning, tone, writing style and customer experience.
This is NOT a word-for-word translation task.
Your goal is to rewrite every review so it feels like it was originally written by a real native {native_language} speaker after visiting the business.
Imagine each customer is sending their review to a friend on WhatsApp, and then posting the same review on Google.

--------------------------------------------------
TRANSLATION RULES
--------------------------------------------------

- Translate the ENTIRE review into {language_name}.
- Rewrite naturally instead of translating literally.
- Preserve the exact meaning.
- Preserve the customer's experience.
- Preserve the original tone and emotion.
- Do NOT change the overall message.
- Do NOT add any new information.
- Do NOT remove any information.
- Do NOT shorten the review.
- Do NOT make the review longer.
- Translate every sentence completely.
- Never leave any sentence in English.
- Keep business names exactly as they are.
- Use ONLY the English alphabet (A-Z).
- Do NOT use the {native_language} script.

--------------------------------------------------
WHATSAPP WRITING STYLE
--------------------------------------------------

- Write exactly how real native {native_language} speakers type on WhatsApp.
- The review should feel like it was personally written by a genuine customer.
- Use simple, everyday conversational language.
- Prefer commonly spoken words instead of formal or textbook language.
- Make the review friendly, smooth, and easy to read.
- The final review should NOT sound like a translation.
- The final review should sound like it was originally written in {language_name}.
- Do NOT sound robotic or AI-generated.
-Do NOT use textbook Gujarati.
-Do NOT use translation-style Gujarati.
-Rewrite every sentence naturally.
-Prefer everyday expressions that Gujarati people commonly use.
-The final review should sound like it was originally written in Gujarati.

--------------------------------------------------
NATURAL REWRITING RULES
--------------------------------------------------

- This is a natural rewrite, NOT a literal translation.
- Never translate English phrases word-for-word.
- If a sentence sounds awkward after translation, rewrite it naturally while keeping the exact meaning.
- Use natural sentence structure of {language_name}.
- Never mix English grammar with {language_name} grammar.
- Every sentence should be immediately understandable to an average native speaker.
- Avoid unnatural wording.
- Avoid meaningless phrases.
- The review should read smoothly from beginning to end.

--------------------------------------------------
LANGUAGE-SPECIFIC RULES
--------------------------------------------------

For Roman Gujarati:

- Write exactly how Gujarati people normally type on WhatsApp.
-Use the kind of Gujarati that people actually speak every day.
- Use natural Gujarati vocabulary and grammar.
- Prefer everyday Gujarati words.
- Avoid formal Gujarati.
- Do NOT use Hindi grammar or Hindi words unless they are commonly used in everyday Gujarati conversation.
-Mane...,
Mane evu lagyu...,
Kharekhar...,
Khub saras...,
Dil thi...,
Badha...,
Aakho experience...,
Maro experience...,
Hu fari jarur avish...,
Badha khub helpful hata...,
Khub satisfaction malyu...,
Ekdam saras...,
- Never generate meaningless phrases such as:
  "tevija spinalu",
  "te hu dedicated",
  or similar awkward literal translations.
- If a sentence sounds unnatural, rewrite it completely while preserving the meaning.

For Roman Hindi:

- Write exactly how Hindi speakers normally type on WhatsApp.
- Use natural spoken Hindi.
- Avoid bookish or overly formal Hindi.
- Do NOT use Gujarati grammar or Gujarati words.
- Rewrite awkward sentences naturally while preserving the meaning.

--------------------------------------------------
OUTPUT RULES
--------------------------------------------------
- Return ONLY valid JSON.
- Do NOT include the original English reviews.
- Do NOT combine English and translated text.
- Do NOT include explanations.
- Do NOT include headings.
- Do NOT include notes.
- Do NOT include quotation marks.
- Do NOT include markdown.
- Do NOT number anything.
-Return exactly one translated review for every English review.

valid Format:

{{
  "reviews": [
    {{
      "review": "Translated review 1"
    }},
    {{
      "review": "Translated review 2"
    }}
  ]
}}
--------------------------------------------------
QUALITY CHECK
--------------------------------------------------

Before returning the answer, silently verify for EVERY review:

- Every sentence is completely translated.
- No English sentence remains.
- No literal translation sounds awkward.
- No meaningless phrases are present.
- The review sounds like a real WhatsApp message written by a native {native_language} speaker.
- The meaning matches the original review exactly.
- The review is smooth, conversational, and natural.
- The number of translated reviews exactly matches the number of English reviews.
{example}

English Reviews: {json.dumps(
    [
        {"review": review}
        for review in reviews
    ],
    indent=2,
    ensure_ascii=False,
)}

""".strip()