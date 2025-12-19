---
name: Booking Management Skill
description: |
  A skill for managing booking operations including:
  1. Collecting customer booking data and validating against API requirements before submission
  2. Querying booking status by bill of lading number
  
  This skill should be activated when customers need to submit new bookings or check existing booking status.
freedom_level: medium
---

## Booking Data Collection and Submission

When customers want to submit a new booking, collect the following required information:

### Required Fields (Mandatory)
- **Shipper Name**: String, 1-100 characters
- **Consignee Name**: String, 1-100 characters  
- **Origin Port**: String, 3-50 characters (must be valid port code/name)
- **Destination Port**: String, 3-50 characters (must be valid port code/name)
- **Cargo Description**: String, 10-500 characters
- **Container Type**: String, must be one of: "20GP", "40GP", "40HQ", "45HQ"
- **Number of Containers**: Integer, 1-999
- **Expected Departure Date**: Date in YYYY-MM-DD format

### Optional Fields
- **Special Instructions**: String, 0-200 characters
- **Reference Number**: String, 0-50 characters
- **Commodity Type**: String, 0-50 characters

### Validation Rules
- All required fields must be provided
- Field lengths must comply with specified limits
- Container type must match allowed values
- Date format must be valid YYYY-MM-DD
- Ports must be recognizable port codes or names

If any validation fails, request the customer to correct the specific field(s) that don't meet requirements.

## Booking Status Query

When customers want to check booking status, ask for the **Bill of Lading Number**.

### Query Process
1. Request the bill of lading number from customer
2. Validate that the number is provided (minimum 5 characters)
3. Query the booking system using the provided number
4. Return current status which may include:
   - Booking Confirmed
   - Documentation Pending
   - Cargo Received
   - Vessel Assigned
   - Sailed
   - Delivered
   - Cancelled

## Usage Guidelines

- Always validate data before attempting API submission
- Provide clear error messages for validation failures
- For status queries, confirm the bill of lading number with customer before querying
- If API returns errors, explain the issue in user-friendly terms
- Maintain professional communication throughout the booking process

## Integration Notes

This skill interfaces with the booking management system via REST API endpoints:
- POST /api/v1/bookings - for new booking submission
- GET /api/v1/bookings/{bol_number} - for status queries

The skill handles all API authentication and error handling internally.
