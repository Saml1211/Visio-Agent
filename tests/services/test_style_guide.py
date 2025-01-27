def test_font_rule_loading():
    service = VisioStyleGuideService("test_config")
    rules = service.get_rules('font')
    assert rules.font_name == "Segoe UI"
    assert rules.size == 10 