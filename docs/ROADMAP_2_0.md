TargetIntel-IO 2.0 Roadmap
Vision

TargetIntel-IO 2.0 will evolve from a transparent rule-based target-prioritization framework into a hybrid artificial-intelligence platform for evidence-grounded target intelligence.

The platform will integrate multiple types of biomedical evidence into a common, traceable representation:

Open Targets ──────────────────┐
Scientific literature ─────────┤
DepMap / CRISPR ───────────────┤
Single-cell / spatial data ────┤
Clinical cohorts ──────────────┤
Drugs, tractability, safety ───┘
                  │
                  ▼
        NORMALIZED EVIDENCE OBJECTS
           with complete provenance
                  │
                  ▼
       EVIDENCE TABLE / KNOWLEDGE GRAPH
                  │
       ┌──────────┼───────────────┐
       ▼          ▼               ▼
 Existing     Target ML      Patient-response
 rules         models            models
       └──────────┼───────────────┘
                  ▼
        STRUCTURED DECISION LAYER
                  ▼
         LLM REASONER AND CRITIC
                  ▼
 Reports containing observations,
 interpretations, contradictions,
 citations, limitations, and uncertainty

The large language model will not be the source of truth.

It will act as a scientific research assistant that queries tools, retrieves stored evidence, evaluates contradictions, and generates explanations grounded in verifiable observations.

Core Design Principles
Evidence before interpretation

All conclusions must originate from structured evidence stored by the platform.

The system must clearly separate:

Retrieved or computed observations
System-generated interpretations
Final target-level recommendations

An LLM may generate an interpretation, but only from observations already stored and linked to their original sources.

Traceability by default

Every evidence record must preserve:

source;
source identifier;
publication, dataset, experiment, or cohort identifiers;
retrieval date;
data release;
transformation history;
quoted or computed supporting evidence;
extraction method;
validation status.
Deterministic baseline preservation

The current transparent scoring and classification system must remain available as a deterministic baseline.

Future statistical models and LLM components must be optional and must not silently alter existing rankings.

No unsupported scientific claims

The system must not:

invent references, identifiers, values, or citations;
describe association as causation;
treat missing evidence as negative evidence;
interpret an internal benchmark as independent biological validation;
treat LLM extraction confidence as scientific confidence.
Independent evidence matters more than record count

The platform must distinguish between:

number of database records;
number of independent experiments;
number of independent publications;
number of independent patient cohorts.

Multiple records derived from the same experiment must not be counted as independent confirmation.

1. Common Evidence Layer

The first and most important architectural change is the introduction of a common evidence representation.

Before adding more scores, datasets, or machine-learning models, all information sources must communicate through the same evidence contract.

EvidenceItem

Every scientific observation will be stored as an EvidenceItem.

Example:

{
  "target": "B2M",
  "disease": "melanoma",
  "treatment": "anti-PD-1",
  "claim": "Loss of B2M is associated with resistance to anti-PD-1",
  "evidence_direction": "supports_biomarker",
  "evidence_type": "clinical_cohort",
  "source": "Europe PMC",
  "source_id": "PMID:...",
  "publication_id": "PMID:...",
  "source_dataset_id": null,
  "patient_cohort_id": "cohort_identifier",
  "cohort_size": 38,
  "comparison": "non-responder versus responder",
  "effect_size": null,
  "p_value": null,
  "species": "human",
  "model_system": "pretreatment tumor biopsy",
  "quoted_span": "Exact sentence supporting the claim",
  "observation": "B2M loss was observed in patients with acquired resistance.",
  "interpretation": null,
  "extraction_method": "LLM",
  "extraction_confidence": 0.91,
  "validation_status": "citation_verified",
  "derived_from": [],
  "evidence_family": "B2M_acquired_resistance_cohort",
  "retrieved_at": "2026-07-10"
}

The same format should support:

genetic associations;
somatic mutations;
CRISPR dependencies;
single-cell expression;
spatial proximity;
clinical response;
tractability;
toxicity;
known drugs;
biomarker evidence;
resistance mechanisms;
contradictory findings;
negative or limiting evidence.
Observation and interpretation must remain separate
Retrieved observation

In cohort X, B2M loss was detected in N patients with acquired resistance.

