import sys
import re


""" Kontrola a spracovanie argumentov """

source_arg = None
input_arg = None
stats_file = None

if len(sys.argv) > 1:
    for arg in sys.argv:
        if arg == '--help':
            if len(sys.argv) == 2:
                print("""Skript typu filtr (parse.php v jazyce PHP 7.4) načte ze standardního vstupu zdrojový kód v IPPcode20
                    , zkontroluje lexikální a syntaktickou správnost kódu a vypíše na standardní
                    výstup XML reprezentaci programu dle specifikace.""")
                sys.exit(0)
            else:
                sys.exit(10)
        elif re.match(r'^--source=(\.){0,2}(\/*[a-zA-Z ]*\d*\S*)*$', arg):
            source_arg = arg[9:]
        elif re.match(r'^--input=(\.){0,2}(\/*[a-zA-Z ]*\d*\S*)*$', arg):
            input_arg = arg[8:]
        elif re.match(r'^--stats=(\.){0,2}(\/*[a-zA-Z ]*\d*\S*)*$', arg):
            try:
                stats_file = open(arg[8:], "w")
            except:
                sys.exit(11)
        elif arg == __file__ or arg == '--vars' or arg == '--insts':
            pass
        else:
            sys.exit(10)

if source_arg == None and input_arg == None:
    sys.exit(10)

if source_arg == None:
    xml_file = sys.stdin
else:
    try:
        xml_file = open(source_arg, "r")
    except:
        sys.exit(11)

if input_arg == None:
    input_file = sys.stdin
else:
    try:
        input_file = open(input_arg, "r")
    except:
        sys.exit(11)

temp = []
for line in input_file:
    temp.append(line.strip())
input_file = temp


""" Deklarácie funkcií """

""" Načítanie vstupného xml súboru do listu """


def file_to_list(xml_file):
    global labels_array
    temp_var = False
    temp_list = []
    xcounter = 0
    for xline in xml_file:
        xcounter += 1
        if re.match(r'^<instruction order="[\d]+" opcode="LABEL">$', xline.strip(), re.IGNORECASE):
            temp_var = True
        if temp_var:
            if re.match(r'^<arg1 type="label">.*</arg1>$', xline.strip()):
                label_name = re.search(
                    r'^<arg1 type="label">(.*)</arg1>$', xline.strip()).group(1)
                if label_name not in labels_array:
                    labels_array[label_name] = int(xcounter)
                    temp_var = False
                else:
                    sys.exit(52)
        if xline.strip() == '':
            pass
        else:
            temp_list.append(xline.strip())
    return temp_list


""" Iterácia cez celý xml list """


def iterate():
    global instructions_cnt
    global lines, order, opcode, tf_frame, lf_frame, var_array_lf, var_array_tf, call_pos, call_varback_stack_lf, call_varback_stack_tf
    for line in xml_file[lines:]:
        if re.match(r'^</instruction>$', line) or re.match(r'^<arg\d type=".*">.*</arg\d>$', line) or re.match(r'^</program>$', line):
            lines += 1
            return
        elif re.match(r'^<instruction order="[\d]+" opcode="[a-zA-Z2]+"/{0,1}>$', line.strip()):
            if order < (int(re.search(r'order="(\d+)"', line).group(1))) or len(labels_array) > 0:
                order = int(re.search(r'order="(\d+)"', line).group(1))
            else:
                sys.exit(32)
            opcode = re.search(r'opcode="([a-zA-Z2]+)"', line).group(1)
            opcode = opcode.upper()
            if opcode in ['CREATEFRAME', 'PUSHFRAME', 'POPFRAME', 'RETURN', 'BREAK']:
                instructions_cnt += 1

                if opcode == 'CREATEFRAME':
                    var_array_tf = {}
                    call_varback_stack_tf = []
                    call_varback_stack_tf.append(var_array_tf)
                    tf_frame = True
                elif opcode == 'PUSHFRAME':
                    if tf_frame:
                        call_varback_stack_lf.append(
                            call_varback_stack_tf.pop())
                        lf_frame = True
                        tf_frame = False
                    else:
                        sys.exit(55)
                elif opcode == 'POPFRAME':
                    if lf_frame:
                        call_varback_stack_tf.append(
                            call_varback_stack_lf.pop())
                        lf_frame = False
                        tf_frame = True
                    else:
                        sys.exit(55)
                elif opcode == 'RETURN':
                    if len(call_pos) < 1:
                        sys.exit(56)
                    else:
                        if len(call_varback_stack_lf) > 0:
                            pass
                        if len(call_varback_stack_tf) > 0:
                            pass
                        lines = call_pos.pop()
                elif opcode == 'BREAK':
                    sys.stderr.write('Globalny ramec: ' +
                                     str(var_array_gf) + "\n")
                    if len(call_varback_stack_lf) > 0:
                        sys.stderr.write('Lokalny ramec: ' +
                                         str(call_varback_stack_lf[-1]) + "\n")
                    else:
                        sys.stderr.write('Lokalny ramec: ' + "{}" + "\n")
                    if len(call_varback_stack_tf) > 0:
                        sys.stderr.write('Docasny ramec: ' +
                                         str(call_varback_stack_tf[-1]) + "\n")
                    else:
                        sys.stderr.write('Docasny ramec: ' + "{}" + "\n")
                    sys.stderr.write(
                        'Pocet vykonanych instrukci: ' + str(instructions_cnt) + "\n")
                else:
                    sys.exit(32)

            else:
                lines += 1
                instructions_cnt += 1
                instruction(xml_file, opcode, tf_frame, lf_frame)
                return
        else:
            sys.exit(32)
        lines += 1
        return


""" Spracovanie jednotlivých inštrukcií a kontrola štruktúry xml kódu """


def instruction(xml_file, opcode, tf_frame, lf_frame):
    global lines, vars_cnt, instructions_cnt
    arg = 0
    reg_line = r'<arg\d type="([a-z]+)">(.*)<\/arg\d>'
    for line in xml_file[lines:]:
        if re.match('^</instruction>$', line.strip()):
            if arg == 0:
                sys.exit(32)
            lines += 1
            return
        elif re.match(r'^<instruction order="[\d]+" opcode="[a-zA-Z2]+"/{0,1}>$', line.strip()):
            sys.exit(31)
        elif re.match(reg_line, line.strip()):
            arg_type = re.search(reg_line, line).group(1)
            arg_content = re.search(reg_line, line).group(2)
            if arg == (int(re.findall(r'\d', line)[0]) - 1) and int(re.findall(r'\d', line)[0]) == int(re.findall(r'\d', line)[-1]):
                arg = int(re.findall(r'\d', line)[0])
                if arg == 4:
                    sys.exit(32)
                opcode = opcode.upper()
                if opcode == 'MOVE':
                    if arg == 3:
                        sys.exit(32)
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                        check_var(arg_type, arg_content)
                    else:
                        inst_move(arg_type, arg_content,
                                  arg, var_frame, var_name)
                elif opcode == 'DEFVAR':
                    if arg == 2:
                        sys.exit(32)
                    vars_cnt += 1
                    inst_defvar(arg_type, arg_content)
                elif opcode == 'CALL':
                    lines = inst_call(arg_type, arg_content)
                    continue
                elif opcode == 'PUSHS':
                    if arg == 2:
                        sys.exit(32)
                    inst_pushs(arg_type, arg_content)
                elif opcode == 'POPS':
                    if arg == 2:
                        sys.exit(32)
                    inst_pops(arg_type, arg_content)

                elif opcode == 'ADD':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_add(arg_type, arg_content, arg, var_frame, var_name)
                elif opcode == 'SUB':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_sub(arg_type, arg_content, arg, var_frame, var_name)
                elif opcode == 'MUL':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_mul(arg_type, arg_content, arg, var_frame, var_name)
                elif opcode == 'IDIV':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_idiv(arg_type, arg_content, arg, var_frame, var_name)
                elif opcode == 'DIV':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_div(arg_type, arg_content, arg, var_frame, var_name)
                elif opcode == 'LT':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_ltgt(arg_type, arg_content, arg,
                              var_frame, var_name, 'lt')
                elif opcode == 'GT':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_ltgt(arg_type, arg_content, arg,
                              var_frame, var_name, 'gt')
                elif opcode == 'EQ':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_eq(arg_type, arg_content, arg, var_frame, var_name)
                elif opcode == 'AND':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_andor(arg_type, arg_content, arg,
                               var_frame, var_name, 'and')
                elif opcode == 'OR':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_andor(arg_type, arg_content, arg,
                               var_frame, var_name, 'or')
                elif opcode == 'NOT':
                    if arg == 3:
                        sys.exit(32)
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_not(arg_type, arg_content, arg, var_frame, var_name)
                elif opcode == 'INT2CHAR':
                    if arg == 3:
                        sys.exit(32)
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_inttochar(arg_type, arg_content,
                                   arg, var_frame, var_name)
                elif opcode == 'STRI2INT':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_stritoint(arg_type, arg_content,
                                   arg, var_frame, var_name)
                elif opcode == 'READ':
                    if arg == 3:
                        sys.exit(32)
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_read(arg_type, arg_content, arg, var_frame, var_name)
                elif opcode == 'WRITE':
                    if arg == 2:
                        sys.exit(32)
                    inst_write(arg_type, arg_content)
                elif opcode == 'CONCAT':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_concat(arg_type, arg_content,
                                arg, var_frame, var_name)
                elif opcode == 'STRLEN':
                    if arg == 3:
                        sys.exit(32)
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_strlen(arg_type, arg_content,
                                arg, var_frame, var_name)
                elif opcode == 'GETCHAR':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_getchar(arg_type, arg_content,
                                 arg, var_frame, var_name)
                elif opcode == 'SETCHAR':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_setchar(arg_type, arg_content,
                                 arg, var_frame, var_name)
                elif opcode == 'TYPE':
                    if arg == 3:
                        sys.exit(32)
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_type(arg_type, arg_content, arg, var_frame, var_name)
                elif opcode == 'LABEL':
                    if arg == 2:
                        sys.exit(32)
                    pass
                elif opcode == 'JUMP':
                    if arg == 2:
                        sys.exit(32)
                    lines = inst_jump(arg_type, arg_content)
                    instructions_cnt += 1
                    continue
                elif opcode == 'JUMPIFEQ':
                    if arg == 1:
                        label = inst_jumpifeq(arg_type, arg_content, arg)
                    elif arg == 3:
                        eq = inst_jumpifeq(arg_type, arg_content, arg)
                        if eq:
                            lines = label
                        else:
                            pass
                        instructions_cnt += 1

                        continue
                    else:
                        inst_jumpifeq(arg_type, arg_content, arg)
                elif opcode == 'JUMPIFNEQ':
                    if arg == 1:
                        label = inst_jumpifneq(arg_type, arg_content, arg)
                    elif arg == 3:
                        eq = inst_jumpifneq(arg_type, arg_content, arg)
                        if eq:
                            lines = label
                        else:
                            pass
                        instructions_cnt += 1

                        continue
                    else:
                        inst_jumpifneq(arg_type, arg_content, arg)
                elif opcode == 'EXIT':
                    if arg == 2:
                        sys.exit(32)
                    inst_exit(arg_type, arg_content)
                elif opcode == 'DPRINT':
                    inst_dprint(arg_type, arg_content)
                elif opcode == 'INT2FLOAT':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_inttofloat(arg_type, arg_content,
                                    arg, var_frame, var_name)
                elif opcode == 'FLOAT2INT':
                    if arg == 1:
                        var_frame, var_name = var_info(reg_line, line)
                    inst_floattoint(arg_type, arg_content,
                                    arg, var_frame, var_name)
                else:
                    sys.exit(32)
            else:
                sys.exit(32)
        else:
            sys.exit(32)


