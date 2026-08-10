![image 1](<Week 3 - Sequence Labelling-CL_images/imageFile1.png>)

## FIT5217

Natural Language Processing

###### Week 3 - Sequence Labelling

###### Trang Vu

Slides build on various sources: Jurafsky and Manning, Nigel Collier

#### Overview

- 1. Word categories
- 2. Part-of-Speech (POS) Tagging
- 3. Other Sequence Labelling Problems
- 4. Hidden Markov Model (HMM)
- 5. HMM: Observation Likelihood
- 6. HMM: Most Likely State Sequence
- 7. HMM: Supervised Learning
- 8. Evaluation


![image 2](<Week 3 - Sequence Labelling-CL_images/imageFile2.png>)

###### • DionysiusThrax wrote (c. 100BCE) about eight parts-of-speech as a way of classifying words based on their functions:

nouns verbs articles adverbs preposition

conjunction pronoun participle

###### • Thrax’s list and minor variations of it dominated European language grammars and dictionaries for 2000 years:

nouns verbs adjectives adverbs preposition conjunction pronoun interjection

- • Open class words (or content words)
- • nouns, main verbs, adjectives, adverbs, numbers, …
- • Mostly content-bearing: they refer to objects, actions and properties in the world
- • There is no limit to what these words are, new ones are added all the time
- • Closed class words (or function words)
- • pronouns, determiners, prepositions, connectives, modal verbs, interjections, …
- • There are a limited number of these


![image 3](<Week 3 - Sequence Labelling-CL_images/imageFile3.png>)

Open class ("content") words

![image 4](<Week 3 - Sequence Labelling-CL_images/imageFile4.png>)

|Nouns<br><br>|Proper<br><br>Janet Italy|
|---|
<br><br>|Common<br><br>cat, cats mango|
|---|
|
|---|


|Adjectives old green tasty|
|---|


Verbs

|Main<br><br>eat went|
|---|


|Adverbs slowly yesterday|
|---|


|Interjections Ow hello|
|---|


###### Numbers

… more

122,312 one

![image 5](<Week 3 - Sequence Labelling-CL_images/imageFile5.png>)

Closed class ("function")

|Auxiliary<br><br>can<br><br>had|
|---|


|Determiners the some|
|---|


|Prepositions to with|
|---|


|Conjunctions and or|
|---|


|Particles off up|
|---|


… more

|Pronouns they its|
|---|


#### Overview

- 1. Word categories
- 2. Part-of-Speech (POS) Tagging
- 3. Other Sequence Labelling Problems
- 4. Hidden Markov Model (HMM)
- 5. HMM: Observation Likelihood
- 6. HMM: Most Likely State Sequence
- 7. HMM: Supervised Learning
- 8. Evaluation


###### English POS Tags – Different Conventions

![image 6](<Week 3 - Sequence Labelling-CL_images/imageFile6.png>)

- • Brown corpus used a set of 87 POS tags.
- • The British National has 61 tags.
- • Most common in NLP today is the PennTreebank


Check this for Penn Treebank POS tags: https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html

#### English POS Tags – Penn Treebank

- • Adjective (modify nouns)

- • Basic (JJ): red, tall
- • Comparative (JJR): redder, taller
- • Superlative (JJS): reddest, tallest


- • Adverb (modify verbs)

- • Basic (RB): quickly
- • Comparative (RBR): quicker
- • Superlative (RBS): quickest


- • Preposition (IN): on, in, by, to, with
- • Determiner:

- • Basic (DT) a, an, the
- • WH-determiner (WDT): which, that


- • Coordinating Conjunction (CC): and, but, or
- • Particle (RP): off (took off), up (put up)


###### • Noun (person, place or thing)

- • Singular (NN): dog, fork
- • Plural (NNS): dogs, forks
- • Proper (NNP, NNPS): John, Springfields
- • Personal pronoun (PRP): I, you, he, she, it
- • Wh-pronoun (WP): who, what


###### • Verb (actions and processes)

