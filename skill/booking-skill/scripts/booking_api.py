#!/usr/bin/env python3
"""
Booking API integration script for the Booking Management Skill.
This script handles both booking submission and status queries.
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Valid container types
VALID_CONTAINER_TYPES = {"20GP", "40GP", "40HQ", "45HQ"}

def validate_booking_data(booking_data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate booking data against requirements.
    
    Args:
        booking_data: Dictionary containing booking information
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields validation
    required_fields = {
        'shipper_name': (str, 1, 100),
        'consignee_name': (str, 1, 100),
        'origin_port': (str, 3, 50),
        'destination_port': (str, 3, 50),
        'cargo_description': (str, 10, 500),
        'container_type': (str, None, None),  # Will validate separately
        'number_of_containers': (int, 1, 999),
        'expected_departure_date': (str, 10, 10)  # YYYY-MM-DD format
    }
    
    for field, (field_type, min_len, max_len) in required_fields.items():
        if field not in booking_data or booking_data[field] is None:
            errors.append(f"Missing required field: {field}")
            continue
            
        value = booking_data[field]
        
        # Type validation
        if field_type == str and not isinstance(value, str):
            errors.append(f"Field '{field}' must be a string")
            continue
        elif field_type == int:
            try:
                value = int(value)
                booking_data[field] = value
            except (ValueError, TypeError):
                errors.append(f"Field '{field}' must be an integer")
                continue
        
        # Length validation for strings
        if field_type == str and min_len is not None:
            if len(str(value)) < min_len:
                errors.append(f"Field '{field}' must be at least {min_len} characters")
            if len(str(value)) > max_len:
                errors.append(f"Field '{field}' must be at most {max_len} characters")
        
        # Special validations
        if field == 'container_type':
            if value not in VALID_CONTAINER_TYPES:
                errors.append(f"Container type must be one of: {', '.join(VALID_CONTAINER_TYPES)}")
        
        if field == 'expected_departure_date':
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                errors.append("Expected departure date must be in YYYY-MM-DD format")
            else:
                try:
                    datetime.strptime(value, '%Y-%m-%d')
                except ValueError:
                    errors.append("Expected departure date must be a valid date")
    
    # Optional fields validation
    optional_fields = {
        'special_instructions': (str, 0, 200),
        'reference_number': (str, 0, 50),
        'commodity_type': (str, 0, 50)
    }
    
    for field, (field_type, min_len, max_len) in optional_fields.items():
        if field in booking_data and booking_data[field] is not None:
            value = booking_data[field]
            if not isinstance(value, str):
                errors.append(f"Field '{field}' must be a string")
            elif len(value) > max_len:
                errors.append(f"Field '{field}' must be at most {max_len} characters")
    
    return len(errors) == 0, errors

def submit_booking(booking_data: Dict) -> Dict:
    """
    Submit booking data to the API (mock implementation).
    
    Args:
        booking_data: Validated booking data
        
    Returns:
        Dictionary with submission result
    """
    # In real implementation, this would make an actual API call
    # For now, return mock success response
    return {
        "success": True,
        "booking_reference": "BK123456789",
        "message": "Booking submitted successfully"
    }

def query_booking_status(bol_number: str) -> Dict:
    """
    Query booking status by bill of lading number (mock implementation).
    
    Args:
        bol_number: Bill of lading number
        
    Returns:
        Dictionary with booking status information
    """
    # In real implementation, this would query the actual API
    # For now, return mock response
    if len(bol_number) < 5:
        return {
            "success": False,
            "error": "Bill of lading number must be at least 5 characters"
        }
    
    # Mock status response
    return {
        "success": True,
        "bol_number": bol_number,
        "status": "Booking Confirmed",
        "details": {
            "vessel": "MV Ocean Star",
            "voyage": "V1234",
            "eta": "2024-02-15",
            "etd": "2024-02-01"
        }
    }

if __name__ == "__main__":
    # This script is meant to be imported, not run directly
    pass
