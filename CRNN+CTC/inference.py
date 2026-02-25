"""
Inference Script for CRNN+CTC Civil Registry OCR
Production-ready implementation for document digitization
"""

import torch
import cv2
import numpy as np
from pathlib import Path
import json
from typing import Dict, List, Tuple

from crnn_model import get_crnn_model
from utils import decode_ctc_predictions, extract_form_fields


class CivilRegistryOCR:
    """
    Production OCR system for Philippine Civil Registry documents
    """
    
    def __init__(self, checkpoint_path, device='cuda'):
        """
        Initialize OCR system
        
        Args:
            checkpoint_path: Path to trained model checkpoint
            device: 'cuda' or 'cpu'
        """
        # Set device
        if device == 'cuda' and not torch.cuda.is_available():
            print("WARNING: CUDA not available, using CPU")
            device = 'cpu'
        
        self.device = torch.device(device)
        
        # Load checkpoint
        print(f"Loading model from {checkpoint_path}...")
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        # Load character mappings
        self.char_to_idx = checkpoint['char_to_idx']
        self.idx_to_char = checkpoint['idx_to_char']
        self.config = checkpoint.get('config', {})
        
        # Create model
        self.model = get_crnn_model(
            model_type=self.config.get('model_type', 'standard'),
            img_height=self.config.get('img_height', 64),
            num_chars=len(self.char_to_idx),
            hidden_size=self.config.get('hidden_size', 256),
            num_lstm_layers=self.config.get('num_lstm_layers', 2)
        )
        
        # Load weights
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model = self.model.to(self.device)
        self.model.eval()
        
        print(f"Model loaded successfully") 
        print(f"  Val CER: {checkpoint.get('val_cer', 0):.2f}%")
        print(f"  Device: {self.device}")
    
    def preprocess_image(self, image_path, target_height=64, target_width=400):
        """
        Preprocess image for OCR
        
        Args:
            image_path: Path to image file
            target_height: Target image height
            target_width: Target image width
            
        Returns:
            Preprocessed image tensor
        """
        # Read image
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        # Denoise
        img = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)
        
        # Adaptive thresholding
        img = cv2.adaptiveThreshold(
            img, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )
        
        # Resize
        img = cv2.resize(img, (target_width, target_height))
        
        # Normalize
        img = img.astype(np.float32) / 255.0
        
        # Convert to tensor [1, 1, H, W]
        img = torch.FloatTensor(img).unsqueeze(0).unsqueeze(0)
        
        return img
    
    def predict(self, image_path, decode_method='greedy'):
        """
        Predict text from image
        
        Args:
            image_path: Path to image file
            decode_method: 'greedy' or 'beam_search'
            
        Returns:
            Recognized text
        """
        # Preprocess
        img = self.preprocess_image(image_path)
        img = img.to(self.device)
        
        # Inference
        with torch.no_grad():
            outputs = self.model(img)
            decoded = decode_ctc_predictions(
                outputs.cpu(),
                self.idx_to_char,
                method=decode_method
            )
        
        return decoded[0]
    
    def predict_batch(self, image_paths, decode_method='greedy'):
        """
        Predict text from multiple images
        
        Args:
            image_paths: List of image paths
            decode_method: 'greedy' or 'beam_search'
            
        Returns:
            List of recognized texts
        """
        results = []
        
        for image_path in image_paths:
            try:
                text = self.predict(image_path, decode_method)
                results.append({
                    'image_path': str(image_path),
                    'text': text,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'image_path': str(image_path),
                    'error': str(e),
                    'success': False
                })
        
        return results
    
    def process_form(self, form_image_path, form_type):
        """
        Process complete civil registry form
        
        Args:
            form_image_path: Path to form image
            form_type: 'form1a', 'form2a', 'form3a', 'form90'
            
        Returns:
            Dictionary of extracted fields
        """
        # This is a simplified version
        # In production, you would:
        # 1. Detect form fields using template matching or object detection
        # 2. Extract each field region
        # 3. Run OCR on each field
        # 4. Post-process and validate
        
        # For now, just recognize the entire form
        text = self.predict(form_image_path)
        
        # Extract fields (simplified)
        fields = extract_form_fields(text, form_type)
        fields['raw_text'] = text
        
        return fields


