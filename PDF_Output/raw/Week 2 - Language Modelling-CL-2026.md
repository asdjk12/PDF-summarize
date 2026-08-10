![image 1](<Week 2 - Language Modelling-CL-2026_images/imageFile1.png>)

![image 2](<Week 2 - Language Modelling-CL-2026_images/imageFile2.png>)

# FIT5217

Natural Language Processing

Week 2 - Language Modelling

###### Trang Vu

(Slides and material built on the foundational work of Jurafsky & Martin; Kai-Wei Chang; Chris D. Manning; Yoav Artzi; Luke Zettlemoyer; Greg Durrett; Dan Klein; Alane Suhr; Mausam Jain, Tanmoy Chakraborty—along with our former CE, Ehsan Shareghi, who curated the majority of the content.)

##### Overview

- 1. What is a language model?
- 2. Context Length
- 3. The Chain Rule of probability
- 4. n-gram language models
- 5. Data sparsity issues
- 6. Smoothed n-grams
- 7. Evaluating model performance


Named must be your fear before banish

![image 4](<Week 2 - Language Modelling-CL-2026_images/imageFile4.png>)

it you can.

Named must be your fear before banish it you can

What?!!

WHAT?!!

Named must be your fear before banish it you can.

It is English, but it is not a proper sentence.

![image 6](<Week 2 - Language Modelling-CL-2026_images/imageFile6.png>)

Your fear must be named before you can banish it. It is English, and it is a proper sentence.

|For a sequence of length N, a language model calculates its probability as 𝑃 𝑤1 ,𝑤2 ,…,𝑤𝑁 , compactly written as 𝑃 𝑤1𝑁 . The probability indicates how likely it is for that sequence to belong to a language (e.g., training corpus domain).<br><br>|
|---|


|𝑃(Named must be your fear before banish it you can.)<br><br><<br><br>𝑃(Your fear must be named before you can banish it.)|
|---|


###### 5

![image 8](<Week 2 - Language Modelling-CL-2026_images/imageFile8.png>)

![image 9](<Week 2 - Language Modelling-CL-2026_images/imageFile9.png>)

###### *Note: let's call these words for now, but for LLMs we instead use tokens

https://web.stanford.edu/~jurafsky/slp3/slides/lm_jan25.pdf

### probabilities are calculated on a training text corpus

![image 11](<Week 2 - Language Modelling-CL-2026_images/imageFile11.png>)

![image 12](<Week 2 - Language Modelling-CL-2026_images/imageFile12.png>)

![image 13](<Week 2 - Language Modelling-CL-2026_images/imageFile13.png>)

![image 14](<Week 2 - Language Modelling-CL-2026_images/imageFile14.png>)

![image 15](<Week 2 - Language Modelling-CL-2026_images/imageFile15.png>)

![image 16](<Week 2 - Language Modelling-CL-2026_images/imageFile16.png>)

### Why Language Modelling? Speech Recognition

![image 18](<Week 2 - Language Modelling-CL-2026_images/imageFile18.png>)

P(I read the whole book) > P(I red the hole book)

### Why Language Modelling? Automatic Translation

|Président de la Chambre des représentants|
|---|


|President of the Bedroom of Representatives<br><br>President of the House of Representatives|
|---|


P(House | President of the ) > P(Bedroom | President of the)

### Why Language Modelling? Predictive Typing

![image 21](<Week 2 - Language Modelling-CL-2026_images/imageFile21.png>)

![image 22](<Week 2 - Language Modelling-CL-2026_images/imageFile22.png>)

* Courtesy of Forbes.

P(pokemon | Donald trump is a) > P(politician | Donald trump is a)

##### Overview

- 1. What is a language model?
- 2. Context Length
- 3. The Chain Rule of probability
- 4. n-gram language models
- 5. Data sparsity issues
- 6. Smoothed n-grams
- 7. Evaluating model performance


![image 25](<Week 2 - Language Modelling-CL-2026_images/imageFile25.png>)

![image 26](<Week 2 - Language Modelling-CL-2026_images/imageFile26.png>)

- * Courtesy of Forbes.


P(| Donald trump is ) vs P(politician | Donald trump is a)

![image 28](<Week 2 - Language Modelling-CL-2026_images/imageFile28.png>)

![image 29](<Week 2 - Language Modelling-CL-2026_images/imageFile29.png>)

