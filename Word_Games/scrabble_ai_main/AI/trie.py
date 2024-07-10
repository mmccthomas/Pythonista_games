class Trie:
    def __init__(self, word_list_file):
        self.root = TrieNode(False)
        with open(word_list_file, 'r', encoding='utf-8') as word_list:
            for line in word_list:
                word = line.strip().upper()
                #word = line.strip().replace('i', 'İ').upper()
                cur_node = self.root
                for letter in word:
                    if letter not in cur_node.children.keys():
                        new_node = TrieNode(False)
                        cur_node.children[letter] = new_node
                    cur_node = cur_node.children[letter]
                cur_node.word = word
                cur_node.is_word = True
        
    def lookup_string(self, word):
        cur_node = self.root
        for letter in word:
            if letter not in cur_node.children:
                return None
            cur_node = cur_node.children[letter]
        return cur_node
    
    def is_word(self, word):
        final_node = self.lookup_string(word)
        if final_node != None and final_node.is_word:
            return True
        return False

class TrieNode:
    def __init__(self, is_word):
        self.is_word = is_word
        self.word = "?"
        self.children = dict() # {letter: node}
