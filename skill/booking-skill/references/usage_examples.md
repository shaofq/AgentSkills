# Booking Skill Usage Examples

## Example 1: New Booking Submission

**Customer Request:**
"I want to book a shipment from Shanghai to Los Angeles."

**Agent Response:**
Please provide the following information for your booking:

1. **Shipper Name**: (1-100 characters)
2. **Consignee Name**: (1-100 characters)
3. **Origin Port**: (e.g., Shanghai, SHANGHAI, or CNSHA)
4. **Destination Port**: (e.g., Los Angeles, LOS ANGELES, or USLAX)
5. **Cargo Description**: (10-500 characters, describe your cargo)
6. **Container Type**: Choose from: 20GP, 40GP, 40HQ, or 45HQ
7. **Number of Containers**: (1-999)
8. **Expected Departure Date**: (YYYY-MM-DD format)

Optional information:
- Special Instructions (0-200 characters)
- Reference Number (0-50 characters)
- Commodity Type (0-50 characters)

**Customer Provides Data:**
- Shipper Name: ABC Trading Co.
- Consignee Name: XYZ Imports Inc.
- Origin Port: Shanghai
- Destination Port: Los Angeles
- Cargo Description: Electronics and computer accessories
- Container Type: 40HQ
- Number of Containers: 2
- Expected Departure Date: 2024-02-01

**Agent Validation & Submission:**
All fields are valid. Submitting booking...
✅ Booking submitted successfully! Your booking reference is BK123456789.

## Example 2: Invalid Data Handling

**Customer Provides:**
- Container Type: 30GP (invalid)

**Agent Response:**
❌ Validation error: Container type must be one of: 20GP, 40GP, 40HQ, 45HQ
Please correct the container type and resubmit.

## Example 3: Booking Status Query

**Customer Request:**
"What's the status of my booking with BOL number ABC12345?"

**Agent Response:**
🔍 Checking status for BOL number ABC12345...

**Status Result:**
- **Status**: Booking Confirmed
- **Vessel**: MV Ocean Star
- **Voyage**: V1234
- **ETD**: 2024-02-01
- **ETA**: 2024-02-15

Your booking is confirmed and scheduled for departure on February 1st, 2024.