System interpretation

This supports B2M as a resistance biomarker, but does not support its prioritization as a direct therapeutic target.

The observation must be stored before an interpretation can be generated.

The interpretation must reference the evidence records on which it depends.

2. Literature Copilot

The platform will not attempt to place the entire scientific literature inside a single LLM conversation.

Instead, it will implement an incremental retrieval, extraction, and verification system.

Europe PMC will initially serve as the primary literature source because it provides programmatic access to:

publication metadata;
abstracts;
references;
annotations;
open-access full text;
stable publication identifiers.
Proposed workflow
Target + disease + treatment context
                  │
                  ▼
      Query generation and synonym expansion
                  │
                  ▼
           Europe PMC retrieval
                  │
                  ▼
          Relevance classification
                  │
                  ▼
      Section-aware document segmentation
                  │
                  ▼
      Structured scientific claim extraction
                  │
                  ▼
       Citation and quotation verification
                  │
                  ▼
             EvidenceItems
                  │
                  ▼
        Target-level evidence summary
Example query

For B2M:

("B2M" OR "beta-2 microglobulin")
AND melanoma
AND ("PD-1" OR pembrolizumab OR nivolumab)
AND (resistance OR response OR progression)

The query-generation layer may expand searches using:

official gene names;
aliases and synonyms;
drug names;
treatment classes;
primary resistance terminology;
acquired resistance terminology;
antigen-presentation pathways;
related biological mechanisms;
disease ontology terms.
Information extracted from each paper

For every relevant publication, the extractor should determine:

Which gene or target was studied?
Which disease was studied?
Which treatment was evaluated?
Was the evidence human, mouse, cell-line, organoid, or in silico?
How many samples or patients were included?
Which comparison was performed?
Which result was reported?
Does the result support, contradict, or limit the hypothesis?
Does the finding concern a target, biomarker, mechanism, or contextual marker?
Which exact passage supports the extraction?
Which table, figure, section, or supplementary item contains the evidence?
Is the finding derived from another dataset or cohort?
Hallucination controls

A literature-derived claim must not enter the evidence store unless it contains:

PMID, DOI, PMCID, or another stable identifier;
a verifiable supporting quotation or document location;
disease context;
treatment context when relevant;
evidence type;
evidence direction;
link to the source document;
extraction method;
validation status.

Citations must be generated from retrieved metadata, not from LLM-generated text.

LLM responsibilities

The LLM layer will eventually perform three separate functions.

Extractor

Transforms scientific text into structured evidence objects.

Critic

Searches for:

contradictory evidence;
negative evidence;
methodological limitations;
alternative explanations;
safety concerns;
weak or indirect evidence.
Writer

Generates the final target explanation using only verified evidence records.

The first implementation should not use multiple autonomous agents debating one another.

A single extractor with deterministic validation and citation verification will be easier to evaluate and debug.

3. Expanded Open Targets Integration

The current implementation primarily uses target–disease association information.

TargetIntel-IO 2.0 should expand this integration to include target feasibility, tractability, clinical precedent, and safety.

For systematic large-scale analysis, versioned downloads or BigQuery-based workflows should be preferred over repeated individual GraphQL requests when appropriate.

Candidate features
association_score_by_source
genetic_association_score
somatic_mutation_score
known_drug_count
maximum_clinical_phase
small_molecule_tractability
antibody_tractability
protac_tractability
chemical_probe_available
safety_signal_count
normal_tissue_risk
clinical_precedence
Example

A simple expert rule such as:

BRAF → suitable small-molecule target

should evolve into a traceable evidence profile:

BRAF
├── melanoma association
├── compatible small-molecule binding pocket
├── pharmacological precedent
├── approved or investigational drugs
├── clinical-stage evidence
├── known resistance mechanisms
└── potential safety limitations

Expert rules will remain useful, but they will no longer be the only source of target-feasibility information.

4. DepMap and CRISPR Dependency

DepMap provides versioned public datasets containing CRISPR-derived gene dependencies and molecular profiles across cancer cell lines.

This layer will help identify functional vulnerabilities that are not already present in curated target lists.

Questions addressed

For each target:

