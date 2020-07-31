from uc_ast import *
from uc_sema import *

class GenerateCode(NodeVisitor):
    '''
    Node visitor class that creates 3-address encoded instruction sequences.
    '''
    def __init__(self):
        super(GenerateCode, self).__init__()

        # version dictionary for temporaries
        self.fname = '_glob_'  # We use the function name as a key
        self.versions = {self.fname: 0}

        self.text = []
        self.code = [] 
        
        self.binary_opcodes = {"+": "add", "-": "sub", "*": "mul", "/": "div", 
                               "%": "mod", "==": "eq", "!=": "ne", "<": "lt",
                               ">": "gt", "<=": "le", ">=": "ge", "&&": "and",
                               "||": "or"}
        
        self.unary_opcodes = {"-": "sub", "+": "", "--": "sub", "++": "add", 
                              "p--": "sub", "p++": "add", "!": "not",
                              "*": "", "&": ""}
        
        self.assign_opcodes = {"+=": "add", "-=": "sub", "*=": "mul", "/=": 
                               "div", "%=": "mod"}

        self.alloc_phase = None
        self.items = []
        self.ret_location = None
        self.ret_label = None
        
    def new_temp(self):
        '''
        Create a new temporary variable of a given scope (function name).
        '''
        if self.fname not in self.versions:
            self.versions[self.fname] = 0
        name = "%" + "%d" % (self.versions[self.fname])
        self.versions[self.fname] += 1
        return name

    def new_text(self):
        name = "@.str." + "%d" % (self.versions['_glob_'])
        self.versions['_glob_'] += 1
        return name        
   
    def clean(self):
        self.items = []

    def enqueue(self, item):
        self.items.insert(0, item)

    def dequeue(self):
        return self.items.pop()
 
    def visit_VarDecl(self, node, decl, dim):
        if node.declname.scope == 1:
            self.global_location(node, decl, dim)  
        else:
            typename = node.type.names[-1].typename + dim
            if self.alloc_phase == 'arg_decl' or self.alloc_phase == 'var_decl':
                varname = self.new_temp()
                self.code.append(('alloc_' + typename, varname))
                node.declname.gen_location = varname
                decl.name.gen_location = varname               
            elif self.alloc_phase == 'arg_init':
                self.code.append(('store_' + typename, self.dequeue(), node.declname.gen_location))
                
            elif self.alloc_phase == 'var_init':
                if decl.init is not None:
                    self.store_location(typename, decl.init, node.declname.gen_location)
    
    def visit_ArrayDecl(self, node, decl, dim):
        _type = node
        dim += "_" + str(node.dim.value)
        while not isinstance(_type, VarDecl):
            _type = _type.type
            if isinstance(_type, ArrayDecl):
                dim += "_" + str(_type.dim.value)
            elif isinstance(_type, PtrDecl):
                dim += "_*"
        self.visit_VarDecl(_type, decl, dim)
      
    def visit_ArrayRef(self, node):
        subs_j = node.subscript
        self.visit(subs_j)
        if isinstance(node.name, ArrayRef):
            subs_i = node.name.subscript
            self.visit(subs_i)
            dim = node.name.name.bind.type.dim
            self.visit(dim)
            if isinstance(subs_i, ID) or isinstance(subs_i, ArrayRef):
                self.load_location(subs_i)
            target = self.new_temp()
            self.code.append(('mul_' + node.type.names[-1].typename, dim.gen_location, subs_i.gen_location, target))
            if isinstance(subs_j, ID) or isinstance(subs_j, ArrayRef):
                self.load_location(subs_j)
            idx = self.new_temp()
            self.code.append(('add_' + node.type.names[-1].typename, target, subs_j.gen_location, idx))
            var = node.name.name.bind.type.type.declname.gen_location
            node.gen_location = self.new_temp()
            self.code.append(('elem_' + node.type.names[-1].typename, var, idx, node.gen_location))  
        else:
            if isinstance(subs_j, ID) or isinstance(subs_j, ArrayRef):
                self.load_location(subs_j)
                var = node.name.bind.type.declname.gen_location
                idx = subs_j.gen_location
                target = self.new_temp()
                node.gen_location = target
                self.code.append(('elem_' + node.type.names[-1].typename, var, idx, target))     
       
    def visit_Assignment(self, node): 
        rval = node.rvalue
        self.visit(rval)
        if isinstance(rval, ID) or isinstance(rval, ArrayRef):
            self.load_location(rval)
        elif isinstance(rval, UnaryOp) and rval.op == "*":      
            self.load_reference(rval)     
        lvar =  node.lvalue
        self.visit(lvar)
        if node.op in self.assign_opcodes:
            lval = self.new_temp()
            target = self.new_temp()
            typename = lvar.type.names[-1].typename 
            if isinstance(rval, ArrayRef):
                typename += "_*"
            self.code.append(('load_' + typename, lvar.gen_location, lval))            
            self.code.append((self.assign_opcodes[node.op] + '_' + lvar.type.names[-1].typename, node.rvalue.gen_location, lval, target))      
            self.code.append(('store_' + lvar.type.names[-1].typename, target, lvar.gen_location))
        else:
            if isinstance(lvar, ID) or isinstance(lvar, ArrayRef):
                typename = lvar.type.names[-1].typename
                if isinstance(lvar, ArrayRef):
                    typename += '_*'
                elif isinstance(lvar.bind, ArrayDecl):
                    typename += '_' + str(lvar.bind.dim.value)
                elif lvar.type.names[0] == PtrType:
                    if lvar.kind == 'func':
                        lvar.bind.type.gen_location = lvar.gen_location
                    typename += '_*'
                    self.code.append(('get_' + typename, node.rvalue.gen_location, lvar.gen_location))
                    return
                self.code.append(('store_' + typename, node.rvalue.gen_location, lvar.gen_location))
            else:
                typename = lvar.type.names[-1].typename
                if isinstance(lvar, UnaryOp):
                    if lvar.op == '*':
                        typename += '_*'
                    self.code.append(('store_' + typename, node.rvalue.gen_location, lvar.gen_location))
                           
    def visit_BinaryOp(self, node):
        self.visit(node.left)
        self.visit(node.right)   
        if isinstance(node.left, ID) or isinstance(node.left, ArrayRef):
            self.load_location(node.left)
        elif isinstance(node.left, UnaryOp) and node.left.op == "*":
            self.load_reference(node.left)
        if isinstance(node.right, ID) or isinstance(node.right, ArrayRef):
            self.load_location(node.right)    
        elif isinstance(node.right, UnaryOp) and node.right.op == "*":
            self.load_reference(node.right)  
        target = self.new_temp()
        opcode = self.binary_opcodes[node.op] + "_" + node.left.type.names[-1].typename
        self.code.append((opcode, node.left.gen_location, node.right.gen_location, target))
        node.gen_location = target
      
    def visit_Break(self, node):
        self.code.append(('jump', node.bind.exit_label))
                
    def visit_Cast(self, node):
        self.visit(node.expr)
        if isinstance(node.expr, ID) or isinstance(node.expr, ArrayRef):
            self.load_location(node.expr)
        temp = self.new_temp()
        if node.to_type.names[-1].typename == IntType.typename:
            inst = ('fptosi', node.expr.gen_location, temp)
        else:
            inst = ('sitofp', node.expr.gen_location, temp)
        self.code.append(inst)
        node.gen_location = temp
            
    def visit_Compound(self, node):
        for item in node.block_items:
            self.visit(item)
    
    def visit_Constant(self, node):
        if node.rawtype == 'string':
            target = self.new_text()
            self.text.append(('global_string', target, node.value))
        else:
            target = self.new_temp()
            self.code.append(('literal_' + node.rawtype, node.value, target))
        node.gen_location = target
  
    def visit_Decl(self, node):
        _type = node.type
        dim = ""
        if isinstance(_type, VarDecl):
            self.visit_VarDecl(_type, node, dim)
        elif isinstance(_type, ArrayDecl):
            self.visit_ArrayDecl(_type, node, dim)
        elif isinstance(_type, PtrDecl):
            self.visit_PtrDecl(_type, node, dim)
        elif isinstance(_type, FuncDecl):
            self.visit_FuncDecl(_type)
  
    def visit_DeclList(self, node):
        for decl in node.decls:
            self.visit(decl)
     
    def visit_EmptyStatement(Node):
        pass
     
    def visit_ExprList(Node):
        pass       
      
    def visit_For(self, node):
        entry_label = self.new_temp()
        body_label = self.new_temp()
        exit_label = self.new_temp()
        node.exit_label = exit_label
        self.visit(node.init)
        self.code.append((entry_label[1:],))
        self.visit(node.cond)
        self.code.append(('cbranch', node.cond.gen_location, body_label, exit_label))
        self.code.append((body_label[1:],))
        self.visit(node.stmt)
        self.visit(node.next)
        self.code.append(('jump', entry_label))
        self.code.append((exit_label[1:],))       
      
    def visit_FuncCall(self, node):
        if node.args is not None:
            if isinstance(node.args, ExprList):
                tcode = []
                for arg in node.args.exprs:
                    self.visit(arg)
                    if isinstance(arg, ID) or isinstance(arg, ArrayRef):
                        self.load_location(arg)   
                    inst = ('param_' + arg.type.names[-1].typename, arg.gen_location)
                    tcode.append(inst)
                for inst in tcode:
                    self.code.append(inst)
            else:
                self.visit(node.args)
                if isinstance(node.args, ID) or isinstance(node.args, ArrayRef):  
                    self.load_location(node.args)
                self.code.append(('param_' + node.args.type.names[-1].typename, node.args.gen_location))
  
        if isinstance(node.name.bind, PtrDecl):
            target = self.new_temp()
            self.code.append(('load_' + node.type.names[-1].typename + '_*', node.name.bind.type.gen_location, target))
            node.gen_location = self.new_temp()
            self.code.append(('call', target, node.gen_location))          
        else:
            node.gen_location = self.new_temp()
            self.visit(node.name)
            self.code.append(('call', '@' + node.name.name, node.gen_location))
     
    def visit_FuncDecl(self, node):
        self.fname = '@' + node.type.declname.name
        self.code.append(('define', self.fname))
        node.type.declname.gen_location = self.fname
        if node.args is not None:
            self.clean()
            for _ in node.args.params:
                self.enqueue(self.new_temp())          
        self.ret_location = self.new_temp()
        self.alloc_phase = 'arg_decl'
        if node.args is not None:
            for arg in node.args:
                self.visit(arg)
        self.ret_label = self.new_temp()
        self.alloc_phase = 'arg_init'
        if node.args is not None:
            for arg in node.args:
                self.visit(arg)
       
    def visit_FuncDef(self, node):
        self.alloc_phase = None
        self.visit(node.decl)
        if node.param_decls is not None:
            for par in node.param_decls:
                self.visit(par)

        if node.body is not None:
            self.alloc_phase = 'var_decl'
            for body in node.body:
                if isinstance(body, Decl):
                    self.visit(body)        
            for decl in node.decls:
                self.visit(decl)
            self.alloc_phase = 'var_init'
            for body in node.body:
                self.visit(body)
        self.code.append((self.ret_label[1:],))
        if node.spec.names[-1].typename == 'void':
            self.code.append(('return_void',))
        else:
            rvalue = self.new_temp()
            self.code.append(('load_' + node.spec.names[-1].typename, self.ret_location, rvalue))
            self.code.append(('return_' + node.spec.names[-1].typename, rvalue))
                 
    def visit_ID(self, node):  
        if node.gen_location is None:
            _type = node.bind
            while not isinstance(_type, VarDecl):
                _type = _type.type 
            if _type.declname.gen_location is None:
                if node.kind == 'func' and node.scope == 1:
                    node.gen_location = '@' + node.name
            else:
                node.gen_location = _type.declname.gen_location
      
    def visit_If(self, node):
        true_label = self.new_temp()
        false_label = self.new_temp()
        exit_label = self.new_temp()
        self.visit(node.cond)
        self.code.append(('cbranch', node.cond.gen_location, true_label, false_label))
        self.code.append((true_label[1:],))
        self.visit(node.iftrue)
        if node.iffalse is not None:
            self.code.append(('jump', exit_label))
            self.code.append((false_label[1:],))
            self.visit(node.iffalse)
            self.code.append((exit_label[1:],))
        else:
            self.code.append((false_label[1:],))
            
    def visit_InitList(self, node):
        node.value = []
        for expr in node.exprs:
            if isinstance(expr, InitList):
                self.visit(expr)
            node.value.append(expr.value)     
 
    def visit_ParamList(self, node):
        for param in node.param_decls:
                self.visit(param)      
   
    def visit_GlobalDecl(self, node):
        for decl in node.decls:
            if not isinstance(decl.type, FuncDecl):
                self.visit(decl)  
    
    def visit_PtrDecl(self, node, decl, dim):
        _type = node
        dim += "_*"
        while not isinstance(_type, VarDecl):
            _type = _type.type
            if isinstance(_type, PtrDecl):
                dim += "_*"
            elif isinstance(_type, ArrayDecl):
                dim += "_" + str(_type.dim.value)
        self.visit_VarDecl(_type, decl, dim)
     
    def visit_Return(self, node):
         if node.expr is not None:
            self.visit(node.expr)
            if isinstance(node.expr, ID) or isinstance(node.expr, ArrayRef):
                self.load_location(node.expr)
            self.code.append(('store_' + node.expr.type.names[-1].typename, node.expr.gen_location, self.ret_location))
         self.code.append(('jump', self.ret_label))
             
    def visit_UnaryOp(self, node):
        self.visit(node.expr)
        source = node.expr.gen_location

        if node.op == '&':
            node.gen_location = node.expr.gen_location
        elif node.op == '*':
            node.gen_location = self.new_temp()
            self.code.append(('load_' + node.expr.type.names[-1].typename + '_*', node.expr.gen_location.node.gen_location))
        else:
            if isinstance(node.expr, ID) or isinstance(node.expr, ArrayRef):
                self.load_location(node.expr)
                
            if node.op == '+':
                node.gen_location = node.expr.gen_location
                
            elif node.op == '-':
                opcode = self.unary_opcodes[node.op] + "_" + node.expr.type.names[-1].typename
                node.gen_location = node.new_temp()
                self.code.append((opcode, 0, node.expr.gen_location, node.gen_location))
            elif node.op in ["++", "p++", "--", "p--"]:
                if node.op == "++" or node.op == "p++":
                    val = 1
                else:
                    val = -1
                value = self.new_temp()
                self.code.append(('literal_int', val, value))
                opcode = self.unary_opcodes[node.op] + "_" + node.expr.type.names[-1].typename
                node.gen_location = self.new_temp()
                self.code.append((opcode, node.expr.gen_location, value, node.gen_location))                 
                opcode = 'store_' + node.expr.type.names[-1].typename
                self.code.append((opcode, node.gen_location, source))
                if node.op in ["p++", "p--"]:
                    node.gen_location = node.expr.gen_location
                      
    def visit_While(self, node):
        entry_label = self.new_temp()
        true_label = self.new_temp()
        exit_label = self.new_temp()
        node.exit_label = exit_label
        self.code.append((entry_label[1:],))
        self.visit(node.cond)
        self.code.append(('cbranch', node.cond.gen_location, true_label, exit_label))
        self.code.append((true_label[1:],))
        if node.stmt is not None:
            self.visit(node.stmt)
        self.code.append(('jump', entry_label))
        self.code.append((exit_label[1:],))
     
    def visit_Type(Node):
        pass
                          
    def visit_Program(self, node):   
        for decl in node.gdecls:
            self.visit(decl)
        self.code = self.text + self.code 
                 
    def visit_Print(self, node):
         if node.expr is not None:
            if isinstance(node.expr[0], ExprList):
                for expr in node.expr[0].exprs:
                    self.visit(expr)                    
                    if isinstance(expr, ID) or isinstance(expr, ArrayRef):
                        self.load_location(expr)

                    elif isinstance(expr, UnaryOp) and expr == "*":
                        self.load_location(expr)
                    self.code.append(('print_' + expr.type.names[-1].typename, expr.gen_location))
         else:
            self.code.append(('print_void',))
    
    def visit_Read(self, node):
        for loc in node.names:
            self.visit(loc)      
            if isinstance(loc, ID) or isinstance(loc, ArrayRef):
                    self.read_location(loc)
            elif isinstance(loc, ExprList):
                    for var in loc.exprs:
                        self.visit(var)
                        self.read_location(var)
                                     
    def visit_Assert(self, node):
        expr = node.expr
        self.visit(expr)
        true_label = self.new_temp()
        false_label = self.new_temp()
        exit_label = self.new_temp()
        self.code.append(('cbranch', expr.gen_location, true_label, false_label))
        self.code.append((true_label[1:],))
        self.code.append(('jump', exit_label))
        self.code.append((false_label[1:],))
        target = self.new_text()
        line = node.expr.coord.line
        col = node.expr.coord.column
        self.text.append(('global_string', target, "assertion_fail on " + f"{line}:{col}"))
        self.code.append(('print_string', target))
        self.code.append(('jump', self.ret_label))
        self.code.append((exit_label[1:],))
      
    def global_location(self, node, decl, dim):
        _type = node.type.names[-1].typename
        if dim is not None:
            _type += dim
        varname = "@" + node.declname.name
        if decl.init is None:
            self.text.append(('global_' + _type, varname))
        elif isinstance(decl.init, Constant):
            self.text.append(('global_' + _type, varname, decl.init.value))
        elif isinstance(decl.init, InitList):
            self.visit(decl.init)
            self.text.append(('global_' + _type, varname, decl.init.value))
        node.declname.gen_location = varname
       
    def load_location(self, node):
        varname = self.new_temp()
        typename = node.type.names[-1].typename
        if isinstance(node, ArrayRef):
            typename += '_*'     
        elif isinstance(node.bind, ArrayDecl):
            typename += '_' + str(node.bind.dim.value)
        self.code.append(('load_' + typename, node.gen_location, varname))
        node.gen_location = varname
        
    def store_location(self, typename, init, target):
        self.visit(init)
        if isinstance(init, ID) or isinstance(init, ArrayRef):
            self.load_location(init)
        elif isinstance(init, UnaryOp) and init.op == '*':
            self.load_reference(init)
        self.code.append(('store_' + typename, init.gen_location, target))
        
    def read_location(self, source):
        target = self.new_temp()
        typename = source.typenames[-1].typename
        self.code.append(('read_' + typename, target))
        if isinstance(source, ArrayRef):
            typename += "_*"
        if isinstance(source, UnaryOp) and source.op == "*":
            self.load_reference(source)
        self.code.append(('store_' + typename, target, source.gen_location))        
    
    def load_reference(self, node):
        node.gen_location = self.new_temp()
        self.code.append(('load_' + node.expr.type.names[-1].typename + "_*", node.expr.gen_location, node.gen_location))
        
