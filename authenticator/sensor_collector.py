import numpy as np
import time
from read_sensor_data import read_sensor_data

class SensorCollector:
    def __init__(self, duration=4, target_hz=40):
        """
        duration: 4 seconds
        target_hz: 40Hz sampling rate → 160 datapoints total
        """
        self.duration = duration
        self.target_hz = target_hz
        self.target_points = duration * target_hz  # 160
        
    def collect_raw_data(self):
        """
        Collect accelerometer data for 4 seconds at raw rate.
        Returns: list of [accel_x, accel_y] readings
        """
        start_time = time.time()
        raw_data = []
        
        while time.time() - start_time < self.duration:
            accel, _ = read_sensor_data()
            raw_data.append([accel['x'], accel['y']])
            # Small sleep to prevent CPU spinning
            time.sleep(0.01)
        
        return np.array(raw_data)  # Shape: (N, 2)
    
    def resample_to_target_hz(self, raw_data):
        """
        Downsample/average raw data to 40Hz (160 points).
        """
        if len(raw_data) == 0:
            return np.array([])
        
        # Calculate chunk size for averaging
        chunk_size = len(raw_data) / self.target_points
        resampled = []
        
        for i in range(self.target_points):
            start_idx = int(i * chunk_size)
            end_idx = int((i + 1) * chunk_size)
            chunk = raw_data[start_idx:end_idx]
            
            if len(chunk) > 0:
                # Average the chunk
                avg_x = np.mean(chunk[:, 0])
                avg_y = np.mean(chunk[:, 1])
                resampled.append([avg_x, avg_y])
        
        return np.array(resampled)  # Shape: (160, 2)
    
    def collect_gesture(self, countdown=3):
        """
        Collect one gesture reading with countdown.
        """
        print(f"\nGet ready to draw your gesture...")
        for i in range(countdown, 0, -1):
            print(f"Starting in {i}...", end='\r')
            time.sleep(1)
        
        print("\n🔴 Recording... (4 seconds)")
        raw_data = self.collect_raw_data()
        resampled = self.resample_to_target_hz(raw_data)
        print(f"✅ Recording complete! Collected {len(resampled)} datapoints")
        
        return resampled  # Shape: (160, 2)
