import requests
import json

url = "http://localhost:8000/api/v1/maintenance/maintenance/format-procedure"
headers = {"Content-Type": "application/json"}

# Procedure to format
procedure = {
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

# Format as markdown with regulatory enrichment
response = requests.post(
    url, 
    headers=headers, 
    json=procedure,
    params={
        "format_type": "markdown",
        "enrich_regulatory": "true",
        "regulatory_requirements": "FAA Part 43"
    }
)

print(f"Status code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
