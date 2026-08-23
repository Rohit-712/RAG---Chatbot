"""
LLM service using local Ollama.
"""

from ollama import chat

from app.config import settings


SYSTEM_PROMPT = """
You are a helpful document question-answering assistant.

Your job is to answer the user's question using the provided document context.

IMPORTANT RULES:

1. Use the provided context as the primary source of truth.
2. If the answer is clearly present in the context, answer it directly.
3. Do NOT say "I don't know" when the context contains enough information.
4. If the context contains only partial information, give the answer using
   the information that is available and clearly mention what is missing.
5. If the answer is completely absent from the context, say:
   "I couldn't find that information in the selected documents."
6. Do not invent names, skills, education, experience, dates, companies,
   projects, or other facts.
7. For questions about a resume, summarize the relevant information from
   the retrieved resume chunks instead of refusing to answer.
8. Be concise but informative.
9. Do not mention internal RAG processes, embeddings, FAISS, or retrieved
   chunks unless the user asks about the system itself.
10. When useful, organize answers using short bullet points.

The current document context is more important than previous conversation
answers. Previous assistant responses may be incomplete or incorrect.
"""


class LLMService:

    def __init__(self) -> None:
        self.model = "llama3.2:3b"

    def generate_answer(
        self,
        question: str,
        context_chunks: list[str],
        chat_history: list[dict] | None = None,
    ) -> str:

        if context_chunks:
            context_block = "\n\n--- DOCUMENT CONTEXT ---\n\n".join(
                context_chunks
            )
        else:
            context_block = "No relevant document context was found."

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

        # Include recent conversation for continuity.
        # Limit it so old answers don't dominate the current context.
        for turn in (chat_history or [])[-4:]:
            messages.append(
                {
                    "role": turn["role"],
                    "content": turn["content"],
                }
            )

        messages.append(
            {
                "role": "user",
                "content": f"""
DOCUMENT CONTEXT:

{context_block}

CURRENT QUESTION:

{question}

Answer the current question using the document context above.
If the context contains the answer, provide the answer directly.
""",
            }
        )

        response = chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": 0.2,
            },
        )

        return response["message"]["content"].strip()


llm_service = LLMService()
