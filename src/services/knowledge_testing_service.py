import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import aiofiles
import numpy as np
import asyncio

from .rag_memory_service import RAGMemoryService
from .ai_service_config import AIServiceManager
from .visio_generation_service import VisioGenerationService
from .exceptions import TestingError

logger = logging.getLogger(__name__)

class TestCaseType(str, Enum):
    """Types of test cases supported"""
    DATA_REFINEMENT = "data_refinement"
    COMPONENT_EXTRACTION = "component_extraction"
    LAYOUT_GENERATION = "layout_generation"
    VISIO_GENERATION = "visio_generation"

class TestStatus(str, Enum):
    """Status of test execution"""
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"

@dataclass
class TestCase:
    """Represents a knowledge test case"""
    id: str
    type: TestCaseType
    description: str
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class TestResult:
    """Represents the result of a test case execution"""
    test_case_id: str
    status: TestStatus
    actual_output: Optional[Dict[str, Any]] = None
    similarity_score: Optional[float] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

@dataclass
class TestSuite:
    """Represents a collection of test cases"""
    id: str
    name: str
    description: str
    test_cases: List[TestCase]
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class TestReport:
    """Represents a test execution report"""
    suite_id: str
    results: List[TestResult]
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    total_time: float
    average_similarity: float
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

@dataclass
class ValidationResult:
    """Represents the result of validating test output"""
    status: TestStatus
    details: Dict[str, Any]