- • Base, infinitive (VB): eat
- • Past tense (VBD): ate
- • Gerund (VBG): eating
- • Past participle (VBN): eaten
- • Non 3rd person singular present tense (VBP): eat
- • 3rd person singular present tense: (VBZ): eats
- • Modal (MD): should, can
- • To (TO): to (to eat)


#### Part-of-Speech Tagging

NNP VBD DT NN CC VBD TO VB PRP IN DT NN

POS TAGGER

John saw the saw and decided to take it to the table

- • Annotate each word in a sentence with a POS
- • Lowest level of syntactic analysis (i.e., used to be done to produce parse trees)


#### Ambiguity in POS Tagging

Words often have more than one POS – “back”:

- • The back door = JJ (Adjective)

- • On my back = NN (Noun, Singular or Mass, Uncountable)

- • Win the voters back = RB (Adverb)

- • Promised to back the bill = VB (Verb Base form)


#### Ambiguity in POS Tagging - Continued

- • Based on Brown corpus: 11.5% of word types and 40% of word tokens are ambiguous.
- • Baseline is already 90%

• Baseline is performance of the simplest possible method: Tag each word with its most frequent tag, and tag unknown words as nouns

- • Partly because many words are not ambiguous
- • Current state-of-the-art is about 98% (checkout the leaderboard)


- • Text-to-speech (how to pronounce “lead”, i.e. is it a verb or a noun?)
- • If we POS tagged a collection of text we could do some basic IR by writing regex. E.g., to extract all noun phrases/compounds:

- • The car
- • A white horse
- • The red big box
- • A round red big cup
- • …


- • As input to syntactic parsers
- • If you know the tags, you can back off from words to their POS tag categories (i.e., another way of smoothing in language modelling)


Question: Can you write a regex to catch all potential noun phrases in a corpus?

- • Sentiment Analysis: "The movie was incredibly amazing."
- • POS Tags:

- • incredibly → RB (Adverb)
- • amazing → JJ (Adjective) → Strong positive sentiment


- • By focusing on adjectives and adverbs, sentiment analysis models can weigh sentiment more accurately.


###### Named Entity Recognition:

###### Sentence Detected Named Entities

"Elon Musk founded Tesla in 2003." Elon Musk (PERSON), Tesla (ORG), 2003 (DATE) "Google's headquarters is in Mountain View, California."

Google (ORG), Mountain View (GPE), California (GPE)

"The iPhone 15 was released in September 2023." iPhone 15 (PRODUCT), September 2023 (DATE) "Microsoft acquired LinkedIn for $26 billion." Microsoft (ORG), LinkedIn (ORG), $26 billion (MONEY) "The Eiffel Tower is one of the most visited landmarks in Paris."

Eiffel Tower (FAC), Paris (GPE)

#### POS Tagging Approaches

- • Rule-Based: Human crafted rules based on lexical and other linguistic knowledge. Expensive!
- • Learning-Based:Trained on human annotated corpora like the PennTreebank.
- • Statistical models: Hidden Markov Model (HMM), Conditional Random Field (CRF), …
- • Neural networks: Recurrent networks like Long ShortTerm Memory (LSTMs)


![image 7](<Week 3 - Sequence Labelling-CL_images/imageFile7.png>)

![image 8](<Week 3 - Sequence Labelling-CL_images/imageFile8.png>)

# →

Brill, Eric. "A simple rule-based part of speech tagger." Speech and Natural Language: Proceedings of a Workshop Held at Harriman, New York, February 23-26, 1992. 1992. Brinton, Laurel J. The structure of modern English: A linguistic introduction. Vol. 1. John Benjamins Publishing, 2000.

#### Side Note: Classification

- • Typical machine learning addresses the problem of classifying a feature-vector description into a fixed number of classes. There are many standard learning methods for this task:

- • Decision Trees
- • Naïve Bayes
- • Logistic Regression / Maximum Entropy (MaxEnt)
- • Perceptron and Neural Networks
- • Support Vector Machines (SVMs)


- • Naïve Solution: Treat POS tagging as predicting a POS label for words independently. Question: what could go wrong? (recall our example for the word “back”)


