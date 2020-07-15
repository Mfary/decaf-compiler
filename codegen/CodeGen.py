from codegen.grammar import parseTree
from codegen.Utils import Variable, Address, SymbolTable, Type, AttName
from codegen.parsetree import Node
from codegen.Error import error
from codegen.Error import TypeError

used_labels = 1
disFp = -4  ### always we have $sp = $fp + disFp.

symbolTable = SymbolTable(False)


def emit_jump(label):
    emit("j " + label)


def emit_label(label):
    emit(label + " :")


def emit_load(dst, src, offset=0):
    emit("lw " + dst + ", " + str(offset) + "(" + src + ")")


def emit_load_double(dst, src, offset=0):
    emit("l.d " + dst + ", " + str(offset) + "(" + src + ")")


def emit_li(dst, val):
    emit("li " + dst + ", " + str(val))


def emit_syscall():
    emit("syscall")


def align_stack(top):
    global disFp
    if top != disFp:
        emit("addi $sp, $sp, " + str(top - disFp))
        disFp = top


def create_label():
    global used_labels
    num = used_labels
    arr = []
    while num != 0:
        s = num % 27
        num //= 27
        arr.append(chr(s + ord('A')))
    arr.append("_")
    used_labels += 1
    return "".join(arr)[::-1]


def emit(st):
    print(st)


def cgen_if1(expr, stmt1, stmt2):
    global disFp
    l1 = create_label()
    l2 = create_label()
    top = disFp
    t1 = cgen_expr(expr)
    if t1.attribute["type"] != "bool":
        print("Error")
        exit(2)
    t1.attribute["address"].load_address()
    emit("lw $t0, 0($s0)")
    align_stack(top)
    emit("beqz $t0, " + l1)
    cgen_stmt(stmt1)
    align_stack(top)
    emit("j " + l2)
    emit(l1 + ":")
    cgen_stmt(stmt2)
    align_stack(top)
    emit(l2 + ":")
    return


def cgen_if2(expr, stmt):
    global disFp
    l1 = create_label()
    top = disFp
    t1 = cgen_expr(expr)
    if t1.attribute["type"] != 'bool':
        print("Error")
        exit(2)
    t1.attribute["address"].load_address()
    emit("lw $t0, 0($s0)")
    align_stack(top)
    emit("beqz $t0, " + l1)
    cgen_stmt(stmt)
    align_stack(top)
    emit(l1 + ":")
    return


def cgen_while(node):
    global disFp
    expr = parseTree.nodes[node].child[0]
    stmt = parseTree.nodes[node].child[1]
    top = disFp
    l1 = create_label()
    l2 = create_label()
    parseTree.nodes[node].attribute["ex_label"] = l2
    t = cgen_expr(expr)
    if t.attribute["type"] != 'bool':
        print("Error!")
        exit(2)
    emit(l1 + ":")
    t.attribute["address"].load_address()
    emit("lw $t0, 0($s0)")
    align_stack(top)
    emit("beqz $t0, " + l2)
    cgen_stmt(stmt)
    align_stack(top)
    emit("j " + l1)
    emit(l2 + ":")
    return


def cgen_for(node):
    nod = parseTree.nodes[node]
    expr1 = nod.child[0]
    expr2 = nod.child[1]
    expr3 = nod.child[2]
    stm = nod.child[3]
    global disFp
    top = disFp
    l1 = create_label()
    l2 = create_label()
    parseTree.nodes[node].attribute["ex_label"] = l2
    cgen_expr(expr1)
    align_stack(top)
    emit(l1 + ":")
    t = cgen_expr(expr2)
    if t.attribute["type"] != 'bool':
        print("Error!")
        exit(2)
    t.attribute["address"].load_address()
    emit("lw $t0, 0($s0)")
    align_stack(top)
    emit("beqz $t0, " + l2)
    cgen_stmt(stm)
    align_stack(top)
    cgen_expr(expr3)
    align_stack(top)
    emit("j " + l1)
    emit(l2 + ":")
    return


