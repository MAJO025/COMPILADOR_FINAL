TNAME = {
    'keyword':    'Palabra clave',
    'identifier': 'Identificador',
    'number':     'Número',
    'string':     'Cadena',
    'operator':   'Operador',
    'symbol':     'Separador',
    'comment':    'Comentario',
    'unknown':    'No identificado'
}

def get_clasif(tk):
    t, v = tk['t'], tk['v']
    if t == 'identifier': return 'Identificador de usuario'
    if t == 'keyword':    return get_kw_clasif(v)
    if t == 'number':     return 'Literal numérico'
    if t == 'string':     return 'Literal'
    if t == 'operator':   return 'Operador'
    if t == 'symbol':     return 'Delimitador'
    if t == 'comment':    return 'Comentario'
    if t == 'unknown':    return 'Error léxico'
    return '—'

def get_sub_clasif(tk):
    t, v = tk['t'], tk['v']
    if t == 'identifier': return 'Privado/especial' if v.startswith('_') else 'Simple'
    if t == 'keyword':    return get_kw_type(v)
    if t == 'number':     return get_num_type(v)
    if t == 'string':     return 'f-string' if v.lower().startswith('f') else 'Cadena'
    if t == 'operator':   return get_op_type(v)
    if t == 'symbol':     return get_sym_type(v)
    if t == 'comment':    return 'Línea' if v.startswith('#') or v.startswith('//') else 'Bloque'
    return '—'

def get_kw_clasif(v):
    if v in ['if','else','elif','switch','case']:           return 'Control condicional'
    if v in ['for','while','do','break','continue']:        return 'Control iterativo'
    if v in ['return','yield','pass']:                      return 'Control de flujo'
    if v in ['int','float','double','char','bool','void','string']: return 'Tipo de dato'
    if v in ['class','struct','interface','enum']:          return 'Definición de tipo'
    if v in ['def','function','lambda']:                    return 'Definición función'
    if v in ['import','from','as','include','using']:       return 'Importación'
    if v in ['true','false','True','False','null','None','undefined']: return 'Literal booleano/nulo'
    if v in ['try','catch','finally','throw','raise','except']: return 'Manejo excepciones'
    return 'Reservada'

def get_kw_type(v):
    if v in ['true','True']:              return 'Booleano verdadero'
    if v in ['false','False']:            return 'Booleano falso'
    if v in ['null','None','undefined']:  return 'Nulo'
    return '—'

def get_num_type(v):
    if '.' in v or 'e' in v.lower():     return 'Real / flotante'
    if v.startswith(('0x','0X')):        return 'Hexadecimal'
    if v.startswith(('0b','0B')):        return 'Binario'
    if v.startswith(('0o','0O')):        return 'Octal'
    return 'Entero'

def get_op_type(v):
    if v in ['+','-','*','/','%','**','//']: return 'Aritmético'
    if v in ['==','!=','<','>','<=','>=']:   return 'Relacional'
    if v in ['&&','||','!','and','or','not']: return 'Lógico'
    if v == '=' or (v.endswith('=') and len(v) > 1 and v not in ['==','!=','<=','>=']): return 'Asignación'
    if v in ['&','|','^','~','<<','>>']:     return 'Bit a bit'
    return '—'

def get_sym_type(v):
    if v in ['(',')','{','}','[',']']: return 'Agrupador'
    if v in [';',',','.']:             return 'Separador'
    if v == ':':                       return 'Dos puntos'
    return 'Delimitador'

def enrich_tokens(tokens):
    for tk in tokens:
        tk['clasif']   = get_clasif(tk)
        tk['subclasif'] = get_sub_clasif(tk)
        tk['tname']    = TNAME.get(tk['t'], '—')
    return tokens
