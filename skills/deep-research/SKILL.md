---
name: deep-research
description: >-
  Autonomous research brief for traffic-oriented blog posts, including SEO and
  SERP-relevance analysis.
---

---
name: blog-deep-research
description: Conduct deep research for blog post creation by analyzing 5-8 authoritative sources, extracting key insights, and benchmarking SEO techniques from top-ranking competitors. Use this skill whenever you need to prepare comprehensive research materials for a blog post—whether the topic is data engineering, AI, fintech, healthcare, or any industry. The skill performs three core functions: (1) sourcing authoritative content through web search, (2) extracting and synthesizing the most important information into a coherent narrative, and (3) analyzing SEO patterns (structure, keyword density, readability, content length) from the top-ranking pages. Output is a standalone markdown research report that a human writer can use as a foundation for drafting the blog post. Perfect for content teams that want structured research input but maintain editorial control over the final piece.
compatibility: Requires web_search tool for sourcing; works best with markdown output parsing.
---

# Blog Deep Research Skill

## Overview

This skill automates the research phase of blog content creation for consultancies, agencies, and editorial teams. It produces structured markdown research reports that serve as the foundation for human-written blog posts, with comprehensive SEO benchmarking to ensure your content aligns with best practices.

**Key outputs:**
- Synthesized insights from 5-8 authoritative sources
- Identified research gaps and emerging patterns
- Competitive SEO analysis (structure, keyword patterns, readability metrics)
- Recommended content angles and key sections

---

## When to Use This Skill

Activate this skill when:
- You're starting a new blog post and need structured research input
- You want to understand what top-ranking pages are doing (SEO reverse-engineering)
- Your topic spans multiple industries or requires cross-domain knowledge
- You need to synthesize expert opinions and technical insights quickly
- Your editorial workflow is: research → human writer → publish

This skill does **not** generate final blog content—it provides the raw material and insights for your writers to craft engaging prose.

---

## Workflow Overview

The skill executes a three-phase process:

### Phase 1: Source Discovery & Collection
1. Parse the blog topic and intent
2. Generate targeted search queries (usually 3-5 queries to cast a wide net)
3. Fetch 5-8 authoritative sources via web search
4. Validate source quality and relevance

### Phase 2: Content Extraction & Synthesis
1. Extract key points, frameworks, and data from each source
2. Identify common themes and consensus areas
3. Flag unique insights or contrarian viewpoints
4. Organize findings into coherent sections

### Phase 3: SEO Benchmarking
1. Analyze structural patterns from top 3 competitor pages (heading hierarchy, section counts, etc.)
2. Extract keyword clusters and search intent signals
3. Assess readability metrics (approx. word count, key phrases per section)
4. Recommend optimal content length, section structure, and keyword placement

---

## Input Requirements

The skill expects a clear **blog topic or angle** that includes:
- **Primary topic**: The main subject (e.g., "Machine Learning Ops best practices", "Data quality frameworks")
- **Target audience** (optional): Who you're writing for (e.g., data engineers, C-suite, startups)
- **Angle/angle (optional)**: A specific perspective or debate (e.g., "Why X is overrated" or "The future of X in 2026")
- **Depth preference** (optional): Standard (5-8 sources) or more/less if specified

Example inputs:
```
Topic: "Real-time data pipelines in production"
Audience: Data engineers managing mission-critical systems
Angle: Cost optimization without sacrificing latency
```

---

## Output Format: Markdown Research Report

All research is delivered as a **standalone markdown document** with this structure:

```markdown
# Research Report: [Topic]

## Executive Summary
[1-2 paragraph overview of key findings]

## Research Scope
- Search queries used
- Sources analyzed (count + quality level)
- Date of research

## Key Findings
### Finding 1: [Theme/Insight]
- Supporting sources and evidence
- Relevant statistics or frameworks
- Consensus vs. contrarian views

### Finding 2: [Theme/Insight]
[... repeat for each major finding ...]

## Common Patterns & Best Practices
[Synthesized approaches from multiple sources]

## Research Gaps & Emerging Areas
[Where sources diverge or are silent]

## Competitive SEO Analysis

### Content Structure Patterns
- Typical article length: X words
- Average heading hierarchy: [H2 structure]
- Common section sequence: [e.g., Problem → Solution → Tools → Case Study]
- Table/code example usage: [observed patterns]

### Keyword & Search Intent Analysis
- Primary keywords: [extracted phrases]
- Long-tail variations: [semantic clusters]
- Search intent signals: [informational vs. transactional]

### Readability & Engagement Patterns
- Estimated reading time targets: X-Y minutes
- Use of bullet points/lists: [frequency]
- Use of visual elements: [images, tables, code]
- Call-to-action patterns: [common CTA placements]

### Recommended Content Approach
- Optimal article length: X words (based on competitors)
- Suggested section count: X-Y sections
- Key sections to include: [list]
- Opportunities for differentiation: [gaps in competitor content]

## Source Summary Table
| Source | Type | Key Insight | Credibility |
|--------|------|-------------|-------------|
| Source 1 | [Blog/Whitepaper/etc.] | Quick summary | [High/Medium] |
| Source 2 | ... | ... | ... |

## Next Steps for Writer
[Specific recommendations for the human writer, e.g., "Consider interviewing an expert on X" or "Test claim Y with recent data"]
```

---

## Execution Details

### Search Query Generation
The skill generates 3-5 targeted search queries based on the topic:
- Main topic query (broad)
- Best practices / how-to variant
- Industry-specific variant (if applicable)
- Recent news / trend variant
- Expert opinion / debate variant

Example for "AI governance":
1. "AI governance frameworks best practices 2026"
2. "How to implement AI governance in enterprises"
3. "AI governance healthcare regulations"
4. "AI governance latest developments 2026"
5. "AI governance challenges risks"

