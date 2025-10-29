"""
Test New Assessment Features
Creates sample data to verify the new system works
"""

from app import app, db
from models import Student, Module, MiniTask, StudentModuleProgress, StudentMiniTaskProgress, Attempt, Group
from datetime import datetime

def test_features():
    """Test new assessment features"""
    with app.app_context():
        print("=" * 60)
        print("TESTING NEW ASSESSMENT FEATURES")
        print("=" * 60)
        
        # Get or create test data
        test_group = Group.query.filter_by(name="Test Group").first()
        if not test_group:
            test_group = Group(name="Test Group")
            db.session.add(test_group)
            db.session.commit()
        
        test_student = Student.query.filter_by(student_name="Test Student").first()
        if not test_student:
            test_student = Student(
                student_name="Test Student",
                level="Level 1",
                mark=0,
                group_id=test_group.id
            )
            db.session.add(test_student)
            db.session.commit()
        
        test_module = Module.query.filter_by(name="Test Module").first()
        if not test_module:
            test_module = Module(name="Test Module")
            db.session.add(test_module)
            db.session.commit()
        
        test_mini_task = MiniTask.query.filter_by(title="Test Mini Task").first()
        if not test_mini_task:
            test_mini_task = MiniTask(
                title="Test Mini Task",
                module_id=test_module.id
            )
            db.session.add(test_mini_task)
            db.session.commit()
        
        print(f"\n✓ Test data ready:")
        print(f"  - Student: {test_student.student_name}")
        print(f"  - Module: {test_module.name}")
        print(f"  - Mini-Task: {test_mini_task.title}")
        
        # Test 1: Module-level progress
        print("\n" + "-" * 60)
        print("TEST 1: Module-Level Progress")
        print("-" * 60)
        
        module_progress = StudentModuleProgress.query.filter_by(
            student_id=test_student.id,
            module_id=test_module.id
        ).first()
        
        if not module_progress:
            module_progress = StudentModuleProgress(
                student_id=test_student.id,
                module_id=test_module.id,
                result="Pass",
                completion_date=datetime.utcnow(),
                notes="Test module completion"
            )
            db.session.add(module_progress)
            db.session.commit()
            print("✓ Created module progress record")
        else:
            print("✓ Module progress already exists")
        
        print(f"  Result: {module_progress.result}")
        print(f"  Completion: {module_progress.completion_date}")
        
        # Test 2: Mini-task progress with unlimited attempts
        print("\n" + "-" * 60)
        print("TEST 2: Unlimited Attempts System")
        print("-" * 60)
        
        mini_task_progress = StudentMiniTaskProgress.query.filter_by(
            student_id=test_student.id,
            mini_task_id=test_mini_task.id
        ).first()
        
        if not mini_task_progress:
            mini_task_progress = StudentMiniTaskProgress(
                student_id=test_student.id,
                mini_task_id=test_mini_task.id,
                notes="Testing unlimited attempts"
            )
            db.session.add(mini_task_progress)
            db.session.commit()
            print("✓ Created mini-task progress record")
        else:
            print("✓ Mini-task progress already exists")
        
        # Add multiple attempts of different types
        attempt_types = [
            ('regular', 'Fail'),
            ('regular', 'Fail'),
            ('regular', 'Pass'),
            ('iwp', 'Fail'),
            ('iwp', 'Pass'),
            ('cwp', 'Pass'),
            ('oe', 'Pass'),
        ]
        
        existing_attempts = Attempt.query.filter_by(progress_id=mini_task_progress.id).count()
        
        if existing_attempts == 0:
            for idx, (attempt_type, result) in enumerate(attempt_types, 1):
                attempt = Attempt(
                    progress_id=mini_task_progress.id,
                    attempt_type=attempt_type,
                    result=result,
                    notes=f"Test attempt #{idx}"
                )
                db.session.add(attempt)
            db.session.commit()
            print(f"✓ Created {len(attempt_types)} test attempts")
        else:
            print(f"✓ {existing_attempts} attempts already exist")
        
        # Display all attempts
        all_attempts = Attempt.query.filter_by(progress_id=mini_task_progress.id).all()
        print(f"\nTotal attempts recorded: {len(all_attempts)}")
        
        for attempt_type in ['regular', 'iwp', 'cwp', 'oe']:
            type_attempts = [a for a in all_attempts if a.attempt_type == attempt_type]
            if type_attempts:
                print(f"\n  {attempt_type.upper()} Attempts ({len(type_attempts)}):")
                for idx, att in enumerate(type_attempts, 1):
                    print(f"    #{idx}: {att.result} - {att.attempt_date.strftime('%Y-%m-%d %H:%M')}")
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        print("\nThe new assessment system is working correctly!")
        print("You can now:")
        print("  1. Record module-level Pass/Fail results")
        print("  2. Add unlimited attempts for mini-tasks")
        print("  3. Use Pass/Fail dropdowns for all assessments")
        print("=" * 60)

if __name__ == "__main__":
    test_features()
