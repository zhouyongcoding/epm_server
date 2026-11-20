import traceback
import os

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query, Request, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import engine, get_db, Base
from app import crud
from app import schemas
from app import models
from app.discovery import DiscoveryResponder
from app.logger import logger

_discovery: DiscoveryResponder | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _discovery
    logger.info("服务端启动中...")
    _auto_migrate()
    Base.metadata.create_all(bind=engine)
    db_session = next(get_db())
    try:
        crud.ensure_default_permissions(db_session)
        crud.ensure_default_roles(db_session)
        crud.ensure_default_admin(db_session)
    finally:
        db_session.close()
    _discovery = DiscoveryResponder()
    _discovery.start()
    logger.info("服务端已启动，监听 http://0.0.0.0:8001")
    yield
    if _discovery:
        _discovery.stop()
    logger.info("服务端已关闭")


def _auto_migrate():
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    try:
        tables = inspector.get_table_names()
    except Exception:
        return

    with engine.connect() as conn:
        # --- 旧版表结构重建（破坏性） ---
        _drop_tables = [
            ("permissions", "perm_type", "permissions + role_permissions",
             ["role_permissions"]),
            ("processes", "craft_id", "processes + process_steps",
             ["process_steps"]),
        ]
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table_name, required_col, drop_label, extra_tables in _drop_tables:
            if table_name in tables:
                cols = {c["name"] for c in inspector.get_columns(table_name)}
                if required_col not in cols:
                    logger.warning("检测到旧版 %s 表结构，正在重建...", drop_label)
                    for t in extra_tables:
                        conn.execute(text(f"DROP TABLE IF EXISTS {t}"))
                    conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

        # --- 新列增量添加（保留数据） ---
        if "products" in tables:
            product_cols = {c["name"] for c in inspector.get_columns("products")}
            for col_name, col_def in [
                ("created_by", "VARCHAR(60) DEFAULT ''"),
                ("updated_by", "VARCHAR(60) DEFAULT ''"),
                ("created_at", "DATETIME"),
                ("updated_at", "DATETIME"),
            ]:
                if col_name not in product_cols:
                    conn.execute(text(f"ALTER TABLE products ADD COLUMN {col_name} {col_def}"))
                    logger.info("products 表新增列: %s", col_name)

        if "tasks" in tables:
            task_cols = {c["name"] for c in inspector.get_columns("tasks")}
            for col_name, col_def in [
                ("product_id", "INTEGER"),
                ("plan_start_time", "VARCHAR(10) DEFAULT ''"),
                ("plan_end_time", "VARCHAR(10) DEFAULT ''"),
                ("actual_start_time", "VARCHAR(10) DEFAULT ''"),
                ("actual_end_time", "VARCHAR(10) DEFAULT ''"),
                ("created_at", "DATETIME"),
                ("updated_at", "DATETIME"),
            ]:
                if col_name not in task_cols:
                    conn.execute(text(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_def}"))
                    logger.info("tasks 表新增列: %s", col_name)

        conn.commit()


app = FastAPI(
    title="工程项目管理系统",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        response = await call_next(request)
        if response.status_code >= 400:
            logger.error(
                "请求失败 %s %s - status=%d",
                request.method,
                request.url.path,
                response.status_code,
            )
        return response
    except Exception:
        logger.exception("未捕获异常 %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误"},
        )


IMAGES_DIR = r"E:\images"
os.makedirs(IMAGES_DIR, exist_ok=True)
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "全局异常 %s %s: %s\n%s",
        request.method,
        request.url.path,
        exc,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"},
    )


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


# ---------- projects ----------

@app.get("/api/projects", response_model=list[schemas.ProjectOut])
def list_projects(q: str | None = Query(None), db: Session = Depends(get_db)):
    return crud.list_projects(db, q)


