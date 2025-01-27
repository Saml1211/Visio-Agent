import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.knowledge_testing_service import (
    KnowledgeTestingService,
    TestCase,
    TestSuite,
    TestResult,
    TestReport,
    TestCaseType,
    TestStatus,
    TestingError
)

@pytest.fixture
def test_data_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test data directories
        test_dir = Path(temp_dir)
        (test_dir / "test_cases").mkdir()
        (test_dir / "test_suites").mkdir()
        yield test_dir

@pytest.fixture
def mock_ai_service():
    return MagicMock()

@pytest.fixture
def mock_rag_service():
    mock = AsyncMock()
    mock.query_memory = AsyncMock(return_value=[])
    return mock

@pytest.fixture
async def testing_service(test_data_dir):
    service = KnowledgeTestingService(test_data_dir)
    await service.initialize()
    return service

@pytest.mark.asyncio
async def test_create_test_case(testing_service):
    # Create test case
    test_case = await testing_service.create_test_case(
        type=TestCaseType.DOCUMENT_PROCESSING,
        description="Test document processing",
        input_data={"document_path": "test.txt"},
        expected_output={"processed_content": "test content"},
        metadata={"priority": "high"},
        validation_rules={"required_fields": ["processed_content"]}
    )
    
    # Verify test case
    assert test_case.id.startswith("test_")
    assert test_case.type == TestCaseType.DOCUMENT_PROCESSING
    assert test_case.description == "Test document processing"
    assert test_case.input_data == {"document_path": "test.txt"}
    assert test_case.expected_output == {"processed_content": "test content"}
    assert test_case.metadata == {"priority": "high"}
    assert test_case.validation_rules == {"required_fields": ["processed_content"]}
    assert isinstance(test_case.created_at, datetime)
    assert isinstance(test_case.updated_at, datetime)
    
    # Verify file was created
    file_path = testing_service.test_data_dir / "test_cases" / f"{test_case.id}.json"
    assert file_path.exists()
    
    # Verify can retrieve test case
    retrieved = testing_service.get_test_case(test_case.id)
    assert retrieved.id == test_case.id
    assert retrieved.type == test_case.type
    assert retrieved.description == test_case.description

@pytest.mark.asyncio
async def test_create_test_suite(testing_service):
    # Create test cases
    test_case_1 = await testing_service.create_test_case(
        type=TestCaseType.DOCUMENT_PROCESSING,
        description="Test 1",
        input_data={"document_path": "test1.txt"},
        expected_output={"processed_content": "content 1"}
    )
    
    test_case_2 = await testing_service.create_test_case(
        type=TestCaseType.DIAGRAM_GENERATION,
        description="Test 2", 
        input_data={"input_text": "test", "template_name": "basic"},
        expected_output={"diagram_path": "test.vsdx"}
    )
    
    # Create test suite
    test_suite = await testing_service.create_test_suite(
        name="Test Suite 1",
        description="First test suite",
        test_case_ids=[test_case_1.id, test_case_2.id],
        metadata={"owner": "test"}
    )
    
    # Verify test suite
    assert test_suite.id.startswith("suite_")
    assert test_suite.name == "Test Suite 1"
    assert test_suite.description == "First test suite"
    assert len(test_suite.test_cases) == 2
    assert test_suite.test_cases[0].id == test_case_1.id
    assert test_suite.test_cases[1].id == test_case_2.id
    assert test_suite.metadata == {"owner": "test"}
    
    # Verify file was created
    file_path = testing_service.test_data_dir / "test_suites" / f"{test_suite.id}.json"
    assert file_path.exists()
    
    # Verify can retrieve test suite
    retrieved = testing_service.get_test_suite(test_suite.id)
    assert retrieved.id == test_suite.id
    assert retrieved.name == test_suite.name
    assert len(retrieved.test_cases) == 2

@pytest.mark.asyncio
async def test_update_test_case(testing_service):
    # Create test case
    test_case = await testing_service.create_test_case(
        type=TestCaseType.DOCUMENT_PROCESSING,
        description="Original description",
        input_data={"document_path": "test.txt"},
        expected_output={"processed_content": "content"}
    )
    
    # Update test case
    updated = await testing_service.update_test_case(
        test_id=test_case.id,
        description="Updated description",
        input_data={"document_path": "new.txt"},
        metadata={"status": "updated"}
    )
    
    # Verify updates
    assert updated.id == test_case.id
    assert updated.description == "Updated description"
    assert updated.input_data == {"document_path": "new.txt"}
    assert updated.metadata == {"status": "updated"}
    assert updated.updated_at > test_case.updated_at
    
    # Verify file was updated
    file_path = testing_service.test_data_dir / "test_cases" / f"{test_case.id}.json"
    with open(file_path) as f:
        data = json.load(f)
        assert data["description"] == "Updated description"

