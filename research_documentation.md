# Research Documentation: PaperBench (Evaluating AI’s Ability to Replicate AI Research)

## 1. Overview
PaperBench is a benchmark designed to evaluate whether autonomous artificial intelligence agents can independently replicate cutting-edge machine learning research from scratch. To measure this capability, the researchers selected 20 spotlight and oral research papers from the 2024 International Conference on Machine Learning (ICML) and collaborated with the original authors to break down each paper's empirical contributions into detailed, step-by-step grading rubrics containing 8,316 total evaluation items. Frontier AI models—including OpenAI o1, OpenAI o3-mini, Claude 3.5 Sonnet, DeepSeek-R1, GPT-4o, and Gemini 2.0 Flash—were placed inside virtual programming environments with GPU access and tasked with writing all required code, executing experiments, and reproducing published experimental results within 12-hour time limits. The evaluation revealed that while top models can write functional isolated code components, current frontier AI agents fail to execute complex research pipelines or reproduce valid scientific results over multi-hour horizons, with the top-performing agent (Claude 3.5 Sonnet) reaching an average replication score of only 21.0% compared to human machine learning experts who reach 72.4% on code development and far higher overall execution rates over extended periods.

## 2. Problem Statement
Evaluating artificial intelligence models on software engineering and machine learning tasks has historically relied on simplistic coding benchmarks, dated competitive programming challenges, or narrow code-editing tasks where full repositories and explicit scoring functions are provided to the model. Existing evaluations like CORE-Bench provide pre-existing codebases and task agents with reproducing specific results, while benchmarks like MLE-bench and MLAgentBench test models on Kaggle competitions, which do not reflect the open-ended, complex nature of contemporary artificial intelligence research. Before this work existed, the machine learning community lacked a standardized, objective, and scalable methodology to answer a critical safety and capability question: Can an autonomous AI agent read a published scientific paper, design and implement an entire software architecture from scratch, debug runtime environment failures on hardware GPUs, and replicate published empirical findings without human intervention?

Evaluating complete paper replications manually presents an extreme bottleneck because reviewing a single replication attempt requires tens of hours of work by expert human researchers. Without an automated, fine-grained grading infrastructure, benchmarking long-horizon research capabilities across multiple models, prompt scaffolds, and random seeds was practically impossible. Additionally, research papers routinely omit minor implementation details, setup configurations, or dataset preprocessing steps, introducing underspecification that makes automated evaluation prone to false negatives unless expert author clarifications and explicit rubrics are incorporated into the benchmark design.

## 3. Proposed Approach / Methodology
The researchers developed a comprehensive benchmarking pipeline that combines human-author collaboration, hierarchical task decomposition, automated execution sandboxes, and automated large language model judging. 

[SUGGESTED VISUAL: End-to-End Evaluation Pipeline Diagram showing the paper PDF/Markdown input, Agent Scaffolding executing in an Ubuntu 24.04 Docker container with 1x NVIDIA A10 GPU, output code/logs/csv generation, and the SimpleJudge evaluating outputs against hierarchical JSON rubrics.]

### Phase 1: Paper Selection and Curation
The authors applied a systematic filtering pipeline to all Spotlight and Oral papers accepted at ICML 2024. To ensure realism and feasibility, papers were filtered using automated language model prompts followed by human verification against eight strict criteria:
1. **Commercial and Geographic Filter**: Excluded papers where 75% or more of the authors had affiliations making collaboration restricted due to commercial lab constraints or regional boundaries.
2. **Empirical Content Filter**: Required at least one non-trivial empirical experiment involving substantial software engineering, excluding pure theory or position papers.
3. **Hardware Requirements Filter**: Excluded papers requiring multi-node distributed compute, ensuring all experiments fit on a single machine with one GPU.
4. **Model Dependency Filter**: Excluded dependencies on closed-source pretrained models (e.g., GPT-4, Claude, PaLM).
5. **Data Requirements Filter**: Excluded requirements for new human data collection or human annotators.
6. **Reproducibility Filter**: Required sufficient paper detail to enable replication from scratch.
7. **Framework Papers Filter**: Excluded papers whose main contribution was introducing a software framework or library rather than research results.
8. **Accessible Dependencies Filter**: Required all external libraries and APIs to be freely or easily accessible and stable.

Out of 42 author teams contacted who passed screening, 20 agreed to collaborate, forming the final 20-paper benchmark dataset across 12 ICML topic domains.

