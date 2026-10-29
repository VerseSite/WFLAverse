# 学生校园网后端

第一版实现主页、学生注册、手机号密码登录、个人资料、修改密码和 admin 用户管理。已合并同学提供的 WFLA VERSE 前端，沿用渐变、玻璃卡片、Logo 和校园概念岛视觉。网页表单和 JSON API 共用用户模型与校验规则。

## 当前规则

- 学生直接注册，不审核身份、不发送短信；真实姓名和班级由用户填写，不代表学校认证。
- 手机号为 11 位中国大陆号码，学号为 8 位数字字符串（保留前导零）；两者分别唯一。
- 学生注册需要真实姓名和班级，简介选填。姓名、班级、简介向未登录访客公开。
- 手机号和学号仅本人及具有用户管理权限的 admin 可见。
- 学生只能修改自己的简介和密码；姓名、班级、手机号、学号联系 admin 修改。
- 仅学生和 admin 两类角色。admin 通过命令行或管理后台创建，注册接口不能设置权限。老师账号暂不实现。
- 忘记密码先线下联系 admin，由 admin 重置；联系方式通过 `ADMIN_CONTACT` 设置。
- 仅保留主页、登录注册、账号设置、同学公开资料及真实 admin 后台。委托招聘、匿名论坛、影像等未来模块只在主页显示筹备中入口。
- 原前端的模拟验证码、身份切换、假管理后台、示例用户和未实现的业务页面没有导入；原有简陋页面已删除。

## 当前推荐：Python 本地演示

用户已决定第一版暂不使用 Docker。PostgreSQL 仍是原定数据库；SQLite 仅是无需安装数据库即可运行的临时演示路径。本机 `.venv`、依赖和 SQLite 数据库迁移已准备好。在项目目录直接启动：

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

在另一个终端创建自己的管理员账号（只需执行一次）：

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

主页 <http://127.0.0.1:8000/>，管理后台 <http://127.0.0.1:8000/admin/>。管理员手机号和密码由你交互输入。停止服务按 Ctrl+C；数据保存在被 Git 忽略的 `data/db.sqlite3` 中，重启保留。

换电脑时，按下方 Python 初始化步骤创建环境和迁移。Docker 配置保留为以后可选方案。

原生 PostgreSQL 也可以不用 Docker：安装并启动 PostgreSQL，创建专用数据库与用户，在启动 Django 的同一个终端设置 `POSTGRES_HOST`、`POSTGRES_DB`、`POSTGRES_USER`、`POSTGRES_PASSWORD`（可选 `POSTGRES_PORT`），然后运行迁移和启动命令。配置了 `POSTGRES_HOST` 后，后端自动使用 PostgreSQL。请勿把实际数据库密码写入代码或提交到 Git。切换后原先 SQLite 中的数据不会自动迁移。

## Docker 本地演示（备用）

先启动 Docker Desktop，确认使用 Linux containers。在项目目录运行：