""" Pomocné funkcie slúžiace na optimalizáciu kódu """

""" Spracovanie escape sekvencií """

def escapes(content):
    for rep in re.findall(r'\\[\d]{3}', content):
        try:
            code = int(rep[-2:])
        except:
            sys.exit(32)
        if code == 92:
            content = re.sub(
                '\\' + rep, "\\\\", content)
        else:
            content = re.sub(
                '\\' + rep, chr(int(rep[-2:])), content)
    return content


""" Kontrola správnosti premennej a uložení informácii o rámci a názvu premennej"""

def var_info(reg_line, line):
    try:
        var_frame = re.search(
            r'^(GF|TF|LF)@(\_|\-|\$|\&|\%|\*|\!|\?*\w+)+$', re.search(reg_line, line).group(2)).group(1)
        var_name = re.search(
            r'^(GF|TF|LF)@(\_|\-|\$|\&|\%|\*|\!|\?*\w+)+$', re.search(reg_line, line).group(2)).group(2)
    except:
        sys.exit(32)
    return var_frame, var_name

""" Kontrola správnosti premmenej v závislosti na rámcoch """

def check_var(arg_type, arg_content):
    try:
        var_frame = re.search(
            r'^(GF|TF|LF)@(\_|\-|\$|\&|\%|\*|\!|\?*\w+)+$', arg_content).group(1)
        var_name = re.search(
            r'^(GF|TF|LF)@(\_|\-|\$|\&|\%|\*|\!|\?*\w+)+$', arg_content).group(2)
    except:
        sys.exit(32)
    if arg_type == 'var':
        if var_frame == 'GF':
            if var_name in var_array_gf:
                pass
            else:
                sys.exit(54)
        elif var_frame == 'TF':
            if not(tf_frame):
                sys.exit(55)
            if var_name in call_varback_stack_tf[-1]:
                pass
            else:
                sys.exit(54)
        elif var_frame == 'LF':
            if not(lf_frame):
                sys.exit(55)
            if var_name in call_varback_stack_lf[-1]:
                pass
            else:
                sys.exit(54)
        else:
            sys.exit(54)
    else:
        sys.exit(32)
    return var_frame, var_name

""" Ukladanie informácií do premenných """

def var_processor(var_frame, arg_content, var_name, savetype):
    if var_frame == 'GF':
        if savetype == 'raw':
            if type(arg_content) == bool:
                if arg_content:
                    var_array_gf[var_name] = 'true'
                else:
                    var_array_gf[var_name] = 'false'
            else:
                if type(arg_content) == str:
                    arg_content = escapes(arg_content)
                var_array_gf[var_name] = arg_content
        elif savetype == 'bool':
            if type(arg_content) == bool:
                if arg_content:
                    var_array_gf[var_name] = True
                else:
                    var_array_gf[var_name] = False
            else:
                if arg_content == 'true':
                    var_array_gf[var_name] = True
                else:
                    var_array_gf[var_name] = False
    elif var_frame == 'TF':
        if not(tf_frame):
            sys.exit(55)
        if savetype == 'raw':
            if type(arg_content) == bool:
                if arg_content:
                    call_varback_stack_tf[-1][var_name] = 'true'
                else:
                    call_varback_stack_tf[-1][var_name] = 'false'
            else:
                if type(arg_content) == str:
                    arg_content = escapes(arg_content)
                call_varback_stack_tf[-1][var_name] = arg_content
        elif savetype == 'bool':
            if not(tf_frame):
                sys.exit(55)
            if type(arg_content) == bool:
                if arg_content:
                    call_varback_stack_tf[-1][var_name] = True
                else:
                    call_varback_stack_tf[-1][var_name] = False
            else:
                if arg_content == 'true':
                    call_varback_stack_tf[-1][var_name] = True
                else:
                    call_varback_stack_tf[-1][var_name] = False
    elif var_frame == 'LF':
        if not(lf_frame):
            sys.exit(55)
        if savetype == 'raw':
            if type(arg_content) == bool:
                if arg_content:
                    call_varback_stack_lf[-1][var_name] = 'true'
                else:
                    call_varback_stack_lf[-1][var_name] = 'false'
            else:
                if type(arg_content) == str:
                    arg_content = escapes(arg_content)
                call_varback_stack_lf[-1][var_name] = arg_content
        elif savetype == 'bool':
            if type(arg_content) == bool:
                if arg_content:
                    call_varback_stack_lf[-1][var_name] = True
                else:
                    call_varback_stack_lf[-1][var_name] = False
            else:
                if arg_content == 'true':
                    call_varback_stack_lf[-1][var_name] = True
                else:
                    call_varback_stack_lf[-1][var_name] = False
    else:
        sys.exit(32)

""" Kopírovanie premenných do premenných """

def symvar_processor(var_frame, arg_content, var_name, savetype):
    try:
        var_frame_sym = re.search(
            r'^(GF|TF|LF)@(\_|\-|\$|\&|\%|\*|\!|\?*\w+)+$', arg_content).group(1)
        var_name_sym = re.search(
            r'^(GF|TF|LF)@(\_|\-|\$|\&|\%|\*|\!|\?*\w+)+$', arg_content).group(2)
    except:
        sys.exit(32)
    if var_frame == 'GF':
        if var_frame_sym == 'GF':
            if var_array_gf[var_name_sym] == None:
                sys.exit(56)
            var_array_gf[var_name] = var_array_gf[var_name_sym]
        elif var_frame_sym == 'TF':
            if not(tf_frame):
                sys.exit(55)
            if call_varback_stack_tf[-1][var_name_sym] == None:
                sys.exit(56)
            var_array_gf[var_name] = call_varback_stack_tf[-1][var_name_sym]
        elif var_frame_sym == 'LF':
            if not(lf_frame):
                sys.exit(55)
            if call_varback_stack_lf[-1][var_name_sym] == None:
                sys.exit(56)
            var_array_gf[var_name] = call_varback_stack_lf[-1][var_name_sym]
        else:
            sys.exit(32)
    elif var_frame == 'TF':
        if var_frame_sym == 'GF':
            if var_array_gf[var_name_sym] == None:
                sys.exit(56)
            call_varback_stack_tf[-1][var_name] = var_array_gf[var_name_sym]
        elif var_frame_sym == 'TF':
            if not(tf_frame):
                sys.exit(55)
            if call_varback_stack_tf[-1][var_name_sym] == None:
                sys.exit(56)
            call_varback_stack_tf[-1][var_name] = call_varback_stack_tf[-1][var_name_sym]
        elif var_frame_sym == 'LF':
            if not(lf_frame):
                sys.exit(55)
            if call_varback_stack_lf[-1][var_name_sym] == None:
                sys.exit(56)
            call_varback_stack_tf[-1][var_name] = call_varback_stack_lf[-1][var_name_sym]
        else:
            sys.exit(32)
    elif var_frame == 'LF':
        if var_frame_sym == 'GF':
            if var_array_gf[var_name_sym] == None:
                sys.exit(56)
            call_varback_stack_lf[-1][var_name] = var_array_gf[var_name_sym]
        elif var_frame_sym == 'TF':
            if not(tf_frame):
                sys.exit(55)
            if call_varback_stack_tf[-1][var_name_sym] == None:
                sys.exit(56)
            call_varback_stack_lf[-1][var_name] = call_varback_stack_tf[-1][var_name_sym]
        elif var_frame_sym == 'LF':
            if not(lf_frame):
                sys.exit(55)
            if call_varback_stack_lf[-1][var_name_sym] == None:
                sys.exit(56)
            call_varback_stack_lf[-1][var_name] = call_varback_stack_lf[-1][var_name_sym]
        else:
            sys.exit(32)
    else:
        sys.exit(32)

""" Vykonávanie aritmetických inštrukcí """