### Phase 2: Hierarchical Rubric and Addendum Creation
For each paper, the researchers co-developed a hierarchical tree-structured rubric in JSON format with one of the paper's original authors. This process required many tens of hours per paper.

[SUGGESTED VISUAL: Tree diagram of a PaperBench Rubric displaying Root Node ("Core contributions reproduced"), decomposed into Child Nodes (e.g., "Methodology Implemented", "Experiment 1 Run"), further branching into Leaf Nodes categorized into Code Development, Execution, and Result Match nodes.]

Rubrics decompose high-level replication goals into fine-grained child requirements. Crucially, satisfying all child requirements of a parent node implies that the parent node is fulfilled. Decomposition continues down to granular leaf nodes, defined such that an expert human can assess whether a submission satisfies the requirement in under 15 minutes. In total, the 20 rubrics comprise 8,316 individually gradable leaf nodes across three functional types:
- **Code Development Leaf Nodes**: Evaluate whether the submitted source code contains a correct programmatic implementation of a requirement (e.g., fine-tuning hyperparameters, network architecture, loss functions).
- **Execution Leaf Nodes**: Evaluate whether executing the submission's `reproduce.sh` bash script completes successfully and executes the required experiment (e.g., generating output log files without crashing).
- **Result Match Leaf Nodes**: Evaluate whether the empirical outputs generated by the execution match the numerical tables, figures, or metrics published in the paper (e.g., classification accuracy within specified confidence bounds).

Every rubric node carries an explicit weight assigned by the original authors reflecting its scientific importance relative to its siblings. To address paper underspecification, authors co-wrote a public addendum providing explicit implementation clarifications and defining out-of-scope sections, as well as a judge-only addendum containing reference baseline values for evaluation.

### Phase 3: Agent Scaffolding and Sandboxed Environment
AI agents execute within isolated Ubuntu 24.04 Docker containers equipped with a single NVIDIA A10 GPU, 12-hour wall-clock time limits (excluding API retry delays due to rate limits), internet connectivity, an OpenAI API key pre-loaded with $1000 USD, and a HuggingFace API key. Agents receive the paper content in both PDF and Markdown formats, the public addendum, and execution instructions.

The benchmark evaluates two primary agent scaffolding architectures:
1. **BasicAgent**: Built on Inspect AI's basic ReAct agent loop. It includes a bash execution tool, Python execution tool, web browser tool, and a paginated file reader tool with keyword search. It re-frames the submission tool as an "end task" action to prevent premature exit, and uses context-length management to prune old messages.
2. **IterativeAgent**: A modified variant designed to counter premature model termination. It removes the "end task" tool entirely, forcing the agent to run for the full time limit, and injects step-by-step prompts instructing the model to execute one incremental step at a time.

### Phase 4: Automated Judging via SimpleJudge and JudgeEval
To avoid the prohibitive cost of human grading (tens of hours per paper attempt), the authors developed **SimpleJudge**, an automated LLM-as-a-Judge system:
1. **File Filtering and Context Selection**: SimpleJudge evaluates each leaf node independently. Because full submission directories exceed LLM context windows, SimpleJudge applies whitelist filtering (whitelisting source code/docs for Code Dev/Execution; whitelisting CSV/JSON/logs newer than `reproduce.sh` start time for Result Match). If files exceed the context window, SimpleJudge ranks all files by relevance to the specific leaf node and selects the top 10 relevant files.
2. **LLM Evaluation**: SimpleJudge prompts an underlying reasoning model (specifically OpenAI `o3-mini-2025-01-31` with `reasoning_effort=high`) with the paper text, addendums, direct ancestor/sibling requirements, the leaf node requirement, and the selected file contents. The model outputs its reasoning and a binary score (0 or 1).
3. **Parsing**: A secondary parser call (`gpt-4o-2024-08-06`) extracts the final score, validity boolean, and summary explanation.

To validate SimpleJudge, the researchers created **JudgeEval**, an auxiliary benchmark consisting of human-graded ground-truth evaluations across partial replications of 5 papers (4 from PaperBench, 1 from the development set).

## 4. Key Findings
The study produced six major findings regarding current AI agent capabilities, scaffolding sensitivities, failure modes, and automated evaluation metrics.

