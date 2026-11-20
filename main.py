from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import threading

app = FastAPI()

# database to store the monitors
# Format: {"device-123": {"timeout": 60, "status": "up", "timer": <TimerObject>}}
monitors_db = {}


class MonitorCreate(BaseModel):
    id: str
    timeout: int
    alert_email: str

# The function that fires when the timer reaches 0
def trigger_alert(device_id: str):
    # Check if the device exists and if it's still 'up' (not paused)
    if device_id in monitors_db and monitors_db[device_id]["status"] == "up":
        monitors_db[device_id]["status"] = "down"
        
        # Log the JSON alert as requested in the README
        alert_data = {
            "ALERT": f"Device {device_id} is down!",
            "time": datetime.now().isoformat()
        }
        print(alert_data) # In a real app, you'd send an email or webhook here

# Helper function to start/reset a timer
def start_timer(device_id: str, timeout: int):
    # Cancel the old timer if it exists
    if "timer" in monitors_db[device_id] and monitors_db[device_id]["timer"] is not None:
        monitors_db[device_id]["timer"].cancel()
    
    # Create and start a new background timer
    new_timer = threading.Timer(timeout, trigger_alert, args=[device_id])
    monitors_db[device_id]["timer"] = new_timer
    new_timer.start()

# ENDPOINTS 

@app.post("/monitors", status_code=201)
def create_monitor(monitor: MonitorCreate):
    if monitor.id in monitors_db:
        raise HTTPException(status_code=400, detail="Monitor already exists")
    
    # Save to database
    monitors_db[monitor.id] = {
        "timeout": monitor.timeout,
        "alert_email": monitor.alert_email,
        "status": "up",
        "timer": None
    }
    
    # Start the countdown
    start_timer(monitor.id, monitor.timeout)
    
    return {"message": f"Monitor created for {monitor.id} with {monitor.timeout}s timeout."}

@app.post("/monitors/{device_id}/heartbeat")
def heartbeat(device_id: str):
    if device_id not in monitors_db:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    # Reset the status to 'up' (in case it was paused) and reset the timer
    monitors_db[device_id]["status"] = "up"
    timeout = monitors_db[device_id]["timeout"]
    start_timer(device_id, timeout)
    
    return {"message": f"Heartbeat received for {device_id}. Timer reset."}
@app.post("/monitors/{device_id}/pause")
def pause_monitor(device_id: str):
    if device_id not in monitors_db:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    # Change status to paused
    monitors_db[device_id]["status"] = "paused"
    
    # Cancel the active timer completely
    if monitors_db[device_id]["timer"]:
        monitors_db[device_id]["timer"].cancel()
        monitors_db[device_id]["timer"] = None
        
    return {"message": f"Monitor {device_id} paused. No alerts will fire."}