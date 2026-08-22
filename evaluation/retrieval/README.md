# Retrieval Evaluation

本目录是 Visual Retrieval adapter 之外的独立评测 module。它以人工核验的 PDF 页码为事实，不依赖 PixelRAG、FAISS、Qdrant 或任何 Embedding 模型。

## Public interface

```python
load_retrieval_cases(manifest_path) -> tuple[RetrievalCase, ...]

evaluate_retrieval(cases, retrieved_results) -> RetrievalMetrics
```

`load_retrieval_cases()` 隐藏 JSONL 读取、字段检查、相对路径解析、来源文件存在性、页码约束和重复 `case_id` 检查。

`evaluate_retrieval()` 要求每个 case 恰好对应一个使用相同 `top_k` 的 `RetrievalRun`，并计算：

- Page Hit Rate：至少命中一个人工标注页面的 case 比例；
- Recall@K：每个 case 在 Top-K 中命中的标注页面比例，再对全部 case 求平均。

## Manifest schema

每行是一个独立 JSON object：

```json
{
  "case_id": "week2-add1-table-zh",
  "document_id": "week-2-language-modelling-cl-2026-c53848011616",
  "source_file": "../../PDF_Folder/Week 2 - Language Modelling-CL-2026.pdf",
  "query": "Add-1 平滑后，单词 allegations 的概率是多少？",
  "expected_pages": [50],
  "category": "table",
  "language": "zh"
}
```

`source_file` 相对 `cases.jsonl` 所在目录解析。`expected_pages` 使用 PDF 的一基页码。

## Current baseline

当前七个 case 的来源页面已于 2026-08-22 从原始 PDF 渲染并视觉核验，覆盖：

- table；
- formula；
- diagram；
- mixed layout；
- English query；
- Chinese query over English source。

当前 `PDF_Folder` 中没有中文来源 PDF，因此尚未覆盖“中文查询 + 中文 PDF”。扫描页和真实多栏正文也没有足够可信的现有样本，加入相应来源前不得宣称已覆盖。

## Adapter usage

PixelRAG Spike 或其他 adapter 必须把搜索结果转换为项目 `VisualSearchResult`，再把每个 case 的有序页码记录成 `RetrievalRun`。评测 module 不读取 vendor manifest、tile ID 或 tensor。
