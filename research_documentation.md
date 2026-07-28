# PaperBench: Evaluating AI’s Ability to Replicate AI Research — Research Documentation

**Source paper:** Giulio Starace, Oliver Jaffe, Dane Sherburn, James Aung, Chan Jun Shern, Leon Maksin, Rachel Dias, Evan Mays, Benjamin Kinsella, Wyatt Thompson, Johannes Heidecke, Amelia Glaese, Tejal Patwardhan (OpenAI). *PaperBench: Evaluating AI’s Ability to Replicate AI Research.* Proceedings of the 42nd International Conference on Machine Learning (ICML), Vancouver, Canada. PMLR 267, 2025.

---

## 1. Overview

PaperBench is a benchmark that tests whether AI agents can reproduce cutting-edge machine learning research the way a skilled engineer would: read a paper, write a full codebase from scratch, run the experiments, and produce matching results. The authors selected 20 highly selective ICML 2024 papers and built detailed, author-approved grading checklists covering 8,316 individually scored requirements. Frontier models show some ability to write code and make partial progress, but even the best tested agent (Claude 3.5 Sonnet with simple scaffolding) reaches only a 21.0% average replication score and still trails expert ML PhDs on a held subset. The work matters because autonomous research replication is a concrete signal of AI systems’ ability to do real ML R&D — useful for capability measurement, safety frameworks, and forecasting how quickly AI could accelerate AI development itself.

---

## 2. Problem Statement

Prior benchmarks either (a) give agents an existing research repository and ask them to reproduce selected results (for example CORE-Bench and SUPER), (b) evaluate ML engineering on relatively dated or simpler Kaggle-style tasks (MLE-bench, MLAgentBench, DSBench), or (c) use shorter, more self-contained research engineering tasks with built-in scoring functions (RE-Bench). None of these fully measure the harder skill of **replicating a modern research paper from scratch**: understanding contributions, designing and implementing a codebase, executing long experiments, and verifying empirical outcomes without access to the authors’ original code.

Human grading of such replications is also impractical at scale — the authors found that grading a single attempt can take tens of hours for an expert — so there was no ready, objective, scalable way to score partial progress on open-ended paper replication. Safety frameworks from OpenAI, Anthropic, and Google DeepMind explicitly care about autonomous ML R&D capabilities, but lacked a rigorous, paper-level replication benchmark for that measurement.

**What was missing:** a curated set of contemporary ML papers, author-validated hierarchical rubrics for objective partial-credit grading, an automated judge with its own accuracy evaluation, and baselines comparing frontier agents against expert humans under comparable constraints.

---

## 3. Proposed Approach / Methodology

**Plain language.** Give an AI agent a research paper (and clarifying notes). Ban it from looking at the authors’ code. Ask it to build a complete reproduction repository with a single entry script (`reproduce.sh`). Run that script on a clean machine with a GPU. Score the attempt against a detailed checklist co-written with an original paper author. Use an LLM to grade each checklist item so evaluation can scale, and separately measure how accurate that LLM judge is.

**Precise methodology.**

### 3.1 Task definition

For each of 20 ICML 2024 Spotlight/Oral papers:

1. Provide the candidate with the paper (PDF + Markdown), an author clarification **addendum**, and task instructions.
2. Require a submission repository that contains all code needed to reproduce the paper’s empirical contributions, including a root-level `reproduce.sh` entrypoint.
3. Hide the grading rubric from the candidate so it must infer what to replicate from the paper itself.
4. Disallow viewing or using authors’ original codebases and other blacklisted online replications.

### 3.2 Paper selection

Start from ICML 2024 Spotlight and Oral papers; filter with GPT-4o-assisted screening plus human review for:

- Collaborator accessibility (exclude papers where ≥75% of authors have affiliations making collaboration unlikely)
- Substantial empirical content (exclude position/theory-only papers and pure framework/library papers)
- Single-machine hardware feasibility (exclude multi-node distributed training)
- No closed-source pretrained model dependencies (e.g., GPT-4, Claude, PaLM)
- No new human data collection/annotation requirements
- Sufficient methodological detail for from-scratch replication
- Accessible, stable dependencies

