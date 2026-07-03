import json
import matplotlib.pyplot as plt

def get_support_foot(f):
    return 27 if f[27][1] > f[28][1] else 28

def test_integration():
    with open('pose_data.json') as f:
        data = json.load(f)
    frames = data['frames']
    
    # Assuming frames are already smoothed and rigidified, but NOT ground anchored?
    # Wait, pose_data.json ALREADY has ground_anchor applied!
    # I need to run this on the raw data, or just look at the code logic.
    pass

if __name__ == '__main__':
    print("Test ready.")
