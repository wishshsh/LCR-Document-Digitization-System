"""
CRNN+CTC Model — simplified for small datasets (~5000-10000 samples)
~700K parameters, converges reliably without CTC blank collapse.
"""
import torch
import torch.nn as nn


class CRNN_CivilRegistry(nn.Module):

    def __init__(self, img_height=64, num_chars=95, hidden_size=128, num_lstm_layers=1):
        super().__init__()

        # CNN — width reductions for 512px input:
        # MaxPool(2,2): 512→256, MaxPool(2,2): 256→128
        # MaxPool(2,1): 128 (height only), MaxPool(2,1): 128 (height only)
        # Conv(k=2,p=0): 127  →  seq_len=127, fits labels up to 64 chars
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),

            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),

            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 1)),

            nn.Conv2d(128, 256, 3, padding=1), nn.BatchNorm2d(256), nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 1)),

            nn.Conv2d(256, 256, kernel_size=2, padding=0),
            nn.BatchNorm2d(256), nn.ReLU(inplace=True),
        )

        cnn_out_h = (img_height // 16) - 1   # = 3 for img_height=64
        rnn_input = 256 * cnn_out_h

        self.rnn = nn.LSTM(
            input_size=rnn_input,
            hidden_size=hidden_size,
            num_layers=num_lstm_layers,
            bidirectional=True,
            batch_first=False,
        )
        self.fc = nn.Linear(hidden_size * 2, num_chars)

    def forward(self, x):
        f = self.cnn(x)
        B, C, h, w = f.size()
        f = f.permute(3, 0, 1, 2).reshape(w, B, C * h)
        f, _ = self.rnn(f)
        return self.fc(f)


class CRNN_Ensemble(nn.Module):
    def __init__(self, num_models=3, **kwargs):
        super().__init__()
        self.models = nn.ModuleList([CRNN_CivilRegistry(**kwargs) for _ in range(num_models)])

    def forward(self, x):
        return torch.mean(torch.stack([m(x) for m in self.models]), dim=0)


def get_crnn_model(model_type='standard', **kwargs):
    if model_type == 'ensemble':
        return CRNN_Ensemble(**kwargs)
    return CRNN_CivilRegistry(**kwargs)


def initialize_weights(model):
    for m in model.modules():
        if isinstance(m, nn.Conv2d):
            nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            if m.bias is not None: nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.BatchNorm2d):
            nn.init.constant_(m.weight, 1); nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, 0, 0.01); nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LSTM):
            for name, param in m.named_parameters():
                if 'weight' in name: nn.init.orthogonal_(param)
                elif 'bias' in name: nn.init.constant_(param, 0)


if __name__ == "__main__":
    model = get_crnn_model('standard', img_height=64, num_chars=95, hidden_size=128, num_lstm_layers=1)
    initialize_weights(model)
    x = torch.randn(2, 1, 64, 512)
    out = model(x)
    params = sum(p.numel() for p in model.parameters())
    print(f"Output: {out.shape}  seq_len={out.shape[0]}")
    print(f"Params: {params:,}")
