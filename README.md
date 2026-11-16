## Entrega 1 — Analisador Léxico

O analisador léxico transforma o código-fonte da MPL em uma sequência de
tokens. Cada token possui tipo, lexema, linha e coluna.

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

## Entrega 2 — Analisador Sintático e Árvore

O analisador sintático transforma a sequência de tokens em uma árvore sintática
abstrata (AST), seguindo a especificação da linguagem e os rótulos definidos em
CONTRATOS.md.

### Gramática implementada (EBNF)

```
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

## Entrega 3 — Análise Semântica

O analisador semântico percorre a Árvore Sintática Abstrata (AST) validando as regras de tipo, declaração e escopo da MPL. Ele garante que os operadores lidem com os tipos corretos e que as funções cumpram seus contratos.

### 1. Pilha de Escopos e Sombreamento
A Tabela de Símbolos é gerenciada como uma **árvore (ou pilha) de escopos**. 
- O escopo `0` (global) guarda apenas as declarações de funções.
- Cada função abre **dois** novos escopos aninhados: um para os seus parâmetros e, logo abaixo, outro para o seu bloco principal. 
- Comandos de controle (como `se` e `enquanto`) e blocos soltos (`{ ... }`) abrem novos escopos filhos.
- **Sombreamento:** Ao buscar uma variável, o compilador procura do escopo atual em direção ao escopo global (de dentro para fora). Variáveis internas podem ter o mesmo nome de variáveis externas, "escondendo-as" enquanto o bloco interno durar.
- A declaração duplicada do mesmo nome, **dentro do mesmo escopo**, aciona um erro semântico.

### 2. Duas Passadas (Two-Pass)
O analisador percorre a árvore sintática duas vezes para suportar chamadas de função independentes da ordem de declaração (incluindo recursão mútua):
1. **Primeira Passada (Coleta):** Percorre a raiz da AST recolhendo apenas as assinaturas (nome, tipo de retorno e lista de parâmetros) de todas as funções e registrando-as no escopo global. Também verifica se a função obrigatória `principal` (sem parâmetros e com retorno `vazio`) existe.
2. **Segunda Passada (Validação):** Entra de fato nas funções, empilha os escopos dos parâmetros e dos blocos internos, e valida todos os comandos, atribuições, expressões e retornos.

### 3. Sistema de Tipos e Conversão
A linguagem possui apenas quatro tipos de dados (`inteiro`, `real`, `logico`, `texto`), além do tipo de retorno `vazio`.
- **A única conversão implícita permitida:** `inteiro` pode ser convertido para `real`. Nenhuma outra conversão é tolerada (ex: `real` não vira `inteiro`, e `texto` e número não se misturam em concatenações literais).
- Operadores relacionais exigem compatibilidade estrita. Operadores lógicos exigem operandos `logico`.
- Operadores matemáticos (`+`, `-`, `*`, `/`) aceitam tipos numéricos. O operador resto (`%`) exige exclusivamente inteiros.

### 4. Garantia de Retorno (A armadilha do `se`)
Para qualquer função com tipo de retorno diferente de `vazio`, o analisador checa obrigatoriamente se ela **garante o retorno** em todos os caminhos possíveis de execução.
- O compilador faz uma verificação estrutural (não executa as condições lógicas).
- Um `retorne` direto no bloco garante o fluxo.
- Um condicional `se` com `senao` onde **ambos** os blocos internos possuem garantia de retorno também valida o fluxo.
- Um `se` **sem** `senao` nunca garante o retorno, pois a condição lógica pode não ser satisfeita, não importando a obviedade da expressão.
