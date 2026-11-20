# 许可

本项目以 **GNU General Public License, version 2 or (at your option) any later version** 发布，
与上游 smartmontools 一致。

## 许可证全文在哪

本仓库**不重复存放** GPL 全文（避免与官方文本出现差异），权威获取途径：

| 方式 | 位置 |
|---|---|
| 上游源码树 | `COPYING`（`https://github.com/smartmontools/smartmontools` 根目录） |
| GNU 官方 | https://www.gnu.org/licenses/old-licenses/gpl-2.0.txt |
| 构建产物 | Release 的 zip 内随包附带 `COPYING`（由 CI 从上游源码树复制） |

## 分发义务

若你转发本仓库构建出的二进制，必须同时：

1. 保留 `NOTICE` 与 `COPYING`
2. 提供完整对应源码：上游仓库（注明 revision）+ 本仓库 `patches/` 全部补丁
3. 以 GPL-2.0-or-later 授权你的分发

## 不授予的权利

GPL 不授予商标权。以本项目名义发布时不得暗示是 smartmontools 官方发行，见 `NOTICE`。
