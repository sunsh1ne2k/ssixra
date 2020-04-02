san_strings = [';','$','&&','../','<','>','%3C','%3E','\'','--','1,2','\x00','`','(',')','file://','input://']

def sanitize(input):
    sanitized = input
    for s in san_strings:
        if s in sanitized:
            sanitized = sanitized.replace(s, '')
    return sanitized

def contains_sanstr(input):
    for s in san_strings:
        if s in input:
            return True
    return False