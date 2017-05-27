from .parsers import Recurrence, BaseParser


class Grammar:
    """Namespace for grammar definitions.

    Facilitates use-before-declaration of rules using a Recurrence parser"""

    def __init__(self, name):
        object.__setattr__(self, '_name', name)
        object.__setattr__(self, '_recurrences', {})
        object.__setattr__(self, '_frozen', False)

    def ensure_parsers_defined(self):
        """Check all parsers are defined"""
        for name, parser in self._recurrences.items():
            if parser.parser is None:
                raise ValueError("{} parser is not defined".format(name))

        object.__setattr__(self, '_frozen', True)

    def __getattr__(self, name):
        if self._frozen:
            raise AttributeError("Frozen grammar has no rule {!r}".format(name))

        recurrence = self._recurrences[name] = Recurrence()
        object.__setattr__(self, name, recurrence)  # Assign recurrence to attribute
        return recurrence

    def __setattr__(self, name, value):
        if self._frozen:
            raise AttributeError("Frozen grammar cannot be assigned to")

        if not isinstance(value, BaseParser):
            raise ValueError("Grammar rule must be assigned to an instance of BaseParser")

        # Existing parser is either forward-declared-recurrence or a normal parser
        if hasattr(self, name):
            try:
                recurrence = self._recurrences[name]

            except KeyError:
                # In this case, parser wasn't found in recurrences so must have been explicitly assigned
                raise ValueError('Parser already assigned')

            else:
                if recurrence.parser is not None:
                    raise ValueError('Recurrent parser already defined')

                recurrence.parser = value
                recurrence.simple_name = name

        # No recurrence relation (as assignment BEFORE get)
        else:
            object.__setattr__(self, name, value)

    def __repr__(self):
        return "Grammar(name={!r})".format(self._name)