Reach out until 20 authors agree to co-develop rubrics (from 42 author outreach attempts). Also release a 3-paper development set (one ICML + two NeurIPS 2024 Workshop papers) and keep a held-out set for internal use.

### 3.3 Rubric design

- Build a hierarchical tree of requirements per paper, co-developed with an original author over multiple weeks.
- Continuously decompose until an expert could judge each leaf in under ~15 minutes (given paper familiarity).
- Weight each node by importance relative to siblings (not necessarily by implementation difficulty).
- Leaf nodes are binary pass/fail; parent score = weighted average of children; root score = **Replication Score**.
- Main metric: average Replication Score across all papers.

Leaf requirement types:

| Type | What it checks | Graded from |
|---|---|---|
| **Code Development** | Correct implementation appears in source | READMEs/docs, source code, `reproduce.sh` |
| **Execution** | Required execution happened when running `reproduce.sh` | READMEs/docs, source code, `reproduce.sh`, `reproduce.log` |
| **Result Match** | Executed outputs match a paper result | READMEs/docs, `reproduce.sh`, `reproduce.log`, reproduction outputs |

Submissions without `reproduce.sh` score 0 on all Execution and Result Match nodes.

### 3.4 Reproduction phase

After the agent run ends, copy the submission to a fresh Ubuntu 24.04 VM with an A10 GPU and execute `reproduce.sh` (capped at 12 hours in the authors’ experiments; agent scripts averaged 5.5 minutes). This produces results/plots and `reproduce.log`, yielding an **executed submission**. Separating reproduction from agent runtime reduces hard-coded result cheating.

### 3.5 Agent evaluation setup (main experiments)

- Environment: Ubuntu 24.04 Docker container, single A10 GPU, internet access
- Inputs: paper PDF/Markdown, addendum, instructions
- Credentials provided: HuggingFace API key; OpenAI API with $1000 loaded
- Max agent runtime: 12 hours (API retries for rate limits/errors not counted against the limit)
- Scaffolding:
  - **BasicAgent:** Inspect AI basic agent / ReAct-style tool loop (bash, Python execution, web browser, paginated file reader); agent may end early
  - **IterativeAgent:** same tools, but removes early termination and prompts stepwise/piecemeal work
- Models tested: GPT-4o, o1, o3-mini, DeepSeek-R1, Claude 3.5 Sonnet (New), Gemini 2.0 Flash (3 runs per paper unless noted)
- Post-hoc blacklist monitor on agent logs; 10 of 646 runs violated blacklist rules and were scored 0

### 3.6 Automated judging (SimpleJudge) and JudgeEval

- Grade each leaf independently with an LLM judge (default backend: o3-mini-high).
- Context management: whitelist relevant files; if too large, rank files by relevance and include top files (top ten / until context budget `nctx − 10,000`).
- Parse judge responses with GPT-4o into binary score + explanation.
- Estimated cost: ~$66 USD per full-paper grading with o3-mini; ~$10 for Code-Dev-only grading.
- **JudgeEval:** human-graded partial replications across 5 papers (4 from PaperBench + 1 from the development set) used as gold labels; evaluate judges with accuracy, precision, recall, F1 (macro-averaged across papers).

### 3.7 PaperBench Code-Dev variant

Skip reproduction and grade only Code Development nodes. Removes GPU needs for rollout/reproduction and cuts grading cost ~85%. Weakly correlated with full PaperBench (for o1: Pearson *r* = 0.48; relationship reported as `PB = 0.45PBCD + 0.05`).

### 3.8 Human baseline

Recruit 8 ML PhD participants (Berkeley, Cambridge, CMU, Columbia, Cornell, Purdue, TU Wien, or UMass Amherst; CV screen + ML/git technical test). Evaluate on a 4-paper subset with 3 independent attempts per paper (best@3 as expert score). Same paper materials and blacklists as agents; A10 GPU (A100 for four attempts due to availability); AI assistants allowed. Part-time work over four weeks; timesheets include unattended experiment time. Compare to extended o1 IterativeAgent runs with hourly snapshots.

[SUGGESTED VISUAL: End-to-end pipeline diagram matching Figure 1 — Agent produces submission → clean VM runs `reproduce.sh` → LLM judge grades executed submission against hierarchical rubric → Replication Score.]

