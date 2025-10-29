# reports.py
from flask import Blueprint, render_template, request, jsonify, send_file, session
from flask_login import login_required, current_user
from models import db, Site, Student, Machine, Module, Lecturer, Group, Schedule, Inventory, InventoryUsage, StudentMiniTaskProgress, MiniTask
from auth_models import DynamicField, DynamicFieldValue
from functools import wraps
from flask import flash, redirect, url_for

# Import site helper functions from app
def get_active_site_id():
    """Get the currently active site ID from session"""
    return session.get('active_site_id')

def require_site_access(f):
    """Decorator to ensure user has access to active site"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        site_id = get_active_site_id()
        if not site_id:
            # If no site selected, redirect
            if current_user.is_authenticated:
                if current_user.sites:
                    session['active_site_id'] = current_user.sites[0].id
                    site_id = current_user.sites[0].id
        
        if not site_id:
            flash('Please select a site first.', 'warning')
            return redirect(url_for('index'))
        
        # Verify user has access
        if not current_user.is_super_admin() and not current_user.has_site_access(site_id):
            flash('You do not have access to this site.', 'danger')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function
from sqlalchemy import func, case, extract
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
import plotly.express as px
import json
from io import BytesIO, StringIO
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from bs4 import BeautifulSoup

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
@require_site_access
def reports_page():
    site_id = get_active_site_id()
    
    # Get filter options (site-specific or all for admins)
    from app import apply_site_filter
    groups = apply_site_filter(Group.query, Group).all()
    modules = apply_site_filter(Module.query, Module).all()
    machines = apply_site_filter(Machine.query, Machine).all()
    inventory_items = apply_site_filter(Inventory.query, Inventory).all()
    students = apply_site_filter(Student.query, Student).all()
    
    # Get dynamic fields for both Students and Machines
    student_dynamic_fields = DynamicField.query.filter_by(model_name='Student').all()
    machine_dynamic_fields = DynamicField.query.filter_by(model_name='Machine').all()
    dynamic_fields = student_dynamic_fields  # Keep for backward compatibility
    
    # Available report types
    report_types = [
        {'id': 'student_performance', 'name': 'Student Performance Analysis', 'icon': 'bi-graph-up', 'category': 'Students'},
        {'id': 'student_progress', 'name': 'Student Progress Tracking', 'icon': 'bi-trophy', 'category': 'Students'},
        {'id': 'group_comparison', 'name': 'Group Comparison & Analytics', 'icon': 'bi-people', 'category': 'Students'},
        {'id': 'demographic_analysis', 'name': 'Student Demographics', 'icon': 'bi-pie-chart', 'category': 'Students'},
        {'id': 'completion_rates', 'name': 'Module Completion Rates', 'icon': 'bi-check-circle', 'category': 'Progress'},
        {'id': 'attempt_analysis', 'name': 'Assessment Attempts Analysis', 'icon': 'bi-clipboard-data', 'category': 'Progress'},
        {'id': 'contingency_table', 'name': 'Contingency Table Analysis', 'icon': 'bi-table', 'category': 'Advanced'},
        {'id': 'custom_report', 'name': 'Custom Report Builder', 'icon': 'bi-gear-wide-connected', 'category': 'Advanced'},
        {'id': 'cross_tabulation', 'name': 'Cross-Tabulation Report', 'icon': 'bi-grid-3x2', 'category': 'Advanced'},
        {'id': 'inventory_usage', 'name': 'Inventory Usage Statistics', 'icon': 'bi-box-seam', 'category': 'Resources'},
        {'id': 'inventory_stock', 'name': 'Inventory Stock Levels', 'icon': 'bi-boxes', 'category': 'Resources'},
        {'id': 'machine_utilization', 'name': 'Machine Utilization Report', 'icon': 'bi-gear', 'category': 'Resources'},
        {'id': 'schedule_analysis', 'name': 'Schedule & Attendance Analysis', 'icon': 'bi-calendar3', 'category': 'Schedule'},
        {'id': 'lecturer_workload', 'name': 'Lecturer Workload Analysis', 'icon': 'bi-person-badge', 'category': 'Management'},
        {'id': 'custom_field_analysis', 'name': 'Custom Fields Analysis', 'icon': 'bi-grid-3x3', 'category': 'Custom'},
    ]
    
    return render_template('reports_enhanced.html',
                         groups=groups,
                         modules=modules,
                         machines=machines,
                         inventory_items=inventory_items,
                         students=students,
                         dynamic_fields=dynamic_fields,
                         student_dynamic_fields=student_dynamic_fields,
                         machine_dynamic_fields=machine_dynamic_fields,
                         report_types=report_types)

@reports_bp.route('/reports/generate', methods=['POST'])
@login_required
@require_site_access
def generate_report():
    site_id = get_active_site_id()
    
    data = request.get_json()
    report_type = data.get('report_type')
    filters = data.get('filters', {})
    filters['site_id'] = site_id  # Add site_id to filters
    chart_type = data.get('chart_type', 'bar')
    
    try:
        if report_type == 'student_performance':
            result = generate_student_performance_report(filters, chart_type)
        elif report_type == 'group_comparison':
            result = generate_group_comparison_report(filters, chart_type)
        elif report_type == 'inventory_usage':
            result = generate_inventory_usage_report(filters, chart_type)
        elif report_type == 'machine_utilization':
            result = generate_machine_utilization_report(filters, chart_type)
        elif report_type == 'schedule_analysis':
            result = generate_schedule_analysis_report(filters, chart_type)
        elif report_type == 'student_progress':
            result = generate_student_progress_report(filters, chart_type)
        elif report_type == 'demographic_analysis':
            result = generate_demographic_analysis_report(filters, chart_type)
        elif report_type == 'completion_rates':
            result = generate_completion_rates_report(filters, chart_type)
        elif report_type == 'attempt_analysis':
            result = generate_attempt_analysis_report(filters, chart_type)
        elif report_type == 'inventory_stock':
            result = generate_inventory_stock_report(filters, chart_type)
        elif report_type == 'lecturer_workload':
            result = generate_lecturer_workload_report(filters, chart_type)
        elif report_type == 'custom_field_analysis':
            result = generate_custom_field_analysis_report(filters, chart_type)
        elif report_type == 'contingency_table':
            result = generate_contingency_table_report(filters, chart_type)
        elif report_type == 'custom_report':
            result = generate_custom_report(filters, chart_type)
        elif report_type == 'cross_tabulation':
            result = generate_cross_tabulation_report(filters, chart_type)
        else:
            return jsonify({'success': False, 'error': 'Invalid report type'})
        
        return jsonify({'success': True, **result})
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})

def generate_student_performance_report(filters, chart_type):
    """Generate student performance analytics"""
    site_id = filters.get('site_id')
    query = Student.query
    
    # Apply site filter
    if site_id:
        query = query.filter(Student.site_id == site_id)
    
    # Apply group filters (multiple groups)
    if filters.get('group_ids'):
        query = query.filter(Student.group_id.in_(filters['group_ids']))
    
    students = query.all()
    
    # Aggregate data
    data = []
    for student in students:
        data.append({
            'Name': student.student_name,
            'Group': student.group.name if student.group else 'N/A'
        })
    
    df = pd.DataFrame(data)
    
    # Generate statistics
    stats = {
        'total_students': len(students),
    }
    
    # Generate chart
    chart_html = None
    if not df.empty:
        if chart_type == 'bar':
            # Student count by group
            group_count = df.groupby('Group').size().reset_index(name='Count')
            fig = go.Figure(data=[
                go.Bar(x=group_count['Group'], y=group_count['Count'], 
                      marker_color='#4A90E2', text=group_count['Count'], textposition='auto')
            ])
            fig.update_layout(
                title='Student Count by Group',
                xaxis_title='Group',
                yaxis_title='Number of Students',
                template='plotly_white',
                height=500
            )
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
        elif chart_type == 'pie':
            # Student distribution by group
            group_counts = df['Group'].value_counts()
            fig = go.Figure(data=[
                go.Pie(labels=group_counts.index, values=group_counts.values, hole=0.3)
            ])
            fig.update_layout(title='Student Distribution by Group', height=500)
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
    
    table_html = df.to_html(classes='table table-striped table-hover', index=False) if not df.empty else '<p>No data available</p>'
    
    return {'chart': chart_html, 'table': table_html, 'stats': stats}

def generate_group_comparison_report(filters, chart_type):
    """Compare performance across groups"""
    site_id = filters.get('site_id')
    query = Group.query
    
    # Apply site filter
    if site_id:
        query = query.filter(Group.site_id == site_id)
    
    groups = query.all()
    
    data = []
    for group in groups:
        students = Student.query.filter_by(group_id=group.id).all()
        if students:
            # Calculate completion rates from StudentMiniTaskProgress
            completion_rates = []
            for student in students:
                # Get all progress records for this student
                progress_records = StudentMiniTaskProgress.query.filter_by(
                    student_id=student.id
                ).all()
                
                if progress_records:
                    # Count passed tasks (any attempt that passed)
                    passed = sum(1 for p in progress_records 
                               if p.attempt_1 == 'Pass' or p.attempt_2 == 'Pass' or p.attempt_3 == 'Pass')
                    completion_rate = (passed / len(progress_records)) * 100
                    completion_rates.append(completion_rate)
            
            # Calculate group statistics
            if completion_rates:
                avg_rate = sum(completion_rates) / len(completion_rates)
                highest_rate = max(completion_rates)
                lowest_rate = min(completion_rates)
            else:
                avg_rate = 0
                highest_rate = 0
                lowest_rate = 0
            
            data.append({
                'Group': group.name,
                'Total Students': len(students),
                'Students with Progress': len(completion_rates),
                'Average Completion %': round(avg_rate, 2),
                'Highest %': round(highest_rate, 2),
                'Lowest %': round(lowest_rate, 2)
            })
    
    df = pd.DataFrame(data)
    
    chart_html = None
    if not df.empty:
        if chart_type == 'bar':
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Average %', x=df['Group'], y=df['Average Completion %'], marker_color='#4A90E2'))
            fig.add_trace(go.Bar(name='Highest %', x=df['Group'], y=df['Highest %'], marker_color='#50C878'))
            fig.update_layout(
                title='Group Performance Comparison',
                xaxis_title='Group',
                yaxis_title='Completion Rate (%)',
                barmode='group',
                template='plotly_white',
                height=500
            )
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
    
    table_html = df.to_html(classes='table table-striped table-hover', index=False) if not df.empty else '<p>No data available</p>'
    stats = {'total_groups': len(groups)}
    
    return {'chart': chart_html, 'table': table_html, 'stats': stats}

def generate_inventory_usage_report(filters, chart_type):
    """Analyze inventory usage"""
    site_id = filters.get('site_id')
    query = InventoryUsage.query
    
    # Apply site filter
    if site_id:
        query = query.filter(InventoryUsage.site_id == site_id)
    
    usage_records = query.all()
    
    data = []
    for usage in usage_records:
        data.append({
            'Item': usage.consumable or 'Unknown',
            'Student': usage.student_name or 'Unknown',
            'Quantity Used': usage.quantity or 0,
            'Date': usage.date_issued.strftime('%Y-%m-%d') if usage.date_issued else 'N/A'
        })
    
    df = pd.DataFrame(data)
    
    stats = {
        'total_records': len(usage_records),
        'total_quantity': df['Quantity Used'].sum() if not df.empty else 0
    }
    
    chart_html = None
    if not df.empty:
        if chart_type == 'bar':
            item_usage = df.groupby('Item')['Quantity Used'].sum().reset_index().sort_values('Quantity Used', ascending=False)
            fig = go.Figure(data=[
                go.Bar(x=item_usage['Item'], y=item_usage['Quantity Used'], 
                      marker_color='#FF6B6B', text=item_usage['Quantity Used'], textposition='auto')
            ])
            fig.update_layout(
                title='Total Usage by Inventory Item',
                xaxis_title='Item',
                yaxis_title='Total Quantity Used',
                template='plotly_white',
                height=500
            )
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
        elif chart_type == 'pie':
            item_usage = df.groupby('Item')['Quantity Used'].sum()
            fig = go.Figure(data=[
                go.Pie(labels=item_usage.index, values=item_usage.values, hole=0.3)
            ])
            fig.update_layout(title='Inventory Usage Distribution', height=500)
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
    
    table_html = df.to_html(classes='table table-striped table-hover', index=False) if not df.empty else '<p>No data available</p>'
    
    return {'chart': chart_html, 'table': table_html, 'stats': stats}

def generate_machine_utilization_report(filters, chart_type):
    """Analyze machine utilization"""
    site_id = filters.get('site_id')
    query = Schedule.query
    
    # Apply site filter
    if site_id:
        query = query.filter(Schedule.site_id == site_id)
    
    # Apply machine filters (multiple machines)
    if filters.get('machine_ids'):
        # Filter by machine names - need to look up machine names from IDs
        machine_names = [Machine.query.get(mid).machine_name for mid in filters['machine_ids'] if Machine.query.get(mid)]
        if machine_names:
            query = query.filter(Schedule.machine_name.in_(machine_names))
    
    schedules = query.all()
    
    data = []
    machine_hours = {}
    for schedule in schedules:
        machine_name = schedule.machine_name or 'Unknown'
        
        # Calculate hours from start_time and end_time
        if schedule.start_time and schedule.end_time:
            duration = (schedule.end_time - schedule.start_time).total_seconds() / 3600
        else:
            duration = 1  # Default to 1 hour
        
        if machine_name in machine_hours:
            machine_hours[machine_name] += duration
        else:
            machine_hours[machine_name] = duration
        
        data.append({
            'Machine': machine_name,
            'Student': schedule.student_name or 'N/A',
            'Group': schedule.group_name or 'N/A',
            'Start Time': schedule.start_time.strftime('%Y-%m-%d %H:%M') if schedule.start_time else 'N/A',
            'End Time': schedule.end_time.strftime('%Y-%m-%d %H:%M') if schedule.end_time else 'N/A',
            'Duration (hrs)': round(duration, 2)
        })
    
    df = pd.DataFrame(data)
    
    stats = {
        'total_bookings': len(schedules),
        'machines_used': len(machine_hours)
    }
    
    chart_html = None
    if machine_hours:
        if chart_type == 'bar':
            machines = list(machine_hours.keys())
            hours = list(machine_hours.values())
            fig = go.Figure(data=[
                go.Bar(x=machines, y=hours, marker_color='#9B59B6', 
                      text=hours, textposition='auto')
            ])
            fig.update_layout(
                title='Machine Utilization (Total Hours)',
                xaxis_title='Machine',
                yaxis_title='Total Hours',
                template='plotly_white',
                height=500
            )
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
        elif chart_type == 'pie':
            fig = go.Figure(data=[
                go.Pie(labels=list(machine_hours.keys()), values=list(machine_hours.values()), hole=0.3)
            ])
            fig.update_layout(title='Machine Usage Distribution', height=500)
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
    
    table_html = df.to_html(classes='table table-striped table-hover', index=False) if not df.empty else '<p>No data available</p>'
    
    return {'chart': chart_html, 'table': table_html, 'stats': stats}

def generate_schedule_analysis_report(filters, chart_type):
    """Analyze schedule patterns"""
    site_id = filters.get('site_id')
    query = Schedule.query
    
    # Apply site filter
    if site_id:
        query = query.filter(Schedule.site_id == site_id)
    
    schedules = query.all()
    
    data = []
    day_counts = {}
    for schedule in schedules:
        # Get day from start_time if available
        day = schedule.start_time.strftime('%A') if schedule.start_time else 'Unknown'
        if day in day_counts:
            day_counts[day] += 1
        else:
            day_counts[day] = 1
        
        data.append({
            'Date': schedule.start_time.strftime('%Y-%m-%d') if schedule.start_time else 'N/A',
            'Day': day,
            'Student': schedule.student_name or 'N/A',
            'Group': schedule.group_name or 'N/A',
            'Machine': schedule.machine_name or 'N/A',
            'Start Time': schedule.start_time.strftime('%H:%M') if schedule.start_time else 'N/A',
            'End Time': schedule.end_time.strftime('%H:%M') if schedule.end_time else 'N/A'
        })
    
    df = pd.DataFrame(data)
    
    stats = {
        'total_schedules': len(schedules),
        'busiest_day': max(day_counts, key=day_counts.get) if day_counts else 'N/A'
    }
    
    chart_html = None
    if day_counts:
        if chart_type == 'bar':
            days = list(day_counts.keys())
            counts = list(day_counts.values())
            fig = go.Figure(data=[
                go.Bar(x=days, y=counts, marker_color='#3498DB', 
                      text=counts, textposition='auto')
            ])
            fig.update_layout(
                title='Schedule Distribution by Day of Week',
                xaxis_title='Day',
                yaxis_title='Number of Schedules',
                template='plotly_white',
                height=500
            )
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
        elif chart_type == 'pie':
            fig = go.Figure(data=[
                go.Pie(labels=list(day_counts.keys()), values=list(day_counts.values()), hole=0.3)
            ])
            fig.update_layout(title='Schedule Distribution', height=500)
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
    
    table_html = df.to_html(classes='table table-striped table-hover', index=False) if not df.empty else '<p>No data available</p>'
    
    return {'chart': chart_html, 'table': table_html, 'stats': stats}

@reports_bp.route('/reports/export_data')
@login_required
def export_report_data():
    """Export report data to Excel"""
    import json
    
    report_type = request.args.get('report_type')
    filters = json.loads(request.args.get('filters', '{}'))
    
    # Generate the report data
    try:
        if report_type == 'student_performance':
            result = generate_student_performance_report(filters, 'bar')
        elif report_type == 'student_progress':
            result = generate_student_progress_report(filters, 'bar')
        elif report_type == 'group_comparison':
            result = generate_group_comparison_report(filters, 'bar')
        elif report_type == 'demographic_analysis':
            result = generate_demographic_analysis_report(filters, 'bar')
        elif report_type == 'completion_rates':
            result = generate_completion_rates_report(filters, 'bar')
        elif report_type == 'attempt_analysis':
            result = generate_attempt_analysis_report(filters, 'bar')
        elif report_type == 'inventory_usage':
            result = generate_inventory_usage_report(filters, 'bar')
        elif report_type == 'inventory_stock':
            result = generate_inventory_stock_report(filters, 'bar')
        elif report_type == 'machine_utilization':
            result = generate_machine_utilization_report(filters, 'bar')
        elif report_type == 'schedule_analysis':
            result = generate_schedule_analysis_report(filters, 'bar')
        elif report_type == 'lecturer_workload':
            result = generate_lecturer_workload_report(filters, 'bar')
        elif report_type == 'custom_field_analysis':
            result = generate_custom_field_analysis_report(filters, 'bar')
        else:
            return jsonify({'success': False, 'error': 'Invalid report type'})
        
        # Extract table data and convert to DataFrame
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(result['table'], 'html.parser')
        table = soup.find('table')
        
        if table:
            df = pd.read_html(str(table))[0]
        else:
            df = pd.DataFrame()
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write data
            if not df.empty:
                df.to_excel(writer, sheet_name='Report Data', index=False)
            
            # Write statistics
            if result.get('stats'):
                stats_df = pd.DataFrame([result['stats']])
                stats_df.to_excel(writer, sheet_name='Statistics', index=False)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{report_type}_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@reports_bp.route('/reports/export', methods=['GET', 'POST'])
@login_required
def export_report():
    # Support both GET (from link) and POST (from form)
    if request.method == 'GET':
        report_type = request.args.get('report_type', 'general')
        # Fallback for GET requests
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df = pd.DataFrame({
                'Message': ['Please use the Export button in the report interface for full data export']
            })
            df.to_excel(writer, sheet_name='Info', index=False)
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'report_{report_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
    
    # POST method - export actual report data
    data = request.get_json()
    report_type = data.get('report_type', 'report')
    report_title = data.get('report_title', 'Report')
    table_html = data.get('table_html', '')
    stats = data.get('stats', {})
    
    try:
        # Parse HTML table to DataFrame
        if table_html and '<table' in table_html:
            # Use pandas to parse HTML table
            dfs = pd.read_html(StringIO(table_html))
            if dfs:
                data_df = dfs[0]
            else:
                data_df = pd.DataFrame()
        else:
            data_df = pd.DataFrame({'Message': ['No data available']})
        
        # Create statistics DataFrame
        if stats:
            stats_df = pd.DataFrame([
                {'Statistic': key.replace('_', ' ').title(), 'Value': value}
                for key, value in stats.items()
            ])
        else:
            stats_df = pd.DataFrame({'Message': ['No statistics available']})
        
        # Create Excel file with multiple sheets
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write report info
            info_df = pd.DataFrame({
                'Report Title': [report_title],
                'Report Type': [report_type],
                'Generated At': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                'Generated By': [current_user.username if current_user else 'Unknown']
            })
            info_df.to_excel(writer, sheet_name='Report Info', index=False)
            
            # Write statistics
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)
            
            # Write data
            if not data_df.empty:
                data_df.to_excel(writer, sheet_name='Data', index=False)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{report_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
    
    except Exception as e:
        # Return error as Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            error_df = pd.DataFrame({
                'Error': [f'Failed to export report: {str(e)}']
            })
            error_df.to_excel(writer, sheet_name='Error', index=False)
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )

def generate_chart(data, config):
    chart_type = config.get('type', 'bar')
    x_field = config.get('x_field')
    y_field = config.get('y_field')
    model_name = config.get('model')
    
    if model_name not in data or data[model_name].empty:
        return None
    
    df = data[model_name]
    
    if chart_type == 'bar':
        fig = go.Figure(data=[
            go.Bar(x=df[x_field], y=df[y_field])
        ])
        fig.update_layout(title=f'{y_field} by {x_field}')
    
    elif chart_type == 'pie':
        value_counts = df[x_field].value_counts()
        fig = go.Figure(data=[
            go.Pie(labels=value_counts.index, values=value_counts.values)
        ])
        fig.update_layout(title=f'Distribution of {x_field}')
    
    elif chart_type == 'line':
        fig = go.Figure(data=[
            go.Scatter(x=df[x_field], y=df[y_field], mode='lines+markers')
        ])
        fig.update_layout(title=f'{y_field} over {x_field}')
    
    elif chart_type == 'scatter':
        fig = go.Figure(data=[
            go.Scatter(x=df[x_field], y=df[y_field], mode='markers')
        ])
        fig.update_layout(title=f'{y_field} vs {x_field}')
    
    elif chart_type == 'histogram':
        fig = go.Figure(data=[
            go.Histogram(x=df[x_field])
        ])
        fig.update_layout(title=f'Distribution of {x_field}')
    
    else:
        return None
    
    fig.update_layout(height=500)
    return pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})

# NEW COMPREHENSIVE REPORT FUNCTIONS

def generate_student_progress_report(filters, chart_type):
    """Track individual student progress through modules and mini-tasks"""
    query = Student.query.join(Student.group, isouter=True)
    
    if filters.get('group_id'):
        query = query.filter(Student.group_id == filters['group_id'])
    
    students = query.all()
    
    data = []
    for student in students:
        progress_records = StudentMiniTaskProgress.query.filter_by(student_id=student.id).all()
        
        total_tasks = len(progress_records)
        passed_tasks = sum(1 for p in progress_records if p.attempt_1 == 'Pass' or p.attempt_2 == 'Pass' or p.attempt_3 == 'Pass')
        completion_rate = (passed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        data.append({
            'Student': student.student_name,
            'Group': student.group.name if student.group else 'N/A',
            'Total Tasks': total_tasks,
            'Passed Tasks': passed_tasks,
            'Completion Rate (%)': round(completion_rate, 1)
        })
    
    df = pd.DataFrame(data)
    
    stats = {
        'total_students': len(students),
        'avg_completion_rate': round(df['Completion Rate (%)'].mean(), 1) if not df.empty else 0,
        'total_tasks_completed': int(df['Passed Tasks'].sum()) if not df.empty else 0
    }
    
    chart_html = None
    if not df.empty:
        if chart_type == 'bar':
            fig = go.Figure(data=[
                go.Bar(x=df['Student'], y=df['Completion Rate (%)'], marker_color='#50C878', 
                      text=df['Completion Rate (%)'], textposition='auto')
            ])
            fig.update_layout(
                title='Student Progress - Completion Rates',
                xaxis_title='Student',
                yaxis_title='Completion Rate (%)',
                template='plotly_white',
                height=500
            )
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
    
    table_html = df.to_html(classes='table table-striped table-hover', index=False) if not df.empty else '<p>No data available</p>'
    
    return {'chart': chart_html, 'table': table_html, 'stats': stats}

def generate_demographic_analysis_report(filters, chart_type):
    """Analyze student demographics using dynamic fields"""
    site_id = filters.get('site_id')
    query = Student.query
    
    # Apply site filter
    if site_id:
        query = query.filter(Student.site_id == site_id)
    
    # Apply group filter (multiple groups)
    if filters.get('group_ids'):
        query = query.filter(Student.group_id.in_(filters['group_ids']))
    elif filters.get('group_id'):
        query = query.filter(Student.group_id == filters['group_id'])
    
    students = query.all()
    dynamic_fields = DynamicField.query.filter_by(model_name='Student').all()
    
    # Get demographic data
    demographics = {}
    for field in dynamic_fields:
        field_values = []
        for student in students:
            field_value = DynamicFieldValue.query.filter_by(
                field_id=field.id,
                record_id=student.id
            ).first()
            if field_value and field_value.value:
                field_values.append(field_value.value)
        
        if field_values:
            demographics[field.field_name] = Counter(field_values)
    
    # Create data for the first demographic field
    data = []
    field_name = 'No Fields'
    if demographics:
        first_field = list(demographics.keys())[0]
        field_name = first_field.replace('_', ' ').title()
        for value, count in demographics[first_field].items():
            data.append({
                'Category': value,
                'Count': count,
                'Percentage': round((count / len(students)) * 100, 1) if students else 0
            })
    
    df = pd.DataFrame(data)
    
    stats = {
        'total_students': len(students),
        'categories_analyzed': len(demographics),
        'field_analyzed': field_name
    }
    
    chart_html = None
    if not df.empty:
        if chart_type == 'pie':
            fig = go.Figure(data=[
                go.Pie(labels=df['Category'], values=df['Count'], hole=0.3)
            ])
            fig.update_layout(title=f'{field_name} Distribution', height=500)
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
        elif chart_type == 'bar':
            fig = go.Figure(data=[
                go.Bar(x=df['Category'], y=df['Count'], marker_color='#FF6B6B',
                      text=df['Count'], textposition='auto')
            ])
            fig.update_layout(
                title=f'{field_name} Distribution',
                xaxis_title=field_name,
                yaxis_title='Number of Students',
                template='plotly_white',
                height=500
            )
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
    
    table_html = df.to_html(classes='table table-striped table-hover', index=False) if not df.empty else '<p>No data available</p>'
    
    return {'chart': chart_html, 'table': table_html, 'stats': stats}

def generate_completion_rates_report(filters, chart_type):
    """Analyze module and mini-task completion rates"""
    site_id = filters.get('site_id')
    query = Module.query
    
    # Apply site filter
    if site_id:
        query = query.filter(Module.site_id == site_id)
    
    modules = query.all()
    
    data = []
    for module in modules:
        mini_tasks = MiniTask.query.filter_by(module_id=module.id).all()
        total_students = Student.query.count()
        
        for task in mini_tasks:
            progress_records = StudentMiniTaskProgress.query.filter_by(mini_task_id=task.id).all()
            
            completed = sum(1 for p in progress_records 
                          if p.attempt_1 == 'Pass' or p.attempt_2 == 'Pass' or p.attempt_3 == 'Pass')
            completion_rate = (completed / len(progress_records) * 100) if progress_records else 0
            
            data.append({
                'Module': module.name,
                'Task': task.title,
                'Students Completed': completed,
                'Total Students': len(progress_records),
                'Completion Rate (%)': round(completion_rate, 1)
            })
    
    df = pd.DataFrame(data)
    
    stats = {
        'total_modules': len(modules),
        'avg_completion_rate': round(df['Completion Rate (%)'].mean(), 1) if not df.empty else 0
    }
    
    chart_html = None
    if not df.empty:
        if chart_type == 'bar':
            # Group by module
            module_completion = df.groupby('Module')['Completion Rate (%)'].mean().reset_index()
            fig = go.Figure(data=[
                go.Bar(x=module_completion['Module'], y=module_completion['Completion Rate (%)'],
                      marker_color='#4A90E2', text=module_completion['Completion Rate (%)'].round(1), 
                      textposition='auto')
            ])
            fig.update_layout(
                title='Module Completion Rates',
                xaxis_title='Module',
                yaxis_title='Average Completion Rate (%)',
                template='plotly_white',
                height=500
            )
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
    
    table_html = df.to_html(classes='table table-striped table-hover', index=False) if not df.empty else '<p>No data available</p>'
    
    return {'chart': chart_html, 'table': table_html, 'stats': stats}

def generate_attempt_analysis_report(filters, chart_type):
    """Analyze assessment attempts and success rates"""
    progress_records = StudentMiniTaskProgress.query.all()
    
    data = []
    for record in progress_records:
        attempts = []
        if record.attempt_1: attempts.append(('Attempt 1', record.attempt_1))
        if record.attempt_2: attempts.append(('Attempt 2', record.attempt_2))
        if record.attempt_3: attempts.append(('Attempt 3', record.attempt_3))
        
        passed = any(attempt[1] == 'Pass' for attempt in attempts)
        pass_attempt = next((attempt[0] for attempt in attempts if attempt[1] == 'Pass'), 'Not Passed')
        
        data.append({
            'Student': record.student.student_name if record.student else 'N/A',
            'Task': record.mini_task.title if record.mini_task else 'N/A',
            'Total Attempts': len(attempts),
            'Pass Attempt': pass_attempt,
            'Status': 'Passed' if passed else 'Failed'
        })
    
    df = pd.DataFrame(data)
    
    # Calculate statistics
    pass_on_first = len(df[df['Pass Attempt'] == 'Attempt 1'])
    pass_on_second = len(df[df['Pass Attempt'] == 'Attempt 2'])
    pass_on_third = len(df[df['Pass Attempt'] == 'Attempt 3'])
    not_passed = len(df[df['Pass Attempt'] == 'Not Passed'])
    
    stats = {
        'total_assessments': len(df),
        'passed_first_attempt': pass_on_first,
        'passed_second_attempt': pass_on_second,
        'passed_third_attempt': pass_on_third,
        'not_passed': not_passed
    }
    
    chart_html = None
    if not df.empty:
        if chart_type == 'pie':
            labels = ['Pass - 1st Attempt', 'Pass - 2nd Attempt', 'Pass - 3rd Attempt', 'Not Passed']
            values = [pass_on_first, pass_on_second, pass_on_third, not_passed]
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3)])
            fig.update_layout(title='Assessment Attempts Distribution', height=500)
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
    
    table_html = df.to_html(classes='table table-striped table-hover', index=False) if not df.empty else '<p>No data available</p>'
    
    return {'chart': chart_html, 'table': table_html, 'stats': stats}

def generate_inventory_stock_report(filters, chart_type):
    """Current inventory stock levels and alerts"""
    inventory_items = Inventory.query.all()
    
    data = []
    low_stock_count = 0
    for item in inventory_items:
        total_used = db.session.query(func.sum(InventoryUsage.quantity)).filter_by(inventory_id=item.id).scalar() or 0
        current_stock = (item.quantity or 0) - total_used
        
        status = 'Critical' if current_stock < 10 else ('Low' if current_stock < 50 else 'Good')
        if status in ['Critical', 'Low']:
            low_stock_count += 1
        
        data.append({
            'Item': item.item_name,
            'Initial Quantity': item.quantity or 0,
            'Total Used': int(total_used),
            'Current Stock': int(current_stock),
            'Status': status
        })
    
    df = pd.DataFrame(data)
    
    stats = {
        'total_items': len(inventory_items),
        'low_stock_items': low_stock_count
    }
    
    chart_html = None
    if not df.empty:
        if chart_type == 'bar':
            fig = go.Figure(data=[
                go.Bar(name='Initial', x=df['Item'], y=df['Initial Quantity'], marker_color='#4A90E2'),
                go.Bar(name='Current', x=df['Item'], y=df['Current Stock'], marker_color='#50C878')
            ])
            fig.update_layout(
                title='Inventory Stock Levels',
                xaxis_title='Item',
                yaxis_title='Quantity',
                barmode='group',
                template='plotly_white',
                height=500
            )
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
    
    table_html = df.to_html(classes='table table-striped table-hover', index=False) if not df.empty else '<p>No data available</p>'
    
    return {'chart': chart_html, 'table': table_html, 'stats': stats}

def generate_lecturer_workload_report(filters, chart_type):
    """Analyze lecturer workload and schedule assignments"""
    site_id = filters.get('site_id')
    query = Lecturer.query
    
    # Apply site filter
    if site_id:
        query = query.filter(Lecturer.site_id == site_id)
    
    lecturers = query.all()
    
    data = []
    for lecturer in lecturers:
        # Count schedules assigned to this lecturer (assuming lecturer might be in notes or we use a different approach)
        # Since there's no direct lecturer_id in schedules, we'll count based on available data
        # For now, just show lecturer info without schedule counts
        data.append({
            'Lecturer': lecturer.name,
            'Phone': lecturer.phone_number or 'N/A',
            'Email': lecturer.email or 'N/A',
            'Notes': lecturer.notes or 'N/A'
        })
    
    df = pd.DataFrame(data)
    
    stats = {
        'total_lecturers': len(lecturers)
    }
    
    chart_html = None
    if not df.empty:
        if chart_type == 'bar':
            # Create a simple count chart
            lecturer_counts = pd.DataFrame({'Lecturer': df['Lecturer'], 'Count': 1})
            fig = go.Figure(data=[
                go.Bar(x=lecturer_counts['Lecturer'], y=lecturer_counts['Count'], marker_color='#9B59B6',
                      text=lecturer_counts['Count'], textposition='auto')
            ])
            fig.update_layout(
                title='Lecturer Overview',
                xaxis_title='Lecturer',
                yaxis_title='Active Status',
                template='plotly_white',
                height=500
            )
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
    
    table_html = df.to_html(classes='table table-striped table-hover', index=False) if not df.empty else '<p>No data available</p>'
    
    return {'chart': chart_html, 'table': table_html, 'stats': stats}

def generate_custom_field_analysis_report(filters, chart_type):
    """Analyze custom fields across students"""
    dynamic_fields = DynamicField.query.filter_by(model_name='Student').all()
    students = Student.query.all()
    
    if not dynamic_fields:
        return {
            'chart': None,
            'table': '<p>No custom fields defined</p>',
            'stats': {'total_fields': 0}
        }
    
    # Analyze first custom field
    field = dynamic_fields[0]
    field_distribution = defaultdict(int)
    
    for student in students:
        field_value = DynamicFieldValue.query.filter_by(
            field_id=field.id,
            record_id=student.id
        ).first()
        
        if field_value and field_value.value:
            field_distribution[field_value.value] += 1
    
    data = [{
        'Value': value,
        'Count': count,
        'Percentage': round((count / len(students)) * 100, 1) if students else 0
    } for value, count in field_distribution.items()]
    
    df = pd.DataFrame(data)
    
    stats = {
        'total_custom_fields': len(dynamic_fields),
        'field_analyzed': field.field_name,
        'unique_values': len(field_distribution)
    }
    
    chart_html = None
    if not df.empty:
        if chart_type == 'pie':
            fig = go.Figure(data=[
                go.Pie(labels=df['Value'], values=df['Count'], hole=0.3)
            ])
            fig.update_layout(title=f'Distribution of {field.field_name.replace("_", " ").title()}', height=500)
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
    
    table_html = df.to_html(classes='table table-striped table-hover', index=False) if not df.empty else '<p>No data available</p>'
    
    return {'chart': chart_html, 'table': table_html, 'stats': stats}

def generate_contingency_table_report(filters, chart_type):
    """Generate contingency table for cross-analysis"""
    site_id = filters.get('site_id')
    
    # Get students with their groups and module enrollments
    student_query = Student.query
    group_query = Group.query
    module_query = Module.query
    
    # Apply site filter
    if site_id:
        student_query = student_query.filter(Student.site_id == site_id)
        group_query = group_query.filter(Group.site_id == site_id)
        module_query = module_query.filter(Module.site_id == site_id)
    
    students = student_query.all()
    
    # Create contingency table: Groups vs Module Completion
    contingency_data = {}
    groups = group_query.all()
    modules = module_query.all()
    
    for group in groups:
        contingency_data[group.name] = {}
        group_students = Student.query.filter_by(group_id=group.id).all()
        
        for module in modules:
            # Count students in this group enrolled in this module
            enrolled_count = sum(1 for s in group_students if module in s.enrolled_modules)
            contingency_data[group.name][module.name] = enrolled_count
    
    # Convert to DataFrame
    df = pd.DataFrame(contingency_data).T
    df = df.fillna(0).astype(int)
    
    # Add row and column totals
    df['Total'] = df.sum(axis=1)
    df.loc['Total'] = df.sum(axis=0)
    
    stats = {
        'total_groups': len(groups),
        'total_modules': len(modules),
        'total_students': len(students)
    }
    
    # Create heatmap visualization
    chart_html = None
    if not df.empty and chart_type == 'bar':
        # Create a heatmap using plotly
        fig = go.Figure(data=go.Heatmap(
            z=df.iloc[:-1, :-1].values,  # Exclude totals
            x=df.columns[:-1],
            y=df.index[:-1],
            colorscale='Blues',
            text=df.iloc[:-1, :-1].values,
            texttemplate='%{text}',
            textfont={"size": 12},
            hoverongaps=False
        ))
        fig.update_layout(
            title='Student Enrollment Contingency Table: Groups vs Modules',
            xaxis_title='Modules',
            yaxis_title='Groups',
            template='plotly_white',
            height=600
        )
        chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
    
    table_html = df.to_html(classes='table table-striped table-hover table-bordered') if not df.empty else '<p>No data available</p>'
    
    return {'chart': chart_html, 'table': table_html, 'stats': stats}

def generate_cross_tabulation_report(filters, chart_type):
    """Generate cross-tabulation report for module status by group"""
    site_id = filters.get('site_id')
    query = Student.query
    
    # Apply site filter
    if site_id:
        query = query.filter(Student.site_id == site_id)
    
    students = query.all()
    
    # Cross-tabulation: Group vs Module Progress Status
    data = []
    for student in students:
        for module in student.enrolled_modules:
            # Get module progress
            progress_records = StudentMiniTaskProgress.query.join(MiniTask).filter(
                StudentMiniTaskProgress.student_id == student.id,
                MiniTask.module_id == module.id
            ).all()
            
            # Determine status
            if progress_records:
                total_tasks = len(progress_records)
                completed = sum(1 for p in progress_records 
                              if any([p.attempt_1 == 'Pass', p.attempt_2 == 'Pass', p.attempt_3 == 'Pass']))
                if completed == total_tasks and total_tasks > 0:
                    status = 'Completed'
                elif completed > 0:
                    status = 'In Progress'
                else:
                    status = 'Not Started'
            else:
                status = 'Not Started'
            
            data.append({
                'Student': student.student_name,
                'Group': student.group.name if student.group else 'No Group',
                'Module': module.name,
                'Status': status
            })
    
    df = pd.DataFrame(data)
    
    # Create crosstab
    if not df.empty:
        crosstab = pd.crosstab(
            index=df['Group'],
            columns=df['Status'],
            margins=True,
            margins_name='Total'
        )
        
        stats = {
            'total_enrollments': len(data),
            'unique_groups': df['Group'].nunique(),
            'unique_modules': df['Module'].nunique()
        }
        
        # Create stacked bar chart
        chart_html = None
        if chart_type == 'bar':
            crosstab_no_total = crosstab.iloc[:-1, :-1]  # Remove total row and column
            fig = go.Figure()
            
            for col in crosstab_no_total.columns:
                fig.add_trace(go.Bar(
                    name=col,
                    x=crosstab_no_total.index,
                    y=crosstab_no_total[col],
                    text=crosstab_no_total[col],
                    textposition='auto'
                ))
            
            fig.update_layout(
                title='Module Status Distribution by Group',
                xaxis_title='Group',
                yaxis_title='Count',
                barmode='stack',
                template='plotly_white',
                height=500
            )
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
        
        table_html = crosstab.to_html(classes='table table-striped table-hover table-bordered')
    else:
        crosstab = pd.DataFrame()
        stats = {'total_enrollments': 0}
        table_html = '<p>No enrollment data available</p>'
        chart_html = None
    
    return {'chart': chart_html, 'table': table_html, 'stats': stats}

def generate_custom_report(filters, chart_type):
    """Generate a customizable report based on user-selected fields"""
    # This is a flexible report that can be extended based on filters
    
    # Get group_by and measure from filters
    group_by_field = filters.get('custom_group_by', 'group')
    measure = filters.get('custom_measure', 'pass_rate')
    
    # Get all available data
    query = Student.query.join(Student.group, isouter=True)
    
    # Apply demographic filters
    if filters.get('gender'):
        # Look for gender in dynamic fields
        gender_field = DynamicField.query.filter_by(model_name='Student', field_name='gender').first()
        if gender_field:
            query = query.join(DynamicFieldValue, 
                             (DynamicFieldValue.record_id == Student.id) & 
                             (DynamicFieldValue.field_id == gender_field.id) &
                             (DynamicFieldValue.value == filters['gender']))
    
    if filters.get('race'):
        # Look for race/population_group in dynamic fields  
        race_field = DynamicField.query.filter_by(model_name='Student').filter(
            (DynamicField.field_name == 'race') | 
            (DynamicField.field_name == 'population_group')
        ).first()
        if race_field:
            query = query.join(DynamicFieldValue,
                             (DynamicFieldValue.record_id == Student.id) &
                             (DynamicFieldValue.field_id == race_field.id) &
                             (DynamicFieldValue.value == filters['race']))
    
    if filters.get('group_id'):
        query = query.filter(Student.group_id == filters['group_id'])
    
    students = query.all()
    modules = Module.query.all()
    groups = Group.query.all()
    
    # Build custom data based on what's requested
    data = []
    for student in students:
        row = {
            'Student Name': student.student_name,
            'Student Number': student.student_number or 'N/A',
            'Group': student.group.name if student.group else 'N/A',
            'Enrolled Modules': len(student.enrolled_modules),
            'Total Progress Records': len(student.progress)
        }
        
        # Calculate completion rate
        if student.progress:
            completed = sum(1 for p in student.progress 
                          if any([p.attempt_1 == 'Pass', p.attempt_2 == 'Pass', p.attempt_3 == 'Pass']))
            row['Completion Rate (%)'] = round((completed / len(student.progress)) * 100, 1) if student.progress else 0
            row['Pass Rate (%)'] = row['Completion Rate (%)']  # Same for now
        else:
            row['Completion Rate (%)'] = 0
            row['Pass Rate (%)'] = 0
        
        # Get dynamic fields including demographics
        dynamic_fields = DynamicField.query.filter_by(model_name='Student').all()
        for field in dynamic_fields:
            field_value = DynamicFieldValue.query.filter_by(
                field_id=field.id,
                record_id=student.id
            ).first()
            row[field.field_name.replace('_', ' ').title()] = field_value.value if field_value else 'N/A'
            # Store raw field name too
            row[field.field_name] = field_value.value if field_value else 'N/A'
        
        data.append(row)
    
    df = pd.DataFrame(data)
    
    stats = {
        'total_students': len(students),
        'total_modules': len(modules),
        'total_groups': len(groups),
        'avg_enrollment': round(df['Enrolled Modules'].mean(), 1) if not df.empty else 0,
        'avg_completion_rate': round(df['Completion Rate (%)'].mean(), 1) if not df.empty else 0
    }
    
    # Create visualization based on group_by field
    chart_html = None
    if not df.empty:
        # Determine which field to group by
        if group_by_field == 'gender':
            group_col = 'gender' if 'gender' in df.columns else 'Gender'
        elif group_by_field == 'race':
            group_col = 'race' if 'race' in df.columns else 'population_group' if 'population_group' in df.columns else 'Population Group'
        elif group_by_field == 'age_range':
            group_col = 'age_range' if 'age_range' in df.columns else 'Age Range'
        elif group_by_field == 'group':
            group_col = 'Group'
        else:
            group_col = group_by_field
        
        # Ensure column exists
        if group_col not in df.columns:
            # Try title case version
            group_col_title = group_col.replace('_', ' ').title()
            if group_col_title in df.columns:
                group_col = group_col_title
            else:
                group_col = 'Group'  # Default fallback
        
        # Determine which measure to calculate
        if measure == 'pass_rate':
            measure_col = 'Pass Rate (%)'
        elif measure == 'completion_rate':
            measure_col = 'Completion Rate (%)'
        elif measure == 'enrollment_count':
            measure_col = 'Enrolled Modules'
        else:
            measure_col = 'Pass Rate (%)'
        
        # Group and aggregate data
        grouped = df.groupby(group_col)[measure_col].mean().reset_index()
        grouped = grouped.sort_values(measure_col, ascending=False)
        
        if chart_type == 'bar':
            fig = go.Figure(data=[
                go.Bar(
                    x=grouped[group_col],
                    y=grouped[measure_col],
                    marker_color='#4A90E2',
                    text=grouped[measure_col].round(1),
                    textposition='auto'
                )
            ])
            fig.update_layout(
                title=f'{measure_col} by {group_col}',
                xaxis_title=group_col,
                yaxis_title=measure_col,
                template='plotly_white',
                height=500
            )
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
        elif chart_type == 'pie':
            # For pie chart, show distribution counts
            dist = df[group_col].value_counts()
            fig = go.Figure(data=[go.Pie(labels=dist.index, values=dist.values, hole=0.3)])
            fig.update_layout(
                title=f'Distribution by {group_col}',
                height=500
            )
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
        elif chart_type == 'line':
            # Line chart for trends
            fig = go.Figure(data=[
                go.Scatter(
                    x=grouped[group_col],
                    y=grouped[measure_col],
                    mode='lines+markers',
                    marker=dict(size=10, color='#4A90E2'),
                    line=dict(width=2, color='#4A90E2')
                )
            ])
            fig.update_layout(
                title=f'{measure_col} Trend by {group_col}',
                xaxis_title=group_col,
                yaxis_title=measure_col,
                template='plotly_white',
                height=500
            )
            chart_html = pio.to_html(fig, include_plotlyjs='cdn', full_html=False, config={'responsive': True})
    
    table_html = df.to_html(classes='table table-striped table-hover', index=False) if not df.empty else '<p>No data available</p>'
    
    return {'chart': chart_html, 'table': table_html, 'stats': stats}

@reports_bp.route('/reports/quick_stats')
@login_required
@require_site_access
def quick_stats():
    """Get quick statistics for the dashboard"""
    site_id = get_active_site_id()
    
    from app import apply_site_filter
    
    total_students = apply_site_filter(Student.query, Student).count()
    total_groups = apply_site_filter(Group.query, Group).count()
    total_modules = apply_site_filter(Module.query, Module).count()
    
    return jsonify({
        'success': True,
        'total_students': total_students,
        'total_groups': total_groups,
        'total_modules': total_modules
    })
