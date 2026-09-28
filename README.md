# 月饼配方本地业务服务

这是一个面向月饼配方与营养声明业务的可审计状态服务。数据保存在当前目录的 SQLite 文件中，命令行入口支持写入状态、查看单条记录和输出汇总。事件带有请求编号，重复提交会返回已有结果；事件历史用于恢复和追责。

## 目录

`moon_cake/` 按访问、审计、容量、合规、调度和恢复职责拆分模块，`app.py` 提供本地命令入口。

## 测试与构建

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall moon_cake app.py
```

## 使用

```bash
python3 app.py apply sample-1 示例 approved --actor operator --request req-1 --payload '{"amount": 1}'
python3 app.py show sample-1
python3 app.py summary
```