@app.post("/api/projects", response_model=schemas.ProjectOut, status_code=201)
def create_project(data: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.create_project(db, data)


@app.get("/api/projects/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    obj = crud.get_project(db, project_id)
    if not obj:
        raise HTTPException(status_code=404, detail="项目不存在")
    return obj


@app.put("/api/projects/{project_id}", response_model=schemas.ProjectOut)
def update_project(project_id: int, data: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    obj = crud.update_project(db, project_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="项目不存在")
    return obj


@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    if not crud.delete_project(db, project_id):
        raise HTTPException(status_code=404, detail="项目不存在")


# ---------- products ----------

def _product_dict(u: models.Product, request: Request | None = None) -> dict:
    d = schemas.ProductOut.model_validate(u).model_dump()
    base = ""
    if request is not None:
        base = str(request.base_url).rstrip("/")
    for img in d.get("images", []):
        path = img.get("image_path", "")
        if base and path:
            img["full_url"] = f"{base}/{path}"
        else:
            img["full_url"] = f"/{path}" if path else None
    return d


@app.get("/api/products", response_model=list[schemas.ProductOut])
def list_products(q: str | None = Query(None), db: Session = Depends(get_db), request: Request = ...):
    from sqlalchemy.orm import joinedload
    query = db.query(models.Product).options(joinedload(models.Product.images))
    if q:
        from sqlalchemy import or_
        query = query.filter(or_(
            models.Product.product_code.ilike(f"%{q}%"),
            models.Product.product_name.ilike(f"%{q}%"),
        ))
    return [_product_dict(p, request) for p in query.all()]


@app.post("/api/products", response_model=schemas.ProductOut, status_code=201)
def create_product(data: schemas.ProductCreate, db: Session = Depends(get_db), request: Request = ...):
    from sqlalchemy.orm import joinedload
    obj = crud.create_product(db, data)
    fresh = db.query(models.Product).options(joinedload(models.Product.images)).filter(models.Product.id == obj.id).first()
    return _product_dict(fresh, request)


@app.get("/api/products/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db), request: Request = ...):
    from sqlalchemy.orm import joinedload
    obj = db.query(models.Product).options(joinedload(models.Product.images)).filter(models.Product.id == product_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="产品不存在")
    return _product_dict(obj, request)


@app.put("/api/products/{product_id}", response_model=schemas.ProductOut)
def update_product(product_id: int, data: schemas.ProductUpdate, db: Session = Depends(get_db), request: Request = ...):
    from sqlalchemy.orm import joinedload
    obj = db.query(models.Product).options(joinedload(models.Product.images)).filter(models.Product.id == product_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="产品不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return _product_dict(obj, request)


@app.delete("/api/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    if not crud.delete_product(db, product_id):
        raise HTTPException(status_code=404, detail="产品不存在")


# ---------- product images ----------

def _product_image_dict(img: models.ProductImage, request: Request | None = None) -> dict:
    d = schemas.ProductImageOut.model_validate(img).model_dump()
    base = ""
    if request is not None:
        base = str(request.base_url).rstrip("/")
    path = d.get("image_path", "")
    if base and path:
        d["full_url"] = f"{base}/{path}"
    else:
        d["full_url"] = f"/{path}" if path else None
    return d


@app.get("/api/products/{product_id}/images", response_model=list[schemas.ProductImageOut])
def list_product_images(product_id: int, db: Session = Depends(get_db), request: Request = ...):
    if not crud.get_product(db, product_id):
        raise HTTPException(status_code=404, detail="产品不存在")
    imgs = crud.list_product_images(db, product_id)
    return [_product_image_dict(i, request) for i in imgs]


@app.post("/api/products/{product_id}/images", response_model=schemas.ProductImageOut, status_code=201)
def create_product_image(
    product_id: int,
    file: UploadFile = File(...),
    sort_order: int = 0,
    db: Session = Depends(get_db),
    request: Request = ...,
):
    if not crud.get_product(db, product_id):
        raise HTTPException(status_code=404, detail="产品不存在")
    obj = crud.create_product_image(db, product_id, file, sort_order)
    return _product_image_dict(obj, request)


@app.delete("/api/products/{product_id}/images/{image_id}", status_code=204)
def delete_product_image(product_id: int, image_id: int, db: Session = Depends(get_db)):
    if not crud.delete_product_image(db, image_id):
        raise HTTPException(status_code=404, detail="图片不存在")


# ---------- roles ----------

@app.get("/api/roles", response_model=list[schemas.RoleOut])
def list_roles(q: str | None = Query(None), db: Session = Depends(get_db)):
    return crud.list_roles(db, q)


@app.post("/api/roles", response_model=schemas.RoleOut, status_code=201)
def create_role(data: schemas.RoleCreate, db: Session = Depends(get_db)):
    return crud.create_role(db, data)


@app.get("/api/roles/{role_id}", response_model=schemas.RoleOutWithPerms)
def get_role(role_id: int, db: Session = Depends(get_db)):
    obj = crud.get_role(db, role_id)
    if not obj:
        raise HTTPException(status_code=404, detail="角色不存在")
    return obj


@app.put("/api/roles/{role_id}", response_model=schemas.RoleOut)
def update_role(role_id: int, data: schemas.RoleUpdate, db: Session = Depends(get_db)):
    obj = crud.update_role(db, role_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="角色不存在")
    return obj


@app.put("/api/roles/{role_id}/permissions", response_model=schemas.RoleOutWithPerms)
def set_role_permissions(role_id: int, data: schemas.RoleUpdatePermissions, db: Session = Depends(get_db)):
    obj = crud.set_role_permissions(db, role_id, data.permission_ids)
    if not obj:
        raise HTTPException(status_code=404, detail="角色不存在")
    return obj


@app.delete("/api/roles/{role_id}", status_code=204)
def delete_role(role_id: int, db: Session = Depends(get_db)):
    if not crud.delete_role(db, role_id):
        raise HTTPException(status_code=404, detail="角色不存在")


# ---------- permissions ----------

@app.get("/api/permissions", response_model=list[schemas.PermissionOut])
def list_permissions(q: str | None = Query(None), db: Session = Depends(get_db)):
    return crud.list_permissions(db, q)


@app.post("/api/permissions", response_model=schemas.PermissionOut, status_code=201)
def create_permission(data: schemas.PermissionCreate, db: Session = Depends(get_db)):
    return crud.create_permission(db, data)


@app.get("/api/permissions/{permission_id}", response_model=schemas.PermissionOut)
def get_permission(permission_id: int, db: Session = Depends(get_db)):
    obj = crud.get_permission(db, permission_id)
    if not obj:
        raise HTTPException(status_code=404, detail="权限不存在")
    return obj


@app.put("/api/permissions/{permission_id}", response_model=schemas.PermissionOut)
def update_permission(permission_id: int, data: schemas.PermissionUpdate, db: Session = Depends(get_db)):
    obj = crud.update_permission(db, permission_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="权限不存在")
    return obj


@app.delete("/api/permissions/{permission_id}", status_code=204)
def delete_permission(permission_id: int, db: Session = Depends(get_db)):
    if not crud.delete_permission(db, permission_id):
        raise HTTPException(status_code=404, detail="权限不存在")


@app.get("/api/permission-defs")
def get_permission_defs():
    return {
        "modules": schemas.SYSTEM_MODULES,
        "perm_types": schemas.PERMISSION_TYPES,
        "button_actions": schemas.BUTTON_ACTIONS,
        "defs": schemas.PERMISSION_DEFS,
    }


@app.post("/api/permissions/init-defaults", status_code=201)
def init_default_permissions(db: Session = Depends(get_db)):
    created = []
    for item in schemas.PERMISSION_DEFS:
        existing = db.query(models.Permission).filter(models.Permission.code == item["code"]).first()
        if not existing:
            obj = models.Permission(**item)
            db.add(obj)
            created.append(item["code"])
    db.commit()
    return {"created": len(created), "codes": created}


# ---------- auth ----------

class _LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
def login(body: _LoginRequest, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "employee_no": user.employee_no,
        "status": user.status,
        "role_id": user.role_id,
    }


# ---------- users ----------

def _user_dict(u: models.User) -> dict:
    d = schemas.UserOut.model_validate(u).model_dump()
    d["role_name"] = u.role.name if u.role else None
    return d


@app.get("/api/users", response_model=list[schemas.UserOut])
def list_users(q: str | None = Query(None), db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    query = db.query(models.User).options(joinedload(models.User.role))
    if q:
        from sqlalchemy import or_
        query = query.filter(or_(models.User.username.ilike(f"%{q}%")))
    return [_user_dict(u) for u in query.all()]


@app.post("/api/users", response_model=schemas.UserOut, status_code=201)
def create_user(data: schemas.UserCreate, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    obj = crud.create_user(db, data)
    fresh = db.query(models.User).options(joinedload(models.User.role)).filter(models.User.id == obj.id).first()
    return _user_dict(fresh)


@app.get("/api/users/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    obj = db.query(models.User).options(joinedload(models.User.role)).filter(models.User.id == user_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="用户不存在")
    return _user_dict(obj)


@app.put("/api/users/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, data: schemas.UserUpdate, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    obj = db.query(models.User).options(joinedload(models.User.role)).filter(models.User.id == user_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="用户不存在")
    update_data = data.model_dump(exclude_unset=True)
    if "password" in update_data:
        from app.crud import _hash_password
        update_data["password"] = _hash_password(update_data.pop("password"))
    for key, value in update_data.items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return _user_dict(obj)


@app.delete("/api/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    if not crud.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="用户不存在")


# ---------- tasks ----------

@app.get("/api/tasks", response_model=list[schemas.TaskOut])
def list_tasks(
    user_id: int | None = Query(None),
    task_date: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    product_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    return crud.list_tasks(db, user_id=user_id, task_date=task_date,
                            start_date=start_date, end_date=end_date,
                            product_id=product_id)


@app.post("/api/tasks", response_model=schemas.TaskOut, status_code=201)
def create_task(data: schemas.TaskCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="用户不存在")
    return crud.create_task(db, data)


@app.get("/api/tasks/{task_id}", response_model=schemas.TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    obj = crud.get_task(db, task_id)
    if not obj:
        raise HTTPException(status_code=404, detail="任务不存在")
    return obj


@app.put("/api/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, data: schemas.TaskUpdate, db: Session = Depends(get_db)):
    obj = crud.update_task(db, task_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="任务不存在")
    return obj


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    if not crud.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="任务不存在")


# ---------- crafts ----------

@app.get("/api/crafts", response_model=list[schemas.CraftOut])
def list_crafts(
    q: str | None = Query(None),
    project_id: int | None = Query(None),
    product_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    from sqlalchemy.orm import joinedload
    query = db.query(models.Craft).options(joinedload(models.Craft.processes))
    if project_id is not None:
        query = query.filter(models.Craft.project_id == project_id)
    if product_id is not None:
        query = query.filter(models.Craft.product_id == product_id)
    if q:
        from sqlalchemy import or_
        query = query.filter(or_(
            models.Craft.craft_code.ilike(f"%{q}%"),
            models.Craft.craft_name.ilike(f"%{q}%"),
        ))
    return query.all()


@app.post("/api/crafts", response_model=schemas.CraftOut, status_code=201)
def create_craft(data: schemas.CraftCreate, db: Session = Depends(get_db)):
    return crud.create_craft(db, data)


@app.get("/api/crafts/{craft_id}", response_model=schemas.CraftOut)
def get_craft(craft_id: int, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    obj = db.query(models.Craft).options(joinedload(models.Craft.processes)).filter(models.Craft.id == craft_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="工艺不存在")
    return obj


@app.put("/api/crafts/{craft_id}", response_model=schemas.CraftOut)
def update_craft(craft_id: int, data: schemas.CraftUpdate, db: Session = Depends(get_db)):
    obj = crud.update_craft(db, craft_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="工艺不存在")
    return obj


@app.delete("/api/crafts/{craft_id}", status_code=204)
def delete_craft(craft_id: int, db: Session = Depends(get_db)):
    if not crud.delete_craft(db, craft_id):
        raise HTTPException(status_code=404, detail="工艺不存在")


# ---------- processes ----------

@app.get("/api/processes", response_model=list[schemas.ProcessOut])
def list_processes(
    craft_id: int | None = Query(None),
    q: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return crud.list_processes(db, craft_id=craft_id, q=q)


@app.post("/api/processes", response_model=schemas.ProcessOut, status_code=201)
def create_process(data: schemas.ProcessCreate, db: Session = Depends(get_db)):
    craft = crud.get_craft(db, data.craft_id)
    if not craft:
        raise HTTPException(status_code=400, detail="工艺不存在")
    return crud.create_process(db, data)


@app.get("/api/processes/{process_id}", response_model=schemas.ProcessOut)
def get_process(process_id: int, db: Session = Depends(get_db)):
    obj = crud.get_process(db, process_id)
    if not obj:
        raise HTTPException(status_code=404, detail="工序不存在")
    return obj


@app.put("/api/processes/{process_id}", response_model=schemas.ProcessOut)
def update_process(process_id: int, data: schemas.ProcessUpdate, db: Session = Depends(get_db)):
    obj = crud.update_process(db, process_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="工序不存在")
    return obj


@app.delete("/api/processes/{process_id}", status_code=204)
def delete_process(process_id: int, db: Session = Depends(get_db)):
    if not crud.delete_process(db, process_id):
        raise HTTPException(status_code=404, detail="工序不存在")


# ---------- operation logs ----------

@app.get("/api/operation-logs", response_model=list[schemas.OperationLogOut])
def list_operation_logs(
    module: str | None = Query(None),
    action: str | None = Query(None),
    project_id: int | None = Query(None),
    product_id: int | None = Query(None),
    craft_id: int | None = Query(None),
    process_id: int | None = Query(None),
    operator: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(200, le=1000),
    db: Session = Depends(get_db),
):
    return crud.list_operation_logs(
        db,
        module=module,
        action=action,
        project_id=project_id,
        product_id=product_id,
        craft_id=craft_id,
        process_id=process_id,
        operator=operator,
        start_date=start_date,
        end_date=end_date,
        q=q,
        limit=limit,
    )


@app.post("/api/operation-logs", response_model=schemas.OperationLogOut, status_code=201)
def create_operation_log(data: schemas.OperationLogCreate, db: Session = Depends(get_db)):
    return crud.create_operation_log(db, data)


@app.get("/api/operation-logs/{log_id}", response_model=schemas.OperationLogOut)
def get_operation_log(log_id: int, db: Session = Depends(get_db)):
    obj = crud.get_operation_log(db, log_id)
    if not obj:
        raise HTTPException(status_code=404, detail="日志不存在")
    return obj


@app.delete("/api/operation-logs/{log_id}", status_code=204)
def delete_operation_log(log_id: int, db: Session = Depends(get_db)):
    if not crud.delete_operation_log(db, log_id):
        raise HTTPException(status_code=404, detail="日志不存在")


@app.delete("/api/operation-logs", response_model=dict)
def clear_operation_logs(
    before_date: str | None = Query(None),
    db: Session = Depends(get_db),
):
    count = crud.clear_operation_logs(db, before_date=before_date)
    return {"deleted": count}


# ---------- task stats ----------

@app.get("/api/task-stats", response_model=list[dict])
def get_task_stats(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    group_by: str = Query("user"),
    db: Session = Depends(get_db),
):
    return crud.get_task_stats(db, start_date=start_date, end_date=end_date, group_by=group_by)