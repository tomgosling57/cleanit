import os
from zoneinfo import ZoneInfo
from config import Config
from database import User, init_db
from database import Team, Property, Job, Assignment, Media, PropertyMedia, JobMedia
from datetime import date, datetime, time, timedelta

from utils.timezone import from_app_tz, get_app_timezone, today_in_app_tz, utc_now
from utils.test_data import JOB_TEMPLATES, PROPERTY_DATA, TEAM_DATA, USER_DATA, get_job_data_by_id


def populate_database(database_uri=None, force=True, Session=None):
    """This function populates the database with dummy data for testing purposes.
    
    Args:
        database_uri (str): The database URI where the dummy data will be inserted.
        force (bool): If True, forces re-population even if data exists. Defaults to True.
        Session: An existing SQLAlchemy session factory. If None, a new one will be created.
    """
    if Session is None:    
        if "sqlite:///" in database_uri:
            database_path = database_uri.replace("sqlite:///", "")
            database_dir = os.path.dirname(database_path)
            if not os.path.exists(database_dir):
                os.makedirs(database_dir)

        Session = init_db(database_uri)
        if not force and Session().query(User).filter_by(role='admin').first():
            print("Database already populated. Exiting.")
        return
    insert_dummy_data(Session)
    print("Database populated with dummy data.")

def create_initial_users(session):
    """
    Creates a set of deterministic initial users (admin, supervisor, user)
    and clears any existing users to ensure a clean state.

    Args:
        session: The SQLAlchemy session.

    Returns:
        tuple: A tuple containing the created admin, supervisor, and user User objects.
    """
    session.query(User).delete()
    session.commit()
    users = {}
    for user_key, user_data in USER_DATA.items():
        user = User(id=user_data['id'], first_name=user_data['first_name'], last_name=user_data['last_name'],
                    email=user_data['email'], phone=user_data.get('phone'), role=user_data['role'])
        user.set_password(user_data['password'])
        session.add(user)
        users[user_key] = user
    session.commit()
    return users['admin'], users['supervisor'], users['user'], users['team_leader']

def _create_team(session, team_name, team_leader_id=None, members=None, team_id=None):
    """
    Helper function to create or update a team with deterministic data.

    Args:
        session: The SQLAlchemy session.
        team_name (str): The name of the team.
        team_leader_id (int): The ID of the team leader.
        members (list, optional): A list of User objects to assign to the team. Defaults to None.
        team_id (int, optional): The explicit ID for the team. If None, SQLAlchemy assigns one.

    Returns:
        Team: The created or updated Team object.
    """
    team = session.query(Team).filter_by(name=team_name).first()
    if team:
        team.team_leader_id = team_leader_id
    else:
        team = Team(id=team_id, name=team_name, team_leader_id=team_leader_id)
        session.add(team)
    session.commit()

    if members:
        for member in members:
            member.team_id = team.id
        session.commit()
    return team

def create_initial_teams(session, admin, supervisor_user, user_user, team_leader):
    """
    Creates a set of deterministic initial teams and clears any existing teams
    to ensure a clean state.

    Args:
        session: The SQLAlchemy session.
        admin (User): The admin User object.
        supervisor_user (User): The supervisor User object.
        user (User): The user User object.
        team_leader (User): The team leader User object.
    Returns:
        tuple: A tuple containing the created initial_team, alpha_team, beta_team,
               charlie_team, and delta_team objects.
    """
    session.query(Team).delete()
    session.commit()
    teams = {}
    for team_key, team_data in TEAM_DATA.items():
        members = []
        for username in team_data.get('members', []):
            user = session.query(User).filter_by(email=USER_DATA[username]['email']).first()
            if user is None:
                raise ValueError(f"User with email {USER_DATA[username]['email']} not found in database. Please make sure the user table is initialized first.")
            members.append(user)
            if team_data['team_leader_key'] == username:
                team_leader_id = user.id
        teams[team_key] = _create_team(session, team_id=team_data['id'], team_name=team_data['name'], team_leader_id=team_leader_id, members=members)
    return teams['initial_team'], teams['alpha_team'], teams['beta_team'], teams['charlie_team'], teams['delta_team']