Do melanoma cell lines require the gene for survival?
Is the dependency selective for melanoma?
Is the dependency widespread across cancer types?
What fraction of melanoma models is dependent?
Is dependency associated with BRAF, NRAS, or NF1 status?
Is dependency associated with expression or mutation?
Is there evidence for synthetic lethality?
Is the gene a common essential?
Would inhibition create a high toxicity risk?
Candidate features
depmap_mean_gene_effect_melanoma
depmap_fraction_dependent_melanoma
depmap_lineage_selectivity
depmap_pan_cancer_dependency
depmap_common_essential_flag
depmap_expression_dependency_correlation
depmap_braf_mutant_dependency
depmap_nras_mutant_dependency
depmap_nf1_mutant_dependency
Contribution to de novo discovery

Current high-priority targets largely originate from curated biological knowledge.

DepMap may identify genes that:

are absent from the current ontology;
do not have known drugs;
are not prominent in the literature;
show selective dependency in a melanoma subtype;
interact with known resistance pathways.

These genes can become de novo candidates for further investigation.

Limitation

Cell-line dependency does not demonstrate that a gene:

is a suitable target in patients;
modulates anti-PD-1 response;
is safe to inhibit;
is relevant within an intact immune microenvironment.

DepMap must therefore contribute one evidence layer, not determine the final recommendation.

5. Single-Cell and Spatial Context

Single-cell and spatial data will provide information about where a target is expressed and which biological compartment it may affect.

CELLxGENE Census can provide programmatic, versioned access to harmonized single-cell datasets and support retrieval into formats such as AnnData, Seurat, or SingleCellExperiment.

Questions addressed

For each target:

Which cell types express the target?
Is expression found in malignant cells, T cells, macrophages, Tregs, fibroblasts, or endothelial cells?
What fraction of each population expresses the target?
Is expression tumor-specific?
Is it also expressed in healthy tissue?
Does expression increase after treatment?
Is it associated with exhausted T-cell states?
Is it enriched in immune-excluded regions?
Does it participate in a ligand–receptor interaction?
Is expression consistent across patients?
Candidate single-cell features
malignant_expression_mean
malignant_fraction_positive
immune_expression_mean
treg_specificity
myeloid_specificity
fibroblast_specificity
tumor_vs_normal_specificity
resistant_vs_sensitive_logFC
pre_vs_on_treatment_logFC
patient_consistency
Candidate spatial features
distance_to_exhausted_T_cells
distance_to_tumor_boundary
immune_exclusion_association
expression_in_TGFb_rich_regions
co_localization_with_PDCD1_cells
ligand_receptor_interaction_score
Role of the LLM

The LLM should not directly analyze millions of cells.

Numerical analysis should be performed using:

Scanpy;
Seurat;
statistical models;
differential-expression methods;
ligand–receptor methods;
spatial-neighborhood analysis;
cell-state and pathway scoring.

The LLM will receive structured summaries such as:

Target X is expressed in 68% of TREM2-positive macrophages
and 4% of malignant cells.

It may then generate a grounded interpretation:

The observed cellular distribution supports a myeloid-targeting
hypothesis rather than a direct tumor-cell-targeting hypothesis.
6. Anti-PD-1 Clinical Response Cohorts

This phase begins the transition from target intelligence toward patient-response research.

Candidate public melanoma cohorts include:

Hugo et al. — GSE78220;
Riaz et al. — GSE91061;
Gide et al.;
additional compatible anti-PD-1 cohorts identified during implementation.
Harmonized clinical table

The first task is to construct a harmonized representation:

patient_id
sample_id
cohort
therapy
timepoint
response
progression_free_survival
overall_survival
expression
mutation
clinical_covariates
Initial modeling strategy

The first models should remain simple, interpretable, and suitable for small heterogeneous cohorts:

regularized logistic regression;
elastic net;
random forest;
gradient boosting;
pathway scores;
immune-cell composition estimates.

Large transformers should not be the starting point because available clinical cohorts are relatively small and technically heterogeneous.

External validation strategy
Train using Hugo + Riaz
          │
          ▼
Select model and parameters
without inspecting Gide outcomes
          │
          ▼
Lock the model
          │
          ▼
Externally validate in Gide

