# 📅 Advanced Schedule Generation Guide

## Overview
The Advanced Schedule Generator allows you to create flexible schedules with support for:
- **Different session types** (Regular Practical, Practical Tests, Written Tests)
- **Multiple students per test session**
- **Filtering by Group, Module, Machine, or Custom selection**
- **Day-of-week restrictions**
- **Priority scheduling rules**

---

## 🚀 How to Access

**Navigate to**: Schedule → Advanced Generator

Or directly: `http://127.0.0.1:5000/schedule/generate_advanced`

---

## ✨ Key Features

### 1. **Session Types**

#### **Regular Practical**
- One student per time slot
- Students work individually on machines
- Standard scheduling

#### **Practical Test**
- Multiple students can write simultaneously
- Configurable students per session (1-50)
- Option to keep same machine for all test sessions
- All students in batch get same time slot

#### **Written Test**
- Similar to practical test
- Multiple students per session
- No machine required (can use classroom)

---

### 2. **Filtering Options**

#### **Generate For: All Students**
- Schedules all students in the database
- No filtering applied

#### **Generate For: Specific Group**
- Select one group
- Only students in that group are scheduled
- Perfect for group-specific practicals

#### **Generate For: Specific Module**
- Select one module
- Only students assigned to that module are scheduled
- Automatically includes module name in schedule

#### **Generate For: Specific Machine(s)**
- Select one or more machines
- Schedule rotates through selected machines only
- Hold Ctrl/Cmd to select multiple

#### **Generate For: Custom Selection**
- Manually select specific students
- Hold Ctrl/Cmd to select multiple students
- Most flexible option

---

### 3. **Date & Time Settings**

| Setting | Description | Example |
|---------|-------------|---------|
| **Start Date** | First day of scheduling period | 2025-10-16 |
| **End Date** | Last day of scheduling period | 2025-10-23 |
| **Start Time** | Daily session start time | 08:00 |
| **End Time** | Daily session end time | 16:00 |
| **Lunch Start** | When lunch break begins | 12:00 |
| **Lunch Duration** | How long lunch break lasts (minutes) | 60 |
| **Break Between Sessions** | Gap between slots (minutes) | 10 |

---

### 4. **Advanced Options**

#### **Scheduling Priority**

**FIFO (First In, First Out)**
- Students scheduled in database order
- Simple and predictable

**SPT (Shortest Processing Time)**
- Shorter sessions scheduled first
- Minimizes average wait time

**LPT (Longest Processing Time)**
- Longer sessions scheduled first
- Good for complex tasks

**Group by Group**
- Schedules all students from same group together
- Keeps groups consecutive

**Group by Module**
- Schedules all students doing same module together
- Good for module-specific tests

#### **Days of Week**
- Select which days to schedule
- Monday through Friday checkboxes
- Unselected days are skipped
- Example: Uncheck Wednesday for staff meetings

#### **Clear Existing Schedule**
- **Checked**: Deletes all current schedule entries before generating
- **Unchecked**: Adds to existing schedule
- ⚠️ **Warning**: Clearing cannot be undone!

---

## 📋 Usage Examples

### Example 1: **Group Practical Sessions**

**Scenario**: Schedule Oct 21 Group for regular practicals

**Settings**:
- Session Type: `Regular Practical`
- Session Duration: `60 minutes`
- Generate For: `Specific Group` → Select "Oct 21 Group"
- Start Date: Today
- End Date: +7 days
- Days: Mon-Fri checked
- Clear Existing: ✅ Checked

**Result**: Each student gets individual 60-minute session spread across week

---

### Example 2: **Module Test - Multiple Students**

**Scenario**: Schedule practical test for Machining Level II module, 5 students per session

**Settings**:
- Session Type: `Practical Test`
- Students Per Session: `5`
- Session Duration: `120 minutes`
- Generate For: `Specific Module` → Select "2.2 Machining Level II"
- Same Machine: ✅ Checked
- Start Date: Tomorrow
- End Date: Tomorrow + 2 days
- Priority: `Group by Group`
- Clear Existing: ❌ Unchecked

**Result**: Students batched in groups of 5, each batch gets 2-hour test slot

---

### Example 3: **Written Test for Multiple Groups**

**Scenario**: Written test for all students, 20 per session

**Settings**:
- Session Type: `Written Test`
- Students Per Session: `20`
- Session Duration: `90 minutes`
- Generate For: `All Students`
- Start Date: Specific test date
- End Date: Same day
- Days: Only Friday checked
- Break Between: `15 minutes`
- Clear Existing: ❌ Unchecked

**Result**: Multiple 90-minute test sessions with 20 students each, 15-min breaks between

---

### Example 4: **Specific Machines Only**

**Scenario**: Schedule only on CNC machines

