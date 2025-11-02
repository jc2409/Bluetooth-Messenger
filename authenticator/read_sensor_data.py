from mpu6050 import mpu6050
from time import sleep

sensor = mpu6050(0x68)

def read_sensor_data():
    accel_data = sensor.get_accel_data()
    gyro_data = sensor.get_gyro_data()
    return accel_data, gyro_data

if __name__ == "__main__":
    while(True):
        accel, gyro = read_sensor_data()
        print("Accelerometer Data:", accel)
        print("Gyroscope Data:", gyro)