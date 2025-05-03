"""Utility functions for testing."""

import json
import random
import string
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI
from fastapi.testclient import TestClient


def random_string(length: int = 10) -> str:
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


def random_email() -> str:
    """Generate a random email address."""
    return f"{random_string(8)}@{random_string(5)}.com"


def random_bool() -> bool:
    """Generate a random boolean value."""
    return random.choice([True, False])


def random_int(min_val: int = 0, max_val: int = 100) -> int:
    """Generate a random integer within a range."""
    return random.randint(min_val, max_val)


def random_float(min_val: float = 0.0, max_val: float = 100.0) -> float:
    """Generate a random float within a range."""
    return random.uniform(min_val, max_val)


def random_list(length: int = 5, item_type: str = "string") -> List[Any]:
    """Generate a random list of items."""
    if item_type == "string":
        return [random_string() for _ in range(length)]
    elif item_type == "int":
        return [random_int() for _ in range(length)]
    elif item_type == "float":
        return [random_float() for _ in range(length)]
    elif item_type == "bool":
        return [random_bool() for _ in range(length)]
    else:
        raise ValueError(f"Unsupported item_type: {item_type}")


def random_dict(keys: int = 5) -> Dict[str, Any]:
    """Generate a random dictionary."""
    return {random_string(): random_string() for _ in range(keys)}


def assert_json_response(
    client: TestClient,
    app: FastAPI,
    url: str,
    expected_status_code: int = 200,
    expected_response: Optional[Dict[str, Any]] = None,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Union[Dict[str, Any], List[Any]]] = None,
) -> Dict[str, Any]:
    """
    Make a request to the API and assert the response.
    
    Args:
        client: TestClient instance
        app: FastAPI application instance
        url: URL to request
        expected_status_code: Expected HTTP status code
        expected_response: Expected response data (if None, only status code is checked)
        method: HTTP method to use
        headers: HTTP headers to include
        data: Data to send in the request body
        
    Returns:
        Response data as a dictionary
    """
    headers = headers or {}
    
    if method.upper() == "GET":
        response = client.get(url, headers=headers)
    elif method.upper() == "POST":
        response = client.post(url, json=data, headers=headers)
    elif method.upper() == "PUT":
        response = client.put(url, json=data, headers=headers)
    elif method.upper() == "DELETE":
        response = client.delete(url, headers=headers)
    elif method.upper() == "PATCH":
        response = client.patch(url, json=data, headers=headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
    
    assert response.status_code == expected_status_code, (
        f"Expected status code {expected_status_code}, got {response.status_code}. "
        f"Response: {response.text}"
    )
    
    if expected_response is not None:
        response_data = response.json()
        assert response_data == expected_response, (
            f"Expected response {expected_response}, got {response_data}"
        )
    
    try:
        return response.json()
    except json.JSONDecodeError:
        return {"text": response.text}
