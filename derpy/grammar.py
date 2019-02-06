from .parsers import Recurrence, BaseParser


class Grammar:
    """Namespace for grammar definitions.

    Facilitates use-before-declaration of rules using a Recurrence parser
    """

    def __init__(self, name: str):
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_recurrences", {})
        object.__setattr__(self, "_frozen", False)

    def validate(self):
        for name, parser in self._recurrences.items():
            if parser.parser is None:
                raise ValueError(f"{name} parser is not defined")

    def freeze(self):
        """Check all parsers are defined"""
        self.validate()
        object.__setattr__(self, "_frozen", True)

    def extend(self, name: str) -> "Grammar":
        self.validate()

        grammar = self.__class__(name)

        for name, value in vars(self).items():
            if isinstance(value, BaseParser):
                setattr(grammar, name, value)

        return grammar

    def __getattr__(self, name):
        if self._frozen:
            raise AttributeError(f"Frozen grammar has no rule {name!r}")

        # __getattr__ only called if parser doesn't exist, so this is a forward-reference (use recurrence)
        recurrence = self._recurrences[name] = Recurrence()
        # Assign recurrence to attribute
        object.__setattr__(self, name, recurrence)
        return recurrence

    def __setattr__(self, name, value):
        if self._frozen:
            raise AttributeError(f"Frozen grammar {self._name} cannot be assigned to")

        if not isinstance(value, BaseParser):
            raise ValueError("Grammar rule must be assigned to an instance of BaseParser")

        # Existing parser is either forward-declared-recurrence or a normal parser
        if hasattr(self, name):
            try:
                recurrence = self._recurrences[name]

            except KeyError:
                # In this case, parser wasn't found in recurrences so must have been explicitly assigned
                raise ValueError("Parser already assigned")

            else:
                if recurrence.parser is not None:
                    raise ValueError(f"Recurrent parser {name!r} already defined")

                recurrence.parser = value

        # No recurrence relation (as assignment BEFORE get)
        else:
            object.__setattr__(self, name, value)

    def __repr__(self):
        return f"Grammar(name={self._name!r})"
