@pytest.mark.asyncio
async def test_av_compliance_checks():
    config = {
        "project_id": "test-project",
        "location": "us-central1",
        "model_map": {
            "vision": "gemini-pro-vision",
            "generative": "gemini-1.5-pro"
        }
    }
    
    service = VertexAIService(config)
    result = await service.validate_schematic("tests/data/projector_rack.png")
    
    # Verify AV-specific compliance checks
    assert any(issue["type"] == "compliance" 
              for issue in result["compliance_issues"]), "Missing compliance checks"
    
    # Verify component recognition
    assert "projector" in result["component_analysis"], "Failed to detect projectors"
    assert "mixer" in result["component_analysis"], "Failed to detect audio mixers"

@pytest.mark.asyncio
async def test_av_schematic_validation():
    config = {
        "project_id": "test-project",
        "location": "us-central1",
        "model_map": {
            "vision": "imagetext@001",
            "generative": "gemini-1.5-pro"
        }
    }
    
    service = VertexAIService(config)
    
    # Test with sample AV schematic
    result = await service.validate_schematic("tests/data/av_schematic.png")
    
    assert "compliance_violations" in result
    assert "anomalies" in result
    assert isinstance(result["anomalies"], list)
    
    # Verify AV-specific checks
    assert any("signal flow" in anomaly["description"].lower() 
              for anomaly in result["anomalies"]) 