---
type: paper
title: "Does Positive Reinforcement Work? A Quasi-Experimental Study of the Effects of Positive Feedback on Reddit"
slug: positive-reinforcement-reddit
venue: CHI
year: 2025
status: mapped
human_verified: true
llm_enriched: false
enrichment_source: human
territory: charted
themes: [healthy-online-behavior, computational-social-science, social-media-online-communities]
pdfs: ["raw/papers/chi2025-positive-reinforcement.pdf"]
updated: 2026-06-25
---

# Does Positive Reinforcement Work? A Quasi-Experimental Study of the Effects of Positive Feedback on Reddit

> Causal study of 11M Reddit posts: positive feedback makes users post more frequently and at higher quality.

> [!tip] Deep dive
> Verified by reviewer.

## Abstract / Notes

Social media platform design often incorporates explicit signals of positive feedback. Some moderators provide positive feedback with the goal of positive reinforcement, but are often unsure of their ability to actually influence user behavior. Despite its widespread use and theory touting positive feedback as crucial for user motivation, its effect on recipients is relatively unknown. This paper examines how positive feedback impacts Reddit users and evaluates its differential effects to understand who benefits most from receiving positive feedback. Through a causal inference study of 11M posts across 4 months, we find that users who received positive feedback made more frequent (2% per day) and higher quality (57% higher score; 2% fewer removals per day) posts compared to a set of matched control users. Our findings highlight the need for platforms, communities, and moderators to expand their perspective on moderation and complement punitive approaches with positive reinforcement strategies to foster desirable behavior online.

## Deep dive

**Authors:** Charlotte Lambert, Koustuv Saha, Eshwar Chandrasekharan (UIUC) · **CHI 2025** · [doi:10.1145/3706598.3713830](https://doi.org/10.1145/3706598.3713830)

**Research question.** Does receiving positive feedback causally change a Reddit user's later behavior, and who benefits most? Framed via Grimmelmann's moderation taxonomy — positive feedback as a form of *[[distributed-moderation]]* serving norm-setting.

**Method.** [[causal-inference-observational|Selection-on-observables causal inference]] on **11M posts over 4 months**. Treatments: receiving **Reddit gold** or a **high score** (top-25th-percentile within a subreddit-month). **Stratified matching** + **difference-in-differences** on post-treatment outcomes.

**Findings.** Treated users post **~2% more frequently per day**, with **~57% higher score** and **~2% fewer removals per day** than matched controls. Effects persist for a period after treatment; heterogeneous across user and community types.

**Claims & evidence.** Strong observational design — matching + DiD on a very large sample. Causal interpretation rests on no-unobserved-confounders.

**Limitations.** Not randomized; gold/upvotes are anonymous (distributed feedback, not moderator-specific); single platform.

**Contributes to:** [[positive-reinforcement]], [[distributed-moderation]]. Pairs with [[language-of-approval]] (what language earns the feedback) and [[popular-feed-audit]] (how algorithmic curation allocates attention).

## Source

- `raw/papers/chi2025-positive-reinforcement.pdf`
- Chart entry: `builder/entries/my-portfolio/positive-reinforcement-reddit.md`