#### But …

- • Standard classification problem assumes individual cases are disconnected and independent (i.i.d. - independently and identically distributed).
- • Many NLP problems do not satisfy this assumption and involve making many connected decisions which are mutually dependent.
- • More sophisticated learning and inference techniques are needed to handle such situations in general.


#### Overview

- 1. Word categories
- 2. Part-of-Speech (POS) Tagging
- 3. Other Sequence Labelling Problems
- 4. Hidden Markov Model (HMM)
- 5. HMM: Observation Likelihood
- 6. HMM: Most Likely State Sequence
- 7. HMM: Supervised Learning
- 8. Evaluation


#### Sequence Labeling Problem

- • Many NLP problems can be viewed as sequence labeling.
- • Each token in a sequence is assigned a label.
- • Labels of tokens are dependent on the labels of other tokens in the sequence, particularly their neighbors (not i.i.d).


#### Example: Information Extraction

- • Identify phrases in language that refer to specific types of entities and relations in text.
- • Named Entity Recognition (NER) is the task of identifying names of people, places, organizations, …, in text.

people organizations places

• Michael Dell is the CEO of Dell Computer Corporation and lives in Austin Texas.

- • Extract pieces of information relevant to a specific application, e.g. used car ads: year make model mileage price


• For sale, 2002 Toyota Prius, 20,000 mi, $15K or best offer.

#### Example: Semantic Role Labeling

• For each clause, determines the semantic role played by each noun

phrase that is an argument to the verb.

agent patient source destination instrument

John drove Mary from Austin to Dallas in his Toyota Prius.

instrument patient

The hammer broke the window.

#### Probabilistic Sequence Models

- • Probabilistic sequence models allow integrating uncertainty over multiple interdependent classifications and collectively determining the most likely global assignment.
- • Two standard models
- • Hidden Markov Model (HMM)
- • Conditional Random Field (CRF)


#### Overview

- 1. Word categories
- 2. Part-of-Speech (POS) Tagging
- 3. Other Sequence Labelling Problems
- 4. Hidden Markov Model (HMM)
- 5. HMM: Observation Likelihood
- 6. HMM: Most Likely State Sequence
- 7. HMM: Supervised Learning
- 8. Evaluation


#### Markov Model / Markov Chain

- • Makes Markov assumption that next state only depends on the current state and independent of previous history. We used this in n-gram language modelling!
- • Markov Chain:


𝑋1 𝑋2 𝑋3 𝑋4 …

- • It is probabilistic: each connection (i.e., transition) is assigned a probability , the sum of the edges exiting each node is 1.
- • This is a complete directed graph, and missing edges here indicate 0 probability.


0.05

final

Verb

state

0.25

0.1

Prop Noun

0.8 0.1

0.4

0.5

0.25

start state 0.1

- • It is probabilistic: each connection (i.e., transition) is assigned a probability , the sum of the edges exiting each node is 1.
- • This is a complete directed graph, and missing edges here indicate 0 probability.


0.05

final

Verb

state

0.25

0.1

Prop Noun

0.8 0.1

0.4

0.5

0.25

start state 0.1

Given a sequence, simply multiply the values of the corresponding edges to compute its probability, by applying chain rule!

P(PropNoun Verb Det Noun) = P(PropNoun | start) * P(Verb | PropNoun)

P(Det |Verb) * P(Noun | Det) * P(Noun | stop) = 0.4*0.8*0.25*0.95*0.1

- • It is probabilistic: each connection (i.e., transition) is assigned a probability , the sum of the edges exiting each node is 1.
- • This is a complete directed graph, and missing edges here indicate 0 probability.


0.05

final

Verb

state

0.25

0.1

Prop Noun

0.8 0.1

0.4

0.5

0.25

start state 0.1

Given a sequence, simply multiply the values of the corresponding edges to compute its probability, by applying chain rule!

P(Det Noun) = 0.5*0.95*0.1

