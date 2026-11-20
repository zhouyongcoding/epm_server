from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.database import Base


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    customer = Column(String(120), default="")
    location = Column(String(200), default="")
    start_date = Column(String(10), default="")
    end_date = Column(String(10), default="")
    status = Column(String(20), default="未开始")
    description = Column(Text, default="")
    created_by = Column(String(60), default="")
    updated_by = Column(String(60), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(100), nullable=False)
    product_name = Column(String(120), nullable=False)
    product_image = Column(Text, default="")
    status = Column(String(10), default="启用")
    notes = Column(Text, default="")
    created_by = Column(String(60), default="")
    updated_by = Column(String(60), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    image_path = Column(String(500), nullable=False)
    sort_order = Column(Integer, default=0)

    product = relationship("Product", back_populates="images")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60), nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", back_populates="role")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    module = Column(String(100), nullable=False, default="")
    perm_type = Column(String(20), nullable=False, default="menu")
    action = Column(String(100), nullable=False, default="")
    code = Column(String(200), nullable=False, unique=True, default="")
    description = Column(String(200), default="")

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(60), nullable=False, unique=True)
    password = Column(String(256), nullable=False)
    name = Column(String(60), default="")
    employee_no = Column(String(60), default="")
    status = Column(String(20), default="活跃")
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    role = relationship("Role", back_populates="users")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    task_date = Column(String(10), nullable=False, index=True)
    content = Column(String(500), nullable=False, default="")
    plan_start_time = Column(String(10), default="")
    plan_end_time = Column(String(10), default="")
    actual_start_time = Column(String(10), default="")
    actual_end_time = Column(String(10), default="")
    status = Column(String(20), default="待办")
    progress = Column(Integer, default=0)
    note = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))


class Craft(Base):
    __tablename__ = "crafts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)
    craft_code = Column(String(100), default="")
    craft_name = Column(String(150), nullable=False)
    description = Column(Text, default="")
    status = Column(String(20), default="启用")
    created_by = Column(String(60), default="")
    updated_by = Column(String(60), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    processes = relationship("Process", back_populates="craft", cascade="all, delete-orphan")


class Process(Base):
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True, index=True)
    craft_id = Column(Integer, ForeignKey("crafts.id", ondelete="CASCADE"), nullable=False, index=True)
    process_code = Column(String(100), default="")
    process_name = Column(String(150), nullable=False)
    sort_order = Column(Integer, default=0)
    duration = Column(String(30), default="")
    equipment = Column(String(150), default="")
    description = Column(Text, default="")
    status = Column(String(20), default="启用")
    created_by = Column(String(60), default="")
    updated_by = Column(String(60), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    craft = relationship("Craft", back_populates="processes")


class ProjectProgress(Base):
    __tablename__ = "project_progresses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    plan_start_date = Column(String(10), default="")
    plan_end_date = Column(String(10), default="")
    actual_start_date = Column(String(10), default="")
    actual_end_date = Column(String(10), default="")
    progress = Column(Integer, default=0)
    status = Column(String(20), default="未开始")
    note = Column(Text, default="")
    created_by = Column(String(60), default="")
    updated_by = Column(String(60), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))


class ProductProgress(Base):
    __tablename__ = "product_progresses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)
    plan_start_date = Column(String(10), default="")
    plan_end_date = Column(String(10), default="")
    actual_start_date = Column(String(10), default="")
    actual_end_date = Column(String(10), default="")
    progress = Column(Integer, default=0)
    status = Column(String(20), default="未开始")
    note = Column(Text, default="")
    created_by = Column(String(60), default="")
    updated_by = Column(String(60), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))


class ProcessProgress(Base):
    __tablename__ = "process_progresses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)
    craft_id = Column(Integer, ForeignKey("crafts.id", ondelete="CASCADE"), nullable=True, index=True)
    process_id = Column(Integer, ForeignKey("processes.id", ondelete="CASCADE"), nullable=True, index=True)
    assigned_to = Column(String(60), default="")
    plan_start_date = Column(String(10), default="")
    plan_end_date = Column(String(10), default="")
    actual_start_date = Column(String(10), default="")
    actual_end_date = Column(String(10), default="")
    progress = Column(Integer, default=0)
    status = Column(String(20), default="未开始")
    note = Column(Text, default="")
    created_by = Column(String(60), default="")
    updated_by = Column(String(60), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    action = Column(String(30), nullable=False, default="")
    module = Column(String(50), nullable=False, default="")
    target_id = Column(Integer, nullable=True)
    target_name = Column(String(200), default="")
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    craft_id = Column(Integer, ForeignKey("crafts.id", ondelete="SET NULL"), nullable=True)
    process_id = Column(Integer, ForeignKey("processes.id", ondelete="SET NULL"), nullable=True)
    old_value = Column(Text, default="")
    new_value = Column(Text, default="")
    operator = Column(String(60), default="")
    operator_id = Column(Integer, nullable=True)
    ip_address = Column(String(64), default="")
    remark = Column(String(500), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))