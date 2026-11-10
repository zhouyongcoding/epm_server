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
) -> list[models.Task]:
    query = db.query(models.Task)
    if user_id is not None:
        query = query.filter(models.Task.user_id == user_id)
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
            "project:menu", "product:menu", "task:menu", "role:menu", "permission:menu", "user:menu",
            "project:create", "project:edit", "project:delete", "project:export", "project:audit", "project:reject", "project:print",
            "product:create", "product:edit",
            "task:create", "task:edit", "task:delete", "task:export",
            "project:api", "product:api", "task:api", "role:api", "permission:api", "user:api",
        ],
    },
    {
        "name": "产品经理",
        "codes": [
            "product:menu", "project:menu", "task:menu",
            "product:create", "product:edit", "product:delete", "product:export", "product:print",
            "task:create", "task:edit", "task:export",
            "project:api", "product:api", "task:api",
        ],
    },
    {
        "name": "普通用户",
        "codes": [
            "project:menu", "product:menu", "task:menu",
            "task:create", "task:edit", "task:delete", "task:export",
            "project:api", "product:api", "task:api",
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


try:
    from app.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)