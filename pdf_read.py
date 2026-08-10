from pathlib import Path
from paddleocr import PaddleOCR
import opendataloader_pdf
from dataclasses import asdict
import json
from OpenDataLoaderSchema import baseline_analyse
from combine_format import FormattedDocumentBuilder

# 文件存放 global Variable
PDF_Folder = Path(r"D:\Leetcode\PDF-summarize\PDF_Folder")
PDF_Output = Path(r"D:\Leetcode\PDF-summarize\PDF_Output")
RAW_OUTPUT_DIR = PDF_Output / "raw"
ANALYSIS_OUTPUT_DIR = PDF_Output / "analysis"       # 分析报告存放folder

BASELINE_ANALYSIS_FILE = ANALYSIS_OUTPUT_DIR / "baseline_analysis.json"    # baseline analyse 分析文件，基于schema判断该pdf是否需要ocr介入
OCR_RESULT_FILE = ANALYSIS_OUTPUT_DIR / "ocr_results.json"      # ocr 识别page后的输出
CANONICAL_DOCUMENT_FILE = ANALYSIS_OUTPUT_DIR / "canonical_documents.json"  


def main():
    # step 1: 使用openDataLoader做baseline
    OpenDataLoader()   

    # step 2: 对baseline 做分析，（基于 schema）得到分析报告
    ANALYSIS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)  # 自动创建if not exist
    baseline_report  = baseline_analyse(
        output_dir=RAW_OUTPUT_DIR,
        analysis_file=BASELINE_ANALYSIS_FILE,   
    )

    # ocr 的结果，用于储存ocr 识别内容
    ocr_report = {
        "source": str(BASELINE_ANALYSIS_FILE),
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
                image_path = RAW_OUTPUT_DIR / image_source

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

    OCR_RESULT_FILE.write_text(         #  构造ocr 最终结果
        json.dumps(ocr_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    
    # canonical 构造: 
    """
        raw OpenDataLoader JSON / 
        baseline_analysis.json /
        ocr_results.json 
    """
    canonical_documents = FormattedDocumentBuilder(
        output_dir=RAW_OUTPUT_DIR,
        baseline_file=BASELINE_ANALYSIS_FILE,
        ocr_file=OCR_RESULT_FILE,
    ).build()

    CANONICAL_DOCUMENT_FILE.write_text(
        json.dumps(
            [asdict(document) for document in canonical_documents],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"OCR result saved to: {OCR_RESULT_FILE}")
    print(f"Canonical documents saved to: {CANONICAL_DOCUMENT_FILE}")


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


def OpenDataLoader():
    if not PDF_Folder.exists():
        raise FileNotFoundError(f"PDF folder does not exist: {PDF_Folder}")

    RAW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    opendataloader_pdf.convert(
        input_path=PDF_Folder,
        output_dir=RAW_OUTPUT_DIR,
        format="markdown,json",
    )

    print(f"Conversion completed; saved to: {RAW_OUTPUT_DIR}")


if __name__ == "__main__":
    main()
