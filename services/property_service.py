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
        
        returns: List of Property"""
        return self.db_session.query(Property).all()

    def get_property_by_id(self, property_id):
        """
        Retrieve a single property by its ID from the database.
        
        returns: Property"""
        return self.db_session.query(Property).filter_by(id=property_id).first()
    
    def get_property_by_address(self, address):
        return self.db_session.query(Property).filter_by(address=address).first()

    def create_property(self, property_data):
        """
        Create a new property in the database.
        
        returns: New property"""
        
        new_property = Property(
            address=property_data.get('address'),
            access_notes=property_data.get('access_notes'),
            notes=property_data.get('notes')
        )
        self.db_session.add(new_property)
        self.db_session.commit()
        self.db_session.refresh(new_property)
        return new_property

    def update_property(self, property_id, property_data):
        """
        Update an existing property in the database.
        
        returns: Property or None"""
        property = self.get_property_by_id(property_id)
        if not property:
            return None

        property.address = property_data.get('address', property.address)
        property.access_notes = property_data.get('access_notes', property.access_notes)
        property.notes = property_data.get('notes', property.notes)

        self.db_session.commit()
        self.db_session.refresh(property)
        return property

    def delete_property(self, property_id):
        """
        Delete a property from the database.
        
        returns: bool
        """
        property = self.get_property_by_id(property_id)
        if not property:
            return False

        self.db_session.delete(property)
        self.db_session.commit()
        return True