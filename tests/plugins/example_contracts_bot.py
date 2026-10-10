"""
Example Plugin: Federal Contracts Bot Tests
This demonstrates how to create a plugin for a different bot type
"""

from tests.framework.base_test import BaseTestModule, TestResult, TestStatus


class ContractsBotTest(BaseTestModule):
    """
    Example test module for a Federal Contracts Bot
    
    This bot would handle:
    - Searching for federal contracts
    - Writing proposals/quotes
    - Managing contracts throughout their lifecycle
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        super().__init__("Federal Contracts Bot", api_base_url)
    
    def test_contract_search(self) -> TestResult:
        """Test contract search endpoint"""
        def _test():
            # Test basic search
            response = self.api_request("GET", "/api/contracts/search", params={
                "keyword": "IT",
                "limit": 10
            })
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            self.assert_field_exists(data, "contracts")
            self.assert_field_exists(data, "total")
            assert isinstance(data["contracts"], list), "contracts should be a list"
            
            # If contracts exist, validate structure
            if data["contracts"]:
                contract = data["contracts"][0]
                required_fields = ["id", "title", "agency", "posted_date", "due_date"]
                for field in required_fields:
                    assert field in contract, f"Contract missing field: {field}"
            
            return True
        
        return self.run_test("Contract Search", _test)
    
    def test_contract_details(self) -> TestResult:
        """Test contract details endpoint"""
        def _test():
            # First get a contract ID
            search_response = self.api_request("GET", "/api/contracts/search", params={"limit": 1})
            if search_response.status_code == 200:
                search_data = self.assert_json(search_response)
                if search_data.get("contracts"):
                    contract_id = search_data["contracts"][0]["id"]
                    
                    # Get contract details
                    response = self.api_request("GET", f"/api/contracts/{contract_id}")
                    self.assert_status(response, 200)
                    data = self.assert_json(response)
                    
                    # Validate contract details structure
                    required_fields = ["id", "title", "description", "requirements", "budget"]
                    for field in required_fields:
                        assert field in data, f"Contract details missing field: {field}"
            
            return True
        
        return self.run_test("Contract Details", _test)
    
    def test_proposal_generation(self) -> TestResult:
        """Test proposal generation endpoint"""
        def _test():
            response = self.api_request("POST", "/api/proposals/generate", json={
                "contract_id": "test-123",
                "template": "standard",
                "sections": ["executive_summary", "technical_approach", "pricing"]
            })
            
            # Should return 200 or 201 (created)
            assert response.status_code in [200, 201], f"Unexpected status: {response.status_code}"
            
            if response.status_code in [200, 201]:
                data = self.assert_json(response)
                self.assert_field_exists(data, "proposal_id")
                self.assert_field_exists(data, "status")
            
            return True
        
        return self.run_test("Proposal Generation", _test)
    
    def test_proposal_templates(self) -> TestResult:
        """Test proposal templates endpoint"""
        def _test():
            response = self.api_request("GET", "/api/proposals/templates")
            self.assert_status(response, 200)
            data = self.assert_json(response)
            
            self.assert_field_exists(data, "templates")
            assert isinstance(data["templates"], list), "templates should be a list"
            
            # Validate template structure
            if data["templates"]:
                template = data["templates"][0]
                required_fields = ["id", "name", "sections"]
                for field in required_fields:
                    assert field in template, f"Template missing field: {field}"
            
            return True
        
        return self.run_test("Proposal Templates", _test)
    
    def test_contract_lifecycle(self) -> TestResult:
        """Test contract lifecycle management"""
        def _test():
            # Test lifecycle stages
            stages = ["draft", "submitted", "under_review", "awarded", "active", "completed"]
            
            for stage in stages:
                response = self.api_request("GET", f"/api/contracts?status={stage}", params={"limit": 5})
                # Should return 200 even if no contracts in that stage
                assert response.status_code == 200, f"Failed to get contracts in {stage} stage"
            
            return True
        
        return self.run_test("Contract Lifecycle", _test)
    
    def test_contract_management(self) -> TestResult:
        """Test contract management operations"""
        def _test():
            # Test updating contract status
            response = self.api_request("PATCH", "/api/contracts/test-123/status", json={
                "status": "under_review",
                "notes": "Submitted for review"
            })
            
            # Should return 200 or 404 (if contract doesn't exist)
            assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
            
            # Test adding milestone
            response = self.api_request("POST", "/api/contracts/test-123/milestones", json={
                "title": "Phase 1 Complete",
                "due_date": "2026-02-01",
                "status": "completed"
            })
            
            assert response.status_code in [200, 201, 404], f"Unexpected status: {response.status_code}"
            
            return True
        
        return self.run_test("Contract Management", _test)
    
    def test_document_management(self) -> TestResult:
        """Test document management for contracts"""
        def _test():
            # Test listing documents
            response = self.api_request("GET", "/api/contracts/test-123/documents")
            assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
            
            if response.status_code == 200:
                data = self.assert_json(response)
                self.assert_field_exists(data, "documents")
                assert isinstance(data["documents"], list), "documents should be a list"
            
            return True
        
        return self.run_test("Document Management", _test)
    
    def run(self):
        """Run all contracts bot tests"""
        self.log("Starting Federal Contracts Bot tests...")
        self.log("Note: These tests are examples - adapt endpoints to your actual API")
        
        tests = [
            self.test_contract_search,
            self.test_contract_details,
            self.test_proposal_generation,
            self.test_proposal_templates,
            self.test_contract_lifecycle,
            self.test_contract_management,
            self.test_document_management,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log(f"Test {test.__name__} raised exception: {e}", "ERROR")
        
        self.log(f"Completed {len(self.results)} tests")
        return self.results
