#!/usr/bin/env python3
"""Shallow reef DATA — demo portfolio (7 papers: 3 deep dive, 4 quick dip).
Run from repo root: python3 builder/build.py --vault examples/minimal-vault"""

VAULT = {
    "name": "Shallow reef",
    "owner": "Eshwar Chandrasekharan",
    "domain": "HCI · online communities · computational social science",
}

THEMES = {
    "computational-social-science": (
        "Computational Social Science",
        "How digital environments shape user behavior and social phenomena.",
        True,
    ),
    "social-media-online-communities": (
        "Social Media & Online Communities",
        "Understanding social behaviors and large-scale phenomena in online communities.",
        True,
    ),
    "digital-governance": (
        "Digital Governance",
        "Understanding what governance interventions actually work in online spaces.",
        True,
    ),
    "healthy-online-behavior": (
        "Healthy Online Behavior",
        "Proactively cultivating desirable behavior through positive reinforcement.",
        True,
    ),
    "algorithmic-ai-audits": (
        "Algorithmic and AI Audits",
        "Auditing how algorithms and AI systems shape attention, information exposure, and user wellbeing.",
        True,
    ),
}

P = [
    dict(
        slug="positive-reinforcement-reddit",
        entry="builder/entries/my-portfolio/positive-reinforcement-reddit.md",
        note="builder/entries/my-portfolio/positive-reinforcement-reddit.md",
        title="Does Positive Reinforcement Work? A Quasi-Experimental Study of the Effects of Positive Feedback on Reddit",
        venue="CHI",
        year=2025,
        status="mapped",
        pdfs=["chi2025-positive-reinforcement.pdf"],
        themes=["healthy-online-behavior", "computational-social-science", "social-media-online-communities"],
        one="Causal study of 11M Reddit posts: positive feedback makes users post more frequently and at higher quality.",
    ),
    dict(
        slug="popular-feed-audit",
        entry="builder/entries/my-portfolio/popular-feed-audit.md",
        note="builder/entries/my-portfolio/popular-feed-audit.md",
        title="Examining Algorithmic Curation on Social Media: An Empirical Audit of Reddit's r/popular Feed",
        venue="ICWSM",
        year=2026,
        status="mapped",
        pdfs=["2502.20491v3.pdf"],
        themes=["algorithmic-ai-audits", "social-media-online-communities"],
        one="11-month audit of r/popular: recent comments help posts climb; cliff below rank 80; toxicity doesn't extend feed life.",
    ),
    dict(
        slug="language-of-approval",
        entry="builder/entries/my-portfolio/language-of-approval.md",
        note="builder/entries/my-portfolio/language-of-approval.md",
        title="The Language of Approval: Identifying the Drivers of Positive Feedback Online",
        venue="CHI",
        year=2026,
        status="mapped",
        pdfs=["chi2026-language-of-approval-2.pdf"],
        themes=["computational-social-science", "social-media-online-communities", "digital-governance"],
        one="Quasi-experiment + prediction on 11M posts identifies linguistic drivers of upvotes/awards and a policy-practice gap.",
    ),
]

TITLES = {
    "positive-reinforcement-reddit": "Does Positive Reinforcement Work?",
    "popular-feed-audit": "r/popular Feed Audit",
    "language-of-approval": "The Language of Approval",
}

CONCEPTS = {
    "positive-reinforcement": (
        "Positive Reinforcement",
        "Rewarding desirable behavior (vs. punishing bad behavior) to shape what users do online.",
        ["positive-reinforcement-reddit", "language-of-approval"],
    ),
    "policy-practice-gap": (
        "Policy–Practice Gap",
        "Mismatch between what community guidelines emphasize and the attributes that actually drive approval.",
        ["language-of-approval"],
    ),
    "causal-inference-observational": (
        "Observational Causal Inference",
        "Matching + difference-in-differences on large observational social-media data.",
        ["positive-reinforcement-reddit", "language-of-approval"],
    ),
    "algorithmic-curation": (
        "Algorithmic Curation",
        "Platforms selecting and ranking content for feeds — often proprietary and opaque.",
        ["popular-feed-audit"],
    ),
    "distributed-moderation": (
        "Distributed Moderation",
        "Community members (not just staff moderators) shaping norms via votes, awards, and feedback.",
        ["positive-reinforcement-reddit"],
    ),
}

PEOPLE = {
    "eshwar-chandrasekharan": (
        "Eshwar Chandrasekharan",
        "Faculty (UIUC)",
        "Research on online communities, moderation, and computational social science.",
        ["positive-reinforcement-reddit", "popular-feed-audit", "language-of-approval"],
    ),
    "charlotte-lambert": (
        "Charlotte Lambert",
        "Student / co-author (UIUC)",
        "Lead/co-author on positive-reinforcement and language-of-approval papers.",
        ["positive-reinforcement-reddit", "language-of-approval"],
    ),
    "koustuv-saha": (
        "Koustuv Saha",
        "Co-author (UIUC)",
        "Causal inference and platform studies on Reddit.",
        ["positive-reinforcement-reddit", "popular-feed-audit"],
    ),
    "agam-goyal": (
        "Agam Goyal",
        "Co-author (UIUC)",
        "Computational linguistics and causal inference on Reddit rewards.",
        ["language-of-approval"],
    ),
}

PLATFORMS = {
    "reddit": (
        "Reddit",
        "Platform",
        "Large federated forum platform; primary empirical site for all three demo papers.",
        ["positive-reinforcement-reddit", "popular-feed-audit", "language-of-approval"],
    ),
}

METHODS = {}