def sym_arithm(var_frame_sym, temp, var_name_sym, op):
    if var_frame_sym == 'GF':
        if var_array_gf[var_name_sym] == None:
            sys.exit(56)
        if type(var_array_gf[var_name_sym]) == int or type(var_array_gf[var_name_sym]) == float:
            if op == '+':
                if type(temp) != type(var_array_gf[var_name_sym]):
                    sys.exit(53)
                temp = temp + var_array_gf[var_name_sym]
            elif op == '-':
                if type(temp) != type(var_array_gf[var_name_sym]):
                    sys.exit(53)
                temp = temp - var_array_gf[var_name_sym]
            elif op == '*':
                if type(temp) != type(var_array_gf[var_name_sym]):
                    sys.exit(53)
                temp = temp * var_array_gf[var_name_sym]
            elif op == '//':
                if type(temp) != type(var_array_gf[var_name_sym]):
                    sys.exit(53)
                if var_array_gf[var_name_sym] == 0:
                    sys.exit(57)
                temp = temp // var_array_gf[var_name_sym]
            elif op == '/':
                if type(temp) != type(var_array_gf[var_name_sym]):
                    sys.exit(53)
                if var_array_gf[var_name_sym] == 0:
                    sys.exit(57)
                temp = temp / var_array_gf[var_name_sym]
            elif op == 'blank':
                temp = var_array_gf[var_name_sym]
        else:
            if op == 'blank':
                temp = var_array_gf[var_name_sym]
            else:
                sys.exit(56)
    if var_frame_sym == 'TF':
        if not(tf_frame):
            sys.exit(55)
        if call_varback_stack_tf[-1][var_name_sym] == None:
            sys.exit(56)
        if type(call_varback_stack_tf[-1][var_name_sym]) == int or type(call_varback_stack_tf[-1][var_name_sym]) == float:
            if op == '+':
                if type(temp) != type(call_varback_stack_tf[-1][var_name_sym]):
                    sys.exit(53)
                temp = temp + call_varback_stack_tf[-1][var_name_sym]
            elif op == '-':
                if type(temp) != type(call_varback_stack_tf[-1][var_name_sym]):
                    sys.exit(53)
                temp = temp - call_varback_stack_tf[-1][var_name_sym]
            elif op == '*':
                if type(temp) != type(call_varback_stack_tf[-1][var_name_sym]):
                    sys.exit(53)
                temp = temp * call_varback_stack_tf[-1][var_name_sym]
            elif op == '//':
                if type(temp) != type(call_varback_stack_tf[-1][var_name_sym]):
                    sys.exit(53)
                if call_varback_stack_tf[-1][var_name_sym] == 0:
                    sys.exit(57)
                temp = temp // call_varback_stack_tf[-1][var_name_sym]
            elif op == '/':
                if type(temp) != type(call_varback_stack_tf[-1][var_name_sym]):
                    sys.exit(53)
                if call_varback_stack_tf[-1][var_name_sym] == 0:
                    sys.exit(57)
                temp = temp / call_varback_stack_tf[-1][var_name_sym]
            elif op == 'blank':
                temp = call_varback_stack_tf[-1][var_name_sym]
        else:
            if op == 'blank':
                temp = call_varback_stack_tf[-1][var_name_sym]
            else:
                sys.exit(56)
    if var_frame_sym == 'LF':
        if not(lf_frame):
            sys.exit(55)
        if call_varback_stack_lf[-1][var_name_sym] == None:
            sys.exit(56)
        if type(call_varback_stack_lf[-1][var_name_sym]) == int or type(call_varback_stack_lf[-1][var_name_sym]) == float:
            if op == '+':
                if type(temp) != type(call_varback_stack_lf[-1][var_name_sym]):
                    sys.exit(53)
                temp = temp + call_varback_stack_lf[-1][var_name_sym]
            elif op == '-':
                if type(temp) != type(call_varback_stack_lf[-1][var_name_sym]):
                    sys.exit(53)
                temp = temp - call_varback_stack_lf[-1][var_name_sym]
            elif op == '*':
                if type(temp) != type(call_varback_stack_lf[-1][var_name_sym]):
                    sys.exit(53)
                temp = temp * call_varback_stack_lf[-1][var_name_sym]
            elif op == '//':
                if type(temp) != type(call_varback_stack_lf[-1][var_name_sym]):
                    sys.exit(53)
                if call_varback_stack_lf[-1][var_name_sym] == 0:
                    sys.exit(57)
                temp = temp // call_varback_stack_lf[-1][var_name_sym]
            elif op == '/':
                if type(temp) != type(call_varback_stack_lf[-1][var_name_sym]):
                    sys.exit(53)
                if call_varback_stack_lf[-1][var_name_sym] == 0:
                    sys.exit(57)
                temp = temp / call_varback_stack_lf[-1][var_name_sym]
            elif op == 'blank':
                temp = call_varback_stack_lf[-1][var_name_sym]
        else:
            if op == 'blank':
                temp = call_varback_stack_lf[-1][var_name_sym]
            else:
                sys.exit(56)
    return temp


""" Definície inštrukcií """

""" Práce s rámci, volání funkcí """


def inst_move(arg_type, arg_content, arg, var_frame, var_name):
    if arg_type == 'string':
        var_processor(var_frame, arg_content, var_name, 'raw')
    elif arg_type == 'nil':
        var_processor(var_frame, arg_content, var_name, 'raw')
    elif arg_type == 'bool':
        var_processor(var_frame, arg_content, var_name, 'bool')
    elif arg_type == 'float':
        try:
            var_processor(var_frame, float(
                float(arg_content)), var_name, 'raw')
        except:
            try:
                var_processor(var_frame, float(
                    float.fromhex(arg_content)), var_name, 'raw')
            except:
                sys.exit(32)
    elif arg_type == 'int':
        try:
            int(arg_content)
        except:
            sys.exit(32)
        var_processor(var_frame, int(arg_content), var_name, 'raw')
    elif arg_type == 'var':
        check_var(arg_type, arg_content)
        symvar_processor(var_frame, arg_content, var_name, 'raw')
    else:
        sys.exit(32)


def inst_defvar(arg_type, arg_content):
    if arg_type == 'var':
        try:
            var_frame = re.search(
                r'^(GF|TF|LF)@(\_|\-|\$|\&|\%|\*|\!|\?*\w+)+$', arg_content).group(1)
            var_name = re.search(
                r'^(GF|TF|LF)@(\_|\-|\$|\&|\%|\*|\!|\?*\w+)+$', arg_content).group(2)
        except:
            sys.exit(32)
        if var_frame == 'GF':
            if var_name in var_array_gf:
                sys.exit(52)
            else:
                var_array_gf[var_name] = None
        elif var_frame == 'TF':
            if not(tf_frame):
                sys.exit(55)
            if var_name in call_varback_stack_tf[-1]:
                sys.exit(52)
            else:
                call_varback_stack_tf[-1][var_name] = None
        elif var_frame == 'LF':
            if not(lf_frame):
                sys.exit(55)
            if var_name in call_varback_stack_lf[-1]:
                sys.exit(52)
            else:
                call_varback_stack_lf[-1][var_name] = None
        else:
            sys.exit(32)
    else:
        sys.exit(32)


def inst_call(arg_type, arg_content):
    global call_pos, call_varback_stack_tf, call_varback_stack_lf
    if arg_type == 'label':
        pass
    else:
        sys.exit(32)

    if arg_content in labels_array:
        call_pos.append(int(lines + 1))
        return int(labels_array[arg_content])
    else:
        sys.exit(52)


""" Práce s datovým zásobníkem """


def inst_pushs(arg_type, arg_content):
    if arg_type == 'string':
        arg_content = escapes(arg_content)
        stack.append(str(arg_content))
    elif arg_type == 'bool':
        stack.append(bool(arg_content))
    elif arg_type == 'int':
        try:
            int(arg_content)
        except:
            sys.exit(53)
        stack.append(int(arg_content))
    elif arg_type == 'float':
        try:
            stack.append(float.hex(float(arg_content)))
        except:
            try:
                stack.append(float.hex(float.fromhex(arg_content)))
            except:
                sys.exit(53)

    elif arg_type == 'var':
        var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
        if var_frame_sym == 'GF':
            if var_array_gf[var_name_sym] == None:
                sys.exit(56)
            stack.append(var_array_gf[var_name_sym])
        if var_frame_sym == 'TF':
            if call_varback_stack_tf[-1][var_name_sym] == None:
                sys.exit(56)
            stack.append(call_varback_stack_tf[-1][var_name_sym])
        if var_frame_sym == 'LF':
            if call_varback_stack_lf[-1][var_name_sym] == None:
                sys.exit(56)
            stack.append(call_varback_stack_lf[-1][var_name_sym])
    else:
        sys.exit(32)


def inst_pops(arg_type, arg_content):
    if arg_type == 'var':
        var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
        if len(stack) < 1:
            sys.exit(56)
        if var_frame_sym == 'GF':
            var_array_gf[var_name_sym] = stack.pop()
        if var_frame_sym == 'TF':
            call_varback_stack_tf[-1][var_name_sym] = stack.pop()
        if var_frame_sym == 'LF':
            call_varback_stack_lf[-1][var_name_sym] = stack.pop()
    else:
        sys.exit(32)


""" Aritmetické, relační, booleovské a konverzní instrukce """


def inst_add(arg_type, arg_content, arg, var_frame, var_name):
    global temp
    if arg == 1:
        check_var(arg_type, arg_content)
        temp = 0
    elif arg == 3:
        if arg_type == 'int':
            if type(temp) == int:
                try:
                    temp = temp + int(arg_content)
                    var_processor(var_frame, int(temp), var_name, 'raw')
                except:
                    sys.exit(32)
            else:
                sys.exit(53)
        elif arg_type == 'float':
            if type(temp) == float:
                try:
                    temp = float(temp) + float(arg_content)
                except:
                    try:
                        temp = float(temp) + float.fromhex(arg_content)
                    except:
                        sys.exit(32)
                var_processor(var_frame, float(temp), var_name, 'raw')
            else:
                sys.exit(53)
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = sym_arithm(var_frame_sym, temp, var_name_sym, '+')
            var_processor(var_frame, temp, var_name, 'raw')
        else:
            sys.exit(53)
    else:
        if arg_type == 'int':
            try:
                temp = int(arg_content)
            except:
                sys.exit(32)
        elif arg_type == 'float':
            try:
                temp = float(arg_content)
            except:
                try:
                    temp = float.fromhex(arg_content)
                except:
                    sys.exit(32)
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = sym_arithm(var_frame_sym, temp, var_name_sym, 'blank')
        else:
            sys.exit(53)