- • Probabilistic generative model for sequences.
- • Assumes an underlying set of hidden (unobserved, latent) states in which the model can be (e.g., parts of speech).
- • Assumes probabilistic transitions between states over time (e.g., transition from one POS to another POS as sequence is generated).
- • Assumes a probabilistic generation of tokens from states (e.g. words generated for each POS).


###### 𝑋1 𝑋2 𝑋3 𝑋4 …

𝐸1 𝐸2 𝐸3 𝐸4

A Markov chain is useful when we need to compute a probability for a

sequence of observable events. In many cases, however, the events we

are interested in are hidden: we don’t observe them directly. For example we don’t normally observe part-of-speech tags in a text. Rather, we see words, and must infer the tags from the word sequence. We call

the tags hidden because they are not observed.

𝑋1 𝑋2 𝑋3 𝑋4 …

𝐸1 𝐸2 𝐸3 𝐸4

#### Sample HMM for POS

0.1

the

cat dog

a the the

bed apple Det

a

car pen

a the

that

0.5

0.95

0.9

Noun

bit

stop

ate saw

0.05

played hit

gave

Tom

0.25

0.1

JohnMary Alice

Verb

0.8

Jerry

0.4

0.1

PropNoun

0.5

0.25

0.1

start

apple Det

pen

that

0.5

0.95

0.9

Noun

bit

stop

ate saw

0.05

played hit

gave

Tom

0.25

0.1

JohnMary Alice

Verb

0.8

Jerry

0.4

0.1

PropNoun

0.5

0.25

0.1

start

apple Det

pen

that

0.5

0.95

0.9

Noun

bit

stop

ate saw

0.05

played hit

gave

Tom

0.25

0.1

JohnMary Alice

Verb

0.8

Jerry

0.4

0.1

PropNoun

0.5

0.1

start

apple Det

pen

that

0.5

0.95

0.9

Noun

bit ate saw

stop

0.05

played hit

gave

Tom

0.25

0.1

JohnMary

Verb

Alice

0.8

Jerry

0.4

0.1

PropNoun

0.5

0.25

0.1

start John

apple Det

pen

that

0.5

0.95

0.9

Noun

bit ate saw

stop

0.05

played hit

gave

Tom

0.25

0.1

JohnMary

Verb

Alice

0.8

Jerry

0.4

0.1

PropNoun

0.5

0.25

0.1

start John

apple Det

pen

that

0.5

0.95

0.9

Noun

bit ate saw

stop

0.05

played hit

gave

Tom

0.25

0.1

JohnMary

Verb

Alice

0.8

Jerry

0.4

0.1

PropNoun

0.5

0.25

0.1

start John bit

apple Det

pen

that

0.5

0.95

0.9

Noun

bit ate saw

stop

0.05

played hit

gave

Tom

0.25

0.1

JohnMary

Verb

Alice

0.8

Jerry

0.4

0.1

PropNoun

0.5

0.25

0.1

start John bit

apple Det

pen

that

0.5

0.95

0.9

Noun

bit ate saw

stop

0.05

played hit

gave

Tom

0.25

0.1

JohnMary

Verb

Alice

0.8

Jerry

0.4

0.1

PropNoun

0.5

0.25

0.1

start John bit the

apple Det

pen

that

0.5

0.95

0.9

Noun

bit ate saw

stop

0.05

played hit

gave

Tom

0.25

0.1

JohnMary

Verb

Alice

0.8

Jerry

0.4

0.1

PropNoun

0.5

0.25

0.1

start John bit the

apple Det

pen

that

0.5

0.95

0.9

Noun

bit ate saw

stop

0.05

played hit

gave

Tom

0.25

0.1

JohnMary

Verb

Alice

0.8

Jerry

0.4

0.1

PropNoun

0.5

0.25

0.1

start John bit the apple

apple Det

pen

that

0.5

0.95

0.9

Noun

bit ate saw

stop

0.05

played hit

gave

Tom

0.25

0.1

JohnMary

Verb

Alice

0.8

Jerry

0.4

0.1

PropNoun

0.5

0.25

0.1

start John bit the apple

#### Formal Definition of HMM (for POS Tagging)

