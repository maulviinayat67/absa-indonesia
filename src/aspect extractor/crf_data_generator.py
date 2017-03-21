import nltk
from conll_table import CONLLTable
from nltk import word_tokenize
from nltk.util import ngrams
from collections import Counter

class CRFDataGenerator:
	def __init__(self):
		self.list_unigrams = []
		self.list_bigrams = []
		self.list_trigrams = []
		self.list_pos_tag_trigrams = []
		self.CONLL_table = CONLLTable("../../data/output1.conll")

	def init_dependency_tags(self):
		bag_of_vbot = {}
		with open("../../data/dependency_tags.txt", "r") as f:
			for line in f:
				line = line.rstrip()
				tokens = line.split()
				bag_of_vbot[tokens[0]] = 0
		return bag_of_vbot

	def get_list_unigrams(self):
		return self.list_unigrams

	def get_list_bigrams(self):
		return self.list_bigrams

	def get_list_trigrams(self):
		return self.list_trigrams

	def get_list_pos_tag_trigrams(self):
		return self.list_pos_tag_trigrams

	def get_window_text(self, n, tokens, pos):
		center = int(n/2) + 1
		text = ""
		if (pos < center) and (pos+int(n/2) >= len(tokens)):
			for i in range(0, len(tokens)):
				text += tokens[i] + " "
		elif (pos < center):
			for i in range (0, pos+int(n/2)+1):
				text += tokens[i] + " "
		elif (pos+int(n/2) >= len(tokens)):
			for i in range(pos - int(n/2), len(tokens)):
				text += tokens[i] + " "
		else:
			for i in range(pos - int(n/2), pos+int(n/2)+1):
				text += tokens[i] + " "

		return text[:-1]

	def get_n_grams(self, n, sentences):
		result = {}
		for sentence in sentences:
			ngram = Counter(ngrams(sentence.split(), n))
			for key in ngram:
				if key not in result:
					if (n == 1):
						result[key[0]] = ngram[key]
					else:
						result[key] = ngram[key]
				else:
					if (n == 1):
						result[key[0]] += ngram[key]
					else:
						result[key] += ngram[key]
		return result

	def get_n_grams_feature(self, n, window_text, list_n_grams):
		line = ""
		window_ngrams = Counter(ngrams(nltk.word_tokenize(window_text), n))

		for n_grams in list_n_grams:
			if (n_grams in window_ngrams):
				line += " " + str(window_ngrams[n_grams])
			else:
				line += " 0"
		return line

	def get_dependency_tags_feature(self, id_sentence):
		bag_of_vbot = self.init_dependency_tags()
		line = ""
		filter = ["VERB"]
		words = self.CONLL_table.filter_words_by_pos_tag(id_sentence, filter)
		for key1 in words:
			children = self.CONLL_table.get_children(key1, id_sentence)
			for key2, value2 in children.iteritems():
				bag_of_vbot[self.CONLL_table.get_tree_tag(value2)] += 1

			siblings = self.CONLL_table.get_siblings(key1, id_sentence)
			for key2, value2 in siblings.iteritems():
				bag_of_vbot[self.CONLL_table.get_tree_tag(value2)] += 1

		for key, value in bag_of_vbot.iteritems():
			line += " " + str(value)

		return line

	def get_dict_feature(self, label):
		line = ""
		if (label == "ASPECT-B" or label == "ASPECT-I"):
			line += " yes"
		else:
			line += " no"
		return line

	def get_feature(self, id_sentence, id_word):
		row = self.CONLL_table.get_row(id_sentence, id_word)
		line = self.CONLL_table.get_word(row) + " " + self.CONLL_table.get_pos_tag(row)

		label = self.CONLL_table.get_label(row)
		
		window_text = self.get_window_text(5, self.CONLL_table.get_sentence(id_sentence).split(), id_word)
		
		line += self.get_n_grams_feature(1, window_text, self.list_unigrams)
		line += self.get_n_grams_feature(2, window_text, self.list_bigrams)
		line += self.get_n_grams_feature(3, window_text, self.list_trigrams)

		window_pos_tag = self.get_window_text(5, self.CONLL_table.get_sentence_pos_tag(id_sentence).split(), id_word)
		line += self.get_n_grams_feature(3, window_pos_tag, self.list_pos_tag_trigrams)

		return line + " " + label + "\n"

	def generate_data(self, filename, start=0, end=None):
		reviews = self.CONLL_table.get_sentences(start, end)

		filter = ["NOUN", "ADJ", "ADV", "VERB"]
		unigrams = self.get_n_grams(1, self.CONLL_table.get_filtered_sentences(filter))

		bigrams = [b for l in reviews for b in zip(l.split(" ")[:-1], l.split(" ")[1:])]
		bigrams = Counter(bigrams)

		trigrams = self.get_n_grams(3, reviews)
		trigrams_postag = self.get_n_grams(3, self.CONLL_table.get_sentences_pos_tag())

		for key in unigrams:
			self.list_unigrams.append(key)

		for key in bigrams:
			self.list_bigrams.append(key)

		for key in trigrams:
			self.list_trigrams.append(key)

		for key in trigrams_postag:
			self.list_pos_tag_trigrams.append(key)

		with open(filename, 'w') as f:
			for i in range(self.CONLL_table.get_sentences_size()):
				for j in range(self.CONLL_table.get_sentence_size(i)):
					f.write(self.get_feature(i, j+1))
				f.write("\n")


if __name__ == '__main__':
	cdg = CRFDataGenerator()
	cdg.generate_data('../../data/train_CRF.txt')

	with open("../../data/list_unigrams.txt", 'w') as f:
		for word in cdg.get_list_unigrams():
			f.write(word + "\n")

	with open("../../data/list_bigrams.txt", 'w') as f:
		for bigrams in cdg.get_list_bigrams():
			line = ','.join(str(x) for x in bigrams)
			f.write(line + "\n")

	with open("../../data/list_trigrams.txt", 'w') as f:
		for trigrams in cdg.get_list_trigrams():
			line = ','.join(str(x) for x in trigrams)
			f.write(line + "\n")

	with open("../../data/list_pos_tag_trigrams.txt", 'w') as f:
		for trigrams in cdg.get_list_pos_tag_trigrams():
			line = ','.join(str(x) for x in trigrams)
			f.write(line + "\n")

	