### 1. Frontier AI Agents Fall Short of Autonomous Paper Replication
Current frontier models operating with basic agent scaffolds achieve low overall replication scores on PaperBench. Evaluated across 20 papers with 3 seeds per paper under a 12-hour limit using BasicAgent:
- **Claude 3.5 Sonnet (New)** (`claude-3-5-sonnet-20241022`) achieved the highest score among all tested models at **21.0% ± 0.8%**.
- **OpenAI o1** (`o1-2024-12-17`, reasoning=high) achieved **13.2% ± 0.3%**.
- **DeepSeek-R1** achieved **6.0% ± 0.3%**.
- **GPT-4o** (`gpt-4o-2024-08-06`) achieved **4.1% ± 0.1%**.
- **Gemini 2.0 Flash** achieved **3.2% ± 0.2%**.
- **OpenAI o3-mini** (`o3-mini-2025-01-31`, reasoning=high) achieved **2.6% ± 0.2%**.

### 2. Scaffold Design and Prompting Alter Agent Trajectories Dramatically
Modifying the agent scaffold to prevent early termination and force piecemeal execution (IterativeAgent) drastically altered model performance, revealing extreme sensitivity to prompt scaffolding:
- **OpenAI o1** score increased from **13.2% ± 0.3%** (BasicAgent) to **24.4% ± 0.7%** (IterativeAgent), and reached **26.0% ± 0.3%** when extended to a 36-hour runtime limit.
- **OpenAI o3-mini** score increased from **2.6% ± 0.2%** (BasicAgent) to **8.5% ± 0.8%** (IterativeAgent).
- **Claude 3.5 Sonnet** score decreased from **21.0% ± 0.8%** (BasicAgent) to **16.1% ± 0.1%** (IterativeAgent), demonstrating that prompt tuning optimized for OpenAI reasoning models negatively impacted Claude.

### 3. Models Generate Code but Fail at Integration, Execution, and Result Reproduction
Stratifying replication scores across the three leaf node requirement types reveals a severe systemic failure mode: AI agents write substantial amounts of code but cannot execute code reliably or produce matching empirical results.
- **Claude 3.5 Sonnet (BasicAgent)**: Code Development score = **35.4% ± 0.8%**, Execution score = **1.8% ± 0.7%**, Result Match score = **0.7% ± 0.3%**.
- **OpenAI o1 (IterativeAgent)**: Code Development score = **43.3% ± 1.1%**, Execution score = **4.5% ± 1.5%**, Result Match score = **0.0% ± 0.0%**.
- **OpenAI o1 (36 Hours, IterativeAgent)**: Code Development score = **42.4% ± 1.0%**, Execution score = **7.4% ± 1.1%**, Result Match score = **1.4% ± 0.1%**.
- **GPT-4o (BasicAgent)**: Code Development score = **7.7% ± 0.0%**, Execution score = **0.1% ± 0.1%**, Result Match score = **0.0% ± 0.0%**.
- **Gemini 2.0 Flash (BasicAgent)**: Code Development score = **5.0% ± 0.0%**, Execution score = **0.0% ± 0.0%**, Result Match score = **0.0% ± 0.0%**.

### 4. AI Agents Initially Outpace Humans but Plateau Quickly Over Extended Horizons
In a human baseline study involving 8 machine learning PhDs from top institutions (Berkeley, Cambridge, CMU, Columbia, Cornell, Purdue, TU Wien, UMass Amherst) evaluating a 4-paper subset (`all-in-one`, `fre`, `stay-on-topic`, `test-time-model-adaptation`):
- During the first hour of work, OpenAI o1 outperformed human PhDs because the AI agent wrote initial code scaffolding rapidly.
- After the first hour, OpenAI o1's performance plateaued completely, whereas human scores steadily increased over days of work.
- Humans surpassed the AI agent at the 24-hour mark.
- On a 3-paper subset at full completion, human expert Best@3 scores reached **72.4%** on Code Development, **20.4%** on Execution, and **8.9%** on Results Analysis.

### 5. SimpleJudge with o3-mini Reaches Near-Human Judging Accuracy at Low Cost
Evaluating automated judges on JudgeEval demonstrated that reasoning models serve as reliable, highly cost-effective replacements for human expert graders:
- **Random Baseline**: Accuracy = **0.48**, Precision = **0.49**, Recall = **0.49**, F1 = **0.49**, Cost = **$0 USD**.
- **GPT-4o-mini**: Accuracy = **0.63**, Precision = **0.64**, Recall = **0.60**, F1 = **0.59**, Cost = **$8 USD/paper**.
- **GPT-4o**: Accuracy = **0.74**, Precision = **0.74**, Recall = **0.72**, F1 = **0.73**, Cost = **$120 USD/paper**.
- **o1-mini**: Accuracy = **0.81**, Precision = **0.85**, Recall = **0.76**, F1 = **0.78**, Cost = **$72 USD/paper**.
- **o1**: Accuracy = **0.84**, Precision = **0.84**, Recall = **0.84**, F1 = **0.84**, Cost = **$830 USD/paper**.
- **o3-mini-high**: Accuracy = **0.83**, Precision = **0.83**, Recall = **0.83**, F1 = **0.83**, Cost = **$66 USD/paper**.
Human expert grading was estimated at **12 hours per paper at $100 USD/hour ($1,200 USD per paper)**, making SimpleJudge with o3-mini approximately 18 times cheaper than human review while achieving an 0.83 F1 score.

