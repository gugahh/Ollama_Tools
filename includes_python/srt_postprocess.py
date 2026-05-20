import re

def fc_remove_lixo_traducao(strTxtIn):
    '''
        Tenta remover erros de formatacao e lixos deixados pelo Modelo de IA no conteudo
        traduzido. O formato SRT e muito formal, e o nosso programa espera 
        que nao haja repeticoes indevidas, tambem.
        Retorna o texto ja saneado.
    '''

    '''
        Caso de ajuste 1: ### repetido (com linha em branco no meio).
        Vou fazer isso 2x, para garantir.
    '''
    for i in range(2):
        strTxtIn = strTxtIn.replace("###\n\n###", "###")

    '''
        Caso de ajuste 2: Linhas do tipo ### (texto);
        (o texto era para estar na linha seguinte ao ###, e nao na mesma linha)
    '''
    lines = strTxtIn.strip().split('\n')

    # Initialize an empty list to hold the modified lines
    modified_lines = []

    # Iterate over each line
    for line in lines:
        # Match the regex pattern at the start of the line
        match = re.match(r'^### ', line)
        
        if match:
            # Replace '^### ' with '###\n'
            modified_line = '###' + '\n' + line[4:]
            modified_lines.append(modified_line)
        else:
            # If no match, just append the original line
            modified_lines.append(line)

    # Join the modified lines back into a single string
    txt_out = '\n'.join(modified_lines)

    return txt_out