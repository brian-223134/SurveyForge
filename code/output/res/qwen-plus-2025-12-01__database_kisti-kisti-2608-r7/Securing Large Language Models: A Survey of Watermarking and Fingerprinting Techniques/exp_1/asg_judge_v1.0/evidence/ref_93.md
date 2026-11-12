# [93] Test-Time Backdoor Attacks on Multimodal Large Language Models
source_url: https://arxiv.org/abs/2402.08577
arxiv_id: 2402.08577   doi: none
first_public: 2024-02-13
fetch_status: ok
printed_title: Test-Time Backdoor Attacks on Multimodal Large Language Models
corpus_title: Test-Time Backdoor Attacks on Multimodal Large Language Models
## abstract
Backdoor attacks are commonly executed by contaminating training data, such that a trigger can activate predetermined harmful effects during the test phase. In this work, we present AnyDoor, a test-time backdoor attack against multimodal large language models (MLLMs), which involves injecting the backdoor into the textual modality using adversarial test images (sharing the same universal perturbation), without requiring access to or modification of the training data. AnyDoor employs similar techniques used in universal adversarial attacks, but distinguishes itself by its ability to decouple the timing of setup and activation of harmful effects. In our experiments, we validate the effectiveness of AnyDoor against popular MLLMs such as LLaVA-1.5, MiniGPT-4, InstructBLIP, and BLIP-2, as well as provide comprehensive ablation studies. Notably, because the backdoor is injected by a universal perturbation, AnyDoor can dynamically change its backdoor trigger prompts/harmful effects, exposing a new challenge for defending against backdoor attacks. Our code is made available at https://github.com/sail-sg/AnyDoor https://github.com/sail-sg/AnyDoor . =-1
## fulltext notes (optional)
