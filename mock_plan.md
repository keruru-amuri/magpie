# MAGPIE Mock Data Plan

This document outlines the approach for generating mock data for the initial development of the MAGPIE platform's three primary use cases.

## 1. Technical Documentation Assistant

### Mock Data Components
- **Aircraft Maintenance Manuals**: Simplified sections covering key aircraft systems (hydraulic, electrical, avionics, engines)
- **Service Bulletins**: Sample bulletins with varying complexity and urgency levels
- **Airworthiness Directives**: Sample regulatory directives with compliance requirements
- **Component Manuals**: Detailed specifications for selected aircraft components

### Data Format
- PDF and text files for documentation
- JSON metadata for document properties (publication date, revision, applicability)
- Sample queries and expected responses for testing

### Generation Approach
- Create templates for each document type
- Populate with realistic but simplified technical content
- Include diagrams and reference tables where appropriate
- Tag sections for searchability

## 2. Troubleshooting Advisor

### Mock Data Components
- **Fault Database**: Common aircraft system faults with symptoms, causes, and solutions
- **Maintenance History**: Synthetic records of past maintenance actions and outcomes
- **Troubleshooting Workflows**: Decision trees for different systems and fault types
- **Component Relationships**: Mapping of how different aircraft systems interact

### Data Format
- JSON structures for fault scenarios and relationships
- CSV for maintenance history records
- Markdown for troubleshooting procedures
- Sample user inputs and expected advisor responses

### Generation Approach
- Define common fault categories for major aircraft systems
- Create realistic symptom descriptions and diagnostic steps
- Generate synthetic maintenance history with patterns and anomalies
- Develop decision trees with varying complexity to test different model sizes

## 3. Maintenance Procedure Generator

### Mock Data Components
- **Procedure Templates**: Standard maintenance task structures
- **Aircraft Configurations**: Sample data for different aircraft types and modifications
- **Regulatory Requirements**: Simplified compliance requirements
- **Parts and Tools Catalog**: Sample inventory with specifications

### Data Format
- JSON templates for procedures
- YAML for aircraft configuration data
- Markdown for regulatory requirements
- CSV for parts and tools catalog

### Generation Approach
- Create base templates for common maintenance tasks
- Define variables for customization points
- Generate sample aircraft configurations with different parameters
- Develop simplified regulatory snippets that affect procedures

## Implementation Priority

1. **Troubleshooting Advisor** - Highest mock data feasibility
2. **Technical Documentation Assistant** - Medium-high mock data feasibility
3. **Maintenance Procedure Generator** - Medium mock data feasibility

## Data Storage and Access

- Store mock data in the project repository under `/data/mock`
- Organize by use case and data type
- Include README files explaining the structure and generation methodology
- Provide utilities for loading and manipulating the mock data

## Validation Approach

- Create test cases to verify data completeness
- Ensure data represents varying complexity levels to test model selection
- Include edge cases to test system robustness
- Develop evaluation metrics for each use case
