import dataset
from trainer import check_accuracy, train_epoch, valid_epoch

import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
from torchsummary import summary
import torchvision.models as models

def save_checkpoint(checkpoint, filename='checkpoint_CIFAR100.pth'):
    print("=> saving checkpoint")
    torch.save(checkpoint, filename)

# Set device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print("Using device = {}".format(device))

# Hyperparameters
in_channel = 3
num_classes = 100
learning_rate = 0.01
epochs = 100

# Load data
train_loader = dataset.train_loader
valid_loader = dataset.valid_loader

# Initialize network and transfer learning
model = models.mobilenet_v3_large(pretrained=True).to(device)

model.classifier = nn.Sequential(
            nn.Linear(960, 1280),
            nn.Hardswish(inplace=True),
            nn.Dropout(p=0.2, inplace=True),
            nn.Linear(1280, num_classes),
        )

summary(model=model, input_size=(3, 96, 96), device=device)

# Loss, optimizer and Scheduler
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr=learning_rate, momentum=0.92, weight_decay=0.0001)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.1, patience=5,
                                                 eps=1e-8, verbose=True, cooldown=0, min_lr=0)

# Transfer learning
checkpoint = torch.load('checkpoint_CIFAR100.pth')
model.load_state_dict(checkpoint['state_dict'])
optimizer.load_state_dict(checkpoint['optimizer'])

# Training
train_loss_his, train_acc_his = [], []
valid_loss_his, valid_acc_his = [], []

best_valid_accuracy = 0.

for epoch in range(epochs):
    train_loss, train_acc = train_epoch(train_loader, model, criterion=criterion,
                                        optimizer=optimizer, device=device)
    valid_loss, valid_acc = valid_epoch(valid_loader, model, criterion=criterion, device=device)

    print(f"Epoch {(epoch + 1):>2d}: - train_loss: {train_loss:>7f}, train accuracy: {(train_acc*100):>0.1f}%")
    print(f"Epoch {(epoch + 1):>2d}: - valid_loss: {valid_loss:>7f}, valid accuracy: {(valid_acc*100):>0.1f}%")
    
    if epoch == 0:
        best_valid_accuracy = valid_acc
        checkpoint = {'state_dict': model.state_dict(),
                      'optimizer': optimizer.state_dict()}
        save_checkpoint(checkpoint)
        
    if valid_acc > best_valid_accuracy:
        checkpoint = {'state_dict': model.state_dict(),
                      'optimizer': optimizer.state_dict()}
        save_checkpoint(checkpoint)
        best_valid_accuracy = valid_acc
        
    print()

    scheduler.step(valid_loss)

    train_loss_his.append(train_loss)
    train_acc_his.append(train_acc)
    valid_loss_his.append(valid_loss)
    valid_acc_his.append(valid_acc)

print(train_loss_his)
print(train_acc_his)
print(valid_loss_his)
print(valid_acc_his)