|• A set of N + 2 states S={s0,s1,s2, … sN, sF}, where N is the number of POS tags<br>• A set of M possible observations V={v1,v2…vM}, where M is the size of the vocabulary<br>• A state transition (i.e., edge) probability distribution A={aij},<br>• Observation probability distribution (i.e., probability of a word given a POS tag) for each state 𝐵 = {𝑏𝑗(𝑘)},<br>• We denote the total parameter set λ={A,B}<br><br><br>aij = P(qt+1 = sj | qt = si ) 1 i , j  N and i = 0, j = F<br><br>bj(k) = P (vk at t | qt = sj ) 1 j  N 1 k  M|
|---|


𝑋1 𝐸1

#### A first-order HMM

With a (commonly made) first-order Markov chain, the probability of a particular

state depends only on the previous state:

|𝑃 𝑞𝑡 = 𝑠𝑗 𝑞1𝑞2 …𝑞𝑡−1 = 𝑃 𝑞𝑡 = 𝑠𝑗 𝑞𝑡−1<br><br>|
|---|


|The probability of an output observation 𝑜𝑡 depends only on the state that produced<br><br>the observation 𝑞𝑡 and not on any other states or any other observations:|
|---|


|𝑃 𝑜𝑡 𝑞1𝑞2 …,𝑜1,𝑜2 … = 𝑃 𝑜𝑡 𝑞𝑡<br><br>|
|---|


#### Three Useful HMM Tasks

- • Observation Likelihood: To classify and order sequences.
- • Most likely state sequence (Decoding): To tag each token in a sequence with a label.
- • Maximum likelihood training (Learning): To train models to fit empirical training data.


![image 9](<Week 3 - Sequence Labelling-CL_images/imageFile9.png>)

#### Overview

- 1. Word categories
- 2. Part-of-Speech (POS) Tagging
- 3. Other Sequence Labelling Problems
- 4. Hidden Markov Model (HMM)
- 5. HMM : Observation Likelihood
- 6. HMM: Most Likely State Sequence
- 7. HMM: Supervised Learning
- 8. Evaluation


#### HMM: Observation Likelihood

- • Given a sequence of observations, O, and a model with a set of parameters, λ (i.e., probability matrices of HMM), what is the probability that this observation was generated by this model: P(O| λ)=?
- • Use HMM like a language model
- • Useful for two tasks
- • Sequence classification
- • Most likely sequence


#### Sequence Classification

- • Assume an HMM is available for each category (i.e. language).
- • What is the most likely category for a given observation sequence, i.e. which category’s HMM is most likely to have generated it?
- • Used in speech recognition to find most likely word model to have generate a given sound or phoneme sequence.


###### O

ah s t e n

###### ? ?

P(O | Austin) > P(O | Boston) ?

Austin Boston

#### Most Likely Sequence

- • Of two or more possible sequences, which one was most likely generated by a given model?
- • Used to score alternative word sequence interpretations in speech


recognition.

- O1
- O2


?

dice precedent core

?

vice president Gore

Ordinary English

P(O2 | OrdEnglish) > P(O1 | OrdEnglish) ?

### Observation Likelihood - Naïve Solution

- • In the naïve solution, you calculate the probability of all possible sequence of tags for the given observation and sum them up.
- • Let’s suppose that we have N possible tag classes and a sentence of length T.
- • How many possible tag sequences are there? Let’s take N=17 and T=1,2,4,8. The answer is a lot!
- • The explosion in the search space!


Possible Sequence of

POS tags (i.e., 17T)

Sentence length (T)

![image 10](<Week 3 - Sequence Labelling-CL_images/imageFile10.png>)

### Observation Likelihood - Efficient Solution

• Intuition: the best path of length t ending in a particular tag must

include the best path of length t-1 ending in the previous tag. This is due to the Markov assumption.

• Forward Algorithm: Uses dynamic programming to exploit this fact

to efficiently compute observation likelihood.

• Compute a forward trellis that compactly and implicitly encodes information about all possible state paths.

#### Forward Trellis

- • • •
- • • •
- • • •
- • • •


