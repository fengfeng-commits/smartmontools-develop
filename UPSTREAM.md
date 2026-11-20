# 上游同步

## 背景

2025-06-01 起 `https://github.com/smartmontools/smartmontools` 是官方上游仓库（此前为 SourceForge SVN）。
默认分支 `main`，旧 `master` 分支已弃用。CI 默认跟随 `main`。

## 补丁失效怎么办

上游一有改动，`patches/*.patch` 就可能 apply 失败。CI 会在 apply 步骤直接报错，不会产出错误构建。
处理流程：

```bash
git clone --depth 1 https://github.com/smartmontools/smartmontools.git src
cd src
git apply -v ../patches/0001-xxx.patch     # 看是哪个 hunk 冲突
```

手工合并后重新生成：

```bash
git -C src diff > ../patches/0001-xxx.patch
```

## 固定上游版本（建议）

`main` 是滚动分支，构建结果会随上游变动。发布前把 `SM_REF` 固定到 tag：

```yaml
env:
  SM_REF: RELEASE_7_5
```

Release 说明里写明所基于的上游版本，`NOTICE` 里的「upstream revision」同步更新。

## drivedb.h（盘型号库）

`drivedb.h` 更新频率高于代码。两种做法：

- **跟随上游**：不单独改，随上游一起更新（省事，推荐）
- **单独覆盖**：把新 `drivedb.h` 作为补丁加入 `patches/`，需自己保证与上游 `smartctl` 版本匹配

上游提供 `update-smart-drivedb` 脚本，可在运行时更新，但需要网络与写权限，发行版里是否启用需自行决定（**未验证**在当前源码树中的默认行为）。
