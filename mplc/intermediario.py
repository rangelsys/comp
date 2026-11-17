
"""
Entrega 4, primeira metade — código de três endereços.
"""

from mplc.sintatico import (
    Declaracao, Atribuicao, Escreva, Se, Enquanto, Retorne,
    Chamada, Binario, Unario, Literal, Variavel, Bloco
)


class GeradorIR:
    def __init__(self):
        self.codigo = []
        self.temp_count = 0
        self.label_count = 0

    def novo_temp(self):
        nome = f"t{self.temp_count}"
        self.temp_count += 1
        return nome

    def novo_label(self):
        nome = f"L{self.label_count}"
        self.label_count += 1
        return nome

    def emitir(self, instrucao):
        self.codigo.append(instrucao)

    def gerar(self, arvore):
        for funcao in arvore.funcoes:
            self.visitar_funcao(funcao)
        return self.codigo

    def visitar_funcao(self, no):
        params = [(p.nome, p.tipo) for p in no.parametros]

        self.emitir((
            'FUNCAO',
            no.nome,
            no.tipo_retorno,
            params
        ))

        self.visitar_bloco(no.bloco)

        if no.tipo_retorno == 'vazio':
            self.emitir(('RETORNE', None))

        self.emitir(('FIM',))

    def visitar_bloco(self, no):
        # Cada bloco possui seu próprio escopo.
        self.emitir(('ABRE_ESCOPO',))

        for comando in no.comandos:
            self.visitar_comando(comando)

        self.emitir(('FECHA_ESCOPO',))

    def visitar_comando(self, no):
        linha = getattr(no, 'linha', 1)
        self.emitir(('LINHA', linha))

        if isinstance(no, Declaracao):
            self.emitir(('DECLARA', no.nome, no.tipo))

            if no.expr is not None:
                val = self.visitar_expressao(no.expr)
                self.emitir(('COPIA', no.nome, val))

        elif isinstance(no, Atribuicao):
            val = self.visitar_expressao(no.expr)
            self.emitir(('COPIA', no.nome, val))

        elif isinstance(no, Escreva):
            val = self.visitar_expressao(no.expressao)
            self.emitir(('ESCREVA', val))

        elif isinstance(no, Retorne):
            if no.expr is not None:
                val = self.visitar_expressao(no.expr)
                self.emitir(('RETORNE', val))
            else:
                self.emitir(('RETORNE', None))

        elif isinstance(no, Se):
            t_cond = self.visitar_expressao(no.cond)

            l_falso = self.novo_label()
            l_fim = self.novo_label()

            self.emitir(('JUMP_FALSO', t_cond, l_falso))

            self.visitar_bloco(no.bloco_entao)

            if no.bloco_senao is not None:
                self.emitir(('JUMP', l_fim))

            self.emitir(('LABEL', l_falso))

            if no.bloco_senao is not None:
                self.visitar_bloco(no.bloco_senao)
                self.emitir(('LABEL', l_fim))

        elif isinstance(no, Enquanto):
            l_inicio = self.novo_label()
            l_fim = self.novo_label()

            self.emitir(('LABEL', l_inicio))
            self.emitir(('LINHA', linha))

            t_cond = self.visitar_expressao(no.cond)

            self.emitir(('JUMP_FALSO', t_cond, l_fim))

            self.visitar_bloco(no.bloco)

            self.emitir(('JUMP', l_inicio))
            self.emitir(('LABEL', l_fim))

        elif isinstance(no, Chamada):
            self.visitar_expressao(no)

        elif isinstance(no, Bloco):
            self.visitar_bloco(no)

    def visitar_expressao(self, no):
        if isinstance(no, Literal):
            return no.valor

        elif isinstance(no, Variavel):
            return no.nome

        elif isinstance(no, Unario):
            val = self.visitar_expressao(no.operando)
            t = self.novo_temp()

            self.emitir(('UNARIO', t, no.op, val))
            return t

        elif isinstance(no, Binario):
            esq = self.visitar_expressao(no.esquerda)
            dir_val = self.visitar_expressao(no.direita)

            t = self.novo_temp()

            self.emitir((
                'BINARIO',
                t,
                esq,
                no.op,
                dir_val
            ))

            return t

        elif isinstance(no, Chamada):
            args_vals = [
                self.visitar_expressao(arg)
                for arg in no.args
            ]

            for arg_val in args_vals:
                self.emitir(('PARAM', arg_val))

            t = self.novo_temp()

            self.emitir((
                'CHAMA',
                t,
                no.nome,
                len(args_vals)
            ))

            return t


def gerar(arvore, tabela):
    return GeradorIR().gerar(arvore)


def despejar(codigo):
    linhas = []

    for inst in codigo:
        tipo = inst[0]

        # Instruções internas da VM não aparecem no --ir.
        if tipo in ('LINHA', 'ABRE_ESCOPO', 'FECHA_ESCOPO'):
            continue

        elif tipo == 'FUNCAO':
            nome, ret, params = inst[1], inst[2], inst[3]
            p_str = ", ".join(
                f"{p[0]} {p[1]}" for p in params
            )
            linhas.append(f"funcao {nome} {ret} ({p_str})")

        elif tipo == 'FIM':
            linhas.append("fim")

        elif tipo == 'LABEL':
            linhas.append(f"{inst[1]}:")

        elif tipo == 'DECLARA':
            linhas.append(f"  declara {inst[1]} {inst[2]}")

        elif tipo == 'BINARIO':
            linhas.append(
                f"  {inst[1]} = {inst[2]} {inst[3]} {inst[4]}"
            )

        elif tipo == 'UNARIO':
            linhas.append(
                f"  {inst[1]} = {inst[2]} {inst[3]}"
            )

        elif tipo == 'COPIA':
            linhas.append(f"  {inst[1]} = {inst[2]}")

        elif tipo == 'JUMP_FALSO':
            linhas.append(
                f"  seFalso {inst[1]} desvie {inst[2]}"
            )

        elif tipo == 'JUMP':
            linhas.append(f"  desvie {inst[1]}")

        elif tipo == 'PARAM':
            linhas.append(f"  param {inst[1]}")

        elif tipo == 'CHAMA':
            linhas.append(
                f"  {inst[1]} = chama {inst[2]} {inst[3]}"
            )

        elif tipo == 'RETORNE':
            if inst[1] is not None:
                linhas.append(f"  retorne {inst[1]}")
            else:
                linhas.append("  retorne")

        elif tipo == 'ESCREVA':
            linhas.append(f"  escreva {inst[1]}")

    return "\n".join(linhas)
