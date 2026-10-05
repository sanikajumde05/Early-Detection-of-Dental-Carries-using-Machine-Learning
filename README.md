🦷 Early Detection of Dental Caries Using Deep Learning

A deep learning-based dental caries detection system that uses YOLOv8 object detection to identify potential dental caries from intraoral images. The project aims to provide AI-assisted visual analysis for early detection and diagnostic support.

📌 Project Overview

Dental caries (tooth decay) is one of the most common oral health problems. Early identification can help in timely diagnosis and treatment.

This project uses YOLOv8 to detect carious regions in dental/intraoral images. The model processes an input image, identifies the relevant region, and returns bounding boxes with confidence scores.

Key Features
🦷 Dental caries detection from intraoral images
🤖 YOLOv8-based object detection
📊 Model evaluation using Precision, Recall, and mAP
🔄 Transfer learning using pretrained YOLOv8 weights
🖼️ Image annotation and dataset preprocessing
🌐 Web-based interface for real-time detection
🛠️ Tech Stack
Technology	Purpose
Python	Model development and preprocessing
YOLOv8	Dental caries object detection
PyTorch	Deep learning framework
OpenCV	Image processing
Ultralytics	YOLOv8 implementation
HTML/CSS/JavaScript	Web interface
🔬 Methodology

The overall workflow is:

Dental/Intraoral Image
        ↓
Dataset Preparation
        ↓
Image Annotation
        ↓
Data Preprocessing
        ↓
YOLOv8 Model
        ↓
Transfer Learning
        ↓
Model Training
        ↓
Model Evaluation
        ↓
Caries Detection
        ↓
Bounding Boxes + Confidence Score
🧠 Model

The project uses YOLOv8 for object detection.

YOLO (You Only Look Once) performs object detection by predicting the location and class of objects directly from an image.

Why YOLOv8?
Real-time object detection
Good balance between speed and accuracy
Suitable for image-based medical/dental applications
Supports transfer learning with pretrained weights
Provides bounding-box predictions and confidence scores
📂 Dataset Preparation

The dataset consists of dental/intraoral images containing examples of dental caries.

The preparation process includes:

Collecting dental images
Annotating carious regions
Converting annotations into YOLO format
Organizing images into training and validation sets
Creating the YOLO dataset configuration
Applying preprocessing and augmentation during training
YOLO Annotation Format

Each object annotation follows:

class_id center_x center_y width height

The coordinates are normalized between 0 and 1.

🚀 Model Training

The YOLOv8 model is trained using transfer learning from pretrained weights.

Example:

from ultralytics import YOLO

model = YOLO("yolov8m.pt")

model.train(
    data="data.yaml",
    epochs=20,
    imgsz=640,
    batch=16
)

Training parameters can be modified according to the available dataset and hardware.

📊 Evaluation

The model is evaluated using standard object-detection metrics:

Precision

Measures how many predicted positive detections are actually correct.

Recall

Measures how many actual positive instances are successfully detected.

mAP

Mean Average Precision (mAP) evaluates the overall object detection performance by considering precision-recall relationships.

The project uses these metrics to evaluate the effectiveness of the trained YOLOv8 model.

🌐 Web Interface

A web-based interface was developed to allow users to upload an intraoral image and obtain AI-assisted detection results.

Upload Image
     ↓
YOLOv8 Model
     ↓
Detect Caries
     ↓
Display Bounding Boxes
     ↓
Show Confidence Score
📁 Project Structure
Dental-Caries-Detection/
│
├── dataset/
│   ├── images/
│   │   ├── train/
│   │   └── val/
│   │
│   └── labels/
│       ├── train/
│       └── val/
│
├── models/
│   └── best.pt
│
├── notebooks/
│   └── training.ipynb
│
├── app/
│   └── app.py
│
├── data.yaml
├── requirements.txt
├── README.md
└── .gitignore
⚙️ Installation

Clone the repository:

git clone https://github.com/your-username/dental-caries-detection.git
cd dental-caries-detection

Create a virtual environment:

python -m venv venv

Activate it:

Windows
venv\Scripts\activate
macOS/Linux
source venv/bin/activate

Install dependencies:

pip install -r requirements.txt
▶️ Running the Model

To perform prediction on an image:

from ultralytics import YOLO

model = YOLO("models/best.pt")

results = model.predict(
    source="test_image.jpg",
    save=True,
    conf=0.25
)

The output contains detected regions along with their confidence scores.

💡 Applications
AI-assisted dental screening
Early identification of potential caries
Computer-aided dental diagnosis
Dental image analysis
Research in AI-based healthcare systems
⚠️ Limitations
Detection performance depends on image quality and dataset diversity.
Variations in lighting and image angles can affect predictions.
The system is intended as diagnostic support, not as a replacement for professional dental examination.
Further clinical validation is required before real-world medical deployment.
🔮 Future Scope
Expand the dataset with more diverse dental images
Improve detection accuracy through larger-scale training
Detect multiple types/stages of dental conditions
Integrate the system with dental record platforms
Develop a mobile-based dental screening application
Explore explainable AI for more interpretable predictions
👩‍💻 Author

Sanika Jumde
B.Tech – Computer Science Engineering
Symbiosis Institute of Technology, Nagpur

📜 License

This project is developed for academic and research purposes.
