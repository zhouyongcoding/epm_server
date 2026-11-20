from __future__ import annotations

import hashlib
from typing import Optional

from sqlalchemy.orm import Session

from app import models, schemas


# ---------- helpers ----------

def _search_filter(query, model, q: str | None, fields: list):
    if q:
        filters = []
        for f in fields:
            filters.append(getattr(model, f).ilike(f"%{q}%"))
        from sqlalchemy import or_
        query = query.filter(or_(*filters))
    return query


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ---------- projects ----------

def list_projects(db: Session, q: str | None = None) -> list[models.Project]:
    query = db.query(models.Project)
    query = _search_filter(query, models.Project, q, ["name", "customer", "location", "status", "description"])
    return query.all()


def create_project(db: Session, data: schemas.ProjectCreate) -> models.Project:
    obj = models.Project(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_project(db: Session, project_id: int) -> models.Project | None:
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def update_project(db: Session, project_id: int, data: schemas.ProjectUpdate) -> models.Project | None:
    obj = get_project(db, project_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_project(db: Session, project_id: int) -> bool:
    obj = get_project(db, project_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# ---------- products ----------

def list_products(db: Session, q: str | None = None) -> list[models.Product]:
    query = db.query(models.Product)
    query = _search_filter(query, models.Product, q, ["product_code", "product_name", "status", "notes"])
    return query.all()


def create_product(db: Session, data: schemas.ProductCreate) -> models.Product:
    obj = models.Product(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_product(db: Session, product_id: int) -> models.Product | None:
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def update_product(db: Session, product_id: int, data: schemas.ProductUpdate) -> models.Product | None:
    obj = get_product(db, product_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_product(db: Session, product_id: int) -> bool:
    obj = get_product(db, product_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# ---------- product images ----------

import os
from uuid import uuid4

BASE_IMAGE_DIR = r"E:\images"
IMAGE_CATEGORIES = {
    "product": "product_imgs",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


def _get_image_dir(category: str) -> str:
    folder = IMAGE_CATEGORIES.get(category, category)
    full_dir = os.path.join(BASE_IMAGE_DIR, folder)
    os.makedirs(full_dir, exist_ok=True)
    return full_dir


def _save_upload_file(upload_file, category: str = "product") -> str:
    image_dir = _get_image_dir(category)
    ext = os.path.splitext(upload_file.filename or ".jpg")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"
    filename = f"{uuid4().hex}{ext}"
    filepath = os.path.join(image_dir, filename)
    with open(filepath, "wb") as f:
        f.write(upload_file.file.read())
    folder = IMAGE_CATEGORIES.get(category, category)
    return f"images/{folder}/{filename}"


def list_product_images(db: Session, product_id: int) -> list[models.ProductImage]:
    return (
        db.query(models.ProductImage)
        .filter(models.ProductImage.product_id == product_id)
        .order_by(models.ProductImage.sort_order)
        .all()
    )


def create_product_image(db: Session, product_id: int, upload_file, sort_order: int = 0) -> models.ProductImage:
    image_path = _save_upload_file(upload_file)
    obj = models.ProductImage(
        product_id=product_id,
        image_path=image_path,
        sort_order=sort_order,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_product_image(db: Session, image_id: int) -> bool:
    obj = db.query(models.ProductImage).filter(models.ProductImage.id == image_id).first()
    if not obj:
        return False
    if obj.image_path.startswith("images/"):
        rel_path = obj.image_path[len("images/"):]
        filepath = os.path.join(BASE_IMAGE_DIR, rel_path)
    else:
        filepath = os.path.join(os.path.dirname(__file__), "..", obj.image_path)
    if os.path.isfile(filepath):
        os.remove(filepath)
    db.delete(obj)
    db.commit()
    return True


# ---------- roles ----------

def list_roles(db: Session, q: str | None = None) -> list[models.Role]:
    query = db.query(models.Role)
    query = _search_filter(query, models.Role, q, ["name"])
    return query.all()


def create_role(db: Session, data: schemas.RoleCreate) -> models.Role:
    obj = models.Role(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_role(db: Session, role_id: int) -> models.Role | None:
    return db.query(models.Role).filter(models.Role.id == role_id).first()


def update_role(db: Session, role_id: int, data: schemas.RoleUpdate) -> models.Role | None:
    obj = get_role(db, role_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_role(db: Session, role_id: int) -> bool:
    obj = get_role(db, role_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def set_role_permissions(db: Session, role_id: int, permission_ids: list[int]) -> models.Role | None:
    role = get_role(db, role_id)
    if not role:
        return None
    permissions = db.query(models.Permission).filter(models.Permission.id.in_(permission_ids)).all()
    role.permissions = permissions
    db.commit()
    db.refresh(role)
    return role


# ---------- permissions ----------

def list_permissions(db: Session, q: str | None = None) -> list[models.Permission]:
    query = db.query(models.Permission)
    if q:
        from sqlalchemy import or_
        query = query.filter(or_(
            models.Permission.module.ilike(f"%{q}%"),
            models.Permission.action.ilike(f"%{q}%"),
            models.Permission.code.ilike(f"%{q}%"),
            models.Permission.description.ilike(f"%{q}%"),
        ))
    return query.order_by(models.Permission.module, models.Permission.perm_type, models.Permission.id).all()


def create_permission(db: Session, data: schemas.PermissionCreate) -> models.Permission:
    obj = models.Permission(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_permission(db: Session, permission_id: int) -> models.Permission | None:
    return db.query(models.Permission).filter(models.Permission.id == permission_id).first()


def update_permission(db: Session, permission_id: int, data: schemas.PermissionUpdate) -> models.Permission | None:
    obj = get_permission(db, permission_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_permission(db: Session, permission_id: int) -> bool:
    obj = get_permission(db, permission_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# ---------- users ----------

def list_users(db: Session, q: str | None = None) -> list[models.User]:
    from sqlalchemy.orm import joinedload
    query = db.query(models.User).options(joinedload(models.User.role))
    query = _search_filter(query, models.User, q, ["username"])
    return query.all()


def create_user(db: Session, data: schemas.UserCreate) -> models.User:
    obj = models.User(
        username=data.username.strip(),
        password=_hash_password(data.password),
        name=data.name,
        employee_no=data.employee_no,
        status=data.status,
        role_id=data.role_id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_user(db: Session, user_id: int) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()


def update_user(db: Session, user_id: int, data: schemas.UserUpdate) -> models.User | None:
    obj = get_user(db, user_id)
    if not obj:
        return None
    update_data = data.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = _hash_password(update_data.pop("password"))
    for key, value in update_data.items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_user(db: Session, user_id: int) -> bool:
    obj = get_user(db, user_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def authenticate_user(db: Session, username: str, password: str) -> models.User | None:
    user = db.query(models.User).filter(models.User.username == username.strip()).first()
    if not user:
        return None
    if user.status != "活跃":
        return None
    if user.password != _hash_password(password):
        return None
    return user


# ---------- tasks ----------

def list_tasks(
    db: Session,
    user_id: int | None = None,
    task_date: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    product_id: int | None = None,
) -> list[models.Task]:
    query = db.query(models.Task)
    if user_id is not None:
        query = query.filter(models.Task.user_id == user_id)
    if product_id is not None:
        query = query.filter(models.Task.product_id == product_id)
    if task_date:
        query = query.filter(models.Task.task_date == task_date)
    if start_date:
        query = query.filter(models.Task.task_date >= start_date)
    if end_date:
        query = query.filter(models.Task.task_date <= end_date)
    return query.order_by(models.Task.task_date, models.Task.id).all()


def get_task(db: Session, task_id: int) -> models.Task | None:
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def create_task(db: Session, data: schemas.TaskCreate) -> models.Task:
    obj = models.Task(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_task(db: Session, task_id: int, data: schemas.TaskUpdate) -> models.Task | None:
    obj = get_task(db, task_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_task(db: Session, task_id: int) -> bool:
    obj = get_task(db, task_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def ensure_default_admin(db: Session):
    admin_role = db.query(models.Role).filter(models.Role.name == "超级管理员").first()
    admin = db.query(models.User).filter(models.User.username == "zhouyong").first()
    if not admin:
        from datetime import datetime, timezone
        admin = models.User(
            username="zhouyong",
            password=_hash_password("zy6951230"),
            name="周勇",
            employee_no="A001",
            status="活跃",
            role_id=admin_role.id if admin_role else None,
            created_at=datetime.now(timezone.utc),
        )
        db.add(admin)
        db.commit()
        logger.info("已创建默认管理员账号 zhouyong")
    elif admin_role and admin.role_id != admin_role.id:
        admin.role_id = admin_role.id
        db.commit()
        logger.info("已将管理员账号 zhouyong 关联到超级管理员角色")


ROLE_PRESETS: list[dict] = [
    {
        "name": "超级管理员",
        "codes": None,
    },
    {
        "name": "项目经理",
        "codes": [
            "project:menu", "product:menu", "craft:menu", "process:menu", "task:menu", "task_stats:menu", "role:menu", "permission:menu", "user:menu",
            "project:create", "project:edit", "project:delete", "project:export", "project:audit", "project:reject", "project:print",
            "product:create", "product:edit",
            "craft:create", "craft:edit", "craft:delete", "craft:export",
            "process:create", "process:edit", "process:delete", "process:export",
            "task:create", "task:edit", "task:delete", "task:export",
            "task_stats:export",
            "project:api", "product:api", "craft:api", "process:api", "task:api", "task_stats:api", "role:api", "permission:api", "user:api",
        ],
    },
    {
        "name": "产品经理",
        "codes": [
            "product:menu", "project:menu", "craft:menu", "process:menu", "task:menu", "task_stats:menu",
            "product:create", "product:edit", "product:delete", "product:export", "product:print",
            "craft:create", "craft:edit", "craft:export",
            "process:create", "process:edit", "process:export",
            "task:create", "task:edit", "task:export",
            "task_stats:export",
            "project:api", "product:api", "craft:api", "process:api", "task:api", "task_stats:api",
        ],
    },
    {
        "name": "普通用户",
        "codes": [
            "project:menu", "product:menu", "craft:menu", "process:menu", "task:menu", "task_stats:menu",
            "craft:create", "craft:edit",
            "process:create", "process:edit",
            "task:create", "task:edit", "task:delete", "task:export",
            "task_stats:export",
            "project:api", "product:api", "craft:api", "process:api", "task:api", "task_stats:api",
        ],
    },
]


def ensure_default_permissions(db: Session):
    created = 0
    for item in schemas.PERMISSION_DEFS:
        existing = db.query(models.Permission).filter(models.Permission.code == item["code"]).first()
        if not existing:
            db.add(models.Permission(**item))
            created += 1
    if created:
        db.commit()
        logger.info("已写入 %d 条预定义权限", created)


def ensure_default_roles(db: Session):
    all_permissions = db.query(models.Permission).all()
    all_codes = {p.code for p in all_permissions}
    perm_map = {p.code: p for p in all_permissions}

    for preset in ROLE_PRESETS:
        role = db.query(models.Role).filter(models.Role.name == preset["name"]).first()
        if not role:
            role = models.Role(name=preset["name"])
            db.add(role)
            db.flush()

        if preset["codes"] is None:
            wanted_codes = list(all_codes)
        else:
            wanted_codes = [c for c in preset["codes"] if c in all_codes]

        existing_codes = {p.code for p in role.permissions}
        codes_to_add = set(wanted_codes) - existing_codes
        codes_to_remove = existing_codes - set(wanted_codes)

        if codes_to_add:
            for code in codes_to_add:
                role.permissions.append(perm_map[code])
        if codes_to_remove:
            role.permissions = [p for p in role.permissions if p.code not in codes_to_remove]

    db.commit()
    logger.info("已初始化 %d 个预设角色（超级管理员、项目经理、产品经理、普通用户）", len(ROLE_PRESETS))


# ---------- crafts ----------

def list_crafts(
    db: Session,
    q: str | None = None,
    project_id: int | None = None,
    product_id: int | None = None,
) -> list[models.Craft]:
    query = db.query(models.Craft)
    if project_id is not None:
        query = query.filter(models.Craft.project_id == project_id)
    if product_id is not None:
        query = query.filter(models.Craft.product_id == product_id)
    query = _search_filter(query, models.Craft, q, ["craft_code", "craft_name", "description", "status"])
    return query.all()


def create_craft(db: Session, data: schemas.CraftCreate) -> models.Craft:
    obj = models.Craft(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_craft(db: Session, craft_id: int) -> models.Craft | None:
    return db.query(models.Craft).filter(models.Craft.id == craft_id).first()


def update_craft(db: Session, craft_id: int, data: schemas.CraftUpdate) -> models.Craft | None:
    obj = get_craft(db, craft_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_craft(db: Session, craft_id: int) -> bool:
    obj = get_craft(db, craft_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# ---------- processes ----------

def list_processes(
    db: Session,
    craft_id: int | None = None,
    q: str | None = None,
) -> list[models.Process]:
    query = db.query(models.Process)
    if craft_id is not None:
        query = query.filter(models.Process.craft_id == craft_id)
    query = _search_filter(query, models.Process, q, ["process_code", "process_name", "equipment", "description", "status"])
    return query.order_by(models.Process.sort_order, models.Process.id).all()


def create_process(db: Session, data: schemas.ProcessCreate) -> models.Process:
    obj = models.Process(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_process(db: Session, process_id: int) -> models.Process | None:
    return db.query(models.Process).filter(models.Process.id == process_id).first()


def update_process(db: Session, process_id: int, data: schemas.ProcessUpdate) -> models.Process | None:
    obj = get_process(db, process_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_process(db: Session, process_id: int) -> bool:
    obj = get_process(db, process_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# ---------- operation logs ----------

def list_operation_logs(
    db: Session,
    module: str | None = None,
    action: str | None = None,
    project_id: int | None = None,
    product_id: int | None = None,
    craft_id: int | None = None,
    process_id: int | None = None,
    operator: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    q: str | None = None,
    limit: int = 200,
) -> list[models.OperationLog]:
    query = db.query(models.OperationLog)
    if module:
        query = query.filter(models.OperationLog.module == module)
    if action:
        query = query.filter(models.OperationLog.action == action)
    if project_id is not None:
        query = query.filter(models.OperationLog.project_id == project_id)
    if product_id is not None:
        query = query.filter(models.OperationLog.product_id == product_id)
    if craft_id is not None:
        query = query.filter(models.OperationLog.craft_id == craft_id)
    if process_id is not None:
        query = query.filter(models.OperationLog.process_id == process_id)
    if operator:
        query = query.filter(models.OperationLog.operator.ilike(f"%{operator}%"))
    if start_date:
        query = query.filter(models.OperationLog.created_at >= start_date)
    if end_date:
        query = query.filter(models.OperationLog.created_at <= end_date + " 23:59:59")
    if q:
        from sqlalchemy import or_
        query = query.filter(or_(
            models.OperationLog.target_name.ilike(f"%{q}%"),
            models.OperationLog.remark.ilike(f"%{q}%"),
        ))
    return query.order_by(models.OperationLog.created_at.desc()).limit(limit).all()


def create_operation_log(db: Session, data: schemas.OperationLogCreate) -> models.OperationLog:
    obj = models.OperationLog(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_operation_log(db: Session, log_id: int) -> models.OperationLog | None:
    return db.query(models.OperationLog).filter(models.OperationLog.id == log_id).first()


def delete_operation_log(db: Session, log_id: int) -> bool:
    obj = get_operation_log(db, log_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def clear_operation_logs(db: Session, before_date: str | None = None) -> int:
    query = db.query(models.OperationLog)
    if before_date:
        query = query.filter(models.OperationLog.created_at < before_date)
    count = query.delete()
    db.commit()
    return count


def get_task_stats(
    db: Session,
    start_date: str | None = None,
    end_date: str | None = None,
    group_by: str = "user",
) -> list[dict]:
    from sqlalchemy import func

    query = db.query(models.Task)
    if start_date:
        query = query.filter(models.Task.task_date >= start_date)
    if end_date:
        query = query.filter(models.Task.task_date <= end_date)

    tasks: list[models.Task] = query.all()
    users: list[models.User] = db.query(models.User).all()
    products: list[models.Product] = db.query(models.Product).all()
    user_map = {u.id: u for u in users}
    product_map = {p.id: p for p in products}

    statuses = ["待办", "进行中", "已完成", "已搁置"]

    def _aggregate(items: list[models.Task], nested_key: str) -> dict:
        total = len(items)
        counts = {s: 0 for s in statuses}
        plan_minutes = 0
        actual_minutes = 0
        weighted_progress = 0.0
        nested_counts: dict[str, int] = {}
        nested_done: dict[str, int] = {}
        for t in items:
            st = t.status or "待办"
            if st in counts:
                counts[st] += 1
            if nested_key == "user":
                nid = t.user_id
                nmap = user_map
            else:
                nid = t.product_id
                nmap = product_map
            if nid is not None:
                nobj = nmap.get(nid)
                if nested_key == "user":
                    nlabel = (nobj.name or nobj.username) if nobj else f"#{nid}"
                else:
                    nlabel = (nobj.product_name or nobj.product_code) if nobj else f"#{nid}"
                nested_counts[nlabel] = nested_counts.get(nlabel, 0) + 1
                if st == "已完成":
                    nested_done[nlabel] = nested_done.get(nlabel, 0) + 1
            plan_minutes += _time_range_minutes(t.plan_start_time, t.plan_end_time)
            actual_minutes += _time_range_minutes(t.actual_start_time, t.actual_end_time)
            weighted_progress += (t.progress or 0)
        avg_progress = round(weighted_progress / total, 1) if total else 0
        completion_rate = round(counts["已完成"] * 100.0 / total, 1) if total else 0

        nested_info = []
        for nlabel, ncnt in sorted(nested_counts.items(), key=lambda x: -x[1]):
            ndone = nested_done.get(nlabel, 0)
            nrate = round(ndone * 100.0 / ncnt, 1) if ncnt else 0
            nested_info.append({
                "name": nlabel,
                "total": ncnt,
                "done": ndone,
                "rate": nrate,
            })

        entry = {
            "total": total,
            **{f"count_{s}": counts[s] for s in statuses},
            "completion_rate": completion_rate,
            "avg_progress": avg_progress,
            "plan_minutes": plan_minutes,
            "actual_minutes": actual_minutes,
        }
        if nested_key == "user":
            entry["users"] = nested_info
        else:
            entry["products"] = nested_info
        return entry

    result: list[dict] = []

    if group_by == "product":
        grouped: dict[int | None, list[models.Task]] = {}
        for t in tasks:
            grouped.setdefault(t.product_id, []).append(t)

        for pid, items in grouped.items():
            product = product_map.get(pid) if pid is not None else None
            base = _aggregate(items, nested_key="user")
            users_info = base.pop("users", [])
            result.append({
                "product_id": pid,
                "product_name": product.product_name if product else "",
                "product_code": product.product_code if product else "",
                "name": product.product_name if product else (f"产品#{pid}" if pid else "未关联产品"),
                **base,
                "users": users_info,
            })
    else:
        grouped = {}
        for t in tasks:
            grouped.setdefault(t.user_id, []).append(t)

        for uid, items in grouped.items():
            user = user_map.get(uid)
            base = _aggregate(items, nested_key="product")
            result.append({
                "user_id": uid,
                "username": user.username if user else "",
                "name": user.name if user else "",
                "employee_no": user.employee_no if user else "",
                **base,
            })

    result.sort(key=lambda x: x["completion_rate"], reverse=True)
    return result


def _time_range_minutes(start: str, end: str) -> int:
    if not start or not end:
        return 0
    try:
        from datetime import datetime
        fmt = "%H:%M"
        s = datetime.strptime(start, fmt)
        e = datetime.strptime(end, fmt)
        delta = (e - s).total_seconds() / 60
        if delta > 0:
            return int(delta)
    except Exception:
        pass
    return 0


try:
    from app.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)