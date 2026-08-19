from pathlib import Path
from paddleocr import PaddleOCR
import opendataloader_pdf
from dataclasses import asdict, dataclass
import json
from OpenDataLoaderSchema import baseline_analyse
from combine_format import FormattedDocumentBuilder
from chunking import ChunkingConfig, chunk_document

PROJECT_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True, slots=True)
class PipelinePaths:
    """All filesystem boundaries for one isolated PDF conversion run."""

    input_dir: Path
    output_dir: Path

    @property
    def raw_output_dir(self) -> Path:
        return self.output_dir / "raw"

    @property
    def analysis_output_dir(self) -> Path:
        return self.output_dir / "analysis"

    @property
    def baseline_analysis_file(self) -> Path:
        return self.analysis_output_dir / "baseline_analysis.json"

    @property
    def ocr_result_file(self) -> Path:
        return self.analysis_output_dir / "ocr_results.json"

    @property
    def canonical_document_file(self) -> Path:
        return self.analysis_output_dir / "canonical_documents.json"

    @property
    def chunks_file(self) -> Path:
        return self.analysis_output_dir / "chunks.json"


DEFAULT_PATHS = PipelinePaths(
    input_dir=PROJECT_ROOT / "PDF_Folder",
    output_dir=PROJECT_ROOT / "PDF_Output",
)

# 保留原有常量，避免破坏现有脚本和测试。
PDF_Folder = DEFAULT_PATHS.input_dir
PDF_Output = DEFAULT_PATHS.output_dir
RAW_OUTPUT_DIR = DEFAULT_PATHS.raw_output_dir
ANALYSIS_OUTPUT_DIR = DEFAULT_PATHS.analysis_output_dir
BASELINE_ANALYSIS_FILE = DEFAULT_PATHS.baseline_analysis_file
OCR_RESULT_FILE = DEFAULT_PATHS.ocr_result_file
CANONICAL_DOCUMENT_FILE = DEFAULT_PATHS.canonical_document_file
CHUNKS_FILE = DEFAULT_PATHS.chunks_file


def main(paths: PipelinePaths | None = None):
    selected_paths = paths or DEFAULT_PATHS

    # step 1: 使用openDataLoader做baseline
    OpenDataLoader(selected_paths)

    # step 2: 对baseline 做分析，（基于 schema）得到分析报告
    selected_paths.analysis_output_dir.mkdir(parents=True, exist_ok=True)
    baseline_report  = baseline_analyse(
        output_dir=selected_paths.raw_output_dir,
        analysis_file=selected_paths.baseline_analysis_file,
    )

    # ocr 的结果，用于储存ocr 识别内容
    ocr_report = {
        "source": str(selected_paths.baseline_analysis_file),
        "document": {}
    }
    
    ocr = None

    for document_name, document in baseline_report["documents"].items():
        needs_ocr_pages  = document["needs_ocr_pages"]     # 需要OCR page

        if not needs_ocr_pages:     # 无ocr condition
            continue
        
        # ocr 初始化
        if ocr is None:
            ocr = PaddleOCR(
                lang="ch",
                device="cpu",
                use_doc_orientation_classify=True,
                use_doc_unwarping=False,
                use_textline_orientation=True,
            )

        document_ocr_pages = {}

        for page_number in needs_ocr_pages:     # ocr page
            page_report = document["pages"][str(page_number)]   
            image_sources = page_report["image_sources"]        # 识别到的图片集

            page_ocr_items = []

            for image_source in image_sources:
                image_path = selected_paths.raw_output_dir / image_source

                if not image_path.exists():
                    # condition 1: 无图片
                    page_ocr_items.append(
                        {
                            "image": image_source,
                            "error": f"Image not found: {image_path}",
                        }
                    )
                    continue
                
                # condition 1: 有图片
                page_ocr_items.append(
                    {
                        "image": image_source,
                        "lines": OCR(ocr, image_path),
                    }
                )

            document_ocr_pages[str(page_number)] = {
                "reasons": page_report["reasons"],
                "text_chars_before_ocr": page_report["text_chars"],
                "image_count": page_report["image_count"],
                "images": page_ocr_items,
            }

        ocr_report["document"][document_name] = {
            "source_pdf": document["source_pdf"],
            "source_json": document["source_json"],
            "needs_ocr_pages": needs_ocr_pages,
            "pages": document_ocr_pages,
        }

    selected_paths.ocr_result_file.write_text(
        json.dumps(ocr_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    
    canonical_documents, chunks = build_derived_artifacts(selected_paths)

    print(f"OCR result saved to: {selected_paths.ocr_result_file}")
    print(
        "Canonical documents saved to: "
        f"{selected_paths.canonical_document_file}"
    )
    print(f"Chunks saved to: {selected_paths.chunks_file}")

    return canonical_documents, chunks


def build_derived_artifacts(paths: PipelinePaths | None = None):
    """Rebuild canonical documents and chunks from existing parser/OCR data."""

    selected_paths = paths or DEFAULT_PATHS

    canonical_documents = FormattedDocumentBuilder(
        output_dir=selected_paths.raw_output_dir,
        baseline_file=selected_paths.baseline_analysis_file,
        ocr_file=selected_paths.ocr_result_file,
        source_dir=selected_paths.input_dir,
    ).build()

    chunks = tuple(
        chunk
        for document in canonical_documents
        for chunk in chunk_document(
            document,
            ChunkingConfig(max_characters=4_000, max_pages=4),
        )
    )

    selected_paths.canonical_document_file.write_text(
        json.dumps(
            [asdict(document) for document in canonical_documents],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    selected_paths.chunks_file.write_text(
        json.dumps(
            [asdict(chunk) for chunk in chunks],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return canonical_documents, chunks


def OCR(ocr, image_path: Path):
    # 运行ocr，行行读取
    results = ocr.predict(str(image_path))
    lines = []

    for page_result in results:
        data = page_result.json["res"]
        texts = data.get("rec_texts", [])
        scores = data.get("rec_scores", [])

        for index, text in enumerate(texts):
            item = {"text": text}

            if index < len(scores):
                item["score"] = float(scores[index])

            lines.append(item)

    return lines


def OpenDataLoader(paths: PipelinePaths | None = None):
    selected_paths = paths or DEFAULT_PATHS

    if not selected_paths.input_dir.exists():
        raise FileNotFoundError(
            f"PDF folder does not exist: {selected_paths.input_dir}"
        )

    selected_paths.raw_output_dir.mkdir(parents=True, exist_ok=True)

    opendataloader_pdf.convert(
        input_path=selected_paths.input_dir,
        output_dir=selected_paths.raw_output_dir,
        format="markdown,json",
    )

    print(f"Conversion completed; saved to: {selected_paths.raw_output_dir}")


if __name__ == "__main__":
    main()
