import pytest
import torch
from torch import nn, optim
from torch.utils.data import DataLoader, TensorDataset
from collections import defaultdict
from einops import rearrange

from overcomplete.sae.train import l2, train_sae
from overcomplete.sae.factory import SAEFactory
from overcomplete.sae.losses import mse_l1
from overcomplete.sae import SAE

from .utils import epsilon_equal


def test_train_mlp_sae():
    """Ensure we can train mlp sae using string identifier."""
    data = torch.randn(10, 10)
    dataset = TensorDataset(data)
    dataloader = DataLoader(dataset, batch_size=10)
    criterion = mse_l1
    n_components = 2

    model = SAE(data.shape[1], n_components, encoder_module="mlp_ln_3")

    optimizer = optim.SGD(model.parameters(), lr=0.001)
    scheduler = None

    logs = train_sae(model, dataloader, criterion, optimizer, scheduler, nb_epochs=2, monitoring=False, device="cpu")

    assert isinstance(logs, defaultdict)
    assert len(logs) == 0

    logs = train_sae(model, dataloader, criterion, optimizer, scheduler, nb_epochs=2, monitoring=True, device="cpu")
    assert isinstance(logs, defaultdict)
    assert "z" in logs
    assert "z_l2" in logs
    assert "z_sparsity" in logs
    assert "time_epoch" in logs


def test_train_resnet_sae():
    """Ensure we can train resnet sae"""

    def criterion(x, x_hat, z, dictionary):
        x = rearrange(x, 'n c w h -> (n w h) c')
        return mse_l1(x, x_hat, z, dictionary)

    data = torch.randn(10, 10, 5, 5)
    dataset = TensorDataset(data)
    dataloader = DataLoader(dataset, batch_size=10)
    n_components = 2

    model = SAE(data.shape[1:], n_components, encoder_module="resnet_1b")

    optimizer = optim.SGD(model.parameters(), lr=0.001)
    scheduler = None

    logs = train_sae(model, dataloader, criterion, optimizer, scheduler, nb_epochs=2, monitoring=False, device="cpu")

    assert isinstance(logs, defaultdict)
    assert len(logs) == 0

    logs = train_sae(model, dataloader, criterion, optimizer, scheduler, nb_epochs=2, monitoring=True, device="cpu")
    assert isinstance(logs, defaultdict)
    assert "z" in logs
    assert "z_l2" in logs
    assert "z_sparsity" in logs
    assert "time_epoch" in logs


def test_train_attention_sae():
    """Ensure we can train attention sae"""

    def criterion(x, x_hat, z, dictionary):
        x = rearrange(x, 'n t c -> (n t) c')
        return mse_l1(x, x_hat, z, dictionary)

    data = torch.randn(10, 10, 64)
    dataset = TensorDataset(data)
    dataloader = DataLoader(dataset, batch_size=10)
    n_components = 2

    model = SAE(data.shape[1:], n_components, encoder_module="attention_1b")

    optimizer = optim.SGD(model.parameters(), lr=0.001)
    scheduler = None

    logs = train_sae(model, dataloader, criterion, optimizer, scheduler, nb_epochs=2, monitoring=False, device="cpu")

    assert isinstance(logs, defaultdict)
    assert len(logs) == 0

    logs = train_sae(model, dataloader, criterion, optimizer, scheduler, nb_epochs=2, monitoring=True, device="cpu")
    assert isinstance(logs, defaultdict)
    assert "z" in logs
    assert "z_l2" in logs
    assert "z_sparsity" in logs
    assert "time_epoch" in logs
