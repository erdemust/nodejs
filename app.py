import streamlit as st
import pandas as pd
import sqlite3

con = sqlite3.connect('db.db')
cur = con.cursor()

cur.execute('''
    CREATE TABLE IF NOT EXISTS db (
        name TEXT,
        letters TEXT,
        note TEXT
    )
''')

st.header("Read")

# Retrieve records when the checkbox is checked
if st.checkbox('Recheck to refresh display', value=True):
    myrows = [
        list(row) for row in cur.execute('''
            SELECT rowid, name, letters, note
            FROM db
            ORDER BY name
        ''')
    ]

    # Create and display the dataframe
    st.dataframe(
        pd.DataFrame(
            myrows,
            columns=['rowid', 'name', 'letters', 'note']
        ),
        height=800
    )

con.close()