@pytest.mark.asyncio
async def test_delete_test_case(testing_service):
    # Create test case
    test_case = await testing_service.create_test_case(
        type=TestCaseType.DOCUMENT_PROCESSING,
        description="Test case",
        input_data={"document_path": "test.txt"},
        expected_output={"processed_content": "content"}
    )
    
    # Create test suite with the test case
    test_suite = await testing_service.create_test_suite(
        name="Test Suite",
        description="Test suite",
        test_case_ids=[test_case.id]
    )
    
    # Delete test case
    await testing_service.delete_test_case(test_case.id)
    
    # Verify test case was deleted
    with pytest.raises(TestingError):
        testing_service.get_test_case(test_case.id)
    
    # Verify file was deleted
    file_path = testing_service.test_data_dir / "test_cases" / f"{test_case.id}.json"
    assert not file_path.exists()
    
    # Verify test case was removed from suite
    updated_suite = testing_service.get_test_suite(test_suite.id)
    assert len(updated_suite.test_cases) == 0

@pytest.mark.asyncio
async def test_execute_document_test(testing_service, mock_ai_service, mock_rag_service):
    # Create document test case
    test_case = await testing_service.create_test_case(
        type=TestCaseType.DOCUMENT_PROCESSING,
        description="Document test",
        input_data={"document_path": "test.txt"},
        expected_output={
            "processed_content": "test content",
            "metadata": {"type": "text"}
        }
    )
    
    # Mock document processing result
    with patch("src.services.document_processing_service.DocumentProcessingService") as mock_doc_service:
        mock_instance = mock_doc_service.return_value
        mock_instance.process_document = AsyncMock(return_value=MagicMock(
            content="test content",
            metadata={"type": "text"}
        ))
        
        # Execute test
        result = await testing_service.execute_test_case(
            test_case.id,
            mock_ai_service,
            mock_rag_service
        )
        
        # Verify result
        assert result.test_case_id == test_case.id
        assert result.status == TestStatus.PASSED
        assert result.actual_output == {
            "processed_content": "test content",
            "metadata": {"type": "text"},
            "error": None
        }
        assert result.execution_time_ms > 0

@pytest.mark.asyncio
async def test_execute_diagram_test(testing_service, mock_ai_service, mock_rag_service):
    # Create diagram test case
    test_case = await testing_service.create_test_case(
        type=TestCaseType.DIAGRAM_GENERATION,
        description="Diagram test",
        input_data={
            "input_text": "test diagram",
            "template_name": "basic"
        },
        expected_output={
            "diagram_path": "output/test.vsdx",
            "pdf_path": "output/test.pdf"
        }
    )
    
    # Mock diagram generation result
    with patch("src.services.visio_generation_service.VisioGenerationService") as mock_visio_service:
        mock_instance = mock_visio_service.return_value
        mock_instance.generate_diagram = AsyncMock(return_value=MagicMock(
            diagram_path=Path("output/test.vsdx"),
            pdf_path=Path("output/test.pdf"),
            metadata={"type": "basic"}
        ))
        
        # Execute test
        result = await testing_service.execute_test_case(
            test_case.id,
            mock_ai_service,
            mock_rag_service
        )
        
        # Verify result
        assert result.test_case_id == test_case.id
        assert result.status == TestStatus.PASSED
        assert result.actual_output == {
            "diagram_path": "output/test.vsdx",
            "pdf_path": "output/test.pdf",
            "metadata": {"type": "basic"},
            "error": None
        }

@pytest.mark.asyncio
async def test_execute_query_test(testing_service, mock_ai_service, mock_rag_service):
    # Create query test case
    test_case = await testing_service.create_test_case(
        type=TestCaseType.KNOWLEDGE_QUERY,
        description="Query test",
        input_data={
            "query": "test query",
            "max_results": 2
        },
        expected_output={
            "results": [
                {"content": "result 1"},
                {"content": "result 2"}
            ]
        }
    )
    
    # Mock query results
    mock_rag_service.query_memory.return_value = [
        MagicMock(to_dict=lambda: {"content": "result 1"}),
        MagicMock(to_dict=lambda: {"content": "result 2"})
    ]
    
    # Execute test
    result = await testing_service.execute_test_case(
        test_case.id,
        mock_ai_service,
        mock_rag_service
    )
    
    # Verify result
    assert result.test_case_id == test_case.id
    assert result.status == TestStatus.PASSED
    assert result.actual_output == {
        "results": [
            {"content": "result 1"},
            {"content": "result 2"}
        ],
        "error": None
    }
    
    # Verify RAG service was called correctly
    mock_rag_service.query_memory.assert_called_once_with(
        query="test query",
        ai_service=mock_ai_service,
        max_results=2
    )

