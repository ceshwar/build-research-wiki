---
type: paper
title: "The Language of Approval: Identifying the Drivers of Positive Feedback Online"
slug: language-of-approval
venue: CHI
year: 2026
status: mapped
themes: [computational-social-science, social-media-online-communities, digital-governance]
pdfs: ["raw/papers/chi2026-language-of-approval-2.pdf"]
updated: 2026-06-20
---

# The Language of Approval: Identifying the Drivers of Positive Feedback Online

> Quasi-experiment + prediction on 11M posts identifies linguistic drivers of upvotes/awards and a policy-practice gap.

## My notes

**Venue:** CHI · **Year:** 2026 · **Source:** 📄 charted + PDF

**Themes:** [[computational-social-science|Computational Social Science]], [[social-media-online-communities|Social Media & Online Communities]], [[digital-governance|Digital Governance]]

## Abstract / Notes

Positive feedback via likes and awards is central to online governance, yet which attributes of users' posts elicit rewards—and how these vary across authors and communities—remains unclear. To examine this, we combine quasi-experimental causal inference with predictive modeling on 11M posts from 100 subreddits. We identify linguistic patterns and stylistic attributes causally linked to rewards, controlling for author reputation, timing, and community context. For example, overtly complicated language, tentative style, and toxicity reduce rewards. We use our set of curated features to train models that can detect highly-upvoted posts with high AUC. Our audit of community guidelines highlights a "policy-practice gap"—most rules focus primarily on civility and formatting requirements, with little emphasis on the attributes identified to drive positive feedback. These results inform the design of community guidelines, support interfaces that teach users how to craft desirable contributions, and moderation workflows that emphasize positive reinforcement over purely punitive enforcement.

## Deep dive

**Authors:** Agam Goyal, Charlotte Lambert, Eshwar Chandrasekharan (UIUC) · **CHI 2026**

**Research question.** (RQ1) Which *linguistic attributes* causally drive positive feedback? (RQ2) Can those attributes predict high-quality posts in real time? (RQ3) Do community guidelines articulate them?

**Method.** **[[causal-inference-observational|Selection-on-observables causal inference]]** + **predictive modeling** on **11M posts from 100 subreddits**. LIWC psycholinguistic features; outcomes include top-quartile score, awards, gold. Plus an **audit of subreddit guidelines**.

**Findings.** **Broad help requests ≈ 43% higher odds** of high scores; **clear, readable writing ≈ +40% odds**. **Complicated language, tentative style, and toxicity reduce rewards.** Predictors achieve **high AUC**. Guideline audit reveals a **[[policy-practice-gap]]**: rules emphasize civility/formatting, not what actually earns approval.

**Claims & evidence.** Strong — causal identification + predictive validation on a large multi-community sample, grounded in a real artifact audit.

**Limitations.** Observational causal assumptions; reward signals are proxies for "approval."

**Contributes to:** [[positive-reinforcement]], [[policy-practice-gap]]. Direct successor to [[positive-reinforcement-reddit]]; informs governance design beyond punitive moderation.

## Source

- `raw/papers/chi2026-language-of-approval-2.pdf`
- Chart entry: `builder/entries/my-portfolio/language-of-approval.md`
