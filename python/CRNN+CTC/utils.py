"""
Utility Functions for CRNN+CTC Civil Registry OCR
Includes CTC decoding, metrics calculation, and helper functions
"""

import torch
import numpy as np
import editdistance
from typing import List, Dict, Tuple


def decode_ctc_predictions(outputs, idx_to_char, method='greedy'):
    """
    Decode CTC predictions to text
    
    Args:
        outputs: Model outputs [seq_len, batch, num_chars]
        idx_to_char: Dictionary mapping indices to characters
        method: 'greedy' or 'beam_search'
        
    Returns:
        List of decoded strings
    """
    if method == 'greedy':
        return greedy_decode(outputs, idx_to_char)
    elif method == 'beam_search':
        return beam_search_decode(outputs, idx_to_char)
    else:
        raise ValueError(f"Unknown decoding method: {method}")


def greedy_decode(outputs, idx_to_char):
    """
    Greedy CTC decoding - fast but less accurate
    """
    # Get most probable characters
    pred_indices = torch.argmax(outputs, dim=2)  # [seq_len, batch]
    pred_indices = pred_indices.permute(1, 0)  # [batch, seq_len]
    
    decoded_texts = []
    
    for sequence in pred_indices:
        chars = []
        prev_idx = -1
        
        for idx in sequence:
            idx = idx.item()
            # Skip blank (0) and consecutive duplicates
            if idx != 0 and idx != prev_idx:
                if idx in idx_to_char:
                    chars.append(idx_to_char[idx])
            prev_idx = idx
        
        decoded_texts.append(''.join(chars))
    
    return decoded_texts


def beam_search_decode(outputs, idx_to_char, beam_width=10):
    """
    Beam search CTC decoding - slower but more accurate.

    FIXED Bug 6: previous code mixed list-of-chars and string representations.
    After sorting new_beams (a dict keyed by strings), it did `list(seq)` on the
    string key — which splits a string like "AB" into ['A','B'] accidentally works
    for ASCII but is fragile and confusing. Rewritten to use strings throughout:
    beams are now List[Tuple[str, float]] with the sequence always kept as a plain
    string, eliminating the list/string ambiguity entirely.
    """
    outputs = torch.nn.functional.softmax(outputs, dim=2)
    outputs = outputs.permute(1, 0, 2).cpu().numpy()  # [batch, seq_len, num_chars]

    decoded_texts = []

    for output in outputs:
        # Each beam is (sequence_string, cumulative_probability)
        beams: list = [('', 1.0)]

        for timestep in output:
            new_beams: dict = {}

            for sequence, prob in beams:
                for idx, char_prob in enumerate(timestep):
                    if idx == 0:  # blank token — sequence unchanged
                        new_seq = sequence
                    elif idx in idx_to_char:
                        char = idx_to_char[idx]
                        # CTC rule: merge consecutive duplicate characters
                        if sequence and sequence[-1] == char:
                            new_seq = sequence        # duplicate — stay the same
                        else:
                            new_seq = sequence + char # append directly to string
                    else:
                        continue

                    new_prob = prob * char_prob
                    # Merge beams that produce the same string
                    if new_seq in new_beams:
                        new_beams[new_seq] = max(new_beams[new_seq], new_prob)
                    else:
                        new_beams[new_seq] = new_prob

            # Keep top-k beams; keys are already strings — no list() conversion needed
            beams = sorted(new_beams.items(), key=lambda x: x[1], reverse=True)[:beam_width]

        # Best sequence is the string with highest probability
        best_sequence = max(beams, key=lambda x: x[1])[0]
        decoded_texts.append(best_sequence)

    return decoded_texts


def calculate_cer(predictions: List[str], ground_truths: List[str]) -> float:
    """
    Calculate Character Error Rate (CER)
    
    CER = (Substitutions + Deletions + Insertions) / Total Characters
    """
    if len(predictions) != len(ground_truths):
        raise ValueError("Predictions and ground truths must have same length")
    
    total_distance = 0
    total_length = 0
    
    for pred, gt in zip(predictions, ground_truths):
        distance = editdistance.eval(pred, gt)
        total_distance += distance
        total_length += len(gt)
    
    cer = (total_distance / total_length * 100) if total_length > 0 else 0
    return cer


def calculate_wer(predictions: List[str], ground_truths: List[str]) -> float:
    """
    Calculate Word Error Rate (WER)
    
    WER = (Substitutions + Deletions + Insertions) / Total Words
    """
    if len(predictions) != len(ground_truths):
        raise ValueError("Predictions and ground truths must have same length")
    
    total_distance = 0
    total_length = 0
    
    for pred, gt in zip(predictions, ground_truths):
        pred_words = pred.split()
        gt_words = gt.split()
        
        distance = editdistance.eval(pred_words, gt_words)
        total_distance += distance
        total_length += len(gt_words)
    
    wer = (total_distance / total_length * 100) if total_length > 0 else 0
    return wer


def calculate_accuracy(predictions: List[str], ground_truths: List[str]) -> float:
    """
    Calculate exact match accuracy
    """
    if len(predictions) != len(ground_truths):
        raise ValueError("Predictions and ground truths must have same length")
    
    correct = sum(1 for pred, gt in zip(predictions, ground_truths) if pred == gt)
    accuracy = (correct / len(predictions) * 100) if len(predictions) > 0 else 0
    
    return accuracy


class EarlyStopping:
    """
    Early stopping to stop training when validation loss stops improving
    """
    
    def __init__(self, patience=10, min_delta=0.001):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False
    
    def __call__(self, val_loss):
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0
        
        return self.early_stop


