PDF Knowledge Agent — Project Vision

Status: Product Vision
Updated: 2026-08-20

1. Project Vision

The goal of this project is to build a personal knowledge agent that can reliably understand, summarize, retrieve, compare, and answer questions from user-provided documents.

The system begins with PDF as the primary knowledge source and is designed to expand toward web pages, images, audio, video, and local knowledge folders.

The core product experience is:

User provides knowledge sources
        ↓
System processes and indexes the content
        ↓
User receives a complete static summary
        ↓
User asks questions dynamically
        ↓
System retrieves relevant evidence
        ↓
Agent produces grounded answers with citations
        ↓
User continues multi-turn knowledge tasks

The product should always preserve traceability back to the original source.

2. PDF Content Reading

PDF documents are treated as visual-first knowledge sources.

Each PDF is processed at page level. Pages are rendered into images and stored as stable knowledge units with document identity, page identity, page number, and source location.

The system should be able to read:

native-text PDFs;

scanned PDFs;

tables;

charts;

figures;

formulas;

multi-column layouts;

mixed text-image pages;

complex visual layouts.

The primary PDF reading flow is:

PDF
 ↓
Page Rendering
 ↓
Page Image
 ↓
Visual Representation
 ↓
Visual Embedding
 ↓
Knowledge Index

Native text parsing, OCR, and structural extraction remain optional auxiliary capabilities.

They can be used when useful for:

keyword retrieval;

exact number matching;

text-heavy summarization;

metadata extraction;

document structure recovery;

validation;

fallback processing.

The system should not depend on OCR success before a PDF can enter the knowledge base.

Every page should remain traceable to its original document and page number.

3. Canonical Knowledge

The system should maintain a unified knowledge representation for every source.

A document is not represented only as extracted text.

A document can contain:

Document
├─ Metadata
├─ Pages
│  ├─ Page Image
│  ├─ Page Number
│  ├─ Source Locator
│  ├─ Visual Embedding Reference
│  ├─ Optional Text
│  └─ Optional Structure Metadata
├─ Summary Artifacts
└─ Processing State

The canonical knowledge layer is the stable source of document identity and source traceability.

Search indexes, embeddings, caches, and retrieval databases are derived data and must be rebuildable.

4. Static Summary

Static summary is a full-document understanding capability.

Its purpose is to answer:

What does this document or document set contain?

Static summary must cover the selected source scope instead of retrieving only a few relevant pages.

The summary pipeline should process long documents hierarchically.

Example:

Pages
 ↓
Page Groups
 ↓
Local Summaries
 ↓
Section Summaries
 ↓
Document Summary
 ↓
Multi-document Summary

The summary system should preserve source references during every aggregation stage.

A final summary should support:

section-level citations;

page-level citations;

multi-document source attribution;

summary artifact versioning;

regeneration after source updates.

Static summary should support both:

Single Document Summary

and:

Multiple Document Summary

For large document sets, the system should summarize documents independently first and then perform higher-level aggregation.

5. Dynamic Query

Dynamic query is the retrieval-based knowledge interaction path.

Its purpose is to answer:

How do the selected documents answer this specific question?

The main flow is:

User Query
 ↓
Source Scope Resolution
 ↓
Query Embedding
 ↓
Visual Retrieval
 ↓
Relevant Pages
 ↓
Optional Text Retrieval
 ↓
Evidence Fusion
 ↓
Rerank
 ↓
Reader Model
 ↓
Grounded Answer
 ↓
Source Citation

The system should retrieve only a small number of relevant pages from a potentially very large knowledge base.

This allows the knowledge base to scale without sending entire documents into the model context.

Dynamic retrieval should support:

single-document queries;

multi-document queries;

visual retrieval;

optional keyword retrieval;

optional text embedding retrieval;

evidence reranking;

source filtering;

document comparison;

evidence sufficiency detection.

All retrieved information must be converted into a unified Evidence format before answer generation.

6. Evidence and Grounded Answer

Evidence is the boundary between retrieval and answer generation.

Evidence can come from:

Visual Retrieval
Text Retrieval
Keyword Search
Static Summary Artifact
Future Audio Retrieval
Future Video Retrieval

Each evidence item should contain:

Evidence
├─ Evidence ID
├─ Document ID
├─ Source Locator
├─ Representation Type
├─ Retrieval Score
├─ Page Image Reference
└─ Optional Text

The grounded answer module receives only:

