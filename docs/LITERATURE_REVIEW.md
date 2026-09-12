# Literature review

Fifteen IEEE journal references have resolved Crossref DOI metadata. The discussion below connects their stated topics to this implementation. Metadata verification does not establish reproduction of paper results, and abstracts do not replace full-text methodological review.

## 1 Surveillance Video-and-Language Understanding: From Small to Large Multimodal Models

Tongtong Yuan, Xuange Zhang, Bo Liu, Kun Liu, Jian Jin, Zhenzhen Jiao. IEEE Transactions on Circuits and Systems for Video Technology, 2025. DOI: 10.1109/tcsvt.2024.3462433. https://doi.org/10.1109/tcsvt.2024.3462433

Conceptual foundation for surveillance video-language understanding. It motivates evaluating language on surveillance rather than assuming general-purpose multimodal performance transfers. ARGUS adds a conservative evidence-consistency interface; it does not claim the video-language task as novel.

## 2 Learning Prompt-Enhanced Context Features for Weakly-Supervised Video Anomaly Detection

Yujiang Pu, Xiaoyu Wu, Lulu Yang, Shengjin Wang. IEEE Transactions on Image Processing, 2024. DOI: 10.1109/tip.2024.3451935. https://doi.org/10.1109/tip.2024.3451935

A reproducible weakly supervised detection comparator with an official code repository and released feature links. The published 86.76% UCF-Crime AUC is a reference from that repository. ARGUS must use matched feature, split and frame-alignment conventions before making a numerical comparison.

## 3 Video Violence Rating: A Large-Scale Public Database and A Multimodal Rating Model

Tao Xiang, Hongyan Pan, Zhixiong Nan. IEEE Transactions on Multimedia, 2024. DOI: 10.1109/tmm.2024.3379893. https://doi.org/10.1109/tmm.2024.3379893

A direct precedent for graded video violence ratings. It prevents treating graded severity itself as new. ARGUS's intended comparison concerns interpretable factors and agreement with independently collected ratings, which remain pending.

## 4 StrongSORT: Make DeepSORT Great Again

Yunhao Du, Zhicheng Zhao, Yang Song, Yanyun Zhao, Fei Su, Tao Gong, Hongying Meng. IEEE Transactions on Multimedia, 2023. DOI: 10.1109/tmm.2023.3240881. https://doi.org/10.1109/tmm.2023.3240881

A tracking baseline and useful reference for association quality. ARGUS currently uses simple geometric IoU association, so it does not inherit StrongSORT accuracy or occlusion handling. Persistent IDs in this implementation are local track labels.

## 5 BatchNorm-Based Weakly Supervised Video Anomaly Detection

Yixuan Zhou, Yi Qu, Xing Xu, Fumin Shen, Jingkuan Song, Heng Tao Shen. IEEE Transactions on Circuits and Systems for Video Technology, 2024. DOI: 10.1109/tcsvt.2024.3450734. https://doi.org/10.1109/tcsvt.2024.3450734

A normalization-focused weak-supervision reference. It motivates examining how bag composition interacts with feature statistics. ARGUS selects LayerNorm as an implementation choice, but this does not reproduce the paper's method or establish a performance improvement.

## 6 Weakly-Supervised Video Anomaly Detection With Snippet Anomalous Attention

Yidan Fan, Yongxin Yu, Wenhuan Lu, Yahong Han. IEEE Transactions on Circuits and Systems for Video Technology, 2024. DOI: 10.1109/tcsvt.2024.3350084. https://doi.org/10.1109/tcsvt.2024.3350084

A snippet-attention reference for prioritizing anomalous temporal segments. ARGUS includes a learnable attention pooling branch and tests its training path. A controlled ablation is still needed to establish its benefit.

## 7 Extended Graph Learning for Weakly Supervised Video Anomaly Detection

Jixiang Deng, Ying Liu, Chunguang Li. IEEE Transactions on Circuits and Systems for Video Technology, 2026. DOI: 10.1109/tcsvt.2025.3625570. https://doi.org/10.1109/tcsvt.2025.3625570

This paper extends the comparison set for weakly supervised temporal and feature modeling. Its contribution should be compared on matched datasets and splits. ARGUS does not reproduce or claim its published performance. Full-text protocol details should be reviewed before adopting a numerical baseline.

## 8 Enhancing Weakly-Supervised Video Anomaly Detection With Temporal Constraints

Francisco Caetano, Pedro Carvalho, Christina Mastralexi, Jaime S. Cardoso. IEEE Access, 2025. DOI: 10.1109/access.2025.3560767. https://doi.org/10.1109/access.2025.3560767

