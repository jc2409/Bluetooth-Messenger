from mpu6050 import mpu6050
from time import sleep
import numpy as np
from dtaidistance import dtw

sensor = mpu6050(0x68)

def read_sensor_data():
    accel_data = sensor.get_accel_data()
    gyro_data = sensor.get_gyro_data()
    return accel_data, gyro_data

def authenticator(gesture_a, gesture_g, ref_a, ref_g, thresh_a_SVM, thresh_g_SVM, thresh_a_p, thresh_g_p):
    """
    Authentication function.

    We use a correlation (p) and signal vector magnitude (SVM) thresholding.

    Args:
        gesture_a: A T * 3 array. T is the sample count. Represents acceleration data for gesture.
        gesture_g: A T * 3 array. T is the sample count. Represents gyroscopic data for gesture.
        ref_a: A N * T * 3 array. N is the number of reference gestures, T is the sample count.
               Represents acceleration data for the reference gestures.
        ref_g:A N * T * 3 array. N is the number of reference gestures, T is the sample count.
               Represents gyroscopic data for the reference gestures.

    Return:
        isValid: bool indicating whether the gestures match or not.
    """
    isValidArr = np.zeros(ref_a.shape[0])

    g_a_SVM = np.mean(np.sqrt(np.sum(gesture_a**2, axis=1)))
    g_g_SVM = np.mean(np.sqrt(np.sum(gesture_g**2, axis=1)))

    g_a_mean = np.mean(gesture_a, axis=0)
    g_g_mean = np.mean(gesture_g, axis=0)

    g_a_var = np.mean((gesture_a - g_a_mean)**2, axis=0)
    g_g_var = np.mean((gesture_g - g_g_mean)**2, axis=0)

    for i in range(ref_a.shape[0]):
        r_a_mean = np.mean(ref_a[i], axis=0)
        r_g_mean = np.mean(ref_g[i], axis=0)

        r_a_var = np.mean((ref_a[i] - r_a_mean)**2, axis=0)
        r_g_var = np.mean((ref_g[i] - r_g_mean)**2, axis=0)

        cov_a = np.mean((ref_a[i] - r_a_mean) * (gesture_a - g_a_mean), axis=0)
        cov_g = np.mean((ref_g[i] - r_g_mean) * (gesture_g - g_g_mean), axis=0)

        p_a = np.mean(cov_a / np.sqrt(g_a_var * r_a_var))
        p_g = np.mean(cov_g / np.sqrt(g_g_var * r_g_var))

        isValidArr[i] = (p_a > thresh_a_p) and (p_g > thresh_g_p) and (g_a_SVM > thresh_a_SVM) and (g_g_SVM > thresh_g_SVM)

    r_a_mean = np.mean(ref_a, axis=1)
    r_g_mean = np.mean(ref_g, axis=1)

    r_a_var = np.mean((ref_a - r_a_mean)**2, axis=1)
    r_g_var = np.mean((ref_g - r_g_mean)**2, axis=1)

    cov_a = np.mean((ref_a - r_a_mean) * (gesture_a - g_a_mean), axis=1)
    cov_g = np.mean((ref_g - r_g_mean) * (gesture_g - g_g_mean), axis=1)

    p_a = np.mean(cov_a / np.sqrt(g_a_var * r_a_var), axis=1)
    p_g = np.mean(cov_g / np.sqrt(g_g_var * r_g_var), axis=1)


    return np.sum(isValidArr) > 1












    