class FormFieldExtractor:
    """
    Extract specific fields from civil registry forms
    """
    
    def __init__(self, ocr_model: CivilRegistryOCR):
        self.ocr = ocr_model
    
    def extract_form1a_fields(self, form_image_path):
        """
        Extract fields from Form 1A (Birth Certificate)
        
        Expected fields:
        - Child's name
        - Date of birth
        - Place of birth
        - Sex
        - Father's name
        - Mother's name
        """
        # In production, use template matching to locate fields
        # For now, process entire form
        
        text = self.ocr.predict(form_image_path)
        
        # Extract fields using pattern matching or NER
        # This is simplified - in production use spaCy NER
        fields = {
            'form_type': 'Form 1A - Birth Certificate',
            'raw_text': text,
            # Add extracted fields here
            'child_name': '',
            'date_of_birth': '',
            'place_of_birth': '',
            'sex': '',
            'father_name': '',
            'mother_name': ''
        }
        
        return fields
    
    def extract_form2a_fields(self, form_image_path):
        """Extract fields from Form 2A (Death Certificate)"""
        text = self.ocr.predict(form_image_path)
        
        fields = {
            'form_type': 'Form 2A - Death Certificate',
            'raw_text': text,
            'deceased_name': '',
            'date_of_death': '',
            'place_of_death': '',
            'cause_of_death': ''
        }
        
        return fields
    
    def extract_form3a_fields(self, form_image_path):
        """Extract fields from Form 3A (Marriage Certificate)"""
        text = self.ocr.predict(form_image_path)
        
        fields = {
            'form_type': 'Form 3A - Marriage Certificate',
            'raw_text': text,
            'husband_name': '',
            'wife_name': '',
            'date_of_marriage': '',
            'place_of_marriage': ''
        }
        
        return fields
    
    def extract_form90_fields(self, form_image_path):
        """Extract fields from Form 90 (Marriage License Application)"""
        text = self.ocr.predict(form_image_path)
        
        fields = {
            'form_type': 'Form 90 - Marriage License Application',
            'raw_text': text,
            'applicant1_name': '',
            'applicant2_name': '',
            'date_of_application': ''
        }
        
        return fields


def demo_inference():
    """
    Demo function showing how to use the OCR system
    """
    print("=" * 70)
    print("Civil Registry OCR - Demo")
    print("=" * 70)
    
    # Initialize OCR
    ocr = CivilRegistryOCR(
        checkpoint_path='checkpoints/best_model.pth',
        device='cuda'
    )
    
    # Single image prediction
    print("\n1. Single Image Prediction:")
    try:
        text = ocr.predict('test_images/sample_name.jpg')
        print(f"   Recognized text: {text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Batch prediction
    print("\n2. Batch Prediction:")
    image_paths = [
        'test_images/name1.jpg',
        'test_images/date1.jpg',
        'test_images/place1.jpg'
    ]
    
    results = ocr.predict_batch(image_paths)
    for result in results:
        if result['success']:
            print(f"   {result['image_path']}: {result['text']}")
        else:
            print(f"   {result['image_path']}: ERROR - {result['error']}")
    
    # Form processing
    print("\n3. Form Processing:")
    extractor = FormFieldExtractor(ocr)
    
    try:
        fields = extractor.extract_form1a_fields('test_images/form1a_sample.jpg')
        print(f"   Form Type: {fields['form_type']}")
        print(f"   Raw Text: {fields['raw_text'][:100]}...")
    except Exception as e:
        print(f"   Error: {e}")


def create_inference_api():
    """
    Create a simple API wrapper for the OCR system
    Can be integrated with Flask/FastAPI
    """
    
    class OCR_API:
        def __init__(self, checkpoint_path):
            self.ocr = CivilRegistryOCR(checkpoint_path)
            self.extractor = FormFieldExtractor(self.ocr)
        
        def recognize_text(self, image_path):
            """API endpoint: Recognize text from image"""
            return {
                'text': self.ocr.predict(image_path),
                'success': True
            }
        
        def process_birth_certificate(self, image_path):
            """API endpoint: Process birth certificate"""
            return self.extractor.extract_form1a_fields(image_path)
        
        def process_death_certificate(self, image_path):
            """API endpoint: Process death certificate"""
            return self.extractor.extract_form2a_fields(image_path)
        
        def process_marriage_certificate(self, image_path):
            """API endpoint: Process marriage certificate"""
            return self.extractor.extract_form3a_fields(image_path)
        
        def process_marriage_license(self, image_path):
            """API endpoint: Process marriage license application"""
            return self.extractor.extract_form90_fields(image_path)
    
    return OCR_API


if __name__ == "__main__":
    # Run demo
    demo_inference()
