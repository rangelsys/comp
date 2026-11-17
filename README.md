# Compilador MPL

Projeto de desenvolvimento de um compilador para a linguagem de programação **MPL**, dividido em quatro etapas. O projeto implementa desde a identificação dos tokens até a execução dos programas por meio de uma máquina virtual.

## Entrega 1 — Analisador Léxico

O analisador léxico transforma o código-fonte da MPL em uma sequência de tokens. Cada token possui tipo, lexema, linha e coluna.

### Tabela de Tokens

| Token | Expressão regular / reconhecimento |
|---|---|
| `ID` | `[a-zA-Z_][a-zA-Z0-9_]*` |
| `INTEIRO` | `[0-9]+` |
| `REAL` | `[0-9]+\.[0-9]+` |
| `LOGICO` | `verdadeiro` \| `falso` |
| `TEXTO` | `"(...)"`, permitindo os escapes `\n`, `\t`, `\"` e `\\` |
| `FUNCAO` | `funcao` |
| `RETORNE` | `retorne` |
| `SE` | `se` |
| `SENAO` | `senao` |
| `ENQUANTO` | `enquanto` |
| `ESCREVA` | `escreva` |
| `TIPO_INTEIRO` | `inteiro` |
| `TIPO_REAL` | `real` |
| `TIPO_LOGICO` | `logico` |
| `TIPO_TEXTO` | `texto` |
| `TIPO_VAZIO` | `vazio` |
| `E` | `e` |
| `OU` | `ou` |
| `NAO` | `nao` |
| `MAIS` | `+` |
| `MENOS` | `-` |
| `VEZES` | `*` |
| `DIVIDE` | `/` |
| `RESTO` | `%` |
| `IGUAL` | `==` |
| `DIFERENTE` | `!=` |
| `MENOR` | `<` |
| `MENOR_IGUAL` | `<=` |
| `MAIOR` | `>` |
| `MAIOR_IGUAL` | `>=` |
| `ATRIBUI` | `=` |
| `ABRE_PAR` | `(` |
| `FECHA_PAR` | `)` |
| `ABRE_CHAVE` | `{` |
| `FECHA_CHAVE` | `}` |
| `VIRGULA` | `,` |
| `PONTO_VIRGULA` | `;` |
| `FIM_ARQUIVO` | fim da entrada |

### Comentários

| Tipo | Forma reconhecida |
|---|---|
| Comentário de linha | `//` até o fim da linha |
| Comentário de bloco | `/*` até o primeiro `*/` |

### Observações

- Identificadores são sensíveis a maiúsculas e minúsculas.
- Palavras reservadas são reconhecidas antes de `ID`.
- `<=`, `>=`, `==` e `!=` são reconhecidos antes dos operadores de um caractere.
- Números reais exigem dígitos antes e depois do ponto.
- Textos aceitam apenas os escapes `\n`, `\t`, `\"` e `\\`.
- Espaços, tabulações, quebras de linha e `\r` são ignorados.

---

## Entrega 2 — Analisador Sintático e Árvore

O analisador sintático transforma a sequência de tokens em uma Árvore Sintática Abstrata (AST), seguindo a especificação da linguagem e os rótulos definidos em `CONTRATOS.md`.

### Gramática implementada (EBNF)

```ebnf
<programa> ::= { <funcao> } EOF

<funcao> ::= FUNCAO <tipo_retorno> ID ABRE_PAR [ <parametros> ] FECHA_PAR <bloco>

<parametros> ::= <parametro> { VIRGULA <parametro> }
<parametro> ::= <tipo> ID

<tipo_retorno> ::= TIPO_INTEIRO
                 | TIPO_REAL
                 | TIPO_LOGICO
                 | TIPO_TEXTO
                 | TIPO_VAZIO

<tipo> ::= TIPO_INTEIRO
         | TIPO_REAL
         | TIPO_LOGICO
         | TIPO_TEXTO

<bloco> ::= ABRE_CHAVE { <comando> } FECHA_CHAVE

<comando> ::= <declaracao>
            | <comando_id>
            | <condicional>
            | <repeticao>
            | <escrita>
            | <retorno>
            | <bloco>

<declaracao> ::= <tipo> ID [ ATRIBUI <expressao> ] PONTO_VIRGULA

<comando_id> ::= ID ATRIBUI <expressao> PONTO_VIRGULA
               | <chamada> PONTO_VIRGULA

<condicional> ::= SE ABRE_PAR <expressao> FECHA_PAR <bloco>
                  [ SENAO <bloco> ]

<repeticao> ::= ENQUANTO ABRE_PAR <expressao> FECHA_PAR <bloco>

<escrita> ::= ESCREVA ABRE_PAR <expressao> FECHA_PAR PONTO_VIRGULA

<retorno> ::= RETORNE [ <expressao> ] PONTO_VIRGULA

<chamada> ::= ID ABRE_PAR [ <argumentos> ] FECHA_PAR
<argumentos> ::= <expressao> { VIRGULA <expressao> }

<expressao> ::= <ou>

<ou> ::= <e> { OU <e> }

<e> ::= <igualdade> { E <igualdade> }

<igualdade> ::= <relacional> { (IGUAL | DIFERENTE) <relacional> }

<relacional> ::= <aditiva> { (MENOR | MENOR_IGUAL | MAIOR | MAIOR_IGUAL) <aditiva> }

<aditiva> ::= <multiplicativa> { (MAIS | MENOS) <multiplicativa> }

<multiplicativa> ::= <unario> { (VEZES | DIVIDE | RESTO) <unario> }

<unario> ::= (NAO | MENOS) <unario> | <primario>

<primario> ::= INTEIRO
             | REAL
             | LOGICO
             | TEXTO
             | ID
             | <chamada>
             | ABRE_PAR <expressao> FECHA_PAR
```

