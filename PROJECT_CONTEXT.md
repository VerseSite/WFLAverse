# 学生校园网：项目上下文

更新时间：2026-10-29（Asia/Shanghai）。后续工作开始时先读取本文件。区分用户决策、实现选择和待定事项；取得实质进展后更新记录。

## 用户已确认

- 与学校同学合作开发以学生为主体的模块化、可扩展校园网。
- 用户负责主页后端；另一位同学负责正式前端。本项目提供最简页面供演示与后续对接。
- 当前交付主页、登录、注册与用户管理后端；开工前需求澄清已完成。
- 将来可能添加“校园委托与招聘”模块，用 tag 区分委托、竞赛组队、社团招聘等；本轮不实现该模块。
- 将来可能添加匿名论坛；本轮不实现，其匿名规则尚未定义。
- 当前只面向本校，不需要多学校租户系统。学校特征应易于移除，便于将来复用。
- 技术选型偏好：好维护、相对轻量，优先复用现成能力。
- 最初提出学生、老师、admin 三类用户，随后明确第一版不做老师账号。当前只有学生和 admin。
- admin 预计只有一两人，具有实际管理权限。
- 学生注册填写手机号和八位学号；明确不验证学生身份，无需审核、邀请码、学校名单或短信验证码。
- 手机号加密码登录；第一版忘记密码先报告给 admin，由 admin 重置。
- 主站使用真名，姓名、班级和简介向所有访客公开。手机号与学号仅本人及具有用户管理权限的 admin 可见。
- 用户同意按助手提出的最小主页和管理功能范围实现。由于取消身份验证，不实现注册审核。
- 已提供同学制作的独立 HTML 前端，当前以 Django 模板合并；未约定正式上线域名或部署环境。
- 用户有 Docker，当前先本地演示。Docker 排障期间用户明确说“先不用 docker 了”，停止继续 Docker 排障。用户并未要求放弃 PostgreSQL；SQLite 是助手为尽快演示启用的临时备用路径，不是用户确认的数据库替换决定。
- 用户要求记录项目相关信息以保证后续连续性。

## 已采用的实现选择

- Python 3.12 + Django 5.2 LTS，复用内置认证、密码校验、Cookie Session 和 admin 后台。
- requirements 固定 Django 5.2.18、psycopg[binary] 3.3.6。
- Docker Compose 使用 PostgreSQL 16；本地 Python 可使用 SQLite，无需 Docker 即可演示和测试。两种方式数据独立。
- `accounts` 管理账户，`core` 管理主页和演示页面；未来业务增加独立 Django app。
- JSON API 位于 `/api/v1/`，与 HTML 演示页复用表单和模型，按同源方式对接前端。
- 用户主键为 UUID，手机号和学号分别唯一，不作为未来业务记录外键。
- 手机号先支持 11 位中国大陆号码；学号为八位 ASCII 数字字符串，保留前导零。
- 班级自由填写，姓名与班级各最多 40 字；简介选填，最多 500 字。
- 学生自行修改简介和密码；姓名、班级、手机号、学号由 admin 修改。
- 公开接口采用字段白名单；admin 与停用账户不进入公开学生列表。
- 不设默认管理员或固定管理员密码，使用 `createsuperuser` 交互创建。
- Session 写操作启用 CSRF；登录和注册响应返回轮换后的 token。
- 数据库限流覆盖 HTML/API/admin 登录及注册、改密码；提供清理过期记录命令。
- Docker 演示只监听本机 127.0.0.1:8000，使用开发服务器，当前不是线上部署方案。
- 学校名称和管理员联系提示通过 `SITE_NAME`、`ADMIN_CONTACT` 配置。
- 主站真实身份与未来模块的展示身份分开设计；当前不承诺匿名论坛的匿名程度。

## 2026-10-16 前端合并

- 用户提供同学制作的 `WFLA VERSE.html`，要求与现有后端合并并删除多余页面。
- 用户明确选择：只保留已有后端支持的主页、账号与同学资料，其他模块只留筹备中入口。
- 已沿用原稿的渐变、玻璃卡片、Logo、字体层级和 Three.js 校园概念岛；未改动用户提供的原文件。
- 原稿为模拟单页原型，登录、验证码、角色切换和管理后台均非真实后端；本次没有保留这些模拟机制。
- 采用 Django 服务器模板直接接入原有认证表单和 Session。所有 JSON API 与原有页面 URL 保留。
- 仅保留学生/admin；手机号密码登录、八位学号、公开真名班级简介等原规则不变。
- `templates/verse/` 将认证页、账号设置页、同学列表/详情页分别共用模板；删除旧根目录简陋模板和 `static/site.css`。
- 首页学生人数及同学卡片使用真实数据库查询，隐藏停用账户与 admin，不显示手机号或学号。
- admin 使用真实 Django `/admin/` 后台，未导入原稿的模拟审核、权限矩阵或假用户。
- 默认品牌改为 WFLA VERSE，仍可通过 `SITE_NAME` 配置；修正了 Django LoginView 默认把站点名写成域名的问题。
- Tailwind 3.4.17 与 Three.js 0.128.0 沿用原稿版本；静态资源已本地化，Python 启动无需 CDN、Node.js 或额外编译。Node/pnpm 仅用于修改设计后重新构建资源。
- 构建配置与脚本：`package.json`、`pnpm-lock.yaml`、`tailwind.config.cjs`、`scripts/build-frontend.cjs`；生成资源在 `static/verse/`。
- 原稿出处与 SHA-256 记录于 `docs/FRONTEND_SOURCE.md`，Three.js MIT 许可证随资源保存。
- 本轮继续使用现有本地数据库演示路径，没有更换数据库、安装 PostgreSQL 或继续 Docker 排障。
- 36 项测试通过；新增测试覆盖前端表单接入、资料/密码提交、导航权限、公开数据与静态资源。Django 系统检查、迁移一致性、JS 语法与前端构建通过。
- 本轮浏览器工具已可正常访问本地服务；已检查桌面和 390px 手机视口、真实登录失败提示及主页 3D，前端控制台无 error。修正手机认证页插画过大问题，未向真实数据库写入测试账号。
- 合并效果截图保存在忽略的 `test-results/merged-home.jpg`。

