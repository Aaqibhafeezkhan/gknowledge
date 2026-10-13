# Chain-of-Thought Prompting

Chain-of-Thought Prompting Elicits Reasoning in Large Language Models is a 2022 paper by Jason Wei and colleagues at Google Brain, presented at NeurIPS 2022.

Instead of showing only question and answer pairs, the prompt includes worked examples with the intermediate reasoning steps written out. Large models then produce their own step-by-step reasoning before giving the final answer. This sharply improves arithmetic, commonsense and symbolic reasoning.

With eight chain-of-thought examples, PaLM 540B reached state-of-the-art accuracy on GSM8K, a benchmark of grade-school math word problems, surpassing fine-tuned GPT-3 with a verifier. The ability emerges only at large scale, roughly around one hundred billion parameters, and does not help small models.
