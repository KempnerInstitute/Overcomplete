from scipy.optimize import linear_sum_assignment
import torch


Epsilon = 1e-6


def avg_l2_loss(x, x_hat):
    """
    Compute the L2 loss, averaged across samples.

    Parameters
    ----------
    x : torch.Tensor
        Original input tensor of shape (batch_size, d).
    x_hat : torch.Tensor
        Reconstructed input tensor of shape (batch_size, d).

    Returns
    -------
    float
        Average L2 loss per sample.
    """
    assert x.shape == x_hat.shape, "Input tensors must have the same shape"
    assert len(x.shape) == 2, "Input tensors must be 2D"
    return torch.mean((x - x_hat).square().sum(-1).sqrt()).item()


def avg_l1_loss(x, x_hat):
    """
    Compute the L1 loss, averaged across samples.

    Parameters
    ----------
    x : torch.Tensor
        Original input tensor of shape (batch_size, d).
    x_hat : torch.Tensor
        Reconstructed input tensor of shape (batch_size, d).

    Returns
    -------
    float
        Average L1 loss per sample.
    """
    assert x.shape == x_hat.shape, "Input tensors must have the same shape"
    assert len(x.shape) == 2, "Input tensors must be 2D"
    return torch.mean(torch.abs(x - x_hat).sum(-1)).item()


def relative_avg_l2_loss(x, x_hat, epsilon=Epsilon):
    """
    Compute the relative reconstruction loss, average across samples.

    The first argument is considered as the true value. The order of the arguments
    is important as the loss is asymmetric:

    ||x - y||_2 / (||x||_2 + epsilon).

    Parameters
    ----------
    x : torch.Tensor
        Original input tensor of shape (batch_size, d).
    x_hat : torch.Tensor
        Reconstructed input tensor of shape (batch_size, d).
    epsilon : float, optional
        Small value to avoid division by zero, by default 1e-6.

    Returns
    -------
    float
        Average relative L2 loss per sample.
    """
    assert x.shape == x_hat.shape, "Input tensors must have the same shape"
    assert len(x.shape) == 2, "Input tensors must be 2D"

    l2_err_per_sample = (x - x_hat).square().sum(-1).sqrt()
    l2_per_sample = x.square().sum(-1).sqrt()

    return torch.mean(l2_err_per_sample / (l2_per_sample + epsilon)).item()


def relative_avg_l1_loss(x, x_hat, epsilon=Epsilon):
    """
    Compute the relative reconstruction loss, average across samples.

    The first argument is considered as the true value. The order of the arguments
    is important as the loss is asymmetric:

    ||x - y||_1 / (||x||_1 + epsilon).

    Parameters
    ----------
    x : torch.Tensor
        Original input tensor of shape (batch_size, d).
    x_hat : torch.Tensor
        Reconstructed input tensor of shape (batch_size, d).
    epsilon : float, optional
        Small value to avoid division by zero, by default 1e-6.

    Returns
    -------
    float
        Average relative L1 loss per sample.
    """
    assert x.shape == x_hat.shape, "Input tensors must have the same shape"
    assert len(x.shape) == 2, "Input tensors must be 2D"

    l1_err_per_sample = torch.abs(x - x_hat).sum(-1)
    l1_per_sample = torch.abs(x).sum(-1)

    return torch.mean(l1_err_per_sample / (l1_per_sample + epsilon)).item()


def sparsity(x, dims=None):
    """
    Compute the average number of zero elements.

    Parameters
    ----------
    x : torch.Tensor
        Input tensor.
    dims : tuple, optional
        Dimensions over which to compute the sparsity, by default None.

    Returns
    -------
    torch.Tensor
        Average sparsity if dims=None else sparsity across dims.
    """
    assert x.dtype == torch.float32, "Input tensor must be of type float32"

    if dims is None:
        return torch.mean((x == 0).float())
    return torch.mean((x == 0).float(), dims)


def sparsity_eps(x, dims=None, threshold=1e-6):
    """
    Compute the sparsity allowing for an epsilon tolerance.

    Parameters
    ----------
    x : torch.Tensor
        Input tensor.
    dims : tuple, optional
        Dimensions over which to compute the sparsity, by default None.
    threshold : float, optional
        Epsilon tolerance, by default 1e-6.

    Returns
    -------
    torch.Tensor
        Average sparsity if dims=None else sparsity across dims.
    """
    if dims is None:
        return torch.mean((x <= threshold).float())
    return torch.mean((x <= threshold).float(), dims)


