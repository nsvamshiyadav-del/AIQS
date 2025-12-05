# backend/aqi_logic.py

# backend/aqi_logic.py

def calculate_aqi(pm25: float, pm10: float) -> float:
    # A simplified AQI calculation logic
    # In reality, this uses complex breakpoints
    aqi_pm25 = (pm25 / 12.0) * 50
    aqi_pm10 = (pm10 / 54.0) * 50
    return max(aqi_pm25, aqi_pm10)

def classify_aqi(aqi_value: float) -> str:
    if aqi_value <= 50: return "Good"
    if aqi_value <= 100: return "Moderate"
    if aqi_value <= 150: return "Unhealthy for Sensitive Groups"
    if aqi_value <= 200: return "Unhealthy"
    if aqi_value <= 300: return "Very Unhealthy"
    return "Hazardous"

def risk_level_from_aqi(aqi_value: float) -> str:
    if aqi_value <= 100: return "Low Risk"
    if aqi_value <= 200: return "Medium Risk"
    return "High Risk"