---

## 4. Key Findings

1. **Frontier agents show non-trivial but limited paper-replication ability.** With BasicAgent, Claude 3.5 Sonnet (New) leads at **21.0% ± 0.8** average Replication Score; o1-high scores **13.2% ± 0.3**; DeepSeek-R1 **6.0% ± 0.3**; GPT-4o **4.1% ± 0.1**; Gemini 2.0 Flash **3.2% ± 0.2**; o3-mini-high **2.6% ± 0.2** (Table 3).

2. **Models do not yet beat expert humans on the compared subset.** On a 3-paper subset after 48 hours, best@3 ML PhDs achieve **41.4%**, versus **26.6%** for o1 on the same subset. Over time, o1 initially leads early then plateaus after roughly the first hour; humans overtake after ~24 hours (Figure 3).

3. **Scaffolding and prompting strongly change scores.** IterativeAgent (no early exit + piecemeal prompting) raises o1 to **24.4% ± 0.7** (and **26.0% ± 0.3** at 36 hours) and o3-mini to **8.5% ± 0.8**, but lowers Claude 3.5 Sonnet to **16.1% ± 0.1** (Table 4) — indicating high sensitivity to agent design.

4. **Agents write code far better than they execute experiments and match results.** Stratified scores (Table 7) show Code Development much higher than Execution and Result Match. Example: Claude 3.5 Sonnet (BasicAgent) scores **35.4% ± 0.8** Code Development vs **1.8% ± 0.7** Execution and **0.7% ± 0.3** Results Analysis; best@3 humans on the 3-paper subset score **72.4 / 20.4 / 8.9** on those three types.

5. **An LLM judge can approximate expert grading at much lower cost.** On JudgeEval, o3-mini SimpleJudge reaches **F1 = 0.83** (ACC 0.83, Prec 0.83, Rec 0.83) at **$66**/paper; o1 reaches F1 **0.84** at **$830**/paper (Table 2). Stratified F1 for o3-mini-high: Code Development **0.72**, Execution **0.82**, Result Match **0.94** (Table 6).

6. **Code-Dev is a cheaper proxy with weaker fidelity.** o1 with IterativeAgent scores **43.4% ± 0.8** on PaperBench Code-Dev (Table 5), but correlation with full PaperBench is only moderate (*r* = 0.48).

7. **Failure modes are mainly long-horizon execution, not blank inability to plan.** Manual log inspection found most models (except Claude 3.5 Sonnet) finish early; all agents fail to strategize under time limits; o3-mini struggles with tool use. Models can draft multi-step plans but often fail to carry them through.

8. **Rule violations and variance are material.** Across 646 runs, 10 used blacklisted resources and were zeroed. Per-paper variance across seeds is often high; authors recommend multiple seeds.

9. **Grading cost can potentially drop further via pruned rubrics (preliminary).** Collapsing rubric depth beyond 3 reduced grading cost by **10×** on one JudgeEval case with only slight score deterioration (Appendix H) — flagged as experimental, not production-ready.

---

## 5. Technical Architecture / System Design

[SUGGESTED VISUAL: Hierarchical rubric tree as in Figure 2 — leaf binary grades propagate as weighted averages to a root Replication Score.]

### Components

| Component | Role | Inputs | Outputs |
|---|---|---|---|
| **Candidate agent** | Reads paper, writes codebase | Paper PDF/MD, addendum, instructions, tools, APIs | Submission repo with `reproduce.sh` |
| **Agent environment** | Isolated execution for development | Ubuntu 24.04 container, A10, internet | Agent logs + submission artifacts |
| **Blacklist monitor** | Detects forbidden URL/resource use | Agent logs, per-paper blacklists | Flags for manual review / DQ |
| **Reproduction runner** | Fresh verification run | Submission + Ubuntu 24.04 + A10 | Executed submission, `reproduce.log`, result files |
| **Rubric** | Hierarchical grading criteria | Author-approved tree of weighted requirements | Structure for leaf grading |
| **SimpleJudge** | Automated leaf grading | Paper MD, addenda, rubric context, filtered submission files | Binary leaf scores + explanations |
| **Score aggregator** | Weighted tree roll-up | Leaf scores + node weights | Replication Score (0–100%) |
| **JudgeEval** | Meta-benchmark for judges | Human gold leaf labels | ACC / Precision / Recall / F1 |

