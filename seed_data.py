# student_scheduler/seed_data.py

from app import db, app
from models import (
    Group, Lecturer, Student, Machine, Module, MiniTask,
    StudentMiniTaskProgress, ErrorLog, Inventory, OverheadCost,
    MachineMaintenance, MacroPlan, Schedule
)
from datetime import datetime, timedelta
import pandas as pd
import random
import re

print("Running seed script...")


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # ---------- IMPORT STUDENTS FROM EXCEL ----------
        group_file = "./Groups.xlsx"
        df = pd.read_excel(group_file)
        df = df.iloc[:, :2].dropna()
        df.columns = ['Student Name', 'Group Name']

        students = []
        group_cache = {}

        for _, row in df.iterrows():
            name = str(row['Student Name']).strip()
            group_name = str(row['Group Name']).strip()
            if not name or not group_name:
                continue

            if group_name not in group_cache:
                group_obj = Group(name=group_name)
                db.session.add(group_obj)
                db.session.commit()
                group_cache[group_name] = group_obj

            student = Student(
                student_name=name,
                level="Level I" if "21" in group_name else "Level II",
                mark=random.choice([40.0, 50.0, 65.0, 80.0]),
                group=group_cache[group_name]
            )
            students.append(student)

        db.session.add_all(students)
        db.session.commit()

        # ---------- LECTURERS ----------
        db.session.add_all([
            Lecturer(name="Mr. John Smith", phone_number="0821234567", email="john@ptsa.org", notes="CNC instructor"),
            Lecturer(name="Ms. Jane Doe", phone_number="0839876543", email="jane@ptsa.org", notes="Milling specialist")
        ])

        # ---------- MACHINES ----------
        machine_names = [
            ("Pedestal Drill", "PD"),
            ("Surface Grinder", "SG"),
            ("Vertical Mill", "VM"),
            ("Lathe", "LATHE"),
            ("CNC Mill", "CNC M"),
            ("CNC Lathe", "CNC T"),
            ("EDM Wire", "EDM W"),
            ("EDM Plunge", "EDM P")
        ]

        machines = []
        for name, short in machine_names:
            for i in range(random.randint(1, 3)):
                machines.append(Machine(machine_name=f"{name} #{i+1}", level="Level I"))

        db.session.add_all(machines)
        db.session.commit()

        # ---------- MODULES & MINITASKS ----------
        machining_i = Module(name="2.1 Machining Level I")
        machining_ii = Module(name="2.2 Machining Level II")
        mould_die = Module(name="2.3 Mould and Die")
        db.session.add_all([machining_i, machining_ii, mould_die])
        db.session.commit()

        all_tasks = []
        tasks_dict = {
            machining_i: [
                "2.10.1.1 CNC Milling I Mini-Task",
                "2.11.1.1 CNC Turning Mini-Task",
                "2.8.1.1 Drill Press I Mini-Task",
                "2.5.2.6.1.1 Vertical Milling I Mini-Task",
                "2.7.B.1.1 Surface Grinding I Mini-Task"
            ],
            machining_ii: [
                "2.19.1.1 EDM Plunge II Mini-Task",
                "2.20.1.1 EDM Wire Mini-Task",
                "2.21.2.22.II.1 CNC Milling II Mini-Task",
                "2.22.2.23.II.1 CNC Turning II Mini-Task",
                "2.6.2.7.9.1.1 Manual Milling Mini-Task"
            ],
            mould_die: [
                "Diemaking – OJT Practical",
                "Mouldmaking – OJT Practical"
            ]
        }

        for module, titles in tasks_dict.items():
            for title in titles:
                task = MiniTask(module_id=module.id, title=title)
                db.session.add(task)
                all_tasks.append(task)

        db.session.commit()

        # ---------- STUDENT MINI TASK PROGRESS ----------
        for student in Student.query.all():
            assigned_tasks = random.sample(all_tasks, k=5)
            for task in assigned_tasks:
                progress = StudentMiniTaskProgress(
                    student_id=student.id,
                    mini_task_id=task.id,
                    attempt_1="Pass",
                    attempt_2="",
                    attempt_3="",
                    iwp_1="Done",
                    cwp_1="Pending",
                    oe_1="Yes",
                    notes="Auto-generated progress"
                )
                db.session.add(progress)

        db.session.commit()

        # ---------- WEEKLY SCHEDULE + MACRO PLAN ----------
        all_students = Student.query.all()
        all_machines = Machine.query.all()
        time_slots = [(7,30,9,30), (9,45,11,45), (12,15,14,15), (14,30,16,0)]
        today = datetime(2025, 4, 14)

        for day_offset in range(10):
            current_day = today + timedelta(days=day_offset)
            if current_day.weekday() >= 5:
                continue

            machine_usage = {m.machine_name: 0.0 for m in all_machines}
            scheduled_students = random.sample(all_students, k=min(len(all_students), len(time_slots)*len(all_machines)))
            idx = 0

            for slot in time_slots:
                slot_start = datetime(current_day.year, current_day.month, current_day.day, slot[0], slot[1])
                slot_end = datetime(current_day.year, current_day.month, current_day.day, slot[2], slot[3])
                duration = (slot_end - slot_start).seconds / 3600.0

                for machine in all_machines:
                    if idx >= len(scheduled_students): break
                    student = scheduled_students[idx]
                    idx += 1
                    sch = Schedule(
                        student_name=student.student_name,
                        group_name=student.group.name,
                        machine_name=machine.machine_name,
                        start_time=slot_start,
                        end_time=slot_end,
                        extra_time=random.choice([0, 15])
                    )
                    db.session.add(sch)
                    machine_usage[machine.machine_name] += duration

            for mname, total_usage in machine_usage.items():
                macro = MacroPlan(
                    machine_name=mname,
                    date=current_day,
                    planned_maintenance=random.choice([0.5, 1.0]),
                    breakdown=random.choice([0, 0.5]),
                    installed_capacity=8.0,
                    usage=round(total_usage, 2)
                )
                db.session.add(macro)

        db.session.commit()
        print("✅ Seeded 2 weeks of data, schedules, and macroplans.")

if __name__ == "__main__":
    seed()
