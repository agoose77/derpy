from . import Recurrence, BaseParser


class Grammar:

    def __init__(self, name):
        object.__setattr__(self, '_name', name)
        object.__setattr__(self, '_recurrences', {})
        object.__setattr__(self, '_frozen', False)

    def ensure_parsers_defined(self):
        for name, parser in self._recurrences.items():
            if parser.parser is None:
                raise ValueError("{} parser is not defined".format(name))
        object.__setattr__(self, '_frozen', True)

    def __getattr__(self, name):
        try:
            recurrence = self._recurrences[name]
        except KeyError:
            if self._frozen:
                raise AttributeError("Grammar has no rule {!r}".format(name))

            self._recurrences[name] = recurrence = Recurrence()

        object.__setattr__(self, name, recurrence)  # To stop this being created again
        return recurrence

    def __setattr__(self, name, value):
        assert isinstance(value, BaseParser), (name, value)

        # Existing parser is either recurrence or non recurrence
        if hasattr(self, name):
            if name in self._recurrences:
                recurrence = getattr(self, name)
                if recurrence.parser is not None:
                    raise ValueError('Recurrent parser already defined')

                recurrence.parser = value
                recurrence.simple_name = name

            else:
                raise ValueError('Parser already assigned')

        # No recurrence relation (as assignment BEFORE get)
        else:
            object.__setattr__(self, name, value)

    def __repr__(self):
        return "Grammar(name={!r})".format(self._name)
