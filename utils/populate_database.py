import os
from config import Config
from database import User, init_db, insert_dummy_data
from database import Team, Property, Job, Assignment, Media, PropertyMedia, JobMedia
from datetime import date, datetime, time, timedelta


def populate_database(database_uri, force=True):
    """This function populates the database with dummy data for testing purposes.
    
    Args:
        database_uri (str): The database URI where the dummy data will be inserted.
    """
    
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

    admin = User(id=1, first_name='Ruby', last_name='Redmond', email='admin@example.com', phone='12345678', role='admin')
    admin.set_password('admin_password')
    session.add(admin)

    supervisor = User(id=2, first_name='Damo', last_name="Brown", email='supervisor@example.com', role='supervisor')
    supervisor.set_password('supervisor_password')
    session.add(supervisor)

    user = User(id=3, first_name='Manchan', last_name='Fionn', email='user@example.com', role='user')
    user.set_password('user_password')
    session.add(user)

    team_leader = User(id=4, first_name='Alice', last_name='Smith', email='teamleader@example.com', role='team_leader')
    team_leader.set_password('team_leader_password')
    session.add(team_leader)
    session.commit()
    print("Initial users created for deterministic testing.")
    return admin, supervisor, user, team_leader

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

def create_initial_teams(session, admin, supervisor_user, user, team_leader):
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

    initial_team = _create_team(session, 'Initial Team', admin.id, members=[admin, user], team_id=1)
    alpha_team = _create_team(session, 'Alpha Team', supervisor_user.id, members=[supervisor_user], team_id=2)
    beta_team = _create_team(session, 'Beta Team', team_leader.id, members=[team_leader], team_id=3)
    charlie_team = _create_team(session, 'Charlie Team', team_id=4)
    delta_team = _create_team(session, 'Delta Team', team_id=5)
    
    print("Initial teams created for deterministic testing.")
    return initial_team, alpha_team, beta_team, charlie_team, delta_team

def _create_job(session, date, time, end_time, description, property_obj, team_obj=None, user_obj=None, job_id=None, arrival_date_offset=0):
    """
    Helper function to create a job with deterministic data.

    Args:
        session: The SQLAlchemy session.
        date (date): The date of the job.
        time (time): The start time of the job.
        end_time (time): The end time of the job.
        description (str): The description of the job.
        property_obj (Property): The Property object associated with the job.
        team_obj (Team, optional): The Team object assigned to the job. Defaults to None.
        user_obj (User, optional): The User object assigned to the job. Defaults to None.
        job_id (int, optional): The explicit ID for the job. If None, SQLAlchemy assigns one.
        arrival_date_offset (int): The number of days to offset the arrival date from the job date.

    Returns:
        Job: The created Job object.
    """
    arrival_date_for_job = date + timedelta(days=arrival_date_offset)
    
    job = Job(
        id=job_id,
        date=date,
        time=time,
        arrival_datetime=datetime.combine(arrival_date_for_job, time),
        end_time=end_time,
        description=description,
        is_complete=False,
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

    anytown_property = Property(id=1, address='123 Main St, Anytown', access_notes='Key under mat')
    session.add(anytown_property)
    
    teamville_property = Property(id=2, address='456 Oak Ave, Teamville', access_notes='Code 1234')
    session.add(teamville_property)
    session.commit()
    print("Initial properties created for deterministic testing.")
    return anytown_property, teamville_property

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

    today = date.today()

    # Initial jobs
    _create_job(session, today, time(9, 0), time(11, 0), 'Full house clean, focus on kitchen and bathrooms.', anytown_property, team_obj=initial_team, user_obj=admin, job_id=1, arrival_date_offset=2)
    _create_job(session, today, time(12, 0), time(14, 0), '', anytown_property, team_obj=initial_team, job_id=2, arrival_date_offset=1)
    _create_job(session, today, time(14, 0), time(16, 0), '', anytown_property, team_obj=initial_team, job_id=3, arrival_date_offset=0)
    
    # Alpha Team job
    _create_job(session, today, time(10, 0), time(12, 0), '', teamville_property, team_obj=alpha_team, job_id=4)
    _create_job(session, today, time(12, 30), time(14, 30), '', teamville_property, team_obj=alpha_team, job_id=8, arrival_date_offset=1)
    _create_job(session, today, time(9, 0), time(10, 30), "Don't let the cat outside", anytown_property, team_obj=alpha_team, job_id=9, arrival_date_offset=2)
    _create_job(session, today, time(18, 30), time(20, 30), '', anytown_property, team_obj=alpha_team, user_obj=user, job_id=10, arrival_date_offset=1)


    # Beta Team job
    _create_job(session, today, time(13, 0), time(15, 0), 'Beta Team Job: Garden maintenance.', anytown_property, team_obj=beta_team, job_id=5)
    _create_job(session, today - timedelta(days=1), time(8, 0), time(10, 0), 'Beta Team Job: Pool cleaning.', anytown_property, team_obj=beta_team, job_id=11)

    # Charlie Team job
    _create_job(session, today, time(9, 30), time(11, 30), 'Charlie Team Job: Roof and gutter clean.', teamville_property, team_obj=charlie_team, job_id=6)

    # Delta Team job
    _create_job(session, today, time(15, 0), time(17, 0), 'Delta Team Job: Driveway pressure wash.', anytown_property, team_obj=delta_team, job_id=7)
                                                   

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
    
    print("Fixing PostgreSQL sequences after inserting data with explicit IDs...")
    
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
                print(f"  Fixed sequence for {table_name}.{id_column}: set to {max_id}")
            else:
                print(f"  No data in {table_name}, skipping sequence fix")
        except Exception as e:
            print(f"  Warning: Could not fix sequence for {table_name}.{id_column}: {e}")
    
    session.commit()


def insert_dummy_data(Session):
    """
    Populates the database with a consistent set of deterministic test data.
    This includes users, teams, properties, and jobs.
    This function clears existing data before seeding to ensure a clean state.

    Args:
        Session: The SQLAlchemy session factory.
    """
    session = Session()
    
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
    
    # 6. Before deleting teams, we need to handle foreign key constraints:
    #    - users.team_id references teams.id
    #    - teams.team_leader_id references users.id
    # So we need to set team_id to NULL for all users first
    session.query(User).update({User.team_id: None})
    # Also set team_leader_id to NULL for all teams
    session.query(Team).update({Team.team_leader_id: None})
    session.commit()
    
    # 7. Now we can delete teams
    session.query(Team).delete()
    # 8. Finally delete users
    session.query(User).delete()
    
    session.commit()
    print("Cleared existing data for fresh population.")
    
    # Now create new data
    admin, supervisor, user, team_leader = create_initial_users(session)
    print("Initial users created for deterministic testing.")
    
    # Create teams    
    initial_team, alpha_team, beta_team, charlie_team, delta_team = create_initial_teams(session, admin, supervisor, user, team_leader)    
    print("Initial teams created for deterministic testing.")
    
    # Create properties
    anytown_property, teamville_property = create_initial_properties(session)
    print("Initial properties created for deterministic testing.")
    
    # Create jobs
    create_initial_jobs(session, anytown_property, teamville_property, admin, user, initial_team, alpha_team, beta_team, charlie_team, delta_team)
    print("Initial jobs created and assigned for deterministic testing.")
    
    # Fix PostgreSQL sequences if needed
    _fix_postgres_sequences(session)
    
    session.close()

if __name__ == '__main__':
    populate_database(Config.SQLALCHEMY_DATABASE_URI)