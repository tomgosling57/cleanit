# Backend Testing Specification

## Testing Environment

### Development Environment
- **Database**: SQLite in-memory database for fast testing
- **Flask App**: Test configuration with debug mode enabled
- **Test Runner**: pytest with Flask-Testing extension
- **Coverage**: pytest-cov for code coverage reporting

### Test Database Setup
```python
# conftest.py
@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def session(app):
    connection = db.engine.connect()
    transaction = connection.begin()
    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)
    
    db.session = session
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()
```

## Unit Testing Strategy

### Model Testing
```python
# tests/test_models.py
class TestUserModel:
    def test_create_user(self, session):
        user = User(username='testuser', email='test@example.com', 
                   password_hash='hashed_password', first_name='Test', 
                   last_name='User', role_id=1)
        session.add(user)
        session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.is_active is True

    def test_user_relationships(self, session):
        role = Role(name='cleaner')
        team = Team(name='Test Team')
        user = User(username='testuser', role=role, team=team)
        
        session.add_all([role, team, user])
        session.commit()
        
        assert user.role.name == 'cleaner'
        assert user.team.name == 'Test Team'

    def test_user_validation(self):
        with pytest.raises(ValueError):
            User(username='ab')  # Too short username
```

### Route Testing
```python
# tests/test_auth_routes.py
class TestAuthRoutes:
    def test_login_success(self, client, session):
        # Setup test user
        user = User(username='testuser', password_hash=generate_password_hash('password'))
        session.add(user)
        session.commit()
        
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'password'
        })
        
        assert response.status_code == 302  # Redirect
        assert '/dashboard' in response.location

    def test_login_failure(self, client):
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'Invalid credentials' in response.data

    def test_protected_route_access(self, client):
        response = client.get('/timetable')
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location
```

### Business Logic Testing
```python
# tests/test_timetable_logic.py
class TestTimetableLogic:
    def test_job_reassignment_permissions(self, session):
        team_leader = User(username='leader', role=Role(name='team_leader'))
        other_team_leader = User(username='other_leader', role=Role(name='team_leader'))
        team = Team(name='Team A', team_leader=team_leader)
        other_team = Team(name='Team B', team_leader=other_team_leader)
        job = Job(title='Test Job', team=team)
        
        session.add_all([team_leader, other_team_leader, team, other_team, job])
        session.commit()
        
        # Team leader should not be able to reassign from other team
        with pytest.raises(PermissionError):
            reassign_job(job.id, other_team.id, team_leader.id)

    def test_job_creation_validation(self):
        with pytest.raises(ValidationError):
            create_job(title='', scheduled_date='invalid-date')
```

## Integration Testing

### Database Integration Tests
```python
# tests/test_database_integration.py
class TestDatabaseIntegration:
    def test_complete_workflow(self, session):
        # Create test data
        role = Role(name='cleaner')
        team = Team(name='Cleaning Team')
        user = User(username='cleaner1', role=role, team=team)
        job = Job(title='Office Cleaning', team=team)
        assignment = Assignment(job=job, cleaner=user)
        
        session.add_all([role, team, user, job, assignment])
        session.commit()
        
        # Verify relationships
        assert len(team.jobs) == 1
        assert len(user.assigned_jobs) == 1
        assert assignment.job.title == 'Office Cleaning'
```

### API Integration Tests
```python
# tests/test_api_integration.py
class TestApiIntegration:
    def test_timetable_api(self, client, session):
        # Setup authenticated session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        
        response = client.get('/timetable')
        assert response.status_code == 200
        assert b'Timetable' in response.data

    def test_htmx_endpoints(self, client, session):
        # Test htmx job update endpoint
        response = client.post('/update-job-assignment', data={
            'job_id': 1,
            'new_team_id': 2
        }, headers={'HX-Request': 'true'})
        
        assert response.status_code == 200
        # Should return HTML fragment, not full page
```

## Test Data Management

### Fixtures
```python
# conftest.py
@pytest.fixture
def sample_roles(session):
    roles = [
        Role(name='cleaner'),
        Role(name='team_leader'), 
        Role(name='owner')
    ]
    session.add_all(roles)
    session.commit()
    return roles

@pytest.fixture
def sample_teams(session, sample_roles):
    teams = [
        Team(name='Team Alpha'),
        Team(name='Team Beta')
    ]
    session.add_all(teams)
    session.commit()
    return teams

@pytest.fixture
def authenticated_client(client, session):
    user = User(username='testuser', role_id=1)
    session.add(user)
    session.commit()
    
    with client.session_transaction() as sess:
        sess['user_id'] = user.id
    
    return client
```

### Test Data Factory
```python
# tests/factories.py
class UserFactory:
    @staticmethod
    def create_cleaner(session, **kwargs):
        defaults = {
            'username': f'cleaner{random.randint(1000,9999)}',
            'email': f'cleaner{random.randint(1000,9999)}@example.com',
            'password_hash': 'hashed_password',
            'first_name': 'Test',
            'last_name': 'Cleaner',
            'role_id': 1  # cleaner role
        }
        defaults.update(kwargs)
        user = User(**defaults)
        session.add(user)
        session.commit()
        return user
```

## Performance Testing

### Database Query Optimization
```python
# tests/test_performance.py
class TestPerformance:
    def test_timetable_query_performance(self, session):
        # Create large dataset
        for i in range(1000):
            job = Job(title=f'Job {i}', team_id=1)
            session.add(job)
        session.commit()
        
        # Test query performance
        start_time = time.time()
        jobs = session.query(Job).filter_by(team_id=1).all()
        end_time = time.time()
        
        assert (end_time - start_time) < 1.0  # Should complete within 1 second
        assert len(jobs) == 1000
```

## Security Testing

### Authentication & Authorization Tests
```python
# tests/test_security.py
class TestSecurity:
    def test_role_based_access(self, client, session):
        # Test that cleaners cannot access admin routes
        cleaner = UserFactory.create_cleaner(session)
        
        with client.session_transaction() as sess:
            sess['user_id'] = cleaner.id
        
        response = client.get('/admin/users')
        assert response.status_code == 403  # Forbidden

    def test_csrf_protection(self, client):
        response = client.post('/job/create', data={
            'title': 'Test Job'
        })  # No CSRF token
        assert response.status_code == 400  # Bad Request
```

## Test Coverage Goals

- **Model Layer**: 95% coverage
- **Route Handlers**: 90% coverage  
- **Business Logic**: 85% coverage
- **Integration Tests**: 80% coverage
- **Security Tests**: 100% of critical paths