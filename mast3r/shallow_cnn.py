# Copyright (C) 2024-present Naver Corporation. All rights reserved.
# Licensed under CC BY-NC-SA 4.0 (non-commercial use only).
#
# --------------------------------------------------------
# DUSt3R model class
# --------------------------------------------------------
from copy import deepcopy
import torch
import os
from packaging import version
import torch.nn as nn
import dust3r.utils.path_to_croco  # noqa: F401
inf = float('inf')
import torch.nn as nn
import torch.nn.functional as F

class ConvBnReLU(nn.Module):
    def __init__(self, in_channels, out_channels,
                 kernel_size=3, stride=1, pad=1):
        super(ConvBnReLU, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels,
                              kernel_size, stride=stride, padding=pad, bias=False)
        self.relu = nn.ReLU(inplace=True)
    def forward(self, x):
        return self.relu(self.conv(x))
    
class FeatureNet(nn.Module):
    def __init__(self, norm_act=nn.BatchNorm2d):
        super(FeatureNet, self).__init__()
        self.conv0 = nn.Sequential(
                        ConvBnReLU(3, 8, 3, 1, 1),
                        ConvBnReLU(8, 8, 3, 1, 1))
        self.conv1 = nn.Sequential(
                        ConvBnReLU(8, 16, 5, 2, 2),
                        ConvBnReLU(16, 16, 3, 1, 1))
        self.conv2 = nn.Sequential(
                        ConvBnReLU(16, 32, 5, 2, 2),
                        ConvBnReLU(32, 32, 3, 1, 1))

        self.toplayer = nn.Conv2d(32, 32, 1)
        self.lat1 = nn.Conv2d(16, 32, 1)
        self.lat0 = nn.Conv2d(8, 32, 1)

        self.smooth1 = nn.Conv2d(32, 32, 3, padding=1)
        self.smooth0 = nn.Conv2d(32, 32, 3, padding=1)

    def _upsample_add(self, x, y):
        return F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=True) + y

    def forward(self, x):
        conv0 = self.conv0(x)
        conv1 = self.conv1(conv0)
        conv2 = self.conv2(conv1)
        feat2 = self.toplayer(conv2)
        feat1 = self._upsample_add(feat2, self.lat1(conv1))
        feat0 = self._upsample_add(feat1, self.lat0(conv0))
        feat1 = self.smooth1(feat1)
        feat0 = self.smooth0(feat0)
        return feat2, feat1, feat0
