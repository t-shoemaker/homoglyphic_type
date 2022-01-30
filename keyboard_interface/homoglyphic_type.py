import json, random, unicodedata
from pynput.keyboard import Listener

with open("./data/unicode_confusables.json", 'r') as f:
    confusables = json.load(f)
    # remove confusables whose base forms need to be compiled
    confusables = {k:v for k,v in confusables.items() if len(k)==4}
    
with open("./data/non_alphanumeric_subs.json", 'r') as f:
    # a multi-level dictionary that contains various character substitutions for 
    # non-alphanumeric keys
	sub_manifold = json.load(f)
    
def homoglyph_sub(letter):
    letter_hex = hex(ord(letter))
    letter_hex = letter_hex.replace("x", "0")
    if letter_hex.upper() in confusables.keys():
        substitute = random.choice(confusables[letter_hex.upper()])
        substitute = int(substitute, 16)
        return str(chr(substitute))
    else:
        return letter

def filter_operators(letter):
    if letter in sub_manifold['operators'].keys():
        letter = sub_manifold['operators'][letter]
    else:
        letter = letter[1:-1]
        letter = homoglyph_sub(letter)
    return letter
    
def handle_modifiers(letter):
    # convert keyed modifier codes to modifiers
    if letter in sub_manifold['modifiers'].keys():
        letter = sub_manifold['modifiers'][letter]
        
    # compile accented characters by looking back one position in the homoglyph stream
    # to see whether it's a compilable modifier
    if len(homoglyph_stream) >= 1:
        for char in homoglyph_stream[-1]:
            char = "'{}'".format(char)
            if char in sub_manifold['modifier_pairs'].keys():
                try:
                    letter = sub_manifold['modifier_pairs'][char][letter]
                    homoglyph_stream[-1] = ""
                # handle instances where two modifiers are typed in sequence (and thus
                # not to be found in modifier_pairs)
                except:
                    pass
    return letter

homoglyph_stream = []
def write_to_log(key):
    letter = str(key)
    if letter == "Key.backspace":
        while len(homoglyph_stream) > 1:
            return homoglyph_stream.pop()
        else:
            pass
            
    # ESC key = quit listening and logging
    if letter == "Key.esc":
        with open("log_final.txt", 'w') as f:
            f.writelines(homoglyph_stream)
        return False
        
    letter = handle_modifiers(letter)
    letter = filter_operators(letter)
    with open("log.txt", 'a') as f:
        f.write(letter)
    homoglyph_stream.append(letter)
    print("\n",''.join(homoglyph_stream))
    
def main():
    print("Begin typing")
    with Listener(on_press=write_to_log) as l:
    	l.join()

if __name__ == "__main__":
    main()
