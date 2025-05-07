import requests
import json

url = "http://localhost:8000/api/v1/maintenance/maintenance/enhance-with-llm"
headers = {"Content-Type": "application/json"}

# Base procedure to enhance
base_procedure = {
    "id": "maint-001",
    "title": "Hydraulic System Inspection",
    "description": "Procedure for inspecting the hydraulic system",
    "steps": [
        {
            "step_number": 1,
            "title": "Preparation",
            "description": "Prepare the aircraft for inspection",
            "cautions": ["Ensure aircraft is properly secured"]
        },
        {
            "step_number": 2,
            "title": "Visual Inspection",
            "description": "Visually inspect hydraulic components",
            "cautions": ["Use proper lighting"]
        }
    ],
    "safety_precautions": [
        "Wear appropriate PPE",
        "Follow safety procedures"
    ],
    "tools_required": [
        {
            "id": "tool-001",
            "name": "Flashlight",
            "specification": "Standard"
        }
    ]
}

# Parameters
params = {
    "aircraft_type": "Boeing 737",
    "aircraft_model": "737-800",
    "system": "Hydraulic",
    "components": "Pumps, Reservoirs",
    "configuration": "Standard configuration",
    "regulatory_requirements": "FAA regulations",
    "special_considerations": "None",
    "use_large_model": "true",
    "format_type": "markdown",
    "enrich_regulatory": "true"
}

response = requests.post(url, headers=headers, json=base_procedure, params=params)
print(f"Status code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