def inst_sub(arg_type, arg_content, arg, var_frame, var_name):
    global temp
    if arg == 1:
        check_var(arg_type, arg_content)
        temp = 0
    elif arg == 3:
        if arg_type == 'int':
            if type(temp) == int:
                try:
                    temp = temp - int(arg_content)
                    var_processor(var_frame, int(temp), var_name, 'raw')
                except:
                    sys.exit(32)
            else:
                sys.exit(32)
        elif arg_type == 'float':
            try:
                temp = float(temp) - float(arg_content)
            except:
                try:
                    temp = float(temp) - float.fromhex(arg_content)
                except:
                    sys.exit(32)
            var_processor(var_frame, float(temp), var_name, 'raw')
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = sym_arithm(var_frame_sym, temp, var_name_sym, '-')
            var_processor(var_frame, temp, var_name, 'raw')
        else:
            sys.exit(53)
    else:
        if arg_type == 'int':
            try:
                temp = int(arg_content)
            except:
                sys.exit(32)
        elif arg_type == 'float':
            try:
                temp = float(arg_content)
            except:
                try:
                    temp = float.fromhex(arg_content)
                except:
                    sys.exit(32)
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = sym_arithm(var_frame_sym, temp, var_name_sym, 'blank')
        else:
            sys.exit(53)


def inst_mul(arg_type, arg_content, arg, var_frame, var_name):
    global temp
    if arg == 1:
        check_var(arg_type, arg_content)
        temp = 1
    elif arg == 3:
        if arg_type == 'int':
            if type(temp) == int:
                temp = temp * int(arg_content)
                var_processor(var_frame, int(temp), var_name, 'raw')
            else:
                sys.exit(32)
        elif arg_type == 'float':
            try:
                temp = float(temp) * float(arg_content)
            except:
                try:
                    temp = float(temp) * float.fromhex(arg_content)
                except:
                    sys.exit(32)
            var_processor(var_frame, float(temp), var_name, 'raw')
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = sym_arithm(var_frame_sym, temp, var_name_sym, '*')
            var_processor(var_frame, temp, var_name, 'raw')
        else:
            sys.exit(53)
    else:
        if arg_type == 'int':
            try:
                temp = int(arg_content)
            except:
                sys.exit(32)
        elif arg_type == 'float':
            try:
                temp = float(arg_content)
            except:
                try:
                    temp = float.fromhex(arg_content)
                except:
                    sys.exit(32)
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = sym_arithm(var_frame_sym, temp, var_name_sym, 'blank')
        else:
            sys.exit(53)


def inst_idiv(arg_type, arg_content, arg, var_frame, var_name):
    global temp
    if arg == 1:
        check_var(arg_type, arg_content)
        temp = 0
    elif arg == 3:
        if arg_type == 'int':
            try:
                int(arg_content)
            except:
                sys.exit(32)
            if int(arg_content) == 0:
                sys.exit(57)
            else:
                temp = temp // int(arg_content)
            var_processor(var_frame, int(temp), var_name, 'raw')
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = sym_arithm(var_frame_sym, temp, var_name_sym, '//')
            var_processor(var_frame, int(temp), var_name, 'raw')

        else:
            sys.exit(53)
    else:
        if arg_type == 'int':
            try:
                temp = int(arg_content)
            except:
                sys.exit(32)
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = sym_arithm(var_frame_sym, temp, var_name_sym, 'blank')
        else:
            sys.exit(53)


def inst_div(arg_type, arg_content, arg, var_frame, var_name):
    global temp
    if arg == 1:
        check_var(arg_type, arg_content)
        temp = 0
    elif arg == 3:
        if arg_type == 'float':
            if type(temp) == float:
                try:
                    float.fromhex(arg_content)
                    if float.fromhex(arg_content) == 0:
                        sys.exit(57)
                except:
                    try:
                        float(arg_content)
                        if float(arg_content) == 0:
                            sys.exit(57)
                    except:
                        sys.exit(32)
                try:
                    temp = float(temp) / float(arg_content)
                except:
                    try:
                        temp = float(temp) / float.fromhex(arg_content)
                    except:
                        sys.exit(53)
                var_processor(var_frame, float(temp), var_name, 'raw')
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = sym_arithm(var_frame_sym, temp, var_name_sym, '/')
            var_processor(var_frame, float(temp), var_name, 'raw')

        else:
            sys.exit(53)
    else:
        if arg_type == 'int':
            try:
                temp = float(arg_content)
            except:
                sys.exit(32)
        elif arg_type == 'float':
            try:
                temp = float(arg_content)
            except:
                try:
                    temp = float.fromhex(arg_content)
                except:
                    sys.exit(53)
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = sym_arithm(var_frame_sym, temp, var_name_sym, 'blank')
        else:
            sys.exit(53)


def inst_ltgt(arg_type, arg_content, arg, var_frame, var_name, op):
    global temp
    if arg == 1:
        temp = 0
        check_var(arg_type, arg_content)
    elif arg == 3:
        if arg_type == 'int':
            if type(temp) == int:
                if op == 'lt':
                    try:
                        int(arg_content)
                    except:
                        sys.exit(32)
                    if temp < int(arg_content):
                        temp = True
                    else:
                        temp = False
                if op == 'gt':
                    try:
                        int(arg_content)
                    except:
                        sys.exit(32)
                    if temp > int(arg_content):
                        temp = True
                    else:
                        temp = False
            else:
                sys.exit(53)
            var_processor(var_frame, bool(temp), var_name, 'bool')
        elif arg_type == 'string':
            arg_content = escapes(arg_content)
            if type(temp) == str:
                if op == 'lt':
                    if temp < arg_content:
                        temp = True
                    else:
                        temp = False
                if op == 'gt':
                    if temp > arg_content:
                        temp = True
                    else:
                        temp = False
            else:
                sys.exit(53)
            var_processor(var_frame, bool(temp), var_name, 'bool')
        elif arg_type == 'bool':
            if type(temp) == bool:
                if arg_content == 'true':
                    arg_content = True
                else:
                    arg_content = False
                if op == 'lt':
                    if temp < arg_content:
                        temp = True
                    else:
                        temp = False
                if op == 'gt':
                    if temp > arg_content:
                        temp = True
                    else:
                        temp = False
            else:
                sys.exit(53)
            var_processor(var_frame, bool(temp), var_name, 'bool')
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(temp) == type(var_array_gf[var_name_sym]):
                    if op == 'lt':
                        if temp < var_array_gf[var_name_sym]:
                            temp = True
                        else:
                            temp = False
                    if op == 'gt':
                        if temp > var_array_gf[var_name_sym]:
                            temp = True
                        else:
                            temp = False
                else:
                    sys.exit(53)
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(temp) == type(call_varback_stack_tf[-1][var_name_sym]):
                    if op == 'lt':
                        if temp < call_varback_stack_tf[-1][var_name_sym]:
                            temp = True
                        else:
                            temp = False
                    if op == 'gt':
                        if temp > call_varback_stack_tf[-1][var_name_sym]:
                            temp = True
                        else:
                            temp = False
                else:
                    sys.exit(53)
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(temp) == type(call_varback_stack_lf[-1][var_name_sym]):
                    if op == 'lt':
                        if temp < call_varback_stack_lf[-1][var_name_sym]:
                            temp = True
                        else:
                            temp = False
                    if op == 'gt':
                        if temp > call_varback_stack_lf[-1][var_name_sym]:
                            temp = True
                        else:
                            temp = False
                else:
                    sys.exit(53)

            var_processor(var_frame, bool(temp), var_name, 'bool')
        elif arg_type == 'nil':
            sys.exit(53)
        else:
            sys.exit(32)
    else:
        if arg_type == 'int':
            try:
                int(arg_content)
            except:
                sys.exit(32)
            temp = int(arg_content)
        elif arg_type == 'float':
            try:
                temp = float(arg_content)
            except:
                try:
                    temp = float.fromhex(arg_content)
                except:
                    sys.exit(32)
        elif arg_type == 'string':
            arg_content = escapes(arg_content)
            temp = str(arg_content)
        elif arg_type == 'bool':
            if arg_content == 'true':
                temp = True
            else:
                temp = False
        elif arg_type == 'nil':
            sys.exit(53)
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = sym_arithm(var_frame_sym, temp, var_name_sym, 'blank')
        else:
            sys.exit(32)


