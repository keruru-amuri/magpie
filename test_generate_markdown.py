import requests
import json

url = "http://localhost:8000/api/v1/maintenance/maintenance/generate-with-llm"
headers = {"Content-Type": "application/json"}
data = {
    "procedure_type": "Inspection",
    "aircraft_type": "Boeing 737",
    "aircraft_model": "737-800",
    "system": "Hydraulic",
    "components": "Pumps, Reservoirs",
    "configuration": "Standard configuration",
    "regulatory_requirements": "FAA regulations",
    "special_considerations": "None",
    "use_large_model": True
}

# Generate procedure with markdown formatting
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
