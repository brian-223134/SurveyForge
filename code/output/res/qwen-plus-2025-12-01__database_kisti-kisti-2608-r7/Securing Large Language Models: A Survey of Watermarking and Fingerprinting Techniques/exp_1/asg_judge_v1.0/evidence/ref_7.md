# [7] Embedding Watermarks into Deep Neural Networks
source_url: https://arxiv.org/abs/1701.04082
arxiv_id: 1701.04082   doi: none
first_public: 2017-01-15
fetch_status: ok
printed_title: Embedding Watermarks into Deep Neural Networks
corpus_title: Embedding Watermarks into Deep Neural Networks
## abstract
Deep neural networks have recently achieved significant progress. Sharing trained models of these deep neural networks is very important in the rapid progress of researching or developing deep neural network systems. At the same time, it is necessary to protect the rights of shared trained models. To this end, we propose to use a digital watermarking technology to protect intellectual property or detect intellectual property infringement of trained models. Firstly, we formulate a new problem: embedding watermarks into deep neural networks. We also define requirements, embedding situations, and attack types for watermarking to deep neural networks. Secondly, we propose a general framework to embed a watermark into model parameters using a parameter regularizer. Our approach does not hurt the performance of networks into which a watermark is embedded. Finally, we perform comprehensive experiments to reveal the potential of watermarking to deep neural networks as a basis of this new problem. We show that our framework can embed a watermark in the situations of training a network from scratch, fine-tuning, and distilling without hurting the performance of a deep neural network. The embedded watermark does not disappear even after fine-tuning or parameter pruning; the watermark completely remains even after removing 65% of parameters were pruned. The implementation of this research is: https://github.com/yu4u/dnn-watermark
## fulltext notes (optional)
