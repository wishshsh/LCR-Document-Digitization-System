# Local Civil Registry Document Digitization and Data Extraction

## Using CRNN+CTC, Multinomial Naive Bayes, and Named Entity Recognition

**Thesis Project by:**
- Shane Mark C. Blanco
- Princess A. Pasamonte  
- Irish Faith G. Ramirez

**Institution:** Tarlac State University, College of Computer Studies

---

## 📋 Project Overview

This system automates the digitization and data extraction of Philippine Civil Registry documents using advanced machine learning algorithms:

### Target Documents:
- **Form 1A** - Birth Certificate
- **Form 2A** - Death Certificate
- **Form 3A** - Marriage Certificate
- **Form 90** - Application of Marriage License

### Key Features:
✅ OCR for printed and handwritten text  
✅ Automatic document classification  
✅ Named entity extraction (names, dates, places)  
✅ Auto-fill digital forms  
✅ MySQL database storage  
✅ Searchable digital archive  
✅ Data visualization dashboard  

---

## 🏗️ System Architecture

```
Input: Scanned Civil Registry Form
    ↓
1. Image Preprocessing
    ↓
2. CRNN+CTC → Text Recognition
    ↓
3. Multinomial Naive Bayes → Document Classification
    ↓
4. spaCy NER → Entity Extraction
    ↓
5. Data Validation & Storage → MySQL Database
    ↓
Output: Digitized & Searchable Record
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- CUDA-capable GPU (recommended) or CPU
- 8GB RAM minimum

### Installation

```bash
# 1. Clone or download the project
cd civil_registry_ocr

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download spaCy model
python -m spacy download en_core_web_sm
```

### Quick Test

```python
from inference import CivilRegistryOCR

# Load model
ocr = CivilRegistryOCR('checkpoints/best_model.pth')

# Recognize text
text = ocr.predict('test_images/sample_name.jpg')
print(f"Recognized: {text}")
```

---

## 📁 Project Files

### Core Implementation Files:

1. **crnn_model.py** - CRNN+CTC neural network architecture
2. **dataset.py** - Data loading and preprocessing  
3. **train.py** - Model training script
4. **inference.py** - Prediction and inference
5. **utils.py** - Helper functions and metrics
6. **requirements.txt** - Python dependencies
7. **IMPLEMENTATION_GUIDE.md** - Detailed implementation guide

### Additional Components (To be created):

8. **document_classifier.py** - Multinomial Naive Bayes classifier
9. **ner_extractor.py** - Named Entity Recognition
10. **web_app.py** - Web application (Flask/FastAPI)
11. **database.py** - MySQL integration

---

## 📊 Training the Model

### 1. Prepare Your Data

Organize images and labels:
```
data/
  train/
    form1a/
      name_001.jpg
      name_001.txt
    form2a/
      ...
  val/
    ...
```

### 2. Create Annotations

```python
from dataset import create_annotation_file

create_annotation_file('data/train', 'data/train_annotations.json')
create_annotation_file('data/val', 'data/val_annotations.json')
```

### 3. Train Model

```bash
python train.py
```

Monitor metrics:
- Character Error Rate (CER)
- Word Error Rate (WER)  
- Training/Validation Loss

### 4. Evaluate

```python
from utils import calculate_cer, calculate_wer

predictions = [ocr.predict(img) for img in test_images]
cer = calculate_cer(predictions, ground_truths)
print(f"CER: {cer:.2f}%")
```

---

## 🌐 Web Application

### Start the Server

```bash
python web_app.py
```

### API Endpoints

**POST /api/ocr** - Process document
```bash
curl -X POST -F "file=@birth_cert.jpg" http://localhost:8000/api/ocr
```

**Response:**
```json
{
  "text": "Juan Dela Cruz\n01/15/1990\nTarlac City",
  "form_type": "form1a",
  "entities": {
    "persons": ["Juan Dela Cruz"],
    "dates": ["01/15/1990"],
    "locations": ["Tarlac City"]
  }
}
```

---

## 🎯 Expected Performance

Based on thesis objectives:

### CRNN+CTC Model:
- **Target CER:** < 5%
- **Target Accuracy:** > 95%
- Handles both printed and handwritten text

### Document Classifier (MNB):
- **Target Accuracy:** > 90%
- Fast classification (< 100ms)

### NER (spaCy):
- **F1 Score:** > 85%
- Extracts: Names, Dates, Places

---

## 🧪 Testing

### ISO 25010 Evaluation

**Usability Testing:**
```python
# Metrics to measure:
- Task completion rate
- Average time per task
- User satisfaction score (SUS)
```

**Reliability Testing:**
```python
# Metrics to measure:
- System uptime %
- Error rate
- Recovery time
```

### Confusion Matrix

```python
from sklearn.metrics import confusion_matrix
import seaborn as sns

