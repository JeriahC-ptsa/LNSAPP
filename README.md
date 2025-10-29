# LnSapp - Learning Management System

Multi-tenant learning management system designed for educational institutions and training centers.

## Features

- **Multi-site Management**: Support for multiple campuses/sites with data isolation
- **Student Progress Tracking**: Comprehensive tracking of student progress across modules and mini-tasks
- **Module & Inventory Management**: Manage training modules, machines, and inventory
- **Advanced Reporting**: Interactive reports with Plotly visualizations
- **Role-Based Access Control**: Super Admin, Admin, Lecturer, and Student roles
- **Dynamic Fields**: Extensible field system for custom data requirements
- **Schedule Management**: Lecturer and class scheduling
- **Excel Import/Export**: Bulk data operations via Excel files

## Technology Stack

- **Backend**: Flask 2.3.2, SQLAlchemy ORM
- **Database**: PostgreSQL (production), SQLite (development)
- **Visualizations**: Plotly, Matplotlib, Seaborn
- **Data Processing**: Pandas
- **Server**: Gunicorn

## Deployment

This application is ready for deployment on Render.com. See deployment documentation for details.

### Quick Start (Local Development)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables** (create `.env` file):
   ```
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///database.db
   FLASK_ENV=development
   ```

3. **Initialize database**:
   ```bash
   flask db upgrade
   ```

4. **Run application**:
   ```bash
   python run.py
   ```

5. **Access**: http://localhost:5000

## Deployment to Render

1. Push to GitHub
2. Connect repository to Render
3. Create PostgreSQL database
4. Configure environment variables
5. Deploy!

See `RENDER_DEPLOYMENT_REPORT.md` for detailed instructions.

## Project Structure

- `app.py` - Main application file
- `models.py` - Database models
- `auth_models.py` - Authentication models
- `reports.py` - Reporting functionality
- `templates/` - Jinja2 templates
- `static/` - CSS, JavaScript, images
- `migrations/` - Database migration files

## License

Proprietary - PTSA Educational Systems

## Support

For support and questions, contact your system administrator.
