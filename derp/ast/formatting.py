class Colours:

    @staticmethod
    def red(text):
        return '\x1b[0;31;m' + text

    @staticmethod
    def blue(text):
        return '\x1b[0;34;m' + text

    @staticmethod
    def green(text):
        return '\x1b[0;32;m' + text

    @staticmethod
    def white(text):
        return '\33[0;37;m' + text


def cyclic_colour_formatter(node, level, text):
    all_colours = Colours.red, Colours.green, Colours.blue, Colours.white
    colour_f = all_colours[level % len(all_colours)]
    return colour_f(text)


def no_op_formatter(text):
    return text


def highlight_node_formatter(node_cls, match_format, other_format=no_op_formatter):
    def wrapper(node, level, text):
        if isinstance(node, node_cls):
            return match_format(text)
        return other_format(text)
    return wrapper