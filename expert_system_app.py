import streamlit as st
import operator
import json

# --- CUSTOM EXCEPTION FOR INTERACTIVE CHAINING ---
class NeedInputException(Exception):
    def __init__(self, var_name, question_text):
        self.var_name = var_name
        self.question_text = question_text

# --- 0. KnowledgeManager ---
class KnowledgeManager:
    @staticmethod
    def load_from_json(engine, file_path_or_buffer):
        try:
            if isinstance(file_path_or_buffer, str):
                with open(file_path_or_buffer, 'r') as f:
                    data = json.load(f)
            else:
                data = json.load(file_path_or_buffer)
        except Exception as e:
            st.error(f"Error loading knowledge base: {e}")
            return

        for fact_name, text in data.get("questions", {}).items():
            engine.add_question(fact_name, text)

        for f_data in data.get("facts", []):
            try:
                engine.initialize_fact(f_data["name"], Fact(
                    f_data["name"], f_data["value"], f_data["cf"], f_data["explanation"]
                ))
            except:
                engine.initialize_fact(f_data["name"], Fact(
                    f_data["name"], f_data["value"], 1.0, f_data["explanation"]
                )) 

        for r_data in data.get("rules", []):
            conditions = [Condition(c["fact1"], c["op"], c["fact2"]) for c in r_data["conditions"]]
            try:
                engine.add_rule(Rule(
                    r_data["id"], conditions, tuple(r_data["conclusion"]), r_data["cf"], r_data["explanation"]
                ))
            except:
                engine.add_rule(Rule(
                    r_data["id"], conditions, tuple(r_data["conclusion"]), 1.0, r_data["explanation"]
                ))

# --- 1. THE INFERENCE ENGINE ---
OPERATORS = {">": operator.gt, "<": operator.lt, ">=": operator.ge, "<=": operator.le, "==": operator.eq, "!=": operator.ne}

class Condition:
    def __init__(self, fact1, op, fact2):
        self.fact1, self.op, self.fact2 = fact1, op, fact2

    def evaluate(self, fact1_value, fact2_value):
        try:
            return OPERATORS[self.op](float(fact1_value), float(fact2_value))
        except (ValueError, TypeError):
            return OPERATORS[self.op](str(fact1_value), str(fact2_value))

class Fact:
    def __init__(self, name, value, cf=1.0, explanation="Given"):
        self.name, self.value, self.cf, self.explanation = name, value, cf, explanation

class Rule:
    def __init__(self, id, conditions, conclusion, rule_cf, explanation):
        self.id, self.conditions, self.conclusion, self.rule_cf, self.explanation = id, conditions, conclusion, rule_cf, explanation

