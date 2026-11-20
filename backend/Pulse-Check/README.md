# Pulse-Check API ("Watchdog" Sentinel)

A backend service designed for CritMon Servers Inc. to monitor remote devices. If a device fails to send a heartbeat before its timer expires, the system triggers a critical alert.

## 1. Architecture Diagram
The following sequence diagram shows the flow of a device registering, sending heartbeats, and the system firing an alert if the timer expires.

```mermaid
sequenceDiagram
    participant Device
    participant API
    participant Timer
    participant Log

    Device->>API: POST /monitors (id, timeout)
    API->>Timer: Start Timer (e.g., 60s)
    API-->>Device: 201 Created

    loop Heartbeat
        Device->>API: POST /monitors/{id}/heartbeat
        API->>Timer: Reset Timer
        API-->>Device: 200 OK
    end

    Note over Timer: Timer reaches 0
    Timer->>Log: Fire Alert (Device is down!)
    Timer->>API: Update status to 'down'

    Device->>API: POST /monitors/{id}/pause
    API->>Timer: Cancel Timer
    API-->>Device: 200 OK (No alerts will fire)