def inst_eq(arg_type, arg_content, arg, var_frame, var_name):
    global temp
    if arg == 1:
        check_var(arg_type, arg_content)
        temp = 0
    elif arg == 3:
        if arg_type == 'int':
            if type(temp) == int:
                try:
                    int(arg_content)
                except:
                    sys.exit(32)
                if temp == int(arg_content):
                    temp = True
                else:
                    temp = False
            elif temp == 'nil':
                temp = False
            else:
                sys.exit(53)
            var_processor(var_frame, bool(temp), var_name, 'bool')
        elif arg_type == 'string':
            if type(temp) == int or type(temp) == bool:
                sys.exit(53)

            arg_content = escapes(arg_content)
            if temp == 'nil':
                temp = False
            elif temp == arg_content:
                temp = True
            else:
                temp = False

            var_processor(var_frame, bool(temp), var_name, 'bool')
        elif arg_type == 'bool':
            if type(temp) == int:
                sys.exit(53)
            elif type(temp) == bool:
                if arg_content == 'true':
                    if temp:
                        temp = True
                    else:
                        temp = False
                else:
                    if temp:
                        temp = False
                    else:
                        temp = True
            elif temp == 'nil':
                temp = False
            else:
                sys.exit(53)
            var_processor(var_frame, bool(temp), var_name, 'bool')
        elif arg_type == 'nil':
            if temp == 'nil':
                temp = True
            else:
                temp = False
            var_processor(var_frame, bool(temp), var_name, 'bool')

        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(temp) == type(var_array_gf[var_name_sym]):
                    if type(temp) == str:
                        pass
                    if temp == var_array_gf[var_name_sym]:
                        temp = True
                    else:
                        temp = False
                elif var_array_gf[var_name_sym] == 'nil':
                    if temp == 'nil':
                        temp = True
                    else:
                        temp = False
                elif temp == 'nil':
                    temp = False
                else:
                    sys.exit(53)
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(temp) == type(call_varback_stack_tf[-1][var_name_sym]):
                    if type(temp) == str:
                        pass
                    if temp == call_varback_stack_tf[-1][var_name_sym]:
                        temp = True
                    else:
                        temp = False
                elif call_varback_stack_tf[-1][var_name_sym] == 'nil':
                    if temp == 'nil':
                        temp = True
                    else:
                        temp = False
                elif temp == 'nil':
                    temp = False
                else:
                    sys.exit(53)
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(temp) == type(call_varback_stack_lf[-1][var_name_sym]):
                    if type(temp) == str:
                        pass
                    if temp == call_varback_stack_lf[-1][var_name_sym]:
                        temp = True
                    else:
                        temp = False
                elif call_varback_stack_lf[-1][var_name_sym] == 'nil':
                    if temp == 'nil':
                        temp = True
                    else:
                        temp = False
                elif temp == 'nil':
                    temp = False
                else:
                    sys.exit(53)

            var_processor(var_frame, bool(temp), var_name, 'bool')
        else:
            sys.exit(32)
    else:
        if arg_type == 'int':
            try:
                int(arg_content)
            except:
                sys.exit(32)
            temp = int(arg_content)
        elif arg_type == 'string':
            temp = str(arg_content)
            temp = escapes(temp)
        elif arg_type == 'bool':
            if arg_content == 'true':
                temp = True
            else:
                temp = False
        elif arg_type == 'nil':
            temp = 'nil'
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = sym_arithm(var_frame_sym, arg_content,
                              var_name_sym, 'blank')
        else:
            sys.exit(32)


def inst_andor(arg_type, arg_content, arg, var_frame, var_name, op):
    global temp
    if arg == 1:
        check_var(arg_type, arg_content)
        temp = 0
    elif arg == 3:
        if arg_type == 'bool':
            if arg_content == 'true':
                if op == 'and':
                    temp = temp and True
                if op == 'or':
                    temp = temp or True
                if temp:
                    temp = True
                else:
                    temp = False
            else:
                if op == 'and':
                    temp = temp and False
                if op == 'or':
                    temp = temp or False
                if temp:
                    temp = True
                else:
                    temp = False

            var_processor(var_frame, bool(temp), var_name, 'bool')
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(var_array_gf[var_name_sym]) == bool:
                    pass
                else:
                    sys.exit(53)
                if var_array_gf[var_name_sym]:
                    if op == 'and':
                        temp = True and temp
                    if op == 'or':
                        temp = True or temp
                else:
                    if op == 'and':
                        temp = False and temp
                    if op == 'or':
                        temp = False or temp
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_tf[-1][var_name_sym]) == bool:
                    pass
                else:
                    sys.exit(53)
                if call_varback_stack_tf[-1][var_name_sym]:
                    if op == 'and':
                        temp = True and temp
                    if op == 'or':
                        temp = True or temp
                else:
                    if op == 'and':
                        temp = False and temp
                    if op == 'or':
                        temp = False or temp
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_lf[-1][var_name_sym]) == bool:
                    pass
                else:
                    sys.exit(53)
                if call_varback_stack_lf[-1][var_name_sym]:
                    if op == 'and':
                        temp = True and temp
                    if op == 'or':
                        temp = True or temp
                else:
                    if op == 'and':
                        temp = False and temp
                    if op == 'or':
                        temp = False or temp

            var_processor(var_frame, bool(temp), var_name, 'bool')
        else:
            sys.exit(53)
    else:
        if arg_type == 'bool':
            if arg_content == 'true':
                temp = True
            else:
                temp = False
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(var_array_gf[var_name_sym]) == bool:
                    pass
                else:
                    sys.exit(53)
                if var_array_gf[var_name_sym]:
                    temp = True
                else:
                    temp = False
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_tf[-1][var_name_sym]) == bool:
                    pass
                else:
                    sys.exit(53)
                if call_varback_stack_tf[-1][var_name_sym]:
                    temp = True
                else:
                    temp = False
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_lf[-1][var_name_sym]) == bool:
                    pass
                else:
                    sys.exit(53)
                if call_varback_stack_lf[-1][var_name_sym]:
                    temp = True
                else:
                    temp = False
        else:
            sys.exit(53)


def inst_not(arg_type, arg_content, arg, var_frame, var_name):
    global temp
    if arg == 1:
        check_var(arg_type, arg_content)
        temp = 0
    else:
        if arg_type == 'bool':
            if arg_content == 'true':
                temp = False
            else:
                temp = True

            var_processor(var_frame, bool(temp), var_name, 'bool')
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(var_array_gf[var_name_sym]) == bool:
                    if var_array_gf[var_name_sym]:
                        temp = False
                    else:
                        temp = True
                else:
                    sys.exit(53)

            if var_frame_sym == 'TF' and tf_frame:
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_tf[-1][var_name_sym]) == bool:
                    if call_varback_stack_tf[-1][var_name_sym]:
                        temp = False
                    else:
                        temp = True
                else:
                    sys.exit(53)
            if var_frame_sym == 'LF' and lf_frame:
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_lf[-1][var_name_sym]) == bool:
                    if call_varback_stack_lf[-1][var_name_sym]:
                        temp = False
                    else:
                        temp = True
                else:
                    sys.exit(53)

            var_processor(var_frame, bool(temp), var_name, 'bool')
        else:
            sys.exit(53)


def inst_inttochar(arg_type, arg_content, arg, var_frame, var_name):
    global temp
    if arg == 1:
        check_var(arg_type, arg_content)
        temp = 0
    else:
        if arg_type == 'int':
            try:
                int(arg_content)
            except:
                sys.exit(32)
            if int(arg_content) < 0 or int(arg_content) > 127:
                sys.exit(58)
            var_processor(var_frame, chr(int(arg_content)), var_name, 'raw')
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = False
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(var_array_gf[var_name_sym]) == int:
                    if var_array_gf[var_name_sym] < 0 or var_array_gf[var_name_sym] > 127:
                        sys.exit(58)
                    temp = chr(var_array_gf[var_name_sym])
                else:
                    sys.exit(53)
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_tf[-1][var_name_sym]) == int:
                    if call_varback_stack_tf[-1][var_name_sym] < 0 or call_varback_stack_tf[-1][var_name_sym] > 127:
                        sys.exit(58)
                    temp = chr(call_varback_stack_tf[-1][var_name_sym])
                else:
                    sys.exit(53)
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_lf[-1][var_name_sym]) == int:
                    if call_varback_stack_lf[-1][var_name_sym] < 0 or call_varback_stack_lf[-1][var_name_sym] > 127:
                        sys.exit(58)
                    temp = chr(call_varback_stack_lf[-1][var_name_sym])
                else:
                    sys.exit(53)

            var_processor(var_frame, temp, var_name, 'raw')
        else:
            sys.exit(53)


def inst_stritoint(arg_type, arg_content, arg, var_frame, var_name):
    global temp
    if arg == 1:
        temp = 0
        check_var(arg_type, arg_content)
    elif arg == 3:
        if arg_type == 'int':
            try:
                int(arg_content)
            except:
                sys.exit(32)
            if int(arg_content) < 0:
                sys.exit(58)
            if var_frame == 'GF':
                if len(temp) <= int(arg_content):
                    sys.exit(58)
                else:
                    var_array_gf[var_name] = ord(temp[int(arg_content)])
            if var_frame == 'TF' and tf_frame:
                if len(temp) <= int(arg_content):
                    sys.exit(58)
                else:
                    call_varback_stack_tf[-1][var_name] = ord(
                        temp[int(arg_content)])
            if var_frame == 'LF' and lf_frame:
                if len(temp) <= int(arg_content):
                    sys.exit(58)
                else:
                    call_varback_stack_lf[-1][var_name] = ord(
                        temp[int(arg_content)])

        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)

            temp_stri2int = ''
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if len(arg_content) > 1:
                    temp_stri2int = var_array_gf[var_name_sym]
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if len(arg_content) > 1:
                    temp_stri2int = call_varback_stack_tf[-1][var_name_sym]
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if len(arg_content) > 1:
                    temp_stri2int = call_varback_stack_lf[-1][var_name_sym]

            if type(temp_stri2int) == int:
                pass
            else:
                sys.exit(58)

            if var_frame == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if len(temp) <= var_array_gf[var_name_sym]:
                    sys.exit(58)
                else:
                    var_array_gf[var_name] = ord(temp[temp_stri2int])
            if var_frame == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if len(temp) <= call_varback_stack_tf[-1][var_name_sym]:
                    sys.exit(58)
                else:
                    call_varback_stack_tf[-1][var_name] = ord(
                        temp[temp_stri2int])
            if var_frame == 'LF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if len(temp) <= call_varback_stack_lf[-1][var_name_sym]:
                    sys.exit(58)
                else:
                    call_varback_stack_lf[-1][var_name] = ord(
                        temp[temp_stri2int])

        else:
            sys.exit(53)
    else:
        if arg_type == 'string':
            temp = arg_content
            temp = escapes(temp)
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(var_array_gf[var_name_sym]) == str:
                    temp = var_array_gf[var_name_sym]
                else:
                    sys.exit(53)
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_tf[-1][var_name_sym]) == str:
                    temp = call_varback_stack_tf[-1][var_name_sym]
                else:
                    sys.exit(53)
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_lf[-1][var_name_sym]) == str:
                    temp = call_varback_stack_lf[-1][var_name_sym]
                else:
                    sys.exit(53)
        else:
            sys.exit(53)


