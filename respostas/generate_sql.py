#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera schema.sql e insert.sql a partir dos arquivos TSV
"""

import csv
import re
import unicodedata

def normalizar_nome_coluna(nome):
    """
    Normaliza nome de coluna para SQL:
    - Remove acentos
    - Substitui espaços e caracteres especiais por _
    - Remove : ? e outros caracteres problemáticos
    - Converte para minúsculas
    """
    # Remove acentos
    nfkd = unicodedata.normalize('NFKD', nome)
    sem_acentos = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    
    # Remove caracteres especiais e substitui por _
    normalizado = re.sub(r'[^a-zA-Z0-9]+', '_', sem_acentos)
    
    # Remove _ do início e fim
    normalizado = normalizado.strip('_')

    # Normaliza digitos
    if normalizado and normalizado[0].isdigit():
        normalizado = 'q_' + normalizado
    
    # Coverte para minúsculas
    return normalizado.lower()

def escapar_sql_string(valor):
    """
    Escapa string para SQL (substitui ' por '')
    """
    if valor is None or valor == '':
        return 'NULL'
    
    # Remove espaços em branco extras
    valor = str(valor).strip()
    
    if valor == '' or valor.lower() == 'sem resposta*':
        return 'NULL'
    
    # Escapa aspas simples
    valor_escapado = valor.replace("'", "''")
    
    return f"'{valor_escapado}'"

def inferir_tipo_coluna(nome_original):
    """
    Infere tipo de dados baseado no nome da coluna
    """
    nome_lower = nome_original.lower()
    
    # Identificadores são INTEGER
    if 'id' in nome_lower or 'numero' in nome_lower or 'questionario' in nome_lower:
        return 'INTEGER'
    
    # Idade é INTEGER
    if 'idade' in nome_lower or 'populacao' in nome_lower or 'familias' in nome_lower:
        return 'INTEGER'
    
    # Telefone, email, nomes são TEXT
    return 'TEXT'

def ler_tsv(arquivo):
    """
    Lê arquivo TSV e retorna lista de dicionários
    """
    with open(arquivo, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        return list(reader), reader.fieldnames

def gerar_schema(comunidades_campos, perfis_campos):
    """
    Gera o schema.sql
    """
    sql = []
    sql.append("-- Schema gerado automaticamente")
    sql.append("-- Encoding: UTF-8\n")
    
    # Tabela Comunidades
    sql.append("DROP TABLE IF EXISTS perfis;")
    sql.append("DROP TABLE IF EXISTS comunidades;\n")
    
    sql.append("CREATE TABLE comunidades (")
    colunas = []
    
    for campo in comunidades_campos:
        nome_norm = normalizar_nome_coluna(campo)
        tipo = inferir_tipo_coluna(campo)
        
        # Chave primária
        if 'numero' in campo.lower() and 'questionario' in campo.lower():
            colunas.append(f"    {nome_norm} {tipo} PRIMARY KEY")
        else:
            colunas.append(f"    {nome_norm} {tipo}")
    
    sql.append(",\n".join(colunas))
    sql.append(");\n")
    
    # Tabela Perfis
    sql.append("CREATE TABLE perfis (")
    colunas = []
    
    for i, campo in enumerate(perfis_campos):
        nome_norm = normalizar_nome_coluna(campo)
        tipo = inferir_tipo_coluna(campo)
        
        # ID automático como chave primária
        if i == 0:
            colunas.append(f"    perfil_id INTEGER PRIMARY KEY AUTOINCREMENT")
        
        # Chave estrangeira
        if 'id' in campo.lower() and 'questionario' in campo.lower():
            colunas.append(f"    {nome_norm} {tipo}")
            colunas.append(f"    FOREIGN KEY ({nome_norm}) REFERENCES comunidades(numero_do_questionario)")
        else:
            colunas.append(f"    {nome_norm} {tipo}")
    
    sql.append(",\n".join(colunas))
    sql.append(");\n")
    
    return "\n".join(sql)

def gerar_inserts(comunidades_dados, comunidades_campos, perfis_dados, perfis_campos):
    """
    Gera o insert.sql
    """
    sql = []
    sql.append("-- Inserts gerados automaticamente")
    sql.append("-- Encoding: UTF-8\n")
    
    # Inserts para Comunidades
    sql.append("-- Inserindo comunidades\n")
    
    for linha in comunidades_dados:
        colunas_norm = [normalizar_nome_coluna(c) for c in comunidades_campos]
        valores = [escapar_sql_string(linha.get(c, '')) for c in comunidades_campos]
        
        sql.append(f"INSERT INTO comunidades ({', '.join(colunas_norm)})")
        sql.append(f"VALUES ({', '.join(valores)});")
        sql.append("")
    
    # Inserts para Perfis
    sql.append("\n-- Inserindo perfis\n")
    
    for linha in perfis_dados:
        # Pula o campo de ID auto-increment
        colunas_norm = [normalizar_nome_coluna(c) for c in perfis_campos]
        valores = [escapar_sql_string(linha.get(c, '')) for c in perfis_campos]
        
        sql.append(f"INSERT INTO perfis ({', '.join(colunas_norm)})")
        sql.append(f"VALUES ({', '.join(valores)});")
        sql.append("")
    
    return "\n".join(sql)

def main():
    print("Lendo arquivos TSV...")
    
    # Lê os arquivos
    comunidades_dados, comunidades_campos = ler_tsv('Comunidades.tsv')
    perfis_dados, perfis_campos = ler_tsv('Perfis.tsv')
    
    print(f"✓ Comunidades: {len(comunidades_dados)} registros, {len(comunidades_campos)} campos")
    print(f"✓ Perfis: {len(perfis_dados)} registros, {len(perfis_campos)} campos")
    
    # Gera schema.sql
    print("\nGerando schema.sql...")
    schema_sql = gerar_schema(comunidades_campos, perfis_campos)
    
    with open('schema.sql', 'w', encoding='utf-8') as f:
        f.write(schema_sql)
    
    print("✓ schema.sql criado")
    
    # Gera insert.sql
    print("\nGerando insert.sql...")
    insert_sql = gerar_inserts(comunidades_dados, comunidades_campos, 
                               perfis_dados, perfis_campos)
    
    with open('insert.sql', 'w', encoding='utf-8') as f:
        f.write(insert_sql)
    
    print("✓ insert.sql criado")
    
    print("\n✅ Concluído! Agora você pode executar:")
    print("   sqlite3 quilombolas.db < schema.sql")
    print("   sqlite3 quilombolas.db < insert.sql")

if __name__ == '__main__':
    main()