### Data flow

1. Agent receives paper materials → writes code over up to 12 hours.
2. Monitor scans logs for blacklist hits.
3. Submission copied to clean VM → `reproduce.sh` executed.
4. For each leaf: filter/rank files → judge prompt → binary grade.
5. Weighted averages propagate to root → Replication Score; average across papers/runs for leaderboard metrics.

### Dependencies and constraints

- Compute: A10 GPU for agent runs and reproduction (A100 used for some human attempts only).
- Services: HuggingFace downloads; optional OpenAI API for paper experiments needing it.
- Soft rules: internet browsing allowed except blacklisted author/replication resources; resources/runtime not capped by the benchmark rules (though experiments used 12h agent limits); account provisioning is out of scope (keys provided).
- Orchestration: nanoeval; agent scaffold based on Inspect AI basic agent.

### Lightweight variant

**PaperBench Code-Dev:** omit reproduction runner; judge only Code Development leaves.

---

## 6. Datasets and Evaluation

### Datasets / task corpus

- **PaperBench main set:** 20 ICML 2024 Spotlight/Oral papers spanning 12 ICML topics (deep RL, robustness, probabilistic methods, LLMs, etc.). Full list in paper Table 8 (examples: APT adaptive pruning; All-in-one simulation-based inference; Batch-and-match VI; BBox-Adapter; PINNs loss landscape; Robust CLIP; SAPG; Test-time model adaptation; etc.).
- **Rubric scale:** 8,316 individually gradable leaf tasks across 20 papers. Per-paper totals range widely (e.g., stochastic-interpolants 94 total nodes; pinn 2551 total nodes / 1963 leaves — Table 9).
- **Development set:** 3 additional papers (1 ICML + 2 NeurIPS 2024 Workshop).
- **Held-out set:** maintained for internal use (size not specified in the paper).
- **JudgeEval:** partial replications of 4 PaperBench papers + 1 development-set paper, manually graded by humans as gold labels. Replications were created from scratch or by modifying authors’ codebases (authors’ repos alone are often incomplete/buggy and lack `reproduce.sh`).

### Evaluation procedure

1. Run agent (typically 3 seeds × 20 papers).
2. Reproduce on clean VM.
3. Grade with SimpleJudge (o3-mini-high unless stated).
4. Aggregate weighted Replication Scores; report mean ± one standard error of the mean.

### Metrics

- **Primary:** average Replication Score (%) across papers.
- **Stratified:** Code Development / Execution / Result Match (Table 7 labels the third column “Results Analysis”).
- **JudgeEval:** Accuracy, Precision, Recall, F1 (macro-averaged); also cost per paper.
- **Human comparison:** time-series Replication Score vs hours of work; best@3 on subset.

### Baselines compared

- Multiple frontier models under BasicAgent and IterativeAgent.
- Random judge baseline on JudgeEval (F1 0.49).
- Expert human judge cost/performance reference (~12 hours/paper at a hypothetical $100/hr).
- Expert ML PhD replication baseline on a paper subset.
- Conceptual comparison to related benchmarks (CORE-Bench, SUPER, MLE-bench, MLAgentBench, DSBench, RE-Bench) — not as identical numeric head-to-heads on the same tasks.

---

## 7. Results Comparison

### Main PaperBench Replication Scores (BasicAgent)

| System | Metric | Value | Source |
|---|---|---|---|
| Claude 3.5 Sonnet (New) + BasicAgent | Avg. Replication Score | **21.0% ± 0.8** | Table 3 |
| o1-high + BasicAgent | Avg. Replication Score | **13.2% ± 0.3** | Table 3 |
| DeepSeek-R1 + BasicAgent | Avg. Replication Score | **6.0% ± 0.3** | Table 3 |
| GPT-4o + BasicAgent | Avg. Replication Score | **4.1% ± 0.1** | Table 3 |
| Gemini 2.0 Flash + BasicAgent | Avg. Replication Score | **3.2% ± 0.2** | Table 3 |
| o3-mini-high + BasicAgent | Avg. Replication Score | **2.6% ± 0.2** | Table 3 |