cm = confusion_matrix(true_labels, predicted_labels)
sns.heatmap(cm, annot=True)
```

---

## 💾 Database Schema

### Birth Certificates Table
```sql
CREATE TABLE birth_certificates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    child_name VARCHAR(255),
    date_of_birth DATE,
    place_of_birth VARCHAR(255),
    sex CHAR(1),
    father_name VARCHAR(255),
    mother_name VARCHAR(255),
    raw_text TEXT,
    form_image LONGBLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📈 System Requirements

### Minimum:
- CPU: Intel i5 or equivalent
- RAM: 8GB
- Storage: 10GB
- OS: Windows 10, Ubuntu 18.04, macOS 10.14

### Recommended:
- CPU: Intel i7 or equivalent
- GPU: NVIDIA GTX 1060 or better
- RAM: 16GB
- Storage: 50GB SSD

---

## 🔒 Data Privacy & Security

Following Philippine Data Privacy Act (RA 10173):

- ✅ Encrypted data transmission
- ✅ Access control and authentication
- ✅ Audit logging
- ✅ Regular security updates
- ✅ Data retention policies

---

## 📚 Key Algorithms

### 1. CRNN+CTC
**Purpose:** Text recognition from images  
**Strengths:** Handles variable-length sequences, no character segmentation needed  
**Reference:** Shi et al. (2016)

### 2. Multinomial Naive Bayes
**Purpose:** Document classification  
**Strengths:** Fast, efficient, works well with text data  
**Reference:** McCallum & Nigam (1998)

### 3. Named Entity Recognition
**Purpose:** Extract entities (names, dates, places)  
**Strengths:** Pre-trained, accurate, easy to use  
**Reference:** spaCy (Honnibal & Montani, 2017)

---

## 🛠️ Troubleshooting

### Low Accuracy?
1. Increase training data (target: 10,000+ samples)
2. Use data augmentation
3. Train longer (100+ epochs)
4. Clean your dataset

### Out of Memory?
1. Reduce batch size
2. Use smaller image dimensions
3. Use gradient accumulation
4. Enable mixed precision

### Slow Inference?
1. Use GPU if available
2. Batch process images
3. Optimize model (ONNX)
4. Cache frequent results

---

## 📖 Documentation

- **IMPLEMENTATION_GUIDE.md** - Complete step-by-step guide
- **API_DOCUMENTATION.md** - API reference (to be created)
- **USER_MANUAL.md** - End-user guide (to be created)

---

## 🎓 Academic References

### Key Papers:

1. **CRNN**  
   Shi, B., Bai, X., & Yao, C. (2016). An end-to-end trainable neural network for image-based sequence recognition and its application to scene text recognition. *IEEE TPAMI*.

2. **CTC Loss**  
   Graves, A., et al. (2006). Connectionist temporal classification: Labelling unsegmented sequence data with recurrent neural networks. *ICML*.

3. **Naive Bayes**  
   McCallum, A., & Nigam, K. (1998). A comparison of event models for naive bayes text classification. *AAAI Workshop*.

4. **spaCy**  
   Honnibal, M., & Montani, I. (2017). spaCy 2: Natural language understanding with Bloom embeddings, convolutional neural networks and incremental parsing.

---

## 👥 Contributors

**Researchers:**
- Shane Mark C. Blanco
- Princess A. Pasamonte
- Irish Faith G. Ramirez

**Advisers:**
- Mr. Rengel V. Corpuz (Technical Adviser)
- Mr. Joselito T. Tan (Subject Teacher)

**Institution:**  
Tarlac State University  
College of Computer Studies  
Bachelor of Science in Computer Science

---

## 📞 Support

For questions regarding this implementation:

1. Review IMPLEMENTATION_GUIDE.md
2. Check code documentation
3. Consult with thesis advisers

---

## 📄 License

This project is for academic purposes as part of a thesis requirement.

---

## ✅ Implementation Checklist

### Phase 1: Setup ✓
- [x] Install dependencies
- [x] Set up project structure
- [x] Prepare development environment

### Phase 2: Data Preparation
- [ ] Collect civil registry form images
- [ ] Create annotations
- [ ] Split into train/val/test sets

### Phase 3: Model Development
- [ ] Train CRNN+CTC model
- [ ] Train document classifier
- [ ] Integrate NER system

### Phase 4: Web Application
- [ ] Develop Flask/FastAPI backend
- [ ] Create frontend interface
- [ ] Implement database integration

### Phase 5: Testing
- [ ] Accuracy testing
- [ ] Black-box testing
- [ ] ISO 25010 evaluation
- [ ] User acceptance testing

### Phase 6: Deployment
- [ ] Optimize for production
- [ ] Set up server
- [ ] Deploy application
- [ ] Monitor performance

---

## 🎯 Success Metrics

Target metrics for thesis evaluation:

| Metric | Target | Status |
|--------|--------|--------|
| OCR Accuracy | > 95% | Pending |
| CER | < 5% | Pending |
| Classifier Accuracy | > 90% | Pending |
| NER F1 Score | > 85% | Pending |
| Response Time | < 2s | Pending |
| System Uptime | > 99% | Pending |

---

**Good luck with your thesis defense! 🎓✨**

For detailed implementation instructions, see **IMPLEMENTATION_GUIDE.md**
