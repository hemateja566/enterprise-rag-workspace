# Personal Protective Equipment (PPE) Detection

Jupyter Notebook project for detecting Personal Protective Equipment using computer vision and machine learning.

## Overview

This project implements PPE detection (helmets, vests, masks, gloves, etc.) using object detection models. Designed for workplace safety monitoring and compliance verification.

## Features

- Real-time PPE detection from video/image streams
- Multiple PPE class detection (helmet, vest, mask, gloves, boots)
- Compliance reporting
- Configurable confidence thresholds
- Export detection results

## Project Structure

```
personel-protective-equipment/
├── ppe_detection.ipynb       # Main Jupyter notebook
├── models/                   # Trained model weights
├── data/                     # Training/validation datasets
├── utils/                    # Helper functions
├── requirements.txt          # Python dependencies
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.8+
- Jupyter Notebook/Lab
- CUDA-compatible GPU (recommended)

### Installation

```bash
# Clone repository
git clone https://github.com/hemateja566/personel-protective-equipment.git
cd personel-protective-equipment

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch Jupyter
jupyter notebook ppe_detection.ipynb
```

## Dependencies

```
torch torchvision
opencv-python
numpy pandas matplotlib
ultralytics (YOLOv8)
jupyter
```

## Usage

1. Open the notebook in Jupyter
2. Configure model path and input source
3. Run cells sequentially
4. Adjust confidence thresholds as needed
5. Export results

## Model

Based on YOLOv8 architecture fine-tuned on PPE dataset.

### Supported PPE Classes

- Hard Hat / Helmet
- Safety Vest
- Face Mask
- Safety Gloves
- Safety Boots
- Eye Protection

## Data

Training data should be organized in YOLO format:
```
data/
├── train/
│   ├── images/
│   └── labels/
├── val/
│   ├── images/
│   └── labels/
└── data.yaml
```

## Results

Detection results include:
- Bounding boxes with class labels
- Confidence scores
- Compliance status per person
- Summary statistics

## Future Improvements

- [ ] Real-time video stream processing
- [ ] Integration with CCTV systems
- [ ] Automated compliance reports
- [ ] Mobile deployment
- [ ] Multi-camera support

## License

MIT License