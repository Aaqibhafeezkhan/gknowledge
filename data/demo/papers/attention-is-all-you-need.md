# Attention Is All You Need

Attention Is All You Need is a 2017 paper by Ashish Vaswani and seven co-authors at Google Brain and Google Research. It introduced the Transformer, a neural network architecture based entirely on self-attention that dispenses with recurrence and convolutions.

The Transformer uses multi-head attention, so the model can look at different positions of a sequence in parallel, and adds positional encodings to keep word order. Because it avoids sequential computation, it trains much faster than recurrent networks.

The model reached 28.4 BLEU on the WMT 2014 English-to-German translation task, a new state of the art, after training for 3.5 days on eight P100 GPUs. The paper was presented at NeurIPS 2017 and became the foundation of BERT, GPT-3 and almost every modern large language model.
