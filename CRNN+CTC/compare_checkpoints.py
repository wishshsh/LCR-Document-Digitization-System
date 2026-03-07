import torch
import sys
sys.path.append('.')
from crnn_model import get_crnn_model

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def test_model(path, label):
    c      = torch.load(path, map_location=device, weights_only=False)
    config = c.get('config', {})
    model  = get_crnn_model(
        model_type      = config.get('model_type', 'standard'),
        img_height      = config.get('img_height', 64),
        num_chars       = c['model_state_dict']['fc.weight'].shape[0],
        hidden_size     = config.get('hidden_size', 128),
        num_lstm_layers = config.get('num_lstm_layers', 1),
    ).to(device)
    model.load_state_dict(c['model_state_dict'], strict=False)
    epoch   = c.get('epoch', 'N/A')
    val_loss = c.get('val_loss', None)   # fine-tuned checkpoints (EMNIST, IAM)
    val_cer  = c.get('val_cer',  None)   # synthetic baseline checkpoint
    if val_loss is not None:
        metric_str = f"val_loss={val_loss:.4f}"
    elif val_cer is not None:
        metric_str = f"val_cer={val_cer:.4f}%"
    else:
        metric_str = "no metric saved"
    print(f"{label}: epoch={epoch}  {metric_str}")

print("=" * 55)
test_model('checkpoints/best_model.pth',       'Synthetic  ')
test_model('checkpoints/best_model_emnist.pth', 'EMNIST     ')
test_model('checkpoints/best_model_iam.pth',    'IAM        ')
print("=" * 55)