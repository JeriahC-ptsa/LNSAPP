# Day View Feature Guide

## Overview
The day view feature allows you to view and manage schedule slots on an hourly basis for any specific day.

## How to Access

### From Calendar View
1. Navigate to **Schedule → Calendar View** in the menu
2. **Click on any date** in the calendar
3. You will be redirected to the day view for that date

### Direct URL
- Access directly via: `http://127.0.0.1:5000/schedule/day/YYYY-MM-DD`
- Example: `http://127.0.0.1:5000/schedule/day/2025-10-07`

## Features

### 1. View Hourly Slots
- Displays time slots from **7:00 AM to 6:00 PM**
- Each hour shows all scheduled bookings
- Empty slots are clearly marked

### 2. Add New Slot
- Click the **"Add Slot"** button in the top-right corner
- Fill in the form:
  - **Student**: Select from dropdown
  - **Machine**: Select from dropdown
  - **Start Time**: Date and time picker
  - **End Time**: Date and time picker
- System automatically checks for conflicts
- Success/error notifications appear after submission

### 3. Edit Existing Slot
- **Click on any slot card** to open the edit modal
- Modify any of the following:
  - Student name
  - Machine assignment
  - Start time
  - End time
- Conflict detection prevents overlapping bookings
- Changes are saved immediately

### 4. Delete Slot
- Click the **trash icon** (🗑️) on any slot card
- Confirm the deletion in the popup dialog
- Slot is removed immediately

### 5. Navigate Between Days
- Use **"Previous Day"** button to go back one day
- Use **"Next Day"** button to go forward one day
- Current date is displayed in the center

## Slot Card Information
Each slot card displays:
- 👤 **Student Name**
- ⚙️ **Machine Name**
- 🕐 **Time Range** (HH:MM - HH:MM)
- 👥 **Group Name** (if assigned)

## Conflict Detection
The system prevents:
- Double-booking the same student on the same machine
- Overlapping time slots for the same student-machine combination
- Invalid time ranges (end time before start time)

## API Endpoints

### View Day Schedule
```
GET /schedule/day/<date>
```

### Add New Slot
```
POST /schedule/slot/add
Body: student_name, machine_name, start_time, end_time
```

### Edit Slot
```
GET /schedule/slot/edit/<slot_id>  (Get slot data)
POST /schedule/slot/edit/<slot_id> (Update slot)
Body: student_name, machine_name, start_time, end_time
```

### Delete Slot
```
POST /schedule/slot/delete/<slot_id>
```

## Tips
- The day view automatically refreshes after any add/edit/delete operation
- All times are in 24-hour format
- Conflict warnings appear immediately if you try to create overlapping bookings
- Use the calendar view for a monthly overview, then drill down to day view for detailed management

## Troubleshooting

### Slot not appearing after adding
- Check if the start time falls within 7 AM - 6 PM range
- Verify the date matches the current day view

### Cannot edit slot
- Ensure you have a stable internet connection
- Check browser console for any JavaScript errors
- Refresh the page and try again

### Conflict error when no conflict exists
- Verify the exact times don't overlap with existing bookings
- Check if the same student-machine combination exists in that time range