User Query
+
Evidence

It should then:

Check Evidence Sufficiency
 ↓
Read Relevant Evidence
 ↓
Generate Answer
 ↓
Map Claims to Sources
 ↓
Validate Grounding
 ↓
Return Answer with Citations

If the available evidence is insufficient, the system should explicitly report insufficient evidence.

7. Agent Architecture

DeepSeek Harness is the Agent Runtime and control plane of the system.

The Agent layer is responsible for:

interpreting user intent;

maintaining the current session;

selecting tools;

coordinating multi-step tasks;

deciding when to summarize, search, compare, or inspect;

combining tool results into final responses.

The Agent should not directly operate low-level infrastructure such as:

vector databases;

file system paths;

embedding models;

OCR engines;

rendering libraries;

SQL;

shell commands.

The Agent interacts with the knowledge system through narrow domain tools.

Primary tools include:

list_sources
inspect_source
summarize_sources
search_evidence
compare_sources
get_artifact

The Agent runtime flow is:

User
 ↓
DeepSeek Harness
 ↓
Session
 ↓
Prompt Assembly
 ↓
LLM
 ↓
Tool Call
 ↓
Validation
 ↓
Scope Guard
 ↓
Knowledge Plugin
 ↓
Knowledge Domain
 ↓
Structured Tool Result
 ↓
LLM
 ↓
Final Response

The knowledge domain should remain independent from the Agent Runtime so that future runtime changes do not require rebuilding the document system.

8. Knowledge Plugin

The Knowledge Plugin is the interface between DeepSeek Harness and the document knowledge domain.

Its responsibilities are:

Tool Registration
Tool Schema
Request Validation
Scope Validation
Transport
Error Mapping
Structured Tool Result

The plugin should remain thin.

It should not implement:

Summary Algorithms
Retrieval Algorithms
Vector Search
Embedding
OCR
Rendering
Knowledge Storage

These capabilities belong to the knowledge domain.

9. Knowledge Repository

The Knowledge Repository is the main domain access layer.

It should provide stable access to:

Documents
Pages
Rendered Pages
Source Metadata
Processing State
Summary Artifacts
Evidence References
Indexes

The repository should hide storage implementation details from higher-level modules.

Possible storage technologies may include:

Local File System
Object Storage
SQLite
PostgreSQL
Document Database
Qdrant
FAISS

The application should access knowledge through repository interfaces rather than directly accessing storage backends.

10. Website

The website is the primary public product interface.

The website should allow users to:

Upload Documents
 ↓
View Processing Status
 ↓
Open Document Library
 ↓
Generate Static Summary
 ↓
Ask Questions
 ↓
View Grounded Answers
 ↓
Open Citations
 ↓
Compare Documents
 ↓
View Generated Artifacts

The website should support:

user authentication;

document upload;

document processing status;

source selection;

multi-document selection;

summary view;

chat interface;

citation viewer;

document page preview;

artifact history;

error states;

data deletion;

knowledge base management.

The browser can only access files explicitly selected or uploaded by the user.

It must not directly scan arbitrary folders on the user's device.

11. Local Knowledge Assistant

The local product extends the same knowledge system to explicitly authorized folders.

Users should be able to select one or more local folders as knowledge sources.

The system should then:

Folder Authorization
 ↓
File Discovery
 ↓
Document Processing
 ↓
Visual Indexing
 ↓
Knowledge Repository
 ↓
Local Agent

The local assistant should support incremental updates.

When a file changes:

File Change
 ↓
Content Hash
 ↓
Version Check
 ↓
Re-render Changed Document
 ↓
Rebuild Derived Representations
 ↓
Update Index
 ↓
Invalidate Dependent Artifacts

The local product should clearly distinguish:

Processing on Local Device

from:

Content Sent to External Models

Local deployment does not automatically imply fully offline operation.

12. Session Memory

Session memory belongs to the Agent Runtime.

It stores the current interaction state, including:

User Messages
Assistant Messages
Tool Calls
Tool Results
Current Source Scope
Current Task State
Current Artifact References

Session memory should not become a second document database.

Document facts remain in the knowledge repository.

13. Long-Term User Memory

Long-term memory stores a small amount of user-level information that is useful across sessions.

Examples include:

Preferred Summary Style
Preferred Response Length
Preferred Workflow
Stable User Choices

Long-term memory should be:

explainable;

removable;

scoped;

versioned where necessary;

optional.