Samples from the same patient must never be divided between training and test partitions.

Candidate outputs
predicted_response_probability
calibration_interval
top_supporting_features
top_opposing_features
cohort_similarity
out_of_distribution_warning
Role of the LLM

The response probability must originate from the statistical model.

The LLM may explain the prediction:

The low predicted response is primarily associated with reduced
antigen presentation, low T-cell infiltration, and an elevated
TGF-beta exclusion signature.

The LLM must not invent a probability or override the statistical model.

7. De Novo Target Discovery

De novo target discovery must not mean:

The LLM mentioned a gene that was not present in the original list.

It should mean:

An algorithm identified a candidate outside the curated rules that is supported by multiple independent evidence sources.

Candidate universe
All human genes
       │
       ▼
Genes with evidence from at least one source:
- Open Targets
- literature
- DepMap
- single-cell
- spatial data
- clinical cohorts
- biological networks
Knowledge graph

Candidate node types:

Target
Disease
Treatment
Drug
Pathway
Cell type
Cohort
Publication
Dataset
Resistance mechanism
Safety event

Candidate relationships:

TARGET associated_with DISEASE
TARGET dependent_in CELL_MODEL
TARGET expressed_in CELL_TYPE
TARGET associated_with RESPONSE
DRUG targets TARGET
TARGET participates_in PATHWAY
CLAIM supported_by PUBLICATION
TARGET has_safety_signal EVENT
EVIDENCE derived_from DATASET
Initial interpretable methods
network propagation;
similarity to known targets;
weighted evidence integration;
clustering of target profiles;
positive–unlabeled learning;
interpretable learning-to-rank.
Later methods
graph neural networks;
gene, disease, and drug embeddings;
multimodal models;
link prediction.

Candidate links may include:

target → resistance mechanism
target → treatment response
target → therapeutic modality
Role of the LLM

For each candidate, the LLM may:

retrieve relevant literature;
search for contradictory findings;
identify toxicity or feasibility limitations;
suggest a biological mechanism;
propose validation experiments;
generate a report with citations.

The LLM will not generate the original numerical signal.

It will contextualize and critically evaluate candidates identified by the analytical system.

8. Evidence Deduplication and Independence

Double counting will become a major risk when multiple sources are integrated.

Example:

A publication associates JAK1 with resistance.
Open Targets includes evidence from the same publication.
The literature extractor extracts the publication again.
A transcriptomic signature derived from the same cohort also contains JAK1.

These may appear to represent four pieces of evidence while originating from one underlying experiment.

Required provenance fields

Each evidence item should include:

source_dataset_id
publication_id
experiment_id
patient_cohort_id
derived_from
evidence_family

The system must group dependent evidence records and calculate independence at several levels.

Number of records
≠ Number of independent experiments
≠ Number of independent publications
≠ Number of independent cohorts

Evidence aggregation and target scoring must account for these distinctions.

9. Confidence Decomposition

A single confidence label is insufficient.

TargetIntel-IO should distinguish several independent dimensions.

Metric	Question
Data completeness	How much required information is available?
Evidence strength	How strong and appropriate are the underlying experiments?
Evidence independence	How many genuinely independent sources support the conclusion?
Decision robustness	Does the recommendation change when weights, assumptions, or evidence are perturbed?
LLM extraction confidence	How confident is the extraction system that it interpreted the source text correctly?

LLM extraction confidence must not be interpreted as evidence quality or scientific truth.

A high extraction-confidence score only means that the text-to-structure transformation appears reliable.

10. Multitumor Architecture

Melanoma-specific concepts should gradually be removed from the core implementation and moved into configurable context packs.

Proposed structure
configs/contexts/
├── melanoma_anti_pd1.yaml
├── nsclc_anti_pd1.yaml
├── renal_cancer_anti_pd1.yaml
├── colorectal_msi_immunotherapy.yaml
└── breast_cancer_adc.yaml
Example context pack
disease:
  name: melanoma
  ontology_id: MONDO_0005105

therapy:
  class: anti_PD1
  drugs:
    - nivolumab
    - pembrolizumab

relevant_cell_types:
  - malignant_cell
  - exhausted_T_cell
  - macrophage
  - Treg
  - fibroblast