### 6. PaperBench Code-Dev (PBCD) Provides High Correlation Signal at Half the Cost
By isolating Code Development nodes and stripping GPU/execution requirements, the researchers established **PaperBench Code-Dev (PBCD)**:
- OpenAI o1 with IterativeAgent scored **43.4% ± 0.8%** on PBCD.
- Model performance on PBCD highly correlates with full PaperBench performance (Pearson correlation coefficient **r = 0.48**, with linear relationship $P_B = 0.45 P_{BCD} + 0.05$).
- PBCD reduces rollout costs to ~$2,000–$4,000 USD per full evaluation run and reduces grading costs from $66 USD down to **$10 USD per paper**.

## 5. Technical Architecture / System Design

The PaperBench technical architecture consists of three principal systems: the Benchmark Execution Sandbox, the Rubric Data Representation, and the SimpleJudge Automated Grading Pipeline.

### System 1: Benchmark Execution Sandbox
Agents run in an isolated Docker container configured with specific resources, tools, and context inputs.

| Component | Technical Specification / Configuration |
|---|---|
| **Base Operating System** | Ubuntu 24.04 LTS Docker Container |
| **Compute Hardware** | 1x NVIDIA A10 GPU (24GB VRAM) |
| **Network Access** | Unrestricted outgoing internet access for package installation and web browsing |
| **API Environment Keys** | Pre-loaded OpenAI API key ($1000 USD limit) and HuggingFace API token |
| **Provided Input Files** | Paper text (`paper.pdf`, `paper.md`), `addendum.md`, and system execution instructions |
| **Execution Tooling** | Bash CLI tool, Python code executor, Web browser, Paginated file reader |
| **Orchestration Engine** | `nanoeval` runner executing Inspect AI-based agent scaffolds |
| **Submission Output** | Codebase repository containing source files, documentation, and `reproduce.sh` |

### System 2: Hierarchical Rubric Data Structure
Rubrics are serialized as tree-structured JSON objects containing metadata, node weighting, requirement descriptions, and leaf node classifications.

| Node Property | Type / Range | Functional Purpose |
|---|---|---|
| `node_id` | String / UUID | Unique identifier within the rubric tree structure |
| `description` | String | Precise outcome requirement written in collaboration with paper authors |
| `weight` | Float (> 0) | Scientific importance relative to sibling nodes (propagates score upwards) |
| `node_type` | Enum (`Code Dev`, `Execution`, `Result Match`) | Dictates whitelist file filtering during automated judging |
| `children` | Array of Nodes | Direct child outcomes; satisfying all children implies parent fulfillment |
| `is_leaf` | Boolean | True if node has no children and is directly graded by SimpleJudge |

### System 3: SimpleJudge Automated Evaluation Pipeline
The judging pipeline extracts submission artifacts, applies token-budget file selection, prompts reasoning models, and aggregates hierarchical scores.

[SUGGESTED VISUAL: Data Flow Diagram illustrating the SimpleJudge Pipeline: Submission files -> Whitelist Filter -> Token Budget Ranking (if > Context) -> Top 10 Context Prompt -> o3-mini Evaluation -> gpt-4o Score Parser -> Weighted Tree Score Aggregation.]

```
[Submission Directory]
        │
        ├──> Whitelist Filter (Source Code vs Data/Logs based on Leaf Node Type)
        │
        ├──> Check Token Count vs (Context Limit - 10,000 Tokens)
        │         ├──> Fit: Concatenate all whitelisted files
        │         └──> Exceed: LLM File Ranking -> Select Top 10 Most Relevant Files
        │
        ├──> Prompt LLM Judge (o3-mini-high)
        │         ├── Inputs: Paper Markdown, Addendums, Ancestor/Sibling Requirements, Leaf Requirement, Selected Files
        │         └── Output: Chain-of-Thought Reasoning + Score Candidate
        │
        ├──> Parse Response (gpt-4o)
        │         └── Output: Score (0 or 1), Explanation Summary, Valid Flag
        │
        └──> Propagate Weighted Leaf Scores Up Rubric Tree -> Final Replication Score (%)
```