- s1

- s2


•

•

•

•

•

s0 sF

•

•

• •

• •

•

•

•

•

sN

t1 t2 t3 tT-1 tT

• Continue forward in time until reaching final time point and sum the

forward probabilities of ending in final state.

#### Forward Probabilities

• Let t(j) be the probability of being in state j after seeing the first t observations (by summing over all initial paths leading to j).

t( j) = P(o1,o2,...ot , qt = sj |)

|Think of 𝑜𝑡 as the t-th word (i.e., “the”) of the sentence you are tagging and think of 𝑞𝑡 = 𝑠𝑗 as assigning a POS tag 𝑠𝑗 (i.e., “DT”) to “the”.|
|---|


S = {start, Det, Noun, PropNoun, Verb, stop} O = John bit the apple

Det Noun

Verb

|𝛼2(3) = 𝑃(𝐽𝑜ℎ𝑛,𝑏𝑖𝑡 , 𝑞2 = 𝑃𝑟𝑜𝑝𝑁𝑜𝑢𝑛|𝜆)|
|---|


PropNoun

#### Forward Step

|• Consider all possible ways of getting to 𝑠𝑗 at time 𝑡 by coming from all<br><br>possible states 𝑠𝑖 and determine<br><br>probability of each.<br><br>• Sum these to get the total probability<br><br>of being in state 𝑠𝑗 at time t while<br><br>accounting for the first 𝑡 − 1 observations.<br><br>• Then multiply by the probability of actually observing 𝑜𝑡 in 𝑠𝑗.<br>|
|---|


- s1

- s2


- a1j
- a2j


a2j

• • •

sj

aNj

sN

t-1(i) t(i)

Computing the Forward Probabilities

- • Initialization
- • Recursion
- • Termination


###### 1( j) = a0jbj(o1) 1 j  N





N

= 

######   1

t t ij     

( ) − ( ) ( ) 1 , 1

j i a bj ot j N t T

 

=

i

1

N



( |)  1( )  ( )

= + =

###### P O T sF T i aiF

=

i

1

|𝑏1(o1 = John)|
|---|


s1= DET

- 𝑎01

- 𝑎02

- 𝑎03

- 𝑎04


###### • Initialization

|𝑏2(o1 = John)|
|---|


###### 1( j) = a0jbj(o1) 1 j  N s

2 = Noun

###### s0

s2 = PropNoun

|𝑏3(o1 = John)|
|---|


0.1

s4 = Verb

|𝑏4(o1 = John)|
|---|


t1

0.95

0.5

0.9

Det Noun

###### John bit the apple

stop

0.05

| |John|bit|the|apple|
|---|---|---|---|---|
|DET|0.01|0.04|0.95|0|
|Noun|0.2|0.05|0.05|0.7|
|PropNoun|0.75|0.05|0|0.2|
|Verb|0|0.9|0.05|0.05|


0.25

0.1

Verb

0.8

0.4

0.1

PropNoun

0.5

0.25

0.1

start

|1 1 = 0.5 × 0.01<br><br>= 0.005|
|---|


s1= DET

𝑎01

###### • Initialization

|1(2) =|
|---|


𝑎02 𝑎03 𝑎04

###### 1( j) = a0jbj(o1) 1 j  N s

2 = Noun

###### s0

|1(3) =|
|---|


s2 = PropNoun

0.1

|1(4) =|
|---|


s4 = Verb

t1

0.95

0.5

0.9

Det Noun

###### John bit the apple

stop

0.05

| |John|bit|the|apple|
|---|---|---|---|---|
|DET|0.01|0.04|0.95|0|
|Noun|0.2|0.05|0.05|0.7|
|PropNoun|0.75|0.05|0|0.2|
|Verb|0|0.9|0.05|0.05|


0.25

0.1

Verb

0.8

0.4

0.1

PropNoun

0.5

0.25

0.1

start

|1 1 = 0.005<br><br>|
|---|


• Recursion

- s1 o2 = bit

- s2

|s<br><br>1 4<br><br>|
|---|