class AverageMeter:
    """
    Computes and stores the average and current value
    """
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0
    
    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


def calculate_confusion_matrix(predictions: List[str], ground_truths: List[str], char_set: List[str]) -> np.ndarray:
    """
    Calculate character-level confusion matrix
    
    Args:
        predictions: List of predicted strings
        ground_truths: List of ground truth strings
        char_set: List of all possible characters
        
    Returns:
        Confusion matrix [num_chars, num_chars]
    """
    char_to_idx = {char: idx for idx, char in enumerate(char_set)}
    n_chars = len(char_set)
    
    confusion = np.zeros((n_chars, n_chars), dtype=np.int64)
    
    for pred, gt in zip(predictions, ground_truths):
        # Align sequences (simple alignment)
        max_len = max(len(pred), len(gt))
        pred_padded = pred + ' ' * (max_len - len(pred))
        gt_padded = gt + ' ' * (max_len - len(gt))
        
        for p_char, g_char in zip(pred_padded, gt_padded):
            if p_char in char_to_idx and g_char in char_to_idx:
                confusion[char_to_idx[g_char], char_to_idx[p_char]] += 1
    
    return confusion


def extract_form_fields(text: str, form_type: str) -> Dict[str, str]:
    """
    Extract specific fields from recognized text based on form type
    
    Args:
        text: Recognized text
        form_type: 'form1a', 'form2a', 'form3a', 'form90'
        
    Returns:
        Dictionary of extracted fields
    """
    fields = {}
    
    if form_type == 'form1a':  # Birth Certificate
        # Extract common fields (simplified)
        # In practice, use NER or regex patterns
        fields['type'] = 'Birth Certificate'
        # Add more field extraction logic
        
    elif form_type == 'form2a':  # Death Certificate
        fields['type'] = 'Death Certificate'
        
    elif form_type == 'form3a':  # Marriage Certificate
        fields['type'] = 'Marriage Certificate'
        
    elif form_type == 'form90':  # Marriage License Application
        fields['type'] = 'Marriage License Application'
    
    return fields


def validate_extracted_data(data: Dict[str, str], form_type: str) -> Tuple[bool, List[str]]:
    """
    Validate extracted data for completeness and format
    
    Args:
        data: Extracted data dictionary
        form_type: Form type
        
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Define required fields per form type
    required_fields = {
        'form1a': ['name', 'date_of_birth', 'place_of_birth'],
        'form2a': ['name', 'date_of_death', 'place_of_death'],
        'form3a': ['husband_name', 'wife_name', 'date_of_marriage'],
        'form90': ['husband_name', 'wife_name', 'date_of_application']
    }
    
    # Check required fields
    for field in required_fields.get(form_type, []):
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Additional validation can be added here
    # - Date format validation
    # - Name format validation
    # - etc.
    
    is_valid = len(errors) == 0
    return is_valid, errors


def load_checkpoint(checkpoint_path, model, optimizer=None, device='cpu'):
    """
    Load model checkpoint
    
    Args:
        checkpoint_path: Path to checkpoint file
        model: Model instance
        optimizer: Optimizer instance (optional)
        device: Device to load to
        
    Returns:
        (model, optimizer, checkpoint_dict)
    """
    checkpoint = torch.load(checkpoint_path, map_location=device)
    
    model.load_state_dict(checkpoint['model_state_dict'])
    
    if optimizer is not None and 'optimizer_state_dict' in checkpoint:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    
    print(f"✓ Loaded checkpoint from {checkpoint_path}")
    print(f"  Epoch: {checkpoint.get('epoch', 'N/A')}")
    if 'val_cer' in checkpoint:
        print(f"  Val CER  : {checkpoint['val_cer']:.4f}%")
    elif 'val_loss' in checkpoint:
        print(f"  Val Loss : {checkpoint['val_loss']:.4f}  (run compare_live_cer.py for true CER)")
    else:
        print(f"  Val CER  : N/A  (run compare_live_cer.py for true CER)")
    
    return model, optimizer, checkpoint


def save_predictions_to_file(predictions: List[str], ground_truths: List[str], output_file: str):
    """
    Save predictions and ground truths to file for analysis
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Ground Truth\tPrediction\tMatch\n")
        f.write("=" * 80 + "\n")
        
        for gt, pred in zip(ground_truths, predictions):
            match = "✓" if gt == pred else "✗"
            f.write(f"{gt}\t{pred}\t{match}\n")
    
    print(f"✓ Predictions saved to {output_file}")


if __name__ == "__main__":
    # Test utility functions
    print("=" * 60)
    print("Testing Utility Functions")
    print("=" * 60)
    
    # Test CER calculation
    predictions = ["Hello World", "Test", "Sample Text"]
    ground_truths = ["Hello World", "Tset", "Sample Txt"]
    
    cer = calculate_cer(predictions, ground_truths)
    wer = calculate_wer(predictions, ground_truths)
    accuracy = calculate_accuracy(predictions, ground_truths)
    
    print(f"\nMetrics:")
    print(f"  CER: {cer:.2f}%")
    print(f"  WER: {wer:.2f}%")
    print(f"  Accuracy: {accuracy:.2f}%")
    
    # Test early stopping
    print("\nTesting Early Stopping:")
    early_stopping = EarlyStopping(patience=3, min_delta=0.001)
    
    val_losses = [1.0, 0.9, 0.85, 0.84, 0.84, 0.84, 0.84]
    for epoch, loss in enumerate(val_losses, 1):
        should_stop = early_stopping(loss)
        print(f"  Epoch {epoch}: Loss = {loss:.2f}, Stop = {should_stop}")
        if should_stop:
            break