def inst_read(arg_type, arg_content, arg, var_frame, var_name):
    if arg == 1:
        check_var(arg_type, arg_content)
    else:
        read_in = ''
        if arg_content == 'int':
            try:
                read_in = (input_file.pop(0)).strip()
            except:
                var_processor(var_frame, 'nil', var_name, 'raw')
                return
            try:
                int(read_in)
                var_processor(var_frame, int(read_in), var_name, 'raw')
            except ValueError:
                var_processor(var_frame, 'nil', var_name, 'raw')
        if arg_content == 'float':
            try:
                read_in = (input_file.pop(0)).strip()
            except:
                var_processor(var_frame, 'nil', var_name, 'raw')
                return
            try:
                var_processor(var_frame, float(
                    float(read_in)), var_name, 'raw')
            except:
                try:
                    var_processor(var_frame, float(
                        float.fromhex(read_in)), var_name, 'raw')
                except:
                    var_processor(var_frame, 'nil', var_name, 'raw')

        elif arg_content == 'string':
            try:
                read_in = input_file.pop(0)
            except:
                var_processor(var_frame, 'nil', var_name, 'raw')
                return
            var_processor(var_frame, str(read_in), var_name, 'raw')

        elif arg_content == 'bool':
            try:
                read_in = (input_file.pop(0)).strip()
            except:
                var_processor(var_frame, 'nil', var_name, 'raw')
                return
            if re.match(r'(?i)true$', read_in):
                read_in = True
            else:
                read_in = False
            if var_frame == 'GF':
                var_array_gf[var_name] = read_in
            if var_frame == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                call_varback_stack_tf[-1][var_name] = read_in
            if var_frame == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                call_varback_stack_lf[-1][var_name] = read_in


def inst_write(arg_type, arg_content):
    if arg_type == 'string' or arg_type == 'bool':
        if arg_content == 'nil' or arg_content == '':
            print('', end='')
        else:
            arg_content = escapes(arg_content)
            print(arg_content, end='')
    elif arg_type == 'int':
        try:
            int(arg_content)
            print(int(arg_content), end='')
        except:
            sys.exit(53)
    elif arg_type == 'float':
        try:
            print(float.hex(float(arg_content)), end='')
        except:
            try:
                print(float.hex(float.fromhex(arg_content)), end='')
            except:
                sys.exit(53)
    elif arg_type == 'nil':
        if arg_content == 'nil':
            print('', end='')
        else:
            sys.exit(32)

    elif arg_type == 'var':
        try:
            var_frame = re.search(
                r'^(GF|TF|LF)@(\_|\-|\$|\&|\%|\*|\!|\?*\w+)+$', arg_content).group(1)
            var_name = re.search(
                r'^(GF|TF|LF)@(\_|\-|\$|\&|\%|\*|\!|\?*\w+)+$', arg_content).group(2)
        except:
            sys.exit(32)
        if var_frame == 'GF':
            if var_name in var_array_gf:
                temp_write = ''
                if str(var_array_gf[var_name]) == 'nil':
                    temp_write = 'nil@nil'
                elif str(var_array_gf[var_name]) == 'nil@nil':
                    temp_write = 'nil'
                elif var_array_gf[var_name] == None:
                    sys.exit(56)
                elif type(var_array_gf[var_name]) == int:
                    pass
                elif type(var_array_gf[var_name]) == float:
                    temp_write = float.hex(var_array_gf[var_name])
                elif type(var_array_gf[var_name]) == bool:
                    if var_array_gf[var_name]:
                        temp_write = 'true'
                    else:
                        temp_write = 'false'
                if temp_write != '':
                    if temp_write == 'nil@nil':
                        print('', end='')
                    else:
                        print(temp_write, end='')
                else:
                    print(var_array_gf[var_name], end='')
            else:
                sys.exit(54)

        elif var_frame == 'LF':
            if len(call_varback_stack_lf) > 0:
                pass
            else:
                sys.exit(55)
            if lf_frame or len(call_varback_stack_lf) > 0:
                if var_name in call_varback_stack_lf[-1]:
                    temp_write = ''
                    if str(call_varback_stack_lf[-1][var_name]) == 'nil':
                        temp_write = 'nil@nil'
                    elif str(call_varback_stack_lf[-1][var_name]) == 'nil@nil':
                        temp_write = 'nil'
                    elif call_varback_stack_lf[-1][var_name] == None:
                        sys.exit(56)
                    elif type(call_varback_stack_lf[-1][var_name]) == int:
                        pass
                    elif type(call_varback_stack_lf[-1][var_name]) == float:
                        temp_write = float.hex(
                            call_varback_stack_lf[-1][var_name])
                    elif type(call_varback_stack_lf[-1][var_name]) == bool:
                        if call_varback_stack_lf[-1][var_name]:
                            temp_write = 'true'
                        else:
                            temp_write = 'false'
                    if temp_write != '':
                        if temp_write == 'nil@nil':
                            print('', end='')
                        else:
                            print(temp_write, end='')
                    else:
                        print(call_varback_stack_lf[-1][var_name], end='')

                else:
                    sys.exit(54)
            else:
                print(str(call_varback_stack_lf))
                sys.exit(55)

        elif var_frame == 'TF':
            if len(call_varback_stack_tf) > 0:
                pass
            else:
                sys.exit(55)
            if tf_frame or len(call_varback_stack_tf[-1]) > 0:
                if var_name in call_varback_stack_tf[-1]:
                    temp_write = ''
                    if str(call_varback_stack_tf[-1][var_name]) == 'nil':
                        temp_write = 'nil@nil'
                    elif str(call_varback_stack_tf[-1][var_name]) == 'nil@nil':
                        temp_write = 'nil'
                    elif call_varback_stack_tf[-1][var_name] == None:
                        sys.exit(56)
                    elif type(call_varback_stack_tf[-1][var_name]) == int:
                        pass
                    elif type(call_varback_stack_tf[-1][var_name]) == float:
                        temp_write = float.hex(
                            call_varback_stack_tf[-1][var_name])
                    elif type(call_varback_stack_tf[-1][var_name]) == bool:
                        if call_varback_stack_tf[-1][var_name]:
                            temp_write = 'true'
                        else:
                            temp_write = 'false'
                    if temp_write != '':
                        if temp_write == 'nil@nil':
                            print('', end='')
                        else:
                            print(temp_write, end='')
                    else:
                        print(call_varback_stack_tf[-1][var_name], end='')
                else:
                    sys.exit(54)
            else:
                sys.exit(55)
        else:
            sys.exit(32)
    else:
        sys.exit(32)


def inst_concat(arg_type, arg_content, arg, var_frame, var_name):
    global temp
    if arg == 1:
        temp = str('')
        check_var(arg_type, arg_content)
    else:
        if arg_type == 'string':
            temp = str(temp) + arg_content
            if arg == 3:
                var_processor(var_frame, temp, var_name, 'raw')
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(var_array_gf[var_name_sym]) == str:
                    pass
                else:
                    sys.exit(53)
                temp = str(temp) + var_array_gf[var_name_sym]
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_tf[-1][var_name_sym]) == str:
                    pass
                else:
                    sys.exit(53)
                temp = str(temp) + call_varback_stack_tf[-1][var_name_sym]
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_lf[-1][var_name_sym]) == str:
                    pass
                else:
                    sys.exit(53)
                temp = str(temp) + call_varback_stack_lf[-1][var_name_sym]
            var_processor(var_frame, temp, var_name, 'raw')
        else:
            sys.exit(53)


def inst_strlen(arg_type, arg_content, arg, var_frame, var_name):
    if arg == 1:
        check_var(arg_type, arg_content)
    else:
        if arg_type == 'string':
            var_processor(var_frame, len(arg_content), var_name, 'raw')
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)

            strlen_sym = 0
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if var_array_gf[var_name_sym] == 'nil':
                    sys.exit(53)
                if type(var_array_gf[var_name_sym]) == str:
                    strlen_sym = len(var_array_gf[var_name_sym])
                else:
                    sys.exit(53)
            if var_frame_sym == 'TF':
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if call_varback_stack_tf[-1][var_name_sym] == 'nil':
                    sys.exit(53)
                if not(tf_frame):
                    sys.exit(55)
                if type(call_varback_stack_tf[-1][var_name_sym]) == str:
                    strlen_sym = len(call_varback_stack_tf[-1][var_name_sym])
                else:
                    sys.exit(53)
            if var_frame_sym == 'LF':
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if call_varback_stack_lf[-1][var_name_sym] == 'nil':
                    sys.exit(53)
                if not(lf_frame):
                    sys.exit(55)
                if type(call_varback_stack_lf[-1][var_name_sym]) == str:
                    strlen_sym = len(call_varback_stack_lf[-1][var_name_sym])
                else:
                    sys.exit(53)
            var_processor(var_frame, strlen_sym, var_name, 'raw')
        else:
            sys.exit(53)