def dead_codes(z):
    """
    Check for codes that never fire and return the percentage of codes that never fire.

    Parameters
    ----------
    z : torch.Tensor
        Input tensor of shape (batch_size, num_codes).

    Returns
    -------
    torch.Tensor
        Tensor indicating which codes are dead.
    """
    assert len(z.shape) == 2, "Input tensor must be 2D"
    is_dead = (z.sum(0) == 0).float()
    return is_dead


def hungarian_loss(dictionary1, dictionary2, p_norm=2):
    """
    Compute the Hungarian loss between two dictionaries.

    Parameters
    ----------
    dictionary1 : torch.Tensor
        First dictionary tensor of shape (num_codes, dim).
    dictionary2 : torch.Tensor
        Second dictionary tensor of shape (num_codes, dim).
    p_norm : int, optional
        Norm to use for computing the distance, by default 2.

    Returns
    -------
    float
        Hungarian loss.
    """
    assert dictionary1.shape == dictionary2.shape, "Input tensors must have the same shape"
    assert len(dictionary1.shape) == 2, "Input tensors must be 2D"

    cost_matrix = torch.cdist(dictionary1, dictionary2, p=p_norm).cpu().numpy()

    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    loss = cost_matrix[row_ind, col_ind].sum()

    return float(loss)


def _max_non_diagonal(matrix):
    """
    Compute the maximum value of non-diagonal elements in a square matrix.

    Parameters
    ----------
    matrix : torch.Tensor
        Input square matrix of shape (n, n).

    Returns
    -------
    float
        Maximum non-diagonal element.
    """
    assert matrix.shape[0] == matrix.shape[1], "Input must be a square matrix"

    mask = ~torch.eye(matrix.shape[0], dtype=torch.bool, device=matrix.device)
    non_diagonal_values = matrix[mask]

    return torch.max(non_diagonal_values).item()


def _cosine_distance_matrix(x, y):
    """
    Compute the cosine distance matrix between two sets of vectors.

    Parameters
    ----------
    x : torch.Tensor
        First set of vectors of shape (num_vectors_x, dim).
    y : torch.Tensor
        Second set of vectors of shape (num_vectors_y, dim).

    Returns
    -------
    torch.Tensor
        Cosine distance matrix of shape (num_vectors_x, num_vectors_y).
    """
    assert x.shape[1] == y.shape[1], "Input vectors must have the same dimensionality"
    assert len(x.shape) == 2 and len(y.shape) == 2, "Input tensors must be 2D"

    x_normalized = x / x.norm(dim=1, keepdim=True)
    y_normalized = y / y.norm(dim=1, keepdim=True)

    cosine_similarity = torch.matmul(x_normalized, y_normalized.T)
    cosine_distance = 1 - cosine_similarity

    return cosine_distance


def cosine_hungarian_loss(dictionary1, dictionary2):
    """
    Compute the cosine Hungarian loss between two dictionaries.

    Parameters
    ----------
    dictionary1 : torch.Tensor
        First dictionary tensor of shape (num_codes, dim).
    dictionary2 : torch.Tensor
        Second dictionary tensor of shape (num_codes, dim).

    Returns
    -------
    float
        Cosine Hungarian loss.
    """
    assert dictionary1.shape == dictionary2.shape, "Input tensors must have the same shape"
    assert len(dictionary1.shape) == 2, "Input tensors must be 2D"

    cost_matrix = _cosine_distance_matrix(dictionary1, dictionary2).cpu().numpy()

    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    loss = cost_matrix[row_ind, col_ind].sum()

    return float(loss)


def dictionary_collinearity(dictionary):
    """
    Compute the collinearity of a dictionary.

    Parameters
    ----------
    dictionary : torch.Tensor
        Dictionary tensor of shape (num_codes, dim).

    Returns
    -------
    max_collinearity : float
        Maximum collinearity across dictionary elements (non diagonal).
    cosine_similarity_matrix : torch.Tensor
        Matrix of cosine similarities across dictionary elements.
    """
    assert len(dictionary.shape) == 2, "Input tensor must be 2D"

    normalized_dict = dictionary / (dictionary.norm(dim=1, keepdim=True) + Epsilon)

    cosine_similarity_matrix = torch.matmul(normalized_dict, normalized_dict.T)
    max_collinearity = _max_non_diagonal(torch.abs(cosine_similarity_matrix))

    return max_collinearity, cosine_similarity_matrix.detach()


