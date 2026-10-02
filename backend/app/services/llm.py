class LLMService:
    """Provider-neutral interface.

    In the hackathon, plug Gemini/OpenAI here after the core order engine works.
    The rest of the backend should not need to change.
    """

    def generate_clarification(self, question: str) -> str:
        return question

    def generate_confirmation(self, total: float) -> str:
        return f"Your total is ₹{total:.2f}. Shall I confirm the order?"