def inst_getchar(arg_type, arg_content, arg, var_frame, var_name):
    global temp
    if arg == 1:
        temp = ''
        check_var(arg_type, arg_content)
    elif arg == 3:
        if arg_type == 'int':
            try:
                int(arg_content)
            except:
                sys.exit(32)
            if len(temp) >= (int(arg_content) + 1) and int(arg_content) >= 0:
                var_processor(
                    var_frame, temp[int(arg_content)], var_name, 'raw')
            else:
                sys.exit(58)
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)

            index = 0
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(var_array_gf[var_name_sym]) == int:
                    index = var_array_gf[var_name_sym]
                else:
                    sys.exit(32)
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_tf[-1][var_name_sym]) == int:
                    index = call_varback_stack_tf[-1][var_name_sym]
                else:
                    sys.exit(32)
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_lf[-1][var_name_sym]) == int:
                    index = call_varback_stack_lf[-1][var_name_sym]
                else:
                    sys.exit(32)

            if len(temp) >= (index + 1) and index >= 0:
                var_processor(var_frame, temp[index], var_name, 'raw')
            else:
                sys.exit(58)
        else:
            sys.exit(53)

    else:
        if arg_type == 'string':
            temp = arg_content
            temp = escapes(temp)
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(var_array_gf[var_name_sym]) == str:
                    temp = var_array_gf[var_name_sym]
                else:
                    sys.exit(53)
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_tf[-1][var_name_sym]) == str:
                    temp = call_varback_stack_tf[-1][var_name_sym]
                else:
                    sys.exit(53)
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_lf[-1][var_name_sym]) == str:
                    temp = call_varback_stack_lf[-1][var_name_sym]
                else:
                    sys.exit(53)
        else:
            sys.exit(53)


def inst_setchar(arg_type, arg_content, arg, var_frame, var_name):
    global temp
    if arg == 1:
        temp = 0
        check_var(arg_type, arg_content)
    elif arg == 3:
        if arg_type == 'string':
            if len(arg_content) < 1:
                sys.exit(58)
            if len(arg_content) > 1:
                arg_content = escapes(arg_content)
                arg_content = arg_content[:1]
            if var_frame == 'GF':
                if var_array_gf[var_name] == None:
                    sys.exit(56)
                if type(var_array_gf[var_name]) == str:
                    if var_array_gf[var_name] == 'nil':
                        sys.exit(53)
                    if temp >= (len(var_array_gf[var_name])) or temp < 0:
                        sys.exit(58)
                    else:
                        var_array_gf[var_name] = (var_array_gf[var_name])[
                            :temp] + arg_content + (var_array_gf[var_name])[temp+1:]
                else:
                    sys.exit(53)
            if var_frame == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name] == None:
                    sys.exit(56)
                if type(call_varback_stack_tf[-1][var_name]) == str:
                    if call_varback_stack_tf[-1][var_name] == 'nil':
                        sys.exit(53)
                    if temp >= (len(call_varback_stack_tf[-1][var_name])) or temp < 0:
                        sys.exit(58)
                    else:
                        call_varback_stack_tf[-1][var_name] = (call_varback_stack_tf[-1][var_name])[
                            :temp] + arg_content + (call_varback_stack_tf[-1][var_name])[temp+1:]
                else:
                    sys.exit(53)
            if var_frame == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name] == None:
                    sys.exit(56)
                if type(call_varback_stack_lf[-1][var_name]) == str:
                    if call_varback_stack_lf[-1][var_name] == 'nil':
                        sys.exit(53)
                    if temp >= (len(call_varback_stack_lf[-1][var_name])) or temp < 0:
                        sys.exit(58)
                    else:
                        call_varback_stack_lf[-1][var_name] = (call_varback_stack_lf[-1][var_name])[
                            :temp] + arg_content + (call_varback_stack_lf[-1][var_name])[temp+1:]
                else:
                    sys.exit(53)

        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)

            temp_setchar = ''
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(var_array_gf[var_name_sym]) == str:
                    if len(arg_content) > 1:
                        temp_setchar = var_array_gf[var_name_sym][:1]
                else:
                    sys.exit(53)
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_tf[-1][var_name_sym]) == str:
                    if len(arg_content) > 1:
                        temp_setchar = call_varback_stack_tf[-1][var_name_sym][:1]
                else:
                    sys.exit(53)
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_lf[-1][var_name_sym]) == str:
                    if len(arg_content) > 1:
                        temp_setchar = call_varback_stack_lf[-1][var_name_sym][:1]
                else:
                    sys.exit(53)

            if var_frame == 'GF':
                if temp >= (len(var_array_gf[var_name])):
                    sys.exit(58)
                else:
                    var_array_gf[var_name] = (var_array_gf[var_name])[
                        :temp] + temp_setchar + (var_array_gf[var_name])[temp+1:]
            if var_frame == 'TF' and tf_frame:
                if temp >= (len(call_varback_stack_tf[-1][var_name])):
                    sys.exit(58)
                else:
                    call_varback_stack_tf[-1][var_name] = (call_varback_stack_tf[-1][var_name])[
                        :temp] + temp_setchar + (call_varback_stack_tf[-1][var_name])[temp+1:]
            if var_frame == 'LF' and lf_frame:
                if temp >= (len(call_varback_stack_lf[-1][var_name])):
                    sys.exit(58)
                else:
                    call_varback_stack_lf[-1][var_name] = (call_varback_stack_lf[-1][var_name])[
                        :temp] + temp_setchar + (call_varback_stack_lf[-1][var_name])[temp+1:]

        else:
            sys.exit(53)
    else:
        if arg_type == 'int':
            try:
                int(arg_content)
            except:
                sys.exit(32)
            temp = int(arg_content)
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(var_array_gf[var_name_sym]) == int:
                    temp = var_array_gf[var_name_sym]
                else:
                    sys.exit(53)
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_tf[-1][var_name_sym]) == int:
                    temp = call_varback_stack_tf[-1][var_name_sym]
                else:
                    sys.exit(53)
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_lf[-1][var_name_sym]) == int:
                    temp = call_varback_stack_lf[-1][var_name_sym]
                else:
                    sys.exit(53)
        else:
            sys.exit(53)


def inst_type(arg_type, arg_content, arg, var_frame, var_name):
    if arg == 1:
        check_var(arg_type, arg_content)
    else:
        if arg_type == 'int' or arg_type == 'string' or arg_type == 'bool' or arg_type == 'float':
            var_processor(var_frame, arg_type, var_name, 'raw')
        elif arg_type == 'nil':
            var_processor(var_frame, arg_type+'@'+arg_type, var_name, 'raw')
        else:
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp_type = ''
            if var_frame_sym == 'GF':
                if type(var_array_gf[var_name_sym]) == int:
                    temp_type = 'int'
                elif type(var_array_gf[var_name_sym]) == float:
                    temp_type = 'float'
                elif type(var_array_gf[var_name_sym]) == bool:
                    temp_type = 'bool'
                elif type(var_array_gf[var_name_sym]) == str:
                    if var_array_gf[var_name_sym] == 'nil@nil' or var_array_gf[var_name_sym] == 'nil':
                        temp_type = 'nil@nil'
                    else:
                        temp_type = 'string'
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if type(call_varback_stack_tf[-1][var_name_sym]) == int:
                    temp_type = 'int'
                elif type(call_varback_stack_tf[-1][var_name_sym]) == bool:
                    temp_type = 'bool'
                elif type(call_varback_stack_tf[-1][var_name_sym]) == str:
                    if call_varback_stack_tf[-1][var_name_sym] == 'nil':
                        temp_type = 'nil'
                    else:
                        temp_type = 'string'
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if type(call_varback_stack_lf[-1][var_name_sym]) == int:
                    temp_type = 'int'
                elif type(call_varback_stack_lf[-1][var_name_sym]) == bool:
                    temp_type = 'bool'
                elif type(call_varback_stack_lf[-1][var_name_sym]) == str:
                    if call_varback_stack_lf[-1][var_name_sym] == 'nil':
                        temp_type = 'nil'
                    else:
                        temp_type = 'string'
            var_processor(var_frame, temp_type, var_name, 'raw')


def inst_jump(arg_type, arg_content):
    if arg_type == 'label':
        pass
    else:
        sys.exit(32)
    if arg_content in labels_array:
        return int(labels_array[arg_content])
    else:
        sys.exit(32)


def inst_jumpifeq(arg_type, arg_content, arg):
    global temp
    if arg == 1:
        if arg_content in labels_array:
            return int(labels_array[arg_content])
        else:
            sys.exit(52)

    elif arg == 3:
        if arg_type == 'int':
            if type(temp) == int or temp == 'nil':
                try:
                    int(arg_content)
                except:
                    sys.exit(32)
                if temp == int(arg_content):
                    return True
                else:
                    return False
            else:
                sys.exit(53)
        elif arg_type == 'string':
            if type(temp) == str or temp == 'nil':
                arg_content = escapes(arg_content)
                if temp == arg_content:
                    return True
                else:
                    return False
            else:
                sys.exit(53)
        elif arg_type == 'bool':
            if type(temp) == bool or temp == 'nil':
                if arg_content == 'true':
                    arg_content = True
                else:
                    arg_content = False
                if temp == bool(arg_content):
                    return True
                else:
                    return False
            else:
                sys.exit(53)
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(temp) == type(var_array_gf[var_name_sym]):
                    if temp == var_array_gf[var_name_sym]:
                        return True
                    else:
                        return False
                else:
                    sys.exit(53)
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(temp) == type(call_varback_stack_tf[-1][var_name_sym]):
                    if temp == call_varback_stack_tf[-1][var_name_sym]:
                        return True
                    else:
                        return False
                else:
                    sys.exit(53)
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(temp) == type(call_varback_stack_lf[-1][var_name_sym]):
                    if temp == call_varback_stack_lf[-1][var_name_sym]:
                        return True
                    else:
                        return False
                else:
                    sys.exit(53)
        elif arg_type == 'nil':
            if temp == 'nil':
                return True
            else:
                return False
        else:
            sys.exit(32)

    else:
        if arg_type == 'int':
            try:
                int(arg_content)
            except:
                sys.exit(32)
            temp = int(arg_content)
        elif arg_type == 'string':
            temp = arg_content
            temp = escapes(temp)

        elif arg_type == 'bool':
            if arg_content == 'true':
                temp = True
            else:
                temp = False

        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = sym_arithm(var_frame_sym, temp, var_name_sym, 'blank')
        elif arg_type == 'nil':
            temp = str('nil')
        else:
            sys.exit(32)