- P(| Donald trump is a) vs P(politician | Donald trump is a p)
- * Courtesy of Forbes.


###### Donald Trump is a ? Trump is a ? is a ? a ?

Donald Trump is a ? Trump is a ? is a ? a ?

Accuracy

Donald Trump is a ? Trump is a ? is a ? a ?

Accuracy

Ideally, we would like to consider the entire context for a

DESIRED: more accurate prediction.

##### Overview

- 1. What is a language model?
- 2. Context Length
- 3. The Chain Rule of probability
- 4. n-gram language models
- 5. Data sparsity issues
- 6. Smoothed n-grams
- 7. Evaluating model performance


![image 35](<Week 2 - Language Modelling-CL-2026_images/imageFile35.png>)

![image 36](<Week 2 - Language Modelling-CL-2026_images/imageFile36.png>)

###### Generated image

![image 38](<Week 2 - Language Modelling-CL-2026_images/imageFile38.png>)

![image 39](<Week 2 - Language Modelling-CL-2026_images/imageFile39.png>)

###### i.e., P(W), the joint probability over the words/ sentence probability

![image 40](<Week 2 - Language Modelling-CL-2026_images/imageFile40.png>)

![image 41](<Week 2 - Language Modelling-CL-2026_images/imageFile41.png>)

![image 42](<Week 2 - Language Modelling-CL-2026_images/imageFile42.png>)

![image 43](<Week 2 - Language Modelling-CL-2026_images/imageFile43.png>)

![image 45](<Week 2 - Language Modelling-CL-2026_images/imageFile45.png>)

![image 46](<Week 2 - Language Modelling-CL-2026_images/imageFile46.png>)

![image 47](<Week 2 - Language Modelling-CL-2026_images/imageFile47.png>)

![image 48](<Week 2 - Language Modelling-CL-2026_images/imageFile48.png>)

![image 49](<Week 2 - Language Modelling-CL-2026_images/imageFile49.png>)

![image 50](<Week 2 - Language Modelling-CL-2026_images/imageFile50.png>)

###### We compactly write this as:

![image 51](<Week 2 - Language Modelling-CL-2026_images/imageFile51.png>)

### The chain rule - example

![image 53](<Week 2 - Language Modelling-CL-2026_images/imageFile53.png>)

##### Overview

- 1. What is a language model?
- 2. Context Length
- 3. The Chain Rule of probability
- 4. n-gram language models
- 5. Data sparsity issues
- 6. Smoothed n-grams
- 7. Evaluating model performance


![image 56](<Week 2 - Language Modelling-CL-2026_images/imageFile56.png>)

![image 57](<Week 2 - Language Modelling-CL-2026_images/imageFile57.png>)

![image 58](<Week 2 - Language Modelling-CL-2026_images/imageFile58.png>)

![image 60](<Week 2 - Language Modelling-CL-2026_images/imageFile60.png>)

###### Donald Trump is a ?

![image 61](<Week 2 - Language Modelling-CL-2026_images/imageFile61.png>)

![image 62](<Week 2 - Language Modelling-CL-2026_images/imageFile62.png>)

![image 63](<Week 2 - Language Modelling-CL-2026_images/imageFile63.png>)

|0|…|…|0|…|…|.18|…|…|.14|…|…|.32|…|.26|…|…|0|…|0|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|


![image 65](<Week 2 - Language Modelling-CL-2026_images/imageFile65.png>)

###### Donald Trump is a X

![image 66](<Week 2 - Language Modelling-CL-2026_images/imageFile66.png>)

![image 67](<Week 2 - Language Modelling-CL-2026_images/imageFile67.png>)

Compactly written as:

![image 68](<Week 2 - Language Modelling-CL-2026_images/imageFile68.png>)

###### Essentially need to assign a probability to each word of the vocabulary

Essentially need to assign a probability to each word of the vocabulary

Context Size = 1, Dictionary Size = 100, Number of parameters = 100 x (100 – 1) = 9900

![image 75](<Week 2 - Language Modelling-CL-2026_images/imageFile75.png>)

List all dictionary words and assign a probability to each word following them

Essentially need to assign a probability to each word of the vocabulary

Context Size = 1, Dictionary Size = 100, Number of parameters = 100 x (100 – 1) = 9900

![image 79](<Week 2 - Language Modelling-CL-2026_images/imageFile79.png>)

