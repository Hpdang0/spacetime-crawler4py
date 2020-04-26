import hashlib

class Tokenizer:
    final_dict = dict()
    max_count = 0

    stopwords = []
    file = open("stopwords.txt",'r')
    lines = file.read().split()
    for word in lines:
        stopwords.append(word)

    similarity_threshold = .85

    def Tokenize(self, input_list):
        token_dict = dict()
        word_count = 0

        for word in input_list:
            word = word.lower().strip("!@#$%^&*(),-_=+./:;''\\][`")
            if len(word) >3 :
                if word not in self.stopwords:
                    word_count += 1

                    if token_dict.get(word) == None :
                        token_dict[word] = 1
                    else:
                        token_dict[word] += 1

                    if self.final_dict.get(word) == None:
                        self.final_dict[word] = 1
                    else:
                        self.final_dict[word] += 1

        if word_count > self.max_count:
            self.max_count = word_count

        # print(word_count)

        return token_dict


    def Similarity(self, dict1, dict2):
        # print(dict1, dict2)
        if self._compute_similarity(self.create_simhash(dict1), self.create_simhash(dict2)) >= .9:
            return True
        return False

        
    def _compute_similarity(self, hash1, hash2):
        # Retuns the % of similarity between two hashes
        total_size = len(hash1)
        similar = 0
        for i in range(total_size):
            if hash1[i] == hash2[i]:
                similar += 1
        
        print(similar/total_size)
        return similar/total_size

    def create_simhash(self, words_dict):
        hash_digest_size = 64
        
        weights = []
        for i in range(hash_digest_size * 8):
            weights.append(int())

        for word in words_dict:
            hash = hashlib.blake2b(digest_size=hash_digest_size)
            # print('Working with: {}'.format(word))
            hash.update(word.encode('utf-8'))
            hashed = hash.digest()
            hashed_bytes = self.ensure_padding(''.join(format(int(b), 'b') for b in hashed), hash.digest_size * 8)
            # print(hashed_bytes)
            # print('>> Bytes: {}'.format(hashed_bytes))

            for i in range(hash.digest_size * 8):
                if bool(int(hashed_bytes[i])):
                    weights[i] += words_dict[word]
                else:
                    weights[i] -= words_dict[word]
            
            # print('>> Weightings: {}'.format(weights))

        # print('>> Weightings: {}'.format(weights))
        print('>> Normalized Weightings: {}'.format(self.normalize_weights(weights)))
        # print()
        return self.normalize_weights(weights)


    def Max_count(self):
        return self.max_count

    def Final_dict(self):
        return self.final_dict

    def ensure_padding(self, hashed_bytes, total_size):
        if len(hashed_bytes) >= total_size:
            return hashed_bytes
        
        extra_padding = total_size - len(hashed_bytes)    
        return '0' * extra_padding + hashed_bytes

    def normalize_weights(self, weights):
        normalized = weights
        for i in range(len(normalized)):
            if normalized[i] > 0:
                normalized[i] = 1
            else:
                normalized[i] = 0
        
        return normalized
