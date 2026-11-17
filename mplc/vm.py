
"""
Entrega 4, terceira metade — a máquina virtual.
"""

import ast
from mplc.erros import ErroMPL


VALORES_PADRAO = {
    'inteiro': 0,
    'real': 0.0,
    'logico': False,
    'texto': ''
}


def executar(texto_mplb, saida):
    instrucoes = []

    if isinstance(texto_mplb, str):
        linhas = texto_mplb.splitlines()
    else:
        linhas = texto_mplb

    for numero, linha in enumerate(linhas, start=1):
        if isinstance(linha, (tuple, list)):
            inst = linha
        else:
            linha = linha.strip()

            if not linha:
                continue

            try:
                inst = ast.literal_eval(linha)
            except Exception as erro:
                raise ValueError(
                    f"Erro ao interpretar IR na linha {numero}: {linha!r}"
                ) from erro

        if not isinstance(inst, (tuple, list)) or not inst:
            raise ValueError(
                f"Instrução inválida na linha {numero}: {inst!r}"
            )

        instrucoes.append(inst)

    labels = {}
    funcs = {}

    for i, inst in enumerate(instrucoes):
        if inst[0] == 'LABEL':
            labels[inst[1]] = i

        elif inst[0] == 'FUNCAO':
            funcs[inst[1]] = (i, inst[3], inst[2])

    if 'principal' not in funcs:
        return

    pc = funcs['principal'][0]

    pilha = [{
        'locais': {},       # Temporários
        'escopos': [{
            'locais': {},
            'tipos': {}
        }],
        'ret': -1,
        'dest': None,
        'ret_tipo': funcs['principal'][2],
        'linha': 1
    }]

    pilha_operandos = []

    def buscar_variavel(nome, frame):
        for escopo in reversed(frame['escopos']):
            if nome in escopo['locais']:
                return escopo['locais'][nome]

        return None

    def buscar_tipo(nome, frame):
        for escopo in reversed(frame['escopos']):
            if nome in escopo['tipos']:
                return escopo['tipos'][nome]

        return None

    def get_val(v, frame):
        if isinstance(v, str):

            # Temporários.
            if v in frame['locais']:
                return frame['locais'][v]

            # Variáveis, respeitando sombreamento.
            for escopo in reversed(frame['escopos']):
                if v in escopo['locais']:
                    return escopo['locais'][v]

            if v == "verdadeiro":
                return True

            if v == "falso":
                return False

            if v.startswith('"'):
                return (
                    v[1:-1]
                    .replace('\\n', '\n')
                    .replace('\\t', '\t')
                    .replace('\\"', '"')
                    .replace('\\\\', '\\')
                )

            try:
                return int(v)
            except ValueError:
                try:
                    return float(v)
                except ValueError:
                    return v

        return v

    def guardar(dest, valor, frame):
        # Se for variável declarada, atualiza o escopo mais interno
        # em que ela existe. Caso contrário, é um temporário.
        for escopo in reversed(frame['escopos']):
            if dest in escopo['locais']:
                tipo = escopo['tipos'].get(dest)

                if tipo == 'real' and type(valor) is int:
                    valor = float(valor)

                escopo['locais'][dest] = valor
                return

        frame['locais'][dest] = valor

    def erro_execucao(mensagem):
        raise ErroMPL(
            'execucao',
            pilha[-1].get('linha', 1),
            1,
            mensagem
        )

    while pc < len(instrucoes):
        inst = instrucoes[pc]
        op = inst[0]

        frame = pilha[-1]

        if op == 'LINHA':
            frame['linha'] = int(inst[1])

        elif op == 'ABRE_ESCOPO':
            frame['escopos'].append({
                'locais': {},
                'tipos': {}
            })

        elif op == 'FECHA_ESCOPO':
            if len(frame['escopos']) > 1:
                frame['escopos'].pop()

        elif op == 'DECLARA':
            nome = inst[1]
            tipo = inst[2]

            escopo = frame['escopos'][-1]

            escopo['tipos'][nome] = tipo

            # Inicialização padrão de cada tipo.
            escopo['locais'][nome] = VALORES_PADRAO.get(
                tipo,
                None
            )

        elif op == 'COPIA':
            val = get_val(inst[2], frame)
            guardar(inst[1], val, frame)

        elif op == 'BINARIO':
            dest = inst[1]
            esq = get_val(inst[2], frame)
            operador = inst[3]
            dir_val = get_val(inst[4], frame)

            if operador == '+':
                res = esq + dir_val

            elif operador == '-':
                res = esq - dir_val

            elif operador == '*':
                res = esq * dir_val

            elif operador == '/':
                if dir_val == 0:
                    erro_execucao("divisao por zero")

                if type(esq) is int and type(dir_val) is int:
                    res = int(esq / dir_val)
                else:
                    res = esq / dir_val

            elif operador == '%':
                if dir_val == 0:
                    erro_execucao("resto por zero")

                res = esq - int(esq / dir_val) * dir_val

            elif operador == '==':
                res = esq == dir_val

            elif operador == '!=':
                res = esq != dir_val

            elif operador == '<':
                res = esq < dir_val

            elif operador == '<=':
                res = esq <= dir_val

            elif operador == '>':
                res = esq > dir_val

            elif operador == '>=':
                res = esq >= dir_val

            elif operador == 'e':
                res = esq and dir_val

            elif operador == 'ou':
                res = esq or dir_val

            else:
                res = None

            frame['locais'][dest] = res

        elif op == 'UNARIO':
            dest = inst[1]
            operador = inst[2]
            val = get_val(inst[3], frame)

            if operador == '-':
                res = -val
            elif operador == 'nao':
                res = not val
            else:
                res = None

            frame['locais'][dest] = res

        elif op == 'JUMP':
            pc = labels[inst[1]]
            continue

        elif op == 'JUMP_FALSO':
            if not get_val(inst[1], frame):
                pc = labels[inst[2]]
                continue

        elif op == 'PARAM':
            pilha_operandos.append(
                get_val(inst[1], frame)
            )

        elif op == 'CHAMA':
            dest = inst[1]
            nome_func = inst[2]
            num_args = inst[3]

            if len(pilha) >= 1000:
                erro_execucao("limite de recursao excedido")

            args_vals = [
                pilha_operandos.pop()
                for _ in range(num_args)
            ][::-1]

            target_pc, params_infos, ret_tipo = funcs[nome_func]

            novo_locais = {}
            novo_tipos = {}

            for (nome_p, tipo_p), val_p in zip(
                params_infos,
                args_vals
            ):
                if tipo_p == 'real' and type(val_p) is int:
                    val_p = float(val_p)

                novo_locais[nome_p] = val_p
                novo_tipos[nome_p] = tipo_p

            pilha.append({
                'locais': {},
                'escopos': [{
                    'locais': novo_locais,
                    'tipos': novo_tipos
                }],
                'ret': pc + 1,
                'dest': dest,
                'ret_tipo': ret_tipo,
                'linha': 1
            })

            pc = target_pc
            continue

        elif op == 'RETORNE':
            ret_val = (
                get_val(inst[1], frame)
                if inst[1] is not None
                else None
            )

            frame = pilha.pop()

            if frame['ret_tipo'] == 'real' and type(ret_val) is int:
                ret_val = float(ret_val)

            if not pilha:
                break

            pc = frame['ret']

            if frame['dest']:
                guardar(frame['dest'], ret_val, pilha[-1])

            continue

        elif op == 'ESCREVA':
            val = get_val(inst[1], frame)

            if val is True:
                saida_str = "verdadeiro"

            elif val is False:
                saida_str = "falso"

            elif type(val) is float:
                saida_str = f"{val:.6f}"

            else:
                saida_str = str(val)

            saida.write(saida_str + "\n")

        pc += 1