class KnowledgeTestingService:
    """Service for testing and validating the system's knowledge base"""
    
    def __init__(
        self,
        rag_memory: RAGMemoryService,
        ai_service_manager: AIServiceManager,
        test_data_dir: Optional[Path] = None,
        similarity_threshold: float = 0.8
    ):
        """Initialize the knowledge testing service
        
        Args:
            rag_memory: RAG memory service for knowledge storage/retrieval
            ai_service_manager: Manager for AI services
            test_data_dir: Directory for storing test data
            similarity_threshold: Minimum similarity score for test validation
        """
        self.rag_memory = rag_memory
        self.ai_service_manager = ai_service_manager
        self.test_data_dir = test_data_dir or Path("data/test_data")
        self.similarity_threshold = similarity_threshold
        
        # Create necessary directories
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        (self.test_data_dir / "test_cases").mkdir(exist_ok=True)
        (self.test_data_dir / "test_suites").mkdir(exist_ok=True)
        (self.test_data_dir / "test_results").mkdir(exist_ok=True)
        
        # Initialize test case and suite storage
        self.test_cases: Dict[str, TestCase] = {}
        self.test_suites: Dict[str, TestSuite] = {}
        
        # Load existing test cases and suites
        self._load_test_data()
        
        logger.info(
            f"Initialized knowledge testing service with "
            f"{len(self.test_cases)} test cases and "
            f"{len(self.test_suites)} test suites"
        )
    
    def _load_test_data(self) -> None:
        """Load existing test cases and suites from disk"""
        try:
            # Load test cases
            test_cases_dir = self.test_data_dir / "test_cases"
            for file_path in test_cases_dir.glob("*.json"):
                with open(file_path) as f:
                    data = json.load(f)
                    test_case = TestCase(**data)
                    self.test_cases[test_case.id] = test_case
            
            # Load test suites
            test_suites_dir = self.test_data_dir / "test_suites"
            for file_path in test_suites_dir.glob("*.json"):
                with open(file_path) as f:
                    data = json.load(f)
                    # Convert test case IDs to actual TestCase objects
                    data["test_cases"] = [
                        self.test_cases[tc_id]
                        for tc_id in data["test_cases"]
                    ]
                    test_suite = TestSuite(**data)
                    self.test_suites[test_suite.id] = test_suite
            
        except Exception as e:
            logger.error(f"Error loading test data: {str(e)}")
            raise TestingError(f"Failed to load test data: {str(e)}")
    
    async def create_test_case(
        self,
        type: TestCaseType,
        description: str,
        input_data: Dict[str, Any],
        expected_output: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> TestCase:
        """Create a new test case
        
        Args:
            type: Type of test case
            description: Description of the test case
            input_data: Input data for the test
            expected_output: Expected output data
            metadata: Optional metadata
            validation_rules: Optional validation rules
            
        Returns:
            Created test case
        """
        try:
            # Generate unique ID
            test_id = f"test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Create test case
            test_case = TestCase(
                id=test_id,
                type=type,
                description=description,
                input_data=input_data,
                expected_output=expected_output,
                metadata=metadata,
                validation_rules=validation_rules,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save to disk
            file_path = self.test_data_dir / "test_cases" / f"{test_id}.json"
            async with aiofiles.open(file_path, "w") as f:
                await f.write(json.dumps(test_case.__dict__, default=str))
            
            # Add to memory
            self.test_cases[test_id] = test_case
            
            logger.info(f"Created test case: {test_id}")
            return test_case
            
        except Exception as e:
            logger.error(f"Error creating test case: {str(e)}")
            raise TestingError(f"Failed to create test case: {str(e)}")
    
    async def create_test_suite(
        self,
        name: str,
        description: str,
        test_case_ids: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> TestSuite:
        """Create a new test suite
        
        Args:
            name: Name of the test suite
            description: Description of the suite
            test_case_ids: List of test case IDs to include
            metadata: Optional metadata
            
        Returns:
            Created test suite
        """
        try:
            # Validate test case IDs
            test_cases = []
            for tc_id in test_case_ids:
                if tc_id not in self.test_cases:
                    raise TestingError(f"Test case not found: {tc_id}")
                test_cases.append(self.test_cases[tc_id])
            
            # Generate unique ID
            suite_id = f"suite_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Create test suite
            test_suite = TestSuite(
                id=suite_id,
                name=name,
                description=description,
                test_cases=test_cases,
                metadata=metadata,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save to disk
            file_path = self.test_data_dir / "test_suites" / f"{suite_id}.json"
            suite_data = test_suite.__dict__.copy()
            suite_data["test_cases"] = [tc.id for tc in test_cases]  # Store IDs only
            
            async with aiofiles.open(file_path, "w") as f:
                await f.write(json.dumps(suite_data, default=str))
            
            # Add to memory
            self.test_suites[suite_id] = test_suite
            
            logger.info(f"Created test suite: {suite_id}")
            return test_suite
            
        except Exception as e:
            logger.error(f"Error creating test suite: {str(e)}")
            raise TestingError(f"Failed to create test suite: {str(e)}")
    
    async def update_test_case(
        self,
        test_id: str,
        description: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        expected_output: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> TestCase:
        """Update an existing test case
        
        Args:
            test_id: ID of test case to update
            description: New description (optional)
            input_data: New input data (optional)
            expected_output: New expected output (optional)
            metadata: New metadata (optional)
            validation_rules: New validation rules (optional)
            
        Returns:
            Updated test case
        """
        try:
            if test_id not in self.test_cases:
                raise TestingError(f"Test case not found: {test_id}")
            
            test_case = self.test_cases[test_id]
            
            # Update fields if provided
            if description is not None:
                test_case.description = description
            if input_data is not None:
                test_case.input_data = input_data
            if expected_output is not None:
                test_case.expected_output = expected_output
            if metadata is not None:
                test_case.metadata = metadata
            if validation_rules is not None:
                test_case.validation_rules = validation_rules
            
            test_case.updated_at = datetime.utcnow()
            
            # Save to disk
            file_path = self.test_data_dir / "test_cases" / f"{test_id}.json"
            async with aiofiles.open(file_path, "w") as f:
                await f.write(json.dumps(test_case.__dict__, default=str))
            
            logger.info(f"Updated test case: {test_id}")
            return test_case
            
        except Exception as e:
            logger.error(f"Error updating test case: {str(e)}")
            raise TestingError(f"Failed to update test case: {str(e)}")
    
    async def update_test_suite(
        self,
        suite_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        test_case_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TestSuite:
        """Update an existing test suite
        
        Args:
            suite_id: ID of suite to update
            name: New name (optional)
            description: New description (optional)
            test_case_ids: New list of test case IDs (optional)
            metadata: New metadata (optional)
            
        Returns:
            Updated test suite
        """
        try:
            if suite_id not in self.test_suites:
                raise TestingError(f"Test suite not found: {suite_id}")
            
            test_suite = self.test_suites[suite_id]
            
            # Update fields if provided
            if name is not None:
                test_suite.name = name
            if description is not None:
                test_suite.description = description
            if test_case_ids is not None:
                # Validate test case IDs
                test_cases = []
                for tc_id in test_case_ids:
                    if tc_id not in self.test_cases:
                        raise TestingError(f"Test case not found: {tc_id}")
                    test_cases.append(self.test_cases[tc_id])
                test_suite.test_cases = test_cases
            if metadata is not None:
                test_suite.metadata = metadata
            
            test_suite.updated_at = datetime.utcnow()
            
            # Save to disk
            file_path = self.test_data_dir / "test_suites" / f"{suite_id}.json"
            suite_data = test_suite.__dict__.copy()
            suite_data["test_cases"] = [tc.id for tc in test_suite.test_cases]
            
            async with aiofiles.open(file_path, "w") as f:
                await f.write(json.dumps(suite_data, default=str))
            
            logger.info(f"Updated test suite: {suite_id}")
            return test_suite
            
        except Exception as e:
            logger.error(f"Error updating test suite: {str(e)}")
            raise TestingError(f"Failed to update test suite: {str(e)}")
    
    async def delete_test_case(self, test_id: str) -> None:
        """Delete a test case
        
        Args:
            test_id: ID of test case to delete
        """
        try:
            if test_id not in self.test_cases:
                raise TestingError(f"Test case not found: {test_id}")
            
            # Remove from test suites
            for suite in self.test_suites.values():
                suite.test_cases = [
                    tc for tc in suite.test_cases
                    if tc.id != test_id
                ]
            
            # Delete file
            file_path = self.test_data_dir / "test_cases" / f"{test_id}.json"
            file_path.unlink(missing_ok=True)
            
            # Remove from memory
            del self.test_cases[test_id]
            
            logger.info(f"Deleted test case: {test_id}")
            
        except Exception as e:
            logger.error(f"Error deleting test case: {str(e)}")
            raise TestingError(f"Failed to delete test case: {str(e)}")
    
    async def delete_test_suite(self, suite_id: str) -> None:
        """Delete a test suite
        
        Args:
            suite_id: ID of suite to delete
        """
        try:
            if suite_id not in self.test_suites:
                raise TestingError(f"Test suite not found: {suite_id}")
            
            # Delete file
            file_path = self.test_data_dir / "test_suites" / f"{suite_id}.json"
            file_path.unlink(missing_ok=True)
            
            # Remove from memory
            del self.test_suites[suite_id]
            
            logger.info(f"Deleted test suite: {suite_id}")
            
        except Exception as e:
            logger.error(f"Error deleting test suite: {str(e)}")
            raise TestingError(f"Failed to delete test suite: {str(e)}")
    
    def get_test_case(self, test_id: str) -> TestCase:
        """Get a test case by ID
        
        Args:
            test_id: ID of test case
            
        Returns:
            Test case
        """
        if test_id not in self.test_cases:
            raise TestingError(f"Test case not found: {test_id}")
        return self.test_cases[test_id]
    
    def get_test_suite(self, suite_id: str) -> TestSuite:
        """Get a test suite by ID
        
        Args:
            suite_id: ID of test suite
            
        Returns:
            Test suite
        """
        if suite_id not in self.test_suites:
            raise TestingError(f"Test suite not found: {suite_id}")
        return self.test_suites[suite_id]
    
    def list_test_cases(
        self,
        type: Optional[TestCaseType] = None,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> List[TestCase]:
        """List test cases with optional filtering
        
        Args:
            type: Filter by test case type
            metadata_filters: Filter by metadata fields
            
        Returns:
            List of matching test cases
        """
        test_cases = list(self.test_cases.values())
        
        if type:
            test_cases = [tc for tc in test_cases if tc.type == type]
        
        if metadata_filters:
            test_cases = [
                tc for tc in test_cases
                if all(
                    tc.metadata.get(k) == v
                    for k, v in metadata_filters.items()
                )
            ]
        
        return test_cases
    
    def list_test_suites(
        self,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> List[TestSuite]:
        """List test suites with optional filtering
        
        Args:
            metadata_filters: Filter by metadata fields
            
        Returns:
            List of matching test suites
        """
        test_suites = list(self.test_suites.values())
        
        if metadata_filters:
            test_suites = [
                ts for ts in test_suites
                if all(
                    ts.metadata.get(k) == v
                    for k, v in metadata_filters.items()
                )
            ]
        
        return test_suites
    
    async def execute_test_case(
        self,
        test_id: str,
        ai_service: AIServiceConfig,
        rag_service: RAGMemoryService
    ) -> TestResult:
        """Execute a single test case
        
        Args:
            test_id: ID of test case to execute
            ai_service: AI service to use for execution
            rag_service: RAG memory service to use
            
        Returns:
            Test result
        """
        try:
            test_case = self.get_test_case(test_id)
            start_time = datetime.utcnow()
            
            # Execute test based on type
            if test_case.type == TestCaseType.DOCUMENT_PROCESSING:
                actual_output = await self._execute_document_test(
                    test_case, ai_service, rag_service
                )
            elif test_case.type == TestCaseType.DIAGRAM_GENERATION:
                actual_output = await self._execute_diagram_test(
                    test_case, ai_service, rag_service
                )
            elif test_case.type == TestCaseType.KNOWLEDGE_QUERY:
                actual_output = await self._execute_query_test(
                    test_case, ai_service, rag_service
                )
            else:
                raise TestingError(f"Unsupported test type: {test_case.type}")
            
            # Validate output
            validation_result = await self._validate_test_output(
                test_case.expected_output,
                actual_output,
                test_case.validation_rules
            )
            
            # Create test result
            result = TestResult(
                test_case_id=test_id,
                status=validation_result.status,
                actual_output=actual_output,
                validation_details=validation_result.details,
                execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                executed_at=start_time
            )
            
            logger.info(
                f"Executed test case {test_id}: {result.status.name}"
                f" ({result.execution_time_ms}ms)"
            )
            return result
            
        except Exception as e:
            logger.error(f"Error executing test case {test_id}: {str(e)}")
            return TestResult(
                test_case_id=test_id,
                status=TestStatus.ERROR,
                actual_output={},
                validation_details={"error": str(e)},
                execution_time_ms=0,
                executed_at=datetime.utcnow()
            )
    
    async def execute_test_suite(
        self,
        suite_id: str,
        ai_service: AIServiceConfig,
        rag_service: RAGMemoryService,
        parallel: bool = False
    ) -> TestReport:
        """Execute a test suite
        
        Args:
            suite_id: ID of suite to execute
            ai_service: AI service to use
            rag_service: RAG memory service to use
            parallel: Whether to execute tests in parallel
            
        Returns:
            Test report
        """
        try:
            suite = self.get_test_suite(suite_id)
            start_time = datetime.utcnow()
            
            # Execute test cases
            if parallel:
                # Run tests in parallel
                tasks = [
                    self.execute_test_case(tc.id, ai_service, rag_service)
                    for tc in suite.test_cases
                ]
                results = await asyncio.gather(*tasks)
            else:
                # Run tests sequentially
                results = []
                for tc in suite.test_cases:
                    result = await self.execute_test_case(
                        tc.id, ai_service, rag_service
                    )
                    results.append(result)
            
            # Generate report
            report = TestReport(
                suite_id=suite_id,
                results=results,
                total_tests=len(results),
                passed_tests=sum(1 for r in results if r.status == TestStatus.PASSED),
                failed_tests=sum(1 for r in results if r.status == TestStatus.FAILED),
                error_tests=sum(1 for r in results if r.status == TestStatus.ERROR),
                total_time_ms=sum(r.execution_time_ms for r in results),
                executed_at=start_time
            )
            
            logger.info(
                f"Executed test suite {suite_id}:"
                f" {report.passed_tests}/{report.total_tests} passed"
                f" ({report.total_time_ms}ms)"
            )
            return report
            
        except Exception as e:
            logger.error(f"Error executing test suite {suite_id}: {str(e)}")
            raise TestingError(f"Failed to execute test suite: {str(e)}")
    
    async def _execute_document_test(
        self,
        test_case: TestCase,
        ai_service: AIServiceConfig,
        rag_service: RAGMemoryService
    ) -> Dict[str, Any]:
        """Execute a document processing test
        
        Args:
            test_case: Test case to execute
            ai_service: AI service to use
            rag_service: RAG memory service to use
            
        Returns:
            Test output
        """
        try:
            # Get input document
            doc_path = test_case.input_data.get("document_path")
            if not doc_path:
                raise TestingError("Missing document_path in input data")
            
            # Process document
            doc_service = DocumentProcessingService(rag_service)
            result = await doc_service.process_document(
                Path(doc_path),
                ai_service=ai_service
            )
            
            return {
                "processed_content": result.content,
                "metadata": result.metadata,
                "error": None
            }
            
        except Exception as e:
            return {
                "processed_content": None,
                "metadata": None,
                "error": str(e)
            }
    
    async def _execute_diagram_test(
        self,
        test_case: TestCase,
        ai_service: AIServiceConfig,
        rag_service: RAGMemoryService
    ) -> Dict[str, Any]:
        """Execute a diagram generation test
        
        Args:
            test_case: Test case to execute
            ai_service: AI service to use
            rag_service: RAG memory service to use
            
        Returns:
            Test output
        """
        try:
            # Get input data
            input_text = test_case.input_data.get("input_text")
            template_name = test_case.input_data.get("template_name")
            if not input_text or not template_name:
                raise TestingError("Missing input_text or template_name")
            
            # Generate diagram
            visio_service = VisioGenerationService(
                ai_service=ai_service,
                rag_service=rag_service
            )
            result = await visio_service.generate_diagram(
                input_text=input_text,
                template_name=template_name
            )
            
            return {
                "diagram_path": str(result.diagram_path),
                "pdf_path": str(result.pdf_path),
                "metadata": result.metadata,
                "error": None
            }
            
        except Exception as e:
            return {
                "diagram_path": None,
                "pdf_path": None,
                "metadata": None,
                "error": str(e)
            }
    
    async def _execute_query_test(
        self,
        test_case: TestCase,
        ai_service: AIServiceConfig,
        rag_service: RAGMemoryService
    ) -> Dict[str, Any]:
        """Execute a knowledge query test
        
        Args:
            test_case: Test case to execute
            ai_service: AI service to use
            rag_service: RAG memory service to use
            
        Returns:
            Test output
        """
        try:
            # Get input query
            query = test_case.input_data.get("query")
            if not query:
                raise TestingError("Missing query in input data")
            
            # Execute query
            results = await rag_service.query_memory(
                query=query,
                ai_service=ai_service,
                max_results=test_case.input_data.get("max_results", 5)
            )
            
            return {
                "results": [r.to_dict() for r in results],
                "error": None
            }
            
        except Exception as e:
            return {
                "results": None,
                "error": str(e)
            }
    
    async def _validate_test_output(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any],
        rules: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate test output against expected output
        
        Args:
            expected: Expected output
            actual: Actual output
            rules: Optional validation rules
            
        Returns:
            Validation result
        """
        try:
            # Check for errors
            if actual.get("error"):
                return ValidationResult(
                    status=TestStatus.ERROR,
                    details={"error": actual["error"]}
                )
            
            # Apply validation rules if provided
            if rules:
                # Custom validation logic based on rules
                validation_details = {}
                
                # Example: Check required fields
                if "required_fields" in rules:
                    missing_fields = []
                    for field in rules["required_fields"]:
                        if field not in actual:
                            missing_fields.append(field)
                    if missing_fields:
                        validation_details["missing_fields"] = missing_fields
                
                # Example: Check field types
                if "field_types" in rules:
                    type_errors = []
                    for field, expected_type in rules["field_types"].items():
                        if field in actual:
                            actual_type = type(actual[field]).__name__
                            if actual_type != expected_type:
                                type_errors.append(
                                    f"{field}: expected {expected_type},"
                                    f" got {actual_type}"
                                )
                    if type_errors:
                        validation_details["type_errors"] = type_errors
                
                # Example: Check value ranges
                if "value_ranges" in rules:
                    range_errors = []
                    for field, range_spec in rules["value_ranges"].items():
                        if field in actual:
                            value = actual[field]
                            min_val = range_spec.get("min")
                            max_val = range_spec.get("max")
                            if min_val is not None and value < min_val:
                                range_errors.append(
                                    f"{field}: {value} below minimum {min_val}"
                                )
                            if max_val is not None and value > max_val:
                                range_errors.append(
                                    f"{field}: {value} above maximum {max_val}"
                                )
                    if range_errors:
                        validation_details["range_errors"] = range_errors
                
                if validation_details:
                    return ValidationResult(
                        status=TestStatus.FAILED,
                        details=validation_details
                    )
            
            # Compare with expected output
            differences = self._compare_outputs(expected, actual)
            if differences:
                return ValidationResult(
                    status=TestStatus.FAILED,
                    details={"differences": differences}
                )
            
            return ValidationResult(
                status=TestStatus.PASSED,
                details={}
            )
            
        except Exception as e:
            return ValidationResult(
                status=TestStatus.ERROR,
                details={"error": str(e)}
            )
    
    def _compare_outputs(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> List[str]:
        """Compare expected and actual outputs
        
        Args:
            expected: Expected output
            actual: Actual output
            
        Returns:
            List of differences
        """
        differences = []
        
        def compare_values(path: str, exp: Any, act: Any):
            if isinstance(exp, dict) and isinstance(act, dict):
                # Compare dictionaries
                for k in set(exp.keys()) | set(act.keys()):
                    if k not in exp:
                        differences.append(f"Extra key at {path}.{k}")
                    elif k not in act:
                        differences.append(f"Missing key at {path}.{k}")
                    else:
                        compare_values(f"{path}.{k}", exp[k], act[k])
            elif isinstance(exp, (list, tuple)) and isinstance(act, (list, tuple)):
                # Compare sequences
                if len(exp) != len(act):
                    differences.append(
                        f"Length mismatch at {path}:"
                        f" expected {len(exp)}, got {len(act)}"
                    )
                else:
                    for i, (e, a) in enumerate(zip(exp, act)):
                        compare_values(f"{path}[{i}]", e, a)
            elif exp != act:
                differences.append(
                    f"Value mismatch at {path}:"
                    f" expected {exp}, got {act}"
                )
        
        compare_values("root", expected, actual)
        return differences 