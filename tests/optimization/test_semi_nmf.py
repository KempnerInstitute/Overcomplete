import pytest
import torch
from sklearn.decomposition import NMF as SkNMF

from overcomplete.optimization import SemiNMF
from overcomplete.metrics import relative_avg_l2_loss, sparsity


data_shape = (50, 10)
n_components = 5

A = torch.rand(data_shape, dtype=torch.float32)

# Sklearn NMF for benchmarking
sk_model = SkNMF(n_components=n_components, init='random', solver='mu', max_iter=1000)
Z_sk = sk_model.fit_transform(A.numpy())
D_sk = sk_model.components_
sk_error = relative_avg_l2_loss(A, Z_sk @ D_sk)

solvers = ['mu', 'pgd']


@pytest.mark.parametrize("solver", solvers)
def test_semi_nmf_initialization(solver):
    """Test that the SemiNMF class initializes properly."""
    model = SemiNMF(n_components=n_components, solver=solver)
    assert model.n_components == n_components, "Incorrect number of components."


@pytest.mark.parametrize("solver", solvers)
def test_semi_nmf_fit(solver):
    """Test that the SemiNMF model can fit to the data."""
    model = SemiNMF(n_components=n_components, max_iter=2, solver=solver)
    Z, D = model.fit(A)
    assert (Z >= 0).all(), "Negative values in Z."
    assert D.shape == (n_components, data_shape[1]), "Incorrect shape for D."
    assert Z.shape == (data_shape[0], n_components), "Incorrect shape for Z."


@pytest.mark.parametrize("solver", solvers)
def test_semi_nmf_negative_data(solver):
    """Test how the model handles negative data."""
    negative_data = torch.randn(data_shape, dtype=torch.float32)
    model = SemiNMF(n_components=n_components, solver=solver)
    Z, D = model.fit(negative_data)
    assert (Z >= 0).all(), "Negative values in Z."
    # D can be negative, so we don't check it


@pytest.mark.parametrize("solver", solvers)
def test_semi_nmf_encode_decode(solver):
    """Test the encode and decode methods of the SemiNMF model."""
    model = SemiNMF(n_components=n_components, max_iter=2, solver=solver)
    model.fit(A)

    Z = model.encode(A)
    assert (Z >= 0).all(), "Negative values in encoded data."
    assert Z.shape == (data_shape[0], n_components), "Incorrect shape for encoded data."

    A_hat = model.decode(Z)
    assert A_hat.shape == (data_shape[0], data_shape[1]), "Incorrect shape for decoded data."


@pytest.mark.parametrize("solver", solvers)
def test_semi_nmf_reconstruction_error(solver):
    """Test that the reconstruction error decreases after fitting."""
    model = SemiNMF(n_components=n_components, max_iter=100, solver=solver)
    init_z = model.init_random_z(A)
    init_d = model.init_random_d(A, init_z)
    initial_error = torch.norm(A - init_z @ init_d, 'fro')
    model.fit(A)
    Z = model.encode(A)
    A_hat = model.decode(Z)
    final_error = torch.norm(A - A_hat, 'fro')
    assert (Z >= 0).all(), "Negative values in Z."
    assert final_error < initial_error, "Reconstruction error did not decrease."


@pytest.mark.parametrize("solver", solvers)
def test_semi_nmf_zero_data(solver):
    """Test how the model handles data with zeros."""
    zero_data = torch.zeros(data_shape)
    model = SemiNMF(n_components=n_components, solver=solver)
    Z, D = model.fit(zero_data)
    reconstruction_error = torch.norm(zero_data - Z @ D, 'fro')
    assert (Z >= 0).all(), "Negative values in Z."
    assert reconstruction_error < 1e-5, "Model did not reconstruct zero data correctly."


@pytest.mark.parametrize("solver", solvers)
def test_semi_nmf_large_number_of_components(solver):
    """Test the SemiNMF model with varying number of components."""
    small_model = SemiNMF(n_components=1, solver=solver)
    small_model.fit(A)
    error_small = torch.square(A - small_model.decode(small_model.encode(A))).sum()

    large_model = SemiNMF(n_components=100, solver=solver)
    large_model.fit(A)
    error_large = torch.square(A - large_model.decode(large_model.encode(A))).sum()

    assert error_large <= error_small, "Higher error with more components."


@pytest.mark.parametrize("solver", solvers)
def test_compare_to_sklearn(solver, repetitions=10):
    """
    Test that SemiNMF achieves similar performance to sklearn NMF.
    """
    is_ok = False
    for _ in range(repetitions):
        our_model = SemiNMF(n_components=n_components, max_iter=1000, solver=solver)
        Z, D = our_model.fit(A)
        our_error = relative_avg_l2_loss(A, Z @ D)

        assert (Z >= 0).all(), "Negative values in Z."

        if our_error < 2.0 * sk_error:
            is_ok = True
            break

    assert is_ok, "SemiNMF did not match sklearn NMF performance."


def test_sparsity():
    # ensure that having stronger penalty induce better sparsity on the solution
    model = SemiNMF(n_components=n_components, max_iter=1000, solver='pgd', l1_penalty=0.0)
    Z, D = model.fit(A)

    model2 = SemiNMF(n_components=n_components, max_iter=1000, solver='pgd', l1_penalty=1.0)
    Z_strong, D_strong = model2.fit(A)

    s_Z = sparsity(Z)
    s_Z_strong = sparsity(Z_strong)

    assert s_Z_strong > s_Z, "Stronger penalty should induce better sparsity."