**Settings**:
- Session Type: `Regular Practical`
- Generate For: `Specific Machine` → Select CNC machines (hold Ctrl)
- Students: Will cycle through selected machines only

**Result**: Schedule uses only selected machines, students rotate through them

---

### Example 5: **Custom Student Selection**

**Scenario**: Makeup sessions for 3 specific students

**Settings**:
- Session Type: `Regular Practical`
- Generate For: `Custom Selection` → Select 3 students
- Session Duration: `45 minutes`
- Start Date: Next available day
- Clear Existing: ❌ Unchecked

**Result**: Only selected students scheduled, existing schedule unchanged

---

## 🔄 How It Works

### Regular Practical Flow:
1. System gets filtered students
2. Applies priority sorting
3. For each student:
   - Finds next available time slot
   - Skips lunch breaks
   - Skips non-working days
   - Assigns to next machine in rotation
   - Adds break time after session

### Test Session Flow:
1. System gets filtered students
2. Batches students (e.g., groups of 5)
3. For each batch:
   - Finds time slot that fits all students
   - Assigns same machine (if option checked)
   - Creates schedule entry for each student in batch
   - All get identical time slot
   - Moves to next batch

---

## 💡 Pro Tips

### **For Regular Practicals:**
- Use `Group by Group` priority to keep classmates together
- Set 10-15 minute breaks between sessions for setup
- Consider 2-3 hour sessions for complex modules

### **For Practical Tests:**
- Set `students_per_session` to number of available test stations
- Check "Same Machine" to ensure consistency
- Allow extra time (e.g., 120-180 minutes)
- Leave breaks between batches for marking

### **For Written Tests:**
- Set high `students_per_session` (classroom capacity)
- No machine filtering needed
- Schedule during specific test days only
- Uncheck non-test days

### **General Tips:**
- Always preview before clearing existing schedule
- Use custom selection for makeup/remedial sessions
- Set realistic session durations
- Account for lunch breaks (default 12:00-13:00)
- Check `Clear Existing` only when starting fresh

---

## ⚠️ Important Notes

### **Database Changes**
The Schedule model now includes:
- `session_type`: practical, practical_test, written_test
- `module_name`: Which module this session is for
- `capacity`: Number of students per session
- `notes`: Optional session notes

### **Migration Required**
After installing, run:
```bash
flask db migrate -m "Add session type and module to schedule"
flask db upgrade
```

---

## 🎯 Quick Reference

| Feature | Use Case |
|---------|----------|
| Session Type: Practical | Regular one-on-one sessions |
| Session Type: Practical Test | Hands-on assessments, multiple students |
| Session Type: Written Test | Written exams, large groups |
| Filter: Group | Class-specific schedules |
| Filter: Module | Module tests or practicals |
| Filter: Machine | Limited machine availability |
| Filter: Custom | Makeup sessions, specific students |
| Priority: FIFO | Simple, predictable |
| Priority: GROUP | Keep groups together |
| Priority: MODULE | Organize by module |
| Days: Custom | Skip meeting days |
| Clear Existing: On | Fresh start |
| Clear Existing: Off | Add to schedule |

---

## ✅ Checklist Before Generating

- [ ] Session type selected appropriately
- [ ] Session duration realistic for task
- [ ] Correct filter applied (group/module/machine/custom)
- [ ] Date range covers needed period
- [ ] Working hours set correctly
- [ ] Lunch break configured
- [ ] Days of week checked appropriately
- [ ] Priority rule makes sense for scenario
- [ ] Decided on clear existing or append
- [ ] Notes added if needed

---

## 🆘 Troubleshooting

**Problem**: No students scheduled
- **Check**: Filter settings - ensure students match criteria
- **Check**: Module filter - students must be assigned to that module

**Problem**: Schedule runs past end date
- **Cause**: Too many students for time period
- **Solution**: Extend date range or reduce session duration

**Problem**: Lunch breaks not working
- **Check**: Lunch start time and duration settings
- **Check**: Ensure sessions fit before/after lunch

**Problem**: Tests overlap
- **Cause**: Batch size too large or sessions too long
- **Solution**: Reduce students per session or extend time slots

**Problem**: Machines not rotating
- **Check**: Multiple machines selected
- **Check**: "Same Machine" option unchecked

---

## 📊 Schedule View

After generation, view your schedule:
- **Schedule → View Schedule** - List view with filters
- **Schedule → Calendar View** - Visual calendar
- Both views now show:
  - Session type badge (Practical/Test)
  - Module name (if applicable)
  - Capacity (for multi-student sessions)
  - Color coding by type

---

## 🎉 You're Ready!

Navigate to **Schedule → Advanced Generator** and start creating flexible, powerful schedules!

For basic scheduling needs, use **Schedule → Basic Schedule Generator**.
For complex scenarios, tests, and filtering, use **Advanced Generator**.
