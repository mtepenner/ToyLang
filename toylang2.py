# Matthew Penner
#

# CS358 Fall'24 Assignment 4 (Part B)
#
# ToyLang - an imperative language with lambda functions
#
#   prog -> stmt
#
#   stmt -> "var" ID "=" expr
#         | "print" "(" expr ")"
#         | "{" stmt (";" stmt)* "}" 
#
#   expr -> "lambda" ID ":" expr
#         | expr "(" expr ")"
#         | aexpr 
#
#   aexpr -> aexpr "+" term
#          | aexpr "-" term
#          | term         
#
#   term -> term "*" atom
#         | term "/" atom
#         | atom
#
#   atom: "(" expr ")"
#         | ID
#         | NUM
#
from lark import Lark, v_args, Tree
from lark.visitors import Interpreter
import copy
debug = False

grammar = """
  ?start: stmt

  stmt: "var" ID "=" expr         -> decl
       | "def" ID "(" ID ")" "=" body  -> funcdecl
       | ID "=" expr               -> assign
       | "if" "(" expr ")" stmt ["else" stmt] -> ifstmt
       | "while" "(" expr ")" stmt -> whstmt
       | "print" "(" expr ")"      -> prstmt
       | "{" stmt (";" stmt)* "}"  -> block      

  ?expr: "lambda" ID ":" expr      -> func
       | expr "(" expr ")"         -> call
       | aexpr 

  ?aexpr: aexpr "+" term  -> add
       |  aexpr "-" term  -> sub
       |  term         

  ?term: term "*" atom  -> mul
       | term "/" atom  -> div
       | atom

  ?atom: "(" expr ")"
       | ID             -> var
       | NUM            -> num

  ?body: "{" (stmt ";")* "return" expr "}" -> body

  %import common.WORD   -> ID
  %import common.INT    -> NUM
  %import common.WS
  %ignore WS
"""

parser = Lark(grammar, parser='lalr')

# Variable environment
#
class Env(dict):
    prev = []
    def openScope(self):
        self.prev.insert(0,self)
        return Env()
    def closeScope(self):
        return self.prev.pop(0)
    def extend(self,x,v):
        assert not x in self, "Variable already defined: " + x
        self[x] = v
    def lookup(self,x):
        if x in self: return self[x]
        for envi in self.prev:
            if x in envi: return envi[x]
        raise Exception("Variable undefined: " + x)
    def retract(self,x):
        assert x in self, "Undefined variable: " + x
        self[x].pop(0)
    def update(self,x,v):
        if x in self: self[x] = v; return
        for envi in self.prev:
            if x in envi: envi[x] = v; return
        raise Exception("Variable undefined: " + x)
env = Env()

# Closure
#
class Closure():
    def __init__(self,id,body,env):
        self.id = id
        self.body = body
        self.env = env

# Interpreter
#
@v_args(inline=True)
class Eval(Interpreter): 
    def __init__(self):
        super().__init__()
        self.env = env

    def num(self, val):  
        return int(val)

    # ... need code
    def var(self, name):
        return env.lookup(name)
    
    def decl(self, name, value):
        evaluated_value = self.visit(value)
        env.extend(name, evaluated_value)
    
    def assign(self, name, value):
        evaluated_value = self.visit(value)
        env.update(name, evaluated_value)

    def prstmt(self, value):
        result = self.visit(value)
        print(result)

    def block(self, *stmts):
        env.openScope()
        for stmt in stmts:
            self.visit(stmt)
        env.closeScope()
    
    def ifstmt(self, condition, true_stmt, false_stmt=None):
        if self.visit(condition):
            self.visit(true_stmt)
        elif false_stmt is not None:
            self.visit(false_stmt)

    def whstmt(self, condition, body):
        while self.visit(condition):
            self.visit(body)

    def add(self, left, right):
        left_val = self.visit(left)
        right_val = self.visit(right)
        return left_val + right_val

    def sub(self, left, right):
        left_val = self.visit(left)
        right_val = self.visit(right)
        return left_val - right_val

    def mul(self, left, right):
        left_val = self.visit(left)
        right_val = self.visit(right)
        return left_val * right_val

    def div(self, left, right):
        left_val = self.visit(left)
        right_val = self.visit(right)
        return left_val // right_val

    def func(self, name, body):
        return Closure(name, body, env)

    def call(self, func, arg):
        global env 
        closure = self.visit(func)
        argv = self.visit(arg)
        env = closure.env.openScope()  
        env.extend(closure.id, argv)
        result = self.visit(closure.body)
        env = env.closeScope()
        return result

    def funcdecl(self, name, param, body):
        closure = Closure(param, body, env.openScope())
        env.extend(name, closure)

    def body(self, *stmts):
        for stmt in stmts[:-1]:
            self.visit(stmt)
        return self.visit(stmts[-1])

   
import sys
def main():
    try:
        prog = sys.stdin.read()
        tree = parser.parse(prog)
        print(prog, end="")
        Eval().visit(tree)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()