List all dictionary words and assign a probability to each word following them

Context Size = 10, Number of parameters = ??? (Homework!)

This is toy scale! Oxford dictionary size is 171,476!

Number of parameters grows exponentially

##### Context Matters

![image 81](<Week 2 - Language Modelling-CL-2026_images/imageFile81.png>)

Daniel Jurafsky and James H. Martin. 2025. Speech and Language Processing: An Introduction to Natural Language Processing, Computational Linguistics, and Speech Recognition with Language Models, 3rd edition. Online manuscript released January 12, 2025. https://web.stanford.edu/~jurafsky/slp3.

### Context Size vs. Memory Usage for Estimation

|| | | | | | | | | |
|---|---|---|---|---|---|---|---|---|
| | | | | | |![image 83](<Week 2 - Language Modelling-CL-2026_images/imageFile83.png>)| | |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
<br><br>0<br><br>50<br><br>100<br><br>150<br><br>200<br><br>250<br><br>300<br><br>2 3 4 5 6 7 8 9 10<br><br>Memory[GiB]<br><br>Amount of Context (Words)<br><br>memory consumption on 32 GiB of data|
|---|


![image 85](<Week 2 - Language Modelling-CL-2026_images/imageFile85.png>)

### Markov Assumption (n-gram LM)

###### • n-gram models are probabilistic models that predict the next word in a sentence given the n-1 preceding words of context.

Andrey Andreyevich Markov (1856 – 1922) , Russian Mathematician

- • 1-grams (unigrams) predict words based on zero words of context
- • 2-grams (bigrams) predict words based on one word of context
- • 3-grams (trigrams) prediction words based on two words of context etc. etc.


###### • TheMarkov assumptionis the assumption that future behavior only depends on recent history. In a k-th order Markov model, the next state

###### depends only on the most recent k states.

Source: https://www.americanscientist.org/article/first-links-in-the-markov-chain

![image 87](<Week 2 - Language Modelling-CL-2026_images/imageFile87.png>)

![image 90](<Week 2 - Language Modelling-CL-2026_images/imageFile90.png>)

| |
|---|


###### Unigram LM (n=1)

![image 93](<Week 2 - Language Modelling-CL-2026_images/imageFile93.png>)

| |
|---|


|![image 94](<Week 2 - Language Modelling-CL-2026_images/imageFile94.png>)|
|---|


OR

###### Unigram LM (n=1)

###### Bigram LM (n=2)

![image 97](<Week 2 - Language Modelling-CL-2026_images/imageFile97.png>)

| |
|---|


|![image 98](<Week 2 - Language Modelling-CL-2026_images/imageFile98.png>)|
|---|


|![image 99](<Week 2 - Language Modelling-CL-2026_images/imageFile99.png>)|
|---|


###### OR

###### OR

Unigram LM (n=1)

###### Bigram LM (n=2) Trigram LM (n=3)

![image 101](<Week 2 - Language Modelling-CL-2026_images/imageFile101.png>)

|?|
|---|


Imagine we are given the small corpus: <s>welcome home</s>

<s>welcome back</s>

<s>welcome home</s> <s>you are a welcome sight</s> <s>what a welcome</s>

|?|
|---|


|?|
|---|


- * Slide credit goes to Nigel Collier @ Cambridge


![image 103](<Week 2 - Language Modelling-CL-2026_images/imageFile103.png>)

Imagine we are given the small corpus: <s>welcome home</s>

<s>welcome back</s>

<s>welcome home</s> <s>you are a welcome sight</s> <s>what a welcome</s>

- * Slide credit goes to Nigel Collier @ Cambridge


![image 105](<Week 2 - Language Modelling-CL-2026_images/imageFile105.png>)

![image 106](<Week 2 - Language Modelling-CL-2026_images/imageFile106.png>)

###### True or False?

![image 108](<Week 2 - Language Modelling-CL-2026_images/imageFile108.png>)

###### Anything wrong with the top 3 probabilities?

##### Overview

- 1. What is a language model?
- 2. Context Length
- 3. The Chain Rule of probability
- 4. n-gram language models
- 5. Data sparsity issues
- 6. Smoothed n-grams
- 7. Evaluating model performance


### Let’s revisit our previous example

Donald Trump is a X

![image 111](<Week 2 - Language Modelling-CL-2026_images/imageFile111.png>)

What if we face the following situation:

