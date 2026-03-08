class DomainEvent:
    """Base class for domain events."""
    def __init__(self, name: str):
        self.name = name