4

- s3 s3






N

𝑎13 𝑎23

= 

|1 2<br><br>|
|---|


  1

t t ij     

###### ( ) − ( ) ( ) 1 , 1

j i a bj ot j N t T

 

𝑎33

=

i

1

|1 3<br><br>|
|---|


|𝑎43|
|---|


𝑏3(o2 = bit)

0.1

2(3)

0.95

0.5

0.9

Det Noun

###### John bit the apple

stop

| |John|bit|the|apple|
|---|---|---|---|---|
|DET|0.01|0.04|0.95|0|
|Noun|0.2|0.05|0.05|0.7|
|PropNoun|0.75|0.05|0|0.2|
|Verb|0|0.9|0.05|0.05|


0.05

0.25

0.1

Verb

0.8

0.4

0.1

PropNoun

0.5

0.25

0.1

start

s2

- • Initialization
- • Recursion


• • •

sF

###### 1( j) = a0jbj(o1) 1 j  N

sN





N

= 

  1

t t ij     

###### ( ) − ( ) ( ) 1 , 1

j i a bj ot j N t T

 

=

i

1

|𝑇(1)|
|---|


|𝑎1𝐹|
|---|


s2

- • Initialization
- • Recursion


|𝑇(2)|
|---|


|𝑎2𝐹|
|---|


• • •

sF

###### 1( j) = a0jbj(o1) 1 j  N

|𝑎𝑁𝐹|
|---|


sN

|𝑇(𝑁)|
|---|






N

= 

  1

t t ij     

###### ( ) − ( ) ( ) 1 , 1

j i a bj ot j N t T

 

=

i

1

![image 11](<Week 3 - Sequence Labelling-CL_images/imageFile11.png>)

###### Forward Computational Complexity

- • Requires only O(TN2) time to compute the probability of an observed sequence given a model (compare this with our naïve solution O(TNT)).
- • Exploits the fact that all state sequences must merge into one of the N


possible states at any point in time and the Markov assumption that

only the last state effects the next one.

#### Overview

- 1. Word categories
- 2. Part-of-Speech (POS) Tagging
- 3. Other Sequence Labelling Problems
- 4. Hidden Markov Model (HMM)
- 5. HMM: Observation Likelihood
- 6. HMM: Most Likely State Sequence
- 7. HMM: Supervised Learning
- 8. Evaluation


### Most Likely State Sequence

- • Given an observation sequence, O, and a model, λ, what is the most

likely state sequence, Q=q1,q2,…qT, that generated this sequence from

this model?

- • Used for sequence labeling, assuming each state corresponds to a tag, it determines the globally best assignment of tags to all tokens in a sequence.
- • Standard procedure is called the Viterbi algorithm (Viterbi, 1967) and also has O(TN2) time complexity.


#### Viterbi Scores

• Recursively compute the probability of the most likely subsequence of

states that accounts for the first t observations and ends in state sj.

###### = − =

###### t t t j 

###### vt j P q q q o o q s

###### ( ) max ( 0, 1,..., 1 , 1,..., , | )

q q q

0, 1,..., 1

−

t

• Also record “backpointers” that subsequently allow backtracking the most probable state sequence.

• btt(j) stores the state at time t-1 that maximizes the probability that system was in state sj at time t (given the observed sequence).

|![image 12](<Week 3 - Sequence Labelling-CL_images/imageFile12.png>)|
|---|


### Computing the Viterbi Scores

- • Initialization
- • Recursion
- • Termination


###### v1( j) = a0jbj(o1) 1 j  N

N

###### t = −    

v j vt i aijbj ot j N t T

###### ( ) max 1( ) ( ) 1 , 1

=

i

1

N

= + =

P* vT (sF ) max v (i)a

1

T iF

=

i

1

Almost identical to the Forward algorithm except we take max instead of sum

### Computing the Viterbi Backpointers

- • Initialization
- • Recursion
- • Termination


bt1( j) = s0 1 j  N

N

###### t = −    

bt j vt i aijbj ot j N t T

###### ( ) argmax 1( ) ( ) 1 , 1

