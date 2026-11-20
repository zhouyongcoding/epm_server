"""清空 tasks 表并重新生成测试数据（按产品关联）"""
import sys
import os
import random
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal
from app import models

STATUSES = ["待办", "进行中", "已完成", "已搁置"]
TASK_TEMPLATES = [
    ("产品外观检查与尺寸测量", "使用游标卡尺、千分尺对关键尺寸进行抽检，记录偏差值"),
    ("产品功能测试", "通电测试基本功能，记录各项参数是否在规格范围内"),
    ("产品装配与调试", "按工艺文件完成产品装配，调试至最佳状态"),
    ("首件试生产", "按照工艺要求完成首件生产，填写首件检验报告"),
    ("批量生产跟踪", "跟踪批量生产过程，记录异常情况并及时反馈"),
    ("产品包装与出货", "按客户要求完成包装，贴标签，准备出货"),
    ("工艺文件修订", "根据实际生产情况修订工艺文件，更新版本号"),
    ("设备日常维护", "对生产设备进行日常点检和保养，记录维护日志"),
    ("来料检验", "对来料进行外观、尺寸、材质等方面的抽样检验"),
    ("成品检验", "对成品进行出厂前的最终检验，出具检验报告"),
    ("不合格品处理", "对检验不合格的产品进行隔离、返工或报废处理"),
    ("客户样品制作", "根据客户需求制作样品，记录制作过程和结果"),
    ("新员工工艺培训", "对新入职员工进行产品工艺知识培训和考核"),
    ("生产数据统计", "统计当日/本周产量、合格率、工时等生产数据"),
    ("模具维护保养", "对生产模具进行定期清洁、润滑和磨损检查"),
]

PLAN_TIMES = [("08:00", "10:00"), ("10:00", "12:00"), ("13:30", "15:30"), ("15:30", "17:30"), ("09:00", "11:30"), ("14:00", "16:30")]


def main():
    db = SessionLocal()
    try:
        models.Base.metadata.create_all(bind=engine)

        print(">>> 清空 tasks 表 ...")
        deleted = db.query(models.Task).delete(synchronize_session=False)
        db.commit()
        print(f"    已删除 {deleted} 条旧任务")

        products = db.query(models.Product).filter(models.Product.status == "启用").all()
        users = db.query(models.User).filter(models.User.status == "活跃").all()

        if not products:
            print("!!! 没有找到启用的产品，退出")
            return
        if not users:
            print("!!! 没有找到活跃用户，退出")
            return

        print(f">>> 产品: {len(products)} 个, 人员: {len(users)} 个")

        today = date.today()
        date_range = [today - timedelta(days=i) for i in range(14)]

        random.seed(42)
        new_tasks = []
        pid = 1

        for product in products:
            n_tasks = random.randint(4, 7)
            picked_users = random.sample(users, min(n_tasks, len(users)))
            for i in range(n_tasks):
                user = picked_users[i % len(picked_users)]
                task_date = random.choice(date_range)
                tmpl_title, tmpl_note = random.choice(TASK_TEMPLATES)
                plan_s, plan_e = random.choice(PLAN_TIMES)

                r = random.random()
                if r < 0.45:
                    status = "已完成"
                    progress = 100
                    actual_s = plan_s
                    actual_e = plan_e
                elif r < 0.75:
                    status = "进行中"
                    progress = random.randint(20, 85)
                    actual_s = plan_s
                    actual_e = ""
                elif r < 0.90:
                    status = "待办"
                    progress = 0
                    actual_s = ""
                    actual_e = ""
                else:
                    status = "已搁置"
                    progress = random.randint(10, 50)
                    actual_s = plan_s
                    actual_e = ""

                content = f"[{product.product_code}] {tmpl_title}"

                task = models.Task(
                    id=pid,
                    user_id=user.id,
                    product_id=product.id,
                    project_id=None,
                    task_date=task_date.strftime("%Y-%m-%d"),
                    content=content,
                    plan_start_time=plan_s,
                    plan_end_time=plan_e,
                    actual_start_time=actual_s,
                    actual_end_time=actual_e,
                    status=status,
                    progress=progress,
                    note=tmpl_note if random.random() > 0.3 else "",
                )
                new_tasks.append(task)
                pid += 1

        db.add_all(new_tasks)
        db.commit()

        status_count = {}
        for t in new_tasks:
            status_count[t.status] = status_count.get(t.status, 0) + 1
        print(f">>> 成功插入 {len(new_tasks)} 条任务")
        print(f"    状态分布: {status_count}")
        for p in products:
            cnt = sum(1 for t in new_tasks if t.product_id == p.id)
            print(f"    产品 #{p.id} {p.product_name}: {cnt} 条")

    finally:
        db.close()


if __name__ == "__main__":
    main()