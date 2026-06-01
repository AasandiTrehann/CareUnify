import re

def soundex(name: str) -> str:
    """Computes the Soundex code for a given name."""
    if not name:
        return "0000"
    
    # Clean the name
    name = re.sub(r'[^A-Z]', '', name.upper())
    if not name:
        return "0000"
        
    first_letter = name[0]
    
    # Soundex mappings
    mappings = {
        'B': '1', 'F': '1', 'P': '1', 'V': '1',
        'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
        'D': '3', 'T': '3',
        'L': '4',
        'M': '5', 'N': '5',
        'R': '6'
    }
    
    # Translate remaining letters
    digits = []
    prev_code = mappings.get(first_letter, '0')
    
    for char in name[1:]:
        code = mappings.get(char, '0')
        # Skip if same code adjacent, or if code is '0' (vowels/h/w/y)
        if code != '0' and code != prev_code:
            digits.append(code)
            prev_code = code
        elif code == '0':
            # Vowels separate letters, reset prev_code
            # But h and w do not separate, so only reset if not H or W
            if char not in ('H', 'W'):
                prev_code = '0'
                
    # Format to 1 letter and 3 digits
    soundex_code = first_letter + "".join(digits)
    soundex_code = soundex_code[:4].ljust(4, '0')
    return soundex_code

def nysiis(name: str) -> str:
    """Computes the NYSIIS code for a given name (standard approximation)."""
    if not name:
        return ""
    
    name = re.sub(r'[^A-Z]', '', name.upper())
    if not name:
        return ""
        
    # 1. Translate first characters of name
    if name.startswith("MAC"):
        name = "MCC" + name[3:]
    elif name.startswith("KN"):
        name = "N" + name[2:]
    elif name.startswith("K"):
        name = "C" + name[1:]
    elif name.startswith("PH") or name.startswith("PF"):
        name = "FF" + name[2:]
    elif name.startswith("SCH"):
        name = "SSS" + name[3:]
        
    # 2. Translate last characters of name
    if name.endswith("EE") or name.endswith("IE"):
        name = name[:-2] + "Y"
    elif name.endswith("DT") or name.endswith("RT") or name.endswith("RD") or name.endswith("NT") or name.endswith("ND"):
        name = name[:-2] + "D"
        
    # 3. Process remaining characters
    key = [name[0]]
    i = 1
    length = len(name)
    
    while i < length:
        ch = name[i]
        
        # Rule translation
        if ch == 'E' and i + 1 < length and name[i+1] == 'V':
            key.append("AF")
            i += 2
            continue
        elif ch in ['A', 'E', 'I', 'O', 'U']:
            key.append('A')
        elif ch == 'Q':
            key.append('G')
        elif ch == 'Z':
            key.append('S')
        elif ch == 'M':
            key.append('N')
        elif ch == 'K':
            if i + 1 < length and name[i+1] == 'N':
                key.append('N')
                i += 2
                continue
            else:
                key.append('C')
        elif ch == 'S' and i + 2 < length and name[i+1:i+3] == "CH":
            key.append("SSS")
            i += 3
            continue
        elif ch == 'P' and i + 1 < length and name[i+1] == 'H':
            key.append("FF")
            i += 2
            continue
        elif ch == 'H':
            # If previous or next character is not a vowel, keep previous, else drop H
            prev_vowel = name[i-1] in ['A', 'E', 'I', 'O', 'U'] if i > 0 else False
            next_vowel = name[i+1] in ['A', 'E', 'I', 'O', 'U'] if i + 1 < length else False
            if not prev_vowel or not next_vowel:
                # Do nothing, H is omitted
                pass
        elif ch == 'W':
            # If previous is vowel, keep previous
            prev_vowel = name[i-1] in ['A', 'E', 'I', 'O', 'U'] if i > 0 else False
            if prev_vowel:
                # Omit W
                pass
            else:
                key.append('W')
        else:
            key.append(ch)
            
        i += 1
        
    # Standard cleanup of double characters and trailing letters
    result = "".join(key)
    # Deduplicate adjacent duplicate characters
    dedup = [result[0]]
    for char in result[1:]:
        if char != dedup[-1]:
            dedup.append(char)
            
    result = "".join(dedup)
    
    if result.endswith("JR") or result.endswith("SR"):
        result = result[:-2]
        
    # Trim trailing A or S
    if len(result) > 1:
        if result.endswith("A"):
            result = result[:-1]
        elif result.endswith("S"):
            result = result[:-1]
            
    return result