@pytest.mark.asyncio
async def test_execute_test_suite(testing_service, mock_ai_service, mock_rag_service):
    # Create test cases
    test_case_1 = await testing_service.create_test_case(
        type=TestCaseType.DOCUMENT_PROCESSING,
        description="Document test",
        input_data={"document_path": "test1.txt"},
        expected_output={"processed_content": "content 1"}
    )
    
    test_case_2 = await testing_service.create_test_case(
        type=TestCaseType.KNOWLEDGE_QUERY,
        description="Query test",
        input_data={"query": "test"},
        expected_output={"results": []}
    )
    
    # Create test suite
    test_suite = await testing_service.create_test_suite(
        name="Test Suite",
        description="Test suite",
        test_case_ids=[test_case_1.id, test_case_2.id]
    )
    
    # Mock service calls
    with patch("src.services.document_processing_service.DocumentProcessingService") as mock_doc_service:
        mock_doc_instance = mock_doc_service.return_value
        mock_doc_instance.process_document = AsyncMock(return_value=MagicMock(
            content="content 1",
            metadata={}
        ))
        
        # Execute suite
        report = await testing_service.execute_test_suite(
            test_suite.id,
            mock_ai_service,
            mock_rag_service
        )
        
        # Verify report
        assert report.suite_id == test_suite.id
        assert report.total_tests == 2
        assert report.passed_tests == 2
        assert report.failed_tests == 0
        assert report.error_tests == 0
        assert len(report.results) == 2
        assert report.total_time_ms > 0
        
        # Verify parallel execution
        parallel_report = await testing_service.execute_test_suite(
            test_suite.id,
            mock_ai_service,
            mock_rag_service,
            parallel=True
        )
        assert parallel_report.total_tests == 2
        assert parallel_report.passed_tests == 2

@pytest.mark.asyncio
async def test_validation_rules(testing_service, mock_ai_service, mock_rag_service):
    # Create test case with validation rules
    test_case = await testing_service.create_test_case(
        type=TestCaseType.DOCUMENT_PROCESSING,
        description="Validation test",
        input_data={"document_path": "test.txt"},
        expected_output={
            "processed_content": "content",
            "word_count": 100
        },
        validation_rules={
            "required_fields": ["processed_content", "word_count"],
            "field_types": {
                "processed_content": "str",
                "word_count": "int"
            },
            "value_ranges": {
                "word_count": {"min": 0, "max": 1000}
            }
        }
    )
    
    # Mock document processing with invalid output
    with patch("src.services.document_processing_service.DocumentProcessingService") as mock_doc_service:
        mock_instance = mock_doc_service.return_value
        mock_instance.process_document = AsyncMock(return_value=MagicMock(
            content="content",
            metadata={"word_count": "invalid"}  # Wrong type
        ))
        
        # Execute test
        result = await testing_service.execute_test_case(
            test_case.id,
            mock_ai_service,
            mock_rag_service
        )
        
        # Verify validation failure
        assert result.status == TestStatus.FAILED
        assert "type_errors" in result.validation_details
        assert any("word_count" in err for err in result.validation_details["type_errors"])

@pytest.mark.asyncio
async def test_error_handling(testing_service, mock_ai_service, mock_rag_service):
    # Test invalid test case ID
    with pytest.raises(TestingError, match="Test case not found"):
        await testing_service.execute_test_case(
            "invalid_id",
            mock_ai_service,
            mock_rag_service
        )
    
    # Test invalid test suite ID
    with pytest.raises(TestingError, match="Test suite not found"):
        await testing_service.execute_test_suite(
            "invalid_id",
            mock_ai_service,
            mock_rag_service
        )
    
    # Test invalid test case type
    test_case = await testing_service.create_test_case(
        type=TestCaseType.DOCUMENT_PROCESSING,
        description="Error test",
        input_data={},  # Missing required field
        expected_output={}
    )
    
    result = await testing_service.execute_test_case(
        test_case.id,
        mock_ai_service,
        mock_rag_service
    )
    
    assert result.status == TestStatus.ERROR
    assert "error" in result.validation_details 