|![image 112](<Week 2 - Language Modelling-CL-2026_images/imageFile112.png>)|
|---|


![image 113](<Week 2 - Language Modelling-CL-2026_images/imageFile113.png>)

### Data Sparsity

Intuitively speaking, as the length of a sequence grows it becomes less likely to find an exact match in a given text corpus!

### Related Issue – Out of Vocabulary (OOV) words

What if we were given the sequence “Meet the husband of Princess Hammock” but the word “Hammock” did not occur in our training

data?

![image 116](<Week 2 - Language Modelling-CL-2026_images/imageFile116.png>)

![image 117](<Week 2 - Language Modelling-CL-2026_images/imageFile117.png>)

* Courtesy of Friends TV Series

![image 118](<Week 2 - Language Modelling-CL-2026_images/imageFile118.png>)

### Solution

Maximum Likelihood Estimation (MLE) fails at dealing with data sparsity

scenarios as it solely estimates the probabilities based on the training

data.

What strategies exist to help with this?

- • Ensurethe training dataadequately represents the final application
- • Smoothing (Interpolation, Backoff)


##### Overview

- 1. What is a language model?
- 2. Context Length
- 3. The Chain Rule of probability
- 4. n-gram language models
- 5. Data sparsity issues 6. Smoothed n-grams 7. Evaluating model performance


- • How do we deal with n-grams which we have never seen in training?
- • Zero counts give zero probability estimates for both words and sentences.
- • But some zero count n-grams are valid sequences.
- • Smoothing is a class of techniques that aims to address this problem.
- • Intuition is to reassign probability mass from seen to unseen events whilst maintaining a joint distribution that sums to 1.


allegations

outcome

reports

###### attack

1 claims 1 request 7 total

…

man

reque

clai

ms

st

* Slides credit goes to Dan Klein/Dan Jurafsky. Data from the Wall Street Journal corpus.

allegations

outcome

reports

###### attack

1 claims 1 request 7 total

…

man

reque

clai

ms

st

###### • Steal probability mass to generalize better

P(w | u) 2.5 allegations

allegations

outcome

attack

reports

1.5 reports

…

man

w ∈

0.5 claims 0.5 request 2 other

uest

clai

ms

req

7 total

* Slides based on to Dan Klein/Dan Jurafsky.

### Add-1 Smoothing

Recall our Maximum Likelihood Estimate:

![image 125](<Week 2 - Language Modelling-CL-2026_images/imageFile125.png>)

Add-1 smoothing simply adds one to each count before normalization:

![image 126](<Week 2 - Language Modelling-CL-2026_images/imageFile126.png>)

whereVis the vocabulary size.

Question: Why do we need V in the denominator?

### Example of Add-1 smoothing for P(w|u)

|wi| | |
|---|---|---|
|allegations|3|3/7|
|reports|2|2/7|
|claims|1|1/7|
|request|1|1/7|
|outcome|0|0|
|fact|0|0|
|Total|7|7/7|


| | |
|---|---|
|4|4/13|
|3|3/13|
|2|2/13|
|2|2/13|
|1|1/13|
|1|1/13|
|13|13/13|


We’ve reduced our

likelihood by 28.2%

unsmoothed

Add-1 smoothing

### More data = less Add-1 smoothing

|wi| | | | |
|---|---|---|---|---|
|allegations|300|300/700|301|301/706|
|reports|200|200/700|201|201/706|
|claims|100|100/700|101|101/706|
|request|100|100/700|101|101/706|
|outcome|0|0|1|1/706|
|fact|0|0|1|1/706|
|Total|700|700/700|706|706/706|


###### We’ve reduced our likelihood by 0.5%.

unsmoothed Add-1 smoothing

### Larger Vocabulary = more Add-1 smoothing

• But suppose the size of our vocabulary was 2000 instead of 6:

|wi| | | | |
|---|---|---|---|---|
|allegations|300|300/700|301|301/2700|
|reports|200|200/700|201|201/2700|
|claims|100|100/700|101|101/2700|
|request|100|100/700|101|101/2700|
|outcome|0|0|1|1/2700|
|fact|0|0|1|1/2700|
|John|0|0|1|1/2700|
|…|0|0|1993|1993/2700|
|Total|700|700/700|2700|2700/2700|


Big change: We’ve reduced our likelihood by 73.9%

Add-1 smoothing thinks we are extremely likely to

