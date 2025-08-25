import streamlit as st
from streamlit_js_eval import streamlit_js_eval

# Example: your cleanup method
def cleanup():
    st.session_state.clear()
    st.toast("Session cleaned!")

# Attach JS that fires on tab close
dead_flag = streamlit_js_eval(
    js_expressions="""
    (function() {
        window.addEventListener("pagehide", () => {
            localStorage.setItem("st_cleanup", "1");
        }, { once: true });
        window.addEventListener("beforeunload", () => {
            localStorage.setItem("st_cleanup", "1");
        }, { once: true });
        return localStorage.getItem("st_cleanup") || "0";
    })();
    """,
    key="tab-close"
)

# If JS wrote the cleanup flag, call Python cleanup
if dead_flag == "1":
    cleanup()
    # reset the flag so it doesn't run again
    streamlit_js_eval("localStorage.removeItem('st_cleanup');", key="reset-flag")

st.write("This is a minimal example. Close the tab to trigger cleanup.")
