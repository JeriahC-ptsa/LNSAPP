"""
Populate Database with Module Structure
Based on the comprehensive module list provided
"""

from app import app, db
from models import Module, MiniTask

def populate_modules():
    """Create all modules and mini-tasks based on the structure"""
    with app.app_context():
        print("=" * 80)
        print("POPULATING MODULE DATABASE")
        print("=" * 80)
        
        modules_data = {
            "FUNDAMENTALS": [
                {"name": "Computer Skills", "code": None, "status_type": "P/NYP"},
                {"name": "English", "code": None, "status_type": "P/NYP"},
                {"name": "Engineering Science", "code": None, "status_type": "P/NYP"},
                {"name": "Mathematics", "code": None, "status_type": "P/NYP"},
                {"name": "Life Skills I", "code": "652201-000-01-00-KM-01", "status_type": "C/NYC"},
                {"name": "Life Skills II", "code": "652201-000-01-00-KM-02", "status_type": "C/NYC"},
                {"name": "Life Skills III", "code": None, "status_type": "C/NYC"},
                {"name": "English II", "code": None, "status_type": "C/NYC"},
                {"name": "English III", "code": None, "status_type": "C/NYC"},
            ],
            "TOOLING U": [
                {"name": "INST04.001.01: Safety 100", "code": "652201-000-01-00-KM-03", "status_type": "C/NYC"},
                {"name": "INST04.001.02: Safety 200", "code": "652201-000-01-00-KM-04", "status_type": "C/NYC"},
                {"name": "INST04.001.03: Math & Science 100", "code": "652201-000-01-00-KM-05", "status_type": "C/NYC"},
                {"name": "INST04.001.04: Math & Science 200 & 300", "code": "652201-000-01-00-KM-06", "status_type": "C/NYC"},
                {"name": "INST04.001.05: Measurements 100", "code": "652201-000-01-00-KM-07", "status_type": "C/NYC"},
                {"name": "INST04.001.06: Materials 200", "code": "652201-000-01-00-KM-08", "status_type": "C/NYC"},
                {"name": "INST04.001.07: Drawings 200", "code": "652201-000-01-00-KM-09", "status_type": "C/NYC"},
                {"name": "INST04.002.08: Quality 100", "code": "652201-000-01-00-KM-10", "status_type": "C/NYC"},
                {"name": "INST04.002.09: NIMS Core Skills 100", "code": "652201-000-01-00-KM-11", "status_type": "C/NYC"},
                {"name": "INST04.002.10: GD&T 200", "code": "652201-000-01-00-KM-12", "status_type": "C/NYC"},
                {"name": "INST04.002.11: Machining Basics 100", "code": "652201-000-01-00-KM-13", "status_type": "C/NYC"},
                {"name": "INST04.002.12: Machining Basics 200", "code": "652201-000-01-00-KM-14", "status_type": "C/NYC"},
                {"name": "INST04.002.13: MMS", "code": "652201-000-01-00-KM-15", "status_type": "C/NYC"},
                {"name": "INST04.002.14: JPBL", "code": "652201-000-01-00-PM-01", "status_type": "C/NYC"},
                {"name": "INST04.002.15: Drill Press", "code": "652201-000-01-00-PM-04", "status_type": "C/NYC"},
                {"name": "INST04.002.16: Machining Advanced 300", "code": None, "status_type": "C/NYC"},
                {"name": "INST04.002.17: Milling", "code": None, "status_type": "C/NYC"},
                {"name": "INST04.002.18: Conventional Turning (TBC & TC)", "code": None, "status_type": "C/NYC"},
                {"name": "INST04.002.19: Grinding 100", "code": None, "status_type": "C/NYC"},
                {"name": "INST04.002.20: Grinding 200", "code": None, "status_type": "C/NYC"},
                {"name": "INST04.002.21: CNC Basics", "code": None, "status_type": "C/NYC"},
                {"name": "INST04.002.22: CNC Milling", "code": None, "status_type": "C/NYC"},
                {"name": "INST04.002.23: CNC Turning", "code": None, "status_type": "C/NYC"},
                {"name": "INST04.002.24: EDM", "code": None, "status_type": "C/NYC"},
            ],
            "THEORY MODULES": [
                {"name": "Applied Theory", "code": None, "status_type": "P/NYP", "credits": "75%"},
                {"name": "Project Management I", "code": "652201-000-01-00-PM-06", "status_type": "P/NYP"},
                {"name": "Project Management II", "code": "652201-000-01-00-PM-08", "status_type": "P/NYP"},
                {"name": "Project Management III", "code": "652201-000-01-00-PM-10", "status_type": "P/NYP"},
                {"name": "Manufacturing Economics I", "code": "652201-000-01-00-PM-12", "status_type": "P/NYP"},
                {"name": "Enterprise Resource Planning (ERP)", "code": "652201-000-01-00-PM-05", "status_type": "P/NYP"},
                {"name": "Plastics Processing I", "code": "652201-000-01-00-PM-14", "status_type": "P/NYP"},
                {"name": "Plastics Processing II", "code": "652201-000-01-00-PM-16", "status_type": "P/NYP"},
                {"name": "Metal Pressing, Blanking & Drawing Processes I", "code": "652201-000-01-00-PM-07", "status_type": "P/NYP"},
                {"name": "Metal Pressing, Blanking & Drawing Processes II", "code": "652201-000-01-00-PM-09", "status_type": "P/NYP"},
                {"name": "Computer Aided Design I", "code": "652201-000-01-00-PM-11", "status_type": "P/NYP"},
                {"name": "Computer Aided Design II", "code": "652201-000-01-00-PM-13", "status_type": "P/NYP", "credits": "60%"},
                {"name": "Computer Numerical Control Turning I Theory and Simulation", "code": "652201-000-01-00-PM-18", "status_type": "P/NYP", "credits": "60%"},
                {"name": "Computer Numerical Control Turning II Theory and Simulation", "code": "652201-000-01-00-PM-19", "status_type": "P/NYP", "credits": "60%"},
            ],
            "PRACTICAL MODULES": [
                {"name": "Measurement, Material & Safety (MMS)", "code": "652201-000-01-00-PM-15", "status_type": "P/NYP", 
                 "assessments": ["Online", "MT", "IWP", "CWP"]},
                {"name": "Job Planning Benchwork and Layout BW (2.1 I)", "code": "652201-000-01-00-PM-17", "status_type": "P/NYP",
                 "assessments": ["MT", "IWP", "CWP"]},
                {"name": "Job Planning Benchwork and Layout LO (2.2 I)", "code": "652201-000-01-00-PM-17", "status_type": "P/NYP",
                 "assessments": ["Online", "MT", "IWP", "CWP"]},
                {"name": "Turning Operations: Between Centres I (2.3 I)", "code": None, "status_type": "P/NYP",
                 "assessments": ["Online", "MT", "IWP", "CWP"]},
                {"name": "Turning Operations: Chucking I (2.4 I)", "code": None, "status_type": "P/NYP",
                 "assessments": ["Online", "MT", "IWP", "CWP"]},
                {"name": "Milling I (2.5 & 2.6 I)", "code": None, "status_type": "P/NYP",
                 "assessments": ["Online", "MT", "IWP", "CWP"]},
                {"name": "Grinding Skills I (2.7B I)", "code": None, "status_type": "P/NYP",
                 "assessments": ["Online", "MT", "IWP", "CWP"]},
                {"name": "Drill Press I (2.8 I)", "code": None, "status_type": "P/NYP",
                 "assessments": ["Online", "MT", "IWP", "CWP"]},
                {"name": "CNC Milling I (2.10 I)", "code": None, "status_type": "P/NYP",
                 "assessments": ["Online", "MT", "IWP", "CWP"]},
                {"name": "CNC Turning I (2.11 I)", "code": None, "status_type": "P/NYP",
                 "assessments": ["Online", "MT", "IWP", "CWP"]},
                {"name": "Turning Operations: Between Centres II (2.3 II)", "code": None, "status_type": "P/NYP",
                 "assessments": ["Online", "MT", "IWP", "CWP"]},
                {"name": "Turning Operations: Chucking II (2.5 II)", "code": None, "status_type": "P/NYP",
                 "assessments": ["Online", "MT", "IWP", "CWP"]},
                {"name": "Milling II (2.6/2.7/2.9 II)", "code": None, "status_type": "P/NYP",
                 "assessments": ["Online", "MT", "IWP", "CWP"]},
                {"name": "Grinding Skills II (2.16 II)", "code": None, "status_type": "P/NYP",
                 "assessments": ["Online", "MT", "IWP", "CWP"]},
                {"name": "EDM Plunge II (2.19 II)", "code": None, "status_type": "P/NYP",
                 "assessments": ["Online", "MT", "IWP", "CWP"]},
                {"name": "EDM Wire II (2.20 II)", "code": None, "status_type": "P/NYP",
                 "assessments": ["Online", "MT", "IWP", "CWP"]},
                {"name": "CNC Milling II (2.21 & 2.22 II)", "code": None, "status_type": "P/NYP",
                 "assessments": ["Online", "MT1", "MT2", "IWP", "CWP"]},
                {"name": "CNC Turning II (2.22 & 2.23 II)", "code": None, "status_type": "P/NYP",
                 "assessments": ["Online", "MT1", "MT2", "IWP", "CWP"]},
                {"name": "Job Pieces Theory L III - Shrinkage Factor", "code": "652201-000-01-00-PM-23", "status_type": "P/NYP"},
                {"name": "Job Pieces Practical L III - Mould", "code": "652201-000-01-00-PM-20", "status_type": "P/NYP"},
                {"name": "Job Pieces Theory L III - Offset", "code": "652201-000-01-00-PM-22", "status_type": "P/NYP"},
                {"name": "Job Pieces Practical L III - Die", "code": None, "status_type": "P/NYP"},
            ]
        }
        
        total_created = 0
        total_mini_tasks = 0
        
        for category, modules in modules_data.items():
            print(f"\n{'='*80}")
            print(f"CATEGORY: {category}")
            print(f"{'='*80}")
            
            for module_data in modules:
                # Check if module already exists
                existing = Module.query.filter_by(name=module_data["name"]).first()
                
                if existing:
                    print(f"  ⊘ SKIP: {module_data['name']} (already exists)")
                    continue
                
                # Create module with all fields
                module = Module(
                    name=module_data["name"],
                    code=module_data.get("code"),
                    category=category,
                    status_type=module_data["status_type"],
                    credits=module_data.get("credits")
                )
                db.session.add(module)
                db.session.flush()  # Get the ID
                
                total_created += 1
                print(f"  ✓ CREATED: {module_data['name']}")
                
                if module_data.get("code"):
                    print(f"    Code: {module_data['code']}")
                if module_data.get("credits"):
                    print(f"    Credits: {module_data['credits']}")
                print(f"    Status Type: {module_data['status_type']}")
                print(f"    Category: {category}")
                
                # Create mini-tasks for assessments if specified
                if "assessments" in module_data:
                    print(f"    Assessments:")
                    for assessment in module_data["assessments"]:
                        mini_task = MiniTask(
                            title=assessment,
                            module_id=module.id
                        )
                        db.session.add(mini_task)
                        total_mini_tasks += 1
                        print(f"      - {assessment}")
        
        # Commit all changes
        db.session.commit()
        
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        print(f"✓ Modules Created: {total_created}")
        print(f"✓ Mini-Tasks Created: {total_mini_tasks}")
        print(f"\nBreakdown:")
        print(f"  - Fundamentals: 9 modules")
        print(f"  - Tooling U: 24 modules")
        print(f"  - Theory Modules: 14 modules")
        print(f"  - Practical Modules: 22 modules")
        print(f"\nTotal: 69 modules")
        print(f"{'='*80}")
        print("✓ DATABASE POPULATION COMPLETE!")
        print(f"{'='*80}")

if __name__ == "__main__":
    populate_modules()
