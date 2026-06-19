---
type: synthesis
title: "Reward, Language, and Attention on Reddit"
updated: 2026-06-19
tags: [demo, positive-reinforcement, reddit, causal-inference]
---

# Reward, Language, and Attention on Reddit

> **Thesis:** These three papers map a stack — *algorithms allocate attention* → *communities signal approval* → *that approval changes behavior* — with shared implications for governance beyond punitive moderation. [[positive-reinforcement-reddit]] · [[language-of-approval]] · [[popular-feed-audit]]

## The stack

1. **Attention (who gets seen).** [[popular-feed-audit]] audits Reddit's r/popular: recent comments help posts climb; rank ~80 is a cliff; toxicity does **not** extend feed life — correcting "outrage wins" intuitions about [[algorithmic-curation]].
2. **Approval (what gets rewarded).** [[language-of-approval]] identifies linguistic drivers of upvotes/awards on 11M posts — clear writing and broad help requests help; toxicity and tentativeness hurt — and finds a **[[policy-practice-gap]]** in written guidelines.
3. **Behavior (what changes).** [[positive-reinforcement-reddit]] shows positive feedback *causally* increases posting frequency (~2%/day) and quality (~57% higher scores) vs. matched controls — evidence that reward is a governance lever, not just a nicety.

## Method spine

Two CHI papers share **[[causal-inference-observational]]** (stratified matching + difference-in-differences). The ICWSM audit is observational but at a different layer (feed snapshots, not user-level treatment). Together they support *mechanism-aware* platform design rather than vibes-based moderation.

## Design implications

- Platforms should treat **positive reinforcement** as first-class ([[positive-reinforcement-reddit]], [[language-of-approval]]).
- **Guidelines and tools** should teach what actually earns approval, not only what to avoid ([[policy-practice-gap]]).
- **Algorithm audits** remain necessary when ranking is proprietary ([[popular-feed-audit]]).

## Sources

- [[positive-reinforcement-reddit]]
- [[language-of-approval]]
- [[popular-feed-audit]]
