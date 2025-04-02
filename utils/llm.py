from langchain_groq import ChatGroq

def get_llm(model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.2) -> ChatGroq:
    """
    Returns a configured instance of ChatGroq LLM.
    Args:
        model_name (str): Groq model name.
        temperature (float): LLM sampling temperature.

    Returns:
        ChatGroq: LangChain-compatible LLM instance.
    """
    return ChatGroq(
        model_name=model_name,
        temperature=temperature
    )