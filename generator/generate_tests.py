"""
AI-Assisted Test Case Generator
================================
Uses Claude to analyze an OpenAPI spec and generate structured test cases.
Demonstrates AI as a capability multiplier in QA engineering —
AI proposes, human validates, automation executes.
"""

import json
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

def load_spec(spec_path: str) -> dict:
    """Load an OpenAPI spec from a JSON file."""
    with open(spec_path, 'r') as f:
        return json.load(f)


def generate_test_cases(spec: dict) -> dict:
    """
    Send the OpenAPI spec to Claude and request structured test cases.
    Returns a dictionary of test cases organized by endpoint.
    """
    spec_text = json.dumps(spec, indent=2)

    prompt = f"""You are a senior QA engineer analyzing an OpenAPI specification.
Your job is to generate up to 20 structured test cases that cover:
- Happy path scenarios
- Negative/error scenarios  
- Edge cases and boundary conditions
- Authentication and authorization scenarios
- Data validation scenarios

Analyze this OpenAPI spec and generate test cases.
Return ONLY valid JSON — no markdown, no explanation, no backticks.

The JSON structure must be:
{{
  "api_name": "string",
  "generated_test_cases": [
    {{
      "test_id": "TC001",
      "endpoint": "/path",
      "method": "GET/POST/etc",
      "category": "happy_path|negative|edge_case|auth|data_validation",
      "description": "What this test validates",
      "preconditions": "What must be true before this test",
      "inputs": {{}},
      "expected_status_code": 200,
      "expected_behavior": "What should happen",
      "risk_level": "high|medium|low"
    }}
  ],
  "coverage_summary": {{
    "total_tests": 0,
    "happy_path": 0,
    "negative": 0,
    "edge_cases": 0,
    "auth": 0,
    "data_validation": 0
  }},
  "coverage_gaps": ["list of areas not covered"],
  "high_risk_areas": ["list of areas needing priority attention"]
}}

OpenAPI Spec:
{spec_text}"""

    print("Sending spec to Claude for analysis...")
    print("AI is generating test cases — this may take a moment...\n")

    message = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=8192,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text

    # Clean response — strip markdown fences if Claude included them
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()

    # Parse the JSON response
    test_cases = json.loads(response_text)

    return test_cases


def save_test_cases(test_cases: dict, output_path: str):
    """Save generated test cases to a JSON file for human review."""
    with open(output_path, 'w') as f:
        json.dump(test_cases, f, indent=2)
    print(f"Test cases saved to: {output_path}")


def print_summary(test_cases: dict):
    """Print a human-readable summary of generated test cases."""
    print("=" * 60)
    print(f"AI-GENERATED TEST CASE SUMMARY")
    print("=" * 60)
    print(f"API: {test_cases.get('api_name', 'Unknown')}")
    
    summary = test_cases.get('coverage_summary', {})
    print(f"\nTotal test cases generated: {summary.get('total_tests', 0)}")
    print(f"  Happy path:      {summary.get('happy_path', 0)}")
    print(f"  Negative:        {summary.get('negative', 0)}")
    print(f"  Edge cases:      {summary.get('edge_cases', 0)}")
    print(f"  Auth/Security:   {summary.get('auth', 0)}")
    print(f"  Data validation: {summary.get('data_validation', 0)}")

    gaps = test_cases.get('coverage_gaps', [])
    if gaps:
        print(f"\nCoverage gaps identified by AI:")
        for gap in gaps:
            print(f"  - {gap}")

    high_risk = test_cases.get('high_risk_areas', [])
    if high_risk:
        print(f"\nHigh-risk areas flagged:")
        for area in high_risk:
            print(f"  - {area}")

    print("\n" + "=" * 60)
    print("HUMAN VALIDATION REQUIRED")
    print("=" * 60)
    print("Review generated test cases in: validation/generated_test_cases.json")
    print("Apply QA judgment before executing:")
    print("  1. Are the test cases accurate for this system?")
    print("  2. Are edge cases realistic?")
    print("  3. Are risk levels correctly assigned?")
    print("  4. What did AI miss that domain knowledge would catch?")
    print("=" * 60)


if __name__ == "__main__":
    # Load the OpenAPI spec
    spec_path = "specs/restful-booker-openapi.json"
    spec = load_spec(spec_path)
    print(f"Loaded spec: {spec.get('info', {}).get('title', 'Unknown API')}\n")

    # Generate test cases using Claude
    test_cases = generate_test_cases(spec)

    # Save for human review
    save_test_cases(test_cases, "validation/generated_test_cases.json")

    # Print summary
    print_summary(test_cases)