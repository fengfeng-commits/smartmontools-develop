# smartmontools · develop

> **本仓库是 smartmontools 的分支，不是官方发行版。**
> 基于 [smartmontools](https://github.com/smartmontools/smartmontools) 修改，不代表上游项目，
> 也未获其背书。本仓库的问题请提交到本仓库 Issues，不要打扰上游。
>
> 项目主页：<https://smartmontools.cn> ｜ 上游官方：<https://www.smartmontools.org>

免费下载、免费使用，遵循 GNU GPL v2 或更新版本。

## 这是什么

在官方源码上叠加少量补丁后重新构建的 Windows x64 发行版。程序本体（`smartctl.exe`、`smartd.exe`）
的功能与上游一致，差异仅限补丁清单所列内容。

## 与上游的差异

基于上游 `RELEASE_7_5`（r5714），只改 Windows 显示字符串，不改任何逻辑。

| 补丁 | 文件 | 改了什么 |
|---|---|---|
| `0001-brand-versioninfo-rc-in.patch` | `os_win32/versioninfo.rc.in` | exe 属性：`ProductName`、`CompanyName`；`LegalCopyright` 保留原作者并追加修改声明 |
| `0002-brand-installer-nsi.patch` | `os_win32/installer.nsi` | 安装向导标题、安装包属性、控制面板「程序和功能」显示名 |

**刻意不修改**，否则会破坏升级与卸载：

| 项 | 原因 |
|---|---|
| `smartctl` / `smartd` 文件名 | 脚本、服务注册、`update-smart-drivedb` 全部依赖 |
| 安装路径 `$PROGRAMFILES\smartmontools` | 改了会与官方版产生两份独立安装，卸载残留 |
| 注册表键 `Uninstall\smartmontools`、`uninst-smartmontools.exe` | 改了卸载程序找不到自己的记录 |
| 版本号 `7.5` | `WIN_RC_FILTER` 用 `sed 's,^\([0-9]*\.[0-9]*\.[0-9]*\).*$,\1,p'` 解析，加后缀会让版本回落成 `0.0.0` |
| 命令行参数、JSON 输出 | 保持与上游完全兼容 |

### 已知限制

安装包与官方版**共用同一安装路径和注册表键**，因此两者不能共存：装这个会覆盖官方版，反之亦然。
需要并存的话必须整体改名（路径、注册表、卸载程序、快捷方式一起改），属于未做的工作。

## 下载

| 平台 | 产物 | 构建方式 |
|---|---|---|
| Windows | `smartmontools-develop-win32-setup.exe` | 解包官方安装器 + 品牌补丁 + `makensis` 重打包 |
| macOS | `smartmontools-develop.dmg` | CI（macOS runner）源码编译 + `pkgbuild` + `hdiutil` |

文件名均带 `develop` 以区别于官方发行包。

macOS 的 dmg 只能由 `.github/workflows/build-darwin.yml` 产出：dmg 是 HFS+ 卷加 UDIF 封装，
Windows 上没有任何工具能写入这种格式，而 GitHub 的 macOS runner 自带 `pkgbuild` 与 `hdiutil`。

## 构建

见 [BUILD.md](BUILD.md)。CI 在每次 push 时自动交叉编译并产出 Windows 包。

## 许可

GPL-2.0-or-later。许可证全文不重复存放，获取途径见 [LICENSE.md](LICENSE.md)。
本仓库的新增文件与补丁同样以 GPL-2.0-or-later 授权。
完整对应源码 = 上游公开仓库 + 本仓库补丁，CI 可一键复现，见 [NOTICE](NOTICE)。

## 上游同步

见 [UPSTREAM.md](UPSTREAM.md)。
