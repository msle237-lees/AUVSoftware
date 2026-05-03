# Hardware Interface

## Controllers:
- Arm = arm
- Display = dis
- Motors = esc
- IMU = imu
- Power Safety = psa
- Torpedo = tor

Two usage patterns are available — pick whichever fits each module better:

**Class-based** (good for long-running modules that hold a connection pool):
```python
from quick_request import AUVClient

client = AUVClient("http://localhost:8000")
client.post("depth", DEPTH=1.23)
latest = client.latest("imu")
```

**Module-level functions** (good for one-off calls or simple scripts):
```python
import quick_request as qr

qr.configure("http://192.168.1.10:8000")   # call once at startup
qr.post("inputs", SURGE=0, SWAY=0, HEAVE=0, ROLL=0, PITCH=0, YAW=0,
         S1=0, S2=0, S3=0, ARM=0)
row  = qr.latest("depth")
page = qr.list_rows("imu", limit=100)
```

A few things worth noting: keys passed to `post()` are automatically uppercased so you can write them in whatever case feels natural in the calling module. All non-2xx responses raise `AUVRequestError` with the status code and body attached, so callers can catch and log specifics. The client reuses a `requests.Session` internally, so connection pooling is handled for free in long-running processes.