---

## Entrega 3 — Análise Semântica

O analisador semântico percorre a Árvore Sintática Abstrata (AST), validando as regras de tipo, declaração e escopo da MPL. Ele garante que os operadores trabalhem com os tipos corretos e que as funções cumpram seus contratos.

### 1. Pilha de Escopos e Sombreamento

A Tabela de Símbolos é gerenciada como uma árvore (ou pilha) de escopos.

- O escopo `0` (global) guarda apenas as declarações de funções.
- Cada função abre dois novos escopos aninhados: um para os seus parâmetros e, logo abaixo, outro para o seu bloco principal.
- Comandos de controle, como `se` e `enquanto`, e blocos soltos (`{ ... }`) abrem novos escopos filhos.
- **Sombreamento:** ao buscar uma variável, o compilador procura do escopo atual em direção ao escopo global. Variáveis internas podem ter o mesmo nome de variáveis externas, escondendo-as enquanto o bloco interno durar.
- A declaração duplicada do mesmo nome dentro do mesmo escopo gera um erro semântico.

### 2. Duas Passadas (Two-Pass)

O analisador percorre a árvore sintática duas vezes para permitir chamadas de função independentemente da ordem de declaração, incluindo recursão mútua.

1. **Primeira Passada (Coleta):** percorre a raiz da AST, recolhendo as assinaturas (nome, tipo de retorno e lista de parâmetros) de todas as funções e registrando-as no escopo global. Também verifica se a função obrigatória `principal` existe, sem parâmetros e com retorno `vazio`.
2. **Segunda Passada (Validação):** entra nas funções, empilha os escopos dos parâmetros e dos blocos internos, e valida todos os comandos, atribuições, expressões e retornos.

### 3. Sistema de Tipos e Conversão

A linguagem possui quatro tipos de dados (`inteiro`, `real`, `logico`, `texto`), além do tipo de retorno `vazio`.

- **A única conversão implícita permitida:** `inteiro` pode ser convertido para `real`. Nenhuma outra conversão é tolerada.
- Operadores relacionais exigem compatibilidade estrita.
- Operadores lógicos exigem operandos do tipo `logico`.
- Operadores matemáticos (`+`, `-`, `*`, `/`) aceitam tipos numéricos.
- O operador resto (`%`) exige exclusivamente inteiros.

### 4. Garantia de Retorno

Para qualquer função com tipo de retorno diferente de `vazio`, o analisador verifica se ela garante o retorno em todos os caminhos possíveis de execução.

- A verificação é estrutural, sem executar as condições lógicas.
- Um `retorne` direto no bloco garante o fluxo.
- Um condicional `se` com `senao`, no qual ambos os blocos possuem garantia de retorno, também valida o fluxo.
- Um `se` sem `senao` nunca garante o retorno, pois a condição pode não ser satisfeita.

---

## Entrega 4 — Geração de Código Intermediário e Máquina Virtual

Nesta etapa, o compilador passa a transformar a AST em instruções de código intermediário e executar essas instruções por meio de uma máquina virtual.

### 1. Geração de Código Intermediário

O Gerador de IR percorre a AST e produz uma sequência de instruções que representa as operações do programa.

São geradas instruções para:

- Operações aritméticas e lógicas.
- Comparações e expressões.
- Declaração e atribuição de variáveis.
- Comandos condicionais (`se` e `senao`).
- Estruturas de repetição (`enquanto`).
- Chamadas de funções e retornos.
- Entrada e saída de valores por meio de `escreva`.
- Abertura e fechamento de escopos.

### 2. Serialização do Código Intermediário

As instruções geradas são serializadas em um arquivo com extensão `.mplb`.

O arquivo armazena a representação textual das instruções, permitindo que a máquina virtual carregue e execute o programa posteriormente.

### 3. Máquina Virtual

A Máquina Virtual (VM) interpreta e executa as instruções presentes no arquivo `.mplb`.

Entre suas responsabilidades estão:

- Executar operações aritméticas, relacionais e lógicas.
- Controlar desvios e repetições.
- Gerenciar chamadas de funções e recursão.
- Armazenar e recuperar valores de variáveis.
- Gerenciar escopos aninhados e sombreamento.
- Inicializar variáveis de acordo com seus tipos.
- Executar as instruções de saída.

### 4. Tratamento de Erros em Tempo de Execução

A máquina virtual também identifica erros que acontecem durante a execução do programa.

São tratados, por exemplo:

- Divisão por zero.
- Resto de divisão por zero.
- Recursão infinita, identificada por um limite de profundidade de chamadas.

Os erros de execução são associados à linha correspondente do código-fonte, facilitando a identificação do problema.

---

## Verificação

O projeto possui testes automatizados para verificar as etapas de desenvolvimento do compilador.

Para executar a suíte de testes, utilize:

```bash
make verificar
```

**Resultado da Entrega 4:** 93 de 93 testes passaram.

---

## Tecnologias e Recursos

- Python
- Análise léxica
- Análise sintática
- Árvore Sintática Abstrata (AST)
- Análise semântica
- Tabela de símbolos e gerenciamento de escopos
- Geração de código intermediário (IR)
- Serialização de instruções
- Máquina Virtual (VM)
- Testes automatizados
