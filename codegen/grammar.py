from lark import Lark
from codegen.parsetree import ParseTree

grammar = """
start : (decl)+

decl : variabledecl
     | functiondecl
     | classdecl
     | interfacedecl

variabledecl : variable ";"

variable : type ident

type : typepri (arr*)?

typepri : int
     | double
     | bool
     | string
     | ident 

arr : "[]"

int : "int"

double : "double" 

bool : "bool"

string : "string"

functiondecl : type ident "(" formals ")" stmtblock
            | void ident "(" formals ")" stmtblock

void : "void"

formals : (variable ( "," variable)*)?


classdecl : "class" ident (extends ident)? (implements ident ("," ident)* )? "{" field* "}"

extends : "extends"

implements : "implements"

field : variabledecl
      | functiondecl

interfacedecl : "interface" ident "{" prototype* "}"

prototype : type ident "(" formals ")" ";"
          | void ident "(" formals ")" ";"

stmtblock : "{" (variabledecl)* (stmt)* "}"

stmt : closestmt
     | openstmt

closestmt : (expr)? ";"
          | ifstmtclose
          | whilestmtclose
          | forstmtclose
          | breakstmt
          | returnstmt
          | printstmt
          | stmtblock

openstmt : ifstmtopen
         | whilestmtopen
         | forstmtopen

ifstmtclose : "if" "(" expr ")" closestmt "else" closestmt

ifstmtopen : "if" "(" expr ")" closestmt "else" openstmt
           | "if" "(" expr ")" stmt

whilestmtopen : "while" "(" expr ")" openstmt

whilestmtclose : "while" "(" expr ")" closestmt

forstmtopen : "for" "(" (expr)? ";" expr ";" (expr)? ")" openstmt

forstmtclose : "for" "(" (expr)? ";" expr ";" (expr)? ")" closestmt

returnstmt : "return" (expr)? ";"

breakstmt : "break" ";"

printstmt : "Print" "(" expr ("," expr)* ")" ";"


expr :  expr1
     | lvalue assign expr

assign : "="

expr1 : expr2 (bitor expr2)*

bitor : "||"

expr2 : expr3 (bitand expr3)*

bitand : "&&"

expr3 : expr4  ((nequal | equal) expr4)*

equal : "=="

nequal : "!="

expr4 : expr5 ( (grq | gr | le | leq) expr5)* 

le : "<"

leq : "<="

gr : ">"

grq : ">="

expr5 : expr6 ( (sub | add) expr6 )*

add : "+"

sub : "-"

expr6 : expr7 ( (mul | div | mod ) expr7)*

mul : "*"

div : "/"

mod : "%"

expr7 : expr8 ( (not | neg) expr7)*

neg : "-"

not : "!"

expr8 : constant
     | lvalue
     | this
     | call 
     | readint "(" ")"
     | readline "(" ")"
     | new ident
     | newarray "(" expr "," type ")"
     |parop expr parcl

new : "new"

readint : "ReadInteger"

readline : "ReadLine"

newarray : "NewArray"

parop : "("

parcl : ")"

this : "this"

lvalue : ident
       | expr8 dot ident 
       | expr8 arin expr arout

dot : "."

arin : "["

arout : "]"

call : ident "(" actuals ")" 
     | expr8 dot ident "(" actuals ")"  

actuals : expr ("," expr)*
        |

constant : intconstant
         | doubleconstant
         | boolconstant
         | stringconstant
         | null

null : "null"

boolconstant : false
             | true

true : "true"

false : "false"

intconstant : integer
            | hexint

integer : /[0-9]+/

hexint : /0[xX][0-9a-fA-f]+/

stringconstant : /"[^"\\n]*"/

doubleconstant : /[0-9]+\\.[0-9]*([eE][+-]?[0-9]+)?/

ident : /(?!for|false|true|null|this|NewArray|new|ReadLine|ReadInteger|Print|break|return|while|if|void|class|string|bool|double|int|interface|extends|implements|else)[a-zA-Z][a-zA-Z0-9_]{,30}|for[a-zA-Z0-9_]{1,28}|false[a-zA-Z0-9_]{1,26}|true[a-zA-Z0-9_]{1,27}|null[a-zA-Z0-9_]{1,27}|this[a-zA-Z0-9_]{1,27}|NewArray[a-zA-Z0-9_]{1,23}|new[a-zA-Z0-9_]{1,28}|ReadLine[a-zA-Z0-9_]{1,23}|ReadInteger[a-zA-Z0-9_]{1,20}|Print[a-zA-Z0-9_]{1,26}|break[a-zA-Z0-9_]{1,26}|return[a-zA-Z0-9_]{1,25}|while[a-zA-Z0-9_]{1,26}|if[a-zA-Z0-9_]{1,29}|void[a-zA-Z0-9_]{1,27}|class[a-zA-Z0-9_]{1,26}|string[a-zA-Z0-9_]{1,25}|bool[a-zA-Z0-9_]{1,27}|double[a-zA-Z0-9_]{1,25}|int[a-zA-Z0-9_]{1,28}|interface[a-zA-Z0-9_]{1,22}|extends[a-zA-Z0-9_]{1,24}|implements[a-zA-Z0-9_]{1,21}|else[a-zA-Z0-9_]{1,27}/

SINGLE_LINE_COMMENT : /\/\/[^\\n]*\\n/
MULTI_LINE_COMMENT : /\/\*([^\\*]|(\*)+[^\\*\\/])*(\*)+\//

%import common.WS -> WHITESPACE
%ignore WHITESPACE
%ignore SINGLE_LINE_COMMENT
%ignore MULTI_LINE_COMMENT

"""
keyWords = ['void', 'int', 'double', 'bool', 'string', 'class', 'interface', 'null', 'this', 'extends', 'implements',
            'for', 'while', 'if', 'else', 'return', 'break', 'new', 'NewArray', 'Print', 'ReadInteger', 'ReadLine']

parser = Lark(grammar, parser='lalr', debug=False)
code = ""
for i in range(5):
    code += input()
x = parser.parse(code)
y = ParseTree(x)
print(y)
s = 0
for j in y.nodes:
    print(s, " ", j)
    s += 1
