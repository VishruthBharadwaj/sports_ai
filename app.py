import os
import boto3
import uuid
import subprocess
from flask import Flask, redirect, url_for, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy

ALLOWED_EXTENSIONS = {'mp4'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy()

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(100))
    filename = db.Column(db.String(100))
    bucket = db.Column(db.String(100))
    region = db.Column(db.String(100))

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"

    db.init_app(app)

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            uploaded_file = request.files["file-to-save"]
            if not allowed_file(uploaded_file.filename):
                return "FILE NOT ALLOWED!"

            new_filename = uploaded_file.filename  # Keep the original filename

            bucket_name = "vishruth"
            s3 = boto3.resource("s3", region_name="eu-west-1")
            s3.Bucket(bucket_name).upload_fileobj(uploaded_file, new_filename)

            file = File(original_filename=uploaded_file.filename, filename=new_filename,
                bucket=bucket_name)

            db.session.add(file)
            db.session.commit()

            return redirect(url_for("index"))

        files = File.query.all()

        return render_template("index.html", files=files)

    @app.route("/process", methods=["POST"])
    def process_file():
        # Get the last uploaded file from the database
        file = File.query.order_by(File.id.desc()).first()

        if file is None:
            return jsonify({"message": "No file available for processing."}), 404

        # Download the video from S3
        s3 = boto3.client("s3", region_name=file.region)
        video_path = "/Users/vishruth/Desktop/flasexample/" + file.filename  # Temporary path to store the video
        s3.download_file(file.bucket, file.filename, video_path)

        # Remove any existing folder in yolov5/runs
        runs_folder = "/Users/vishruth/Desktop/flasexample/yolov5/runs"
        if os.path.exists(runs_folder):
            for root, dirs, files in os.walk(runs_folder, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(runs_folder)

        # YOLOv5 detection command
        weights_path = "/Users/vishruth/Desktop/flasexample/yolov5/weights/yolov5x.pt"
        command = f"python3 yolov5/detect.py --weights {weights_path} --img 640 --conf 0.25 --source {video_path}"

        # Execute the command using subprocess
        try:
            subprocess.run(command, shell=True, check=True)
            print('Processed')

            # Find the processed video file in the runs directory
            for root, dirs, files in os.walk(runs_folder):
                for name in files:
                    if name.endswith('.mp4'):
                        processed_video_path = os.path.join(root, name)
                        break

            # Upload the processed video back to S3
            s3.upload_file(processed_video_path, file.bucket, file.filename)

            return jsonify({"message": "File processing completed!"})
        except subprocess.CalledProcessError:
            return jsonify({"message": "File processing failed."}), 500

    
    @app.route("/videodisplay", methods=["GET"])
    def display_video():
        # Get the last uploaded file from the database
        file = File.query.order_by(File.id.desc()).first()
        print('File name is ', file)
        # Generate a signed URL for the processed video to allow public access
        s3 = boto3.client("s3", region_name=file.region)
        signed_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": file.bucket, "Key": file.filename},
            ExpiresIn=3600,  # Set the expiration time for the URL (1 hour in this example)
        )
        print('Signed url is ')
        print(signed_url)
        # Check if the file is an MP4 file
        if file.filename.endswith(".mp4"):
            return render_template("videodisplay.html", signed_url=signed_url)
        else:
            return render_template("videodisplay.html", message="File is not an MP4 file")
    return app
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
