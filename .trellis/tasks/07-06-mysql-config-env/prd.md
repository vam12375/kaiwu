# 抽离 MySQL 数据库配置到环境变量

## Goal

将后端 MySQL 连接配置从源码硬编码改为从环境变量读取，避免账号、密码等敏感信息直接出现在代码中。

## Requirements

* `kaiwuback/server/config.py` 不再硬编码 MySQL 用户名、密码等真实连接信息。
* 后端通过环境变量读取 MySQL host、port、user、password、database、charset 等配置。
* 保留本地开发可启动的非敏感默认值，密码默认值必须为空。
* 文档说明需要设置的 MySQL 环境变量。
* 不改动数据库访问调用方的接口形状，继续通过 `DB_CONFIG` 使用。

## Acceptance Criteria

* [x] 源码中不再出现 MySQL 默认密码。
* [x] `DB_CONFIG` 仍可被 `server.persistence.database.get_db()` 直接使用。
* [x] README 后端环境变量表包含 MySQL 配置项。
* [x] 后端语法检查通过。

## Out of Scope

* 不迁移数据库结构。
* 不改变现有 MySQL 兜底/错误处理逻辑。
* 不提交或创建真实 `.env` 密钥文件。

## Technical Notes

* 相关文件：`kaiwuback/server/config.py`、`kaiwuback/server/persistence/database.py`、`README.md`。