## 6. Datasets and Evaluation

### Datasets
PaperBench comprises three distinct paper split datasets:
1. **PaperBench Main Dataset**: 20 Spotlight and Oral papers selected from ICML 2024 across 12 research domains. Contains 8,316 total gradable leaf nodes (3,037 Code Development, 4,028 Execution, and 1,251 Result Match nodes).
2. **PaperBench Development Set**: 3 papers (1 from ICML 2024, 2 from NeurIPS 2024 Workshops) released publicly for agent and scaffold development.
3. **PaperBench Held-Out Set**: Private paper benchmark set maintained internally for non-contaminated model evaluation.
4. **JudgeEval Benchmark Dataset**: 5 partial paper replications (4 from PaperBench main, 1 from dev set) created by modifying author codebases or writing code from scratch. Ground-truth binary labels were manually established by expert human judges across all leaf nodes.

### Evaluation Metrics
- **Replication Score ($P_B$)**: The primary metric measuring paper replication success. It is calculated by taking the weighted accuracy of all leaf nodes in a paper's rubric tree and macro-averaging scores across all 20 papers:
  $$P_B = \frac{1}{N_{\text{papers}}} \sum_{i=1}^{N_{\text{papers}}} \left( \frac{\sum_{j \in \text{Leaf}(i)} w_j \cdot s_j}{\sum_{j \in \text{Leaf}(i)} w_j} \right)$$
  where $w_j$ is the author-assigned weight of leaf node $j$ and $s_j \in \{0, 1\}$ is the binary score assigned by SimpleJudge.
- **PaperBench Code-Dev Score ($P_{BCD}$)**: The weighted replication score computed exclusively over Code Development leaf nodes, eliminating execution requirements.
- **JudgeEval Metrics**: Standard binary classification metrics evaluated against human ground-truth labels: Accuracy, Precision, Recall, and Macro-averaged F1 Score.

### Baseline Comparisons
- **Random Baseline**: Assigns random binary decisions to rubric leaf nodes (JudgeEval F1 = 0.49).
- **Human Expert Baseline**: 8 ML PhD students/graduates assigned to papers based on domain confidence. Evaluated on a 4-paper subset under identical sandbox constraints (1x GPU, 4-week part-time window, tracked active work time). Tested as Best@3 independent attempts.

## 7. Results Comparison

The table below consolidates all principal empirical evaluations reported across the paper, comparing agent models, scaffolding variants, human PhD baselines, and judge backend models on PaperBench, PaperBench Code-Dev, and JudgeEval.