class ExpertSystem:
    def __init__(self, reasoning='deductive'):
        self.reasoning = reasoning
        self.rules, self.facts, self.questions, self.logs = [], {}, {}, []

    def log(self, message): self.logs.append(message)

    def add_rule(self, rule): self.rules.append(rule)

    def initialize_fact(self, name, fact): self.facts[name] = fact

    def add_fact(self, name, value, cf=1.0, explanation="User Input"):
        if name in self.facts:
            old_cf = self.facts[name].cf
            self.facts[name].cf = old_cf + cf * (1 - old_cf)
            if cf > old_cf: self.facts[name].value = value
        else:
            self.facts[name] = Fact(name, value, cf, explanation)

    def add_question(self, fact_name, text): self.questions[fact_name] = text

    def get_explanation(self, fact_name):
        if fact_name not in self.facts: return f"Goal '{fact_name}' could not be proven."
        f = self.facts[fact_name]
        return f"**Conclusion:** {f.name} is **{f.value}** \n**Confidence:** {f.cf:.2%}  \n**Reasoning:** {f.explanation}"

    def backward_chain(self, goal_name):
        #self.log(f"Attempting to prove: {goal_name}")
        return self._prove(goal_name)
        
    def _prove(self, goal_name):
            if goal_name in self.facts: return self.facts[goal_name].cf
            self.log(f"............Trying to prove: {goal_name}")

            rule_cfs = []
            for rule in self.rules:
                if rule.conclusion[0] == goal_name:
                    rule_satisfied = True
                    cond_cfs = [] 
                    for cond in rule.conditions:
                        res_cf = [1.0] 
                        
                        if cond.fact1.startswith('$') and cond.fact2.startswith('$'):
                            res_cf.append(self._prove(cond.fact1.removeprefix('$')))
                            fact1 = self.facts.get(cond.fact1.removeprefix('$'))
                            res_cf.append(self._prove(cond.fact2.removeprefix('$')))
                            fact2 = self.facts.get(cond.fact2.removeprefix('$')) 
                        elif cond.fact1.startswith('$') and not cond.fact2.startswith('$'):
                            res_cf.append(self._prove(cond.fact1.removeprefix('$')))
                            fact1 = self.facts.get(cond.fact1.removeprefix('$'))
                            res_cf.append(1.0)
                            self.add_fact(cond.fact2, cond.fact2, 1.0, 'Implied KB fact')
                            try:
                                self.log(f"Added implied fact from KB: {fact2.name}")
                            except:
                                pass
                            fact2 = self.facts.get(cond.fact2)
                        elif not cond.fact1.startswith('$') and cond.fact2.startswith('$'):
                            res_cf.append(1.0)
                            self.add_fact(cond.fact1, cond.fact1, 1.0, 'Implied KB fact')
                            try:
                                self.log(f"Added implied fact from KB: {fact1.name}")
                            except:
                                pass
                            fact1 = self.facts.get(cond.fact1)
                            res_cf.append(self._prove(cond.fact2.removeprefix('$')))
                            fact2 = self.facts.get(cond.fact2.removeprefix('$')) 
                        else:
                            print("ERROR: Invalid rule definition")

                        # FIX: Check if any part of the proof is still waiting for input (-1.0)
                        if -1.0 in res_cf:
                            return -1.0
                        
                        if min(res_cf) > 0 and fact1 and fact2 and cond.evaluate(fact1.value, fact2.value):
                            cond_cfs.append(min(res_cf)) 
                        else:
                            rule_satisfied = False; break                  
                    
                    if rule_satisfied:
                        min_cond_cfs = min(cond_cfs) 
                        new_cf = rule.rule_cf * min_cond_cfs 
                        rule_cfs.append(new_cf)
                        self.add_fact(rule.conclusion[0], rule.conclusion[1], new_cf, rule.explanation)
                        self.log(f"Rule: '{rule.id}' has fired --> {rule.conclusion[0]} is {rule.conclusion[1]}")

            if rule_cfs:
                res = rule_cfs[0]
                for c in rule_cfs[1:]: res = res + c * (1 - res)
                return res

            #################################
            # If no rule exists, trigger the UI Question/Slider
            if goal_name in self.questions:
                q_key = f"input_{goal_name}"
                cf_key = f"cf_{goal_name}"
                
                if q_key in st.session_state and st.session_state[q_key] != "":
                    val_raw = st.session_state[q_key]
                    if self.reasoning == 'deductive':
                        user_cf = 1.0
                    else:
                        user_cf = st.session_state.get(cf_key, 1.0) 
                    try: val = float(val_raw)
                    except: val = val_raw.lower().strip()
                    
                    self.add_fact(goal_name, val, user_cf, "User input with CF")
                    return user_cf
                else:
                    # Use a container to keep the question UI tidy
                    with st.container():
                        st.info(f"👉 **Required Information:** {self.questions[goal_name]}")
                        if self.reasoning == 'deductive':
                            st.text_input("Enter value and press Enter:", key=q_key)
                        else:
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.text_input("Enter value and press Enter:", key=q_key)
                            with col2:
                                st.slider("Certainty Factor", 0.0, 1.0, 1.0, step=0.1, key=cf_key)
                    return -1.0 
            return 0.0 
            

# --- STREAMLIT DASHBOARD ---
def main():
    st.set_page_config(page_title="Expert System Dashboard", layout="wide")
    st.title("🧠 Expert System Dashboard")