def inst_jumpifneq(arg_type, arg_content, arg):
    global temp
    if arg == 1:
        temp = 0
        if arg_content in labels_array:
            return int(labels_array[arg_content])
        else:
            sys.exit(52)
    elif arg == 3:
        if arg_type == 'int':
            if type(temp) == int or temp == 'nil':
                try:
                    int(arg_content)
                except:
                    sys.exit(32)
                if temp == int(arg_content):
                    return False
                else:
                    return True
            else:
                sys.exit(53)
        elif arg_type == 'string':
            if type(temp) == str or temp == 'nil':
                arg_content = escapes(arg_content)
                if temp == arg_content:
                    return False
                else:
                    return True
            else:
                sys.exit(53)
        elif arg_type == 'bool':
            if type(temp) == bool or temp == 'nil':
                if arg_content == 'true':
                    arg_content = True
                else:
                    arg_content = False
                if temp == bool(arg_content):
                    return False
                else:
                    return True
            else:
                sys.exit(53)
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(temp) == type(var_array_gf[var_name_sym]):
                    if temp != var_array_gf[var_name_sym]:
                        return False
                    else:
                        return True
                else:
                    sys.exit(53)
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(temp) == type(call_varback_stack_tf[-1][var_name_sym]):
                    if temp == call_varback_stack_tf[-1][var_name_sym]:
                        return False
                    else:
                        return True
                else:
                    sys.exit(53)
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(temp) == type(call_varback_stack_lf[-1][var_name_sym]):
                    if temp == call_varback_stack_lf[-1][var_name_sym]:
                        return False
                    else:
                        return True
                else:
                    sys.exit(53)
        elif arg_type == 'nil':
            if temp == 'nil':
                return False
            else:
                return True
        else:
            sys.exit(32)
    else:
        if arg_type == 'int':
            try:
                int(arg_content)
            except:
                sys.exit(32)
            temp = int(arg_content)
        elif arg_type == 'string':
            temp = arg_content
            temp = escapes(temp)

        elif arg_type == 'bool':
            if arg_content == 'true':
                temp = True
            else:
                temp = False
        elif arg_type == 'var':
            temp = int(temp)
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = sym_arithm(var_frame_sym, temp, var_name_sym, 'blank')
        elif arg_type == 'nil':
            temp = str('nil')
        else:
            sys.exit(32)


def inst_exit(arg_type, arg_content):
    if arg_type == 'int':
        try:
            int(arg_content)
        except:
            sys.exit(32)
        if int(arg_content) >= 0 and int(arg_content) <= 49:
            sys.exit(int(arg_content))
        else:
            sys.exit(57)
    elif arg_type == 'var':
        var_frame_sym, var_name_sym = check_var(arg_type, arg_content)

        if var_frame_sym == 'GF':
            if var_array_gf[var_name_sym] == None:
                sys.exit(56)
            if type(var_array_gf[var_name_sym]) == int:
                sys.exit(var_array_gf[var_name_sym])
            else:
                sys.exit(53)
        if var_frame_sym == 'TF':
            if not(tf_frame):
                sys.exit(55)
            if call_varback_stack_tf[-1][var_name_sym] == None:
                sys.exit(56)
            if type(call_varback_stack_tf[-1][var_name_sym]) == int:
                sys.exit(call_varback_stack_tf[-1][var_name_sym])
            else:
                sys.exit(53)
        if var_frame_sym == 'LF':
            if not(lf_frame):
                sys.exit(55)
            if call_varback_stack_lf[-1][var_name_sym] == None:
                sys.exit(56)
            if type(call_varback_stack_lf[-1][var_name_sym]) == int:
                sys.exit(call_varback_stack_lf[-1][var_name_sym])
            else:
                sys.exit(53)
    else:
        sys.exit(53)


def inst_dprint(arg_type, arg_content):
    if arg_type == 'int' or arg_type == 'string' or arg_type == 'bool':
        sys.stderr.write(arg_content)
        sys.stderr.write("\n")
    elif arg_type == 'var':
        var_frame_sym, var_name_sym = check_var(arg_type, arg_content)

        if var_frame_sym == 'GF':
            if var_array_gf[var_name_sym] == None:
                sys.exit(56)
            sys.stderr.write(var_array_gf[var_name_sym])
        if var_frame_sym == 'TF':
            if not(tf_frame):
                sys.exit(55)
            if call_varback_stack_tf[-1][var_name_sym] == None:
                sys.exit(56)
            sys.stderr.write(var_array_tf[var_name_sym])
        if var_frame_sym == 'LF':
            if not(lf_frame):
                sys.exit(55)
            if call_varback_stack_lf[-1][var_name_sym] == None:
                sys.exit(56)
            sys.stderr.write(var_array_lf[var_name_sym])
    else:
        sys.exit(32)


""" Implementácia rozšírenia FLOAT """

def inst_inttofloat(arg_type, arg_content, arg, var_frame, var_name):
    global temp
    if arg == 1:
        check_var(arg_type, arg_content)
        temp = 0
    else:
        if arg_type == 'int':
            try:
                int(arg_content)
            except:
                sys.exit(32)
            try:
                var_processor(var_frame, float(
                    int((arg_content))), var_name, 'raw')
            except:
                sys.exit(32)
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = False
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(var_array_gf[var_name_sym]) == int:
                    try:
                        temp = float(var_array_gf[var_name_sym])
                    except:
                        sys.exit(32)
                else:
                    sys.exit(53)
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_tf[-1][var_name_sym]) == int:
                    try:
                        temp = float(var_array_tf[var_name_sym])
                    except:
                        sys.exit(32)
                else:
                    sys.exit(53)
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_lf[-1][var_name_sym]) == int:
                    try:
                        temp = float(var_array_lf[var_name_sym])
                    except:
                        sys.exit(32)
                else:
                    sys.exit(53)

            var_processor(var_frame, float(temp), var_name, 'raw')
        else:
            sys.exit(53)


def inst_floattoint(arg_type, arg_content, arg, var_frame, var_name):
    global temp
    if arg == 1:
        check_var(arg_type, arg_content)
        temp = 0
    else:
        if arg_type == 'float':
            try:
                int(arg_content)
            except:
                sys.exit(32)
            try:
                var_processor(var_frame,
                              int((arg_content)), var_name, 'raw')
            except:
                sys.exit(32)
        elif arg_type == 'var':
            var_frame_sym, var_name_sym = check_var(arg_type, arg_content)
            temp = False
            if var_frame_sym == 'GF':
                if var_array_gf[var_name_sym] == None:
                    sys.exit(56)
                if type(var_array_gf[var_name_sym]) == float:
                    try:
                        temp = int(var_array_gf[var_name_sym])
                    except:
                        sys.exit(32)
                else:
                    sys.exit(53)
            if var_frame_sym == 'TF':
                if not(tf_frame):
                    sys.exit(55)
                if call_varback_stack_tf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_tf[-1][var_name_sym]) == float:
                    try:
                        temp = int(var_array_tf[var_name_sym])
                    except:
                        sys.exit(32)
                else:
                    sys.exit(53)
            if var_frame_sym == 'LF':
                if not(lf_frame):
                    sys.exit(55)
                if call_varback_stack_lf[-1][var_name_sym] == None:
                    sys.exit(56)
                if type(call_varback_stack_lf[-1][var_name_sym]) == float:
                    try:
                        temp = int(var_array_lf[var_name_sym])
                    except:
                        sys.exit(32)
                else:
                    sys.exit(53)
            var_processor(var_frame, int(temp), var_name, 'raw')
        else:
            sys.exit(53)


""" Inicializácia pomocných premenných a kontrola xml štruktúri"""

xml_head = '<?xml version="1.0" encoding="UTF-8"?>'
if xml_head != xml_file.readline().strip():
    sys.exit(32)

""" Dictionaries """
var_array_gf = {}
var_array_lf = {}
var_array_tf = {}
labels_array = {}
""" Listy """
stack = []
call_pos = []
call_varback_stack_lf = []
call_varback_stack_tf = []
""" Premenné """
temp = 0
lines = 0
order = 0
tf_frame = False
lf_frame = False
""" STATI """
instructions_cnt = 0
vars_cnt = 0
""" xml_file to list """
xml_file = file_to_list(xml_file)

""" Kontrola program atributu xml """
if re.match(r'^<program language="IPPcode20"( name="\S*"){0,1}( description="\S*"){0,1}>$|^<program language="IPPcode20"( description="[a-zA-Z 1-9]*"){0,1}( name="[a-zA-z 1-9]*"){0,1}>$', xml_file[0]):
    pass
elif re.match(r'^<program language="IPPcode20"/>$', xml_file[0]):
    sys.exit(0)
else:
    if not re.match(r'^<.*>$', xml_file[0]):
        sys.exit(31)
    sys.exit(32)
lines = 1
if xml_file[-1] != "</program>":
    sys.exit(31)

""" Iterácia cez súbor xml """
while len(xml_file) > lines:
    iterate()


""" Implementácia rozšírenia STATI """

for arg in sys.argv:
    if arg == '--insts':
        if stats_file == None:
            sys.exit(10)
        else:
            stats_file.write(str(instructions_cnt)+'\n')
    if arg == '--vars':
        if stats_file == None:
            sys.exit(10)
        else:
            stats_file.write(str(vars_cnt)+'\n')


""" 
alias t="php parse.php < vole > out"
alias r="python interpret.py --source=out --input=in"
alias rr="t | r"
alias test='php test.php --directory=ipp-2020-tests-master/both/ --recursive > test.html'
"""
