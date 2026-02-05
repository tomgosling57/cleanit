from app_factory import create_app
from database import get_db
from services.job_service import JobService

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    # Auto push past uncompleted jobs to current time on startup to prevent stale jobs
    JobService(get_db()).push_uncompleted_jobs_to_next_day()
    