# GLSCL 论文阅读与独立实现

本目录原有论文为 **GLSCL: Graph local similarity contrastive learning for recommendation**，Zhou Zhou、Zheng Hu、Shi-Min Cai、Tao Zhou，*Expert Systems with Applications* 284 (2025), 127855。DOI: [10.1016/j.eswa.2025.127855](https://doi.org/10.1016/j.eswa.2025.127855)。原 PDF 保持不变。

**结论：找到一个自称官方的占位仓库，但没有可下载的模型源码；已根据论文完成独立 PyTorch 实现，并通过核心检查和真实数据子集训练。尚未复现论文完整实验指标。**

## 源码检索

Git 仓库中的 [reports/](reports/README.md) 保存已验证实验的配置、结果、日志和数据来源快照。下载数据与模型权重保留在原本地/服务器目录，不随 Git 上传；原论文 PDF 和阅读时生成的正文、截图也不上传。

2026-10-17 检查了 [zzoxi/GLSCL](https://github.com/zzoxi/GLSCL)。README 原文是：

> The official implementation of GLSCL will be made public once the paper is accepted. Coming soon ...

当时唯一分支 `main` 指向 `264c8a9570cb708153c92796a80247b575bb7388`，完整文件树只有 `README.md`。其公开 forks 为空。还检查了该账号其他公开仓库，并做了 GLSCL、论文短语以及推荐主题 README 检索，未找到可确认对应本文的完整实现。论文正文未发现代码链接，因此账号与作者的对应关系没有独立证实。

另一个同名 [zchoi/GLSCL](https://github.com/zchoi/GLSCL) 是文本视频检索项目，不能拿来复现这篇推荐系统论文。查询返回、候选仓库文件树及 README 快照保存在 `paper_reading/`。

## 已完成的代码

- `glscl/model.py`：LightGCN 图传播、排除初始层的均值池化、同象限归一化噪声、BPR、随机扰动 InfoNCE、局部相似节点对比损失及联合优化。
- `glscl/data.py`：稳定 ID 映射、互斥划分检查、仅训练集建图、负采样、批内精确余弦最近邻和低相似度自对比回退。
- `glscl/metrics.py`：全物品排序的 Recall@10/20、NDCG@10/20；验证时屏蔽训练交互，测试时屏蔽训练和验证交互。
- `prepare_data.py`：合成数据、固定版本的 Douban-Book 下载、评分过滤、自定义数据读入以及按用户约 7:1:2 划分。
- `train.py`：种子控制、验证集选模/早停、检查点、完整配置、逐轮日志、最终测试。
- `recommend.py`：加载检查点，使用原始用户 ID 输出推荐。
- `tests/test_core.py`：手算公式、梯度、相似邻居选择、数据隔离、排序屏蔽、检查点和学习能力检查。

更详细的公式对应和不确定性见 [REPRODUCTION_NOTES.md](REPRODUCTION_NOTES.md)。

## 快速运行

在当前文件夹的 PowerShell 中执行。当前机器已有 Python、NumPy、SciPy 和 CPU 版 PyTorch，通常可直接开始；其他环境先运行 `python -m pip install -r requirements.txt`。

```powershell
python -m unittest discover -s tests -v
python prepare_data.py demo
python train.py --config configs/demo.json --output-dir runs/my-demo
python recommend.py --checkpoint runs/my-demo/best.pt --user user-00 --k 10
```

`--output-dir` 应使用新目录，防止覆盖已有训练。下面列出的已交付实验目录已经存在，重复训练时也请另设输出目录。

真实数据子集验证：

```powershell
python prepare_data.py douban --max-users 512 --output data/douban-subset
python train.py --config configs/douban_subset.json --output-dir runs/my-douban-subset
python train.py --eval-only runs/my-douban-subset/best.pt
```

现有检查点可直接复核：

```powershell
python train.py --eval-only runs/douban-subset/best.pt
```

公开 Douban 数据的非抽样起步流程（默认保留至少 10 条交互的用户）：

```powershell
python prepare_data.py douban --output data/douban-book
python train.py --config configs/douban_paper_start.json --output-dir runs/my-full-douban
```

本次已经生成 `data/douban-book/`：8,863 用户、22,287 物品，训练/验证/测试交互数为 414,585 / 54,507 / 113,037。该非抽样版本尚未训练。

完整训练默认 300 轮、批大小 6000，CPU 耗时明显更长；当前没有执行该完整训练。配置名称中的 `paper_start` 表示参考论文的起点，**不是作者最终配置**。如果安装了 CUDA 版 PyTorch，可加 `--device cuda`。

自备 Yelp/Amazon-Book 等数据时，支持两种格式：

```powershell
# 每行 user item [rating]；二值数据不要设置 --min-rating
python prepare_data.py split --input path/to/ratings.txt --min-rating 4 --output data/custom
# LightGCN 常见格式，每行 user item1 item2 ...
python prepare_data.py split --input path/to/train.txt path/to/test.txt --format user-list --output data/custom
python train.py --config configs/douban_subset.json --data-dir data/custom --output-dir runs/custom
```

如果已有可信的作者划分，可以直接准备互不重叠的 `train.txt`、`valid.txt`、`test.txt`，每行 `user item`，通过 `--data-dir` 指定目录。此时不要再重新划分。检查点保存了三份数据的指纹，换数据或换划分不能直接套用旧检查点。

## 已执行验证

9 个核心测试通过。真实数据来自 [SELFRec 的 Douban-Book](https://github.com/Coder-Yu/SELFRec/tree/5b0229423cb1c727e85a704d63e460368c8b9dde/dataset/douban-book)，固定提交 `5b0229423cb1c727e85a704d63e460368c8b9dde`，下载文件 SHA256 保存在 `data/raw/douban-book/source.json`。

真实子集使用 seed 2026，512 用户、11,089 物品；训练/验证/测试交互数分别为 22,907 / 2,986 / 6,213。训练集中未出现的物品有 1,914 个，评估中仍然保留，未事后删除。CPU 训练 15 轮，按验证集 Recall@20 选择第 15 轮，耗时约 63 秒：

- 验证集 Recall@20：初始 0.004737，选中模型 0.088738。
- 测试集 Recall@10：0.056221；Recall@20：0.080220。
- 测试集 NDCG@10：0.074408；NDCG@20：0.076152。

配置、运行环境、逐轮训练日志、结果和权重分别位于 `runs/douban-subset/config.json`、`environment.json`、`history.jsonl`、`results.json`、`best.pt`。这是实现可训练的证据，不能与论文完整 Douban-Book 的 Recall@20=0.1865/NDCG@20=0.1646 作直接优劣比较。

## 复现限制

当前公开 SELFRec 文件去重合并后只有 **12,859 用户、22,294 物品、598,420 交互**，与论文表 3 的 **13,024 用户、22,347 物品、792,062 交互** 不一致。这里保留真实数据统计，不用名称相同来假定数据版本相同。

论文未给出原始划分、划分种子、全部数据清洗规则，以及最终 `epsilon`、`lambda_uniform`、正则权重和相似度阈值。本实现中的这些取值是公开的实现选择。实际子集 batch=512 也小于论文的 Douban batch≈6000。

进一步复现论文数值需要拿到相同数据版本和划分，并在验证集上搜索超参数、做多随机种子实验。可以用 `configs/douban_subset_simgcl.json` 和 `configs/douban_subset_lightgcn.json` 运行同一代码框架内的两个基线近似配置；本次未执行这两个对照，也不声称 GLSCL 已优于它们。

## 服务器 2 的实际试跑（2026-10-17）

已使用 `teacher-server2` 的第 0 张 RTX 4090 D 完成试跑。服务器目录为 `/home/xiao20244352113/glscl-reproduction/20261017_gpu_trial`，Python 为 `/home/xiao20244352113/miniconda3/bin/python`，环境是 Python 3.10.14、PyTorch 2.3.1+cu121、NumPy 1.26.4、SciPy 1.15.3。没有修改原有项目或安装全局依赖。

9 项核心检查和一轮合成数据 GPU 训练通过。随后对 `data/douban-book` 的 414,585 条训练交互跑了一轮：batch=6000、维度 64、2 层，采用 `configs/douban_paper_start.json`，仅将设备设为 CUDA、轮数设为 1，并使用新的输出目录。

实测训练 42.63 秒，验证 2.25 秒，含验证和保存检查点的单轮为 44.93 秒。包括读数据、初始化、初始验证和最终测试的整个训练子进程耗时 57.01 秒。PyTorch 峰值已分配显存约 244 MiB、峰值缓存保留显存 302 MiB；这不是包含 CUDA 上下文等开销的整卡显存统计。

按这次单轮实测外推，同一配置的一次训练：10 轮约 7-10 分钟，100 轮约 1.2-1.5 小时，300 轮约 3.5-4.5 小时。默认每 5 轮验证一次，早停可能提前结束；估计未包括多组调参、多随机种子或其他数据集，也未测量后续稳态轮次。

本次单轮验证集 Recall@20=0.107829，测试集 Recall@20=0.107080；这些只是运行结果，不是收敛指标。试跑已结束，300 轮长跑尚未启动。

服务器日志和结果归档到本地 `runs/server2-trial-20261017/`，其中 `full-one-epoch/history.jsonl` 包含计时和显存记录，`full-one-epoch/results.json` 是指标；`server-trial/status.json` 记录各阶段退出码和耗时，`deployment_manifest.json` 记录上传源码及数据文件的 SHA256。

完整模型权重保存在服务器 `/home/xiao20244352113/glscl-reproduction/20261017_gpu_trial/runs/full-one-epoch/best.pt`。由于回传速度较慢，未等待完整权重下载；其大小和 SHA256 保存在本地 `remote_checkpoints.json`。本地 `.tar.gz.partial` 是中止的下载，不是可用模型或完整归档。