see an unknown event. Is

having a big dictionary a good reason?

unsmoothed Add-1 smoothing

Add-k Smoothing

• One alternative to add-1 smoothing is to move a bit less of the probability mass

from the seen to unseen events. So, instead of adding one, we add a fractional

count k (i.e., k=0.5, 0.2, 0.01). This improves things only a little bit.

![image 131](<Week 2 - Language Modelling-CL-2026_images/imageFile131.png>)

K is typically chosen on a validation or development set.

n-gram smoothing

- • A large dictionary makes an unknown event too likely.
- • Add-1 smoothing gives away too much probability mass.
- • Is there a better way? Yes. Interpolation and backoff.


![image 133](<Week 2 - Language Modelling-CL-2026_images/imageFile133.png>)

Good reference if you want to know

about other smoothing techniques

![image 134](<Week 2 - Language Modelling-CL-2026_images/imageFile134.png>)

### Let’s revisit our previous example

![image 136](<Week 2 - Language Modelling-CL-2026_images/imageFile136.png>)

|![image 137](<Week 2 - Language Modelling-CL-2026_images/imageFile137.png>)|
|---|


![image 138](<Week 2 - Language Modelling-CL-2026_images/imageFile138.png>)

![image 140](<Week 2 - Language Modelling-CL-2026_images/imageFile140.png>)

###### 56

![image 141](<Week 2 - Language Modelling-CL-2026_images/imageFile141.png>)

56

![image 142](<Week 2 - Language Modelling-CL-2026_images/imageFile142.png>)

![image 143](<Week 2 - Language Modelling-CL-2026_images/imageFile143.png>)

![image 145](<Week 2 - Language Modelling-CL-2026_images/imageFile145.png>)

![image 146](<Week 2 - Language Modelling-CL-2026_images/imageFile146.png>)

![image 147](<Week 2 - Language Modelling-CL-2026_images/imageFile147.png>)

![image 149](<Week 2 - Language Modelling-CL-2026_images/imageFile149.png>)

![image 150](<Week 2 - Language Modelling-CL-2026_images/imageFile150.png>)

![image 151](<Week 2 - Language Modelling-CL-2026_images/imageFile151.png>)

![image 152](<Week 2 - Language Modelling-CL-2026_images/imageFile152.png>)

![image 154](<Week 2 - Language Modelling-CL-2026_images/imageFile154.png>)

![image 155](<Week 2 - Language Modelling-CL-2026_images/imageFile155.png>)

![image 156](<Week 2 - Language Modelling-CL-2026_images/imageFile156.png>)

![image 157](<Week 2 - Language Modelling-CL-2026_images/imageFile157.png>)

![image 158](<Week 2 - Language Modelling-CL-2026_images/imageFile158.png>)

![image 160](<Week 2 - Language Modelling-CL-2026_images/imageFile160.png>)

![image 161](<Week 2 - Language Modelling-CL-2026_images/imageFile161.png>)

![image 162](<Week 2 - Language Modelling-CL-2026_images/imageFile162.png>)

![image 163](<Week 2 - Language Modelling-CL-2026_images/imageFile163.png>)

![image 164](<Week 2 - Language Modelling-CL-2026_images/imageFile164.png>)

![image 165](<Week 2 - Language Modelling-CL-2026_images/imageFile165.png>)

![image 166](<Week 2 - Language Modelling-CL-2026_images/imageFile166.png>)

|3-gram|
|---|


Modified Kneser-Ney Smoothing

![image 168](<Week 2 - Language Modelling-CL-2026_images/imageFile168.png>)

This is an interpolation smoothing, and you can see the recursive form of it.

![image 169](<Week 2 - Language Modelling-CL-2026_images/imageFile169.png>)

![image 170](<Week 2 - Language Modelling-CL-2026_images/imageFile170.png>)

###### Not Examinable

#### Stupid backoff

![image 172](<Week 2 - Language Modelling-CL-2026_images/imageFile172.png>)

![image 173](<Week 2 - Language Modelling-CL-2026_images/imageFile173.png>)

## Summary of Smoothing, Interpolation, and Backoff

Smoothing: Pretend you saw every n-gram one (or k) times more than you did

- • A blunt instrument (replacing a lot of zeros) but sometimes useful

Backoff: If you haven't seen the trigram, use the (weighted) bigram probability instead

- • Weighting is messy; "stupid" backoff works fine at web-scale

