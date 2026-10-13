# GPT-3

Language Models are Few-Shot Learners is the 2020 paper by Tom Brown and colleagues at OpenAI that introduced GPT-3. The model has 175 billion parameters, more than ten times larger than any earlier non-sparse language model.

The key finding is in-context learning. Given only a few examples written in the prompt, GPT-3 performs translation, question answering and arithmetic without any gradient update or fine-tuning. Performance improves smoothly with model size, and few-shot results approached those of fine-tuned systems on many benchmarks.

GPT-3 was trained on roughly 300 billion tokens of filtered Common Crawl, books and Wikipedia. The paper also discussed risks such as bias and misuse for generating misleading text.