## 2026-10-29 GitHub 提交约定

- 用户要求将当前版本提交并推送到 `https://github.com/VerseSite/WFLAverse`。
- 使用用户本人的 GitHub 账号 `zhenan-li`；已在 Git Credential Manager 中确认存在该账号。
- 提交作者和提交者使用 `李哲楠 <li_z_n@outlook.com>`，不添加助手署名或共同作者 trailer。
- 远端当前没有已有引用，本地尚无提交；使用 `main` 作为首次提交分支。
- 本轮只提交当前应用及文档，不改动应用业务功能。数据库、环境文件、依赖目录和截图保持忽略。
- 本地首次提交已完成，作者与提交者均为上述用户身份。推送被 GitHub 以 403 拒绝；用同一凭据查询目标仓库确认 `permissions.pull=true`、`permissions.push=false`。
- 后续需要仓库管理员为 `zhenan-li` 授予 Write 权限，或用户接受待处理的协作邀请，再执行 `git push -u origin main`。当前尚未成功上传到 GitHub。

## 后续待定（不影响本轮）

- 最终部署环境与将来业务模块的前端实现。
- 线上域名、HTTPS、正式密钥、备份和生产服务器配置。
- 老师账号与老师发布权限。
- 委托招聘的业务字段、tag、内容管理与权限。
- 匿名论坛的匿名程度、显示身份与管理规则。

## 关键文件

- `README.md`：Docker/Python 启动、创建管理员、管理操作和项目结构。
- `docs/API.md`：字段、错误格式、Cookie/CSRF 和前端调用示例。
- `accounts/models.py`、`forms.py`、`api.py`、`admin.py`、`middleware.py`：账户实现。
- `accounts/tests.py`：认证、权限、公开字段、管理操作和限流测试。
- `accounts/migrations/0001_initial.py`：初始数据库迁移。
- `compose.yaml`、`Dockerfile`、`docker/start.sh`：Docker 演示配置。
- `templates/verse/`、`static/verse/`：合并后的 WFLA VERSE 前端。

## 当前状态

- 工作区初始仅有 .git，没有应用代码。
- 后端、最简页面、API 文档、Docker 配置已实现。
- SQLite 路径 36 项测试通过；Django 系统检查通过；迁移已运行，无未生成的模型迁移。
- Docker Compose 配置语法检查通过；完整 Docker/PostgreSQL 运行验证未完成，用户明确暂不使用 Docker，配置仅保留备用。
- Python 本地服务已成功监听 127.0.0.1:8000，用于启动验证。
- 10 月 13 日浏览器访问曾被限制；10 月 16 日本轮可正常使用浏览器，已完成新版桌面与手机布局检查。
- 实际本机 HTTP 检查：`/health/` 返回 ok，`/api/v1/site/` 返回站点配置。
- Docker 环境排障：先遇到 WSL 查询超时；用户截图随后显示清理 `userAnalyticsOtlpHttp.sock` 失败。文件零字节且带 NTFS ReparsePoint，直接改名和 fsutil 查询均报系统无法访问。
- 已确认 Docker 进程退出、`AppData/Local/Docker/run` 只含该 socket，随后将该临时目录改名为 `run.stale-20261013` 保留备份，新建空 run 并重启 Docker。未删除容器、镜像或 WSL 数据。未再次观察到同一 socket 错误，但 Docker 引擎未就绪；依照用户决定不继续排查。
- 本机 .venv、依赖、SQLite 迁移已准备完成，README 开头的默认启动路径改为 Python。
- 用户随后询问“为啥不用 postgresql 了”：已解释不用 Docker 不等于不用 PostgreSQL，现有后端支持原生 PostgreSQL。只读检查未在 PATH、Windows 服务或 Program Files/PostgreSQL 目录中查到现成 PostgreSQL；尚未安装或启动原生 PostgreSQL。
