from transformers import AutoTokenizer

def count_tokens(text: str, model: str = "nvidia/Llama-3.3-70B-Instruct-FP4") -> int:
    """
    Estimate the number of tokens in a string for a given model.
    """
    tokenizer = AutoTokenizer.from_pretrained(model)
    tokens = tokenizer.tokenize(text)
    num_tokens = len(tokens)
    return num_tokens