# Early Detection of Dental Caries Using Deep Learning

## 📌 Overview

This project focuses on the early detection of dental caries using deep learning and computer vision. A YOLOv8-based object detection model is used to identify potential carious regions from intraoral dental images.

The system is designed to provide AI-assisted visual analysis that can support early identification of dental caries.

## 🎯 Objectives

- Detect dental caries from intraoral images.
- Apply deep learning for automated dental image analysis.
- Use YOLOv8 for accurate object detection.
- Evaluate the model using Precision, Recall, and mAP.
- Develop a web-based interface for real-time detection.

## 🛠️ Technologies Used

- Python
- YOLOv8
- PyTorch
- Ultralytics
- OpenCV
- HTML
- CSS
- JavaScript

## 🔬 Methodology

The project follows the following workflow:

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
Dental Caries Detection  
↓  
Bounding Boxes + Confidence Score

## 🧠 YOLOv8 Model

YOLOv8 is used as the object detection model to identify carious regions in dental images.

The model was trained using transfer learning with pretrained YOLOv8 weights. This allows the model to leverage previously learned visual features and adapt them to the dental caries detection task.

### Training Configuration

- Model: YOLOv8m
- Image Size: 640 × 640
- Epochs: 20
- Batch Size: 16
- Optimizer: Adam
- Pretrained Weights: COCO

## 📊 Evaluation Metrics

The model performance is evaluated using:

### Precision
Measures the proportion of predicted caries detections that are actually correct.

### Recall
Measures the proportion of actual caries instances that are successfully detected.

### mAP
Mean Average Precision is used to evaluate the overall object detection performance of the model.

## 📂 Dataset Preparation

The dataset consists of dental/intraoral images used for training and evaluating the object detection model.

The dataset preparation process includes:

1. Collecting dental images.
2. Annotating carious regions.
3. Converting annotations into YOLO format.
4. Organizing images into training and validation datasets.
5. Creating the YOLO dataset configuration file.
6. Preprocessing images before model training.

### YOLO Annotation Format

Each object annotation follows the format:

```text
class_id center_x center_y width height