This paper extends the comparison set for weakly supervised temporal and feature modeling. Its contribution should be compared on matched datasets and splits. ARGUS does not reproduce or claim its published performance. Full-text protocol details should be reviewed before adopting a numerical baseline.

## 9 Reconstructive Visual Tuning for Weakly Supervised Video Anomaly Detection

Shuangqing Zhang, Wei Xu, Yuqi Fang, Fan Lyu, Leilei Ma, Gangming Zhao, Fang Zhao, Caifeng Shan, Liang Wang. IEEE Transactions on Information Forensics and Security, 2026. DOI: 10.1109/tifs.2026.3729516. https://doi.org/10.1109/tifs.2026.3729516

This paper extends the comparison set for weakly supervised temporal and feature modeling. Its contribution should be compared on matched datasets and splits. ARGUS does not reproduce or claim its published performance. Full-text protocol details should be reviewed before adopting a numerical baseline.

## 10 Delving Into Instance Modeling for Weakly Supervised Video Anomaly Detection

Shengyang Sun, Jiashen Hua, Junyi Feng, Dongxu Wei, Baisheng Lai, Xiaojin Gong. IEEE Transactions on Circuits and Systems for Video Technology, 2025. DOI: 10.1109/tcsvt.2025.3546766. https://doi.org/10.1109/tcsvt.2025.3546766

This paper extends the comparison set for weakly supervised temporal and feature modeling. Its contribution should be compared on matched datasets and splits. ARGUS does not reproduce or claim its published performance. Full-text protocol details should be reviewed before adopting a numerical baseline.

## 11 Learning Confidence-Aware Prototypes for Weakly-Supervised Video Anomaly Detection

Zhao Xie, Jinkang Luo, Kewei Wu, Zhehan Kan, Dan Guo. IEEE Transactions on Circuits and Systems for Video Technology, 2026. DOI: 10.1109/tcsvt.2025.3628630. https://doi.org/10.1109/tcsvt.2025.3628630

This paper extends the comparison set for weakly supervised temporal and feature modeling. Its contribution should be compared on matched datasets and splits. ARGUS does not reproduce or claim its published performance. Full-text protocol details should be reviewed before adopting a numerical baseline.

## 12 Enhancing Weakly Supervised Multimodal Video Anomaly Detection Through Text Guidance

Shengyang Sun, Jiashen Hua, Junyi Feng, Xiaojin Gong. IEEE Transactions on Multimedia, 2026. DOI: 10.1109/tmm.2026.3668927. https://doi.org/10.1109/tmm.2026.3668927

This paper extends the comparison set for multimodal or language-guided detection. Its contribution should be compared on matched datasets and splits. ARGUS does not reproduce or claim its published performance. Full-text protocol details should be reviewed before adopting a numerical baseline.

## 13 Feature Differentiation Reconstruction Network for Weakly-Supervised Video Anomaly Detection

Yiling Gong, Sihui Luo, Chong Wang, Yujie Zheng. IEEE Signal Processing Letters, 2023. DOI: 10.1109/lsp.2023.3324299. https://doi.org/10.1109/lsp.2023.3324299

This paper extends the comparison set for weakly supervised temporal and feature modeling. Its contribution should be compared on matched datasets and splits. ARGUS does not reproduce or claim its published performance. Full-text protocol details should be reviewed before adopting a numerical baseline.

## 14 Audio-Visual Collaborative Learning for Weakly Supervised Video Anomaly Detection

Jingke Meng, Huilin Tian, Ge Lin, Jian-Fang Hu, Wei-Shi Zheng. IEEE Transactions on Multimedia, 2025. DOI: 10.1109/tmm.2025.3535377. https://doi.org/10.1109/tmm.2025.3535377

This paper extends the comparison set for multimodal or language-guided detection. Its contribution should be compared on matched datasets and splits. ARGUS does not reproduce or claim its published performance. Full-text protocol details should be reviewed before adopting a numerical baseline.

## 15 PLOVAD: Prompting Vision-Language Models for Open Vocabulary Video Anomaly Detection

Chenting Xu, Ke Xu, Xinghao Jiang, Tanfeng Sun. IEEE Transactions on Circuits and Systems for Video Technology, 2025. DOI: 10.1109/tcsvt.2025.3528108. https://doi.org/10.1109/tcsvt.2025.3528108

This paper extends the comparison set for multimodal or language-guided detection. Its contribution should be compared on matched datasets and splits. ARGUS does not reproduce or claim its published performance. Full-text protocol details should be reviewed before adopting a numerical baseline.