=

i

1

N

= + =

qT* btT (sF ) argmax v (i)a

1

T iF

=

i

1

Final state in the most probable state sequence. Follow backpointers to initial state to construct full sequence.

#### Viterbi Backpointers

- • • •
- • • •
- • • •
- • • •


- s1

- s2


• • •

• • •

• •

•

• • •

s0 sF

•

•

•

sN

t1 t2 t3 tT-1 tT

#### Viterbi Backtrace

![image 13](<Week 3 - Sequence Labelling-CL_images/imageFile13.png>)

- • • • • • •
- • • •
- • • •


###### s1 s2

• • •

• • •

• •

•

• • •

s0 sF

•

•

•

sN

t1 t2 t3 tT-1 tT

###### Most likely Sequence: s0 sN s1 s2 …s2 sF

#### Overview

- 1. Word categories
- 2. Part-of-Speech (POS) Tagging
- 3. Other Sequence Labelling Problems
- 4. Hidden Markov Model (HMM)
- 5. HMM: Observation Likelihood
- 6. HMM: Most Likely State Sequence
- 7. HMM: Supervised Learning
- 8. Evaluation


#### HMM Learning

- • Supervised Learning: All training sequences are completely labeled (tagged). We only cover this.
- • Unsupervised Learning: All training sequences are unlabeled (but generally know the number of tags/states).
- • Semi-supervised Learning: Some training sequences are labeled, most are unlabeled.


• We can use a method called Expectation Maximization (EM) for both unsupervised and semi-supervised learning of HMMs. EM is an iterative method for learning probabilistic categorization model from unsupervised data.

### Supervised Parameter Estimation

- • If training sequences are labeled (tagged) with the underlying state/POS sequences, then the parameters, λ={A,B}, can all be estimated directly.
- • Estimate state transition probabilities based on tag bigram and unigram statistics


in the labeled data.

Training Sequences

|John ate the apple<br><br>A dog bit Mary<br><br>Mary hit the dog John gave Mary the cat.<br><br>.<br><br>.<br><br>.|
|---|


|Supervised HMM Training|
|---|


Det Noun PropNoun Verb

### Supervised Parameter Estimation - continued

• Use a corpus of labeled sequence data to easily construct an HMM using supervised

training.

• Given a novel unlabeled test sequence to tag, use the Viterbi algorithm to predict

the most likely (globally optimal) tag sequence.

C q s s

( ,qt 1 )

t i j

- a

=

= =

= +

( )

( , ) ( )

i j

i j i k

j C q s

C q s o v

- b k


ij C q s

( )

t i

• Estimate the observation probabilities based on tag/word co-occurrence statistics in the labeled data.

= =

=

=

Use appropriate smoothing if training data is sparse.

#### Overview

- 1. Word categories
- 2. Part-of-Speech (POS) Tagging
- 3. Other Sequence Labelling Problems
- 4. Hidden Markov Model (HMM)
- 5. HMM: Observation Likelihood
- 6. HMM: Most Likely State Sequence
- 7. HMM: Supervised Learning
- 8. Evaluation


### Evaluating POS Tagger performance

- • The metric most often reported for POS tagging is accuracy: The proportion of words in the test corpus that were tagged correctly by the POS tagger:
- • Given that many words in the testing corpus have been seen during training, it makes


![image 14](<Week 3 - Sequence Labelling-CL_images/imageFile14.png>)

sense to also report accuracy specifically for out of vocabulary words.

• The state-of-the-art accuracy for all words in English is almost 98%.

##### Feedback time!

![image 15](<Week 3 - Sequence Labelling-CL_images/imageFile15.png>)

![image 16](<Week 3 - Sequence Labelling-CL_images/imageFile16.png>)

![image 17](<Week 3 - Sequence Labelling-CL_images/imageFile17.png>)

** Please submit weekly Feedback! **

![image 18](<Week 3 - Sequence Labelling-CL_images/imageFile18.png>)

![image 19](<Week 3 - Sequence Labelling-CL_images/imageFile19.png>)

