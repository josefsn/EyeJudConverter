import argparse
import textwrap
import os
import csv
import pandas
import numpy
import glob
import json
import time

# *******************************************************************
# *** Configura argumentos externos do script (command line args) ***
# *******************************************************************

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description='Gera arquivos CSV a partir dos arquivos JSON do Tipo de Justiça informado. Gera também as tabelas processuais unificadas de forma hierarquizada.',
                                 epilog=textwrap.dedent('''\
                                    Caso seja fornecida uma lista de assuntos, serão gerados arquivos CSV para cada assunto,
                                    caso contrário, será gerado um único arquivo CSV com todos os assuntos.
                                    É importante que a estrutura de pastas contendo os JSONs a partir da pasta raiz respeitem o formato:
                                        {pastaRaiz}/{tipoJustica}/**/*.json
                                        Exemplo:
                                        ./justica_trabalho/processos-trt23/processos-tre-ac_1.json
                                    '''))
parser.add_argument('pastaRaiz', help='Caminho para a pasta raiz contendo a respectiva pasta do tipo de justiça e os arquivos auxiliares (sgt_assuntos.csv, sgt_classes.csv.')
parser.add_argument('tipoJustica', choices=['justica_eleitoral', 'justica_estadual', 'justica_federal', 'justica_militar', 'justica_trabalho', 'tribunais_superiores'],
                    help='Tipo de Justiça cujos CSVs serão gerados.')
parser.add_argument('--assuntos', nargs='*', type=int, help='Lista de assuntos (números inteiros) para separar os CSVs (argumento opcional)')

# Cria objeto args contendo os argumentos do script
# args.pastaRaiz conterá a pasta raiz
# args.tipoJustica conterá o tipo de justiça
# args.assuntos conterá a lista de assuntos ou None
args = parser.parse_args()


# **********************************************************************************
# *** Funções que hierarquizam as tabelas processuais unificadas oriundas do SGT ***
# **********************************************************************************

