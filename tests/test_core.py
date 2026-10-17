"""Small hand-computed oracles for the scientific failure points."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import torch
from torch.nn import functional as F

from glscl.data import InteractionData, LocalSimilarity
from glscl.metrics import evaluate, ranking_metrics
from glscl.model import GLSCL, contrastive_loss, signed_noise
from prepare_data import split_pairs
from train import DEFAULTS, build_model, load_checkpoint


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)

    def test_graph_and_excluded_initial_layer(self):
        # Two users, two items; edges (u0,i0),(u0,i1),(u1,i1).
        dense = torch.tensor([[0., 0., 2**-.5, .5],
                              [0., 0., 0., 2**-.5],
                              [2**-.5, 0., 0., 0.],
                              [.5, 2**-.5, 0., 0.]])
        model = GLSCL(2, 2, dense.to_sparse(), embedding_dim=1, layers=2)
        initial = torch.tensor([[1.], [2.], [3.], [4.]])
        with torch.no_grad():
            model.user_embedding.weight.copy_(initial[:2])
            model.item_embedding.weight.copy_(initial[2:])
        actual = torch.cat(model())
        expected = (dense @ initial + dense @ dense @ initial) / 2
        torch.testing.assert_close(actual, expected)
        wrong = (initial + dense @ initial + dense @ dense @ initial) / 3
        self.assertFalse(torch.allclose(actual, wrong))

    def test_local_similarity_full_norms_batch_scope_threshold_and_singleton(self):
        matrix = sp.csr_matrix(np.array([[1, 1, 0, 0], [1, 1, 0, 0],
                                        [1, 0, 1, 0], [0, 0, 0, 1]], dtype=np.float32))
        similarity = LocalSimilarity(matrix, block_size=1)
        # u1 is globally best for u0, but absent from this batch.
        batch = np.array([0, 2, 3])
        np.testing.assert_array_equal(similarity.select(batch, "users", .4), [1, 0, 2])
        # u0/u2 cosine is exactly .5. Above that threshold both must use self.
        np.testing.assert_array_equal(similarity.select(batch, "users", .6), [0, 1, 2])
        np.testing.assert_array_equal(similarity.select(np.array([0]), "users", .1), [0])
        np.testing.assert_array_equal(similarity.select(np.array([0, 1]), "items", .1), [1, 0])
        with self.assertRaises(ValueError):
            similarity.select(np.array([0, 0]), "users", .1)

    def test_chunked_infonce_values_and_gradients_match_formula(self):
        torch.manual_seed(4)
        a = torch.randn(5, 3, dtype=torch.float64, requires_grad=True)
        b = torch.randn(5, 3, dtype=torch.float64, requires_grad=True)
        targets = torch.tensor([2, 0, 1, 4, 3])
        expected = F.cross_entropy(a @ b.T / .2, targets, reduction="sum")
        expected_grad = torch.autograd.grad(expected, (a, b), retain_graph=True)
        for size in (1, 2, 20):
            actual = contrastive_loss(a, b, targets, chunk_size=size)
            torch.testing.assert_close(actual, expected)
            actual_grad = torch.autograd.grad(actual, (a, b), retain_graph=True)
            for left, right in zip(actual_grad, expected_grad):
                torch.testing.assert_close(left, right)
        normalized = contrastive_loss(a, b, targets, normalize=True, reduction="mean", chunk_size=2)
        oracle = F.cross_entropy(F.normalize(a, dim=1) @ F.normalize(b, dim=1).T / .2, targets)
        torch.testing.assert_close(normalized, oracle)

    def test_noise_length_orthant_and_independence(self):
        torch.manual_seed(2)
        x = torch.tensor([[1., -2., 3.], [-1., 2., -3.]])
        first, second = signed_noise(x, .15), signed_noise(x, .15)
        torch.testing.assert_close(first.norm(dim=1), torch.full((2,), .15))
        self.assertTrue(torch.equal(first.sign(), x.sign()))
        self.assertFalse(torch.equal(first, second))

    def test_ranking_metric_oracle(self):
        measured = ranking_metrics([9, 2, 7], {2, 7}, ks=[1, 3])
        self.assertEqual(measured["Recall@1"], 0.)
        self.assertEqual(measured["Recall@3"], 1.)
        self.assertAlmostEqual(measured["NDCG@3"],
                               (1 / np.log2(3) + 1 / np.log2(4)) / (1 + 1 / np.log2(3)))

    def test_data_train_only_graph_negative_sampling_leakage_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "train.txt").write_text("a x\na y\nb y\n", encoding="utf-8")
            (root / "valid.txt").write_text("a z\nb x\n", encoding="utf-8")
            (root / "test.txt").write_text("b z\n", encoding="utf-8")
            data = InteractionData(root)
            graph = data.graph(torch.device("cpu")).to_dense()
            # Validation edge b-x is absent from both the graph and cosine input.
            self.assertEqual(float(graph[1, data.n_users]), 0.)
            self.assertEqual(float(data.matrix[1, 0]), 0.)
            self.assertEqual(int(torch.count_nonzero(graph)), 6)
            for _ in range(10):
                for users, _, negatives in data.epoch_batches(2, np.random.default_rng(_)):
                    self.assertTrue(all(int(i) not in data.by_user["train"][int(u)]
                                        for u, i in zip(users, negatives)))
            model = build_model(data, DEFAULTS, torch.device("cpu"))
            path = root / "model.pt"
            torch.save({"config": DEFAULTS, "fingerprint": data.fingerprint,
                        "model": model.state_dict(), "epoch": 1}, path)
            restored, _ = load_checkpoint(path, data, torch.device("cpu"))
            for a, b in zip(model(), restored()):
                torch.testing.assert_close(a, b)
            # A swapped split must be rejected, even if dimensions happen to match.
            (root / "valid.txt").write_text("b z\n", encoding="utf-8")
            (root / "test.txt").write_text("a z\nb x\n", encoding="utf-8")
            changed = InteractionData(root)
            with self.assertRaises(ValueError):
                load_checkpoint(path, changed, torch.device("cpu"))
            (root / "test.txt").write_text("a x\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                InteractionData(root)

    def test_evaluation_masks_train_and_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, text in {"train": "a x\n", "valid": "a y\n", "test": "a z\n"}.items():
                (root / f"{name}.txt").write_text(text, encoding="utf-8")
            data = InteractionData(root)
            class Fixed(torch.nn.Module):
                def forward(self):
                    return torch.tensor([[1.]]), torch.tensor([[100.], [50.], [1.]])
            # If validation is not excluded at test time, y would outrank true z.
            self.assertEqual(evaluate(Fixed(), data, "test", ks=[1])["Recall@1"], 1.)

    def test_objective_finite_backward_and_bpr_overfit(self):
        torch.manual_seed(7)
        graph = torch.tensor([[0., 0., 1., 0.], [0., 0., 0., 1.],
                              [1., 0., 0., 0.], [0., 1., 0., 0.]]).to_sparse()
        model = GLSCL(2, 2, graph, embedding_dim=4, layers=2)
        users, positive, negative = torch.tensor([0, 1]), torch.tensor([0, 1]), torch.tensor([1, 0])
        config = {**DEFAULTS, "contrastive_chunk_size": 1}
        targets = (torch.tensor([1, 0]), torch.tensor([1, 0]))
        full_loss, _ = model.objective(users, positive, negative, config, targets)
        full_loss.backward()
        self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters()))
        config.update(lambda_uniform=0., lambda_local=0., lambda_reg=0.)
        optimizer = torch.optim.Adam(model.parameters(), lr=.03)
        initial = float(model.objective(users, positive, negative, config)[0].detach())
        for _ in range(60):
            optimizer.zero_grad()
            loss, _ = model.objective(users, positive, negative, config)
            loss.backward()
            optimizer.step()
        final = float(model.objective(users, positive, negative, config)[0].detach())
        self.assertLess(final, initial * .1)

    def test_deterministic_disjoint_splits(self):
        pairs = [(str(u), str(i)) for u in range(5) for i in range(20)]
        with tempfile.TemporaryDirectory() as temp:
            a, b = Path(temp) / "a", Path(temp) / "b"
            split_pairs(pairs, a, seed=2026)
            split_pairs(reversed(pairs), b, seed=2026)
            for name in ("train", "valid", "test"):
                self.assertEqual((a / f"{name}.txt").read_bytes(), (b / f"{name}.txt").read_bytes())
            self.assertEqual(InteractionData(a).summary()["train"], 70)


if __name__ == "__main__":
    unittest.main()