def _create_job(session, date, start_time, end_time, description, property_obj, team_obj=None, user_obj=None, job_id=None, arrival_date_offset=0, complete=False):
    """
    Helper function to create a job with deterministic data.

    Args:
        session: The SQLAlchemy session.
        date (date): The date of the job.
        start_time (time): The start time of the job.
        end_time (time): The end time of the job.
        description (str): The description of the job.
        property_obj (Property): The Property object associated with the job.
        team_obj (Team, optional): The Team object assigned to the job. Defaults to None.
        user_obj (User, optional): The User object assigned to the job. Defaults to None.
        job_id (int, optional): The explicit ID for the job. If None, SQLAlchemy assigns one.
        arrival_date_offset (int): The number of days to offset the arrival date from the job date.
        complete (bool): Whether the job is marked as complete. Defaults to False.

    Returns:
        Job: The created Job object.
    """
    app_tz = get_app_timezone()

    start_dt = datetime.combine(date, start_time)
    end_dt = datetime.combine(date, end_time)

    # label as Melbourne
    start_dt = start_dt.replace(tzinfo=app_tz)
    end_dt = end_dt.replace(tzinfo=app_tz)

    # convert to UTC for storage
    start_dt = from_app_tz(start_dt)
    end_dt = from_app_tz(end_dt)

    arrival_date_for_job = start_dt.date() + timedelta(days=arrival_date_offset)
    
    job = Job(
        id=job_id,
        date=start_dt.date(),
        end_date=end_dt.date(),  # Use end date from end_dt
        start_time=start_dt.time(),
        arrival_datetime=datetime.combine(arrival_date_for_job, start_dt.time()),
        end_time=end_dt.time(),
        description=description,
        is_complete=complete,
        property=property_obj
    )
    session.add(job)
    session.commit()

    if user_obj:
        assignment = Assignment(job_id=job.id, user_id=user_obj.id)
        session.add(assignment)
        session.commit()
    
    if team_obj:
        assignment = Assignment(job_id=job.id, team_id=team_obj.id)
        session.add(assignment)
        session.commit()
    return job

def create_initial_properties(session):
    """
    Creates a set of deterministic initial properties and clears any existing
    properties to ensure a clean state.

    Args:
        session: The SQLAlchemy session.

    Returns:
        tuple: A tuple containing the created anytown_property and teamville_property objects.
    """
    session.query(Property).delete()
    session.commit()
    properties = {}
    for property_key, property_data in PROPERTY_DATA.items():
        property_obj = Property(id=property_data['id'], address=property_data['address'], access_notes=property_data['access_notes'])
        session.add(property_obj)
        properties[property_key] = property_obj
    session.commit()
    return properties['anytown_property'], properties['teamville_property']

def create_initial_jobs(session, anytown_property, teamville_property, admin, user, initial_team, alpha_team, beta_team, charlie_team, delta_team):
    """
    Creates a set of deterministic initial jobs and clears any existing
    jobs and assignments to ensure a clean state.

    Args:
        session: The SQLAlchemy session.
        anytown_property (Property): The '123 Main St, Anytown' Property object.
        teamville_property (Property): The '456 Oak Ave, Teamville' Property object.
        admin (User): The admin User object.
        user (User): The user User object.
        initial_team (Team): The 'Initial Team' object.
        alpha_team (Team): The 'Alpha Team' object.
        beta_team (Team): The 'Beta Team' object.
        charlie_team (Team): The 'Charlie Team' object.
        delta_team (Team): The 'Delta Team' object.
    """
    session.query(Assignment).delete()
    session.query(Job).delete()
    session.commit()

    today = today_in_app_tz()
    jobs = {}
    for template in JOB_TEMPLATES:
        job_data = get_job_data_by_id(template['id'])
        team = session.query(Team).filter_by(name=TEAM_DATA[template['team_key']]['name']).first() if template['team_key'] else None
        user = session.query(User).filter_by(email=USER_DATA[template['user_key']]['email']).first() if template['user_key'] else None
        property_obj = anytown_property if template['property_key'] == 'anytown_property' else teamville_property
        job = _create_job(
            session=session,
            date=job_data['date'],
            start_time=job_data['start_time'],
            end_time=job_data['end_time'],
            description=template['description'],
            property_obj=property_obj,
            team_obj=team,
            user_obj=user,
            job_id=template['id'],
            arrival_date_offset=template.get('arrival_date_offset', 0),
            complete=template.get('complete', False)
        )
        jobs[template['id']] = job
    return jobs

