# App Hub 商店上架提交记录（2026-10-06）

依据：[Design-Flow README.zh-CN §发布](https://github.com/OctoSense-org/OctoScript-App-Design-Flow/blob/main/README.zh-CN.md#发布)
与 [App Hub PUBLISHING.md](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/main/docs/PUBLISHING.md)。

## 六步流程对照

| 步骤 | 状态 | 说明 |
|---|---|---|
| 1. manifest/listing 定稿 | ✅ | `version: 0.1.0`、最少权限（octos.turn.start + storage，无 net、agent tools=[]）；listing 无占位（publisher Aurora-X / kkkkikun@foxmail.com / PRIVACY.md） |
| 2. 真实截图（octo shot） | ⚠ 诚实替代 | llvmpipe 无头环境 `/g` 抓帧超时（`{"err":"grab timeout"}` 实录）；以 `tools/snap-to-png.py` 按运行时真实控件树重绘替代（文字/层级/坐标/状态色来自实际运行），已在 Submit issue 与 review-answers 披露；评审可用 `octo shot` 获取宿主像素 |
| 3. `hub check` PASSED | ✅ | `--publisher-key aurora-x=<hex>` 通过（**unsigned 警告消失**）；`--catalog`（App Hub catalog.json）对照通过（无重复版本/发布者冲突） |
| 4. `hub scan` + 7 问书面回答 | ✅ | `build/review.json` + `build/review-answers.md`（2026-10-06 刷新） |
| 5. 签名（由人掌握私钥） | ✅ | `hub keygen` → 私钥存仓库外 `.secrets/hub-keys/`（**绝不入库**）；`hub sign-manifest --key-id aurora-x`；公钥 hex 见下 |
| 6. tag + `Submit <app id> <version>` issue | ✅ | tag `v0.1.0` 指向签名后冻结 commit；issue：App-Hub `Submit qianxian 0.1.0` |

## 发布者公钥（aurora-x）

```
30c7d686aa2b582adc1a4b94900a5b486d87d377b54ffcb94985bbc18cd74a71
```

验签命令：

```sh
hub check app/qianxian/bundle --publisher-key aurora-x=30c7d686aa2b582adc1a4b94900a5b486d87d377b54ffcb94985bbc18cd74a71
```

## 签名机制说明

- `bundle_blake3` 摘要（743c1a7f…）不含 integrity/signature 字段——签名后 digest 不变（实测一致）。
- 签名后任何包内容修改都需重新 `hub stamp` + `hub sign-manifest`（README §发布 契约）。
- 私钥位置：`Agentic-octos/.secrets/hub-keys/qianxian-publisher.key`（仓库外，不在任何 git 树内）。
