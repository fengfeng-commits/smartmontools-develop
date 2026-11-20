# 在 GitHub 建仓库（方案 A：独立仓库）

## 需要填的字段

网页建仓和脚本建仓用的是同一套值，照抄即可。

| 字段 | 值 |
|---|---|
| Repository name | `smartmontools-develop` |
| Description | `Unofficial smartmontools branch — Windows installer and macOS dmg rebuilt with branding patches` |
| Website | `https://smartmontools.cn` |
| Topics | `smartmontools` `smartctl` `smartd` `smart` `disk-health` `windows` `macos` `gplv2` `unofficial-build` |
| Visibility | Public |
| Initialize this repository with | **全部不勾**（README / .gitignore / license 都不勾，仓库里已有） |

Description 里用 “Unofficial … branch”，不用 “official”，也不用 “official Chinese site”。

## 方式 1：网页上传（最快，不需要 token）

1. GitHub → New repository → 按上表填写 → Create
2. 解压 `smartmontools-develop-skeleton.zip`
3. 在空仓库页面点 **uploading an existing file**
4. 把解压出来的 16 个文件/文件夹**整体拖进浏览器**
   - 关键：把 `.github`、`.gitignore` 一起拖进去。Windows 资源管理器默认隐藏以点开头的项，
     先在「查看 → 显示 → 隐藏的项目」打开，否则 `.github/workflows/` 会漏传，CI 不会跑
5. Commit changes
6. 进 Settings 或仓库主页右侧 About，点齿轮补上 Description / Website / Topics

## 方式 2：脚本建仓（需要 PAT）

```powershell
cd C:\Users\Administrator\Documents\deepseek-harness\default-workspace\smartmontools-develop
$env:GH_TOKEN = "ghp_你的token"     # 只需 repo 权限
python scripts\create_repo.py --dry-run   # 先看会传哪些文件
python scripts\create_repo.py             # 真建
```

脚本行为：

| 动作 | 说明 |
|---|---|
| 建仓库 | 已存在则复用，不报错 |
| 传文件 | 16 个，`.exe/.dmg/.zip/__pycache__` 自动跳过 |
| 设元数据 | description、homepage、topics 一并写入 |
| 幂等 | 重复运行是更新文件，不会重复建库 |

Token 只从 `GH_TOKEN` / `GITHUB_TOKEN` 环境变量读取，不落盘、不回显。

## 方式 3：让 DSH 代跑脚本

需要 token 出现在 DSH 进程的环境里。环境变量在进程启动时捕获，所以：

```powershell
setx GH_TOKEN "ghp_你的token"
```

然后**重启 DSH 会话**，再让我执行 `python scripts\create_repo.py`。

不重启的话，当前会话的进程读不到这个变量，我这边只会报 `GH_TOKEN is not set`。

## 域名现状

`smartmontools.cn` 与 `www.smartmontools.cn` 当前 DNS 无解析，链接点不开。

建议先配一条 A 记录或 CNAME，再对外发布。About 的 Website 字段可以先填，GitHub 不校验可达性。

## 建仓后自检

| 检查 | 期望 |
|---|---|
| Actions 标签 | 出现 `build-windows` 与 `build-darwin` 两个 workflow |
| 首次 Actions 运行 | 手动 `workflow_dispatch` 触发，看能否出 artifact |
| 关于区 | Description 含 “Unofficial”，Website 指向 .cn |
| 首屏 | README 第一行就写明是分支、非官方 |
