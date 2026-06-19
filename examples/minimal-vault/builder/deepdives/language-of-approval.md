**Authors:** Agam Goyal, Charlotte Lambert, Eshwar Chandrasekharan (UIUC) · **CHI 2026**

**Research question.** (RQ1) Which *linguistic attributes* causally drive positive feedback? (RQ2) Can those attributes predict high-quality posts in real time? (RQ3) Do community guidelines articulate them?

**Method.** **[[causal-inference-observational|Selection-on-observables causal inference]]** + **predictive modeling** on **11M posts from 100 subreddits**. LIWC psycholinguistic features; outcomes include top-quartile score, awards, gold. Plus an **audit of subreddit guidelines**.

**Findings.** **Broad help requests ≈ 43% higher odds** of high scores; **clear, readable writing ≈ +40% odds**. **Complicated language, tentative style, and toxicity reduce rewards.** Predictors achieve **high AUC**. Guideline audit reveals a **[[policy-practice-gap]]**: rules emphasize civility/formatting, not what actually earns approval.

**Claims & evidence.** Strong — causal identification + predictive validation on a large multi-community sample, grounded in a real artifact audit.

**Limitations.** Observational causal assumptions; reward signals are proxies for "approval."

**Contributes to:** [[positive-reinforcement]], [[policy-practice-gap]]. Direct successor to [[positive-reinforcement-reddit]]; informs governance design beyond punitive moderation.
