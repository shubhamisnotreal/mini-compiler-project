import streamlit as st
import pandas as pd
from processor import MacroProcessor

st.set_page_config(page_title="MiniMacro Processor (Jury-Ready)", layout="wide", page_icon="⚙️")

# --- Presets & Config ---
presets = {
    "Basic Macro": "MACRO\nINCR &X, &Y\nADD &X\nSTORE &Y\nMEND\n\nREAD A\nINCR A, B\nWRITE B",
    "Nested Macro (Macro-in-Macro)": "MACRO\nINNER &A\nADD &A\nMEND\n\nMACRO\nOUTER &X\nREAD &X\nINNER &X\nSTORE &X\nMEND\n\nOUTER NUM\nWRITE NUM",
    "Infinite Recursion Trap": "MACRO\nLOOP_A &X\nLOOP_B &X\nMEND\n\nMACRO\nLOOP_B &Y\nLOOP_A &Y\nMEND\n\nREAD X\nLOOP_A X",
    "Dead Code (Unused)": "MACRO\nUNUSED &A\nADD &A\nMEND\n\nREAD X\nWRITE X"
}

if "source_code" not in st.session_state:
    st.session_state["source_code"] = presets["Basic Macro"]

if "trace_mdt" not in st.session_state:
    st.session_state["trace_mdt"] = None

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Compiler Panel")
    
    st.markdown("### 🗂️ Sample Gallery")
    selected_preset = st.selectbox("Load an architecture preset:", ["None"] + list(presets.keys()))
    if st.button("Load Preset", use_container_width=True):
        if selected_preset != "None":
            st.session_state["source_code"] = presets[selected_preset]
            st.session_state["trace_mdt"] = None
            st.rerun()
            
    st.divider()
    st.markdown("### 📚 Instruction Set")
    st.info("Recognized system pseudo-ops & macros:")
    st.markdown("""
    - `MACRO` / `MEND`
    - `START` / `STOP`
    - `READ`  (Mem -> Reg)
    - `WRITE` (Reg -> Mem)
    - `ADD`   (ALU operation)
    - `SUB`   (ALU operation)
    - `STORE` (Reg -> Mem)
    """)

# --- Main App ---
st.title("Jury-Ready MiniMacro Processor")
st.markdown("A professional compiler front-end demonstration featuring Symbol Tables, Interactive Expansion Trees, and Infinite Recursion Traps.")

if st.session_state.get("trace_toast"):
    st.toast(st.session_state["trace_toast"], icon="🔍")
    st.session_state["trace_toast"] = None

# Define Tabs
tab_editor, tab_tables, tab_tree, tab_debugger = st.tabs([
    "📝 Editor & Stats", 
    "📊 System Tables", 
    "🌳 Expansion Tree", 
    "🐞 Debugger"
])

# Initialize Processor
processor = MacroProcessor()
result = processor.process(st.session_state["source_code"])

with tab_editor:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Assembly Source")
        st.session_state["source_code"] = st.text_area("Input Assembly / Macros:", value=st.session_state["source_code"], height=400)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Compile Code", type="primary", use_container_width=True):
                st.session_state["trace_mdt"] = None
                st.rerun()
        with c2:
            if st.button("Reset Workspace", use_container_width=True):
                st.session_state["source_code"] = ""
                st.session_state["trace_mdt"] = None
                st.rerun()

    with col2:
        st.subheader("Expanded Output")
        if result["errors"]:
            st.error("⚠️ Compilation Failed! Check the 🐞 Debugger tab.")
            st.code("; Fix compilation errors to generate expanded code.", language="text", line_numbers=True)
        else:
            st.success("✅ Compilation Successful!")
            expanded = result["expanded_code"]
            st.code(expanded, language="text", line_numbers=True)
            
            st.download_button(
                label="📥 Download Assembly (.asm)",
                data=expanded,
                file_name="expanded_code.asm",
                mime="text/plain",
                use_container_width=True
            )
            
        # Stats Dashboard
        st.divider()
        st.markdown("### 📈 Process Statistics")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Original Lines", result['stats']['original_lines'])
        s2.metric("Expanded Lines", result['stats']['expanded_lines'])
        s3.metric("Expansion Ratio", f"{result['stats']['expansion_ratio']}x")
        s4.metric("Compile Time", f"{result['stats']['time_taken_ms']} ms")

def highlight_traced_row(row):
    trace_range = st.session_state["trace_mdt"]
    if trace_range and trace_range[0] <= row["Index"] <= trace_range[1]:
        return ['background-color: #3b82f6; color: white; font-weight: bold'] * len(row)
    return [''] * len(row)