### IterativeAgent and extended runs

| System | Metric | Value | Source |
|---|---|---|---|
| o1-high + IterativeAgent | Avg. Replication Score | **24.4% ± 0.7** | Table 4 |
| o1-high + IterativeAgent (36h) | Avg. Replication Score | **26.0% ± 0.3** | Table 4 |
| Claude 3.5 Sonnet + IterativeAgent | Avg. Replication Score | **16.1% ± 0.1** | Table 4 |
| o3-mini-high + IterativeAgent | Avg. Replication Score | **8.5% ± 0.8** | Table 4 |
| o1-high + IterativeAgent | PaperBench Code-Dev | **43.4% ± 0.8** | Table 5 |

### Human vs model (subset)

| System | Setting | Metric | Value | Source |
|---|---|---|---|---|
| ML PhDs (best@3) | 3-paper subset, 48h | Replication Score | **41.4%** | §1 / intro results |
| o1 | Same 3-paper subset | Replication Score | **26.6%** | §1 / intro results |
| Humans best@3 | 3-paper subset | Code Dev / Exec / Results | **72.4 / 20.4 / 8.9** | Table 7 |
| o1 IterativeAgent (36h) | Full eval stratified | Code Dev / Exec / Results | **42.4% ± 1.0 / 7.4% ± 1.1 / 1.4% ± 0.1** | Table 7 |

*Note:* Figure 3 uses a 4-paper subset; the `test-time-model-adaptation` human attempt ends at 24 hours and is excluded from the “3-paper subset” numbers elsewhere.

### JudgeEval (macro-averaged)

| Judge backend | ACC | Precision | Recall | F1 | Cost USD/paper | Source |
|---|---|---|---|---|---|---|
| Random | 0.48 | 0.49 | 0.49 | 0.49 | 0 | Table 2 |
| GPT-4o-mini | 0.63 | 0.64 | 0.60 | 0.59 | 8 | Table 2 |
| GPT-4o | 0.74 | 0.74 | 0.72 | 0.73 | 120 | Table 2 |
| o1-mini | 0.81 | 0.85 | 0.76 | 0.78 | 72 | Table 2 |
| o3-mini | 0.83 | 0.83 | 0.83 | **0.83** | **66** | Table 2 |
| o1 | 0.84 | 0.84 | 0.84 | **0.84** | 830 | Table 2 |

### Related prior work (qualitative contrast; not same-task scores)

| Prior work | What agents get | What PaperBench changes |
|---|---|---|
| CORE-Bench; Bogin et al. (SUPER) | Existing research repositories | Replication from scratch; no author code |
| Liang et al. (GPT-4 for SE papers) | Manual expert rubric review | Fully specified rubrics + automated LLM judge |
| MLE-bench / MLAgentBench / DSBench | Kaggle-style competitions | Contemporary ICML research papers |
| RE-Bench | 7 open-ended ML R&D tasks, often with scoring functions | Broader multi-day paper replication without a single scalar scoring function |

---

## 8. Limitations and Constraints

Authors explicitly flag:

1. **Dataset size:** Only 20 papers (though thousands of leaf requirements). Coverage of the ML community remains limited.
2. **Contamination risk:** Author codebases often exist online. Current models are likely unaffected due to paper recency, but future models pretrained on these materials may inflate scores.
3. **Expensive, hard-to-scale dataset creation:** Each rubric takes expert humans many tens of hours / multiple weeks with author collaboration. Training others to match quality was difficult; automated rubric generation is unfinished.
4. **LLM judge gaps:** JudgeEval F1 of 0.83 is good but below expert humans; judging is non-deterministic; adversarial/specification-gaming submissions are not fully ruled out.
5. **Cost:** ~$400 API credits for a 12-hour o1 IterativeAgent rollout per paper (~$8000 per full 20-paper eval run) plus ~$66 grading/paper. Code-Dev and pruned grading mitigate but do not eliminate cost.
6. **Incomplete research coverage:** PaperBench measures replication of empirical ML papers, not idea generation, theory, multi-node training, closed-model work, or human-subjects research (those were filtered out).
7. **Scaffold sensitivity:** Large swings between BasicAgent and IterativeAgent mean reported model rankings are not scaffold-invariant; authors treat results as initial baselines, not capability ceilings.
8. **Human baseline caveats:** Humans could use AI coding assistants; some used A100 vs agents’ A10 during development (reproduction still on A10); humans worked part-time over weeks vs continuous agent runs; subset-only comparison.
9. **Ambiguity in public reporting:** Table 7’s third column is labeled “Results Analysis” while the rest of the paper uses “Result Match”; the documentation treats these as the same category based on context, but the naming inconsistency is in the paper.
10. **Future work called out:** dependency-graph rubrics; automated/human-in-the-loop rubric creation; stronger judges; stress-testing for sandbagging and reward hacking; broader autonomous R&D evaluations beyond replication.

