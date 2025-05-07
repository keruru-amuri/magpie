import requests
import json

url = "http://localhost:8000/api/v1/maintenance/maintenance/generate-hybrid"
headers = {"Content-Type": "application/json"}
data = {
    "aircraft_type": "Boeing 737",
    "system": "Hydraulic",
    "procedure_type": "Inspection",
    "parameters": {
        "aircraft_model": "737-800",
        "components": "Pumps, Reservoirs",
        "configuration": "Standard configuration",
        "regulatory_requirements": "FAA regulations",
        "special_considerations": "None"
    }
}

# Generate procedure with hybrid approach and markdown formatting
response = requests.post(
    url, 
    headers=headers, 
    json=data,
    params={
        "format_type": "markdown",
        "enrich_regulatory": "true"
    }
)

print(f"Status code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