resistance_programs:
  - antigen_presentation_loss
  - IFNG_resistance
  - myeloid_suppression
  - TGFb_exclusion
  - melanoma_plasticity

clinical_endpoints:
  - response
  - progression_free_survival
  - overall_survival

The analytical engine should remain generic.

Disease, treatment, cell-type, resistance-program, and endpoint definitions should be provided by the selected context pack.

Final AI Architecture

TargetIntel-IO 2.0 will not consist of one monolithic model.

It will combine several specialized components.

Component	Appropriate technology
Literature processing	Retrieval, LLM extraction, and citation verification
Biological evidence integration	Rules, statistical aggregation, and provenance models
CRISPR dependency	Statistics, machine learning, and biological networks
Single-cell and spatial analysis	Specialized omics methods
Target discovery	Learning-to-rank, graph methods, and eventually GNNs
Patient-response prediction	Supervised and calibrated statistical models
Scientific explanations	LLM grounded exclusively in verified evidence
Quality control	Deterministic rules, tests, schema validation, and citation verification

Together, these components constitute a hybrid AI platform for target intelligence.

Relationship Between Objectives and Requirements
Objective	What is actually required
Build an AI model	Add learned models, not only an LLM interface
De novo target discovery	Generate candidates outside curated lists and evaluate them using independent signals
Read literature automatically	Europe PMC retrieval, structured extraction, and citation verification
Integrate CRISPR and DepMap	Versioned downloads and dependency/selectivity features
Integrate single-cell and spatial data	Numerical pipelines and cell- or region-level features
Predict patient response	Labeled cohorts, locked models, calibration, and external validation
Achieve clinical validation	Retrospective external validation followed by prospective evaluation
Become multitumoral	Generic analytical engine plus configurable context packs

Clinical validation cannot be achieved through software development alone.

It requires appropriately designed retrospective and eventually prospective studies.

Version Roadmap
v0.2.0 — Common Evidence Layer and Literature Copilot
Objective

Establish the shared evidence infrastructure required by all later data sources and models.

Scope
EvidenceItem schema;
explicit separation of observation and interpretation;
controlled evidence vocabularies;
provenance and evidence lineage;
DuckDB and/or Parquet evidence store;
Europe PMC connector;
target-specific literature searches;
synonym and query expansion;
structured JSON extraction;
verifiable quotations and citations;
citation validation;
supportive and contradictory evidence;
evidence deduplication;
target evidence summaries;
manually evaluated extraction benchmark.
Explicitly out of scope
DepMap;
single-cell and spatial analysis;
patient-response prediction;
graph neural networks;
automatic changes to existing ranking weights;
multitumor production support.
v0.3.0 — Target Feasibility
Objective

Separate biological relevance from therapeutic feasibility.

Scope
expanded Open Targets integration;
target–disease evidence by source;
small-molecule tractability;
antibody tractability;
PROTAC tractability where available;
known drugs;
maximum clinical phase;
clinical precedent;
chemical probes;
safety signals;
normal-tissue risk;
explicit relevance-versus-druggability representation.
v0.4.0 — Functional Dependency
Objective

Add functional vulnerability evidence and identify non-curated candidate targets.

Scope
versioned DepMap CRISPR integration;
melanoma-specific dependency;
fraction of dependent melanoma models;
lineage selectivity;
pan-cancer dependency;
common-essential penalties;
BRAF-mutant dependency;
NRAS-mutant dependency;
NF1-mutant dependency;
expression–dependency correlations;
initial identification of candidates absent from the curated ontology.
v0.5.0 — Cellular and Spatial Context
Objective

Determine which cells and tissue regions express each candidate target.

Scope
selected single-cell datasets;
harmonized cell-type annotations;
malignant-cell expression;
immune-cell expression;
Treg, myeloid, and fibroblast specificity;
tumor-versus-normal specificity;
resistant-versus-sensitive comparisons;
pretreatment-versus-on-treatment comparisons;
patient-level consistency;
spatial immune-exclusion features;
ligand–receptor context;
target-level cellular-context reports.
v0.6.0 — Clinical Response Research Model
Objective

Develop and externally evaluate an interpretable anti-PD-1 response model.