# get type of a type node
def get_type(type_id):
    node = parseTree.nodes[type_id]
    type_pri_id = node.child[0]
    node = parseTree.node[type_pri_id]
    type_id_direct = node.child[0]
    node = parseTree.nodes[type_id_direct]
    return node.data
    pass


def get_name(ident_id):
    node = parseTree.nodes[ident_id]
    ident_id_direct = node.child[0]
    node = parseTree.nodes[ident_id_direct]
    return node.data
    pass


def cgen_variable(variable_id):
    node = parseTree.node[variable_id]
    type_id = node.child[0]
    ident_id = node.child[1]
    type = get_type(type_id)
    name = get_name(ident_id)
    return name, type


def cgen_variable_decl(node_id):
    global disFp, symbolTable
    node = parseTree.nodes[node_id]
    variable_id = node.child[0]
    name, type = cgen_variable(variable_id)
    symbolTable.add_variable(type, name)
    if type == "double":
        disFp -= 8
        emit("addi $sp, $sp, -8")
    else:
        disFp -= 4
        emit("addi $sp, $sp, -4")
    return


def cgen_readline(node):  # after calling this function address of the string is in $S0
    emit("addi $s3, $sp, 0")  # $s3 saves top of stack
    emit_li("$v0", 8)
    emit_li("$a1", 1)  # length of read (1 byte)
    emit_li("$s1", ord("\n"))
    l1 = create_label()
    l2 = create_label()
    emit_label(l1)
    emit("addi $sp, $sp, -1")
    emit("addi $a0, $sp, 0")
    emit_syscall()  # read one char and store in top of stack
    emit("lbu $s0, 0($sp)")
    emit("bneq $s0, $s1, " + l1)  # check the end of line
    emit("sub $a0, $s3, $sp")
    emit("addi $a0, $a0, 1")  # amount ot get memory
    emit_li("$v0", 9)
    emit_syscall()  # first of allocated memory is in $v0
    emit("addi $v1, $v0, 0")  # store address of string in v1 (don't change this reg!)
    emit("addi $a0, $a0, -1")
    emit("addi $sp, $s3, -1")
    emit_label(l2)
    emit("lbu $s0, 0($sp)")
    emit("sb $s0, 0($v0)")
    emit("addi $v0, $v0, 1")
    emit("addi $sp, $sp, -1")
    emit("addi $a0, $a0, -1")
    emit("bnez $a0, l2")  # check that all characters have benn writen
    # TODO : store a zero character at "0($v0)". I don't know how to do it.
    emit("addi $s0, $v1, 0")
    emit("addi $sp, $s3, 0")
    node.attribute["type"] = "string"
    return node


def cgen_readint(node):
    global disFp
    disFp -= 4
    emit("li $v0, 5")
    emit("syscall")
    emit("sw $v0, " + str(disFp) + "($fp)")
    emit("addi $s0, $fp, " + str(disFp))
    node.attribute["type"] = "integer"
    return node


def cgen_call(node):
    pass


def cgen_this(node):
    pass


def cgen_lvalue(node):
    pass