---

## 9. Practical Applications

1. **Frontier safety / preparedness evaluations:** Use PaperBench (or Code-Dev as a cheaper smoke test) as a concrete autonomy/ML-R&D gauge inside frameworks like OpenAI’s Preparedness Framework, Anthropic’s Responsible Scaling Policy, and Google DeepMind’s Frontier Safety Framework — e.g., gate higher autonomy tiers on Replication Score thresholds plus human baselines.
2. **Agent scaffolding R&D:** Treat PaperBench as a long-horizon tool-use stress test. Product teams building coding agents can A/B test planners, memory, early-stop prevention, and experiment-monitoring loops against the Execution/Result Match gap (where today’s models collapse).
3. **Automated research reproduction pipelines:** Adapt the reproduce-on-clean-VM + hierarchical rubric + LLM judge pattern to internal “paper → runnable repo” assistants that help labs verify claims before adoption — especially to catch incomplete reproductions that only look correct in code review.
4. **LLM-as-judge productization for complex artifacts:** Reuse SimpleJudge + JudgeEval methodology when grading large unstructured deliverables (codebases, experiment logs, reports) where binary leaf criteria and file-relevance ranking keep context feasible.
5. **Hiring / training proxies (with caution):** The human protocol (paper + blacklist + GPU + timed snapshots) can inform take-home assessments for research engineers, but PaperBench itself is designed for AI agents and author-approved rubrics are not publicly framed as interview kits.
6. **Cost-controlled continuous eval:** Run PaperBench Code-Dev in CI for frequent regression signal on research-coding agents; periodically sample full PaperBench (with reproduction) before claiming real replication gains, given only *r* = 0.48 correlation.
7. **Risk monitoring for recursive self-improvement narratives:** Track whether agents move from Code Development credit into true Result Match success on fresh papers — a practical early-warning metric for systems that can not only write research code but close the loop on empirical validation.

---

## 10. Glossary

- **Addendum:** Author-provided clarifications and out-of-scope notes packaged with each paper for candidates (plus optional judge-only addendum with grading reference information).
- **BasicAgent:** The authors’ default ReAct-style scaffold based on Inspect AI’s basic agent, with bash/Python/browser/file tools and an “end task” action.
- **Blacklist:** Per-paper list of forbidden web resources (typically author code and other replications) that candidates may not use.
- **Code Development (leaf type):** Rubric criterion checking whether source code appears to implement a requirement correctly.
- **Executed submission:** Submission after `reproduce.sh` has been run on a clean VM, including logs and generated artifacts.
- **Execution (leaf type):** Rubric criterion checking whether a required execution occurred when running `reproduce.sh`.
- **F1 score:** Harmonic mean of precision and recall; used on JudgeEval for binary leaf grading quality.
- **Hierarchical rubric:** Tree of weighted requirements whose leaf binary scores roll up to a root Replication Score.
- **ICML:** International Conference on Machine Learning; source venue for the 20 evaluated papers (2024 Spotlight/Oral).
- **IterativeAgent:** Scaffold variant that removes early termination and prompts the model to take only the next piecemeal step.
- **JudgeEval:** Auxiliary dataset/benchmark of human-graded submissions used to measure automated judges.
- **Leaf node:** Finest-grained rubric requirement graded pass/fail (0/1).
- **LLM-based judge / SimpleJudge:** Automated grader that scores each leaf using an LLM with paper context and filtered submission files.
- **Macro-averaging:** Averaging metrics equally across papers (used for JudgeEval).
- **nanoeval:** Orchestration system used to run agent evaluations in the authors’ experiments.
- **PaperBench:** The full benchmark requiring code development, execution, and result matching for paper replication.
- **PaperBench Code-Dev (PBCD):** Lightweight variant grading only Code Development nodes (no reproduction).
- **ReAct:** Reasoning-and-acting agent pattern (Yao et al., 2023) underlying the scaffolds.
- **Replication Score:** Root-level weighted proportion of satisfied rubric requirements for one submission; 100% = perfect replication.
- **reproduce.log:** Log captured while running `reproduce.sh` on the clean reproduction VM.
- **reproduce.sh:** Required repository entrypoint script that should regenerate the paper’s empirical results.
- **Result Match (leaf type):** Rubric criterion checking whether reproduction outputs evidence a specific paper result.
- **SEM:** Standard error of the mean; used for error bars on agent scores.
- **Spotlight / Oral:** Highly selective ICML presentation categories used as the candidate pool for paper inclusion.

