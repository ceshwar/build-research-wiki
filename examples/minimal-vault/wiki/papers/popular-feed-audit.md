---
type: paper
title: "Examining Algorithmic Curation on Social Media: An Empirical Audit of Reddit's r/popular Feed"
slug: popular-feed-audit
venue: ICWSM
year: 2026
status: mapped
human_verified: true
llm_enriched: false
enrichment_source: human
territory: charted
themes: [algorithmic-ai-audits, social-media-online-communities]
pdfs: ["raw/papers/2502.20491v3.pdf"]
updated: 2026-06-25
---

# Examining Algorithmic Curation on Social Media: An Empirical Audit of Reddit's r/popular Feed

> 11-month audit of r/popular: recent comments help posts climb; cliff below rank 80; toxicity doesn't extend feed life.

> [!tip] Deep dive
> Verified by reviewer.

## Abstract / Notes

Platforms are increasingly relying on algorithms to curate the content within users' social media feeds. However, the growing prominence of proprietary, algorithmically curated feeds has concealed what factors influence the presentation of content on social media feeds and how that presentation affects user behavior. This lack of transparency can be detrimental to users, from reducing users' agency over their content consumption to the propagation of misinformation and toxic content. To uncover details about how these feeds operate and influence user behavior, we conduct an empirical audit of Reddit's algorithmically curated trending feed called r/popular. Using 10K r/popular posts collected by taking snapshots of the feed over 11 months, we find that recent comments help a post remain on r/popular longer and climb the feed. We also find that posts below rank 80 correspond to a sharp decline in activity compared to posts above. When examining the effects of having a higher proportion of undesired behavior---i.e., moderator-removed and toxic comments---we find no significant evidence that it helps posts stay on r/popular for longer. Although posts closer to the top receive more undesired comments, we find this increase to coincide with a broader increase in overall engagement---rather than indicating a disproportionate effect on undesired activity. The relationships between algorithmic rank and engagement highlight the extent to which algorithms employed by social media platforms essentially determine which content is prioritized and which is not. We conclude by discussing how content creators, consumers, and moderators on social media platforms can benefit from empirical audits aimed at improving transparency in algorithmically curated feeds.

## Deep dive

**Authors:** Jackie Chan, Frederick Choi, Koustuv Saha, Eshwar Chandrasekharan (UIUC) · **ICWSM 2026** · [arXiv:2502.20491](https://arxiv.org/abs/2502.20491)

**Research question.** What factors govern whether a post stays on or climbs Reddit's r/popular feed, and does undesirable content (toxic / moderator-removed comments) help or hurt?

**Method.** Observational **empirical audit** of **10K r/popular posts** via **feed snapshots over 11 months**. Models longevity and ascent as a function of engagement signals and undesirable-content proportions.

**Findings.** **Recent comments help posts stay longer and climb.** A **sharp activity cliff below rank ~80**. **No significant evidence** that a higher proportion of toxic/removed comments helps posts persist; top posts attract more undesired comments only as part of broader engagement.

**Claims & evidence.** Solid observational audit at scale; the null result on toxicity is a useful corrective to "outrage wins" intuitions.

**Limitations.** Black-box audit; single feed; snapshot cadence bounds temporal resolution.

**Contributes to:** [[algorithmic-curation]], [[algorithmic-ai-audits]]. Complements [[positive-reinforcement-reddit]] and [[language-of-approval]] — together they map *what earns attention*, *whether reward changes behavior*, and *how algorithms allocate visibility*.

## Source

- `raw/papers/2502.20491v3.pdf`
- Chart entry: `builder/entries/my-portfolio/popular-feed-audit.md`