Scope
Hugo cohort integration;
Riaz cohort integration;
Gide cohort integration;
harmonized response and survival variables;
preprocessing and batch-awareness;
interpretable baseline models;
pathway-level features;
immune-composition features;
patient-level train/test separation;
locked-model external validation;
probability calibration;
uncertainty estimates;
cohort-similarity assessment;
out-of-distribution warnings;
grounded LLM explanations of model outputs.
Limitation

This version will be a research model and must not be presented as a clinically validated diagnostic system.

v0.7.0 — De Novo Target Discovery
Objective

Generate and prioritize targets outside the existing curated rule system.

Scope
pan-gene candidate universe;
multi-source evidence profiles;
evidence knowledge graph;
network propagation;
similarity to known targets;
interpretable evidence integration;
positive–unlabeled learning;
learning-to-rank;
independent-evidence requirements;
identification of candidates absent from current rules;
critical literature review for each new candidate;
proposed validation experiments.
Later extensions
graph neural networks;
multimodal embeddings;
knowledge-graph link prediction;
target–mechanism prediction;
target–response prediction;
target–modality prediction.
v1.0.0 — Multitumor Target-Intelligence Platform
Objective

Generalize TargetIntel-IO beyond melanoma and anti-PD-1 resistance.

Scope
generic disease and treatment engine;
validated context-pack specification;
multiple tumor types;
multiple therapeutic classes;
context-specific resistance programs;
context-specific cell types and endpoints;
temporal evaluation;
external evaluation;
evidence-grounded conversational interface;
complete provenance and uncertainty reporting;
reproducible release and benchmarking framework.
Initial Development Priority

The first implementation priority is:

v0.2.0 — Common Evidence Layer and Literature Copilot

This version provides the best balance between:

scientific value;
engineering difficulty;
immediate visibility;
reproducibility;
usefulness for future integrations.

It will:

introduce an LLM in a constrained and useful role;
improve current hypothesis cards;
add real references;
identify contradictory evidence;
create the infrastructure required for DepMap, single-cell, spatial, and clinical data;
produce a demonstrable GitHub feature;
support manual and quantitative evaluation.
Initial MVP

The initial literature and evidence benchmark will focus on approximately 15 targets:

CTLA4
LAG3
TIGIT
B2M
JAK1
JAK2
TAP1
CSF1R
TREM2
TGFB1
TGFBR1
BRAF
NRAS
AXL
WNT5A

For each target, the MVP should:

Retrieve approximately 20–50 potentially relevant publications.
Rank publications by relevance.
Extract structured claims.
Preserve exact supporting text.
Preserve publication and document identifiers.
Separate supportive, contradictory, and limiting evidence.
Detect duplicates and shared evidence origins.
Generate a target evidence card.
Manually review a representative sample.
Measure extraction and citation accuracy.
Example output
B2M — Evidence Summary

Observed evidence
-----------------

[Clinical cohort]
Observation: ...
Source: PMID ...
Supporting text: ...
Cohort: ...
Validation status: citation verified

[Experimental]
Observation: ...
Source: PMID ...
Supporting text: ...
Model system: ...
Validation status: citation verified

Contradictory or limiting evidence
----------------------------------

Observation: ...
Source: PMID ...
Limitation: ...

System interpretation
---------------------

Likely role:
Resistance biomarker

Direct target suitability:
Low

Evidence strength:
Moderate

Independent cohorts:
2

Main uncertainty:
The available evidence supports B2M loss as a resistance mechanism,
but does not establish B2M as a therapeutically actionable direct target.
Success Criteria for v0.2.0

The first milestone will be considered successful when an EvidenceItem can:

represent a scientific observation;
preserve its complete provenance;
distinguish observation from interpretation;
identify its publication, dataset, experiment, and cohort;
record derived-evidence relationships;
serialize and deserialize without information loss;
be rejected when required traceability is missing;
distinguish evidence records from independent evidence families;
support verified literature quotations;
integrate with future sources without changing its core contract;
coexist with the current deterministic ranking engine without changing baseline results.

The objective of v0.2.0 is not to create an autonomous scientist.

It is to create a reliable evidence substrate on which future retrieval, machine-learning, and reasoning systems can safely operate.
