# -*- coding: utf-8 -*-
"""Copy of Comp 448 HW3

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1i9Mb1katuqx3gLVF2fz2qOhaa4QnunVc
"""

from __future__ import print_function, division
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
import numpy as np
import torchvision
from torchvision import datasets, models, transforms
import matplotlib.pyplot as plt
import time
import os
import copy
from torch.utils.data import WeightedRandomSampler

from google.colab import drive
drive.mount("/content/gdrive")

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model_conv = models.alexnet(pretrained = True)

data_dir = '/content/gdrive/My Drive/dataset'
data_transforms = {
 'train': transforms.Compose([
  transforms.Resize(256),
  transforms.CenterCrop(224),
  transforms.ToTensor(),
  transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
 ]),
 'valid': transforms.Compose([
  transforms.Resize(256),
  transforms.CenterCrop(224),
  transforms.ToTensor(),
  transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
 ]),
 'test': transforms.Compose([
  transforms.Resize(256),
  transforms.CenterCrop(224),
  transforms.ToTensor(),
  transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
 ])
}
image_datasets = {x: datasets.ImageFolder(os.path.join(data_dir, x),
 data_transforms[x]) for x in ['train', 'valid', 'test']}

for param in model_conv.parameters():
  param.requires_grad = False

model_conv.classifier[len(model_conv.classifier)-1] = nn.Linear(4096, 3, bias=True)
model_conv = model_conv.to(device)
criterion = nn.CrossEntropyLoss()
optimizer_conv = torch.optim.SGD(model_conv.parameters(), lr=0.1, momentum = 0.9)
exp_lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer_conv, step_size=20, gamma=0.1)

def train_model(image_datasets, model, criterion, optimizer, scheduler, num_epochs):
  dataloaders = {x: torch.utils.data.DataLoader(image_datasets[x], batch_size = 4, shuffle = True, num_workers = 4) for x in ['train', 'valid']}
  best_model_wts = copy.deepcopy(model.state_dict())
  best_no_corrects = 0
  for epoch in range(num_epochs):
    # Set the model to the training mode for updating the weights using
    # the first portion of training images
    model.train()
    for inputs, labels in dataloaders['train']: # iterate over data
      inputs = inputs.to(device)
      labels = labels.to(device)
      optimizer.zero_grad()
      with torch.set_grad_enabled(True):
        outputs = model(inputs)
        _, preds = torch.max(outputs, 1)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
    # Set the model to the evaluation mode for selecting the best network
    # based on the number of correctly classified validation images
    model.eval()
    no_corrects = 0
    for inputs, labels in dataloaders['valid']:
      inputs = inputs.to(device)
      labels = labels.to(device)
      with torch.set_grad_enabled(False):
        outputs = model(inputs)
        _, preds = torch.max(outputs, 1)
        no_corrects += torch.sum(preds == labels.data)
      if no_corrects > best_no_corrects:
        best_no_corrects = no_corrects
        best_model_wts = copy.deepcopy(model.state_dict())
      scheduler.step()
  # Load the weights of the best network
  model.load_state_dict(best_model_wts)
  return model

new_model = train_model(image_datasets, model_conv, criterion, optimizer_conv, exp_lr_scheduler, 15)

dataloaders = {x: torch.utils.data.DataLoader(image_datasets[x], batch_size = 4, shuffle = True, num_workers = 4)for x in ['test']}
class_correct = list(0. for i in range(3))
class_total = list(0. for i in range(3))
with torch.no_grad():
    for inputs, labels in dataloaders['test']:
      inputs = inputs.to(device)
      labels = labels.to(device)
      outputs = new_model(inputs)
      _, predicted = torch.max(outputs, 1)
      c = (predicted == labels).squeeze()
      for i in range(2):
          label = labels[i]
          class_correct[label] += c[i].item()
          class_total[label] += 1
c = 0
t = 0
for i in range(3):
  c += class_correct[i]
  t += class_total[i]
  print(classes[i], 100 * class_correct[i] / class_total[i])
print((100 * c / t))