with tab_tables:
    st.subheader("Internal Data Structures")
    c3, c4, c5 = st.columns([1.5, 1.5, 1])
    
    with c3:
        st.markdown("#### 📖 Macro Name Table (MNT)")
        if result["mnt"]:
            mnt_data = [{"Macro Name": name, "MDT Index": data["index"], "Parameters": data["params"]} for name, data in result["mnt"].items()]
            st.dataframe(pd.DataFrame(mnt_data), use_container_width=True, hide_index=True)
        else:
            st.info("MNT is empty.")
            
    with c4:
        st.markdown("#### 📑 Macro Definition Table (MDT)")
        if result["mdt"]:
            mdt_data = [{"Index": i, "Instruction": instr} for i, instr in enumerate(result["mdt"])]
            df = pd.DataFrame(mdt_data)
            
            if st.session_state["trace_mdt"]:
                styled_df = df.style.apply(highlight_traced_row, axis=1)
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("MDT is empty.")
            
    with c5:
        st.markdown("#### 🔤 Symbol Table")
        if result["symbol_table"]:
            sym_data = [{"Symbol": sym, "Address": addr} for sym, addr in result["symbol_table"].items()]
            st.dataframe(pd.DataFrame(sym_data), use_container_width=True, hide_index=True)
        else:
            st.info("No variables detected.")

with tab_tree:
    st.subheader("Interactive Expansion Accordion")
    st.markdown("Expand the macro nodes below to see the exact substitution logic mapping.")
    
    def render_tree(nodes, parent_name=None, path="0"):
        for i, node in enumerate(nodes):
            current_path = f"{path}_{i}"
            if node["type"] == "instruction":
                st.code(node["text"], language="text")
            elif node["type"] == "error":
                st.error(node["text"])
            elif node["type"] == "recursion":
                st.error(f"🛑 {node['text']}")
            elif node["type"] == "macro":
                is_expanded = st.checkbox(f"▶ Expand Macro: {node['name']}({node['args']})", key=f"expand_{current_path}")
                if is_expanded:
                    with st.container():
                        st.markdown("#### 💡 What's happening here?")
                    # Human Language Narrator
                    params = node['args'] if node['args'] else "None"
                    num_instructions = len(node['substitution'])
                    
                    narrative = f"The system found the macro call `{node['name']}` and is replacing its placeholders with your variables: `{params}`. "
                    narrative += f"It retrieved **{num_instructions}** instruction(s) from the MDT and is now expanding them."
                    
                    if parent_name:
                        narrative += f"\n\n*Note: Macro `{node['name']}` was found inside `{parent_name}`. The processor is pausing `{parent_name}` to resolve this inner macro first.*"
                        
                    st.write(narrative)
                    
                    # Visual Polish for substitution logic
                    if node["substitution"]:
                        sub_text = "\n".join(node["substitution"])
                        st.info(f"**Substitution Logic:**\n\n```text\n{sub_text}\n```")
                        
                    trace_btn_key = f"trace_{node['name']}_{current_path}"
                    
                    if node["mdt_range"]:
                        if st.button(f"🔍 Trace '{node['name']}' in MDT", key=trace_btn_key):
                            st.session_state["trace_mdt"] = node["mdt_range"]
                            st.session_state["trace_toast"] = f"Traced! '{node['name']}' is stored at MDT indices {node['mdt_range'][0]} to {node['mdt_range'][1]}."
                            st.rerun()
                    
                    st.markdown("**Children Nodes:**")
                    render_tree(node["children"], parent_name=node['name'], path=current_path)

    if result.get("execution_tree"):
        render_tree(result["execution_tree"])
    else:
        st.info("No expandable logic to display.")

with tab_debugger:
    st.subheader("Compiler Diagnostics")
    
    has_issues = False
    
    if result["errors"]:
        has_issues = True
        st.error(f"Found {len(result['errors'])} Fatal Error(s):")
        for error in result["errors"]:
            with st.expander(f"❌ Error at Line {error['line']}: {error['msg']}", expanded=True):
                st.write(f"**Suggested Fix:** {error['fix']}")
                st.caption(f"Review Line {error['line']} in your source code.")
                
    if result["stats"]["unused_macros"] > 0:
        has_issues = True
        st.warning(f"⚠️ Dead Code Warning: Found {result['stats']['unused_macros']} unused macro(s).")
        for unused in result["unused_macros"]:
            st.write(f"- `{unused}` was defined but never called.")
            
    if not has_issues:
        st.success("🎉 Clean build! 0 Errors, 0 Warnings.")
