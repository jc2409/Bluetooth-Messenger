# Installation Guide

## 📦 Prerequisites

- Python 3.7+
- pip (Python package manager)
- MPU6050 sensor connected via I2C (address 0x68)

## ⚡ Quick Install

### 1. Install Dependencies

Navigate to the authenticator folder and install all required packages:

```bash
cd authenticator
pip install -r requirements.txt
```

Or install individually:

```bash
pip install numpy>=1.21.0
pip install dtaidistance>=2.3.0
pip install hmmlearn>=0.2.7
pip install scikit-learn>=1.0.0
pip install mpu6050-datasheet>=0.1.0
```

### 2. Verify Installation

Test that everything is installed correctly:

```bash
python -c "import numpy, dtaidistance, hmmlearn, sklearn, mpu6050; print('✅ All imports successful!')"
```

### 3. Check I2C Connection

Verify your MPU6050 sensor is connected:

```bash
python -c "from mpu6050 import mpu6050; sensor = mpu6050(0x68); print(sensor.get_accel_data())"
```

If you see acceleration data, your sensor is connected! ✅

## 📋 Dependencies Explained

| Package | Purpose | Version |
|---------|---------|---------|
| **numpy** | Array manipulation | ≥1.21.0 |
| **dtaidistance** | DTW algorithm (fast C implementation) | ≥2.3.0 |
| **hmmlearn** | Hidden Markov Models | ≥0.2.7 |
| **scikit-learn** | Required by hmmlearn | ≥1.0.0 |
| **mpu6050-datasheet** | MPU6050 sensor interface | ≥0.1.0 |

## 🐛 Troubleshooting Installation

### ImportError: No module named 'dtaidistance'

Make sure you installed from requirements.txt:
```bash
pip install -r requirements.txt
```

### ImportError: No module named 'mpu6050'

Check that you have the correct package:
```bash
pip install mpu6050-datasheet
```

Not `mpu6050` - must be `mpu6050-datasheet`.

### I2C Connection Issues

If sensor read fails, check:

1. **I2C is enabled on Raspberry Pi:**
   ```bash
   sudo raspi-config
   # Enable I2C: Interface Options → I2C
   ```

2. **Sensor is on address 0x68:**
   ```bash
   sudo i2cdetect -y 1
   # Should show "68" somewhere in the output
   ```

3. **Connection is secure:**
   - SDA → GPIO 2 (Pin 3)
   - SCL → GPIO 3 (Pin 5)
   - GND → Ground (Pin 6, 9, 14, 20, 25, 30, 34, 39)
   - VCC → 3.3V (Pin 1 or 17) - **NOT 5V!**

### Windows/Mac Users

If you don't have an actual MPU6050 sensor:
- The code will fail on sensor reads
- You can test the gesture algorithms separately
- For full testing, use a Raspberry Pi with attached sensor

## 🚀 First Run

After installation, test the system:

```bash
# Generate a gesture
python test_generation.py

# Authenticate
python authenticate_gesture.py
```

## 📊 System Requirements

**Minimum:**
- Python 3.7
- 50 MB disk space
- 100 MB RAM

**Recommended:**
- Python 3.9+
- 200 MB disk space
- 512 MB RAM

## 🔧 Virtual Environment (Optional but Recommended)

To isolate dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

## ✅ Verification Checklist

After installation, verify:

- [ ] Python 3.7+ installed: `python --version`
- [ ] All packages installed: `pip list`
- [ ] Imports work: See "Verify Installation" above
- [ ] Sensor accessible: See "Check I2C Connection" above
- [ ] Can run: `python test_generation.py`

## 🎉 Ready to Go!

Once all packages are installed and verified, you're ready to use the gesture authentication system!

```bash
python test_generation.py   # Generate a gesture
python authenticate_gesture.py  # Test authentication
```

---

**Need help?** Check `README_START_HERE.md` for usage instructions.

