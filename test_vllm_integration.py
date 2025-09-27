#!/usr/bin/env python
"""
Test script for vLLM integration
This script tests the vLLM client functionality without running full evaluations.
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_vllm_imports():
    """Test if vLLM modules can be imported successfully."""
    print("Testing vLLM imports...")
    
    try:
        from agents.config.vllm import VLLM_API_KEY, VLLM_BASE_URL, VLLM_MODEL_CONFIGS
        print("✓ vLLM config imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import vLLM config: {e}")
        return False
    
    try:
        from agents.vllm_client import VLLMClient, vllm_completion_with_backoff, check_vllm_server_health
        print("✓ vLLM client imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import vLLM client: {e}")
        return False
    
    try:
        from agents.openai_chatComplete import completion_with_backoff
        print("✓ Updated completion function imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import completion function: {e}")
        return False
    
    return True


def test_vllm_server_connection():
    """Test connection to vLLM server."""
    print("\nTesting vLLM server connection...")
    
    try:
        from agents.vllm_client import check_vllm_server_health, get_available_models
        
        # Check server health
        if check_vllm_server_health():
            print("✓ vLLM server is running and healthy")
            
            # Get available models
            models = get_available_models()
            if models:
                print(f"✓ Available models: {models}")
            else:
                print("⚠ No models found (server might be starting up)")
            
            return True
        else:
            print("✗ vLLM server is not responding")
            print("Please start a vLLM server with:")
            print("python -m vllm.entrypoints.openai.api_server --model <model_name> --port 8000")
            return False
            
    except Exception as e:
        print(f"✗ Error testing server connection: {e}")
        return False


def test_completion_function():
    """Test the completion function with vLLM."""
    print("\nTesting completion function...")
    
    try:
        from agents.openai_chatComplete import completion_with_backoff
        
        # Test messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        # Test with vLLM model
        print("Testing with vLLM backend...")
        response = completion_with_backoff(messages, "vllm/codellama-7b")
        
        if response:
            print(f"✓ vLLM completion successful: {response[:100]}...")
            return True
        else:
            print("✗ vLLM completion failed (no response)")
            return False
            
    except Exception as e:
        print(f"✗ Error testing completion: {e}")
        return False


def test_config_files():
    """Test if vLLM config files are valid."""
    print("\nTesting vLLM config files...")
    
    config_files = [
        "config/vllm_single_bug_eval_agent_config.py",
        "config/vllm_multi_bug_eval_agent_config.py"
    ]
    
    for config_file in config_files:
        try:
            if os.path.exists(config_file):
                # Try to import the config
                module_name = config_file.replace('/', '.').replace('.py', '')
                import importlib
                config_module = importlib.import_module(module_name)
                
                # Check if required attributes exist
                if hasattr(config_module, 'AGENT_CONFIG') and hasattr(config_module, 'WORKFLOW'):
                    print(f"✓ {config_file} is valid")
                else:
                    print(f"✗ {config_file} missing required attributes")
            else:
                print(f"✗ {config_file} not found")
        except Exception as e:
            print(f"✗ Error loading {config_file}: {e}")


def main():
    """Run all tests."""
    print("=== vLLM Integration Test ===\n")
    
    # Test imports
    if not test_vllm_imports():
        print("\n❌ Import tests failed. Please check your installation.")
        return
    
    # Test config files
    test_config_files()
    
    # Test server connection
    server_ok = test_vllm_server_connection()
    
    # Test completion function only if server is running
    if server_ok:
        test_completion_function()
    
    print("\n=== Test Summary ===")
    if server_ok:
        print("✅ vLLM integration is working correctly!")
        print("\nYou can now run evaluations with:")
        print("python run_vllm_single_bug_eval.py")
    else:
        print("⚠️  vLLM integration is set up but server is not running.")
        print("\nTo use vLLM, start a server with:")
        print("python -m vllm.entrypoints.openai.api_server --model codellama/CodeLlama-7b-Instruct-hf --port 8000")


if __name__ == "__main__":
    main()