### Source Quality Validation
Prioritize:
- ✅ Industry blogs, whitepapers, research orgs
- ✅ Author credentials visible (expert bios)
- ✅ Recent publication (within 12 months, unless foundational)
- ✅ Data-backed claims with citations
- ⚠️ Medium-trust: Competitor blogs, medium publications (use sparingly)
- ❌ Low-trust: Reddit, non-expert forums, unattributed content

### Keyword Extraction
For each source, note:
- Primary keywords (appear 3+ times)
- Semantic variations (synonyms the author uses)
- Long-tail phrases (specificity indicators)
- Question-based keywords (from FAQs, headings)

### SEO Structure Analysis
Examine top 3 sources for:
- H1 (title) and H2 (section) patterns
- Average word count per section
- List/table frequency
- Code examples or visual elements
- Intro/body/conclusion word distribution
- Internal/external link density (note if observable)

---

## Key Principles

### 1. Synthesis Over Reproduction
- Extract concepts, don't copy passages
- Merge similar ideas from multiple sources
- Highlight where experts disagree

### 2. Signal Quality
- Prioritize data-backed insights
- Note the absence of evidence for unsupported claims
- Distinguish between consensus and fringe ideas

### 3. Actionable Structure
- Organize findings by theme, not by source
- Provide a clear "so what?" for each finding
- Flag opportunities for the writer to differentiate

### 4. Transparent Sourcing
- Always note which sources support each finding (without full citations)
- If a claim appears in only one source, note it's less consensual
- Include source types so writers know credibility level

---

## Phase Execution Walkthrough

### Phase 1: Discovery (Your Starting Point)
```
USER INPUT:
Topic: "Optimizing data warehouse costs"
Audience: Finance + Data Engineering leaders
Angle: Balancing performance and budget

AGENT ACTION:
→ Generate search queries:
  1. "Data warehouse cost optimization 2026"
  2. "Reduce Snowflake/BigQuery costs efficiently"
  3. "Data warehouse architecture cost efficiency"
  4. "Cloud data warehouse cost benchmarks"
  5. "Cost optimization tools data warehouses"

→ Execute web searches (5-8 results per query, deduplicate)
→ Fetch full content from top results
→ Validate source quality
```

### Phase 2: Extraction & Synthesis
```
AGENT ACTION:
→ For each source, extract:
  - Core concepts and frameworks
  - Specific recommendations
  - Data points and benchmarks
  - Case studies or examples
  
→ Group findings by theme:
  - Query optimization
  - Data archiving strategies
  - Tool selection
  - Organizational practices
  
→ Create synthesis: merge insights, note patterns
```

### Phase 3: SEO Analysis
```
AGENT ACTION:
→ Analyze top 3-4 sources for:
  - Structure: How many H2s? What's their sequence?
  - Length: Word count ranges
  - Keywords: What phrases repeat?
  - Examples: Tables, code, images?
  
→ Create recommendation summary:
  "Top articles average 2,500-3,500 words with 6-8 main sections.
   Keywords cluster around: cost, optimization, efficiency, tools.
   Most include at least one comparison table and a case study."
```

---

## Common Customizations

### For Different Industries
- **Data/AI**: Emphasize benchmarks, tools, and performance trade-offs
- **Healthcare/Fintech**: Emphasize compliance, risk, regulatory frameworks
- **SaaS/Product**: Emphasize user workflows, adoption, metrics
- **Leadership/Exec**: Emphasize business outcomes, ROI, strategic context

Adjust search queries and emphasis accordingly.

### For Different Depths
- **Quick research** (1-2 sources): Use for straightforward topics, foundational concepts
- **Standard** (5-8 sources): Default for most blog posts
- **Deep dive** (10+ sources): For trend analysis, competitive analysis, breaking news

Adjust source count and synthesis detail.

### For Different Angles
- **Educational**: Emphasize how-to, frameworks, step-by-step
- **Trend**: Emphasize recent developments, emerging consensus, predictions
- **Thought leadership**: Emphasize unique angles, contrarian views, expert opinions
- **News-driven**: Emphasize latest developments, immediate applications

Adjust keyword extraction and section recommendations.

---

## Quality Checklist

Before outputting the research report, verify:
- [ ] All sources are from the last 12 months (unless foundational)
- [ ] At least 60% of sources are from authoritative domains
- [ ] Each major finding is supported by at least 2 sources
- [ ] SEO analysis covers structure, keywords, and readability
- [ ] Synthesis avoids simple concatenation—ideas are merged, not listed
- [ ] The report is actionable for a human writer (not just raw notes)
- [ ] No claims lack supporting evidence
- [ ] Source summary table includes credibility levels

---

## Integration with Your Blog Pipeline

This research output is designed to integrate with:
- **Handoff to writers**: Share markdown file; writers use findings to draft prose
- **Editorial review**: Editor fact-checks against source list before publishing
- **CMS integration**: Writer converts markdown to blog platform after drafting
- **SEO implementation**: Writer applies structure/keyword recommendations during drafting

The skill stops before content generation—your writers maintain full creative control.

---

## Example Trigger Phrases

- "Research blog post on X"
- "Do deep research for a piece about Y"
- "What should we know about [topic] before writing a blog post?"
- "Analyze top pages on [topic] and give me research insights"
- "Prepare research materials for our next blog post on Z"

---

## Notes & Limitations

- **Research depth**: Analyzed within 5-8 sources per topic (configurable)
- **Freshness**: Results reflect current web content; topic recency depends on content velocity
- **Bias**: Source availability may skew toward English-language, Western perspectives
- **Verification**: Research provides synthesis, not validation—writers should fact-check critical claims
- **SEO analysis**: Based on observable page structure; relies on accessibility of source pages