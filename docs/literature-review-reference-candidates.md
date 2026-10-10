# DermTrack literature review — verified reference candidates

This is the initial source list for the lecturer's literature survey. The survey requirement is approximately 10–15 relevant papers/articles/white papers and, for each selected source:

**Paper → Method → Dataset → Major Findings → Performance → Limitations**

The DOI/stable links below were checked against OpenAlex bibliographic records on 2026-08-27. Full-text reading is still required before writing performance claims.

## Dermatology image AI and multimodal clinical AI

1. Liu, Y. et al. (2020). **A deep learning system for differential diagnosis of skin diseases.** *Nature Medicine*. https://doi.org/10.1038/s41591-020-0842-3  
   Relevance: dermatology image-based differential diagnosis; useful baseline for method, clinical image datasets, and external evaluation.

2. Daneshjou, R. et al. (2022). **Disparities in dermatology AI performance on a diverse, curated clinical image set.** *Science Advances*. https://doi.org/10.1126/sciadv.abq6147  
   Relevance: skin-tone diversity, DDI dataset, subgroup performance, and fairness limitations.

3. Hekler, A. et al. (2019). **Superior skin cancer classification by the combination of human and artificial intelligence.** *European Journal of Cancer*. https://doi.org/10.1016/j.ejca.2019.07.019  
   Relevance: human–AI collaboration rather than autonomous replacement; useful for explaining clinician-in-the-loop design.

4. Yan, S. et al. (2025). **A multimodal vision foundation model for clinical dermatology.** *Nature Medicine*. https://doi.org/10.1038/s41591-025-03747-y  
   Relevance: recent dermatology-specific multimodal foundation-model research; useful comparison with DermTrack's image-observation workflow.

5. Zhou, J. et al. (2024). **Pre-trained multimodal large language model enhances dermatological diagnosis using SkinGPT-4.** *Nature Communications*. https://doi.org/10.1038/s41467-024-50043-3  
   Relevance: dermatology vision-language modelling; useful for comparing multimodal generation, evaluation design, and diagnostic-risk limitations.

6. **Transparent medical image AI via an image–text foundation model grounded in medical literature.** (2024). *Nature Medicine*. https://doi.org/10.1038/s41591-024-02887-x  
   Relevance: image–text grounding and medical-literature support; directly relevant to evidence-grounded image explanations.

7. Groh, M. et al. (2022). **Towards Transparency in Dermatology Image Datasets with Skin Tone Annotations by Experts, Crowds, and an Algorithm.** *Proceedings of the ACM on Human-Computer Interaction*. https://doi.org/10.1145/3555634  
   Relevance: dataset annotation quality, skin-tone metadata, and fairness measurement.

8. Abhishek, K., Jain, A., & Hamarneh, G. (2025). **Investigating the Quality of DermaMNIST and Fitzpatrick17k Dermatological Image Datasets.** *Scientific Data*. https://doi.org/10.1038/s41597-025-04382-5  
   Relevance: dataset quality and label reliability; useful for discussing why benchmark performance may not equal clinical performance.

## RAG, medical language models, and evidence grounding

9. Lewis, P. et al. (2020). **Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.** *Advances in Neural Information Processing Systems*. https://arxiv.org/abs/2005.11401  
   Relevance: foundational RAG method; establishes retrieval plus generation rather than relying only on model parameters.

10. Xiong, G., Jin, Q., Lu, Z., & Zhang, A. (2024). **Benchmarking Retrieval-Augmented Generation for Medicine.** *Findings of the Association for Computational Linguistics*. https://doi.org/10.18653/v1/2024.findings-acl.372  
    Relevance: medical RAG benchmarking; useful for evaluating retrieval quality, answer quality, and medical-domain limitations.

11. Zakka, C. et al. (2024). **Almanac — Retrieval-Augmented Language Models for Clinical Medicine.** *NEJM AI*. https://doi.org/10.1056/aioa2300068  
    Relevance: clinical RAG using external medical knowledge; directly relevant to trusted-source retrieval and reducing unsupported answers.

12. Gao, Y. et al. (2023). **Retrieval-Augmented Generation for Large Language Models: A Survey.** arXiv. https://doi.org/10.48550/arxiv.2312.10997  
    Relevance: taxonomy of RAG architectures, indexing, retrieval, generation, evaluation, and failure modes. Use as a survey/background source rather than the main experimental evidence.

13. Jeong, M. et al. (2024). **Improving medical reasoning through retrieval and self-reflection with retrieval-augmented large language models.** *Bioinformatics*. https://doi.org/10.1093/bioinformatics/btae238  
    Relevance: medical reasoning with retrieval and self-reflection; useful for discussing answer verification and remaining hallucination risks.

## Fairness, safety, and clinical deployment

14. Ghassemi, M., Oakden-Rayner, L., & Beam, A. L. (2021). **The false hope of current approaches to explainable artificial intelligence in health care.** *The Lancet Digital Health*. https://doi.org/10.1016/S2589-7500(21)00208-9  
    Relevance: cautions against treating explanations as proof of correctness; relevant to DermTrack's non-diagnostic observation policy.

15. **Algorithmic fairness in artificial intelligence for medicine and healthcare.** (2023). *Nature Biomedical Engineering*. https://doi.org/10.1038/s41551-023-01056-8  
    Relevance: fairness definitions, subgroup evaluation, clinical bias, and governance.

16. Liu, X. et al. (2020). **Reporting guidelines for clinical trial reports for interventions involving artificial intelligence: the CONSORT-AI extension.** *Nature Medicine*. https://doi.org/10.1038/s41591-020-1034-x  
    Relevance: reporting and evaluation checklist for clinical AI interventions.

17. World Health Organization. (2021). **Ethics and governance of artificial intelligence for health.** https://www.who.int/publications/i/item/9789240029200  
    Relevance: authoritative governance, safety, human oversight, privacy, accountability, and equity guidance. This is a policy report, not a peer-reviewed experimental paper.

## Initial recommended final selection

For a 10–15-source lecturer submission, the strongest first selection is likely:

- Liu et al. (2020)
- Daneshjou et al. (2022)
- Hekler et al. (2019)
- Yan et al. (2025)
- SkinGPT-4 (2024)
- Transparent medical image AI (2024)
- Groh et al. (2022)
- Lewis et al. (2020)
- Xiong et al. (2024)
- Almanac (2024)
- Jeong et al. (2024)
- Algorithmic fairness (2023)
- CONSORT-AI (2020)
- WHO (2021)

Next step: read the selected full texts and complete one comparison row per source with verified dataset names, sample sizes, metrics, findings, and limitations. Do not infer or invent performance numbers from titles or abstracts.
