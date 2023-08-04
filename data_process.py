import subprocess

def run_yolov5_detection(weights_path, video_path):
    # Command to run YOLOv5 detection
    command = f"python detect.py --weights {weights_path} --img 640 --conf 0.25 --source {video_path}"
                
    # Execute the command using subprocess
    subprocess.run('python detect.py --weights weights/yolov5x.pt --img 640 --conf 0.25 --source /Users/vishruthbharadwaj/Desktop/flasexample/clips/football_goal.mp4', shell=True)

if __name__ == "__main__":
    weights_path = "weights/yolov5x.pt"
    video_path = "/Users/vishruthbharadwaj/Desktop/flasexample/clips/football_goal.mp4"
    run_yolov5_detection(weights_path, video_path)
