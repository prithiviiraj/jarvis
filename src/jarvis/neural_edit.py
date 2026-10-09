"""Owner's unsent popup edit, no vault write or external effect."""
def text(value):
 if not isinstance(value,str)or not 0<len(value.strip())<=4000:raise ValueError('Enter visual text up to4000characters')
 return value