def hierarquiza_assuntos():
    # O requisito para que essa função funcione é a existência do arquivo sgt_assuntos.csv dentro da pasta raiz.
    sgt_assuntos = pandas.read_csv('{}/sgt_assuntos.csv'.format(args.pastaRaiz), sep=';', index_col=0)
    with open('{}/assuntos.csv'.format(args.pastaRaiz), 'w', newline='', encoding='utf8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['codigo','cod_pri','primario','secundario','descricao'], delimiter=';',quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for codigo in list(sgt_assuntos.index.values):
            descricao = sgt_assuntos.loc[int(codigo),'descricao']
            cod_pai = sgt_assuntos.loc[int(codigo),'cod_pai']
            cod_avo = None
            cod_bisavo = None
            if cod_pai and not numpy.isnan(cod_pai):
                cod_avo = sgt_assuntos.loc[int(cod_pai),'cod_pai']
            if cod_avo and not numpy.isnan(cod_avo):
                cod_bisavo = sgt_assuntos.loc[int(cod_avo),'cod_pai']
            while cod_bisavo and not numpy.isnan(cod_bisavo):
                descricao = sgt_assuntos.loc[int(cod_pai),'descricao']+' | '+descricao
                cod_pai = cod_avo
                cod_avo = cod_bisavo
                if cod_avo and not numpy.isnan(cod_avo):
                    cod_bisavo = sgt_assuntos.loc[int(cod_avo), 'cod_pai']
            if cod_avo and not numpy.isnan(cod_avo):
                cod_pri = int(cod_avo)
                primario = sgt_assuntos.loc[cod_pri, 'descricao']
                secundario = sgt_assuntos.loc[int(cod_pai), 'descricao']
            else:
                secundario = descricao
                if cod_pai and not numpy.isnan(cod_pai):
                    cod_pri = int(cod_pai)
                    primario = sgt_assuntos.loc[cod_pri, 'descricao']
                else:
                    cod_pri = int(codigo)
                    primario = descricao
            writer.writerows([{'codigo':codigo,'cod_pri':cod_pri,'primario':primario,'secundario':secundario,'descricao':descricao}])

def hierarquiza_classes():
    # O requisito para que essa função funcione é a existência do arquivo sgt_classes.csv dentro da pasta raiz.

    sgt_classes = pandas.read_csv('{}/sgt_classes.csv'.format(args.pastaRaiz), sep=';', index_col=0)
    with open('{}/classes.csv'.format(args.pastaRaiz), 'w', newline='', encoding='utf8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['codigo','primario','descricao'], delimiter=';',quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for codigo in list(sgt_classes.index.values):
            descricao = sgt_classes.loc[int(codigo),'descricao']
            primario = descricao
            cod_pai = sgt_classes.loc[int(codigo),'cod_pai']
            while not numpy.isnan(cod_pai):
                descricao_pai = sgt_classes.loc[int(cod_pai), 'descricao']
                cod_pai = sgt_classes.loc[int(cod_pai),'cod_pai']
                if not numpy.isnan(cod_pai):
                    descricao = descricao_pai+' | '+descricao
                else: primario = descricao_pai
            writer.writerows([{'codigo':codigo,'primario':primario,'descricao':descricao}])

def hierarquiza_movimentos(local_ou_nacional):
    # O requisito para que essa função funcione é a existência do arquivo sgt_movimentos.csv e/ou sgt_movimentos_{tipoJustica}.csv dentro da pasta raiz.
    # Isso se justifica pelo fato de que em várias modalidades de justiça os códigos de andamento que estão nos arquivos JSON são códigos locais
    # e, portanto, não estão na tabela processual unificada nacional (sgt_movimentos.csv).
    # Nesse caso, pode optar-se por obter a respectiva tabela local de uma determinada justiça (sgt_movimentos_{tipoJustica}.csv).
    # A função deverá ser chamada uma vez para cada opção 'local' ou 'nacional'

    if local_ou_nacional == 'local':
        ifile = '{}/sgt_movimentos_{}.csv'.format(args.pastaRaiz, args.tipoJustica)
        ofile = '{}/movimentos_{}.csv'.format(args.pastaRaiz, args.tipoJustica)
    else:
        ifile = '{}/sgt_movimentos.csv'.format(args.pastaRaiz)
        ofile = '{}/movimentos.csv'.format(args.pastaRaiz)
    try:
        sgt_movimentos = pandas.read_csv(ifile, sep=';', index_col=0)
        with open(ofile, 'w', newline='', encoding='utf8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['codigo','primario','descricao'], delimiter=';',quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for codigo in list(sgt_movimentos.index.values):
                descricao = sgt_movimentos.loc[int(codigo),'descricao']
                cod_pai = sgt_movimentos.loc[int(codigo),'cod_pai']
                cod_avo = None
                cod_bisavo = None
                if cod_pai and not numpy.isnan(cod_pai):
                    cod_avo = sgt_movimentos.loc[int(cod_pai),'cod_pai']
                if cod_avo and not numpy.isnan(cod_avo):
                    cod_bisavo = sgt_movimentos.loc[int(cod_avo),'cod_pai']
                while cod_bisavo and not numpy.isnan(cod_bisavo):
                    descricao = sgt_movimentos.loc[int(cod_pai),'descricao']+' | '+descricao
                    cod_pai = cod_avo
                    cod_avo = cod_bisavo
                    if cod_avo and not numpy.isnan(cod_avo):
                        cod_bisavo = sgt_movimentos.loc[int(cod_avo),'cod_pai']
                if cod_avo and not numpy.isnan(cod_avo):
                    if cod_pai and not numpy.isnan(cod_pai):
                        primario = sgt_movimentos.loc[int(cod_pai), 'descricao']
                else:
                    primario = descricao
                writer.writerows([{'codigo':codigo,'primario':primario,'descricao':descricao}])
    except FileNotFoundError:
        print('Arquivo de movimentos local não encontrado!')

def gera_csv(assunto):
    # O requisito para que essa função funcione é a existência dos arquivos:
    #  - assuntos hierarquizados: {pastaRaiz}/assuntos.csv
    #  - classes hierarquizadas: {pastaRaiz}/classes.csv
    #  - assuntos hierarquizados: {pastaRaiz}/assuntos.csv
    #  - movimentos hierarquizados: {pastaRaiz}/movimentos.csv e/ou {pastaRaiz}/movimentos_{tipoJustica}.csv
    #  - serventias: {pastaRaiz}/serventias.csv
    #  - tabela de municípios do IBGE: {pastaRaiz}/ibge.csv

    sgt_assuntos = pandas.read_csv('{}/assuntos.csv'.format(args.pastaRaiz), sep=';', index_col=0)
    sgt_classes = pandas.read_csv('{}/classes.csv'.format(args.pastaRaiz), sep=';', index_col=0)
    sgt_movimentos = pandas.read_csv('{}/movimentos.csv'.format(args.pastaRaiz), sep=';', index_col=0)
    try:
        sgt_movimentos_local = pandas.read_csv('{}/movimentos_{}.csv'.format(args.pastaRaiz, args.tipoJustica), sep=';', index_col=0)
    except FileNotFoundError:
        sgt_movimentos_local = None
    mpm_serventias = pandas.read_csv('{}/mpm_serventias.csv'.format(args.pastaRaiz), sep=';', usecols=["SEQ_ORGAO", "DSC_TIP_ORGAO"],index_col=0)
    ibge = pandas.read_csv('{}/ibge.csv'.format(args.pastaRaiz), sep=';', index_col=0)
    ifile = '{}/{}/**/*.json'.format(args.pastaRaiz, args.tipoJustica)
    if assunto is None:
        ofile = '{}/tmp/{}.csv'.format(args.pastaRaiz, args.tipoJustica)
    else:
        ofile = '{}/tmp/{}.csv'.format(args.pastaRaiz, args.tipoJustica+'_'+str(assunto))
    file = glob.glob(ifile, recursive=True)
    with open(ofile, 'w', newline='', encoding='utf8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['ProcessoNumero',
                                                     'MovimentoSecundario',
                                                     'MovimentoDataHora',
                                                     '5-Movi ID',
                                                     '1-Grau',
                                                     '4-Sigla Tribunal',
                                                     '2-Assunto Primário',
                                                     '2-Assunto Secundário',
                                                     '2-Assunto Terciário',
                                                     '4-Assunto Local',
                                                     '2-Assunto Descrição',
                                                     '4-Vinculado',
                                                     '4-Relação Incidental',
                                                     '4-Prioridade',
                                                     '4-Valor Causa',
                                                     'ProcessoOrgaoJulgador',
                                                     'ProcessoOrgaoJulgadorTipo',
                                                     '4-Instância',
                                                     '3-Orgão Julgador Município',
                                                     '3-Orgão Julgador UF',
                                                     '4-Competência',
                                                     '4-Outros Números',
                                                     '1-Classe Primária',
                                                     '1-Classe Secundária',
                                                     '3-Processo Município',
                                                     '3-Processo UF',
                                                     '4-Nível Sigilo',
                                                     '4-Intervenção MP',
                                                     '4-Tamanho',
                                                     '4-Data Ajuizamento',
                                                     '4-Processo EL',
                                                     '4-Sistema',
                                                     '4-Movi Primário',
                                                     '5-Movi Nível Sigilo',
                                                     '4-Movi Tipo Respo',
                                                     '5-Movi Local',
                                                     '5-Movi Complemento',
                                                     '5-Movi Cód Comple',
                                                     '5-Movi Doc Vinculado',
                                                     '5-Movi Órgão Julgador',
                                                     '5-Movi Órgão Julg Tipo',
                                                     '5-Movi Órgão Julg Inst',
                                                     '5-Movi Órgão Julg Município',
                                                     '5-Movi Órgão Julg UF',
                                                     '5-Movi Tipo Decisão'])
        writer.writeheader()
        for i in file:
            print('Processando arquivo {}'.format(i))
            data = json.loads(open(i, 'r').read())
            for j in data:
                ProcessoNumero = None
                ProcessoGrau = None
                ProcessoSiglaTribunal = None
                ProcessoAssuntoPrimario = None
                ProcessoAssuntoSecundario = None
                ProcessoAssuntoTerciario = None
                ProcessoAssuntoLocal = None
                ProcessoAssuntoDescricao = None
                ProcessoVinculado = None
                ProcessoRelacaoIncidental = None
                ProcessoPrioridade = None
                ProcessoValorCausa = None
                ProcessoOrgaoJulgador = None
                ProcessoOrgaoJulgadorTipo = None
                ProcessoOrgaoJulgadorInstancia = None
                ProcessoOrgaoJulgadorMunicipio = None
                ProcessoOrgaoJulgadorUF = None
                ProcessoCompetencia = None
                ProcessoOutrosNumeros = None
                ProcessoClassePrimaria = None
                ProcessoClasseSecundaria = None
                ProcessoMunicipio = None
                ProcessoUF = None
                ProcessoNivelSigilo = None
                ProcessoIntervencaoMP = None
                ProcessoTamanho = None
                ProcessoDataAjuizamento = None
                ProcessoEl = None
                ProcessoSistema = None
                ListaAssuntos = []
                ListaAssuntosPrimarios = []
                ListaAssuntosLocais = []
                ListaAssuntosDescricao = []
                datahoraok = True
                if 'dadosBasicos' in j and j['dadosBasicos'] is not None and 'numero' in j['dadosBasicos'] and j['dadosBasicos']['numero'] is not None and 'movimento' in j and j['movimento'] is not None:
                    for k in j['movimento']:
                        try:
                            datahora = time.strptime(str(k['dataHora'])[0:4]+'-'+str(k['dataHora'])[4:6]+'-'+str(k['dataHora'])[6:8]+'T'+str(k['dataHora'])[8:10]+':'+str(k['dataHora'])[10:12]+':'+str(k['dataHora'])[12:14],'%Y-%m-%dT%H:%M:%S')
                            segundo = int(str(k['dataHora'][12:14]))
                        except TypeError:
                            datahora = None
                            segundo = 0
                        except ValueError:
                            datahora = None
                            segundo = 0
                        if datahora is None or segundo>59:
                            datahoraok = False
                    if datahoraok:
                        if 'assunto' in j['dadosBasicos'] and j['dadosBasicos']['assunto'] is not None:
                            for l in j['dadosBasicos']['assunto']:
                                if 'codigoNacional' in l and l['codigoNacional'] is not None:
                                    ListaAssuntos.append(l['codigoNacional'])
                                elif 'codigoPaiNacional' in l and l['codigoPaiNacional'] is not None:
                                    ListaAssuntos.append(l['codigoPaiNacional'])
                                if 'descricao' in l and l['descricao'] is not None:
                                    ListaAssuntosDescricao.append(l['descricao'])
                                elif 'assuntoLocal' in l and l['assuntoLocal'] is not None:
                                    if 'codigoNacional' in l['assuntoLocal'] and l['assuntoLocal']['codigoNacional'] is not None:
                                        ListaAssuntos.append(l['assuntoLocal']['codigoNacional'])
                                    elif 'codigoPaiNacional' in l['assuntoLocal'] and l['assuntoLocal']['codigoPaiNacional'] is not None:
                                        ListaAssuntos.append(l['assuntoLocal']['codigoPaiNacional'])
                                    if 'descricao' in l['assuntoLocal'] and l['assuntoLocal']['descricao'] is not None:
                                        ListaAssuntosDescricao.append(l['assuntoLocal']['descricao'])
                                    if 'codigoAssunto' in l['assuntoLocal'] and l['assuntoLocal']['codigoAssunto'] is not None:
                                        ListaAssuntosLocais.append(l['assuntoLocal']['codigoAssunto'])
                        for a in ListaAssuntos:
                            try:
                                ListaAssuntosPrimarios.append(sgt_assuntos.loc[int(a)].cod_pri)
                            except KeyError:
                                ListaAssuntosPrimarios = ListaAssuntosPrimarios
                            except ValueError:
                                ListaAssuntosPrimarios = ListaAssuntosPrimarios
                        if assunto is None or assunto in ListaAssuntos or assunto in ListaAssuntosPrimarios:
                            ProcessoNumero = str(j['dadosBasicos']['numero'])[0:7]+'-'+str(j['dadosBasicos']['numero'])[7:9]+'.'+str(j['dadosBasicos']['numero'])[9:13]+'.'+str(j['dadosBasicos']['numero'])[13:16]+'.'+str(j['dadosBasicos']['numero'])[16:20]
                            if 'grau' in j and j['grau'] is not None:
                                ProcessoGrau = j['grau']
                            if 'siglaTribunal' in j and j['siglaTribunal'] is not None:
                                ProcessoSiglaTribunal = j['siglaTribunal']
                            if ListaAssuntos:
                                ProcessoAssuntoTerciario = ListaAssuntos[-1]
                            if ProcessoAssuntoTerciario:
                                try:
                                    ProcessoAssuntoPrimario = sgt_assuntos.loc[int(ProcessoAssuntoTerciario)].primario
                                    ProcessoAssuntoSecundario = sgt_assuntos.loc[int(ProcessoAssuntoTerciario)].secundario
                                    ProcessoAssuntoTerciario = sgt_assuntos.loc[int(ProcessoAssuntoTerciario)].descricao
                                except KeyError:
                                    ProcessoAssuntoPrimario = None
                                    ProcessoAssuntoSecundario = None
                                    ProcessoAssuntoTerciario = None
                                except ValueError:
                                    ProcessoAssuntoPrimario = None
                                    ProcessoAssuntoSecundario = None
                                    ProcessoAssuntoTerciario = None
                            if ListaAssuntosLocais:
                                ProcessoAssuntoLocal = ListaAssuntosLocais[-1]
                            if ListaAssuntosDescricao:
                                ProcessoAssuntoDescricao = ListaAssuntosDescricao[-1]
                            if 'processoVinculado' in j['dadosBasicos'] and j['dadosBasicos']['processoVinculado'] is not None:
                                ProcessoVinculado = j['dadosBasicos']['processoVinculado']
                            if 'relacaoIncidental' in j['dadosBasicos'] and j['dadosBasicos']['relacaoIncidental'] is not None:
                                ProcessoRelacaoIncidental = j['dadosBasicos']['relacaoIncidental']
                            if 'prioridade' in j['dadosBasicos'] and j['dadosBasicos']['prioridade'] is not None:
                                ProcessoPrioridade = j['dadosBasicos']['prioridade']
                            if 'valorCausa' in j['dadosBasicos'] and j['dadosBasicos']['valorCausa'] is not None:
                                ProcessoValorCausa = j['dadosBasicos']['valorCausa']
                            if 'orgaoJulgador' in j['dadosBasicos'] and j['dadosBasicos']['orgaoJulgador'] is not None:
                                if 'nomeOrgao' in j['dadosBasicos']['orgaoJulgador'] and j['dadosBasicos']['orgaoJulgador']['nomeOrgao'] is not None:
                                    ProcessoOrgaoJulgador = j['dadosBasicos']['orgaoJulgador']['nomeOrgao']
                                if 'codigoOrgao' in j['dadosBasicos']['orgaoJulgador'] and j['dadosBasicos']['orgaoJulgador']['codigoOrgao'] is not None:
                                    ProcessoOrgaoJulgadorTipo = j['dadosBasicos']['orgaoJulgador']['codigoOrgao']
                                    try:
                                        ProcessoOrgaoJulgadorTipo = mpm_serventias.loc[int(ProcessoOrgaoJulgadorTipo)].DSC_TIP_ORGAO
                                    except KeyError:
                                        ProcessoOrgaoJulgadorTipo = ProcessoOrgaoJulgadorTipo
                                    except ValueError:
                                        ProcessoOrgaoJulgadorTipo = ProcessoOrgaoJulgadorTipo
                                if 'instancia' in j['dadosBasicos']['orgaoJulgador'] and j['dadosBasicos']['orgaoJulgador']['instancia'] is not None:
                                    ProcessoOrgaoJulgadorInstancia = j['dadosBasicos']['orgaoJulgador']['instancia']
                                if 'codigoMunicipioIBGE' in j['dadosBasicos']['orgaoJulgador'] and j['dadosBasicos']['orgaoJulgador']['codigoMunicipioIBGE'] is not None:
                                    ProcessoOrgaoJulgadorMunicipio = j['dadosBasicos']['orgaoJulgador']['codigoMunicipioIBGE']
                                    try:
                                        ProcessoOrgaoJulgadorUF = ibge.loc[int(ProcessoOrgaoJulgadorMunicipio)].sig_uf
                                        ProcessoOrgaoJulgadorMunicipio = ibge.loc[int(ProcessoOrgaoJulgadorMunicipio)].municipio
                                    except KeyError:
                                        ProcessoOrgaoJulgadorMunicipio = ProcessoOrgaoJulgadorMunicipio
                                        ProcessoOrgaoJulgadorUF = ProcessoOrgaoJulgadorMunicipio
                                    except ValueError:
                                        ProcessoOrgaoJulgadorMunicipio = ProcessoOrgaoJulgadorMunicipio
                                        ProcessoOrgaoJulgadorUF = ProcessoOrgaoJulgadorMunicipio
                            if 'competencia' in j['dadosBasicos'] and j['dadosBasicos']['competencia'] is not None:
                                ProcessoCompetencia = j['dadosBasicos']['competencia']
                            if 'outrosnumeros' in j['dadosBasicos'] and j['dadosBasicos']['outrosnumeros'] is not None:
                                ProcessoOutrosNumeros = j['dadosBasicos']['outrosnumeros']
                            if 'classeProcessual' in j['dadosBasicos'] and j['dadosBasicos']['classeProcessual'] is not None:
                                ProcessoClasseSecundaria = j['dadosBasicos']['classeProcessual']
                                try:
                                    ProcessoClassePrimaria = sgt_classes.loc[int(ProcessoClasseSecundaria)].primario
                                    ProcessoClasseSecundaria = sgt_classes.loc[int(ProcessoClasseSecundaria)].descricao
                                except KeyError:
                                    ProcessoClassePrimaria = ProcessoClassePrimaria
                                    ProcessoClasseSecundaria = ProcessoClasseSecundaria
                                except ValueError:
                                    ProcessoClassePrimaria = ProcessoClassePrimaria
                                    ProcessoClasseSecundaria = ProcessoClasseSecundaria
                            if 'codigoLocalidade' in j['dadosBasicos'] and j['dadosBasicos']['codigoLocalidade'] is not None:
                                ProcessoMunicipio = j['dadosBasicos']['codigoLocalidade']
                            if ProcessoMunicipio:
                                try:
                                    ProcessoUF = ibge.loc[int(ProcessoMunicipio)].sig_uf
                                    ProcessoMunicipio = ibge.loc[int(ProcessoMunicipio)].municipio
                                except KeyError:
                                    ProcessoMunicipio = ProcessoMunicipio
                                    ProcessoUF = ProcessoMunicipio
                                except ValueError:
                                    ProcessoMunicipio = ProcessoMunicipio
                                    ProcessoUF = ProcessoMunicipio
                            if 'nivelSigilo' in j['dadosBasicos'] and j['dadosBasicos']['nivelSigilo'] is not None:
                                ProcessoNivelSigilo = j['dadosBasicos']['nivelSigilo']
                            if 'intervencaoMP' in j['dadosBasicos'] and j['dadosBasicos']['intervencaoMP'] is not None:
                                ProcessoIntervencaoMP = j['dadosBasicos']['intervencaoMP']
                            if 'tamanhoProcesso' in j['dadosBasicos'] and j['dadosBasicos']['tamanhoProcesso'] is not None:
                                ProcessoTamanho = j['dadosBasicos']['tamanhoProcesso']
                            if 'dataAjuizamento' in j['dadosBasicos'] and j['dadosBasicos']['dataAjuizamento'] is not None:
                                ProcessoDataAjuizamento = j['dadosBasicos']['dataAjuizamento']
                                ProcessoDataAjuizamento = str(ProcessoDataAjuizamento)[0:4] + '-' + str(ProcessoDataAjuizamento)[4:6] + \
                                                      '-' + str(ProcessoDataAjuizamento)[6:8] + 'T' + str(ProcessoDataAjuizamento)[8:10] \
                                                      + ':' + str(ProcessoDataAjuizamento)[10:12] + ':' + str(ProcessoDataAjuizamento)[12:14]
                            if 'procEl' in j['dadosBasicos'] and j['dadosBasicos']['procEl'] is not None:
                                ProcessoEl = j['dadosBasicos']['procEl']
                                try:
                                    ProcessoEl = int(ProcessoEl)
                                except TypeError:
                                    ProcessoEl = ProcessoEl
                                except ValueError:
                                    ProcessoEl = ProcessoEl
                                if ProcessoEl == 0:
                                    ProcessoEl = 'Eletronico'
                                elif ProcessoEl == 1:
                                    ProcessoEl = 'Fisico'
                            if 'dscSistema' in j['dadosBasicos'] and j['dadosBasicos']['dscSistema'] is not None:
                                ProcessoSistema = j['dadosBasicos']['dscSistema']
                                try:
                                    ProcessoSistema = int(ProcessoSistema)
                                except TypeError:
                                    ProcessoSistema = ProcessoSistema
                                except ValueError:
                                    ProcessoSistema = ProcessoSistema
                                if ProcessoSistema == 1:
                                    ProcessoSistema = 'PJE'
                                elif ProcessoSistema == 2:
                                    ProcessoSistema = 'PROJUDI'
                                elif ProcessoSistema == 3:
                                    ProcessoSistema = 'SAJ'
                                elif ProcessoSistema == 4:
                                    ProcessoSistema = 'EPROC'
                                elif ProcessoSistema == 5:
                                    ProcessoSistema = 'APOLO'
                                elif ProcessoSistema == 6:
                                    ProcessoSistema = 'THEMIS'
                                elif ProcessoSistema == 7:
                                    ProcessoSistema = 'LIBRA'
                                elif ProcessoSistema == 8:
                                    ProcessoSistema = 'Outros'
                            for k in j['movimento']:
                                MovimentoPrimario = None
                                MovimentoSecundario = None
                                MovimentoDataHora = None
                                MovimentoId = None
                                MovimentoNivelSigilo = None
                                MovimentoTipoResponsavel = None
                                MovimentoLocal = None
                                MovimentoComplemento = None
                                MovimentoCodComplemento = None
                                MovimentoIdDocumentoVinculado = None
                                MovimentoOrgaoJulgador = None
                                MovimentoOrgaoJulgadorTipo = None
                                MovimentoOrgaoJulgadorInstancia = None
                                MovimentoOrgaoJulgadorMunicipio = None
                                MovimentoOrgaoJulgadorUF = None
                                MovimentoTipoDecisao = None
                                if 'movimentoNacional' in k and k['movimentoNacional'] is not None and 'codigoNacional' in k['movimentoNacional'] and k['movimentoNacional']['codigoNacional'] is not None:
                                    MovimentoSecundario = k['movimentoNacional']['codigoNacional']
                                elif 'movimentoLocal' in k and k['movimentoLocal'] is not None:
                                    if 'codigoPaiNacional' in k['movimentoLocal'] and k['movimentoLocal']['codigoPaiNacional'] is not None:
                                        MovimentoSecundario = k['movimentoLocal']['codigoPaiNacional']
                                    elif 'codigoMovimento' in k['movimentoLocal'] and k['movimentoLocal']['codigoMovimento'] is not None:
                                        MovimentoSecundario = k['movimentoLocal']['codigoMovimento']
                                        MovimentoLocal = MovimentoSecundario
                                if 'dataHora' in k and k['dataHora'] is not None:
                                    MovimentoDataHora = str(k['dataHora'])[0:4]+'-'+str(k['dataHora'])[4:6]+'-'+str(k['dataHora'])[6:8]+'T'+str(k['dataHora'])[8:10]+':'+str(k['dataHora'])[10:12]+':'+str(k['dataHora'])[12:14]
                                if MovimentoSecundario is not None and MovimentoDataHora is not None:
                                    if MovimentoLocal:
                                        try:
                                            MovimentoPrimario = sgt_movimentos_local.loc[int(MovimentoSecundario)].descricao
                                            MovimentoSecundario = sgt_movimentos_local.loc[int(MovimentoSecundario)].descricao
                                        except KeyError:
                                            MovimentoPrimario = MovimentoPrimario
                                            MovimentoSecundario = MovimentoSecundario
                                        except ValueError:
                                            MovimentoPrimario = MovimentoPrimario
                                            MovimentoSecundario = MovimentoSecundario
                                    if not MovimentoPrimario:
                                        try:
                                            MovimentoPrimario = sgt_movimentos.loc[int(MovimentoSecundario)].primario
                                            MovimentoSecundario = sgt_movimentos.loc[int(MovimentoSecundario)].descricao
                                        except KeyError:
                                            MovimentoPrimario = MovimentoPrimario
                                            MovimentoSecundario=MovimentoSecundario
                                        except ValueError:
                                            MovimentoPrimario = MovimentoPrimario
                                            MovimentoSecundario = MovimentoSecundario
                                    if 'identificadorMovimento' in k and k['identificadorMovimento'] is not None:
                                        MovimentoId = k['identificadorMovimento']
                                    if 'nivelSigilo' in k and k['nivelSigilo'] is not None:
                                        MovimentoNivelSigilo = k['nivelSigilo']
                                    if 'tipoResponsavelMovimento' in k and k['tipoResponsavelMovimento'] is not None:
                                        MovimentoTipoResponsavel = k['tipoResponsavelMovimento']
                                        try:
                                            MovimentoTipoResponsavel = int(MovimentoTipoResponsavel)
                                        except TypeError:
                                            MovimentoTipoResponsavel = MovimentoTipoResponsavel
                                        except ValueError:
                                            MovimentoTipoResponsavel = MovimentoTipoResponsavel
                                        if MovimentoTipoResponsavel == 0:
                                            MovimentoTipoResponsavel = 'Servidor'
                                        elif MovimentoTipoResponsavel == 1:
                                            MovimentoTipoResponsavel = 'Magistrado'
                                    if 'complementoNacional' in k and k['complementoNacional'] is not None and 'descricaoComplemento' in k['complementoNacional'] and k['complementoNacional']['descricaoComplemento'] is not None:
                                        MovimentoComplemento = k['complementoNacional']['descricaoComplemento']
                                    if 'complementoNacional' in k and k['complementoNacional'] is not None and 'codComplementoTabelado' in k['complementoNacional'] and k['complementoNacional']['codComplementoTabelado'] is not None:
                                        MovimentoCodComplemento = k['complementoNacional']['codComplementoTabelado']
                                    if 'idDocumentoVinculado' in k and k['idDocumentoVinculado'] is not None:
                                        MovimentoIdDocumentoVinculado = k['idDocumentoVinculado']
                                    if 'orgaoJulgador' in k and k['orgaoJulgador'] is not None:
                                        if 'nomeOrgao' in k['orgaoJulgador'] and k['orgaoJulgador']['nomeOrgao'] is not None:
                                            MovimentoOrgaoJulgador = k['orgaoJulgador']['nomeOrgao']
                                        if 'codigoOrgao' in k['orgaoJulgador'] and k['orgaoJulgador']['codigoOrgao'] is not None:
                                            MovimentoOrgaoJulgadorTipo = k['orgaoJulgador']['codigoOrgao']
                                            try:
                                                MovimentoOrgaoJulgadorTipo = mpm_serventias.loc[int(MovimentoOrgaoJulgadorTipo)].DSC_TIP_ORGAO
                                            except KeyError:
                                                MovimentoOrgaoJulgadorTipo = MovimentoOrgaoJulgadorTipo
                                            except ValueError:
                                                MovimentoOrgaoJulgadorTipo = MovimentoOrgaoJulgadorTipo
                                        if 'instancia' in k['orgaoJulgador'] and k['orgaoJulgador']['instancia'] is not None:
                                            MovimentoOrgaoJulgadorInstancia = k['orgaoJulgador']['instancia']
                                        if 'codigoMunicipioIBGE' in k['orgaoJulgador'] and k['orgaoJulgador']['codigoMunicipioIBGE'] is not None:
                                            MovimentoOrgaoJulgadorMunicipio = k['orgaoJulgador']['codigoMunicipioIBGE']
                                            try:
                                                MovimentoOrgaoJulgadorUF = ibge.loc[int(MovimentoOrgaoJulgadorMunicipio)].sig_uf
                                                MovimentoOrgaoJulgadorMunicipio = ibge.loc[int(MovimentoOrgaoJulgadorMunicipio)].municipio
                                            except KeyError:
                                                MovimentoOrgaoJulgadorMunicipio = MovimentoOrgaoJulgadorMunicipio
                                                MovimentoOrgaoJulgadorUF = MovimentoOrgaoJulgadorMunicipio
                                            except ValueError:
                                                MovimentoOrgaoJulgadorMunicipio = MovimentoOrgaoJulgadorMunicipio
                                                MovimentoOrgaoJulgadorUF = MovimentoOrgaoJulgadorMunicipio
                                    if 'tipoDecisao' in k and k['tipoDecisao'] is not None:
                                        MovimentoTipoDecisao = k['tipoDecisao']
                                        try:
                                            MovimentoTipoDecisao = int(MovimentoTipoDecisao)
                                        except TypeError:
                                            MovimentoTipoDecisao = MovimentoTipoDecisao
                                        except ValueError:
                                            MovimentoTipoDecisao = MovimentoTipoDecisao
                                        if MovimentoTipoDecisao == 0:
                                            MovimentoTipoDecisao = 'Monocratica'
                                        elif MovimentoTipoDecisao == 1:
                                            MovimentoTipoDecisao = 'Colegiada'
                                    writer.writerows([
                                {
                                 'ProcessoNumero': ProcessoNumero,
                                 'MovimentoSecundario': MovimentoSecundario,
                                 'MovimentoDataHora': MovimentoDataHora,
                                 '5-Movi ID': MovimentoId,
                                 '1-Grau': ProcessoGrau,
                                 '4-Sigla Tribunal': ProcessoSiglaTribunal,
                                 '2-Assunto Primário': ProcessoAssuntoPrimario,
                                 '2-Assunto Secundário': ProcessoAssuntoSecundario,
                                 '2-Assunto Terciário': ProcessoAssuntoTerciario,
                                 '4-Assunto Local': ProcessoAssuntoLocal,
                                 '2-Assunto Descrição': ProcessoAssuntoDescricao,
                                 '4-Vinculado': ProcessoVinculado,
                                 '4-Relação Incidental': ProcessoRelacaoIncidental,
                                 '4-Prioridade': ProcessoPrioridade,
                                 '4-Valor Causa': ProcessoValorCausa,
                                 'ProcessoOrgaoJulgador': ProcessoOrgaoJulgador,
                                 'ProcessoOrgaoJulgadorTipo': ProcessoOrgaoJulgadorTipo,
                                 '4-Instância': ProcessoOrgaoJulgadorInstancia,
                                 '3-Orgão Julgador Município': ProcessoOrgaoJulgadorMunicipio,
                                 '3-Orgão Julgador UF': ProcessoOrgaoJulgadorUF,
                                 '4-Competência': ProcessoCompetencia,
                                 '4-Outros Números': ProcessoOutrosNumeros,
                                 '1-Classe Primária': ProcessoClassePrimaria,
                                 '1-Classe Secundária': ProcessoClasseSecundaria,
                                 '3-Processo Município': ProcessoMunicipio,
                                 '3-Processo UF': ProcessoUF,
                                 '4-Nível Sigilo': ProcessoNivelSigilo,
                                 '4-Intervenção MP': ProcessoIntervencaoMP,
                                 '4-Tamanho': ProcessoTamanho,
                                 '4-Data Ajuizamento': ProcessoDataAjuizamento,
                                 '4-Processo EL': ProcessoEl,
                                 '4-Sistema': ProcessoSistema,
                                 '4-Movi Primário': MovimentoPrimario,
                                 '5-Movi Nível Sigilo': MovimentoNivelSigilo,
                                 '4-Movi Tipo Respo': MovimentoTipoResponsavel,
                                 '5-Movi Local': MovimentoLocal,
                                 '5-Movi Complemento': MovimentoComplemento,
                                 '5-Movi Cód Comple': MovimentoCodComplemento,
                                 '5-Movi Doc Vinculado': MovimentoIdDocumentoVinculado,
                                 '5-Movi Órgão Julgador': MovimentoOrgaoJulgador,
                                 '5-Movi Órgão Julg Tipo': MovimentoOrgaoJulgadorTipo,
                                 '5-Movi Órgão Julg Inst': MovimentoOrgaoJulgadorInstancia,
                                 '5-Movi Órgão Julg Município': MovimentoOrgaoJulgadorMunicipio,
                                 '5-Movi Órgão Julg UF': MovimentoOrgaoJulgadorUF,
                                 '5-Movi Tipo Decisão': MovimentoTipoDecisao
                                 }])
    print('Arquivo {} gerado com sucesso!'.format(ofile))


if __name__ == '__main__':
    # Obtém caminho completo da pasta raiz quando o argumento for '.'
    if args.pastaRaiz == '.':
        args.pastaRaiz = os.path.dirname(os.path.abspath(__file__))

    # Gera tabelas processuais unificadas de forma hierarquizada
    hierarquiza_assuntos()
    hierarquiza_classes()
    hierarquiza_movimentos('nacional')
    hierarquiza_movimentos('local')

    # Gera a base JSON em CSV
    if args.assuntos:
        for assunto in args.assuntos:
            gera_csv(assunto)
    else:
        gera_csv(None)
