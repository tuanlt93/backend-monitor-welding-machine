## Getting Started

First, setup influxdb:
The next, run project
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Note

Read holding register from 0 to 9
Register 4: voltage value
Register 5: ampere value
Value voltage min: 0
Value voltage max: 100
Value ampere min: 0
Value ampere max: 100
Resolution: 65535

## Example

volt_current = (Value voltage max - Value voltage min) / Resolution *  Value of register 4