#!/usr/bin/env python3
"""
Test script for Agentcy 2.0
Validates core functionality without requiring API keys
"""

def test_imports():
    """Test that all modules can be imported"""
    try:
        from agentcy import (
            AgentcyConfig, 
            AdvancedResearchTools, 
            VisualContentTools,
            MarketingFrameworks,
            AgentcyCore
        )
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration setup"""
    try:
        from agentcy import AgentcyConfig
        config = AgentcyConfig()
        
        # Check that directories are created
        assert config.output_dir.exists(), "Output directory not created"
        assert config.research_dir.exists(), "Research directory not created"
        assert config.content_dir.exists(), "Content directory not created"
        assert config.images_dir.exists(), "Images directory not created"
        
        print("✅ Configuration and directory setup successful")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_frameworks():
    """Test marketing frameworks"""
    try:
        from agentcy import MarketingFrameworks
        
        frameworks = MarketingFrameworks()
        
        # Test framework methods
        copywriting = frameworks.get_copywriting_guidance()
        marketing = frameworks.get_marketing_guidance()
        media = frameworks.get_media_guidance()
        
        assert "Reciprocity" in copywriting, "Copywriting principles missing"
        assert "4Ps" in marketing, "Marketing frameworks missing"
        assert "RACE" in media, "Media frameworks missing"
        
        print("✅ Marketing frameworks working correctly")
        return True
    except Exception as e:
        print(f"❌ Frameworks error: {e}")
        return False

def test_research_tools():
    """Test research tools initialization"""
    try:
        from agentcy import AgentcyConfig, AdvancedResearchTools
        
        config = AgentcyConfig()
        research_tools = AdvancedResearchTools(config)
        
        # Test basic functionality without making actual API calls
        assert hasattr(research_tools, 'search'), "Search method missing"
        assert hasattr(research_tools, 'scrape_basic'), "Scraping method missing"
        assert hasattr(research_tools, 'summarize_text'), "Summarization method missing"
        
        print("✅ Research tools initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Research tools error: {e}")
        return False

def test_visual_tools():
    """Test visual content tools"""
    try:
        from agentcy import AgentcyConfig, VisualContentTools
        
        config = AgentcyConfig()
        visual_tools = VisualContentTools(config)
        
        # Test that methods exist
        assert hasattr(visual_tools, 'generate_image'), "Image generation method missing"
        assert hasattr(visual_tools, 'critique_image'), "Image critique method missing"
        
        print("✅ Visual tools initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Visual tools error: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🧪 Running Agentcy 2.0 Tests")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_config,
        test_frameworks,
        test_research_tools,
        test_visual_tools
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Agentcy 2.0 is ready to use.")
        print("\nTo get started:")
        print("1. Set up your .env file with API keys")
        print("2. Run: python agentcy.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == len(tests)

if __name__ == "__main__":
    run_all_tests()