Interpolation: (weighted) mix of trigram, bigram, unigram

- • Usually the best! We also use interpolation to combine multiple LLMs


### Out Of Vocabulary (OOV) – a common trick

One way to handle OOV (unknown words) is to set a frequency threshold (i.e., threshold = 3) and replace all the words in the training data below this frequency threshold with a special token <UNK> at training time. This solution shares the probability mass of all the rare words in the training corpus and accumulates them under the <UNK> token. Then at test time we replace all unseen words

with <UNK>. This avoids assigning zero probabilities to sequences with unseen

words.

##### Overview

- 1. What is a language model?
- 2. Context Length
- 3. The Chain Rule of probability
- 4. n-gram language models
- 5. Data sparsity issues
- 6. Smoothed n-grams
- 7. Evaluating model performance


- • Evaluating model performance is a key issue in NLP.
- • There are a variety of methods to evaluate NLP models. Broadly divided into:


###### • Extrinsic evaluation: put each model into a task (e.g. MT, spelling correction), test on real-world data.

• Realistic (best for comparing two or more models), expensive

###### • Intrinsic evaluation: application-independent evaluations that often correlate with improvements in applications.

• Less realistic, cheaper

### Perplexity

- • Perplexity is the most common intrinsic evaluation metric for n-gram models.
- • A measure of how well the language model ‘predicts’ the test data.
- • The higher the prediction probabilities (the lower the perplexity will be), the better the model.
- • Can think of perplexity as the average number of guesses the model makes to correctly predict the next word.
- • Lower perplexity is better.


![image 179](<Week 2 - Language Modelling-CL-2026_images/imageFile179.png>)

![image 180](<Week 2 - Language Modelling-CL-2026_images/imageFile180.png>)

|3.93<br><br>2.69<br><br>2.37|
|---|


20-gram 10-gram

1 Billion Words Corpus

5-gram

Perplexity (# of guesses required for correct prediction)

##### Challenges with n-gram models

- 1. N-grams can't handle long-distance dependencies: “The soups that I made from that new cookbook I bought yesterday were amazingly delicious."
- 2. N-grams don't do well at modeling new sequences (even if they have similar meanings to sequences they've seen)

Ex: suppose "I drove the car" appears 1000 times vs appears first time: "I drove the automobile"

. What probability will be assigned to it??

- 3. Data Sparsity, Smoothing redistributes probability mass to unseen n-grams, but blindly.


It cannot recognize that "the cat sat" and "the dog sat" are semantically related, so it treats every unseen n-gram as equally plausible regardless of meaning.

The solution: Large language models

- • can handle much longer contexts
- • because they use neural embedding spaces, can model meaning better


### Popular n-gram LM toolkits

###### KenLM https://github.com/kpu/kenlm

|![image 184](<Week 2 - Language Modelling-CL-2026_images/imageFile184.png>)|
|---|


###### SRILM http://www.speech.sri.com/projects/srilm

Run over the data, precompute the probabilities and coefficients of (modified) kneser-ney smoothing for

the given n-gram order. Store it on a giant ARPA file

that looks like this, and then use it with loads of engineering tricks at query phase as a lookup table.

But everything is now neural models. They perform so well on language

Last word

modelling, why should I use an n-gram LM any ways?

![image 186](<Week 2 - Language Modelling-CL-2026_images/imageFile186.png>)

![image 187](<Week 2 - Language Modelling-CL-2026_images/imageFile187.png>)

- • 50 languages covering all morphological families.
- • A simple extension of Modified Kneser-Ney outperforms LSTM language model on 42 languages.
- • Bayesiann-gram LM outperforms the character-aware neural model on average across all languages
- • n-gram models lend themselves as natural choices for resource-lean or morphologically rich languages
- • n-grams are still used in NLP pipeline: pre-processing, evaluation


![image 189](<Week 2 - Language Modelling-CL-2026_images/imageFile189.png>)

###### Feedback time!

![image 191](<Week 2 - Language Modelling-CL-2026_images/imageFile191.png>)

![image 192](<Week 2 - Language Modelling-CL-2026_images/imageFile192.png>)

![image 193](<Week 2 - Language Modelling-CL-2026_images/imageFile193.png>)

** Please submit weekly Feedback! **

![image 194](<Week 2 - Language Modelling-CL-2026_images/imageFile194.png>)