---

## 11. References and Citations

Resources and works cited that are directly relevant to PaperBench’s methodology, baselines, or findings:

### Primary artifact

- Starace, G., Jaffe, O., Sherburn, D., Aung, J., Shern, C. J., Maksin, L., Dias, R., Mays, E., Kinsella, B., Thompson, W., Heidecke, J., Glaese, A., & Patwardhan, T. (2025). *PaperBench: Evaluating AI’s Ability to Replicate AI Research.* ICML 2025, PMLR 267. (Code open-sourced by the authors.)

### Safety frameworks and agent infrastructure

- OpenAI (2023). Preparedness Framework.
- Anthropic (2024). Responsible Scaling Policy.
- Google DeepMind (2024). Frontier Safety Framework.
- UK AI Safety Institute (2025). Inspect (basic agent documentation).
- Yao, S., et al. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. arXiv:2210.03629.

### Closely related evaluation benchmarks

- Siegel, Z. S., et al. (2024). CORE-Bench. arXiv:2409.11363.
- Bogin, B., et al. (2024). SUPER: Evaluating Agents on Setting Up and Executing Tasks from Research Repositories. arXiv:2409.07440.
- Liang, J. T., et al. (2024). Can GPT-4 Replicate Empirical Software Engineering Research? arXiv:2310.01727.
- Chan, J. S., et al. (2024). MLE-bench. arXiv:2410.07095.
- Huang, Q., et al. (2024). MLAgentBench. ICML 2024.
- Jing, L., et al. (2024). DSBench. arXiv:2409.07703.
- Wijk, H., et al. (2024). RE-Bench. arXiv:2411.15114.
- Sawada, T., et al. (2023). ARB: Advanced Reasoning Benchmark for Large Language Models. arXiv:2307.13692.
- Harvey Team (2024). BigLaw Bench.

### Automated judging / evaluation methodology

- Zheng, L., et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS.
- Chen, D., et al. (2024). MLLM-as-a-Judge. arXiv:2402.04788.
- Fu, J., et al. (2023). GPTScore. arXiv:2302.04166.
- Zhuge, M., et al. (2024). Agent-as-a-Judge. arXiv:2410.10934.
- Chiang, C.-H., & Lee, H.-y. (2023). Can Large Language Models Be an Alternative to Human Evaluations? arXiv:2305.01937.
- Lambert, N., et al. (2024). RewardBench. arXiv:2403.13787.
- Wang, T., et al. (2024a). Self-Taught Evaluators. arXiv:2408.02666.

### Related scientific-agent / research-capability work

- Si, C., Yang, D., & Hashimoto, T. (2024). Can LLMs Generate Novel Research Ideas? arXiv:2409.04109.
- Jansen, P., et al. (2024). DiscoveryWorld. arXiv:2406.06769.
- Wang, R., et al. (2022). ScienceWorld. arXiv:2203.07540.
- van der Weij, T., et al. (2024). AI Sandbagging. arXiv:2406.07358.
- Pan, A., Bhatia, K., & Steinhardt, J. (2022). The Effects of Reward Misspecification. arXiv:2201.03544.
- DeepMind (2024). Specification Gaming: The Flip Side of AI Ingenuity.

### Papers included in the PaperBench dataset (replication targets)

