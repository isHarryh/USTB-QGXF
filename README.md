USTB-QGXF
==========
Auto complete USTB QiangGuoXianFeng series lessons  
北京科技大学强国先锋系列课程自动代理（国防教育/DXPX）**` v2.2 `**

<sup> This project only supports Chinese docs. If you are an English user, feel free to contact us. </sup>

-----

> **警告：** 请避免在国内社交媒体平台等公共空间传播本项目。


## 介绍 <sub>Intro</sub>

本项目实现了无人值守式地自动完成《北京科技大学强国先锋》系列课程的线上课程任务的功能，包括[北京科技大学国防教育平台](https://gfjy.ustb.edu.cn)和[北京科技大学 DXPX 平台](https://dxpx.ustb.edu.cn)。

### 实现的功能

1. **平台选择和登录：**  
   启动程序后，可以选择目标平台。手动输入账号密码后，会显示验证码图片，手动输入验证码后，即可完成登录。
2. **视频课程自动完成：**  
   自动获取视频课程列表，并模拟观看视频的操作（每隔若干秒向服务器报告一次播放进度）。
   > 支持多个视频同时进行。“观看”的过程中并不会下载和播放视频文件，而只是上报播放进度。
3. **章节测验自动完成：**  
   自动获取章节测验列表，并自动完成测验。
   > 章节测验不限答题次数，程序会通过不断试错来记住答案，直到达到指定的分数后（或达到某个最大尝试次数后）结束。
4. **考试自动完成：**  
   自动完成考试（例如结业考试）。
   > 结业考试可能会有答题次数的限制，所以我们规定，只有在用户手动输入考试编号后才会执行一次考试。
5. **基于配置文件的记忆：**  
   可以记住登录状态和题目的参考答案，详见[配置文件](#配置文件-configuration)章节。

### 功能性更新日志

- `v2.2` 新增了对考试的全面支持。
- `v2.1` 新增了基于配置文件的记忆，支持持久化保存题库；新增了全新的终端界面，提供更好的交互体验。
- `v2.0` 新增了对 DXPX 平台的支持。

## 使用方法 <sub>Usage</sub>

### A. 推荐方案

对于 Windows 系统，可前往 [Releases](https://github.com/isHarryh/USTB-QGXF/releases) 页面，下载 EXE 文件。下载完成后直接运行，然后跟随程序的指引来操作即可。

### B. 备选方案

对于非 Windows 系统或者开发者，可[下载](https://github.com/isHarryh/USTB-QGXF/archive/refs/heads/main.zip)（或克隆）本仓库的源码。确保已安装 [Python](https://www.python.org) 3.9+ 运行环境，并安装了 Pillow、pycryptodome、requests 库（有条件者建议使用 [Poetry](https://python-poetry.org) 依赖管理工具）。最后，运行 `Main.py` 即可。

## 配置文件 <sub>Configuration</sub>

下面介绍配置文件的格式，以便高级用户使用。如果您不清楚您在做什么，请不要修改配置文件。

配置文件直接位于程序的工作目录下，命名为 `USTB-QGXF-Config.json`。配置文件不存在时会自动创建。配置文件的内容示例如下：

```json
{
    "connection": {
        "baseUrl": "https://...",
        "token": "Ygp...bDg=="
    },
    "memory": {
        "0": {
            "title": "This is an example multiple-selection question record.",
            "type": 2,
            "answers": {
                "1": {
                    "title": "Example option 1."
                },
                "2": {
                    "title": "Example option 2."
                },
                "3": {
                    "title": "Example option 3."
                }
            },
            "rightAnswer": "1|2|3",
            "stageId": 0
        }
    }
}
```

`connection` 字段保存了上一次登录的基本信息，包括 `baseUrl`（平台的网址）和 `token`（令牌）。当这 `baseUrl` 和 `token` 都不为空时，程序运行后会验证登录信息是否有效，如果登录失效，则会回退到手动登录模式。

`memory` 字段中，以题目 ID 为键，保存着先前已经遇到过的题目的信息。每次课程考试结束，都会获取该次考试的参考答案，然后对 `memory` 进行增量更新。

## 许可证 <sub>Licensing</sub>

本项目基于 **MIT 开源许可证**，详情参见 [License](https://github.com/isHarryh/USTB-QGXF/blob/main/LICENSE) 页面。
