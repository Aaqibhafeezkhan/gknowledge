# BERT

BERT, short for Bidirectional Encoder Representations from Transformers, was introduced in 2018 by Jacob Devlin, Ming-Wei Chang, Kenton Lee and Kristina Toutanova at Google AI Language. The paper was published at NAACL 2019.

BERT pre-trains a Transformer encoder on unlabelled text with two objectives: a masked language model, which hides some words and asks the model to predict them, and next sentence prediction. Because it reads context from both directions, it builds richer representations than left-to-right models.

BERT-base has 110 million parameters and BERT-large has 340 million. After fine-tuning it set a new state of the art on eleven natural language processing tasks, including the GLUE benchmark and the SQuAD question answering dataset.
