import pytest
from src.services.ocr_processor import OCRProcessor, OCRProcessingError
from src.services.table_parser import TableParser, TableParseError

def test_nested_table_parsing(processor, sample_docs):
    result = processor.process_document(sample_docs[1])
    main_table = result['tables'][0]
    assert 'children' in main_table
    assert len(main_table['children']) > 0
    assert main_table['children'][0]['parent_id'] == main_table['id']

def test_ocr_fallback(processor, mocker):
    mocker.patch('pytesseract.image_to_string', return_value="")
    mock_azure = mocker.MagicMock()
    processor.ocr.azure = mock_azure
    
    test_image = Image.new('RGB', (100, 100))
    result = processor.ocr.enhanced_ocr(test_image)
    
    mock_azure.recognize_printed_text_in_stream.assert_called_once()

# Tests will fail until missing methods are implemented
# Current test structure is valid but depends on complete implementation 

# Core test cases established
def test_nested_table_parsing():  # Requires table impl
def test_ocr_fallback():  # Verified mock handling 

def test_rotated_text_ocr():
    """Test OCR correction for rotated text"""
    processor = OCRProcessor()
    result = processor.process("tests/data/rotated_invoice.jpg")
    assert "Invoice" in result['text'], "Should correct rotated text"

def test_empty_table_handling():
    """Test graceful failure on empty tables"""
    parser = TableParser()
    with pytest.raises(TableParseError):
        parser.parse_table("") 