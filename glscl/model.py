"""Paper equations, with explicitly configurable loss reduction."""
from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.checkpoint import checkpoint


def signed_noise(embedding: torch.Tensor, epsilon: float) -> torch.Tensor:
    """Eqs. (14-16): U(0,1), unit row norm, original orthant, length eps."""
    return epsilon * F.normalize(torch.rand_like(embedding), dim=1) * embedding.sign()


def contrastive_loss(anchors, candidates, targets, temperature=0.2,
                     normalize=False, reduction="sum", chunk_size=512):
    """Stable Eq. (10/11/17); candidates include the anchor itself.

    Targets index the ORIGINAL batch embeddings, not a reordered neighbour view.
    Checkpointing bounds saved logits during training, without detaching gradients.
    """
    if temperature <= 0 or chunk_size <= 0:
        raise ValueError("temperature and chunk_size must be positive")
    if reduction not in ("sum", "mean"):
        raise ValueError("reduction must be sum or mean")
    if len(anchors) == 0:
        return anchors.sum() * 0
    if normalize:
        anchors = F.normalize(anchors, dim=1)
        candidates = F.normalize(candidates, dim=1)
    losses = []
    def block_loss(a, b, labels):
        return F.cross_entropy(a @ b.T / temperature, labels, reduction="sum")
    for start in range(0, len(anchors), chunk_size):
        a, labels = anchors[start:start + chunk_size], targets[start:start + chunk_size]
        if torch.is_grad_enabled() and (a.requires_grad or candidates.requires_grad):
            loss = checkpoint(block_loss, a, candidates, labels, use_reentrant=False)
        else:
            loss = block_loss(a, candidates, labels)
        losses.append(loss)
    total = torch.stack(losses).sum()
    return total / len(anchors) if reduction == "mean" else total


class GLSCL(nn.Module):
    def __init__(self, n_users, n_items, graph, embedding_dim=64, layers=2,
                 epsilon=0.1, include_initial=False):
        super().__init__()
        if layers < 1:
            raise ValueError("layers must be >= 1")
        self.n_users, self.n_items = n_users, n_items
        self.layers, self.epsilon = layers, epsilon
        self.include_initial = include_initial
        self.user_embedding = nn.Embedding(n_users, embedding_dim)
        self.item_embedding = nn.Embedding(n_items, embedding_dim)
        nn.init.xavier_uniform_(self.user_embedding.weight)
        nn.init.xavier_uniform_(self.item_embedding.weight)
        self.register_buffer("graph", graph, persistent=False)

    def forward(self, perturbed=False):
        x = torch.cat((self.user_embedding.weight, self.item_embedding.weight))
        outputs = [x] if self.include_initial else []
        for _ in range(self.layers):
            x = torch.sparse.mm(self.graph, x)
            if perturbed:
                x = x + signed_noise(x, self.epsilon)
            outputs.append(x)
        # Eq. (2): mean of layers 1..L. include_initial is only for LightGCN baseline.
        final = torch.stack(outputs, dim=0).mean(dim=0)
        return final[:self.n_users], final[self.n_users:]

    def objective(self, users, positives, negatives, config, local_targets=None):
        user_repr, item_repr = self()
        u, p, n = user_repr[users], item_repr[positives], item_repr[negatives]
        reduction = config["loss_reduction"]
        scores = (u * (p - n)).sum(dim=1)
        bpr_values = F.softplus(-scores)
        main = bpr_values.sum() if reduction == "sum" else bpr_values.mean()
        zero = main.new_zeros(())
        uniform, local_user, local_item = zero, zero, zero
        uid, iid = users.unique(sorted=True), positives.unique(sorted=True)
        kwargs = dict(temperature=config["temperature"], reduction=reduction,
                      chunk_size=config["contrastive_chunk_size"])
        if config["lambda_uniform"]:
            u1, i1 = self(perturbed=True)
            u2, i2 = self(perturbed=True)
            uniform = contrastive_loss(u1[uid], u2[uid], torch.arange(len(uid), device=users.device),
                                       normalize=True, **kwargs)
            uniform = uniform + contrastive_loss(
                i1[iid], i2[iid], torch.arange(len(iid), device=users.device), normalize=True, **kwargs)
        if config["lambda_local"]:
            if local_targets is None:
                raise ValueError("local targets required when lambda_local != 0")
            if config["local_user_weight"]:
                local_user = contrastive_loss(user_repr[uid], user_repr[uid], local_targets[0],
                                              normalize=config["normalize_local"], **kwargs)
            if config["alpha"]:
                local_item = contrastive_loss(item_repr[iid], item_repr[iid], local_targets[1],
                                              normalize=config["normalize_local"], **kwargs)
        # Eq. (18) prints ||Theta||_2 (without a square). Keep that literal default.
        # The optional squared form is explicit because many BPR implementations use it.
        regularization = torch.linalg.vector_norm(torch.stack([
            torch.linalg.vector_norm(parameter) for parameter in self.parameters()]))
        if config["regularization"] == "l2_squared":
            regularization = regularization.square()
        local = config["local_user_weight"] * local_user + config["alpha"] * local_item
        total = (main + config["lambda_uniform"] * uniform
                 + config["lambda_local"] * local + config["lambda_reg"] * regularization)
        return total, {"bpr": main.detach(), "uniform": uniform.detach(),
                       "local_user": local_user.detach(), "local_item": local_item.detach(),
                       "l2": regularization.detach(), "total": total.detach()}
