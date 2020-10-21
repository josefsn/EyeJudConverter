# EyeJud Converter
## Script desenvolvido em Python para a conversão de arquivos json da base do DataJud em arquivos CSV  especialmente formatados para a mineração de processos.


### Funcionalidades do script

- [x] Leitura de arquivos json do DataJud nos padrões fornecidos pelo CNJ Inova
- [x] Hierarquização de tabelas processuais unificadas: assuntos, classes e movimentoss (nacionais e locais)
- [x] Construção dos arquivos CSV com os atributos mandatórios para mineração de processos e os atributos acessórios úteis para as análises durante a mineração de processos, eliminando processos que contenham datas de movimentação inconsistentes.

### Pré-requisitos para utilizar o script
É necessário ter um ambiente de execução de scripts em Python.

### Parâmetros de utilização do script
O script espera alguns parâmetros que devem ser fonecidos via linha de comando:

<table>
<tr><td><strong>Uso:</strong></td><td>eye_jud_converter.py [-h] [--assuntos [ASSUNTOS [ASSUNTOS ...]]]</td></tr>
<tr><td></td><td>pastaRaiz</td></tr>
<tr><td></td><td>{justica_eleitoral,justica_estadual,justica_federal,justica_militar,justica_trabalho,tribunais_superiores}</td></tr>
</table>
<br />
<br />
<table>
<tr><td colspan="3"><strong>Argumentos posicionais:</strong></td></tr>
<tr><td></td><td width="45%">pastaRaiz</td><td width="45%">Caminho para a pasta raiz contendo a respectiva pasta do tipo de justiça e os arquivos auxiliares (sgt_assuntos.csv, sgt_classes.csv).</td></tr>
<tr><td></td><td>{justica_eleitoral,justica_estadual,justica_federal,justica_militar,justica_trabalho,tribunais_superiores}</td><td>Tipo de Justiça cujos CSVs serão gerados.</td></tr>
</table>
<br />
<br />
<table>
<tr><td colspan="3"><strong>Argumentos opcionais:</strong></td></tr>
<tr><td></td><td>-h, --help</td><td>Exibe uma mensagem de help de utilização e sai do script.</td></tr>
<tr><td></td><td>--assuntos [ASSUNTOS [ASSUNTOS ...]]</td><td>Lista de assuntos (números inteiros) para separar os arquivos CSVs (argumento opcional).</td></tr>
</table>
<br />
Caso seja fornecida uma lista de assuntos, serão gerados arquivos CSV para cada assunto, caso contrário, será gerado um único arquivo CSV com todos os assuntos.<br />
<br />

<strong>Exemplos de uso:</strong>
> eye_jud_converter.py -h<br />
> eye_jud_converter.py . justica_militar<br />
> eye_jud_converter.py . justica_trabalho 9985 12734 1156 864<br />
<br />
<br />
Os arquivos serão gerados na em uma pasta 'tmp' dentro da pasta raiz.

É importante que a estrutura de pastas contendo os JSONs a partir da pasta raiz respeitem o formato: <br />
{pastaRaiz}/{tipoJustica}/**/*.json<br />
Exemplo:<br />
./justica_trabalho/processos-trt23/processos-tre-ac_1.json<br />