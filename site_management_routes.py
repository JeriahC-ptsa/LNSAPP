"""
Site Management Routes
======================
Add these routes to your app.py file for complete site management functionality.

Copy the entire content below and paste it into app.py after the site switching routes.
"""

SITE_MANAGEMENT_ROUTES = """
##############################################
# SITE MANAGEMENT CRUD
##############################################
@app.route('/sites')
@login_required
def list_sites():
    '''List all sites - Admin only'''
    if not current_user.is_super_admin():
        flash('Only administrators can manage sites.', 'danger')
        return redirect(url_for('index'))
    
    sites = Site.query.order_by(Site.name).all()
    
    # Get user count for each site
    for site in sites:
        site.user_count = len(site.users)
        site.student_count = Student.query.filter_by(site_id=site.id).count()
        site.machine_count = Machine.query.filter_by(site_id=site.id).count()
    
    return render_template('sites/list.html', sites=sites)

@app.route('/sites/add', methods=['GET', 'POST'])
@login_required
def add_site():
    '''Create a new site - Admin only'''
    if not current_user.is_super_admin():
        flash('Only administrators can create sites.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper()
        location = request.form.get('location', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        is_active = request.form.get('is_active') == 'on'
        
        # Validate required fields
        if not name or not code:
            flash('Site name and code are required.', 'danger')
            return redirect(url_for('add_site'))
        
        # Check for duplicate code
        existing = Site.query.filter_by(code=code).first()
        if existing:
            flash(f'Site code "{code}" already exists.', 'danger')
            return redirect(url_for('add_site'))
        
        # Create new site
        new_site = Site(
            name=name,
            code=code,
            location=location,
            address=address,
            phone=phone,
            email=email,
            is_active=is_active,
            created_date=datetime.utcnow()
        )
        
        db.session.add(new_site)
        db.session.commit()
        
        flash(f'Site "{name}" created successfully!', 'success')
        return redirect(url_for('list_sites'))
    
    return render_template('sites/add.html')

@app.route('/sites/edit/<int:site_id>', methods=['GET', 'POST'])
@login_required
def edit_site(site_id):
    '''Edit a site - Admin only'''
    if not current_user.is_super_admin():
        flash('Only administrators can edit sites.', 'danger')
        return redirect(url_for('index'))
    
    site = Site.query.get_or_404(site_id)
    
    if request.method == 'POST':
        site.name = request.form.get('name', '').strip()
        site.code = request.form.get('code', '').strip().upper()
        site.location = request.form.get('location', '').strip()
        site.address = request.form.get('address', '').strip()
        site.phone = request.form.get('phone', '').strip()
        site.email = request.form.get('email', '').strip()
        site.is_active = request.form.get('is_active') == 'on'
        
        # Validate required fields
        if not site.name or not site.code:
            flash('Site name and code are required.', 'danger')
            return redirect(url_for('edit_site', site_id=site_id))
        
        # Check for duplicate code (excluding current site)
        existing = Site.query.filter(Site.code == site.code, Site.id != site_id).first()
        if existing:
            flash(f'Site code "{site.code}" already exists.', 'danger')
            return redirect(url_for('edit_site', site_id=site_id))
        
        db.session.commit()
        flash(f'Site "{site.name}" updated successfully!', 'success')
        return redirect(url_for('list_sites'))
    
    return render_template('sites/edit.html', site=site)

@app.route('/sites/delete/<int:site_id>', methods=['POST'])
@login_required
def delete_site(site_id):
    '''Delete a site - Admin only'''
    if not current_user.is_super_admin():
        flash('Only administrators can delete sites.', 'danger')
        return redirect(url_for('index'))
    
    site = Site.query.get_or_404(site_id)
    
    # Check if site has data
    student_count = Student.query.filter_by(site_id=site_id).count()
    machine_count = Machine.query.filter_by(site_id=site_id).count()
    
    if student_count > 0 or machine_count > 0:
        flash(f'Cannot delete site "{site.name}" because it has {student_count} students and {machine_count} machines. Please reassign or delete them first.', 'danger')
        return redirect(url_for('list_sites'))
    
    site_name = site.name
    db.session.delete(site)
    db.session.commit()
    
    flash(f'Site "{site_name}" deleted successfully!', 'success')
    return redirect(url_for('list_sites'))

@app.route('/sites/<int:site_id>/users')
@login_required
def site_users(site_id):
    '''Manage users for a site - Admin only'''
    if not current_user.is_super_admin():
        flash('Only administrators can manage site users.', 'danger')
        return redirect(url_for('index'))
    
    site = Site.query.get_or_404(site_id)
    all_users = User.query.order_by(User.username).all()
    
    # Get user-site associations with manager status
    from sqlalchemy import and_
    from auth_models import user_sites
    
    site_user_data = []
    for user in all_users:
        has_access = site in user.sites
        is_manager = False
        
        if has_access:
            # Check if user is manager at this site
            result = db.session.execute(
                user_sites.select().where(
                    and_(
                        user_sites.c.user_id == user.id,
                        user_sites.c.site_id == site_id
                    )
                )
            ).fetchone()
            is_manager = result.is_manager if result else False
        
        site_user_data.append({
            'user': user,
            'has_access': has_access,
            'is_manager': is_manager
        })
    
    return render_template('sites/users.html', site=site, site_user_data=site_user_data)

@app.route('/sites/<int:site_id>/assign_user/<int:user_id>', methods=['POST'])
@login_required
def assign_user_to_site(site_id, user_id):
    '''Assign a user to a site - Admin only'''
    if not current_user.is_super_admin():
        flash('Only administrators can assign users to sites.', 'danger')
        return redirect(url_for('index'))
    
    site = Site.query.get_or_404(site_id)
    user = User.query.get_or_404(user_id)
    is_manager = request.form.get('is_manager') == 'on'
    
    if site not in user.sites:
        user.sites.append(site)
        db.session.commit()
    
    # Update manager status
    from auth_models import user_sites
    from sqlalchemy import and_
    
    db.session.execute(
        user_sites.update().where(
            and_(
                user_sites.c.user_id == user_id,
                user_sites.c.site_id == site_id
            )
        ).values(is_manager=is_manager)
    )
    db.session.commit()
    
    flash(f'User "{user.username}" assigned to site "{site.name}"' + (' as manager' if is_manager else '') + '.', 'success')
    return redirect(url_for('site_users', site_id=site_id))

@app.route('/sites/<int:site_id>/remove_user/<int:user_id>', methods=['POST'])
@login_required
def remove_user_from_site(site_id, user_id):
    '''Remove a user from a site - Admin only'''
    if not current_user.is_super_admin():
        flash('Only administrators can remove users from sites.', 'danger')
        return redirect(url_for('index'))
    
    site = Site.query.get_or_404(site_id)
    user = User.query.get_or_404(user_id)
    
    if site in user.sites:
        user.sites.remove(site)
        db.session.commit()
        flash(f'User "{user.username}" removed from site "{site.name}".', 'success')
    else:
        flash(f'User "{user.username}" does not have access to site "{site.name}".', 'warning')
    
    return redirect(url_for('site_users', site_id=site_id))
"""

print("="*80)
print("SITE MANAGEMENT ROUTES")
print("="*80)
print("\nCopy the code below and add it to your app.py file:")
print("\n" + SITE_MANAGEMENT_ROUTES)
print("\n" + "="*80)
print("After adding these routes, you'll need to create the template files:")
print("  - templates/sites/list.html")
print("  - templates/sites/add.html")
print("  - templates/sites/edit.html")
print("  - templates/sites/users.html")
print("="*80)