def _fix_postgres_sequences(session):
    """
    Fix PostgreSQL sequences after inserting data with explicit IDs.
    This ensures that the next auto-generated ID will be higher than any existing ID.
    
    Args:
        session: SQLAlchemy session
    """
    from sqlalchemy import text
    
    # Check if we're using PostgreSQL by looking at the bind's dialect
    bind = session.bind
    if bind is None:
        return
    
    dialect_name = bind.dialect.name
    if dialect_name != 'postgresql':
        return  # Only needed for PostgreSQL
    
    
    # List of tables and their primary key columns
    tables = [
        ('users', 'id'),
        ('teams', 'id'),
        ('properties', 'id'),
        ('jobs', 'id'),
        ('assignments', 'id'),
        ('media', 'id'),
        ('property_media', 'id'),
        ('job_media', 'id'),
    ]
    
    for table_name, id_column in tables:
        try:
            # Get the maximum ID in the table
            max_id_result = session.execute(
                text(f'SELECT COALESCE(MAX({id_column}), 0) FROM {table_name}')
            ).scalar()
            max_id = max_id_result or 0
            
            if max_id > 0:
                # Fix the sequence
                sequence_name = f'{table_name}_{id_column}_seq'
                session.execute(
                    text(f"SELECT setval('{sequence_name}', :max_id, true)"),
                    {'max_id': max_id}
                )
        except Exception as e:
            print(f"  Warning: Could not fix sequence for {table_name}.{id_column}: {e}")
    
    session.commit()

def delete_jobs_assignments_properties(session):
    """
    Deletes all jobs, assignments, properties and associated media from the database.
    This is useful for resetting the database state before populating with new data.

    Args:
        session: The SQLAlchemy session.
    """
    # Delete all data in correct order to avoid foreign key constraint violations
    # 1. Delete assignments first (references users, jobs, teams)
    session.query(Assignment).delete()
    # 2. Delete job_media and property_media (references media, jobs, properties)
    session.query(JobMedia).delete()
    session.query(PropertyMedia).delete()
    # 3. Delete media (referenced by job_media and property_media)
    session.query(Media).delete()
    # 4. Delete jobs (references properties)
    session.query(Job).delete()
    # 5. Delete properties
    session.query(Property).delete()
    session.commit()

def delete_teams_users(session):
    """
    Deletes all teams and users from the database.
    Must be run after deleting all jobs assignments and properties.
    Args:
        session: The SQLAlchemy session.
    """
    # Before deleting teams, we need to handle foreign key constraints:
    #    - users.team_id references teams.id
    #    - teams.team_leader_id references users.id
    # So we need to set team_id to NULL for all users first
    session.query(User).update({User.team_id: None})
    # Also set team_leader_id to NULL for all teams
    session.query(Team).update({Team.team_leader_id: None})
    session.commit()
    
    # Now we can delete teams
    session.query(Team).delete()
    # Finally delete users
    session.query(User).delete()
    session.commit()

def insert_dummy_data(session_maker=None, existing_session=None):
    """
    Populates the database with a consistent set of deterministic test data.
    This includes users, teams, properties, and jobs.
    This function clears existing data before seeding to ensure a clean state.

    Args:
        session_maker: The SQLAlchemy session factory.
        existing_session: An existing SQLAlchemy session. If provided, this session will be used instead of creating a new one.
    """
    if existing_session:
        session = existing_session
    else:
        session = session_maker()
    
    # Clear existing data
    delete_jobs_assignments_properties(session)
    delete_teams_users(session)
    
    # Now create new data
    admin, supervisor, user, team_leader = create_initial_users(session)
    
    # Create teams    
    initial_team, alpha_team, beta_team, charlie_team, delta_team = create_initial_teams(session, admin, supervisor, user, team_leader)    
    
    # Create properties
    anytown_property, teamville_property = create_initial_properties(session)
    
    # Create jobs
    create_initial_jobs(session, anytown_property, teamville_property, admin, user, initial_team, alpha_team, beta_team, charlie_team, delta_team)
    
    # Fix PostgreSQL sequences if needed
    _fix_postgres_sequences(session)
    
    session.close()

if __name__ == '__main__':
    populate_database(Config.SQLALCHEMY_DATABASE_URI)