def wasserstein_1d(x1, x2):
    """
    Compute the 1D Wasserstein-1 distance between two sets of codes and average
    across dimensions.

    Parameters
    ----------
    x1 : torch.Tensor
        First set of samples of shape (num_samples, d).
    x2 : torch.Tensor
        Second set of samples of shape (num_samples, d).

    Returns
    -------
    torch.Tensor
        Wasserstein distance.
    """
    assert x1.shape == x2.shape, "The two sets must have the same shape"
    assert len(x1.shape) == 2, "Input tensors must be 2D"

    x1_sorted, _ = torch.sort(x1, dim=0)
    x2_sorted, _ = torch.sort(x2, dim=0)

    # avg of wasserstein across dimensions
    dist = torch.mean(torch.abs(x1_sorted - x2_sorted))

    return dist


def frechet_distance(x1, x2):
    """
    Compute the Fréchet distance (Wasserstein-2 distance) between two sets of activations.
    Assume that the activations are normally distributed.

    ||mu_x1 - mu_x2||^2 + Tr(Cov_x1 + Cov_x2 - 2 * (Cov_x1 * Cov_x2)**(1/2))
    with mu_x1, mu_x2 the means and Cov_x1, Cov_x2 the covariances of the two sets.

    Parameters
    ----------
    x1 : torch.Tensor
        First set of samples of shape (num_samples, d).
    x2 : torch.Tensor
        Second set of samples of shape (num_samples, d).

    Returns
    -------
    torch.Tensor
        Fréchet distance.
    """
    assert x1.shape == x2.shape, "The two sets must have the same shape"
    assert len(x1.shape) == 2, "Input tensors must be 2D"

    mu_x1 = torch.mean(x1, dim=0)
    mu_x2 = torch.mean(x2, dim=0)

    cov_x1 = torch.cov(x1.T)
    cov_x2 = torch.cov(x2.T)

    trace_sum = cov_x1.trace() + cov_x2.trace()

    mean_diff = mu_x1 - mu_x2
    mean_diff_squared = torch.sum(mean_diff ** 2)

    cov_prod = torch.matmul(cov_x1, cov_x2)

    eigvals = torch.linalg.eigvals(cov_prod)
    tr_cov_prod_sqrt = eigvals.sqrt().real.sum()

    dist = mean_diff_squared + trace_sum - 2.0 * tr_cov_prod_sqrt

    return dist


def codes_correlation_matrix(codes):
    """
    Compute the correlation matrix of codes.

    Parameters
    ----------
    codes : torch.Tensor
        Codes tensor of shape (batch_size, num_codes).

    Returns
    -------
    max_corr : float
        Maximum correlation across codes (non diagonal).
    corrs : torch.Tensor
        Correlation matrix of codes.
    """
    assert len(codes.shape) == 2, "Input tensor must be 2D"
    assert codes.shape[0] > 1, "At least two samples are required"

    codes_centered = codes - codes.mean(dim=0, keepdim=True)

    cov = torch.matmul(codes_centered.T, codes_centered) / (codes_centered.shape[0] - 1)
    std = torch.sqrt(torch.diag(cov))

    corrs = cov / (torch.outer(std, std) + Epsilon)
    max_corr = _max_non_diagonal(torch.abs(corrs))

    return max_corr, corrs


def energy_of_codes(codes, dictionary):
    """
    Compute the energy of codes given a dictionary.

     for example, with X input sample, Z the codes and D the dictionary:
     X = ZD, Energy(Z) = || E[Z]D ||^2

     and correspond to the average energy the codes bring to the reconstruction.

    Parameters
    ----------
    codes : torch.Tensor
        Codes tensor of shape (batch_size, num_codes).
    dictionary : torch.Tensor
        Dictionary tensor of shape (num_codes, dim).

    Returns
    -------
    torch.Tensor
        Energy of codes, one per codes dimension.
    """
    assert len(codes.shape) == 2, "Input tensor must be 2D"
    assert len(dictionary.shape) == 2, "Dictionary tensor must be 2D"
    assert codes.shape[1] == dictionary.shape[0], "Number of codes must match dictionary size"

    avg_codes = torch.mean(codes, 0)
    energy = (avg_codes[:, None] * dictionary).square().sum(-1).sqrt()

    return energy
