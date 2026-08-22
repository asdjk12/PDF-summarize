import importlib


def test_pdf_pipeline_can_be_imported_without_optional_paddleocr():
    module = importlib.import_module("pdf_read")

    assert callable(module.main)
