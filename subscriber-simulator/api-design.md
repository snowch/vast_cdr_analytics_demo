# Subscriber Simulator API Design

This document outlines the API design for the Subscriber Simulator, which will interact with VastDB for state management.

## Goals

*   **Scalability**: The API should be designed to handle a large number of concurrent requests, supporting a scalable subscriber simulator.
*   **VastDB Integration**: Seamless integration with VastDB for storing and retrieving subscriber state.
*   **Clear Interface**: Provide a clear and intuitive interface for managing subscriber data.

## API Endpoints

The API will expose the following endpoints:

### 1. Create/Update Subscriber

*   **Endpoint**: `/subscribers`
*   **Method**: `POST`
*   **Description**: Creates a new subscriber or updates an existing one.
*   **Request Body**:
    ```json
    {
        "subscriber_id": "string",
        "status": "active" | "inactive" | "suspended",
        "plan_type": "basic" | "premium" | "enterprise",
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD" (optional),
        "last_activity": "YYYY-MM-DDTHH:MM:SSZ" (ISO 8601 format)
    }
    ```
*   **Response**:
    *   `200 OK`: Subscriber created/updated successfully.
        ```json
        {
            "message": "Subscriber created/updated successfully",
            "subscriber_id": "string"
        }
        ```
    *   `400 Bad Request`: Invalid input.
    *   `500 Internal Server Error`: Server-side error.

### 2. Get Subscriber Details

*   **Endpoint**: `/subscribers/{subscriber_id}`
*   **Method**: `GET`
*   **Description**: Retrieves details for a specific subscriber.
*   **Path Parameters**:
    *   `subscriber_id`: The unique identifier of the subscriber.
*   **Response**:
    *   `200 OK`: Subscriber details.
        ```json
        {
            "subscriber_id": "string",
            "status": "active" | "inactive" | "suspended",
            "plan_type": "basic" | "premium" | "enterprise",
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD" (optional),
            "last_activity": "YYYY-MM-DDTHH:MM:SSZ"
        }
        ```
    *   `404 Not Found`: Subscriber not found.
    *   `500 Internal Server Error`: Server-side error.

### 3. Delete Subscriber

*   **Endpoint**: `/subscribers/{subscriber_id}`
*   **Method**: `DELETE`
*   **Description**: Deletes a subscriber from the system.
*   **Path Parameters**:
    *   `subscriber_id`: The unique identifier of the subscriber to delete.
*   **Response**:
    *   `200 OK`: Subscriber deleted successfully.
        ```json
        {
            "message": "Subscriber deleted successfully",
            "subscriber_id": "string"
        }
        ```
    *   `404 Not Found`: Subscriber not found.
    *   `500 Internal Server Error`: Server-side error.

### 4. List Subscribers

*   **Endpoint**: `/subscribers`
*   **Method**: `GET`
*   **Description**: Lists subscribers with optional filtering and pagination.
*   **Query Parameters**:
    *   `status`: (Optional) Filter by subscriber status (`active`, `inactive`, `suspended`).
    *   `plan_type`: (Optional) Filter by plan type (`basic`, `premium`, `enterprise`).
    *   `limit`: (Optional) Maximum number of subscribers to return (default: 100).
    *   `offset`: (Optional) Number of subscribers to skip (for pagination).
*   **Response**:
    *   `200 OK`: List of subscribers.
        ```json
        {
            "subscribers": [
                {
                    "subscriber_id": "string",
                    "status": "active" | "inactive" | "suspended",
                    "plan_type": "basic" | "premium" | "enterprise",
                    "start_date": "YYYY-MM-DD",
                    "end_date": "YYYY-MM-DD" (optional),
                    "last_activity": "YYYY-MM-DDTHH:MM:SSZ"
                }
            ],
            "total_count": "integer",
            "limit": "integer",
            "offset": "integer"
        }
        ```
    *   `400 Bad Request`: Invalid query parameters.
    *   `500 Internal Server Error`: Server-side error.

### 5. Bulk Load Subscribers

*   **Endpoint**: `/subscribers/bulk`
*   **Method**: `POST`
*   **Description**: Bulk loads multiple subscribers into the system. This is intended for initial setup and large-scale data ingestion.
*   **Request Body**:
    ```json
    [
        {
            "subscriber_id": "string",
            "status": "active" | "inactive" | "suspended",
            "plan_type": "basic" | "premium" | "enterprise",
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD" (optional),
            "last_activity": "YYYY-MM-DDTHH:MM:SSZ"
        },
        {
            "subscriber_id": "string",
            "status": "active" | "inactive" | "suspended",
            "plan_type": "basic" | "premium" | "enterprise",
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD" (optional),
            "last_activity": "YYYY-MM-DDTHH:MM:SSZ"
        }
        // ... more subscriber objects
    ]
    ```
*   **Response**:
    *   `200 OK`: Bulk load initiated successfully.
        ```json
        {
            "message": "Bulk load initiated successfully",
            "records_processed": "integer"
        }
        ```
    *   `400 Bad Request`: Invalid input format or data.
    *   `500 Internal Server Error`: Server-side error during bulk ingestion.

## Data Model (VastDB Table Schema)

The `subscribers` table in VastDB will have the following schema:

| Field Name      | Data Type | Description                               |
| :-------------- | :-------- | :---------------------------------------- |
| `subscriber_id` | `string`  | Unique identifier for the subscriber (Primary Key) |
| `status`        | `string`  | Current status of the subscriber (`active`, `inactive`, `suspended`) |
| `plan_type`     | `string`  | Type of subscription plan (`basic`, `premium`, `enterprise`) |
| `start_date`    | `date`    | Date when the subscription started (YYYY-MM-DD) |
| `end_date`      | `date`    | Date when the subscription ends (YYYY-MM-DD, optional) |
| `last_activity` | `timestamp` | Last activity timestamp (ISO 8601 format) |

## Error Handling

*   **400 Bad Request**: For invalid request payloads or query parameters.
*   **404 Not Found**: When a requested resource (e.g., subscriber_id) does not exist.
*   **500 Internal Server Error**: For unexpected server-side issues, including VastDB connection or operation failures.

## Scalability Considerations

*   **Stateless API**: The API itself will be stateless, relying entirely on VastDB for state persistence. This allows for easy horizontal scaling of the API service.
*   **VastDB Scalability**: VastDB is designed for high-performance and scalability, handling the underlying data storage and retrieval efficiently.
*   **Containerization**: The simulator will be deployed as a containerized application (e.g., Docker, Kubernetes) to leverage orchestration features for scaling and resilience.
*   **Load Balancing**: A load balancer will distribute incoming requests across multiple instances of the subscriber simulator API.
