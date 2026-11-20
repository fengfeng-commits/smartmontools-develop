# 构建说明

三条路线。选 **路线 0** 可以最快拿到一个能装的 exe；选 **路线 A** 才是长期可维护的做法。

| 路线 | 需要编译器 | 程序本体 | 适用 |
|---|---|---|---|
| 0 重打包官方二进制 | 否，只要 NSIS + 7-Zip | 官方原版 | 快速出包、只换品牌 |
| A 补丁仓库 + CI 编译 | 云端有 | 自己编译 | 长期演进 |
| B Fork 整包 | 云端有 | 自己编译 | 需要大改代码 |

---

## 路线 0：重打包官方二进制（无需编译器）

把官方 `setup.exe` 解包，用本仓库的品牌补丁重打安装器。程序本体仍是官方二进制，
换的只是安装界面标题、文件属性、控制面板显示名。

前置：7-Zip、NSIS 3.x（便携版即可，解压后含 `Bin\makensis.exe`）、Python。

```powershell
# 系统默认策略常禁止运行 .ps1，用 Bypass 子进程调用最省事
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-installer.ps1 `
  -OfficialSetup C:\Downloads\smartmontools-7.5.win32-setup.exe `
  -SourceTree    C:\src\smartmontools-RELEASE_7_5 `
  -NsisDir       C:\nsis `
  -OutFile       .\smartmontools-develop-win32-setup.exe
```

产物不可逐字节复现：NSIS 会把构建时间写进 PE 头，两次构建 SHA256 必然不同，
但文件大小与内容一致。要哈希稳定只能等 NSIS 3.08+ 支持 `SOURCE_DATE_EPOCH`。

脚本做四件事，每步都可单独复现：

| 步 | 动作 |
|---|---|
| 1 | `7z x` 解包官方安装器，得到 `bin\`（64 位）、`bin32\`（32 位）、`doc\` |
| 2 | 拆成两棵输入树：`INPDIR` 放 32 位 exe + 共用脚本与文档，`INPDIR64` 只放 64 位 exe |
| 3 | 对上游源码树应用 `patches/*.patch`（含 `Unicode true`） |
| 4 | `makensis -DINPDIR=... -DINPDIR64=... -DOUTFILE=... -DVERSION=... -DYY=... -DVERSTR=...` |

`INPDIR` / `INPDIR64` 的拆分不是可选项：`installer.nsi` 的 `FileExe` 宏靠这两个符号决定
文件进 `bin\` 还是 `bin32\`，安装时再按系统位数二选一。只给 `INPDIR` 会得到一个没有
32 位程序的包（实测会少掉全部 `bin32\` 内容）。

产物无数字签名（改一个字节官方签名即失效），详见 README。

---

## 路线 A：补丁仓库（本仓库默认）

仓库内不含上游源码，只有 `patches/` 与 CI。CI 流程：

1. clone 上游 `smartmontools`（默认 `main`，可用 `SM_REF` 环境变量固定到 tag）
2. 按文件名顺序 `git apply` 全部补丁
3. `./autogen.sh && ./configure --host=x86_64-w64-mingw32 && make`
4. 收集 `*.exe` 打成 zip，上传 artifact

本地复现同一流程：

```bash
git clone --depth 1 https://github.com/smartmontools/smartmontools.git src
cd src
for p in ../patches/*.patch; do git apply -v "$p"; done
./autogen.sh
./configure --build=x86_64-pc-linux-gnu --host=x86_64-w64-mingw32
make -j"$(nproc)"
```

依赖（Debian/Ubuntu）：

```bash
sudo apt install -y autoconf automake libtool gettext pkg-config \
  mingw-w64 g++-mingw-w64-x86-64 zip
```

### 加一个补丁

```bash
# 在 src/ 里改完代码后
git -C src diff > ../patches/0001-<描述>.patch
```

补丁文件名用 4 位序号前缀，保证应用顺序确定。

---

## 路线 B：Fork 整包（仓库内含全部源码）

适合需要长期大改、补丁会失控的情况。

1. GitHub 网页 Fork `smartmontools/smartmontools`
2. `git clone` 自己的 fork，直接改源码
3. CI 去掉「拉上游 + 应用补丁」两步，其余相同

代价：仓库体积约 40 MB+，每次上游合并都可能冲突，`drivedb.h` 同步也更麻烦。

---

## 本地 Windows 原生构建（MSYS2）

```bash
pacman -S --needed base-devel mingw-w64-x86_64-toolchain \
  autoconf automake libtool gettext
```

在 **MINGW64** shell 中：

```bash
./autogen.sh
./configure --host=x86_64-w64-mingw32
make -j"$(nproc)"
```

产物 `smartctl.exe`、`smartd.exe` 在源码根目录。

---

## macOS：dmg 只能在 CI 构建

Windows 上做不了，原因不是缺工具链，而是格式本身：

| 障碍 | 说明 |
|---|---|
| dmg 容器 | HFS+ 卷 + UDIF 封装，Windows 没有可写的实现；7-Zip 只能读 |
| pkg | xar 归档（内含 gzip cpio 的 `Payload`、`Bom`、`PackageInfo`、`Distribution`），7-Zip 只读 |
| 二进制 | 安装的是 Mach-O，不是 PE，无法用 Windows 产物顶替 |

官方自己也是跨平台构建的：`Makefile.am:1168-1200` 显示他们用 `cpio` + `xar` + `mkbom` +
`xorriso` + `libdmg-hfsplus` 在 Linux 上生成 pkg 与 dmg。macOS runner 上有更原生的路径，
所以本仓库的 darwin 流程直接用 `pkgbuild` + `hdiutil`，不走官方那套。

`.github/workflows/build-darwin.yml` 的步骤：

| 步 | 动作 |
|---|---|
| 1 | clone 上游 `RELEASE_7_5` |
| 2 | `./autogen.sh && ./configure --prefix=/usr/local && make` |
| 3 | `DESTDIR` 安装到暂存树，补上 `smart-pkg-uninstall` |
| 4 | `pkgbuild --root ... --identifier com.smartmontools.pkg --install-location /` |
| 5 | `hdiutil create -volname "SmartmonTools Develop" -srcfolder dmg -fs HFS+ -format UDZO` |

卷名、`darwin/README.html`（dmg 内的说明页）可改；pkg 的 `identifier` 与
`com.smartmontools.smartd` 服务标识**不可改**，否则升级与卸载认不出旧安装。

未做：`Distribution` 自定义安装界面（需要 `productbuild` 再包一层），首版只出 component pkg。

## 状态说明

- `configure --host=x86_64-w64-mingw32` 是上游 `configure.ac` 明确支持的交叉编译路径（有 `mingw*` 分支）。
- **未验证**：在当前 `main` 上完整跑通交叉编译所需的确切参数组合、`make` 是否默认构建 man 页与脚本导致失败。
  首次跑 CI 若报错，按报错补 `--disable-*` 或在 `make` 时指定子目录目标，然后把有效参数写回本文件。
- 官方 Windows 发行包由 MinGW-w64 + NSIS 在 Linux 上交叉编译生成；本仓库暂不生成 NSIS 安装包，只出 zip。
