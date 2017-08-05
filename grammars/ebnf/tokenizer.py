from derp.tokenizer import Tokenizer, Token


class EBNFTokenizer(Tokenizer):

    patterns = Tokenizer.patterns + (
        ("COMMENT", r'#[^\n]*'),
        ("COLON", r':')
    )

    def create_context(self, string):
        ctx = super().create_context(string)
        ctx['paren_depth'] = 0
        return ctx

    def handle_COLON(self, match, value, context):
        return Token(value, value)

    def handle_PAREN(self, match, value, context):
        if value in "({[":
            context['paren_depth'] += 1
        else:
            context['paren_depth'] -= 1

        return Token(value, value)

    def handle_NEWLINE(self, match, value, context):
        super().handle_NEWLINE(match, value, context)

        if context['paren_depth']:
            return

        return Token('\n', '\n')