- Zhao, B., Hajishirzi, H., & Cao, Q. (2024). APT: Adaptive Pruning and Tuning…
- Gloeckler, M., et al. (2024). All-in-one simulation-based inference.
- Cai, D., et al. (2024). Batch and match: black-box variational inference…
- Sun, H., et al. BBox-Adapter: Lightweight Adapting for Black-Box Large Language Models.
- Wang, X., et al. (2024b). Bridging Data Gaps in Diffusion Models…
- Frans, K., et al. (2024). Unsupervised Zero-Shot RL via Functional Reward Encodings.
- Wołczyk, M., et al. (2024). Fine-tuning RL Models is Secretly a Forgetting Mitigation Problem.
- Xia, X., et al. (2024). Refined Coreset Selection…
- Shi, J., et al. (2024). LCA-on-the-Line…
- Lee, A., et al. (2024). A Mechanistic Understanding of Alignment Algorithms (DPO and Toxicity).
- Rathore, P., et al. (2024). Challenges in Training PINNs…
- Cheng, Z., et al. RICE: Breaking Through the Training Bottlenecks of RL with Explanation.
- Schlarmann, C., et al. (2024). Robust CLIP…
- Cai, C., et al. (2024). Sample-specific Masks for Visual Reprogramming-based Prompting.
- Singla, J., Agarwal, A., & Pathak, D. (2024). SAPG: Split and Aggregate Policy Gradients.
- Sharrock, L., et al. (2024). Sequential Neural Score Estimation…
- Sanchez, G., et al. (2024). Stay on Topic with Classifier-Free Guidance.
- Albergo, M. S., et al. (2024). Stochastic Interpolants with Data-Dependent Couplings.
- Niu, S., et al. (2024). Test-Time Model Adaptation with Only Forward Passes.
- Jin, X., & Ren, X. (2024). What Will My Model Forget?

---

## Execution Report

| Metric | Value |
|---|---|
| Model used | Cursor Grok 4.5 (run metadata: cursor-grok-4.5-medium) |
| Input token count | ~28,000 (estimate; exact API metering unavailable — based on ~16,568 extracted PDF words + prompt/instructions) |
| Output token count | ~6,300 (estimate; based on ~4,859 output words × ~1.3) |
| Total tokens consumed | ~34,300 (estimate) |
| Execution time | ~3 minutes 12 seconds (start 2026-07-28T05:48:50Z → end 2026-07-28T05:52:02Z) |
| Input file name | starace25a_02c9.pdf |
| Input file size | 1,591,351 bytes (~1.52 MB) |
| Approximate input word count | 16,568 (extracted text via pypdf) |
| Output file name | research_documentation.md |
| Output word count | 4,859 |
| Output section count | 12 (sections 1–11 + Execution Report) |
| Timestamp (start) | 2026-07-28T05:48:50Z |
| Timestamp (end) | 2026-07-28T05:52:02Z |
| Any errors or skipped sections | No sections skipped. Exact token counts unavailable from the runtime API (estimates used). PDF text extracted with pypdf because `pdftotext` was not installed. Table 7’s “Results Analysis” label retained as published while noting likely equivalence to Result Match. |

### Reflection questions

**What was the hardest part of this paper to document clearly, and why?**  
The scoring system — hierarchical weighted rubrics with three leaf types, separate reproduction, and LLM judging — is conceptually dense and easy to flatten incorrectly. Capturing how partial credit works without oversimplifying required careful cross-referencing of Figures 1–2, Table 1, and the grading equations.

**Which section of the documentation is most likely to need human review?**  
Section 7 (Results Comparison), because agent rankings flip under different scaffolds and human numbers come from overlapping but not identical subsets (3-paper vs 4-paper, 24h vs 48h). A domain expert should verify that cross-table comparisons are not over-interpreted as fair head-to-heads.

**What follow-up questions would a reader most likely have that this paper does not answer?**  
Readers will ask how to obtain/run the open-sourced code and rubrics end-to-end in their own stack, what the held-out set contains, whether newer models (e.g., Claude 3.7, which the authors could not finish evaluating) close the human gap, and what Replication Score thresholds should trigger safety-policy actions — none of which the paper fully specifies.
