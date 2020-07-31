from uc_ast import *

class uCType(object):
    '''
    Class that represents a type in the uC language.  Types 
    are declared as singleton instances of this type.
    '''
    def __init__(self, typename, 
                 binary_ops=None, 
                 unary_ops=None,
                 rel_ops=None,
                 assign_ops=None):
      
        self.typename = typename
        self.unary_ops = unary_ops or set()
        self.binary_ops = binary_ops or set()
        self.rel_ops = rel_ops or set()
        self.assign_ops = assign_ops or set()
        
    def __repr__(self):
        return "type({})".format(self.typename)

         
IntType = uCType("int",
                 unary_ops   = {"-", "+", "--", "++", "p--", "p++", "*", "&"},
                 binary_ops  = {"+", "-", "*", "/", "%"},
                 rel_ops     = {"==", "!=", "<", ">", "<=", ">="},
                 assign_ops  = {"=","+=", "-=", "*=", "/=", "%="}
                 )

FloatType = uCType("float",
                 unary_ops   = {"-", "+", "*", "&"},
                 binary_ops  = {"+", "-", "*", "/", "%"},
                 rel_ops     = {"==", "!=", "<", ">", "<=", ">="},
                 assign_ops  = {"=", "+=", "-=", "*=", "/=", "%="}
                 )

CharType = uCType("char",
                  binary_ops  = {"+"},
                  unary_ops   = {"*", "&"},
                  rel_ops     = {"==", "!=", "&&", "||"},
                  assign_ops  = {"="}
                  )

BoolType = uCType("bool",
                  unary_ops   = {"!", "*", "&"},
                  rel_ops     = {"==", "!=", "&&", "||"},
                  )

ArrayType = uCType("array",
                   unary_ops   = {"*", "&"},
                   rel_ops     = {"==", "!="}
                   )

StringType = uCType("string",
                   binary_ops  = {"+"},
                   unary_ops   = {},
                   rel_ops     = {"==", "!="}
                   )

PtrType = uCType("ptr",
                  unary_ops   = {"*", "&"},
                  rel_ops     = {"==", "!="},
                  )

VoidType = uCType("void",
                  unary_ops   = {"*", "&"},
                  binary_ops  = {}
                  )

class SymbolTable(dict):
    '''
    Class representing a symbol table.  It should provide functionality
    for adding and looking up nodes associated with identifiers.
    '''
    def __init__(self, decl=None):
        super().__init__()
        self.decl = decl
        
    def add(self, name, value):
        self[name] = value
        
    def lookup(self, name):
        return self.get(name, None)
    
    def return_type(self):
        if self.decl:
            return self.decl.returntype
        return None
        
class Environment(object):
    def __init__(self):
        self.rtypes = []
        self.cur_rtype = []
        self.cur_loop = []
        self.stack = []
        self.root = SymbolTable()
        self.stack.append(self.root)
        self.funcdef = None
        self.root.update({
            'int': IntType,
            'float': FloatType,
            'char': CharType,
            'string': StringType,
            'bool': BoolType,
            'array': ArrayType,
            'ptr': PtrType,
            'void': VoidType
        })
                
    def push(self, enclosure):
        self.stack.append(SymbolTable(enclosure))
        self.rtypes.append(self.cur_rtype)
        if isinstance(enclosure, FuncDecl):
            self.cur_rtype = enclosure.type.type.names  
        else:
            self.cur_rtype = [VoidType]
            
    def pop(self):
        self.stack.pop()
        self.cur_rtype = self.rtypes.pop()
        
    def lookup(self, name):
        for scope in reversed(self.stack):
            hit = scope.lookup(name)
            if hit is not None:
                return hit
        return None   

    def scope_level(self):
        return len(self.stack)-1

    def add_local(self, name, kind):
        self.peek().add(name.name, name)
        name.kind = kind
        name.scope = self.scope_level()

    def add_root(self, name, value):
        self.root.add(name, value)

    def peek_root(self):
        return self.stack[0]

    def peek(self):
        return self.stack[-1]
    
    def find(self, name):
        cur_symtable = self.stack[-1]
        if name in cur_symtable:
            return True
        else:
            return False