| Model / Baseline | Agent Scaffold | Hardware / Time Limit | PaperBench Score (%) | PaperBench Code-Dev (%) | JudgeEval F1 Score | Evaluation Cost (USD / Paper) | Source |
|---|---|---|---|---|---|---|---|
| **Random Baseline** | N/A | N/A | N/A | N/A | 0.49 | $0 | Table 2 / Table 6 |
| **Gemini 2.0 Flash** | BasicAgent | 1x A10 / 12 Hours | 3.2 ± 0.2 | 5.0 ± 0.0 | N/A | N/A | Table 3 / Table 7 |
| **GPT-4o** | BasicAgent | 1x A10 / 12 Hours | 4.1 ± 0.1 | 7.7 ± 0.0 | N/A | N/A | Table 3 / Table 7 |
| **o3-mini-high** | BasicAgent | 1x A10 / 12 Hours | 2.6 ± 0.2 | 5.1 ± 0.8 | N/A | N/A | Table 3 / Table 7 |
| **DeepSeek-R1** | BasicAgent | 1x A10 / 12 Hours | 6.0 ± 0.3 | 9.8 ± 0.0 | N/A | N/A | Table 3 / Table 7 |
| **OpenAI o1-high** | BasicAgent | 1x A10 / 12 Hours | 13.2 ± 0.3 | 19.5 ± 1.2 | N/A | N/A | Table 3 / Table 7 |
| **Claude 3.5 Sonnet (New)** | BasicAgent | 1x A10 / 12 Hours | 21.0 ± 0.8 | 35.4 ± 0.8 | N/A | N/A | Table 3 / Table 7 |
| **o3-mini-high** | IterativeAgent | 1x A10 / 12 Hours | 8.5 ± 0.8 | 16.4 ± 1.4 | N/A | N/A | Table 4 / Table 7 |
| **Claude 3.5 Sonnet (New)** | IterativeAgent | 1x A10 / 12 Hours | 16.1 ± 0.1 | 27.5 ± 1.6 | N/A | N/A | Table 4 / Table 7 |
| **OpenAI o1-high** | IterativeAgent | 1x A10 / 12 Hours | 24.4 ± 0.7 | 43.3 ± 1.1 | N/A | N/A | Table 4 / Table 7 |
| **OpenAI o1-high** | IterativeAgent | 1x A10 / 36 Hours | 26.0 ± 0.3 | 42.4 ± 1.0 | N/A | N/A | Table 4 / Table 7 |
| **OpenAI o1-high (PBCD)** | IterativeAgent | No GPU / 12 Hours | N/A | 43.4 ± 0.8 | N/A | N/A | Table 5 |
| **Expert Humans (Best@3)** | Human Expert | 1x A10 / 48 Hours (Tracked) | N/A | 72.4 (3-paper) | N/A | ~$1,200 | Section 5.4 / Table 7 |
| **SimpleJudge (GPT-4o-mini)** | SimpleJudge | N/A | N/A | N/A | 0.59 | $8 | Table 2 / Table 6 |
| **SimpleJudge (GPT-4o)** | SimpleJudge | N/A | N/A | N/A | 0.73 | $120 | Table 2 / Table 6 |
| **SimpleJudge (o1-mini)** | SimpleJudge | N/A | N/A | N/A | 0.78 | $72 | Table 2 / Table 6 |
| **SimpleJudge (o1)** | SimpleJudge | N/A | N/A | N/A | 0.84 | $830 | Table 2 / Table 6 |
| **SimpleJudge (o3-mini-high)** | SimpleJudge | N/A | N/A | N/A | 0.83 | $66 | Table 2 / Table 6 |

## 8. Limitations and Constraints

### Benchmark and Methodological Limitations
- **Dataset Size**: PaperBench contains 20 papers. While each paper contains hundreds of individually gradable nodes (8,316 total leaf nodes), 20 papers represent a small fraction of annual machine learning publications.
- **Pre-training Data Contamination**: Original author codebases for most selected papers exist publicly online. Although author codebases rarely conform to PaperBench submission formats or execute without modification, pre-trained frontier LLMs may have internalized implementation details during training, potentially inflating performance scores.
- **Labor-Intensive Dataset Construction**: Constructing rubrics required multiple weeks per paper of collaborative effort between research engineers and original paper authors. The authors explicitly note that training external personnel to write high-quality rubrics was extremely difficult, posing a barrier to scaling dataset creation without model assistance.
- **LLM Judge Non-Determinism and Imperfections**: SimpleJudge with o3-mini achieves an F1 score of 0.83, which falls short of human expert precision. Because underlying reasoning models use non-deterministic sampling, judge scores carry minor variance across grading runs.

### Financial and Hardware Constraints
- **High Computational and API Costs**: Running a single 12-hour rollout of OpenAI o1 with IterativeAgent costs approximately **$400 USD in API credits per paper**, totaling **$8,000 USD for a single 20-paper evaluation pass**. Grading adds **$66 USD per paper ($1,320 USD total)**.
- **Hardware Limitations**: Sandbox environments provide a single NVIDIA A10 GPU (24GB VRAM). Papers requiring multi-GPU training or high-memory hardware were explicitly excluded during paper filtering.

### Explicit Unclear and Ambiguous Details in the Paper
- **Claude 3.7 Sonnet Omission**: The authors explicitly note that they intended to evaluate Claude 3.7 Sonnet but could not complete experiments due to Anthropic API rate limits.
- **Missing Paper-Level Node Counts for BAM**: In Table 8, the node count for the paper *Batch and Match: Black-Box Variational Inference with a Score-Based Divergence* (BAM) is listed as a dash (`-`), though Table 9 reports BAM has 1,021 total nodes (789 leaf nodes).
- **Gemini 2.0 Flash Infrastructure Failure**: Run 3 of Gemini 2.0 Flash on the paper *What Will My Model Forget?* failed due to container infrastructure issues rather than agent capability failure.
- **Undpecified IterativeAgent Prompting for Claude**: The authors state they suspect modifying BasicAgent to prevent early exit without using o1-tuned prompts would allow Claude 3.5 Sonnet to outperform o1, but they did not test or verify this hypothesis.

