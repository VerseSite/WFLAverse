# 第一版 API

基础路径 `/api/v1/`，URL 末尾保留 `/`。写接口使用 JSON，请求头 `Content-Type: application/json`；所有 JSON 字段值使用字符串。学号不能作为数字发送，以免丢失前导零。

## 登录与 CSRF

使用 Django Cookie Session。浏览器保留 `sessionid`（HttpOnly）和 `csrftoken` Cookie。每次写操作都需要 `X-CSRFToken`，包括未登录时的注册和登录。

1. `GET /auth/csrf/` 获取 `{ "csrf_token": "…" }` 并设置 CSRF Cookie。
2. 注册或登录时带上 token 和 Cookie。
3. 注册、登录成功会轮换 CSRF token。使用成功响应中的新 `csrf_token`，或重新获取。
4. 后续所有 POST/PATCH 同样携带 CSRF token。退出后重新获取 token 再登录。

前后端同源示例：

```javascript
let csrfToken;

async function refreshCsrf() {
  const response = await fetch('/api/v1/auth/csrf/', {
    credentials: 'same-origin',
  });
  csrfToken = (await response.json()).csrf_token;
}

async function api(path, method = 'GET', data) {
  const writing = method !== 'GET';
  if (writing && !csrfToken) await refreshCsrf();
  const response = await fetch(`/api/v1/${path}`, {
    method,
    credentials: 'same-origin',
    headers: writing ? {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    } : {},
    body: writing ? JSON.stringify(data ?? {}) : undefined,
  });
  const result = await response.json();
  if (result.csrf_token) csrfToken = result.csrf_token;
  if (!response.ok) throw result.error;
  return result;
}

await refreshCsrf();
await api('auth/login/', 'POST', {
  phone: '13800138001',
  password: '用户输入的密码',
});
const { user } = await api('me/');
await api('me/', 'PATCH', { bio: '喜欢物理和工程' });
await api('auth/logout/', 'POST', {});
csrfToken = undefined;
```

正式前端使用开发服务器代理 `/api/` 到 `http://127.0.0.1:8000`，保留 Cookie；页面 origin 必须在 Django 接受的 origin 内。如果前端在 `http://localhost:5173`，需要设置 `DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:5173` 后重启后端（仅添加该实际使用的开发地址）。同域部署时不需要 CORS 配置。跨域方案另行配置，当前不启用通配跨域授权。

## 接口表

| 方法 | 路径 | 登录要求 | 行为 |
| --- | --- | --- | --- |
| GET | `/site/` | 无 | 站点名称、admin 联系说明和模块入口 |
| GET | `/auth/csrf/` | 无 | 获取 CSRF token |
| POST | `/auth/register/` | 无 | 创建学生账号并登录 |
| POST | `/auth/login/` | 无 | 手机号与密码登录 |
| POST | `/auth/logout/` | 有 | 退出当前会话 |
| POST | `/auth/password/` | 有 | 用旧密码修改密码 |
| GET | `/me/` | 有 | 查看本人完整资料 |
| PATCH | `/me/` | 有 | 仅修改本人简介 |
| GET | `/members/?page=1` | 无 | 学生公开资料列表，每页 20 人 |
| GET | `/members/<uuid>/` | 无 | 指定学生公开资料 |

另外，`GET /health/` 返回 `{ "status": "ok" }`，只代表应用可响应，不检测数据库健康。

## 注册

```json
{
  "phone": "13800138001",
  "student_id": "00123456",
  "real_name": "测试同学",
  "class_name": "Pre10-1",
  "bio": "喜欢物理与工程",
  "password": "实际用户自设的密码",
  "password_confirm": "实际用户自设的密码"
}
```

`bio` 可省略，其余必填。手机号 11 位中国大陆号码，学号 8 位 ASCII 数字，两者分别唯一。姓名和班级各最多 40 字，简介最多 500 字。密码至少 8 位，并接受 Django 的常见密码、纯数字和用户资料相似度检查。

成功为 201，返回本人资料和新的 CSRF token。注册直接生效，系统不核实手机号持有者或学校身份。重复资料通常返回 400 字段校验错误；数据库并发冲突时返回 409。

客户端不能提交 `role`、`is_staff`、`is_superuser` 等权限字段，未知字段被拒绝。

## 资料响应

本人资料（注册、登录、`GET/PATCH /me/`）：

```json
{
  "user": {
    "id": "由系统生成的UUID",
    "real_name": "测试同学",
    "class_name": "Pre10-1",
    "bio": "喜欢物理",
    "phone": "13800138001",
    "student_id": "00123456",
    "role": "student"
  }
}
```

`role` 为 `student` 或 `admin`。admin 可以没有学号，`student_id` 此时为 `null`。角色由服务器权限推导，不能通过本人资料接口修改。

公开单个资料只返回 `id`、`real_name`、`class_name`、`bio`。列表格式为：

```json
{
  "users": [{ "id": "UUID", "real_name": "测试同学", "class_name": "Pre10-1", "bio": "喜欢物理" }],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

公开列表不包含 admin 或停用账号；指定不存在、停用或 admin 的 UUID 返回 404。列表默认按注册时间、UUID 排序；`page` 范围 1～100000，超出实际页数返回空列表。

本人修改简介：`PATCH /me/`，请求 `{ "bio": "新简介" }`。清空简介传空字符串。修改姓名、班级、手机号、学号联系 admin。

## 修改密码与退出

`POST /auth/password/`：

```json
{
  "old_password": "当前密码",
  "new_password": "新密码",
  "new_password_confirm": "新密码"
}
```

成功返回 `{ "message": "密码已修改。" }`，保留当前会话、使其他旧会话失效。

`POST /auth/logout/` 请求 `{}`，成功返回 `{ "message": "已退出登录。" }`。忘记密码没有自助重置 API，前端展示 `/site/` 中的 `admin_contact`。

## 错误

```json
{
  "error": {
    "code": "validation_error",
    "message": "请检查填写内容。",
    "fields": { "student_id": ["学号必须是 8 位数字。"] }
  }
}
```

`fields` 仅在字段校验错误时出现，`__all__` 表示表单整体错误。注册密码错误字段使用 `password`/`password_confirm`，改密码使用 `old_password`/`new_password`/`new_password_confirm`。

| 状态 | 含义 |
| --- | --- |
| 400 | 字段校验、JSON 格式、未知字段或分页参数错误 |
| 401 | 未登录，或账号/密码错误（停用账号与错误账号使用同一登录提示） |
| 403 | CSRF 失败或权限不足 |
| 404 | 指定公开用户不存在 |
| 405 | HTTP 方法错误，响应 `Allow` 列出支持方法 |
| 409 | 注册时数据库并发唯一性冲突 |
| 413 | API 解析时发现请求体过大 |
| 415 | 写接口没有使用 `application/json` |
| 429 | 限流，`Retry-After` 为建议等待秒数 |

CSRF 检查先于业务校验：缺少 token 的未登录写请求可能先返回 403。调试模式下未知路由或框架异常可能返回 Django HTML 调试页面；前端调用上表内有效接口，不应依赖调试异常响应。

前端展示姓名和简介使用文本渲染，不把用户输入直接写入 `innerHTML`。