class Visitor(NodeVisitor):
    '''
    Program visitor class. This class uses the visitor pattern. You need to define methods
    of the form visit_NodeName() for each kind of AST node that you want to process.
    Note: You will need to adjust the names of the AST nodes if you picked different names.
    '''
    def __init__(self):
        self.environment = Environment()
        self.typemap = {
            "int": IntType,
            "float": FloatType,
            "string": StringType,
            "char": CharType,
            "void": VoidType,       
            "bool": BoolType, 
            "ptr": PtrType,
            "array": ArrayType   
        }
    
    def visit_Program(self, node):
        self.environment.push(node)
        node.symtab = self.environment.peek_root()  
        for _decl in node.gdecls:
            self.visit(_decl)
        self.environment.pop()

    def visit_GlobalDecl(self, node):
        for _decl in node.decls:
            self.visit(_decl)
        
    def visit_FuncDef(self, node):
        node.decls =[]
        self.environment.funcdef = node
        self.visit(node.spec)
        self.visit(node.decl)
        if node.param_decls is not None:
            for _par in node.param_decls:
                self.visit(_par)
        if node.body is not None:
            for _body in node.body:
                self.visit(_body)
        self.environment.pop()
        _func = self.environment.lookup(node.decl.name.name)
        node.spec = _func.type  

    def visit_FuncDecl(self, node):
        self.visit(node.type)
        _func = self.environment.lookup(node.type.declname.name)
        _func.kind = 'func'
        _func.bind = node.args
        self.environment.push(node)
        if node.args is not None:
            for _arg in node.args:
                self.visit(_arg)
                
    def visit_Decl(self, node):
        _type = node.type
        self.visit(_type)
        node.name.bind = _type
        _var = node.name.name
        _line = f"{node.name.coord.line}:{node.name.coord.column} - "
        if isinstance(_type, PtrDecl):
            while isinstance(_type, PtrDecl):
                _type = _type.type
        if isinstance (_type, FuncDecl):
            assert self.environment.lookup(_var), _line + f"'{_var}' is not defined."
        else:
            assert self.environment.find(_var), _line + f"'{_var}' is not defined."
            if node.init is not None:
                self.checkInit(_type, node.init, _var, _line)
    
    def visit_ArrayDecl(self, node):
        self.visit(node.type)
        _type = node.type
        while not isinstance(_type, VarDecl):
            _type = _type.type
        _id = _type.declname
        _id.type.names.insert(0, self.typemap["array"])
        if node.dim is not None:
            self.visit(node.dim) 
    
    def visit_ArrayRef(self, node):
        _subs = node.subscript
        self.visit(_subs)
        if isinstance(_subs, ID):
            _line = f"{_subs.coord.line}:{_subs.coord.column} - "
            assert _subs.scope is not None, _line + f"'{_subs.name}' is not defined."
        _stype = _subs.type.names[-1]
        _line = f"{node.coord.line}:{node.coord.column} - "
        assert _stype == IntType, _line + f"'{_stype}' must be of type(int)."
        self.visit(node.name)
        _type = node.name.type.names[1:]
        node.type = Type(_type, node.coord)
 
    def visit_VarDecl(self, node):        
        self.visit(node.type)
        _loc = node.declname
        self.visit(_loc)
        if isinstance(_loc, ID):
            _line = f"{_loc.coord.line}:{_loc.coord.column} - "
            assert not self.environment.find(_loc.name), _line + f"'name {_loc.name} already defined in this scope.'"
            self.environment.add_local(_loc, 'var')
            _loc.type = node.type
        
    def visit_ID(self, node):
        _id = self.environment.lookup(node.name)
        if _id is not None:
            node.type = _id.type
            node.kind = _id.kind
            node.scope = _id.scope
            node.bind = _id.bind
            
    def visit_Type(self, node):
        for i, _name in enumerate(node.names or []):
            if not isinstance(_name, uCType):
                _type = self.typemap[_name]
                node.names[i] = _type
                
    def setDim(self, type, length, line, var):
        if type.dim is None:
            type.dim = Constant('int', length)
            self.visit_Constant(type.dim)
        else:
            assert type.dim.value == length, line + f"incompatible size at '{var}' initialization."     
             
    def checkInit(self, type, init, var, line):
        self.visit(init)
        if isinstance(init, Constant):
            if init.rawtype == 'string':
                assert type.type.type.names == [self.typemap["array"], self.typemap["char"]], line + f"'{var}' initialization type incompatible."
                self.setDim(type, len(init.value), line, var)
            else:
                assert type.type.names[0] == init.type.names[0], line + f"'{var}' initialization type incompatible."
                
        elif isinstance(init, InitList):
            _exprs = init.exprs
            _length = len(_exprs)       
            if isinstance(type, VarDecl):  
                assert _length == 1, line + f"'{var}' initialization must be a single element."
                assert type.type == _exprs[0].type, line + f"'{var}' initialization type incompatible."     
            elif isinstance(type, ArrayDecl):
                _size = _length
                _head = _exprs
                _decl = type
                while isinstance(type.type, ArrayDecl):
                    type = type.type
                    _length = len(_exprs[0].exprs)  
                    for i in range(len(_exprs)):
                        assert len(_exprs[i].exprs) == _length, line + f"list have different sizes."
                    _exprs = _exprs[0].exprs       
                    if isinstance(type, ArrayDecl):
                        self.setDim(type, _length, line, var) 
                        _size += _length 
                    else:
                        assert _exprs[0].type == type.type.type.names[-1], line + f"'{var}' initialization type incompatible."
                type = _decl
                _exprs = _head
                _length = _size
                if type.dim is None:
                    type.dim = Constant('int', _size)
                    self.visit_Constant(type.dim) 
                else:                  
                 assert type.dim.value == _length, line + f"incompatible size at '{var}' initialization."    
                 
        elif isinstance(init, ArrayRef):
            _id = self.environment.lookup(init.name.name)
            if isinstance(init.subscript, Constant):
                _rtype = _id.type.names[1]
                assert type.type.names[0] == _rtype, line + f"'{var}' initialization type incompatible."   
                
        elif isinstance(init, ID):
            if isinstance(type, ArrayDecl):
                type2 = type.type
                while not isinstance(type2, VarDecl):
                    type2 = type2.type 
                assert type2.type.names == init.type.names, line + f"Initialization type missmatch." 
                self.setDim(type, init.bind.dim.value, line, var)
            else:
                assert type.type.names[-1] == init.type.names[-1], line + f"Initialization type missmatch." 
                 
    def visit_Constant(self, node):
        if not isinstance(node.type, uCType):
            _type = self.typemap[node.rawtype]
            node.type = Type([_type], node.coord)
            if _type.typename == 'int':
                node.value = int(node.value)
            elif _type.typename == 'float':
                node.value = float(node.value)        
     
    def visit_Assignment(self, node): 
        _line = f"{node.coord.line}:{node.coord.column} - "
        self.visit(node.rvalue)
        rtype = node.rvalue.type.names
        _var = node.lvalue
        self.visit(_var)
        if isinstance(_var, ID):
            assert _var.scope is not None, _line + f"'{_var.name}' is not defined."
        ltype = node.lvalue.type.names
        assert ltype == rtype, _line + f"cannot assign '{rtype[0]}' to '{ltype[0]}'."
        assert node.op in ltype[-1].assign_ops, _line + f"operator {node.op} not supported by '{ltype[-1]}'."
            
    def visit_BinaryOp(self, node):
        self.visit(node.left)
        ltype = node.left.type.names[-1]
        self.visit(node.right)
        rtype = node.right.type.names[-1]
        _line = f"{node.coord.line}:{node.coord.column} - "
        assert ltype == rtype, _line + f"binary operator does not have matching '{ltype}'/'{rtype}'."
        if node.op in ltype.binary_ops:
            node.type = Type([ltype], node.coord)
        elif node.op in ltype.rel_ops:
            node.type = Type([self.typemap["bool"]], node.coord)
        else:
            assert False, _line + f"Binary operator '{node.op}' not supported by '{ltype}'."
            
    def visit_Break(self, node):
        _line = f"{npde.coord.line}:{node.coord.column} - "
        assert self.environment.cur_loop != [], _line + "Break statement must be inside a loop block."
        node.bind = self. environment.cur_loop[-1]
     
    def visit_Cast(self, node):
        self.visit(node.expr)
        self.visit(node.to_type)
        node.type = Type(node.to_type.names, node.coord)
       
    def visit_Compound(self, node):
        for item in node.block_items:
            self.visit(item)
    
    def visit_DeclList(self, node):
        for decl in  node.decls:
            self.visit(decl)
            self.environment.funcdef.decls.append(decl)
            
    def visit_EmptyStatement(self, node):
        pass
                
    def visit_For(self, node):
        if isinstance(node.init, DeclList):
            self.environment.push(node)
        self.environment.cur_loop.append(node)
        self.visit(node.init)
        self.visit(node.cond)
        self.visit(node.next)
        self.visit(node.stmt)
        self.environment.cur_loop.pop()
        if isinstance(node.init, DeclList):
            self.environment.pop()
        
    def visit_FuncCall(self, node):
        _line = f"{node.coord.line}:{node.coord.column} - "
        _label = self.environment.lookup(node.name.name)
        assert _label.kind == "func", _line + f"'{_label.name}' is not a function."
        node.type = _label.type
        node.name.type = _label.type
        node.name.bind = _label.bind
        node.name.kind = _label.kind
        node.name.scope = _label.scope
        if node.args is not None:
            _sig = _label.bind
            if isinstance(node.args, ExprList):
                assert len(_sig.args.params) == len(node.args.exprs), _line + f"no. arguments to call '{_label.name}' function incompatible."
                for (_arg, _fpar) in zip(node.args.exprs, _sig.args.params):
                    self.visit(_arg)     
                    _line = f"{node.coord.line}:{node.coord.column} - "
                    if isinstance(_arg, ID):
                        assert self.environment.find(_arg.name), _line + f"'{_arg.name}' is not defined."
                    assert _arg.type.names == _fpar.type.type.names, _line+ f"type mismatch with param '{_fpar.type.declname.name}'." 
            else:
                self.visit(node.args)
                assert len(_sig.args.params) == 1, _line + f"no. arguments to call '{_label.name}' function mismatch."
                _type = _sig.args.params[0].type
                while not isinstance(_type, VarDecl):
                    _type = _type.type
                assert node.args.type.names == _type.type.names, _line + f"type mismath with param '{_sig.args.params[0].name.name}'."
         
    def visit_InitList(self, node):
        for expr in node.exprs:
            self.visit(expr)
      
    def visit_ParamList(self, node):
        for _par in node.params:
            self.visit(_par)
        
    def visit_PtrDecl(self, node):
        self.visit(node.type)
        _type = node.type
        while not isinstance(_type, VarDecl):
            _type = _type.type
        _type.type.names.insert(0, self.typemap["ptr"])
       
    def visit_Return(self, node):   
        if node.expr is not None:
            self.visit(node.expr)
            _type = node.expr.type.names
        else:
            _type = [self.typemap['void']]
        _rtype = self.environment.cur_rtype
        _line = f"{node.coord.line}:{node.coord.column} - "
        assert _type == _rtype, _line + f"return '{_type[0]}' is incompatible with '{_rtype[0]}' function definition."      
            
    def visit_Print(self, node):
        if node.expr is not None:
            self.visit(node.expr)
             
    def visit_Read(self, node):
        for _loc in node.names:
            self.visit(_loc)
            if isinstance(_loc, ID) or isinstance(_loc, ArrayRef):
                self._checkLocation(_loc)
            elif isinstance(_loc, ExprList):
                for _var in loc.exprs:
                    if isinstance(_var, ID) or isinstance(_var, ArrayRef):
                        self._checkLocation(_var)  
                    else:
                        _line = f"{_var.coord.line}:{_var.coord.column} - "
                        assert False, _line + f"'{_var}' is not variable."
            else:
                 _line = f"{_loc.coord.line}:{_loc.coord.column} - "
                 assert False, _line + f"'{_loc}' is not variable."
    
    def _checkLocation(self, var):
        _line = f"{var.coord.line}:{var.coord.column} - "
        _test = (isinstance(var, ArrayRef) and len(var.type.names) == 1)
        _test = _test or isinstance(var, ID)
        _name = var.name
        if isinstance(_name, ArrayRef):
            _name = _name.name.name + "[" + _name.subscript.name + "][" + var.subscript.name +"]"
        elif hasattr(var, 'subscript'):
            _name = _name.name + "[" + var.subscript.name + "]"            
       # assert _test, _line + f"{_name} is not simple variable."
        if isinstance(var, ID):
            assert var.scope is not None, _line + f"type of '{_name}' is not defined."           
        #assert len(var.type.names) == 1, _line + f"type of {_name} is not primitive type."
                  
    def visit_ExprList(self, node):
        for _expr in node.exprs:
            self.visit(_expr)
            if isinstance(_expr, ID):
               _line = f"{_expr.coord.line}:{_expr.coord.column} - "
               assert _expr.scope is not None, _line + "f{_expr.name} is not defined."
               
    def visit_UnaryOp(self, node):
        self.visit(node.expr)
        unaryType = node.expr.type.names[-1]
        _line = f"{node.coord.line}:{node.coord.column} - "
        assert node.op in unaryType.unary_ops, _line + f"unary operator {node.op} not supported."
        node.type = Type(list(node.expr.type.names), node.coord)
        if node.op == "*":
            node.type.names.pop(0)
        elif node.op == "&":
            node.type.names.insert(0, self.typemap["ptr"])
       
    def visit_While(self, node):
        self.visit(node.cond)
        _ctype = node.cond.type.names[0]
        _line = f"{node.coord.line}:{node.coord.column} - "
        assert _ctype == BoolType, _line + f"conditional expression has '{_ctype}', not boolean type."
        if node.stmt is not None:
            self.visit(node.stmt)
        
    def visit_Assert(self, node):
        _expr = node.expr
        self.visit(_expr)
        if hasattr(_expr, "type"):
            assert _expr.type.names[0] == self.typemap["bool"], f"{_expr.coord.line}:{_expr.coord.column} - expression must be boolean type."
        else:
            assert False, f"{_expr.coord.line}:{_expr.coord.column} - expression must be boolean."
    
    def visit_If(self, node):
        self.visit(node.cond)
        _line = f"{node.cond.coord.line}:{node.cond.coord.column} - "   
        if hasattr(node.cond, 'type'):
            assert node.cond.type.names[0] == self.typemap["bool"], _line + "The condition expression must be of the boolean type."        
        else:
            assert False, _line + "The condition expression must be of the boolean type."      
        self.visit(node.iftrue)
        if node.iffalse is not None:
            self.visit(node.iffalse)
