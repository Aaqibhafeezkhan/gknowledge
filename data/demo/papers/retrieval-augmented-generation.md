# Retrieval-Augmented Generation

Retrieval-Augmented Generation, or RAG, was introduced in 2020 by Patrick Lewis and colleagues at Facebook AI Research, University College London and New York University. The paper appeared at NeurIPS 2020.

RAG combines two kinds of memory. The parametric memory is a pre-trained sequence-to-sequence model, BART. The non-parametric memory is a dense vector index of Wikipedia that is searched with a neural retriever called DPR. For each question the retriever finds relevant passages and the generator conditions on them to write the answer.

The paper defines RAG-Sequence, which uses the same passages for the whole output, and RAG-Token, which can use different passages for each token. RAG set a new state of the art on several open-domain question answering tasks and produced more factual answers than parametric-only models. It lets knowledge be updated by changing the index instead of retraining the model.
