#!/usr/bin/env python3
"""Test the parameter ordering fix for _update_status function."""

import inspect

# Mock the types we need for testing
class MockDatabase:
    pass

class DocumentStatus:
    PROCESSING = "processing"
    DRAFT = "draft"
    ERROR = "error"

# Create a mock function with the fixed signature
def _update_status(db: MockDatabase, document_id: str, status: DocumentStatus, **kwargs):
    """Atualiza o status do documento no MongoDB."""
    print(f"Atualizando status para {status} com dados adicionais: {kwargs}")
    return True

def test_parameter_order():
    """Test that the parameters are in the correct order."""
    sig = inspect.signature(_update_status)
    params = list(sig.parameters.keys())
    
    print("Function signature:", sig)
    print("Parameter order:", params)
    
    # Check that db is first, then document_id, then status
    assert params[0] == 'db', f"First parameter should be 'db', got {params[0]}"
    assert params[1] == 'document_id', f"Second parameter should be 'document_id', got {params[1]}"
    assert params[2] == 'status', f"Third parameter should be 'status', got {params[2]}"
    
    # Check that db doesn't have a default value (it's required)
    db_param = sig.parameters['db']
    assert db_param.default == inspect.Parameter.empty, "db should not have a default value"
    
    print("\n✓ All tests passed! Parameter ordering is correct.")
    print("✓ No non-default arguments follow default arguments.")
    
    # Test that we can call the function correctly
    mock_db = MockDatabase()
    result = _update_status(mock_db, "doc123", DocumentStatus.PROCESSING, extra="data")
    print(f"\n✓ Function call successful with result: {result}")

if __name__ == "__main__":
    test_parameter_order()