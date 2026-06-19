**Authors:** Charlotte Lambert, Koustuv Saha, Eshwar Chandrasekharan (UIUC) · **CHI 2025** · [doi:10.1145/3706598.3713830](https://doi.org/10.1145/3706598.3713830)

**Research question.** Does receiving positive feedback causally change a Reddit user's later behavior, and who benefits most? Framed via Grimmelmann's moderation taxonomy — positive feedback as a form of *[[distributed-moderation]]* serving norm-setting.

**Method.** [[causal-inference-observational|Selection-on-observables causal inference]] on **11M posts over 4 months**. Treatments: receiving **Reddit gold** or a **high score** (top-25th-percentile within a subreddit-month). **Stratified matching** + **difference-in-differences** on post-treatment outcomes.

**Findings.** Treated users post **~2% more frequently per day**, with **~57% higher score** and **~2% fewer removals per day** than matched controls. Effects persist for a period after treatment; heterogeneous across user and community types.

**Claims & evidence.** Strong observational design — matching + DiD on a very large sample. Causal interpretation rests on no-unobserved-confounders.

**Limitations.** Not randomized; gold/upvotes are anonymous (distributed feedback, not moderator-specific); single platform.

**Contributes to:** [[positive-reinforcement]], [[distributed-moderation]]. Pairs with [[language-of-approval]] (what language earns the feedback) and [[popular-feed-audit]] (how algorithmic curation allocates attention).
