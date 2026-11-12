import pyotp
import requests

SECRET = "JBSWY3DPEHPK3PXP"
totp = pyotp.TOTP(SECRET)
current_code = totp.now()

print(f"Código TOTP generado: {current_code}")

payload = {
    "employee_id": "EMP-9482",
    "event_type": "CHECK_IN",
    "timestamp": "2026-11-11T12:00:00Z",
    "totp_code": current_code,
    "location": {
        "latitude": 40.416775,
        "longitude": -3.703790
    }
}

response = requests.post("http://localhost:8000/api/v1/check-in", json=payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")