It should not store:

Full PDF Content
Full Page Images
Full Conversation History
Document Knowledge

14. Source Scope and Permissions

Every knowledge task operates inside an explicit source scope.

Example:

source_scope = [
    "doc_001",
    "doc_014",
    "doc_091"
]

Before any domain operation:

Tool Call
 ↓
Schema Validation
 ↓
User Authorization
 ↓
Source Scope Validation
 ↓
Repository Validation
 ↓
Execution

The model must never be allowed to expand its own permissions.

The model should not be able to:

scan arbitrary paths;

read unauthorized documents;

delete user files;

modify source content;

execute arbitrary shell commands;

rebuild indexes without authorization;

modify canonical knowledge directly.

15. Large-Scale Knowledge Base

The architecture should support growth from:

Single PDF

to:

Thousands of PDFs

and eventually:

Millions of Pages

For example:

10,000 PDFs
×
100 pages
=
1,000,000 pages

The query path remains:

1,000,000 Indexed Pages
 ↓
Approximate Nearest Neighbor Search
 ↓
Top-K Pages
 ↓
Rerank
 ↓
Reader

The model never needs to load the entire knowledge base.

Scaling concerns therefore focus on:

Rendering Throughput
Embedding Throughput
Image Storage
Vector Storage
Index Performance
Metadata Filtering
Incremental Update
Reader Cost

16. Failure Handling

The system should degrade gracefully when individual capabilities fail.

Examples:

Visual Retrieval Failure
 ↓
Fallback Text Retrieval

Native Parse Failure
 ↓
Continue Visual Processing

OCR Failure
 ↓
Continue Visual Processing

Reader Failure
 ↓
Return Retrieved Evidence

Insufficient Evidence
 ↓
Return Explicit Limitation

The system should never fabricate document-grounded answers when source processing or retrieval fails.

17. Security

Untrusted documents should be isolated from the main runtime.

For public upload scenarios, document processing may run inside short-lived workers.

Worker responsibilities may include:

PDF Rendering
Native Parsing
OCR
Structure Processing

The worker should enforce:

CPU Limits
Memory Limits
Execution Timeout
Restricted File System
Restricted Network
No Long-Term Credentials

The Agent Runtime should separately enforce:

Tool Allowlist
Schema Validation
Source Scope
Permission Policy
Sandbox Rules

18. Model Roles

The system separates several model responsibilities.

Agent Model

Used for:

Intent Understanding
Tool Selection
Workflow Orchestration
Multi-turn Reasoning

Primary runtime:

DeepSeek Harness

Visual Embedding Model

Used for:

Page Image → Vector
Query → Vector

Reader Model

Used for:

Relevant Pages
+
Question
 ↓
Evidence Understanding
 ↓
Grounded Answer

The reader should be multimodal.

The Agent Model and Reader Model may be different models.

19. Evaluation

The project should maintain independent evaluation for retrieval, summary, and grounded answers.

Retrieval

Recall@K
MRR
nDCG
Page Hit Rate

Evaluation document types:

Plain Text
Scanned PDF
Table
Chart
Formula
Multi-column Layout
Mixed Layout

Static Summary

Coverage
Faithfulness
Citation Correctness
Cross-page Consistency
Cross-document Consistency

Grounded Answer

Evidence Relevance
Answer Faithfulness
Citation Precision
Citation Recall
Insufficient Evidence Detection

20. Multi-Modal Expansion

The long-term knowledge system should support:

PDF
Web
Image
Audio
Video

Each source should provide:

Knowledge Representation
+
Source Locator
+
Searchable Representation
+
Evidence

Source location differs by modality.

Examples:

PDF   → Page Number
Web   → URL / Screenshot Region
Image → Image ID / Region
Audio → Time Range
Video → Time Range / Frame Range

The same high-level capabilities should continue to work:

Summary
Search
Compare
Grounded Answer
Agent Tools

21. Final Product

The final system should allow a user to:

Provide Knowledge Sources
        ↓
Build a Personal Knowledge Base
        ↓
Receive Complete Static Summaries
        ↓
Ask Dynamic Questions
        ↓
Retrieve Relevant Visual Evidence
        ↓
Receive Grounded Answers
        ↓
Inspect Original Sources
        ↓
Continue Multi-step Tasks with an Agent
        ↓
Keep the Knowledge Base Updated

The core product principle is:

Every generated conclusion should remain connected to the original knowledge source.