def cgen_constant_int(node):
    expr_set_node_attributes(node, Type.bool)
    child = node.ref_child[0]

    value = child.data
    if node.data == 'integer':
        value = int(value, 10)
    else:
        value = int(value, 16)

    emit('lui $s0, ' + str(value // (2 ** 16)))
    emit('addiu $s0, $s0, ' + str(value % (2 ** 16)))

    node.attribute[AttName.address].store()
    return node


def cgen_constant_double(node):
    pass


def cgen_constant_bool(node):
    expr_set_node_attributes(node, Type.bool)
    child = node.ref_child[0]

    if child.data == 'true':
        emit("li $s0, 1")
    elif child.data == 'false':
        emit("li $s0, 0")

    node.attribute[AttName.address].store()
    return node


def cgen_constant_string(node):
    pass


def cgen_constant_null(node):
    pass


def cgen_constant(node):
    child = node.ref_child[0]

    if child.data == 'intconstant':
        return cgen_constant_int(child.ref_child[0])
    elif child.data == 'doubleconstant':
        return cgen_constant_double(child)
    elif child.data == 'boolconstant':
        return cgen_constant_bool(child)
    elif child.data == 'stringconstant':
        return cgen_constant_string(child)
    elif child.data == 'null':
        return cgen_constant_null(child)


def cgen_expr_not(node):
    child = cgen_expr(node.child[1])

    if child.attribute[AttName.type] != Type.bool:
        raise TypeError("in node: \n" + node.__repr__() + "\n expr's type is not bool.")

    child_address = child.attribute[AttName.address]
    child_address.load()

    emit("li $t0, 1")
    emit("sub $s0, $t0, $s0")

    child_address.store()

    return child


def cgen_expr_neg(node):
    child = cgen_expr(node.child[1])
    child_type = child.attribute[AttName.type]
    child_address = child.attribute[AttName.address]
    child_address.load()

    if child_type == Type.int:
        emit("sub $s0, $zero, $s0")
    elif child_type == Type.double:
        emit("neg.d $f0, $f0")
    else:
        raise TypeError("in node: \n" + node.__repr__() + "\n expr's type is not int or double.")

    child_address.store()
    return child


def cgen_expr_new(node):
    pass


def cgen_newarray(node):
    pass


def cgen_expr_assign(node):
    pass


def expr_set_node_attributes(node, type):
    global disFp
    emit("addi $sp, -4")
    disFp -= 4

    if type == Type.double:
        emit("addi $sp, -4")
        disFp -= 4

    node.attribute[AttName.address] = Address(disFp, 0)
    node.attribute[AttName.type] = type


def expr_or_and(node, operation):
    # operation = 'and' or 'or'
    expr_set_node_attributes(node, Type.bool)
    address = node.attribute[AttName.address]

    left_child = cgen_expr(node.child[0])
    right_child = cgen_expr(node.child[2])

    if left_child.attribute[AttName.type] != Type.bool or right_child.attribute[AttName.type] != Type.bool:
        raise TypeError("in node: \n" + node.__repr__() + "\n one of exprs' type is not bool.")

    left_child_address = left_child.attribute[AttName.address]
    right_child_address = right_child.attribute[AttName.address]

    left_child_address.load()
    emit("move $s1, $s0")
    right_child_address.load()
    emit(operation + " $s0, $s0, $s1")
    address.store()

    return node


def cgen_expr_bitor(node):
    return expr_or_and(node, 'or')


def cgen_expr_bitand(node):
    return expr_or_and(node, 'and')


def cgen_expr_equal(node):
    expr_set_node_attributes(node, Type.bool)
    address = node.attribute[AttName.address]

    left_child = cgen_expr(node.child[0])
    right_child = cgen_expr(node.child[2])

    left_child_address = left_child.attribute[AttName.address]
    right_child_address = right_child.attribute[AttName.address]

    if left_child.attribute[AttName.type] != right_child.attribute[AttName.type]:
        emit("li $s0, 0")
    elif left_child.attribute[AttName.type] == Type.double:
        left_child_address.load()
        emit("mov.d $f2, $f0")
        right_child_address.load()
        emit("c.eq.d $f0, $f2")
        # TODO chejoori mishe be flagesh dastresi dasht :-?
    elif left_child.attribute[AttName.type] in (Type.array, Type.string):
        pass
        # TODO :((
    else:
        left_child_address.load()
        emit("move $s1, $s0")
        right_child_address.load()
        emit("and $t0, $s0, $s1")

        emit("slt $t1, $t0, $zero")
        emit("slt $t0, $zero, $t0")
        emit("or $t0, $t0, $t1")

        emit("li $t1, 1")
        emit("sub $s0, $t1, $t0")
        emit("")

    address.store()
    return node


def cgen_expr_nequal(node):
    node = cgen_expr_equal(node)
    address = node.attribute[AttName.address]

    address.load()
    emit("li $t0, 1")
    emit("sub $t0, $s0")
    address.store()
    return node


def cgen_expr_grq(node):
    pass


def cgen_expr_gr(node):
    pass


def cgen_expr_le(node):
    pass


def cgen_expr_leq(node):
    pass


def expr_add_sub(node, operation):
    # operation = 'add' or 'sub'
    left_child = cgen_expr(node.child[0])
    right_child = cgen_expr(node.child[2])
    left_child_type = left_child.attribute[AttName.type]

    expr_set_node_attributes(node, left_child_type)
    address = node.attribute[AttName.address]

    left_child_address = left_child.attribute[AttName.address]
    right_child_address = right_child.attribute[AttName.address]

    if left_child_type != right_child.attribute[type] or left_child_type not in (Type.double, Type.int):
        raise TypeError(
            "in node: \n" + node.__repr__() + "\n exprs' types are not good for " + operation + " operation.")
    elif left_child_type == Type.int:
        left_child_address.load()
        emit("move $s1, $s0")
        right_child_address.load()
        emit(operation + " $s0, $s0, $s1")
    elif left_child_type == Type.double:
        left_child_address.load()
        emit("mov.d $f2, $f0")
        right_child_address.load()
        emit(operation + ".d $f0, $f0, $f2")

    address.store()
    return node


def cgen_expr_add(node):
    return expr_add_sub(node, 'add')


def cgen_expr_sub(node):
    return expr_add_sub(node, 'sub')


def expr_mul_mod_div(node, operation):
    # operation = 'div' or 'mod' or 'mul'
    left_child = cgen_expr(node.child[0])
    right_child = cgen_expr(node.child[2])
    left_child_type = left_child.attribute[AttName.type]

    expr_set_node_attributes(node, left_child_type)
    address = node.attribute[AttName.address]

    left_child_address = left_child.attribute[AttName.address]
    right_child_address = right_child.attribute[AttName.address]

    if left_child_type != right_child.attribute[type] or left_child_type not in (Type.double, Type.int) or (
            operation == 'mod' and left_child_type != Type.int):
        raise TypeError(
            "in node: \n" + node.__repr__() + "\n exprs' types are not good for " + operation + " operation.")
    elif left_child_type == Type.int:
        left_child_address.load()
        emit("move $s1, $s0")
        right_child_address.load()
        if operation == 'mul':
            emit("mult $s0, $s1")
        else:
            emit("div $s0, $s1")

        if operation == 'mod':
            emit("mfhi $s0")
        else:
            emit("mflo $s0")
    elif left_child_type == Type.double:
        left_child_address.load()
        emit("mov.d $f2, $f0")
        right_child_address.load()
        emit(operation + ".d $f0, $f0, $f2")

    address.store()
    return node


def cgen_expr_mul(node):
    return expr_mul_mod_div(node, 'mul')


def cgen_expr_div(node):
    return expr_mul_mod_div(node, 'div')


def cgen_expr_mod(node):
    return expr_mul_mod_div(node, 'mod')


def cgen_expr(node_id):
    node = parseTree.nodes[node_id]

    if len(node.child) == 1:
        child = node.ref_child[0]

        if child.data == 'expr':
            return cgen_expr(node.child[0])
        elif child.data == 'readline':
            return cgen_readline(child)
        elif child.data == 'readint':
            return cgen_readint(child)
        elif child.data == 'call':
            return cgen_call(child)
        elif child.data == 'this':
            return cgen_this(child)
        elif child.data == 'lvalue':
            return cgen_lvalue(child)
        elif child.data == 'constant':
            return cgen_constant(child)

    elif len(node.child) == 2:
        child = node.ref_child[0]

        if child.data == 'not':
            return cgen_expr_not(node)
        elif child.data == 'neg':
            return cgen_expr_neg(node)
        elif child.data == 'new':
            return cgen_expr_new(node)

    elif len(node.child) == 3:
        mid_child = node.ref_child[1]

        if mid_child.data == 'assign':
            return cgen_expr_assign(node)
        elif mid_child.data == 'bitor':
            return cgen_expr_bitor(node)
        elif mid_child.data == 'bitand':
            return cgen_expr_bitand(node)
        elif mid_child.data == 'equal':
            return cgen_expr_equal(node)
        elif mid_child.data == 'nequal':
            return cgen_expr_nequal(node)
        elif mid_child.data == 'grq':
            return cgen_expr_grq(node)
        elif mid_child.data == 'gr':
            return cgen_expr_gr(node)
        elif mid_child.data == 'le':
            return cgen_expr_le(node)
        elif mid_child.data == 'leq':
            return cgen_expr_leq(node)
        elif mid_child.data == 'sub':
            return cgen_expr_sub(node)
        elif mid_child.data == 'add':
            return cgen_expr_add(node)
        elif mid_child.data == 'mul':
            return cgen_expr_mul(node)
        elif mid_child.data == 'div':
            return cgen_expr_div(node)
        elif mid_child.data == 'mod':
            return cgen_expr_mod(node)
        elif mid_child.data == 'expr':
            left_child = node.ref_child[0]

            if left_child.data == 'parop':
                return cgen_expr(node.child[0])
            elif left_child.data == 'newarray':
                return cgen_newarray(node)

    return Node("", 0)


def cgen_if(if_id):
    node = parseTree.nodes[if_id]
    length = len(node.child)
    if length == 2:
        cgen_if2(node.child[0], node.child[1])
    elif length == 3:
        cgen_if1(node.child[0], node.child[1], node.child[2])
    # TODO {sharifi} mage bazam halat dare? : bara mohkam kariye


def cgen_print_stmt(print_id):
    global disFp
    top = disFp

    node = parseTree.nodes[print_id]
    for child_id in node.child:
        expr = cgen_expr(child_id)
        address = expr.attribute["address"]
        type = expr.attribute["type"]
        address.load_address()
        if type is "double":
            emit_load_double("$f12", "$s0")
            emit_li("$v0", 3)
            emit_syscall()
        elif type is "string":  ## TODO {keivan} is it correct? :>
            emit_load("$a0", "$s0")
            emit_li("$v0", 4)
            emit_syscall()
        else:
            emit_load("$a0", "$s0")
            emit_li("$v0", 1)
            emit_syscall()

        align_stack(top)


def cgen_stmt(node_id):
    node = parseTree.nodes[node_id]
    child_id = node.child[0]
    child = parseTree.nodes[child_id]

    if child.data is "stmt":
        cgen_stmt(child_id)
    elif child.data is "forstmt":
        cgen_for(child_id)
    elif child.data is "whilestmt":
        cgen_while(child_id)
    elif child.data is "ifstmt":
        cgen_if(child_id)
    elif child.data is "stmtblock":
        cgen_stmt_block(child_id)
    elif child.data is "expr":
        cgen_expr(child_id)
    elif child.data is "breakstmt":
        cgen_break(child_id)
    elif child.data is "printstmt":
        cgen_print_stmt(child_id)


# TODO cgen_return_stmt


def cgen_stmt_block(node_id):
    global symbolTable
    symbolTable.add_scope()
    node = parseTree.nodes[node_id]

    global disFp
    top = disFp

    for id in node.child:
        child_node = parseTree.nodes[id]
        if child_node.data is "variabledecl":
            cgen_variable_decl(child_node)
        else:
            cgen_stmt(child_node)

    align_stack(top)

    symbolTable.remove_scope()


def cgen_break(node):
    parent = parseTree.nodes[node].parent
    while parent is not None:
        data = parseTree.nodes[parent].data
        if data == "whilestmt" or data == "forstmt":
            break
        parent = parseTree.nodes[parent].parent

    if parent is None:
        print("Error!")
        exit(2)

    emit("j " + parseTree.nodes[node].attribute["ex_label"])
    return