# --- 1. SIDEBAR CONFIGURATION ---
    with st.sidebar:
        st.header("⚙️ Configuration")

        # A. File Uploader
        uploaded_file = st.file_uploader("📂 Load Knowledge Base (JSON)", type="json")
        
        # B. Reasoning Button
        reasoning = st.radio("Reasoning Type", ('deductive', 'probabilistic'), index=None) # Optional: starts with no selection
        if 'reasoning' not in st.session_state or st.session_state.reasoning != reasoning:
            st.session_state.reasoning = reasoning
            if 'engine' in st.session_state:
                del st.session_state['engine']  # Reset engine to reload with new reasoning
                st.session_state.kb_loaded = False


        # B. Reset Button
        if st.button("🔄 Restart/Clear Session", type="primary"):
            # Completely clear session state to force a clean slate
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.markdown("---")
        st.info("Strategy: Backward Chaining")

    # --- 2. INITIALIZE ENGINE & DATA LOADING ---
    # We only proceed if a file has been uploaded
    if uploaded_file is not None:
        if 'engine' not in st.session_state:
            st.session_state.engine = ExpertSystem(st.session_state.reasoning)
            # Load the uploaded file into the engine
            KnowledgeManager.load_from_json(st.session_state.engine, uploaded_file)
            st.session_state.kb_loaded = True
            st.success("Knowledge Base Loaded Successfully!")
        
        engine = st.session_state.engine
    else:
        # This stops the dashboard from loading the rest of the script
        st.header("Welcome to the Expert System")
        st.warning("👈 Please upload a Knowledge Base JSON file in the sidebar to begin the session.")
        st.stop()

    # 3. HANDLE GOAL SELECTION FOR BACKWARD CHAINING
    target_goal = None
    with st.sidebar:
        possible_goals = sorted(list(set(r.conclusion[0] for r in engine.rules)))
        if possible_goals:
            target_goal = st.selectbox("Select Goal to Prove", possible_goals)
        else:
            st.warning("No rules found in KB.")

    # 4. MAIN INTERFACE
    if target_goal:
        st.header(f"🕵️ Diagnosing: {target_goal}")
        #confidence = engine.backward_chain(target_goal)
        confidence = st.session_state.engine.backward_chain(target_goal)

# --- 3. EXPLANATION SYSTEM ---
        st.divider()
        st.subheader("🔍 Analysis & Logic Trace")

        if confidence > 0:
            # Main Conclusion Header
            final_fact = st.session_state.engine.facts[target_goal]
            st.success(f"**Final Conclusion:** {target_goal} is **{final_fact.value}**")
            
            col_metric, col_info = st.columns([1, 3])
            with col_metric:
                st.metric("Total Certainty", f"{confidence:.2%}")
            with col_info:
                st.write(f"**Reasoning Summary:** {final_fact.explanation}")

            # Detailed Breakdown Tabs
            tab1, tab2, tab3 = st.tabs(["📌 Deduced Facts", "⌨️ User Inputs", "📜 Full Inference Log"])
            
            with tab1:
                st.markdown("#### Facts derived through Rule Evaluation")
                # Filter for facts that were NOT user inputs or built-in
                deduced = [f for f in engine.facts.values() if "User" not in f.explanation and "Initial" not in f.explanation and "Built-in" not in f.explanation]
                if deduced:
                    for f in deduced:
                        with st.container(border=True):
                            st.markdown(f"**Variable:** `{f.name}` → **Value:** `{f.value}`")
                            st.markdown(f"**Confidence:** `{f.cf:.2%}`")
                            st.caption(f"Logic: {f.explanation}")
                else:
                    st.write("No intermediate facts were deduced.")

            with tab2:
                st.markdown("#### Evidence provided by User")
                # Filter for user-provided data
                user_data = [f for f in engine.facts.values() if "User" in f.explanation]
                for f in user_data:
                    st.write(f"✅ **{f.name}**: `{f.value}` (Certainty: {f.cf:.2%})")

            with tab3:
                st.markdown("#### Step-by-Step Rule Execution")
                # Displays the self.logs list from the ExpertSystem engine
                if engine.logs:
                    for log in engine.logs:
                        st.text(f"→ {log}")
                else:
                    st.write("No logs available for this session.")

        elif confidence == 0.0:
            st.warning("⚠️ No diagnosis could be reached. The rules in the knowledge base do not support a conclusion with the current evidence.")
        else:
            st.info("⏳ System is waiting for user input above to continue the proof...")


if __name__ == "__main__":
    main()


