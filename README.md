# expert-system-shell-edu
A prototype implementation of a new expert system (i.e. knowledge-based system) shell for developing and deploying expert systems and their paired knowlege bases.

Author: Ryan J Urbanowicz, PhD
Institution: Cedars Sinai Health Sciences University
Developed for the 'Artificial Intelligence' course for the Health AI PhD program

## Expert System (i.e. Knowledge-Based System) Shell/Engine - Educational DEMO
This repository includes code assembling a **basic but flexible expert system shell, built from the ground up** (i.e. without using existing expert system shells like CLIPS, clipspy, or PyKE), but certainly directly inspired by them. 

This expert system shell is primarily intended for educational purposes. While it is a realtively simple implementation it has been designed with a good deal of flexibility - not found in other Python or Java expert system implementations which are often confusing, not well documented, and or no longer supported/used often. This shell can be used to create a fairly wide varity of expert and knowledge-based system decision making/reasoning tools. Here is a summary of the key features of this shell impelemntation. 
1. Handles both **deductive** (certain) and **inductive** (uncertain/probabilistic) **reasoning**
2. Can perform both **forward** and **backward chaining** (i.e. reasoning)
3. Separates the knowledge base (saved as a json file) from the inference engine and other components (a simple knowlege base editor and a simple explanation system)
4. Uses an easy-to-understand and simple syntax for facts, rules, and questions in the knoweldge-base (however potentially limiting for some applications)
5. Flexibly handles truth comparisons including **(==, >, <, <=, >=,!=)** and fact-states such as True/False, yes/no, etc. 
6. For inductive reasoning - employs certainty factores (0-1 values) - rule firing propagates uncertainty with a product of cfs, while 'and's' of conjuntive rules take the minimum cfs across rule conditions. When multiple rules fire, certainty factors are combined with the Mycin cf update (i.e. new_cf = new_cf + old_cf * (1 - new_cf))
7. The code in the shell below has also been adapted into a 'Streamlit' web dashboard/GUI that can be easily shared and played with. (i.e. **'expert_system_app.py'**)
    * This dashboard is:
        * Limited to **backward chaining**.
        * Allows loading of different knowlege bases as .json files.
        * Requires selection of **deductive** vs. **probailistic** (i.e. inductive) reasoning before loading a knowelege base.
        * Supports selection of certainty factors for inputs using a slider.
        * Allows selection from available goals in knowledge base that can be proved.
        * Provides a breakdown of reasoning, and an explanation of decisions.

## Introduction to the Knowledge Base Syntax
Below we explore simple expert systems designed as accessible examples.
* Each knowlege base is stored within a .json file. 
* The .json knowlege base syntax is that of a dictionary organized by 'questions', 'facts' and 'rules'. Each type of entry has its own required syntax.
    * 'questions' - a dictionary of key:value pairs where the key is the name of a fact needed by the system and the value is the text description of the input needed seen by the user.
    * 'facts' - an array of objects (i.e. a list of dictionaries) where each fact has the keys (name, value, cf, explanation) identifying the fact name, it's assigned value, it's certainty factor, and a description of the fact (used by the explanation system)
    * 'rules' - an array of objects (i.e. a list of dictionaries) where each rule has the keys (id, conditions, conclusion, cf, explanation) 
        * 'Conditions' are list objects that can include one or more conditions (to be satisfied) in order for the rule to 'fire' (i.e. add the conclusion as a new fact in the knowledge base)
        * Each condition has two 'facts' that are compared using any of the following (==, >, <, <=, >=,!=). 
        * These 'facts' can either be variables (starting with '$') (which can also be defined as facts in the KB directly) or static (hard-coded) values within the condition itself, that the system will automatically turn into 'implied facts'. 
        * 'Conclusions' are given as a tuple that first defines the [fact name, fact value] when the rule fires.
        * 'cf' and 'explanation' mean the same as for 'facts'
