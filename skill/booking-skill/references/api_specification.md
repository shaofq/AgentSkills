# Booking API Specification

## Authentication
All API endpoints require Bearer token authentication in the Authorization header.

## Endpoints

### POST /api/v1/bookings
Submit a new booking request.

**Request Body (JSON):**
```json
{
  "shipper_name": "string (1-100 chars)",
  "consignee_name": "string (1-100 chars)",
  "origin_port": "string (3-50 chars)",
  "destination_port": "string (3-50 chars)",
  "cargo_description": "string (10-500 chars)",
  "container_type": "string (20GP|40GP|40HQ|45HQ)",
  "number_of_containers": "integer (1-999)",
  "expected_departure_date": "string (YYYY-MM-DD)",
  "special_instructions": "string (optional, 0-200 chars)",
  "reference_number": "string (optional, 0-50 chars)",
  "commodity_type": "string (optional, 0-50 chars)"
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "booking_reference": "string",
  "message": "Booking submitted successfully"
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "errors": ["array of error messages"]
}
```

### GET /api/v1/bookings/{bol_number}
Query booking status by bill of lading number.

**Path Parameters:**
- `bol_number`: Bill of lading number (minimum 5 characters)

**Success Response (200 OK):**
```json
{
  "success": true,
  "bol_number": "string",
  "status": "string",
  "details": {
    "vessel": "string",
    "voyage": "string",
    "eta": "YYYY-MM-DD",
    "etd": "YYYY-MM-DD"
  }
}
```

**Error Response (404 Not Found):**
```json
{
  "success": false,
  "error": "Booking not found"
}
```

## Status Values
- `Booking Confirmed`
- `Documentation Pending`
- `Cargo Received`
- `Vessel Assigned`
- `Sailed`
- `Delivered`
- `Cancelled`
