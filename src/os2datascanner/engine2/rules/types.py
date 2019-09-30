from enum import Enum

class InputType(Enum):
    """Rules declare what type they expect to operate on by specifying a member
    of the InputType enumeration. The values associated with these members are
    simple string identifiers that can be used in serialisation formats."""
    Text = "text"
