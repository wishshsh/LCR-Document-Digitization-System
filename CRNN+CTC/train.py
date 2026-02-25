
"""
Training Script for CRNN+CTC Civil Registry OCR
Includes CTC loss, learning rate scheduling, and model checkpointing
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import os
from tqdm import tqdm
import numpy as np
from pathlib import Path
import json

from crnn_model import get_crnn_model, initialize_weights
from dataset import CivilRegistryDataset, collate_fn
from utils import (
    decode_ctc_predictions,
    calculate_cer,
    calculate_wer,
    EarlyStopping
)


class CRNNTrainer:
    """
    Trainer class for CRNN+CTC model
    """
    
    def __init__(self, config):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Create directories
        self.checkpoint_dir = Path(config['checkpoint_dir'])
        self.log_dir = Path(config['log_dir'])
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize datasets
        print("Loading datasets...")
        self.train_dataset = CivilRegistryDataset(
            data_dir=config['train_data_dir'],
            annotations_file=config['train_annotations'],
            img_height=config['img_height'],
            img_width=config['img_width'],
            augment=True,
            form_type=config.get('form_type', 'all')
        )
        
        self.val_dataset = CivilRegistryDataset(
            data_dir=config['val_data_dir'],
            annotations_file=config['val_annotations'],
            img_height=config['img_height'],
            img_width=config['img_width'],
            augment=False,
            form_type=config.get('form_type', 'all')
        )
        
        # Create data loaders
        self.train_loader = DataLoader(
            self.train_dataset,
            batch_size=config['batch_size'],
            shuffle=True,
            num_workers=config['num_workers'],
            collate_fn=collate_fn,
            pin_memory=False
        )
        
        self.val_loader = DataLoader(
            self.val_dataset,
            batch_size=config['batch_size'],
            shuffle=False,
            num_workers=config['num_workers'],
            collate_fn=collate_fn,
            pin_memory=False
        )
        
        # Initialize model
        print(f"Initializing model on {self.device}...")
        self.model = get_crnn_model(
            model_type=config.get('model_type', 'standard'),
            img_height=config['img_height'],
            num_chars=self.train_dataset.num_chars,
            hidden_size=config['hidden_size'],
            num_lstm_layers=config['num_lstm_layers']
        )
        
        initialize_weights(self.model)
        self.model = self.model.to(self.device)
        
        # Loss function - CTC Loss
        self.criterion = nn.CTCLoss(blank=0, zero_infinity=True)
        
        # Optimizer
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=config['learning_rate'],
            weight_decay=config.get('weight_decay', 1e-5)
        )
        
        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=config.get('lr_patience', 3),
            min_lr=1e-6
        )
        
        # Early stopping
        self.early_stopping = EarlyStopping(
            patience=config.get('early_stopping_patience', 10),
            min_delta=config.get('min_delta', 0.001)
        )
        
        # Training history
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'val_cer': [],
            'val_wer': [],
            'learning_rates': []
        }
        
        print(f"✓ Model initialized with {sum(p.numel() for p in self.model.parameters()):,} parameters")
    
    def train_epoch(self, epoch):
        """Train for one epoch"""
        self.model.train()
        total_loss = 0
        
        pbar = tqdm(self.train_loader, desc=f"Epoch {epoch}/{self.config['epochs']}")
        
        for batch_idx, (images, targets, target_lengths, _) in enumerate(pbar):
            images = images.to(self.device)
            targets = targets.to(self.device)
            
            # Forward pass
            outputs = self.model(images)  # [seq_len, batch, num_chars]
            
            # Apply log_softmax for CTC
            log_probs = nn.functional.log_softmax(outputs, dim=2)
            
            # Calculate sequence lengths
            batch_size = images.size(0)
            input_lengths = torch.full(
                size=(batch_size,),
                fill_value=outputs.size(0),
                dtype=torch.long
            ).to(self.device)
            
            # CTC loss
            loss = self.criterion(
                log_probs,
                targets,
                input_lengths,
                target_lengths
            )
            
            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            
            # Gradient clipping to prevent exploding gradients
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 5.0)
            
            self.optimizer.step()
            
            total_loss += loss.item()
            
            # Update progress bar
            pbar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'avg_loss': f'{total_loss / (batch_idx + 1):.4f}'
            })
        
        avg_loss = total_loss / len(self.train_loader)
        return avg_loss
    
    def validate(self):
        """Validate the model"""
        self.model.eval()
        total_loss = 0
        all_predictions = []
        all_ground_truths = []
        
        with torch.no_grad():
            for images, targets, target_lengths, texts in tqdm(self.val_loader, desc="Validating"):
                images = images.to(self.device)
                targets_gpu = targets.to(self.device)
                
                # Forward pass
                outputs = self.model(images)
                log_probs = nn.functional.log_softmax(outputs, dim=2)
                
                # CTC loss
                batch_size = images.size(0)
                input_lengths = torch.full(
                    size=(batch_size,),
                    fill_value=outputs.size(0),
                    dtype=torch.long
                ).to(self.device)
                
                loss = self.criterion(log_probs, targets_gpu, input_lengths, target_lengths)
                total_loss += loss.item()
                
                # Decode predictions
                predictions = decode_ctc_predictions(
                    outputs.cpu(),
                    self.train_dataset.idx_to_char
                )
                
                all_predictions.extend(predictions)
                all_ground_truths.extend(texts)
        
        avg_loss = total_loss / len(self.val_loader)
        
        # Calculate metrics
        cer = calculate_cer(all_predictions, all_ground_truths)
        wer = calculate_wer(all_predictions, all_ground_truths)
        
        return avg_loss, cer, wer, all_predictions, all_ground_truths
    
    def train(self):
        """Main training loop"""
        print("\n" + "=" * 70)
        print("Starting Training")
        print("=" * 70)
        
        best_val_loss = float('inf')
        
        for epoch in range(1, self.config['epochs'] + 1):
            print(f"\nEpoch {epoch}/{self.config['epochs']}")
            print("-" * 70)
            
            # Train
            train_loss = self.train_epoch(epoch)
            
            # Validate
            val_loss, val_cer, val_wer, predictions, ground_truths = self.validate()
            
            # Learning rate scheduling
            self.scheduler.step(val_loss)
            current_lr = self.optimizer.param_groups[0]['lr']
            
            # Update history
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['val_cer'].append(val_cer)
            self.history['val_wer'].append(val_wer)
            self.history['learning_rates'].append(current_lr)
            
            # Print metrics
            print(f"\nMetrics:")
            print(f"  Train Loss: {train_loss:.4f}")
            print(f"  Val Loss:   {val_loss:.4f}")
            print(f"  Val CER:    {val_cer:.2f}%")
            print(f"  Val WER:    {val_wer:.2f}%")
            print(f"  LR:         {current_lr:.6f}")
            
            # Print sample predictions
            print(f"\nSample Predictions:")
            for i in range(min(3, len(predictions))):
                print(f"  GT:   {ground_truths[i]}")
                print(f"  Pred: {predictions[i]}")
                print()
            
            # Save checkpoint
            is_best = val_loss < best_val_loss
            if is_best:
                best_val_loss = val_loss
            
            self.save_checkpoint(epoch, val_loss, val_cer, is_best)
            
            # Early stopping
            if self.early_stopping(val_loss):
                print(f"\nEarly stopping triggered at epoch {epoch}")
                break
        
        print("\n" + "=" * 70)
        print("Training Complete!")
        print(f"Best validation loss: {best_val_loss:.4f}")
        print("=" * 70)
        
        # Save final training history
        self.save_history()
    
    def save_checkpoint(self, epoch, val_loss, val_cer, is_best=False):
        """Save model checkpoint"""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'val_loss': val_loss,
            'val_cer': val_cer,
            'char_to_idx': self.train_dataset.char_to_idx,
            'idx_to_char': self.train_dataset.idx_to_char,
            'config': self.config,
            'history': self.history
        }
        
        # Save latest checkpoint
        checkpoint_path = self.checkpoint_dir / 'latest_checkpoint.pth'
        torch.save(checkpoint, checkpoint_path)
        
        # Save best checkpoint
        if is_best:
            best_path = self.checkpoint_dir / 'best_model.pth'
            torch.save(checkpoint, best_path)
            print(f"  ✓ Best model saved (Val Loss: {val_loss:.4f}, CER: {val_cer:.2f}%)")
        
        # Save epoch checkpoint
        if epoch % self.config.get('save_freq', 10) == 0:
            epoch_path = self.checkpoint_dir / f'checkpoint_epoch_{epoch}.pth'
            torch.save(checkpoint, epoch_path)
    
    def save_history(self):
        """Save training history"""
        history_path = self.log_dir / 'training_history.json'
        with open(history_path, 'w') as f:
            json.dump(self.history, f, indent=2)
        print(f"\n✓ Training history saved to {history_path}")


def main():
    """Main training function"""
    
    # Configuration
    config = {
        # Data
        'train_data_dir': 'data/train',
        'train_annotations': 'data/train_annotations.json',
        'val_data_dir': 'data/val',
        'val_annotations': 'data/val_annotations.json',
        'form_type': 'all',  # 'all', 'form1a', 'form2a', 'form3a', 'form90'
        
        # Model
        'model_type': 'standard',  # 'standard', 'ensemble', 'lightweight'
        'img_height': 64,
        'img_width': 400,
        'hidden_size': 256,
        'num_lstm_layers': 2,
        
        # Training
        'batch_size': 32,
        'epochs': 100,
        'learning_rate': 0.001,
        'weight_decay': 1e-5,
        'num_workers': 0,
        
        # Scheduling & Early Stopping
        'lr_patience': 3,
        'early_stopping_patience': 10,
        'min_delta': 0.001,
        
        # Saving
        'checkpoint_dir': 'checkpoints',
        'log_dir': 'logs',
        'save_freq': 10,
    }
    
    # Initialize trainer
    trainer = CRNNTrainer(config)
    
    # Start training
    trainer.train()


if __name__ == "__main__":
    main()
