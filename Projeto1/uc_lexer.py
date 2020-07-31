import ply.lex as lex
import sys

class UCLexer():
    """ A lexer for the uC language. After building it, set the
        input text with input(), and call token() to get new
        tokens.
    """
    def __init__(self, error_func):
        """ Create a new Lexer.
            An error function. Will be called with an error
            message, line and column as arguments, in case of
            an error during lexing.
        """
        self.error_func = error_func
        self.filename = ''

        # Keeps track of the last token returned from self.token()
        self.last_token = None

    def build(self, **kwargs):
        """ Builds the lexer from the specification. Must be
            called after the lexer object is created.

            This method exists separately, because the PLY
            manual warns against calling lex.lex inside __init__
        """
        self.lexer = lex.lex(object=self, **kwargs)

    def reset_lineno(self):
        """ Resets the internal line number counter of the lexer.
        """
        self.lexer.lineno = 1

    def input(self, text):
        self.lexer.input(text)

    def token(self):
        self.last_token = self.lexer.token()
        return self.last_token

    def find_tok_column(self, token):
        """ Find the column of the token in its line.
        """
        last_cr = self.lexer.lexdata.rfind('\n', 0, token.lexpos)
        return token.lexpos - last_cr

    # Internal auxiliary methods
    def _error(self, msg, token):
        location = self._make_tok_location(token)
        self.error_func(msg, location[0], location[1])
        self.lexer.skip(1)

    def _make_tok_location(self, token):
        return (token.lineno, self.find_tok_column(token))

    # Reserved keywords
    keywords = (
        'ASSERT', 'BREAK', 'CHAR', 'ELSE', 'FLOAT', 'FOR', 'IF',
        'INT', 'PRINT', 'READ', 'RETURN', 'VOID', 'WHILE',
    )
    
    keyword_map = {}
    for keyword in keywords:
        keyword_map[keyword.lower()] = keyword

    tokens = keywords + (

        'ID',        
        'INT_CONST',
        'FLOAT_CONST',
        'STRING',        
        'LESSTHAN',
        'LESSTHANEQ',       
        'GREATERTHAN', 
        'GREATERTHANEQ', 
        'NOTEQ',       
        'PLUSEQ',
        'MINUSEQ',
        'TIMESEQ',
        'DIVEQ',
        'MODEQ',        
        'PLUSPLUS',
        'MINUSMINUS',         
        'PLUS',
        'MINUS',
        'TIMES',
        'DIVIDE',
        'MOD',                       
        'EQUALS',
        'EQ',        
        'SEMI',
        'COMMA',        
        'ADDRESS',      
        'AND',
        'OR',   
        'NOT',        
        'LPAREN',
        'RPAREN',
        'LBRACE',
        'RBRACE',
        'LBRACKET',
        'RBRACKET',
        'CHAR_CONST'
     
    )
    t_ignore = ' \t'
    
    # Literals.  Should be placed in module given to lex()
    literals = ['+','-','*','/' ]
    
    def t_uccomment(self, t):
        r'/\*.*\n'
        t.lexer.lineno += t.value.count('\n')

    def t_comment(self, t):
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count('\n')
        
    def t_cppcomment(self, t):
        r'//.*\n'
        t.lexer.lineno += t.value.count('\n')
        
    def t_INT(self, t):
        r"int"
        t.type = self.keyword_map.get(t.value, "INT")    
        return t
    
    def t_FLOAT(self, t):
        r"float"
        t.type = self.keyword_map.get(t.value, "FLOAT")    
        return t
    
    def t_CHAR(self, t):
        r"char"
        t.type = self.keyword_map.get(t.value, "CHAR")    
        return t
    
    def t_FLOAT_CONST(self, t):
        r'([0-9]*\.[0-9]+)|([0-9]+\.)'
        t.type = self.keyword_map.get(t.value, "FLOAT_CONST")    
        return t
         
    def t_INT_CONST(self, t):
        r'\d+'
        t.type = self.keyword_map.get(t.value, "INT_CONST")    
        return t
    
    def t_CHAR_CONST(self, t):
        r"""'.'"""
        t.type = self.keyword_map.get(t.value, "CHAR_CONST")    
        return t
    
    def t_STRING(self, t):
         r'".*?"'
         t.type = self.keyword_map.get(t.value, "STRING")    
         return t
     
    def t_LESSTHANEQ(self, t):
         r'\<='
         t.type = self.keyword_map.get(t.value, "LESSTHANEQ")    
         return t
           
    def t_LESSTHAN(self, t):
         r'\<'
         t.type = self.keyword_map.get(t.value, "LESSTHAN")    
         return t
        
        
    def t_GREATERTHANEQ(self, t):
         r'\>='
         t.type = self.keyword_map.get(t.value, "GREATERTHANEQ")    
         return t  
        
       
    def t_GREATERTHAN(self, t):
         r'\>'
         t.type = self.keyword_map.get(t.value, "GREATERTHAN")    
         return t       
          
    def t_NOTEQ(self, t):
         r'\!='
         t.type = self.keyword_map.get(t.value, "NOTEQ")    
         return t
     
    def t_PLUSEQ(self, t):
         r'\+='
         t.type = self.keyword_map.get(t.value, "PLUSEQ")    
         return t
     
    def t_MINUSEQ(self, t):
         r'\-='
         t.type = self.keyword_map.get(t.value, "MINUSEQ")    
         return t
     
    def t_TIMESEQ(self, t):
         r'\*='
         t.type = self.keyword_map.get(t.value, "TIMESEQ")    
         return t
     
    def t_DIVEQ(self, t):
         r'\/='
         t.type = self.keyword_map.get(t.value, "DIVEQ")    
         return t

    def t_MODEQ(self, t):
         r'\%='
         t.type = self.keyword_map.get(t.value, "MODEQ")    
         return t
        
    def t_PLUSPLUS(self, t):
         r'\+\+'
         t.type = self.keyword_map.get(t.value, "PLUSPLUS")    
         return t
     
    def t_MINUSMINUS(self, t):
         r'\-\-'
         t.type = self.keyword_map.get(t.value, "MINUSMINUS")    
         return t
            
    def t_PLUS(self, t):
         r'\+'
         t.type = self.keyword_map.get(t.value, "PLUS")    
         return t
     
    def t_MINUS(self, t):
         r'\-'
         t.type = self.keyword_map.get(t.value, "MINUS")    
         return t
     
    def t_TIMES(self, t):
         r'\*'
         t.type = self.keyword_map.get(t.value, "TIMES")    
         return t
     
    def t_DIVIDE(self, t):
         r'\/'
         t.type = self.keyword_map.get(t.value, "DIVIDE")    
         return t
     
    def t_MOD(self, t):
         r'\%'
         t.type = self.keyword_map.get(t.value, "MOD")    
         return t
     
    def t_EQ(self, t):
         r'\=='
         t.type = self.keyword_map.get(t.value, "EQ")    
         return t
     
    def t_EQUALS(self, t):
         r'\='
         t.type = self.keyword_map.get(t.value, "EQUALS")    
         return t
        
    def t_AND(self, t):
         r'\&\&'
         t.type = self.keyword_map.get(t.value, "AND")
         return t
     
    def t_OR(self, t):
         r'\|\|'
         t.type = self.keyword_map.get(t.value, "OR")
         return t
     
    def t_NOT(self, t):
         r'\!'
         t.type = self.keyword_map.get(t.value, "NOT")
         return t  

    def t_SEMI(self, t):
        r'\;'
        t.type = self.keyword_map.get(t.value, "SEMI")    
        return t
    
    def t_COMMA(self, t):
         r'\,'
         t.type = self.keyword_map.get(t.value, "COMMA")    
         return t
     
    def t_ADDRESS(self, t):
         r'\&'
         t.type = self.keyword_map.get(t.value, "ADDRESS")    
         return t
     
    def t_LPAREN(self, t):
         r'\('
         t.type = self.keyword_map.get(t.value, "LPAREN")    
         return t
     
    def t_RPAREN(self, t):
         r'\)'
         t.type = self.keyword_map.get(t.value, "RPAREN")    
         return t
     
    def t_LBRACE(self, t):
         r'\{'
         t.type = self.keyword_map.get(t.value, "LBRACE")    
         return t
    
    def t_RBRACE(self, t):
         r'\}'
         t.type = self.keyword_map.get(t.value, "RBRACE")    
         return t
     
    def t_LBRACKET(self, t):
         r'\['
         t.type = self.keyword_map.get(t.value, "LBRACKET")    
         return t
     
    def t_RBRACKET(self, t):
         r'\]'
         t.type = self.keyword_map.get(t.value, "RBRACKET")    
         return t
     
    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_ID(self, t):
        r'[a-zA-Z_][0-9a-zA-Z_]*'
        t.type = self.keyword_map.get(t.value, "ID")
        return t
    
    def t_error(self, t):
        msg = "Illegal character %s" % repr(t.value[0])
        self._error(msg, t)
       
    # Scanner (used only for test)
    def scan(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            print(tok)

