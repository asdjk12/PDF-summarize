# PixelRAG Stage 1 Spike

此目录是项目拥有的 PixelRAG 集成实验，不包含上游源码。上游依赖固定为
`pixelrag[index,pdf,serve]==0.4.0`，通过 CLI 构建索引、HTTP seam 查询，所有
vendor schema 都在 `client.py` 内转换为项目领域类型。

当前配置从项目本地的
`../model/modelscope/hub/models/Qwen/Qwen3-VL-Embedding-2B` 加载视觉嵌入模型，
不在索引过程中访问 Hugging Face。

## 模块边界

- `client.py`：隐藏 PixelRAG `/search` JSON、路径和零基 `tile_index`；对外只返回
  `VisualSearchResult`。
- `evaluation_runner.py`：通过项目 `VisualRetrieval` seam 运行标准用例并计算
  Page Hit Rate 与 Recall@K。
- `run_evaluation.py`：薄命令入口，不包含检索或评分规则。
- `pixelrag.yaml`：仅配置三份测试 PDF、模型和可重建索引目录。
- `work/`、`.venv/`、`reports/`：本地运行产物，不进入 Git。

该 Spike 不属于生产 Infrastructure Adapter。只有真实评测达到后续确定的采用门槛，
才会在 `pdf_knowledge_agent/infrastructure/` 中实现生产 Adapter。

## 安装

要求 Python 3.12。PDF 渲染还需要把 Poppler 的 `pdftoppm` 加入 `PATH`。本项目
已在 Windows、RTX 4080 Laptop GPU、CUDA 12.6 对三份 PDF 完成原生索引验证；
这只是当前机器的实测结论，不代表所有 Windows/CUDA 组合都受上游保证。

```powershell
uv venv .venv --python 3.12
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
uv pip install --python .venv\Scripts\python.exe `
  torch==2.12.0 torchvision==0.27.0 `
  --index-url https://download.pytorch.org/whl/cu126
```

## 构建与启动

命令必须从本目录执行，使 `pixelrag.yaml` 中的相对路径保持稳定：

```powershell
.venv\Scripts\pixelrag.exe index build --config pixelrag.yaml
.venv\Scripts\pixelrag.exe serve `
  --index-dir .\work\index `
  --tiles-dir .\work\index\tiles `
  --articles-json .\work\index\articles.json `
  --model ..\model\modelscope\hub\models\Qwen\Qwen3-VL-Embedding-2B `
  --device cuda `
  --port 30001
```

PixelRAG 0.4.0 在当前环境中不能仅靠 `--index-dir` 正确推导另外两个资源路径，
所以启动命令显式传入 `tiles` 与 `articles.json`。该版本还会因日志格式缺少
`req` 字段输出 `KeyError: 'req'`；已验证该日志错误不改变 `/search` 的 200 响应，
集成层不修改 `.venv` 中的第三方源码。

## 评测

在仓库根目录执行：

```powershell
$env:PIXELRAG_TEST_ENDPOINT = "http://127.0.0.1:30001"
python -m pytest PixelRAG\tests -q
python -m PixelRAG.run_evaluation --top-k 5 --output PixelRAG\reports\top5.json
```

`tile_index + 1` 仅适用于 PixelRAG 0.4.0 的完整 PDF 渲染：该版本把每个 PDF
页面保存为一个零基 tile。若升级依赖，必须先重新运行映射契约测试。

## 当前验证结果

- 索引输入：Week 2（74 页）、Week 3（74 页）、Week 4（118 页），共 266 页。
- 嵌入输出：266 个 2048 维向量，FAISS 索引构建成功。
- 真实 HTTP 契约测试：5 项全部通过。
- 严格单文档 scope 的 7 条标准用例：Page Hit Rate = 1.0，Recall@5 = 1.0。

`reports/` 是可重建的本地证据，不作为源码提交。评测代码会按每条 case 的
`document_id` 过滤 vendor 候选，避免相同页码跨 PDF 造成假命中。