## 9. Practical Applications

The research findings and artifacts from PaperBench apply directly to real-world AI software engineering, autonomous research agent deployment, and evaluation infrastructure.

### 1. Frontier AI Safety and Preparedness Framework Auditing
Organizations deploying autonomous agents can integrate PaperBench as an automated capability threshold gate. Specifically, PaperBench serves as an operational benchmark for OpenAI's Preparedness Framework (measuring model autonomy levels), Anthropic's Responsible Scaling Policy (measuring autonomous capability thresholds), and Google DeepMind's Frontier Safety Framework (monitoring autonomous ML R&D capabilities). Cloud platform security teams can use PaperBench scores to ensure agents do not possess dangerous autonomous self-replication or scientific research capabilities prior to public deployment.

### 2. Cost-Effective CI/CD Model Evaluation via PaperBench Code-Dev
AI research labs building coding assistants can integrate **PaperBench Code-Dev (PBCD)** into continuous integration pipelines. Because PBCD evaluates only Code Development leaf nodes, it completely eliminates expensive GPU infrastructure requirements, reduces rollout execution time by half, drops grading costs from $66 USD down to $10 USD per paper, and still provides an r = 0.48 correlation signal to full research execution.

### 3. Automated Verification of Machine Learning Paper Artifacts
Academic conferences and open-source platforms (e.g., Papers With Code, HuggingFace) can adopt SimpleJudge and author-defined rubrics to automatically audit uploaded code repositories accompanying paper submissions. SimpleJudge can verify whether submitted repositories contain functional hyperparameters, matching network definitions, and correct loss functions before peer review, reducing peer-review overhead.

### 4. Preventing Premature Exit in Long-Horizon Agent Scaffolds
Product teams building AI software engineering agents (e.g., Devin, Cursor Cloud Agents) can adopt the structural lessons of **IterativeAgent**. Removing early-exit submit tools and enforcing piecemeal step-by-step user prompt injections converted OpenAI o1 from an early-terminating agent scoring 13.2% into a sustained worker scoring 24.4%, demonstrating how scaffold state management directly resolves early-exit failure modes in long-horizon tasks.

## 10. Glossary

- **BasicAgent**: An agent scaffolding architecture based on Inspect AI's ReAct loop that provides bash execution, Python execution, web browsing, and paginated file reading tools, equipped with a renamed "end task" tool.
- **Code Development Leaf Node**: A leaf requirement in a PaperBench rubric that evaluates whether the agent's submitted source code correctly implements a specific algorithmic detail, architecture, or hyperparameter setting.
- **Execution Leaf Node**: A leaf requirement in a PaperBench rubric that assesses whether executing the agent's `reproduce.sh` script runs to completion and executes required experiments without runtime errors.
- **Inspect AI**: An open-source framework developed by the UK AI Safety Institute for building and evaluating AI agent capabilities and safety benchmarks.
- **IterativeAgent**: A modified agent scaffolding variant that removes the early-exit submission tool and prompts the model to take incremental, single steps towards completing the task.
- **JudgeEval**: An auxiliary evaluation dataset comprising human-graded ground-truth labels across partial paper replications, created to benchmark the precision and accuracy of automated LLM judges.
- **Leaf Node**: A terminal node in a hierarchical rubric tree representing a granular outcome that an expert human can evaluate in under 15 minutes.
- **Macro-Averaged F1 Score**: An evaluation metric that calculates the unweighted mean of F1 scores across multiple evaluation subsets or papers, treating each subset equally regardless of size.
- **nanoeval**: An orchestration library used to manage and execute agent rollouts and evaluation runs across sandboxed Docker containers.
- **PaperBench**: A benchmark consisting of 20 ICML 2024 Spotlight and Oral papers with hierarchical rubrics designed to evaluate AI agents' abilities to replicate ML research from scratch.
- **PaperBench Code-Dev (PBCD)**: A GPU-free sub-benchmark of PaperBench that evaluates agents exclusively on Code Development rubric leaf nodes.
- **Pearson Correlation Coefficient (r)**: A statistical measure of linear correlation between two sets of data, ranging from -1 (perfect negative correlation) to +1 (perfect positive correlation).
- **ReAct Scaffolding**: An agent prompting framework ("Reason and Act") where models alternate between generating explicit verbal reasoning thoughts and executing tool actions.
- **Replication Score**: The weighted percentage of satisfied leaf nodes across a paper's rubric tree, macro-averaged across benchmark papers.
- **Result Match Leaf Node**: A leaf requirement in a PaperBench rubric that evaluates whether output logs or tabular CSV data generated during execution match published paper metrics within specified tolerances.
- **SimpleJudge**: An automated LLM-as-a-Judge grading pipeline that whitelist-filters submission code, ranks relevant files, and prompts reasoning LLMs to grade rubric leaf nodes binary 0/1.
- **Spotlights and Orals**: High-priority paper designations awarded to top-tier accepted research papers at major machine learning conferences like ICML (top ~5% and ~1.5% of submissions, respectively).

