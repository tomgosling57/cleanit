from database import Property

class PropertyService:
    """
    Service layer for property-related operations.
    """
    def __init__(self, db_session):
        self.db_session = db_session

    def get_all_properties(self):
        """
        Retrieve all properties from the database.
        """
        return self.db_session.query(Property).all()

    def get_property_by_id(self, property_id):
        """
        Retrieve a single property by its ID from the database.
        """
        return self.db_session.query(Property).filter_by(id=property_id).first()

    def create_property(self, property_data):
        """
        Create a new property in the database.
        """
        pass

    def update_property(self, property_id, property_data):
        """
        Update an existing property in the database.
        """
        pass

    def delete_property(self, property_id):
        """
        Delete a property from the database.
        """
        pass