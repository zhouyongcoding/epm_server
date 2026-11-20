from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


# ---------- Project ----------

class ProjectCreate(BaseModel):
    name: str
    customer: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    status: str = "未开始"
    description: str = ""

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("项目名称不能为空")
        return v.strip()

    @field_validator("start_date", "end_date")
    @classmethod
    def date_format(cls, v: str) -> str:
        v = v.strip()
        if v and not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("日期格式必须为 YYYY-MM-DD")
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    customer: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    customer: str
    location: str
    start_date: str
    end_date: str
    status: str
    description: str
    created_by: str = ""
    updated_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------- Product ----------

class ProductCreate(BaseModel):
    product_code: str
    product_name: str
    product_image: str = ""
    status: str = "启用"
    notes: str = ""
    created_by: str = ""

    @field_validator("product_code")
    @classmethod
    def code_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("产品代号不能为空")
        return v.strip()

    @field_validator("product_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("产品名称不能为空")
        return v.strip()


class ProductImageOut(BaseModel):
    id: int
    product_id: int
    image_path: str
    sort_order: int
    full_url: str | None = None

    model_config = {"from_attributes": True}


class ProductUpdate(BaseModel):
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    product_image: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    updated_by: str | None = None


class ProductOut(BaseModel):
    id: int
    product_code: str
    product_name: str
    product_image: str
    status: str
    notes: str
    created_by: str = ""
    updated_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    images: list[ProductImageOut] = []

    model_config = {"from_attributes": True}


# ---------- Role ----------

class RoleCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("角色名称不能为空")
        return v.strip()


class RoleUpdate(BaseModel):
    name: Optional[str] = None


class RoleOut(BaseModel):
    id: int
    name: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoleOutWithPerms(RoleOut):
    permissions: list[PermissionOut] = []


class RoleUpdatePermissions(BaseModel):
    permission_ids: list[int] = []


# ---------- Permission ----------

SYSTEM_MODULES = [
    "项目管理",
    "产品管理",
    "工艺管理",
    "工序管理",
    "项目进度",
    "产品进度",
    "工序进度",
    "任务管理",
    "任务统计",
    "角色管理",
    "权限管理",
    "用户管理",
]

PERMISSION_TYPES = {
    "menu": "菜单权限",
    "button": "按钮权限",
    "api": "接口权限",
}

BUTTON_ACTIONS = ["新增", "编辑", "删除", "导出", "审核", "驳回", "打印"]

PERMISSION_DEFS: list[dict] = [
    # -------------------- 菜单权限 --------------------
    {"module": "项目管理", "perm_type": "menu", "action": "工程项目页面", "code": "project:menu", "description": "能否看到【工程项目】Tab页面"},
    {"module": "产品管理", "perm_type": "menu", "action": "产品管理页面", "code": "product:menu", "description": "能否看到【产品管理】Tab页面"},
    {"module": "工艺管理", "perm_type": "menu", "action": "工艺管理页面", "code": "craft:menu", "description": "能否看到【工艺管理】Tab页面"},
    {"module": "工序管理", "perm_type": "menu", "action": "工序管理页面", "code": "process:menu", "description": "能否看到【工序管理】Tab页面"},
    {"module": "项目进度", "perm_type": "menu", "action": "项目进度页面", "code": "project_progress:menu", "description": "能否看到【项目进度】Tab页面"},
    {"module": "产品进度", "perm_type": "menu", "action": "产品进度页面", "code": "product_progress:menu", "description": "能否看到【产品进度】Tab页面"},
    {"module": "工序进度", "perm_type": "menu", "action": "工序进度页面", "code": "process_progress:menu", "description": "能否看到【工序进度】Tab页面"},
    {"module": "任务管理", "perm_type": "menu", "action": "我的任务页面", "code": "task:menu", "description": "能否看到【我的任务】Tab页面"},
    {"module": "任务统计", "perm_type": "menu", "action": "任务统计页面", "code": "task_stats:menu", "description": "能否看到【任务统计】Tab页面"},
    {"module": "角色管理", "perm_type": "menu", "action": "角色管理页面", "code": "role:menu", "description": "能否看到【角色管理】Tab页面"},
    {"module": "权限管理", "perm_type": "menu", "action": "权限管理页面", "code": "permission:menu", "description": "能否看到【权限管理】Tab页面"},
    {"module": "用户管理", "perm_type": "menu", "action": "用户管理页面", "code": "user:menu", "description": "能否看到【用户管理】Tab页面"},
    # -------------------- 按钮权限 --------------------
    {"module": "项目管理", "perm_type": "button", "action": "新增", "code": "project:create", "description": "能否新增项目"},
    {"module": "项目管理", "perm_type": "button", "action": "编辑", "code": "project:edit", "description": "能否编辑项目"},
    {"module": "项目管理", "perm_type": "button", "action": "删除", "code": "project:delete", "description": "能否删除项目"},
    {"module": "项目管理", "perm_type": "button", "action": "导出", "code": "project:export", "description": "能否导出项目"},
    {"module": "项目管理", "perm_type": "button", "action": "审核", "code": "project:audit", "description": "能否审核项目"},
    {"module": "项目管理", "perm_type": "button", "action": "驳回", "code": "project:reject", "description": "能否驳回项目"},
    {"module": "项目管理", "perm_type": "button", "action": "打印", "code": "project:print", "description": "能否打印项目"},
    {"module": "产品管理", "perm_type": "button", "action": "新增", "code": "product:create", "description": "能否新增产品"},
    {"module": "产品管理", "perm_type": "button", "action": "编辑", "code": "product:edit", "description": "能否编辑产品"},
    {"module": "产品管理", "perm_type": "button", "action": "删除", "code": "product:delete", "description": "能否删除产品"},
    {"module": "产品管理", "perm_type": "button", "action": "导出", "code": "product:export", "description": "能否导出产品"},
    {"module": "产品管理", "perm_type": "button", "action": "审核", "code": "product:audit", "description": "能否审核产品"},
    {"module": "产品管理", "perm_type": "button", "action": "驳回", "code": "product:reject", "description": "能否驳回产品"},
    {"module": "产品管理", "perm_type": "button", "action": "打印", "code": "product:print", "description": "能否打印产品"},
    {"module": "工艺管理", "perm_type": "button", "action": "新增", "code": "craft:create", "description": "能否新增工艺"},
    {"module": "工艺管理", "perm_type": "button", "action": "编辑", "code": "craft:edit", "description": "能否编辑工艺"},
    {"module": "工艺管理", "perm_type": "button", "action": "删除", "code": "craft:delete", "description": "能否删除工艺"},
    {"module": "工艺管理", "perm_type": "button", "action": "导出", "code": "craft:export", "description": "能否导出工艺"},
    {"module": "工序管理", "perm_type": "button", "action": "新增", "code": "process:create", "description": "能否新化工序"},
    {"module": "工序管理", "perm_type": "button", "action": "编辑", "code": "process:edit", "description": "能否编辑工序"},
    {"module": "工序管理", "perm_type": "button", "action": "删除", "code": "process:delete", "description": "能否删除工序"},
    {"module": "工序管理", "perm_type": "button", "action": "导出", "code": "process:export", "description": "能否导出工序"},
    {"module": "项目进度", "perm_type": "button", "action": "新增", "code": "project_progress:create", "description": "能否新增项目进度"},
    {"module": "项目进度", "perm_type": "button", "action": "编辑", "code": "project_progress:edit", "description": "能否编辑项目进度"},
    {"module": "项目进度", "perm_type": "button", "action": "删除", "code": "project_progress:delete", "description": "能否删除项目进度"},
    {"module": "产品进度", "perm_type": "button", "action": "新增", "code": "product_progress:create", "description": "能否新增产品进度"},
    {"module": "产品进度", "perm_type": "button", "action": "编辑", "code": "product_progress:edit", "description": "能否编辑产品进度"},
    {"module": "产品进度", "perm_type": "button", "action": "删除", "code": "product_progress:delete", "description": "能否删除产品进度"},
    {"module": "工序进度", "perm_type": "button", "action": "新增", "code": "process_progress:create", "description": "能否新加工序进度"},
    {"module": "工序进度", "perm_type": "button", "action": "编辑", "code": "process_progress:edit", "description": "能否编辑工序进度"},
    {"module": "工序进度", "perm_type": "button", "action": "删除", "code": "process_progress:delete", "description": "能否删除工序进度"},
    {"module": "任务管理", "perm_type": "button", "action": "新增", "code": "task:create", "description": "能否新增任务"},
    {"module": "任务管理", "perm_type": "button", "action": "编辑", "code": "task:edit", "description": "能否编辑任务"},
    {"module": "任务管理", "perm_type": "button", "action": "删除", "code": "task:delete", "description": "能否删除任务"},
    {"module": "任务管理", "perm_type": "button", "action": "导出", "code": "task:export", "description": "能否导出任务"},
    {"module": "任务统计", "perm_type": "button", "action": "导出", "code": "task_stats:export", "description": "能否导出任务统计"},
    {"module": "角色管理", "perm_type": "button", "action": "新增", "code": "role:create", "description": "能否新增角色"},
    {"module": "角色管理", "perm_type": "button", "action": "编辑", "code": "role:edit", "description": "能否编辑角色"},
    {"module": "角色管理", "perm_type": "button", "action": "删除", "code": "role:delete", "description": "能否删除角色"},
    {"module": "权限管理", "perm_type": "button", "action": "新增", "code": "permission:create", "description": "能否新增权限"},
    {"module": "权限管理", "perm_type": "button", "action": "编辑", "code": "permission:edit", "description": "能否编辑权限"},
    {"module": "权限管理", "perm_type": "button", "action": "删除", "code": "permission:delete", "description": "能否删除权限"},
    {"module": "用户管理", "perm_type": "button", "action": "新增", "code": "user:create", "description": "能否新增用户"},
    {"module": "用户管理", "perm_type": "button", "action": "编辑", "code": "user:edit", "description": "能否编辑用户"},
    {"module": "用户管理", "perm_type": "button", "action": "删除", "code": "user:delete", "description": "能否删除用户"},
    # -------------------- 接口权限 --------------------
    {"module": "项目管理", "perm_type": "api", "action": "调用接口", "code": "project:api", "description": "能否调用项目管理后端接口"},
    {"module": "产品管理", "perm_type": "api", "action": "调用接口", "code": "product:api", "description": "能否调用产品管理后端接口"},
    {"module": "工艺管理", "perm_type": "api", "action": "调用接口", "code": "craft:api", "description": "能否调用工艺管理后端接口"},
    {"module": "工序管理", "perm_type": "api", "action": "调用接口", "code": "process:api", "description": "能否调用工序管理后端接口"},
    {"module": "任务管理", "perm_type": "api", "action": "调用接口", "code": "task:api", "description": "能否调用任务管理后端接口"},
    {"module": "任务统计", "perm_type": "api", "action": "调用接口", "code": "task_stats:api", "description": "能否调用任务统计后端接口"},
    {"module": "角色管理", "perm_type": "api", "action": "调用接口", "code": "role:api", "description": "能否调用角色管理后端接口"},
    {"module": "权限管理", "perm_type": "api", "action": "调用接口", "code": "permission:api", "description": "能否调用权限管理后端接口"},
    {"module": "用户管理", "perm_type": "api", "action": "调用接口", "code": "user:api", "description": "能否调用用户管理后端接口"},
]


class PermissionCreate(BaseModel):
    module: str
    perm_type: str = "menu"
    action: str = ""
    code: str = ""
    description: str = ""

    @field_validator("module")
    @classmethod
    def module_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("所属模块不能为空")
        return v.strip()

    @field_validator("perm_type")
    @classmethod
    def perm_type_valid(cls, v: str) -> str:
        if v not in PERMISSION_TYPES:
            raise ValueError(f"权限类型必须是: {', '.join(PERMISSION_TYPES.keys())}")
        return v


class PermissionUpdate(BaseModel):
    module: Optional[str] = None
    perm_type: Optional[str] = None
    action: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class PermissionOut(BaseModel):
    id: int
    module: str
    perm_type: str
    action: str
    code: str
    description: str

    model_config = {"from_attributes": True}


# ---------- User ----------

class UserCreate(BaseModel):
    username: str
    password: str
    name: str = ""
    employee_no: str = ""
    status: str = "活跃"
    role_id: int | None = None

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("用户名不能为空")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("密码不能为空")
        return v.strip()


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    employee_no: Optional[str] = None
    status: Optional[str] = None
    role_id: Optional[int] = None


class UserOut(BaseModel):
    id: int
    username: str
    name: str = ""
    employee_no: str = ""
    status: str = "活跃"
    role_id: int | None = None
    role_name: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------- Task ----------

class TaskCreate(BaseModel):
    user_id: int
    project_id: int | None = None
    product_id: int | None = None
    task_date: str
    content: str
    plan_start_time: str = ""
    plan_end_time: str = ""
    actual_start_time: str = ""
    actual_end_time: str = ""
    status: str = "待办"
    progress: int = 0
    note: str = ""

    @field_validator("task_date")
    @classmethod
    def date_format(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("日期格式必须为 YYYY-MM-DD")
        return v

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("任务内容不能为空")
        return v.strip()

    @field_validator("plan_start_time", "plan_end_time", "actual_start_time", "actual_end_time")
    @classmethod
    def time_format(cls, v: str) -> str:
        v = v.strip()
        if v and not re.match(r"^\d{1,2}:\d{2}$", v):
            raise ValueError("时间格式必须为 HH:MM")
        return v

    @field_validator("progress")
    @classmethod
    def progress_range(cls, v: int) -> int:
        return max(0, min(100, v))


class TaskUpdate(BaseModel):
    project_id: int | None = None
    product_id: int | None = None
    task_date: str | None = None
    content: str | None = None
    plan_start_time: str | None = None
    plan_end_time: str | None = None
    actual_start_time: str | None = None
    actual_end_time: str | None = None
    status: str | None = None
    progress: int | None = None
    note: str | None = None


class TaskOut(BaseModel):
    id: int
    user_id: int
    project_id: int | None = None
    product_id: int | None = None
    task_date: str
    content: str
    plan_start_time: str
    plan_end_time: str
    actual_start_time: str
    actual_end_time: str
    status: str
    progress: int
    note: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------- Craft ----------

class CraftCreate(BaseModel):
    project_id: int | None = None
    product_id: int | None = None
    craft_code: str = ""
    craft_name: str
    description: str = ""
    status: str = "启用"
    created_by: str = ""

    @field_validator("craft_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("工艺名称不能为空")
        return v.strip()


class CraftUpdate(BaseModel):
    project_id: int | None = None
    product_id: int | None = None
    craft_code: Optional[str] = None
    craft_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    updated_by: str | None = None


class CraftOut(BaseModel):
    id: int
    project_id: int | None = None
    product_id: int | None = None
    craft_code: str
    craft_name: str
    description: str
    status: str
    created_by: str = ""
    updated_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    processes: list["ProcessOut"] = []

    model_config = {"from_attributes": True}


# ---------- Process ----------

class ProcessCreate(BaseModel):
    craft_id: int
    process_code: str = ""
    process_name: str
    sort_order: int = 0
    duration: str = ""
    equipment: str = ""
    description: str = ""
    status: str = "启用"
    created_by: str = ""

    @field_validator("process_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("工序名称不能为空")
        return v.strip()


class ProcessUpdate(BaseModel):
    craft_id: int | None = None
    process_code: Optional[str] = None
    process_name: Optional[str] = None
    sort_order: Optional[int] = None
    duration: Optional[str] = None
    equipment: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    updated_by: str | None = None


class ProcessOut(BaseModel):
    id: int
    craft_id: int
    process_code: str
    process_name: str
    sort_order: int
    duration: str
    equipment: str
    description: str
    status: str
    created_by: str = ""
    updated_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------- Project Progress ----------

class ProjectProgressCreate(BaseModel):
    project_id: int | None = None
    plan_start_date: str = ""
    plan_end_date: str = ""
    actual_start_date: str = ""
    actual_end_date: str = ""
    progress: int = 0
    status: str = "未开始"
    note: str = ""

    @field_validator("plan_start_date", "plan_end_date", "actual_start_date", "actual_end_date")
    @classmethod
    def date_format(cls, v: str) -> str:
        v = v.strip()
        if v and not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("日期格式必须为 YYYY-MM-DD")
        return v

    @field_validator("progress")
    @classmethod
    def progress_range(cls, v: int) -> int:
        return max(0, min(100, v))


class ProjectProgressUpdate(BaseModel):
    project_id: int | None = None
    plan_start_date: str | None = None
    plan_end_date: str | None = None
    actual_start_date: str | None = None
    actual_end_date: str | None = None
    progress: int | None = None
    status: str | None = None
    note: str | None = None
    updated_by: str | None = None


class ProjectProgressOut(BaseModel):
    id: int
    project_id: int | None = None
    project_name: str | None = None
    plan_start_date: str
    plan_end_date: str
    actual_start_date: str
    actual_end_date: str
    progress: int
    status: str
    note: str
    created_by: str = ""
    updated_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------- Product Progress ----------

class ProductProgressCreate(BaseModel):
    project_id: int | None = None
    product_id: int | None = None
    plan_start_date: str = ""
    plan_end_date: str = ""
    actual_start_date: str = ""
    actual_end_date: str = ""
    progress: int = 0
    status: str = "未开始"
    note: str = ""

    @field_validator("plan_start_date", "plan_end_date", "actual_start_date", "actual_end_date")
    @classmethod
    def date_format(cls, v: str) -> str:
        v = v.strip()
        if v and not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("日期格式必须为 YYYY-MM-DD")
        return v

    @field_validator("progress")
    @classmethod
    def progress_range(cls, v: int) -> int:
        return max(0, min(100, v))


class ProductProgressUpdate(BaseModel):
    project_id: int | None = None
    product_id: int | None = None
    plan_start_date: str | None = None
    plan_end_date: str | None = None
    actual_start_date: str | None = None
    actual_end_date: str | None = None
    progress: int | None = None
    status: str | None = None
    note: str | None = None
    updated_by: str | None = None


class ProductProgressOut(BaseModel):
    id: int
    project_id: int | None = None
    project_name: str | None = None
    product_id: int | None = None
    product_name: str | None = None
    plan_start_date: str
    plan_end_date: str
    actual_start_date: str
    actual_end_date: str
    progress: int
    status: str
    note: str
    created_by: str = ""
    updated_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------- Process Progress ----------

class ProcessProgressCreate(BaseModel):
    project_id: int | None = None
    product_id: int | None = None
    craft_id: int | None = None
    process_id: int | None = None
    assigned_to: str = ""
    plan_start_date: str = ""
    plan_end_date: str = ""
    actual_start_date: str = ""
    actual_end_date: str = ""
    progress: int = 0
    status: str = "未开始"
    note: str = ""

    @field_validator("plan_start_date", "plan_end_date", "actual_start_date", "actual_end_date")
    @classmethod
    def date_format(cls, v: str) -> str:
        v = v.strip()
        if v and not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("日期格式必须为 YYYY-MM-DD")
        return v

    @field_validator("progress")
    @classmethod
    def progress_range(cls, v: int) -> int:
        return max(0, min(100, v))


class ProcessProgressUpdate(BaseModel):
    project_id: int | None = None
    product_id: int | None = None
    craft_id: int | None = None
    process_id: int | None = None
    assigned_to: str | None = None
    plan_start_date: str | None = None
    plan_end_date: str | None = None
    actual_start_date: str | None = None
    actual_end_date: str | None = None
    progress: int | None = None
    status: str | None = None
    note: str | None = None
    updated_by: str | None = None


class ProcessProgressOut(BaseModel):
    id: int
    project_id: int | None = None
    project_name: str | None = None
    product_id: int | None = None
    product_name: str | None = None
    craft_id: int | None = None
    craft_name: str | None = None
    process_id: int | None = None
    process_name: str | None = None
    assigned_to: str
    plan_start_date: str
    plan_end_date: str
    actual_start_date: str
    actual_end_date: str
    progress: int
    status: str
    note: str
    created_by: str = ""
    updated_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------- OperationLog ----------

class OperationLogCreate(BaseModel):
    action: str
    module: str
    target_id: int | None = None
    target_name: str = ""
    project_id: int | None = None
    product_id: int | None = None
    craft_id: int | None = None
    process_id: int | None = None
    old_value: str = ""
    new_value: str = ""
    operator: str = ""
    operator_id: int | None = None
    ip_address: str = ""
    remark: str = ""


class OperationLogOut(BaseModel):
    id: int
    action: str
    module: str
    target_id: int | None = None
    target_name: str
    project_id: int | None = None
    product_id: int | None = None
    craft_id: int | None = None
    process_id: int | None = None
    old_value: str
    new_value: str
    operator: str
    operator_id: int | None = None
    ip_address: str
    remark: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class OperationLogQuery(BaseModel):
    module: str | None = None
    action: str | None = None
    project_id: int | None = None
    product_id: int | None = None
    craft_id: int | None = None
    process_id: int | None = None
    operator: str | None = None
    start_date: str | None = None
    end_date: str | None = None