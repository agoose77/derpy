class Colours:
    @staticmethod
    def red(text):
        return  '\033[31m{}\033[0m'.format(text)

    @staticmethod
    def blue(text):
        return  '\033[34m{}\033[0m'.format(text)

    @staticmethod
    def green(text):
        return  '\033[32m{}\033[0m'.format(text)

    @staticmethod
    def white(text):
        return  '\033[37m{}\033[0m'.format(text)


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