```powershell
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

第二条命令交互式输入管理员手机号和密码；管理员无需学号。没有默认管理员或固定管理员密码。

- 主页：<http://localhost:8000/>
- 管理后台：<http://localhost:8000/admin/>
- 同学公开资料：<http://localhost:8000/members/>

首次启动自动迁移数据库。PostgreSQL 数据保存在 `campus_db` Docker volume，正常停止和重新构建不会清空。

```powershell
docker compose logs -f web
docker compose exec web python manage.py test
docker compose stop
```

`compose.yaml` 只监听本机 `127.0.0.1:8000`，数据库不向宿主机开放端口。它使用 Django 开发服务器，专供当前本地演示。

需要改站点名称或管理员联系方式时，可以复制 `.env.example` 为 `.env`，修改后运行 `docker compose up -d`。不要提交 `.env`。

## Python 环境初始化（换电脑或重建环境）

需要 Python 3.12。这个路径默认使用 SQLite，便于快速演示；Docker 使用 PostgreSQL。两种方式的数据相互独立。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

如果 Anaconda 创建 `.venv` 时 `ensurepip` 失败，但 `.venv\Scripts\python.exe` 已存在，可以使用宿主 Python 的 pip 安装：

```powershell
python -m pip --python .venv install -r requirements.txt
```

本地 Python 不自动读取 `.env`，用 PowerShell 环境变量配置。例如：

```powershell
$env:SITE_NAME = '学校校园网'
$env:ADMIN_CONTACT = '请联系校园网管理员：填写实际联系方式'
```

## admin 操作

在 `/admin/` 的“用户”中可以搜索用户、修改资料、停用账号、设置权限，以及通过“密码”字段旁的修改密码入口重置密码。

- 学生：`is_staff=False`、`is_superuser=False`。
- 完整 admin：同时勾选后台访问和超级用户权限。`is_staff` 单独勾选仅允许进入后台，具体管理权限还取决于组或授权。
- 停用账号后，其已有登录会话也无法继续访问登录功能，公开资料会隐藏。
- 重置密码后旧会话失效。请将临时密码线下交给用户，并让用户自行修改。
- 批量停用操作保留当前操作管理员；单个用户编辑仍需自行留意是否停用了自己。

认证请求采用数据库限流：15 分钟内同一 IP 最多 30 次登录请求，同一手机号最多 10 次登录请求；注册与修改密码分别最多 10 次/IP。HTML、API 和 admin 登录共享登录限流，达到上限返回 429 与 `Retry-After`。统计包含成功请求，重启服务不重置计数。

限流记录中的账号/IP键经过哈希。可定期清理过期记录：

```powershell
docker compose exec web python manage.py cleanup_auth_limits
```

## 前端对接与项目结构

当前前端由 Django 模板直接渲染，表单提交给同源 Django 页面，登录状态和权限来自服务器 Session。注册直接生效，忘记密码显示管理员联系方式，没有模拟发送邮件或短信。

原独立 HTML 的页面被收敛为 `templates/verse/` 下的主页、共用认证页、共用账号设置页、共用同学列表/详情页及错误页。所有原有账号 URL 和 `/api/v1/` 接口保留，后续也可以改用 JSON API。接口、CSRF 流程和示例见 [docs/API.md](docs/API.md)。

Tailwind 样式和 Three.js 已构建为本地资源，日常启动只需要 Python。要修改 Tailwind 类或重新生成资源，安装 Node.js 与 pnpm 后运行：

```powershell
pnpm install --frozen-lockfile --ignore-scripts
pnpm run build
```

构建配置见 `tailwind.config.cjs`，构建入口为 `scripts/build-frontend.cjs`；生成的 `static/verse/utilities.css`、Three.js 与许可证应随代码保留。`theme.css` 是从同学原稿提取的视觉样式，`integration.css` 是表单及响应式适配，`ui.js` 仅负责主题等界面行为，`campus.js` 负责概念岛。

不支持 WebGL 时显示静态校园岛插画。前端来源和修改范围见 [docs/FRONTEND_SOURCE.md](docs/FRONTEND_SOURCE.md)。

```text
accounts/    用户模型、表单、认证 API、后台与限流
core/        最简页面、主页配置、公共错误处理
config/      Django 设置和路由
templates/verse/  WFLA VERSE 页面及共用组件
static/verse/     本地样式、UI 脚本、SVG 与 3D 依赖
frontend/         Tailwind 构建输入
scripts/          前端静态资源构建脚本
docs/        API 对接说明
```

后续模块可以作为独立 Django app 添加，关联用户时使用 `settings.AUTH_USER_MODEL` 和稳定的 UUID，避免用手机号或学号做业务记录外键。用户展示身份与账户标识分开；未来匿名论坛规则尚未定义。

项目决策与当前进度记录在 [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)，后续开发约定在 [AGENTS.md](AGENTS.md)。

## 检查

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
docker compose config --quiet
```

36 项测试覆盖注册校验、密码哈希、重复账号、会话与 CSRF、越权修改、公开信息边界、停用和密码重置、admin 管理、页面转义和限流；还覆盖新前端的真实表单字段、资料/密码提交、登录前后导航、真实用户数据与本地资源。

上线前另行配置部署服务器、HTTPS、正式密钥、`DEBUG=0`、静态文件服务、数据库备份和代理环境限流。当前交付目标仅为本地演示。
