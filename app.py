import streamlit as st
import pandas as pd
import sqlite3

# Connect to SQLite database
con = sqlite3.connect("db.db", check_same_thread=False)
cur = con.cursor()

# Create table
cur.execute("""
    CREATE TABLE IF NOT EXISTS db (
        name TEXT,
        letters TEXT,
        note TEXT
    )
""")
con.commit()

st.title("SQLite Database")
st.header("Add Record")

# Input fields
name = st.text_input("Name")
letters = st.text_input("Letters")
note = st.text_area("Note")

# Insert record
if st.button("Save"):
    if name.strip():
        cur.execute(
            "INSERT INTO db (name, letters, note) VALUES (?, ?, ?)",
            (name, letters, note)
        )
        con.commit()
        st.success("Record saved!")
    else:
        st.warning("Please enter a name.")

st.divider()

st.header("Database Records")

# Read records
if st.button("Refresh"):
    st.rerun()

myrows = cur.execute("""
    SELECT rowid, name, letters, note
    FROM db
    ORDER BY name
""").fetchall()

# Display records
df = pd.DataFrame(
    myrows,
    columns=["rowid", "name", "letters", "note"]
)

st.dataframe(df, use_container_width=True, hide_index=True)

# Display record count
st.write(f"Total records: {len(df)}")

con.close()
