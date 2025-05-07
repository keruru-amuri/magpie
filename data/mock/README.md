# MAGPIE Mock Data

This directory contains mock data for the MAGPIE platform's three primary use cases:

1. Technical Documentation Assistant
2. Troubleshooting Advisor
3. Maintenance Procedure Generator

## Directory Structure

- `/documentation` - Mock data for the Technical Documentation Assistant
  - Aircraft maintenance manuals
  - Service bulletins
  - Airworthiness directives
  - Component manuals

- `/troubleshooting` - Mock data for the Troubleshooting Advisor
  - Fault database
  - Maintenance history
  - Troubleshooting workflows
  - Component relationships

- `/maintenance` - Mock data for the Maintenance Procedure Generator
  - Procedure templates
  - Aircraft configurations
  - Regulatory requirements
  - Parts and tools catalog

- `/schemas` - JSON schemas for all data types
  - Documentation schemas
  - Troubleshooting schemas
  - Maintenance procedure schemas

## Usage

The mock data can be loaded using the utilities in the `app/core/mock` module. See the module documentation for details on how to use the mock data in development and testing.

## Generation Methodology

The mock data was generated using templates and realistic but simplified technical content. It includes diagrams, reference tables, and other elements to simulate real-world aircraft maintenance documentation.

## Data Format

- Documentation: PDF and text files with JSON metadata
- Troubleshooting: JSON structures for fault scenarios and relationships
- Maintenance: JSON templates for procedures with YAML for aircraft configurations