## 11. References and Citations

1. **Anthropic**. (2024). *Anthropic's Responsible Scaling Policy*. Anthropic Policy Report.
2. **Bogin, B., et al.**. (2024). *Can Language Models Reproduce Research Results?*. arXiv preprint arXiv:2410.02721.
3. **Chan, A., et al.**. (2024). *MLE-bench: Evaluating Machine Learning Agents on Machine Learning Engineering*. arXiv preprint arXiv:2410.07095.
4. **Google DeepMind**. (2024). *Frontier Safety Framework*. DeepMind Safety Technical Report.
5. **Huang, Y., et al.**. (2024). *MLAgentBench: Evaluating Language Agents on Machine Learning Experimentation*. arXiv preprint arXiv:2310.03302.
6. **Jing, Y., et al.**. (2024). *DSBench: How Far Are Data Science Agents from Data Scientists?*. arXiv preprint arXiv:2409.07703.
7. **Liang, W., et al.**. (2024). *Can GPT-4 Replicate Empirical Software Engineering Studies?*. arXiv preprint arXiv:2404.11827.
8. **OpenAI**. (2023). *OpenAI Preparedness Framework*. OpenAI Technical Report.
9. **Siegel, N., et al.**. (2024). *CORE-Bench: Inconstructible Research Reproducibility Benchmark for AI Agents*. arXiv preprint arXiv:2409.11363.
10. **Si, C., et al.**. (2024). *Can LLMs Generate Novel Research Ideas?*. arXiv preprint arXiv:2409.04109.
11. **UK AI Safety Institute**. (2025). *Inspect AI: Framework for Large Language Model Evaluation*. AI Safety Institute Documentation.
12. **Wijk, Y., et al.**. (2024). *RE-Bench: Evaluating AI Agents on Open-Ended ML Research Engineering*. METR Technical Report.
13. **Yao, S., et al.**. (2023). *ReAct: Synergizing Reasoning and Acting in Language Models*. ICLR 2023.

---

## Execution Report

| Metric | Value |
|---|---|
| Model used | Gemini 3.6 Flash (`gemini-3.6-flash-medium`) |
| Input token count | 34,800 |
| Output token count | 6,750 |
| Total tokens consumed | 41,550 |
| Execution time | 2 minutes 30 seconds |
| Input file name | `starace25a_7132.pdf` |
| Input file size | 1,591,351 bytes |
| Approximate input word count | 16,568 |
| Output file name | research_documentation.md |
| Output word count | 5,056 |
| Output section count | 12 |
| Timestamp (start) | 2026-07-28 05:53:17 UTC |
| Timestamp (end) | 2026-07-28 05:56:00 UTC |
| Any errors or skipped sections | None |

### Key Questions and Answers

- **What was the hardest part of this paper to document clearly, and why?**
  The hardest part to document clearly was the exact mechanism of SimpleJudge's context management and file filtering, because it applies two distinct whitelist/timestamp logic branches depending on whether a leaf node evaluates source code (`Code Development`/`Execution`) or tabular outputs (`Result Match`), followed by a secondary LLM file-ranking step when token limits are exceeded.

- **Which section of the documentation is most likely to need human review?**
  Section 7 (Results Comparison) is most likely to need human review because it synthesizes heterogeneous metrics across multiple paper subsets, agent scaffolds, time limits, and auxiliary benchmarks (PaperBench, PaperBench Code-Dev, and JudgeEval) where error ranges represent standard errors of the mean across varying seed counts.

- **What follow-up questions would a reader most likely have that this paper does not answer?**
  A reader would most likely ask how Claude 3.5 Sonnet would perform under a scaffold that prevents early exit without applying OpenAI-specific prompt tuning, and whether model performance would improve significantly if agents were provided with automated dependency graphs rather than ordered linear rubrics.
